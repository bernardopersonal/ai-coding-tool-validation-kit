# Developer notes

How the kit turns answers into documents, and the exact contract template
authors must follow. Python 3.9+ standard library only (no PyYAML, no Jinja).

```
kit.py            CLI: init / render / example-config / vars
kit/config.py     defaults, validation, derive(), variable registry (VARIABLES)
kit/wizard.py     interactive questionnaire (input() with [defaults])
kit/render.py     strict mustache-like engine
kit/package.py    templates/*.md.tmpl -> output/ layout, optional pandoc .docx
templates/        *.md.tmpl
tests/            python3 -m unittest discover -s tests -v
```

## Pipeline

1. `python3 kit.py init` runs the wizard (or `--defaults` skips it), writes
   `kit.config.json` and renders. `python3 kit.py render --config kit.config.json`
   re-renders from an existing (possibly hand-edited) config.
2. `config.validate_config()` rejects unknown keys (keys starting with `_` are
   allowed as comments), derived keys, wrong types/enums, executor == approver,
   duplicate or reserved (`GEN`) tool IDs, a pinned model outside the envelope,
   and any `{{` / `}}` in values.
3. `config.derive()` builds the template context: the answers plus every
   derived field (booleans, doc IDs, loop lists, `today`). The config file never
   stores derived values. The optional config key `today` (YYYY-MM-DD) freezes
   the date for reproducible examples.
4. `package.render_package()` renders every template in memory and writes files
   only if all of them rendered:
   - `templates/00-<name>.md.tmpl` -> `output/00-shared/<name>.md`, context stack `[global]`;
   - any other `templates/NN-<name>.md.tmpl` -> `output/<TOOL_ID>/NN-<name>.md`, once per
     tool, context stack `[global, tool]`.
5. `--docx` converts each `.md` with `pandoc` if it is on PATH; otherwise prints a
   notice and continues.

## Wizard

Questions in order: organisation name/code, doc ID pattern, product context,
regulatory frameworks (multi-select), roles (approver must differ from
executor; PRRC optional, `-` clears it), code host, contexts of use
(multi-select), risk model, already in use, periodic review months (default 6
when `agents_qms` is selected), number of tools, then per tool: type, name, ID
code, vendor, surfaces (multi-select), approved models (comma-separated ids or
patterns such as `vendor-family-*`), model policy (`envelope` / `pinned`) and,
if pinned, the exact pinned model (must match an approved entry). Defaults are
shown in brackets; Enter accepts. Multi-select answers are comma-separated keys
or option numbers. An existing valid config supplies the defaults. `init
--defaults` refuses to overwrite a different existing config unless `--force`.

## Template syntax (the only syntax)

| Tag | Meaning |
|---|---|
| `{{name}}`, `{{a.b}}` | Variable. Booleans print `yes` / `no`. Lists, dicts and null are errors. |
| `{{#name}}...{{/name}}` | Section: rendered if truthy. A list repeats the block per item with the item pushed on the stack; a dict or other truthy value is pushed once. |
| `{{^name}}...{{/name}}` | Inverted section: rendered once if falsy (`false`, `""`, `0`, empty list). |
| `{{.}}` | Current scalar item, e.g. `{{#approved_models}}- {{.}}{{/approved_models}}`. |

Rules enforced by `kit/render.py` (all failures raise `RenderError` with
`template:line` and the name):

- Unknown variable or section name is an error, in every branch: a static
  check walks blocks that are not rendered for the current data too, and
  suggests close matches (`did you mean ...`).
- Unbalanced, mismatched or unclosed tags, tags split across lines, and any
  other syntax (`{{! }}`, `{{> }}`, `{{{ }}}`, `{{& }}`, `{{= =}}`) are errors.
- Lookup goes from the innermost section item down to the global context.
- Standalone lines: a line holding only section tags (`#`, `^`, `/`) and
  whitespace is removed with its newline, so put section tags on their own
  lines and no blank lines are left behind.
- After rendering: whitespace-only lines are emptied, 3+ blank lines collapse
  to 2, the output ends with one newline, and any leftover `{{` is an error.
  Consequence: templates cannot emit literal `{{` (for example GitHub Actions
  `${{ }}` expressions); put such snippets in `examples/` files instead.

