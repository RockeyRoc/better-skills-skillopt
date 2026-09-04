# Better Skills SkillOpt

<<<<<<< HEAD
[中文版 README](README.zh-CN.md) · [未来发展计划书](ROADMAP.zh-CN.md) · [宣传网站](index.html)
>>>>>>>

*A low-friction, local-only optimizer for portable agent skills.*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Standard Library](https://img.shields.io/badge/Dependencies-Python%20standard%20library-green.svg)](https://docs.python.org/3/library/)
[![Inspired by SkillOpt](https://img.shields.io/badge/Inspired%20by-Microsoft%20SkillOpt-8dbb3c)](https://github.com/microsoft/SkillOpt)
[![GitHub](https://img.shields.io/badge/Repository-better--skills-181717?logo=github)](https://github.com/RockeyRoc/better-skills)

> Improve an existing SKILL.md from reviewed feedback, validate the candidate, and export a new better-name.zip for Codex, Claude Code, Cursor, Devin, or GitHub Copilot.

---

## Overview

Agent skills are often hand-written or rewritten in one large step. Better Skills SkillOpt turns improvement into a small, auditable workflow:

~~~text
source skill + feedback
        |
        v
agent reflection
        |
        v
bounded text patch
        |
        v
local validation gate
        |
        v
portable ZIP package
~~~

The agent performs semantic reflection. The included Python utility stays deliberately narrow: it reads local inputs, applies exact patches, validates the result, summarizes JSONL evidence, and creates the ZIP. It does not call a model provider or execute the candidate skill.

## Why this project exists

Microsoft SkillOpt is a research-oriented optimizer with model backends, benchmarks, training configurations, and datasets. This project packages the deployment-facing idea for coding-agent users who need a simple, portable output artifact.

The design is inspired by Yang et al., [SkillOpt: Executive Strategy for Self-Evolving Agent Skills](https://arxiv.org/abs/2605.23904):

- Treat the skill document as mutable text state.
- Learn from repeated success and failure evidence.
- Keep edits bounded and inspectable.
- Validate a candidate before calling it better.
- Separate optimizer notes from the deployed skill.

## Features

### Bounded edits

Only append, insert_after, replace, and delete operations are accepted. The default proposal budget is four edits. Protected sections, ambiguous anchors, destructive command patterns, and secret-shaped values are rejected.

### Local validation

The validation gate checks frontmatter, non-empty content, compactness, protected markers, suspicious destructive patterns, and secret-shaped values. A safety failure is a hard stop; passing validation is not a benchmark score.

### Portable packaging

The package command creates an inert ZIP with one canonical skill and target-oriented copies:

~~~text
better-name/
|-- SKILL.md
|-- manifest.json
|-- README.md
+-- targets/
    |-- codex/.agents/skills/name/SKILL.md
    |-- claude/.claude/skills/name/SKILL.md
    |-- cursor/.cursor/skills/name/SKILL.md
    |-- devin/.devin/skills/name/SKILL.md
    +-- copilot/copilot-instructions.md
~~~

The archive does not install anything or modify an agent directory. Review it first, then copy the appropriate target file manually.

## Supported agent layouts

| Target | Deployment-facing file |
|---|---|
| Codex | targets/codex/.agents/skills/name/SKILL.md |
| Claude Code | targets/claude/.claude/skills/name/SKILL.md |
| Cursor | targets/cursor/.cursor/skills/name/SKILL.md |
| Devin | targets/devin/.devin/skills/name/SKILL.md |
| GitHub Copilot | targets/copilot/copilot-instructions.md |

## Quick start

Requirements: Python 3.10 or newer. No third-party package is required.

~~~powershell
python scripts/skillopt_portable.py validate path\to\SKILL.md
python scripts/skillopt_portable.py summarize-feedback data\examples.jsonl
python scripts/skillopt_portable.py package --skill path\to\candidate\SKILL.md --output-dir .\dist
~~~

To apply a reviewed proposal:

~~~powershell
python scripts/skillopt_portable.py apply-patch --skill path\to\original\SKILL.md --patch path\to\proposal.json --output path\to\candidate\SKILL.md
~~~

Run tests with:

~~~powershell
python -m unittest discover -s tests -v
~~~

The result is dist/better-<skill-name>.zip.

## Feedback format

Feedback is stored as one JSON object per line with a task, outcome, failure type, observation, and score between 0 and 1.

Use the summarizer to inspect recurring patterns. Do not include passwords, tokens, private prompts, raw tool payloads, or unnecessary local paths.

## Safety boundary

This project is designed to generate new skill files only.

- It reads only files explicitly supplied by the user.
- It never overwrites the original skill.
- It writes only the selected candidate path and output directory.
- It does not access the network, install dependencies, or modify system files.
- It does not copy files into agent directories automatically.
- It rejects unsafe archive paths and suspicious command or secret patterns.
- The ZIP is inert and requires manual review before deployment.

## Project structure

~~~text
better-skills-skillopt/
|-- SKILL.md
|-- agents/openai.yaml
|-- data/examples.jsonl
|-- references/
|   |-- method.md
|   +-- portable_contract.md
|-- scripts/skillopt_portable.py
|-- skillopt/portable.py
+-- tests/test_portable.py
~~~

SKILL.md is the deployable entry point. The Python package and CLI provide deterministic local operations; references record the method and safety contract.

## Method and references

The conservative loop is: review outcomes, propose a small patch, apply it to a copy, validate locally, package the candidate, and retain the original for comparison.

This lightweight implementation is a portable deployment layer, not a replacement for the full Microsoft SkillOpt research framework.

- SkillOpt paper: https://arxiv.org/abs/2605.23904
- Microsoft SkillOpt project: https://github.com/microsoft/SkillOpt
- Codex skill creator guidance: https://developers.openai.com/codex/skills/

## Citation

~~~bibtex
@article{yang2026skillopt,
  title={SkillOpt: Executive strategy for self-evolving agent skills},
  author={Yang, Yifan and Gong, Ziyang and Huang, Weiquan and Yang, Qihao and Zhou, Ziwei and Huang, Zisu and Li, Yan and Gao, Xuemei and Dai, Qi and Liu, Bei and others},
  journal={arXiv preprint arXiv:2605.23904},
  year={2026}
}
~~~
