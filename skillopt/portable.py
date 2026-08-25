"""Local-only validation, bounded patching, feedback summaries, and packaging.

The module deliberately uses only the Python standard library. It never starts
processes, opens network connections, edits the source skill, or writes outside
the output path explicitly supplied by the caller.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


MAX_SKILL_BYTES = 1_000_000
DEFAULT_EDIT_BUDGET = 4
SLOW_UPDATE_START = "<!-- SLOW_UPDATE_START -->"
SLOW_UPDATE_END = "<!-- SLOW_UPDATE_END -->"
APPENDIX_START = "<!-- APPENDIX_START -->"
APPENDIX_END = "<!-- APPENDIX_END -->"
PROTECTED_REGIONS = (
    (SLOW_UPDATE_START, SLOW_UPDATE_END),
    (APPENDIX_START, APPENDIX_END),
)

SAFE_SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_FIELD = re.compile(r"^\s*(name|description)\s*:\s*(.*?)\s*$", re.I)

# These are intentionally conservative. A source skill that contains one of
# these as a negated example is allowed; a positive instruction is rejected
# before packaging because the delivered artifact must not encourage system
# mutation or destructive shell use.
HIGH_RISK_PATTERNS = (
    re.compile(r"\brm\s+-rf\b", re.I),
    re.compile(r"\bdel(?:ete)?\s+/[sqf]+\b", re.I),
    re.compile(r"\bformat\s+[a-z]:", re.I),
    re.compile(r"\b(?:reg(?:\.exe)?\s+(?:add|delete|import)|diskpart)\b", re.I),
    re.compile(r"\b(?:shutdown|restart-computer|stop-computer)\b", re.I),
    re.compile(r"\b(?:curl|wget|iwr|invoke-webrequest)\b[^\n|]*\|\s*(?:sh|bash|iex|invoke-expression)\b", re.I),
    re.compile(r"\bchmod\s+7{3}\b", re.I),
)
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
)
NEGATION_MARKERS = (
    "do not",
    "don't",
    "never",
    "must not",
    "mustn't",
    "avoid",
    "refuse",
    "prohibit",
    "without running",
    "read-only",
    "read only",
)


class PortableSkillError(ValueError):
    """Raised for an unsafe or ambiguous local operation."""


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    message: str


@dataclass(frozen=True)
class SkillInput:
    text: str
    source_kind: str
    source_name: str


def _ensure_utf8(data: bytes, label: str) -> str:
    if len(data) > MAX_SKILL_BYTES:
        raise PortableSkillError(f"{label} exceeds the {MAX_SKILL_BYTES} byte limit")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PortableSkillError(f"{label} is not valid UTF-8") from exc


def _safe_zip_member(name: str) -> bool:
    """Return whether a zip member is safe to inspect without extraction."""
    if not name or name.startswith(("/", "\\")) or "\\" in name:
        return False
    parts = PurePosixPath(name).parts
    if any(part in {"", ".", ".."} for part in parts):
        return False
    if parts and ":" in parts[0]:
        return False
    return True


def _find_skill_in_zip(path: Path) -> SkillInput:
    with zipfile.ZipFile(path, "r") as archive:
        candidates: list[str] = []
        for info in archive.infolist():
            name = info.filename.replace("\\", "/")
            if not _safe_zip_member(name) or name.startswith("__MACOSX/"):
                continue
            if PurePosixPath(name).name.lower() == "skill.md":
                candidates.append(name)
        if len(candidates) != 1:
            raise PortableSkillError(
                "input ZIP must contain exactly one safe SKILL.md; "
                f"found {len(candidates)}"
            )
        member = candidates[0]
        info = archive.getinfo(member)
        if info.file_size > MAX_SKILL_BYTES:
            raise PortableSkillError("SKILL.md inside input ZIP is too large")
        return SkillInput(
            text=_ensure_utf8(archive.read(member), f"{path.name}:{member}"),
            source_kind="zip",
            source_name=member,
        )


def load_skill(source: str | Path) -> SkillInput:
    """Read a skill file, a one-skill folder, or a ZIP without extracting it."""
    path = Path(source).expanduser()
    if not path.exists():
        raise PortableSkillError(f"input does not exist: {path}")
    if path.is_symlink():
        raise PortableSkillError("symbolic-link inputs are refused")
    if path.is_file() and path.suffix.lower() == ".zip":
        return _find_skill_in_zip(path)
    if path.is_file():
        return SkillInput(
            text=_ensure_utf8(path.read_bytes(), str(path)),
            source_kind="file",
            source_name=path.name,
        )
    if not path.is_dir():
        raise PortableSkillError(f"unsupported input type: {path}")

    direct = path / "SKILL.md"
    if direct.is_file():
        return SkillInput(
            text=_ensure_utf8(direct.read_bytes(), str(direct)),
            source_kind="directory",
            source_name=direct.name,
        )
    candidates = sorted(
        child / "SKILL.md"
        for child in path.iterdir()
        if child.is_dir() and not child.is_symlink() and (child / "SKILL.md").is_file()
    )
    if len(candidates) != 1:
        raise PortableSkillError(
            "input folder must contain SKILL.md at its root or exactly one "
            f"immediate skill folder; found {len(candidates)}"
        )
    candidate = candidates[0]
    return SkillInput(
        text=_ensure_utf8(candidate.read_bytes(), str(candidate)),
        source_kind="directory",
        source_name=str(candidate.relative_to(path)),
    )


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse the two discovery fields without requiring PyYAML."""
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}
    result: dict[str, str] = {}
    for line in lines[1:end]:
        match = FRONTMATTER_FIELD.match(line)
        if match:
            result[match.group(1).lower()] = _unquote(match.group(2))
    return result


