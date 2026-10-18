# Repository rules for AI agents

- Use only the documents in `docs/sources/` as sources. Never invent facts.
- Every statement must cite the source file it comes from, in the form
  `[source: docs/sources/<file>.md]`.
- If the sources do not contain the answer, say so instead of guessing.
- Files under `docs/sources/`, `.github/` and `tests/` are controlled. Never
  modify them.
- Never write secrets, tokens or credentials to any file.
