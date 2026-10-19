# Developer notes

How the kit turns answers into documents, and the exact contract template
authors must follow. Python 3.9+ standard library only (no PyYAML, no Jinja).

```
kit.py            CLI: init / render / example-config / vars
kit/config.py     defaults, validation, profiles, derive(), variable registry (VARIABLES)
kit/wizard.py     interactive questionnaire (input() with [defaults])
kit/render.py     strict mustache-like engine
kit/package.py    templates/<profile>/*.md.tmpl -> output/ layout, optional pandoc .docx
templates/full/   *.md.tmpl, the in-depth package
templates/lite/   *.md.tmpl, the risk-proportionate minimum
examples/acme-medsoft/       filled fictional example, full profile
examples/acme-medsoft-lite/  filled fictional example, lite profile
tests/            python3 -m unittest discover -s tests -v
```

## Profiles

Two template sets render from the same config and the same variables:

| Profile | Templates | Package |
|---|---|---|
| `full` | `templates/full/` | per tool 01 inventory and intended use ... 08 change and revalidation; shared work instruction, tool-discovery checklist and code-host gate qualification |
| `lite` | `templates/lite/` | per tool 01 validation plan, 02 test record, 03 validation report; shared work instruction and tool-discovery checklist |

- Lite uses the canonical IDs (REQ-xx, IQ-xx, OQ-xx, MA-01, PQ-xx) and the
  commands of full; under a shared ID the lite criterion equals or exceeds the
  full one, and full adds tests and steps (listed in `docs/lite-vs-full.md`,
  "Differences under shared IDs"). `tests/test_lite.py` rejects an ID in a lite
  template that the full templates do not define, and a lite test ID missing
  from that table.
- Document IDs: every lite document has its own number token, so one ID
  always names one document. Per tool `L01` to `L03` (`doc_id_01` to
  `doc_id_03` in the lite profile, e.g. `ACME-VAL-CLAUDE-L01`, never the full
  inventory `ACME-VAL-CLAUDE-01`); shared `GEN-L01` and `GEN-L02`
  (`doc_id_wi`, `doc_id_discovery`, never the full `GEN-01`, `GEN-02`).
  `L` plus two digits is not confused with the triggers L1 to L9.
  `doc_id_04` to `doc_id_08` and `doc_id_gates` name full-only documents and
  are the same in both profiles. On upgrade the full documents supersede the
  lite records under their own IDs; evidence IDs (IQ, OQ, MA, PQ) are reused
  and new deviations continue the lite DEV numbering (`config.LITE_DOC_NN`, `config.LITE_SHARED_NN`; `tests/test_style.py`
  checks that the default config gives no collision).
- Selection, highest first: `--profile lite|full` on `init` or `render`; the
  config key `profile`; otherwise `full`. A config without the key (written by
  kit 0.1.0) renders as `full`, and `render` prints a notice. New configs get
  `lite`: `init --defaults` writes `"profile": "lite"`, and the wizard defaults
  to the recommendation (below). `init --profile X` stores X in the config;
  `render --profile X` leaves the config unchanged.
- Recommendation: `config.full_profile_reasons()` returns one short sentence
  per trigger in the answers, starting with its L number (lite plan section 2):
  model policy `pinned` (L1), context `agents_qms` or `agent_qms_write` (L2),
  context `doc_drafting` (L3), GxP `reg_gxp` (L4), `ai_output_as_evidence` (L8),
  `agent_untrusted_with_secrets` (L9). L1, L2, L8 and L9 are hard stops
  (`config.lite_blockers()`): `package.render_package()` raises `RenderRefused`
  for a lite render unless `force` (`--force`), and the lite documents then
  carry a NOT VALID FOR RELEASE banner (`lite_blocked`, `lite_blockers`). L3
  and L4 give the warning (`full_recommended`, `full_reasons`). `risk_model`
  `three_level` is not a trigger by itself. L5 to L7 (a CSA "high process risk"
  determination, auditor or customer expectations, previous audit findings)
  cannot be read from the answers and are decided in the lite plan.
- The three optional config keys `agent_qms_write`, `ai_output_as_evidence` and
  `agent_untrusted_with_secrets` (booleans, absent = false) are asked by the
  wizard after the tools.
- `render_package()` also refuses, unless `force`, to write into a directory
  that holds per-tool documents of the other profile (their shared documents
  have the same names). `render` prints a notice for other Markdown files in
  the output directory that it did not write. Render each profile into its own
  directory; templates print the full-profile command with `{{config_file}}`
  and `--out output-full`.
- Profile variables (global scope, generated table below): `profile` (`lite`
  or `full`, the profile being rendered), `profile_lite` and `profile_full`
  (booleans for `{{#profile_lite}}...{{/profile_lite}}` blocks in text shared
  by both sets), `full_recommended`, `full_reasons`, `lite_blocked` and
  `lite_blockers` (independent of the profile rendered), `config_file` and
  `owner_is_executor` (tool owner and executor are the same role; the lite
  report then has the approver do the technical review). Each template directory holds a
  complete set; there is no inheritance between `templates/lite/` and
  `templates/full/`, so a change to a shared ID, command or acceptance
  criterion is made in both.
