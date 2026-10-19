# Contributing

Thanks for helping. Issues and pull requests are welcome: corrections of vendor facts, new admission tasks, adapters for other tools, translations of the guide, and reports from real validations or audits (de-identified).

## Before you open a pull request

1. Run the tests: `python3 -m unittest discover -s tests -v`. CI runs the same suite on Python 3.9 and 3.12.
2. Render both profiles with the defaults and read the output: `python3 kit.py init --defaults --force --config /tmp/kit-check/kit.config.json --out /tmp/kit-check/lite` (lite) and `python3 kit.py render --config /tmp/kit-check/kit.config.json --profile full --out /tmp/kit-check/full`. If you changed a template, also render the example of its profile into a scratch directory and carry the change into the filled example by hand (see [README_DEV.md](README_DEV.md)): `python3 kit.py render --config examples/acme-medsoft/kit.config.json --out /tmp/acme` (full) and `python3 kit.py render --config examples/acme-medsoft-lite/kit.config.json --out /tmp/acme-lite` (lite).
3. Add a line to [CHANGELOG.md](CHANGELOG.md) under "Unreleased".

## Rules

- **Standard library only.** Python 3.9+, no third-party packages.
- **Canonical IDs are fixed.** Do not renumber REQ, IQ, OQ, MA or PQ identifiers. Add new ones only after discussing it in an issue.
- **Templates use only the documented variables and syntax** ([README_DEV.md](README_DEV.md)). The test matrix renders every template of both profiles (`templates/full/`, `templates/lite/`) across 156 configurations. Lite uses only IDs that full defines, keeps criteria equal to or stricter than full under each shared ID (differences listed in `docs/lite-vs-full.md`), and stays within its word budget: shorten text rather than raise the budget.
- **No hard-coded model names in templates.** Models come from the wizard (`approved_models`, `pinned_model`). The tests reject model ids in template text.
- **Verified facts only.** Every vendor setting key, CLI flag, API field or enum value must come from the vendor's documentation or source code. Give the source URL and the date you checked it in the pull request. If you cannot verify something, write "verify against the vendor's current documentation" instead of guessing. Mark regulatory interpretations as interpretations.
- **No copied standard text.** ISO and IEC texts are copyrighted, so paraphrase them. Do not copy material under non-commercial or share-alike licences into the kit.
- **De-identification.** No real company other than tool vendors and public sources, no internal document codes, no names of real people in examples, no dates or wording taken from a real organisation's records. The example organisation is fictional (Acme MedSoft). The repository-wide de-identification test reads its deny-list from a local file that is never committed (`tests/deid-local.txt`, git-ignored, or the file named by `KIT_DEID_PATTERNS`), so the list itself does not publish what it protects. Maintainers run it before every release.
- **Human-in-the-loop stays.** Changes must not let the AI tool approve, sign, merge or conclude anything, or treat AI output as a control without the pinned policy.
- **English, concise, auditor-friendly.** Short sentences, one idea per line in tables, clause references where they help.
- **Citation and time style** (enforced by `tests/test_style.py`). Never use the section sign: write "ISO 13485:2016 clause 4.1.6", "IEC 62304 clause 5.1.4", "21 CFR 820.10", "21 CFR 11.10(e)", "FD&C Act section 524B", "MDR Article 10(8)", "section 3 of this plan". README.md states no times or durations; make no effort or speed claims anywhere (the tests check GUIDE.md and `docs/`). Minimum observation periods and review cadences that are acceptance criteria may stay in templates and docs.

## Adding an admission task

Add a JSON file to `admission/tasks/` with the documented keys (see `admission/README.md`) and a small self-contained fixture under `admission/fixtures/`. Criteria must be objective (repository state, command results), never similarity of output. A new task changes the suite version, and validated organisations treat that as a change to their validation plan.

## Licence of contributions

By contributing, you agree that code contributions are licensed under the MIT licence ([LICENSE](LICENSE)), and documentation and template contributions under CC BY 4.0 ([LICENSE-docs](LICENSE-docs)).
