# Contributing

Thanks for helping. Issues and pull requests are welcome: corrections of vendor facts, new admission tasks, adapters for other tools, translations of the guide, and reports from real validations or audits (de-identified).

## Before you open a pull request

1. Run the tests: `python3 -m unittest discover -s tests -v`. CI runs the same suite on Python 3.9 and 3.12.
2. Render with the defaults and read the output: `python3 kit.py init --defaults --force --config /tmp/kit-check/kit.config.json --out /tmp/kit-check`. If you changed a template, also render `examples/acme-medsoft/kit.config.json` and carry the change into the filled example (see [README_DEV.md](README_DEV.md)).
3. Add a line to [CHANGELOG.md](CHANGELOG.md) under "Unreleased".

## Rules

- **Standard library only.** Python 3.9+, no third-party packages.
- **Canonical IDs are fixed.** Do not renumber REQ, IQ, OQ, MA or PQ identifiers. Add new ones only after discussing it in an issue.
- **Templates use only the documented variables and syntax** ([README_DEV.md](README_DEV.md)). The test matrix renders every template across 156 configurations.
- **No hard-coded model names in templates.** Models come from the wizard (`approved_models`, `pinned_model`). The tests reject model ids in template text.
- **Verified facts only.** Every vendor setting key, CLI flag, API field or enum value must come from the vendor's documentation or source code. Give the source URL and the date you checked it in the pull request. If you cannot verify something, write "verify against the vendor's current documentation" instead of guessing. Mark regulatory interpretations as interpretations.
- **No copied standard text.** ISO and IEC texts are copyrighted, so paraphrase them. Do not copy material under non-commercial or share-alike licences into the kit.
- **De-identification.** No real company other than tool vendors and public sources, no internal document codes, no names of real people in examples, no dates or wording taken from a real organisation's records. The example organisation is fictional (Acme MedSoft). The repository-wide de-identification test reads its deny-list from a local file that is never committed (`tests/deid-local.txt`, git-ignored, or the file named by `KIT_DEID_PATTERNS`), so the list itself does not publish what it protects. Maintainers run it before every release.
- **Human-in-the-loop stays.** Changes must not let the AI tool approve, sign, merge or conclude anything, or treat AI output as a control without the pinned policy.
- **English, concise, auditor-friendly.** Short sentences, one idea per line in tables, clause references where they help.

## Adding an admission task

Add a JSON file to `admission/tasks/` with the documented keys (see `admission/README.md`) and a small self-contained fixture under `admission/fixtures/`. Criteria must be objective (repository state, command results), never similarity of output. A new task changes the suite version, and validated organisations treat that as a change to their validation plan.

## Licence of contributions

By contributing, you agree that code contributions are licensed under the MIT licence ([LICENSE](LICENSE)), and documentation and template contributions under CC BY 4.0 ([LICENSE-docs](LICENSE-docs)).
