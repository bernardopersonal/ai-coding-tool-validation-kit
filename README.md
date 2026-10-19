# AI Coding Tool Validation Kit

**Using Claude Code or Codex in a regulated team? Good. Is it validated?**

**Why it matters.** Tools that write or change your product code, tests or quality records have a direct impact on quality. Validating them is neither a side issue nor paperwork: ISO 13485:2016 clause 4.1.6 requires validation of QMS software before initial use and, as appropriate, after changes, proportionate to risk, and auditors are starting to ask. Do it properly and your QA/RA lead will be enormously grateful.

**No shadow AI.** AI tools the organisation does not know about (unsanctioned tools, personal accounts, AI-assisted changes nobody declared) cannot be validated, controlled or defended in an audit. Declare every tool, use organisation accounts, and label AI-assisted changes. The tool-discovery checklist and `checks/find_ai_footprint.py` help you find what is already in use.

A ready-to-run kit to validate AI coding assistants as QMS and development software under ISO 13485:2016 (and the FDA QMSR, which incorporates ISO 13485 by reference), with a risk-based, CSA-style approach. A wizard renders a validation package for your organisation, lite or full. Scripts collect the evidence. A model admission suite keeps you validated when the vendor ships a new model.

Version 0.2.0 · Python 3.9+ standard library only · Claude Code and OpenAI Codex supported out of the box, GitHub Copilot, Cursor and other tools through [docs/adapting-other-tools.md](docs/adapting-other-tools.md).

## Two profiles: lite and full

| | Lite | Full |
|---|---|---|
| Documents | 3 per tool (plan, test record, report) + 2 shared (work instruction, tool discovery) | 8 per tool (inventory to change and revalidation) + 3 shared (adds the code-host gate qualification) |
| Tests | 12 test records covering 14 IDs: IQ-03, OQ-01 to OQ-10 (OQ-03 with OQ-06 and OQ-08 with OQ-09 share a record), MA-01, PQ-01, PQ-02 | IQ-01 to IQ-05, OQ-01 to OQ-13, OQ-20 / OQ-30 by context, OQ-40 when the agent reads untrusted content, MA-01, RV-01 when already in use, PQ-01, PQ-02 |
| Depth | Smallest record set that still proves every gate and the model allow-list negatively; one compact record per test; one engineer, one approver and sandbox test accounts | Audit depth: failure-mode analysis, per-step records, separate baseline and change documents |
| When to use | Every AI output is independently verified downstream by qualified human review and required CI, and none of the conditions L1 to L9 applies | The AI output itself is a control or evidence, agents writing to QMS systems, AI-drafted controlled records, agents with secrets reading untrusted content, high-impact GxP, or more depth expected |

Lite uses the requirement and test IDs and the commands of full. Under each shared ID the lite acceptance criterion equals or exceeds full's, and full adds tests and steps ([docs/lite-vs-full.md](docs/lite-vs-full.md)), so lite evidence is reused when you move to full. Lite documents have their own document IDs (per tool `...-L01` to `-L03`, shared `...-GEN-L01` and `-GEN-L02`), so no ID names two documents and the full documents supersede the lite ones on upgrade.

**How to choose.** New configs default to lite; the wizard recommends a profile from your answers. Hard stops require full, and `render` refuses lite for them: a pinned model policy (L1), `agents_qms` or any agent write path to QMS systems outside the code-host gate (L2), AI output used as verification evidence without review of its adequacy (L8), and an agent with write credentials or secrets that reads untrusted content (L9). Full is also required for `doc_drafting` without independent verification of each draft (L3), high-impact GxP use (L4), a CSA "high process risk" determination (L5), a notified body, FDA or customer expecting more depth (L6), or audit findings on the tool (L7). The lite plan records a decision on each and warns prominently when your answers contain one. Residual risk and upgrade path: [docs/lite-vs-full.md](docs/lite-vs-full.md).

## What "validated" means here

You cannot qualify a large language model, and you do not need to. The kit validates three things:

