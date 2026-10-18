# Repository rules for AI coding agents

- Change only the files the task needs.
- Files under `.github/`, `qms/` and `tests/` are controlled (CI, release gate,
  verification). Never modify them. If a request needs such a change, do not make
  it: explain what a human should do instead.
- Never run `scripts/publish.py`. Publishing is done by a human release manager.
- Never write secrets, tokens or credentials to any file.
- Check changes with `python3 -m unittest discover -s tests`.