## Adding or changing templates

- Name: `NN-lowercase-words.md.tmpl`; `00-` = shared document, anything else
  = per-tool document (`01`-`08` map to `doc_id_01`-`doc_id_08`).
- Use only the variables listed below. Never hard-code model names: use
  `{{#approved_models}}{{.}}{{/approved_models}}` and `{{pinned_model}}`.
- `tests/test_templates.py` renders every template across a matrix of 156
  configs (every tool type, csa / three_level, all contexts / only
  `code_product` / only `doc_drafting`, in use or not, GxP on/off, envelope /
  pinned, github / gitlab / other) and also checks file names, hard-coded model
  ids and the de-identification rules. Run the suite before committing.
- The tests need at least one shared (`00-`) and one per-tool template.
- `examples/acme-medsoft/` holds the fictional example: `kit.config.json`, the
  package rendered from it and then filled in by hand as if executed. After a
  template change, render the config into a scratch directory (`python3 kit.py
  render --config examples/acme-medsoft/kit.config.json --out /tmp/acme`) and
  carry the relevant changes into the filled files by hand: rendering straight
  into `examples/acme-medsoft/package` overwrites the filled-in content.
  `tests/test_examples.py` checks the config, the file set, the banner and the
  absence of leftover tags and real model names.
- Adding a variable: add it in `config.derive()` / `derive_tool()` and in
  `VARIABLES`, then run `python3 kit.py vars --update README_DEV.md` (a test
  fails if this file is stale or if `derive()` and `VARIABLES` disagree).

## Variables available to templates

Per-tool templates see the global and tool variables; shared templates see
the global variables, and the tool variables only inside
`{{#tools_list}}...{{/tools_list}}`.

<!-- BEGIN GENERATED VARIABLES (python3 kit.py vars --update README_DEV.md) -->

#### Global variables (every template)

| Variable | Type | Description |
|---|---|---|
| `kit_version` | str | Kit version that rendered the document. |
| `today` | str | Render date, ISO format (YYYY-MM-DD). Optional config override: `today`. |
| `org_name` | str | Organisation legal name. |
| `org_code` | str | Short organisation code used in document IDs. |
| `doc_id_pattern` | str | Document ID pattern with tokens `{org}`, `{tool}`, `{nn}`. |
| `product_context` | str | Product / regulatory context (free text). |
| `reg_iso13485` | bool | ISO 13485:2016 (§4.1.6 software validation) |
| `reg_fda_qmsr` | bool | FDA QMSR (21 CFR Part 820, incorporates ISO 13485) |
| `reg_gxp` | bool | GxP: EU GMP Annex 11 + 21 CFR Part 11 |
| `reg_iso27001` | bool | ISO/IEC 27001 (cross-references) |
| `reg_iso42001` | bool | ISO/IEC 42001 (cross-references) |
| `role_executor` | str | Role that executes the validation. |
| `role_approver` | str | Role that approves the validation (always different from the executor). |
| `role_tool_owner` | str | Role that owns the tool and its configuration. |
| `role_prrc` | str | PRRC role/name; empty string if not set (use `{{#role_prrc}}...{{/role_prrc}}`). |
| `code_host` | str | Git hosting: `github`, `gitlab` or `other`. |
| `code_github` | bool | `code_host` is `github`. |
| `code_gitlab` | bool | `code_host` is `gitlab`. |
| `code_other` | bool | `code_host` is `other`. |
| `contexts` | list[str] | Selected context keys, canonical order (scalars: use `{{.}}`). |
| `contexts_list` | list[context] | Selected contexts as items {key, label, description}. |
| `ctx_code_product` | bool | Context `code_product` selected: Code for the regulated product (software in or as a medical device). |
| `ctx_code_tooling` | bool | Context `code_tooling` selected: Internal tools, scripts and automation that are not part of the product. |
| `ctx_pr_review` | bool | Context `pr_review` selected: AI review comments on pull requests; advisory only, never counted as the required human approval. |
| `ctx_test_generation` | bool | Context `test_generation` selected: Generation of unit, integration or regression tests and test data. |
| `ctx_doc_drafting` | bool | Context `doc_drafting` selected: Drafting of controlled documents and records, previewed and approved by a human before they are written or released. |
| `ctx_agents_qms` | bool | Context `agents_qms` selected: Autonomous or scheduled agents acting on QMS systems. |
| `risk_model` | str | `csa` or `three_level`. |
| `risk_csa` | bool | `risk_model` is `csa` (high / not high process risk). |
| `risk_three` | bool | `risk_model` is `three_level` (low / medium / high). |
| `already_in_use` | bool | Tool already in use: add retrospective validation and interim-use justification. |
| `periodic_review_months` | int | Periodic review interval in months. |
| `doc_id_wi` | str | Doc ID of the shared work instruction (tool token `GEN`, nn `01`). |
| `doc_id_discovery` | str | Doc ID of the shared tool-discovery checklist (tool token `GEN`, nn `02`). |
| `doc_id_gates` | str | Doc ID of the shared code-host gate qualification (tool token `GEN`, nn `03`): OQ-01 to OQ-07 and OQ-12 executed once per code host for all tools. |
| `tools_list` | list[tool] | All tools (each item has the tool variables below). |
| `tools` | list[tool] | Alias of `tools_list`. |

