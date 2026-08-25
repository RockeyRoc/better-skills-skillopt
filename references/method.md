# SkillOpt method notes

## What is reused

The paper treats a skill document as the external trainable state of a frozen
agent. The useful deployment ideas are:

1. Keep the target model/harness fixed while changing only the text skill.
2. Collect multiple success and failure examples before proposing a rule.
3. Prefer procedural, reusable rules over task-specific fixes.
4. Use a bounded edit budget as a textual learning-rate analogue.
5. Validate a candidate on comparable held-out evidence before accepting it.
6. Keep rejected edits as negative feedback instead of repeatedly proposing them.
7. Keep optimizer-side memory separate from the compact deployed skill.

## Deployment adaptation

The full research loop can execute a benchmark harness and make model calls. This
portable project intentionally stops at the safe boundary available to a normal
agent skill:

- the current agent performs evidence-based reflection in context;
- `apply-patch` applies a small, exact proposal locally;
- `validate` checks the candidate artifact;
- `package` creates a portable ZIP;
- any real score comparison must be supplied by the user or an explicitly
  configured, separate evaluation workflow.

The package therefore does not claim that a rewrite is better merely because it
sounds better. A valid syntax/safety check is not a benchmark score.

## Patch schema

```json
{
  "edits": [
    {"op": "append", "content": "A general rule."},
    {"op": "insert_after", "target": "## Workflow", "content": "..."},
    {"op": "replace", "target": "an exact unique span", "content": "..."},
    {"op": "delete", "target": "an exact unique redundant span"}
  ]
}
```

`insert_after`, `replace`, and `delete` require an exact target occurring once.
The protected `SLOW_UPDATE` and `APPENDIX` regions are reserved for a future
explicit consolidation pass and cannot be changed by bounded step edits.

## Evidence discipline

One example is a hint. A rule becomes a good candidate when it explains a
repeated failure or a repeated successful behavior across multiple tasks. For
open-ended coding work, use a short local score or reviewer label and keep the
same task mix for baseline and candidate comparisons. If there is no comparable
selection evidence, report the result as a reviewed candidate, not as a proven
improvement.

