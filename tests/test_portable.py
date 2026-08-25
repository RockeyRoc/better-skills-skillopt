from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from skillopt.portable import PortableSkillError, apply_bounded_patch, package_skill, validate_skill_text


SAFE_SKILL = """---
name: demo-skill
description: A small skill used for local validation tests.
---

# Demo skill

## Workflow

1. Inspect the request.
2. Verify the result.
"""


class PortableSkillTests(unittest.TestCase):
    def test_validation_accepts_safe_skill(self) -> None:
        self.assertTrue(validate_skill_text(SAFE_SKILL)["valid"])

    def test_patch_budget_and_exact_targets_are_enforced(self) -> None:
        candidate, reports = apply_bounded_patch(
            SAFE_SKILL,
            {"edits": [{"op": "insert_after", "target": "## Workflow", "content": "Check scope."}]},
        )
        self.assertEqual(len(reports), 1)
        self.assertIn("Check scope.", candidate)
        with self.assertRaises(PortableSkillError):
            apply_bounded_patch(SAFE_SKILL, {"edits": [{"op": "append", "content": "x"}] * 5})

    def test_packaging_creates_only_target_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            archive_path = package_skill(SAFE_SKILL, temp)
            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
                self.assertIn("better-demo-skill/manifest.json", names)
                self.assertIn("better-demo-skill/targets/copilot/copilot-instructions.md", names)
                manifest = json.loads(archive.read("better-demo-skill/manifest.json"))
                self.assertEqual(set(manifest["targets"]), {"codex", "claude", "cursor", "devin", "copilot"})
                self.assertTrue(all(".." not in name for name in names))


if __name__ == "__main__":
    unittest.main()