- User-facing comparison, the conditions that require full with their
  anchors, the residual risk lite accepts and the upgrade path:
  `docs/lite-vs-full.md`. Keep it in step with section 2 of the lite plan and
  with `full_profile_reasons()`.

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
4. `package.render_package()` takes the templates of the profile
   (`templates/<profile>/`; `--templates DIR` replaces the directory, and a
   directory with `lite/` and `full/` subdirectories selects the profile's
   one), renders every template in memory and writes files only if all of them
   rendered:
   - `00-<name>.md.tmpl` -> `output/00-shared/<name>.md`, context stack `[global]`;
   - any other `NN-<name>.md.tmpl` -> `output/<TOOL_ID>/NN-<name>.md`, once per
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
if pinned, the exact pinned model (must match an approved entry), then the
three yes / no questions behind the hard stops L2, L8 and L9 (with a hint when
the contexts or surfaces make one relevant), and last the profile: the wizard
shows the recommended profile with its reasons and the triggers it cannot see,
and defaults to the recommendation (`full` stays the default when an existing
config already says `full` or has no `profile` key). With a hard stop it sets
`full` without asking. `init --profile X` skips the question. Defaults are shown in brackets; Enter
accepts. Multi-select answers are comma-separated keys or option numbers. An
existing valid config supplies the defaults. `init --defaults` refuses to
overwrite a different existing config unless `--force`.

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

- Location: `templates/full/` or `templates/lite/`; a template anywhere else
  is never rendered (a test rejects it).
- Name: `NN-lowercase-words.md.tmpl`; `00-` = shared document, anything else
  = per-tool document (`01`-`08` map to `doc_id_01`-`doc_id_08`; in lite,
  `doc_id_01` to `doc_id_03` are the plan, the test record and the report).
- Use only the variables listed below. Never hard-code model names: use
  `{{#approved_models}}{{.}}{{/approved_models}}` and `{{pinned_model}}`.
- `tests/test_templates.py` renders every template of BOTH profiles across a
  matrix of 156 configs (every tool type, csa / three_level, all contexts /
  only `code_product` / only `doc_drafting`, in use or not, GxP on/off,
  envelope / pinned, github / gitlab / other; full adds a config without the
  `profile` key) and also checks file names, hard-coded model ids and the
  de-identification rules. Both profiles are required: an empty
  `templates/full/` or `templates/lite/` fails the suite, nothing is skipped.
  Run the suite before committing.
- Each profile needs at least one shared (`00-`) and one per-tool template.
- `tests/test_lite.py` checks the lite file set, the ID subset, the tests in
  the test record, the requirement subset, the full-profile warning and the
  hard stops (refusal without `--force`, banner with it, no pinned-policy
  branches in the lite templates), that every lite test ID is in the
  differences table of `docs/lite-vs-full.md`, and the word budget: with the
  default config, each lite per-tool package at most 5,000 words in total and
  each lite shared document at most 1,200 words (whitespace-separated tokens of
  the rendered Markdown).