def _is_negated(line: str, match: re.Match[str]) -> bool:
    prefix = line[: match.start()].lower()
    return any(marker in prefix for marker in NEGATION_MARKERS)


def _balanced_region_checks(text: str) -> Iterable[Check]:
    for start, end in PROTECTED_REGIONS:
        starts = text.count(start)
        ends = text.count(end)
        if starts == ends == 0:
            continue
        if starts == 1 and ends == 1 and text.index(start) < text.index(end):
            yield Check(start, "pass", "protected region is balanced")
        else:
            yield Check(start, "fail", "protected region markers are unbalanced")


def validate_skill_text(text: str) -> dict[str, Any]:
    """Return machine-readable checks; no filesystem writes are performed."""
    checks: list[Check] = []
    frontmatter = parse_frontmatter(text)
    if frontmatter.get("name"):
        if SAFE_SKILL_NAME.fullmatch(frontmatter["name"]):
            checks.append(Check("frontmatter.name", "pass", "valid lowercase skill name"))
        else:
            checks.append(
                Check(
                    "frontmatter.name",
                    "fail",
                    "name must use lowercase letters, digits, and single hyphens",
                )
            )
    else:
        checks.append(Check("frontmatter.name", "fail", "missing name"))

    description = frontmatter.get("description", "").strip()
    if description:
        checks.append(Check("frontmatter.description", "pass", "description is present"))
    else:
        checks.append(Check("frontmatter.description", "fail", "missing description"))

    body = text.split("---", 2)[-1].strip() if text.startswith("---") else text.strip()
    if body:
        checks.append(Check("body", "pass", "skill body is non-empty"))
    else:
        checks.append(Check("body", "fail", "skill body is empty"))

    approximate_tokens = max(1, len(text) // 4) if text else 0
    if approximate_tokens <= 2_000:
        checks.append(Check("compactness", "pass", f"approximately {approximate_tokens} tokens"))
    else:
        checks.append(
            Check(
                "compactness",
                "warn",
                f"approximately {approximate_tokens} tokens; review for redundant rules",
            )
        )

    checks.extend(_balanced_region_checks(text))

    for line_number, line in enumerate(text.splitlines(), 1):
        for pattern in HIGH_RISK_PATTERNS:
            match = pattern.search(line)
            if match and not _is_negated(line, match):
                checks.append(
                    Check(
                        "safety",
                        "fail",
                        f"line {line_number} contains a destructive/system-mutation instruction",
                    )
                )
                break
        for pattern in SECRET_PATTERNS:
            if pattern.search(line):
                checks.append(
                    Check(
                        "secrets",
                        "fail",
                        f"line {line_number} resembles a credential; remove it before packaging",
                    )
                )
                break

    if not any(check.name == "safety" for check in checks):
        checks.append(Check("safety", "pass", "no positive destructive command pattern found"))
    if not any(check.name == "secrets" for check in checks):
        checks.append(Check("secrets", "pass", "no known secret-shaped value found"))

    failed = [asdict(check) for check in checks if check.status == "fail"]
    return {
        "valid": not failed,
        "frontmatter": frontmatter,
        "approximate_tokens": approximate_tokens,
        "checks": [asdict(check) for check in checks],
        "failures": failed,
    }


def _protected_bounds(text: str, start: str, end: str) -> tuple[int, int] | None:
    start_at = text.find(start)
    end_at = text.find(end)
    if start_at == -1 and end_at == -1:
        return None
    if start_at == -1 or end_at == -1 or end_at < start_at:
        raise PortableSkillError("protected region markers are unbalanced")
    return start_at, end_at + len(end)


def _target_is_protected(text: str, target: str) -> bool:
    if not target:
        return False
    target_at = text.find(target)
    if target_at == -1:
        return False
    return any(
        bounds is not None and bounds[0] <= target_at < bounds[1]
        for start, end in PROTECTED_REGIONS
        for bounds in [_protected_bounds(text, start, end)]
    )


def _strip_protected_markers(text: str) -> str:
    for start, end in PROTECTED_REGIONS:
        text = text.replace(start, "").replace(end, "")
    return text.strip()


def apply_bounded_patch(skill: str, patch: dict[str, Any], max_edits: int = DEFAULT_EDIT_BUDGET) -> tuple[str, list[dict[str, Any]]]:
    """Apply only exact, bounded, auditable patch operations."""
    if not isinstance(patch, dict) or not isinstance(patch.get("edits"), list):
        raise PortableSkillError("patch must be a JSON object with an edits list")
    edits = patch["edits"]
    if len(edits) > max_edits:
        raise PortableSkillError(f"patch has {len(edits)} edits; budget is {max_edits}")
    current = skill
    reports: list[dict[str, Any]] = []
    allowed = {"append", "insert_after", "replace", "delete"}
    for index, edit in enumerate(edits, 1):
        if not isinstance(edit, dict):
            raise PortableSkillError(f"edit {index} is not an object")
        op = str(edit.get("op", "")).strip().lower()
        if op not in allowed:
            raise PortableSkillError(f"edit {index} uses unsupported operation: {op!r}")
        target = str(edit.get("target", ""))
        content = _strip_protected_markers(str(edit.get("content", "")))
        if op == "append":
            earliest = [current.find(start) for start, _ in PROTECTED_REGIONS if current.find(start) >= 0]
            insert_at = min(earliest) if earliest else len(current)
            before = current[:insert_at].rstrip()
            after = current[insert_at:]
            current = f"{before}\n\n{content}\n" + after
            reports.append({"index": index, "op": op, "status": "applied"})
            continue
        if not target or target not in current:
            raise PortableSkillError(f"edit {index} target was not found exactly")
        if current.count(target) != 1:
            raise PortableSkillError(f"edit {index} target must occur exactly once")
        if _target_is_protected(current, target):
            raise PortableSkillError(f"edit {index} targets a protected region")
        if op == "insert_after":
            at = current.index(target) + len(target)
            newline = current.find("\n", at)
            at = newline + 1 if newline >= 0 else len(current)
            current = current[:at] + "\n" + content + "\n" + current[at:]
        elif op == "replace":
            if not content:
                raise PortableSkillError(f"edit {index} replacement is empty")
            current = current.replace(target, content, 1)
        else:
            current = current.replace(target, "", 1)
        reports.append({"index": index, "op": op, "status": "applied"})
    return current.rstrip() + "\n", reports


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    normalized = re.sub(r"-+", "-", normalized)
    return normalized[:48] or "skill"


def _write_new(path: Path, data: bytes) -> None:
    if path.exists():
        raise PortableSkillError(f"refusing to overwrite existing output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _target_readme(name: str, slug: str, validation: dict[str, Any]) -> str:
    return f"""# better-{slug}\n\nThis archive contains an optimized, portable agent skill named `{name}`.\n\n## Install manually\n\nCopy exactly one target file into the agent/project layout you use:\n\n- Codex: `targets/codex/.agents/skills/{slug}/SKILL.md`\n- Claude Code: `targets/claude/.claude/skills/{slug}/SKILL.md`\n- Cursor: `targets/cursor/.cursor/skills/{slug}/SKILL.md`\n- Devin-compatible layout: `targets/devin/.devin/skills/{slug}/SKILL.md`\n- GitHub Copilot: `targets/copilot/copilot-instructions.md`\n\nThe archive is inert: it contains no installer and makes no changes by itself.\nReview the skill text before copying it into an agent.\n\nValidation result at packaging time: `{str(validation['valid']).lower()}`.\n"""


def package_skill(text: str, output_dir: str | Path, explicit_name: str | None = None) -> Path:
    """Create a portable target-skill ZIP in a caller-selected directory."""
    validation = validate_skill_text(text)
    if not validation["valid"]:
        messages = "; ".join(item["message"] for item in validation["failures"])
        raise PortableSkillError(f"skill failed validation: {messages}")
    frontmatter = validation["frontmatter"]
    name = explicit_name or frontmatter.get("name", "optimized-skill")
    slug = _slug(name)
    root = f"better-{slug}/"
    canonical = text.rstrip() + "\n"
    sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    files: dict[str, bytes] = {
        root + "SKILL.md": canonical.encode("utf-8"),
        root + f"targets/codex/.agents/skills/{slug}/SKILL.md": canonical.encode("utf-8"),
        root + f"targets/claude/.claude/skills/{slug}/SKILL.md": canonical.encode("utf-8"),
        root + f"targets/cursor/.cursor/skills/{slug}/SKILL.md": canonical.encode("utf-8"),
        root + f"targets/devin/.devin/skills/{slug}/SKILL.md": canonical.encode("utf-8"),
        root + "targets/copilot/copilot-instructions.md": (
            f"# {name}\n\n{canonical}"
        ).encode("utf-8"),
        root + "README.md": _target_readme(name, slug, validation).encode("utf-8"),
    }
    manifest = {
        "format": "better-skills-skillopt/v1",
        "skill_name": name,
        "slug": slug,
        "skill_sha256": sha256,
        "approximate_tokens": validation["approximate_tokens"],
        "targets": {
            "codex": f"targets/codex/.agents/skills/{slug}/SKILL.md",
            "claude": f"targets/claude/.claude/skills/{slug}/SKILL.md",
            "cursor": f"targets/cursor/.cursor/skills/{slug}/SKILL.md",
            "devin": f"targets/devin/.devin/skills/{slug}/SKILL.md",
            "copilot": "targets/copilot/copilot-instructions.md",
        },
        "validation": validation,
    }
    files[root + "manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    archive_path = Path(output_dir).expanduser() / f"better-{slug}.zip"
    if archive_path.exists():
        raise PortableSkillError(f"refusing to overwrite existing output: {archive_path}")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for member, data in sorted(files.items()):
            archive.writestr(member, data)
    return archive_path


def summarize_feedback(path: str | Path) -> dict[str, Any]:
    """Summarize reusable JSONL evidence without sending it anywhere."""
    rows: list[dict[str, Any]] = []
    ignored = 0
    for line_number, raw in enumerate(Path(path).expanduser().read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PortableSkillError(f"feedback line {line_number} is invalid JSON") from exc
        if not isinstance(row, dict):
            ignored += 1
            continue
        score = row.get("score")
        if isinstance(score, bool):
            score = None
        if isinstance(score, (int, float)) and 0 <= float(score) <= 1:
            numeric = float(score)
        else:
            outcome = str(row.get("outcome", "")).strip().lower()
            numeric = 1.0 if outcome in {"success", "passed", "pass"} else 0.0 if outcome in {"failure", "failed", "fail"} else None
        if numeric is None:
            ignored += 1
            continue
        rows.append({"score": numeric, "failure_type": str(row.get("failure_type", ""))})
    mean = sum(row["score"] for row in rows) / len(rows) if rows else None
    failure_types: dict[str, int] = {}
    for row in rows:
        failure_type = row["failure_type"]
        if failure_type:
            failure_types[failure_type] = failure_types.get(failure_type, 0) + 1
    return {
        "records": len(rows),
        "ignored_records": ignored,
        "mean_score": mean,
        "failure_types": dict(sorted(failure_types.items(), key=lambda item: (-item[1], item[0]))),
    }


def _json_print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-only Better Skills SkillOpt utility")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a SKILL.md, folder, or input ZIP")
    validate.add_argument("source")

    patch = sub.add_parser("apply-patch", help="apply a bounded SkillOpt-style JSON patch")
    patch.add_argument("--skill", required=True)
    patch.add_argument("--patch", required=True)
    patch.add_argument("--output", required=True)
    patch.add_argument("--max-edits", type=int, default=DEFAULT_EDIT_BUDGET)

    feedback = sub.add_parser("summarize-feedback", help="summarize local JSONL feedback")
    feedback.add_argument("source")

    package = sub.add_parser("package", help="package an optimized skill into a portable ZIP")
    package.add_argument("--skill", required=True)
    package.add_argument("--output-dir", required=True)
    package.add_argument("--name", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            loaded = load_skill(args.source)
            result = validate_skill_text(loaded.text)
            result["source_kind"] = loaded.source_kind
            result["source_name"] = loaded.source_name
            _json_print(result)
            return 0 if result["valid"] else 2
        if args.command == "summarize-feedback":
            _json_print(summarize_feedback(args.source))
            return 0
        if args.command == "apply-patch":
            loaded = load_skill(args.skill)
            patch_path = Path(args.patch).expanduser()
            patch = json.loads(patch_path.read_text(encoding="utf-8"))
            candidate, reports = apply_bounded_patch(loaded.text, patch, args.max_edits)
            validation = validate_skill_text(candidate)
            if not validation["valid"]:
                raise PortableSkillError("candidate failed validation; no output was written")
            output = Path(args.output).expanduser()
            _write_new(output, candidate.encode("utf-8"))
            _json_print({"output": str(output), "reports": reports, "validation": validation})
            return 0
        if args.command == "package":
            loaded = load_skill(args.skill)
            archive = package_skill(loaded.text, args.output_dir, args.name)
            _json_print({"output": str(archive), "source_kind": loaded.source_kind})
            return 0
    except (OSError, PortableSkillError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