1. **The intended use.** Who uses which tool, on which surface, for what, where, and who approves the result.
2. **The guardrails around the tool.** Approval gates, required CI checks, permissions, sandbox, managed configuration, accounts, attribution. Model-independent, they are the core of the validation.
3. **Verification of the output.** Every AI-assisted change is reviewed by a qualified human and passes CI before it reaches a protected branch. "You own every line you merge."

The principles behind every document:

- Assurance is proportionate to risk (FDA CSA, ISO/TR 80002-2, GAMP 5 2nd ed.): scripted tests where process risk is high, unscripted tests elsewhere.
- Acceptance criteria are fixed **before** execution; expected results are computed independently first.
- The tool never executes, concludes or approves its own validation. Executor and approver differ, and people sign for themselves.
- Configuration is baselined and change-controlled; behaviour is monitored, because models change without a version bump.
- Gates are proven with **negative** tests (merge without approval, direct push, bot approval, self-approval, admin bypass) on more than one repository.
- Evidence comes from exports (API JSON, logs, SHA-256 hashes), not only screenshots.
- The binding control lives server-side (code host and CI), not in the agent's local configuration.
- If the tool is already in use, say so: retrospective validation plus a documented interim-use justification.

## Models change often: three tiers

The validation unit is **tool + vendor + surface + context of use**, not a single model. Each tool has an approved *model envelope* (ids or family patterns), handled in both profiles as a predetermined change protocol:

1. **Initial validation** (once per tool and vendor): IQ/OQ/PQ of the guardrails, plus the admission suite MA-01 on every model in the envelope.
2. **Model admission** (new id matching a pattern pre-authorised in the plan): rerun MA-01 headlessly. Pass: a short admission record, and the exact id joins the allow-list, enforced where the tool can enforce it.
3. **Re-baseline** (new model family, guardrail-relevant release, new surface or context, admission failure, vendor terms change): MA-01 plus a targeted OQ subset. New vendor: new initial validation.

Details: [docs/model-change-protocol.md](docs/model-change-protocol.md).

## Quick start

You need Python 3.9+, a clone of this repository, and for the checks the `gh` CLI (or a `GITHUB_TOKEN`) with read access to a repository.

**1. Render your package**

```bash
python3 kit.py init                   # wizard: organisation, roles, tools, models, contexts, risk model, profile
# or: python3 kit.py init --defaults  # fictional example answers (Acme MedSoft), lite profile
python3 kit.py render --config kit.config.json --docx                            # re-render; .docx needs pandoc
python3 kit.py render --config kit.config.json --profile full --out output-full  # --profile lite|full overrides the config
```