- `tests/test_style.py` enforces the kit's style rules: no section sign in
  any tracked text file or rendered default package (write "ISO 13485:2016
  clause 4.1.6", "21 CFR 820.10", "MDR Article 10(8)", "section 3 of this
  plan"); no times or durations in README.md; no effort or speed claims in
  GUIDE.md and `docs/`; the "No shadow AI" message in README and GUIDE and
  the rule in both work instructions; GUIDE.md at most 1,250 words; no
  collision between lite and full document IDs; and no em dash in any
  tracked text file or rendered default package.
- The repository-wide de-identification test in `tests/test_templates.py` is
  skipped unless a pattern file exists (`tests/deid-local.txt`, git-ignored, or
  `$KIT_DEID_PATTERNS`; a `$KIT_DEID_PATTERNS` naming a missing file fails);
  CI does not have it. It scans every text file outside `.git`, `__pycache__`
  and `output`, `tests/` included, except the pattern file. Maintainers run it
  with the pattern file before every release.
- `examples/acme-medsoft/` holds the fictional example of the FULL profile
  (`"profile": "full"`): `kit.config.json`, the package rendered from it and
  then filled in by hand as if executed. After a
  template change, render the config into a scratch directory (`python3 kit.py
  render --config examples/acme-medsoft/kit.config.json --out /tmp/acme`) and
  carry the relevant changes into the filled files by hand: rendering straight
  into `examples/acme-medsoft/package` overwrites the filled-in content.
- `examples/acme-medsoft-lite/` is the same for the LITE profile
  (`"profile": "lite"`, `today` 2026-10-19, no trigger for full); maintain it
  the same way (`--out /tmp/acme-lite`). Illustrative SHA-256 values in both
  examples are the SHA-256 of the evidence path.
- `tests/test_examples.py` checks both examples: valid frozen config and its
  profile, the rendered file set with the same first heading (document ID and
  title) as the kit renders, the banner on every Markdown file, no
  leftover template syntax, `[fill in` / `______` / `[yes/no` placeholders or
  real model names, a filled nonconformity reference in the interim-use block
  when `already_in_use` is true (full: `04-validation-plan.md` section 12;
  lite: `01-validation-plan.md` section 9), and for lite a decision on each of
  L1 to L9 without the full-profile warning.
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
| `profile` | str | Validation profile rendered: `lite` or `full` (config key `profile`, overridden by `--profile`; a config without the key renders as `full`). |
| `profile_lite` | bool | `profile` is `lite` (templates/lite/). |
| `profile_full` | bool | `profile` is `full` (templates/full/). |
| `full_recommended` | bool | The answers contain a trigger for the full profile: a hard stop (`lite_blocked`), context `doc_drafting` (L3) or GxP (L4). Independent of the profile rendered. |
| `full_reasons` | list[str] | One short sentence per trigger behind `full_recommended`, starting with its L number; empty list when none (scalars: use `{{.}}`). |
| `lite_blocked` | bool | The answers contain a hard stop for the lite profile: model policy `pinned` (L1), context `agents_qms` or `agent_qms_write` (L2), `ai_output_as_evidence` (L8), `agent_untrusted_with_secrets` (L9). A lite render then needs `--force` and is not valid for release. |
| `lite_blockers` | list[str] | The reasons of `full_reasons` that are hard stops (scalars: use `{{.}}`). |
| `config_file` | str | Config file as given to `render` / `init` (`kit.config.json` when rendered without a file). |
| `reg_iso13485` | bool | ISO 13485:2016 (clause 4.1.6, software validation) |
| `reg_fda_qmsr` | bool | FDA QMSR (21 CFR Part 820, incorporates ISO 13485) |
| `reg_gxp` | bool | GxP: EU GMP Annex 11 + 21 CFR Part 11 |
| `reg_iso27001` | bool | ISO/IEC 27001 (cross-references) |
| `reg_iso42001` | bool | ISO/IEC 42001 (cross-references) |
| `role_executor` | str | Role that executes the validation. |
| `role_approver` | str | Role that approves the validation (always different from the executor). |
| `role_tool_owner` | str | Role that owns the tool and its configuration. |
| `owner_is_executor` | bool | `role_tool_owner` and `role_executor` are the same role (small team: the approver does the technical review). |
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
| `agent_qms_write` | bool | L2: Can an agent, interactive or autonomous, write to QMS systems outside the code-host gate (eQMS, issue tracker or document system, for example through MCP or an API)? (optional config key, default false). |
| `ai_output_as_evidence` | bool | L8: Are AI-generated tests or other AI output used as verification evidence or as QMS records without independent review of their adequacy? (optional config key, default false). |
| `agent_untrusted_with_secrets` | bool | L9: Does an agent that holds write credentials or secrets beyond the pull-request path read untrusted content (issues or comments from outside contributors, web pages, third-party MCP results)? (optional config key, default false). |
| `risk_model` | str | `csa` or `three_level`. |
| `risk_csa` | bool | `risk_model` is `csa` (high / not high process risk). |
| `risk_three` | bool | `risk_model` is `three_level` (low / medium / high). |
| `already_in_use` | bool | Tool already in use: add retrospective validation and interim-use justification. |
| `periodic_review_months` | int | Periodic review interval in months. |
| `doc_id_wi` | str | Doc ID of the shared work instruction (tool token `GEN`; full: nn `01`; lite: nn `L01`). |
| `doc_id_discovery` | str | Doc ID of the shared tool-discovery checklist (tool token `GEN`; full: nn `02`; lite: nn `L02`). |
| `doc_id_gates` | str | Doc ID of the shared code-host gate qualification (tool token `GEN`, nn `03`): OQ-01 to OQ-07 and OQ-12 executed once per code host for all tools (full profile only). |
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
| `doc_id_01` | str | Doc ID of per-tool document 01 (full: Inventory and intended use, nn `01`; lite: Validation plan, nn `L01`). |
| `doc_id_02` | str | Doc ID of per-tool document 02 (full: Requirements, nn `02`; lite: Test record, nn `L02`). |
| `doc_id_03` | str | Doc ID of per-tool document 03 (full: Risk assessment, nn `03`; lite: Validation report, nn `L03`). |
| `doc_id_04` | str | Doc ID of per-tool document 04 (full: Validation plan). |
| `doc_id_05` | str | Doc ID of per-tool document 05 (full: Test protocol). |
| `doc_id_06` | str | Doc ID of per-tool document 06 (full: Configuration baseline). |
| `doc_id_07` | str | Doc ID of per-tool document 07 (full: Validation report). |
| `doc_id_08` | str | Doc ID of per-tool document 08 (full: Change and revalidation). |

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