#### Tool variables (per-tool templates, and inside `{{#tools_list}}` loops)

| Variable | Type | Description |
|---|---|---|
| `tool_key` | str | Tool type: `claude_code`, `codex`, `copilot`, `cursor` or `other`. |
| `tool_name` | str | Display name, e.g. Claude Code. |
| `tool_id` | str | Short code used in doc IDs and as output folder name. |
| `vendor` | str | Vendor name. |
| `surfaces` | list[str] | Surface keys in use, canonical order (scalars: use `{{.}}`). |
| `surfaces_list` | list[surface] | Surfaces in use as items {key, label}. |
| `surf_local_cli_ide` | bool | Surface `local_cli_ide` (Local CLI / IDE) in use. |
| `surf_cloud_agent` | bool | Surface `cloud_agent` (Cloud agent) in use. |
| `surf_pr_review_bot` | bool | Surface `pr_review_bot` (PR review bot) in use. |
| `surf_ci_headless` | bool | Surface `ci_headless` (CI / headless) in use. |
| `approved_models` | list[str] | Approved model ids or family patterns (scalars: use `{{.}}`). |
| `model_policy` | str | `envelope` or `pinned`. |
| `policy_envelope` | bool | `model_policy` is `envelope`. |
| `policy_pinned` | bool | `model_policy` is `pinned`. |
| `pinned_model` | str | Exact pinned model id; empty string when envelope. |
| `is_claude_code` | bool | Tool type is `claude_code` (Claude Code (Anthropic)). |
| `is_codex` | bool | Tool type is `codex` (OpenAI Codex). |
| `is_copilot` | bool | Tool type is `copilot` (GitHub Copilot). |
| `is_cursor` | bool | Tool type is `cursor` (Cursor). |
| `is_other` | bool | Tool type is `other` (Other AI coding tool). |
| `doc_id_01` | str | Doc ID of per-tool document 01 (Inventory and intended use). |
| `doc_id_02` | str | Doc ID of per-tool document 02 (Requirements). |
| `doc_id_03` | str | Doc ID of per-tool document 03 (Risk assessment). |
| `doc_id_04` | str | Doc ID of per-tool document 04 (Validation plan). |
| `doc_id_05` | str | Doc ID of per-tool document 05 (Test protocol). |
| `doc_id_06` | str | Doc ID of per-tool document 06 (Configuration baseline). |
| `doc_id_07` | str | Doc ID of per-tool document 07 (Validation report). |
| `doc_id_08` | str | Doc ID of per-tool document 08 (Change and revalidation). |

#### Items of `contexts_list` (inside `{{#contexts_list}}`)

| Variable | Type | Description |
|---|---|---|
| `key` | str | Context key, e.g. `code_product`. |
| `label` | str | Short human-readable label. |
| `description` | str | One-sentence description. |

#### Items of `surfaces_list` (inside `{{#surfaces_list}}`)

| Variable | Type | Description |
|---|---|---|
| `key` | str | Surface key, e.g. `local_cli_ide`. |
| `label` | str | Short human-readable label. |

<!-- END GENERATED VARIABLES -->
