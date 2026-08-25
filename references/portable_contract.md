# Portable packaging and safety contract

## Input contract

The CLI accepts one of:

- a UTF-8 `SKILL.md` file;
- a folder with `SKILL.md` at its root;
- a folder with exactly one immediate child containing `SKILL.md`;
- a ZIP containing exactly one safe `SKILL.md`.

ZIP input is inspected in place and never extracted. Absolute members, Windows
drive prefixes, path traversal, and ambiguous skill files are refused.

## Output contract

`package` writes exactly one new ZIP below the caller-provided `--output-dir`.
It refuses to overwrite an existing archive. The archive contains:

- the canonical optimized skill;
- explicit ready-to-copy target layouts;
- a small README;
- a manifest with the skill hash and validation results.

It contains no installer, executable, credentials, shell script, background job,
or auto-adoption behavior.

## Safety checks

Packaging stops on positive occurrences of destructive/system-mutation patterns
such as recursive deletion, registry/disk operations, shutdown commands, shell
pipe-to-execution patterns, and overly broad permission changes. Negated prose
such as “never run `rm -rf`” is allowed but still deserves human review.

Known secret-shaped values are rejected. This is defense in depth, not a secret
scanner guarantee; users must still review input and feedback.

The validator does not execute the candidate, inspect unrelated directories,
modify system configuration, install packages, or contact a provider.