Documents land in `output/`; render each profile into its own directory (`render` refuses to overwrite the other profile's documents, and refuses lite for a hard stop, unless `--force`). `init --profile lite|full` stores the profile without asking; a 0.1.0 config (no `profile` key) renders as full. `kit.config.json`, `output/` and `output-*/` are git-ignored: they belong in your QMS.

**2. Explore with the checks**

```bash
export KIT_OPERATOR="Your Name"     # recorded in every evidence file
python3 checks/find_ai_footprint.py --path REPO_DIR --out evidence/_exploratory/   # AI tools you may not know about
python3 checks/capture_baseline.py --tool claude_code --repo REPO_DIR --out evidence/_exploratory/
python3 checks/check_github_gates.py --repo OWNER/REPO --branch main --prs 20 --out evidence/_exploratory/
python3 admission/run_admission.py --tool claude_code --model <model-id> --runs 3 --out evidence/_exploratory/ --dry-run
```

Exploratory runs are not test evidence. IQ-03, OQ-01 and MA-01 are re-run after approval, into `evidence/<TOOL>/<TEST-ID>/`. For a tool already in use, file the check of the interim controls under `evidence/<TOOL>/INTERIM/`.

Use `--tool codex` for Codex. Every script has `--help`, writes JSON and Markdown evidence (UTC timestamp, operator, machine, SHA-256) and exits non-zero when a check fails. The admission dry run calls no model; drop `--dry-run` with your own vendor credentials. The suite never runs in this kit's CI.

**3. Execute**

Prepare tool discovery, the drafts and a sandbox protected like production (`checks/mirror_protection.py`); the lite plan has a readiness checklist. The approver approves the plan and the test record (lite) or protocols (full) *before* the first test. Execute IQ, OQ and MA-01; `checks/canary/` drives the negative gate tests. Tools sharing repositories run the code-host gate tests once (lite: in the first tool's record, `evidence/GEN/`; full: `00-shared/code-host-gate-qualification.md`). PQ-01 and PQ-02 run after release and are reported in a signed addendum.

**4. Sign the report**

The validation report (lite `03`, full `07`) carries the release decision (approved, with restrictions, or not approved), "approved with conditions" until the PQ addendum is signed. People sign it themselves in your eQMS or with an e-signature. The AI tool does not draft the conclusion without independent review, and the report states who wrote it.

New to the topic? Read [GUIDE.md](GUIDE.md). Executed fictional packages: [examples/acme-medsoft-lite/](examples/acme-medsoft-lite/README.md) (lite) and [examples/acme-medsoft/](examples/acme-medsoft/README.md) (full).

## What you get

```
README.md, GUIDE.md          this file; a two-page guide for QA/RA leads
README_DEV.md                template syntax, variables and profiles, how the engine works
CHANGELOG.md, CONTRIBUTING.md, LICENSE, LICENSE-docs
kit.py, kit/                 CLI (init, render, example-config, vars), wizard, strict template engine
templates/lite/              *.md.tmpl of the lite profile (syntax: README_DEV.md)
templates/full/              *.md.tmpl of the full profile
checks/                      evidence scripts (details: checks/README.md)
  check_github_gates.py        protection, rulesets, Actions approval setting, review record of merged PRs
  capture_baseline.py          tool versions, config and instruction files, SHA-256 hashes
  find_ai_footprint.py         agent config files and AI workflows in a repo, org app installations
  canary/                      throwaway PR that must NOT merge without approval
  mirror_protection.py         copy the gate configuration to a sandbox repository
  soup_gate.py, client_regression.py   reference SOUP gate; client regression on a candidate version
admission/                   model admission suite MA-01: runner, tasks, fixtures
tools/claude-code/, tools/codex/   verified configuration examples and notes
docs/                        lite vs full, regulatory mapping, model-change protocol, adapting other tools
examples/                    filled fictional packages (acme-medsoft-lite/, acme-medsoft/), workflows, PR template
tests/                       unit tests (python3 -m unittest discover -s tests)
.github/workflows/ci.yml     runs the tests and smoke renders on Python 3.9 and 3.12
```

The rendered package, one folder per tool (folder = tool ID). Lite:

```
output/
  00-shared/ai-assisted-development-work-instruction.md, tool-discovery-checklist.md
  CLAUDE/
    01-validation-plan.md      inventory, intended use, L1 to L9, risk and known limits, REQ subset, three tiers, readiness
    02-test-record.md          IQ-03, OQ-01..10, MA-01, PQ-01, PQ-02 with commands and criteria
    03-validation-report.md    results, model list, release decision, signatures, change triggers, admission record
  CODEX/ ...
```

Full:

```
output-full/
  00-shared/                   the same two, plus code-host-gate-qualification.md (OQ-01..07, OQ-12 once)
  CLAUDE/
    01-inventory-and-intended-use.md   02-requirements.md (REQ-01..17)   03-risk-assessment.md
    04-validation-plan.md              05-test-protocol.md               06-configuration-baseline.md
    07-validation-report.md            08-change-and-revalidation.md
  CODEX/ ...
```

## What the kit checks

| Control | How | Lite / full documents |
|---|---|---|
| Use before validation | Interim-use justification with nonconformity and CAPA; release decision | 01, 03 / 04, 07 |
| Unregistered AI tools | Discovery checklist and `checks/find_ai_footprint.py` | 00-shared / 00-shared, 08 |
| Model changes | Envelope, pre-authorised patterns, allow-list test OQ-10, MA-01, triggers | 01, 02, 03 / 02, 04, 05, 08 |
| Strength of the human gate | Negative tests OQ-02 to OQ-07 on 2 repositories when available; OQ-01; PQ-01; reviewer effectiveness PQ-02 | 02 / 00-shared code-host record, 05 |
| Configuration control | Hashed baseline (IQ-03) | 02 / 05, 06 |
| Signatures and independence | Signatures by the people themselves; authorship and independence statement | 03 / 07 |

## Regulatory mapping (summary)

Document numbers are those of the full profile; the lite plan, test record and report condense the same content.

| Framework | What it asks | Where the kit answers |
|---|---|---|
| ISO 13485:2016 clause 4.1.6 | Documented procedure; validate QMS software before initial use and after changes; risk-proportionate; records | The whole package; 04, 05, 07, 08 |
| FDA QMSR (21 CFR 820, in force 2 Feb 2026) | ISO 13485 incorporated by reference (21 CFR 820.7, 820.10); the former 21 CFR 820.70(i) no longer exists | Same documents; cite ISO 13485 clause 4.1.6 "as incorporated by 21 CFR 820.10" |
| FDA CSA guidance (final Sep 2025, revised Feb 2026) | Intended use, risk-based approach, assurance activities, lean record | 01, 03 risk determination, 04/05 scripted vs unscripted, 07; the lite profile |
| ISO 13485 clauses 4.2.4, 4.2.5, 6.2, 7.4 | Document and record control, competence, supplier control | 06 hashes, evidence rules, work instruction and training, IQ-05 |
| ISO/TR 80002-2:2017, GAMP 5 2nd ed., ISPE GAMP AI guide | Critical thinking, risk-based toolbox, life cycle, category | 01 GAMP category, 03, 04, 08 |
| IEC 62304 clauses 5.1.4, 5.1.10, 8 | Tools in the development plan (class C), tool settings under configuration control | 01, 06, 08 |
| 21 CFR Part 11 (FDA QMSR and GxP options) | Electronic records and signatures | Evidence rules, signature tables (name, date and time, meaning) |
| EU GMP Annex 11 (GxP option) | Computerised systems in medicinal-product GMP | Added when the GxP option is selected |

Clause by clause, requirement and interpretation marked separately: [docs/regulatory-mapping.md](docs/regulatory-mapping.md).

## Tool-specific notes

- [tools/claude-code/](tools/claude-code/README.md): managed settings for a validated state, per-surface delivery caveats, known guardrail limits.
- [tools/codex/](tools/codex/README.md): user defaults versus admin-enforced requirements, recent breaking changes, known guardrail limits.
- [docs/adapting-other-tools.md](docs/adapting-other-tools.md): GitHub Copilot, Cursor and any other tool, including the admission runner.

Vendor facts were verified against vendor documentation and source code on 2026-10-18. Re-verify before you rely on a setting. Where a fact could not be verified, the kit says "verify against the vendor's current documentation" and does not guess.

## Disclaimer

This kit is not legal advice. It is a starting point, so adapt it to your QMS: your software validation procedure, document control, e-signature system and risk method take precedence over anything here. Using the kit does not by itself make a tool validated. People executing, reviewing and approving the records do.

## Licence

- Code (`kit.py`, `kit/`, `checks/`, `admission/`, `tests/`, configuration examples in `tools/` and `examples/`): [MIT](LICENSE).
- Templates and documentation (`templates/`, `docs/`, `README.md`, `GUIDE.md`, other Markdown files): [CC BY 4.0](LICENSE-docs).

Contributing: [CONTRIBUTING.md](CONTRIBUTING.md). Changes: [CHANGELOG.md](CHANGELOG.md). Developer notes: [README_DEV.md](README_DEV.md).

---

Maintained by Bernardo Plaza - regulatory, quality and security for software medical devices.
