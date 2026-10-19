> FICTIONAL EXAMPLE, invented for illustration only. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are made up to show what an executed lite package looks like. Model ids are placeholders. Each person signs in the eQMS, shown here only as "[signed in eQMS]".

# Example: Acme MedSoft, lite profile (fictional)

This folder shows a **lite** validation package after execution: the documents the kit rendered with `"profile": "lite"`, then filled in by people as the work was done.

It's a separate scenario from the full-profile example in [../acme-medsoft/](../acme-medsoft/README.md). Same fictional company, narrower intended use: AI stays out of controlled documents, so none of the conditions for the full profile applies.

Compare the 2 to see what lite leaves out ([docs/lite-vs-full.md](../../docs/lite-vs-full.md)). And don't copy its results into your own records.

| Item | Value |
|---|---|
| Organisation | Acme MedSoft, a fictional manufacturer of a Class II SaMD (FDA 510(k)), EU MDR planned |
| Profile | `lite`: per tool `01-validation-plan`, `02-test-record`, `03-validation-report` (document IDs `ACME-VAL-<TOOL>-L01` to `-L03`); shared work instruction `ACME-VAL-GEN-L01` and tool-discovery checklist `ACME-VAL-GEN-L02`. Lite IDs never repeat a full-profile ID |
| Tools | Claude Code (`CLAUDE`: local CLI and an advisory PR review bot) and OpenAI Codex (`CODEX`: local CLI only), both under the envelope model policy |
| Approved models | `anthropic-model-a`, `anthropic-model-b` / `openai-model-a` (placeholder ids) |
| Contexts of use | `code_product`, `code_tooling`, `pr_review`; no `doc_drafting`, no `agents_qms`, no hard stop (L1, L2, L8, L9) |
| Code host / risk model | GitHub / FDA CSA: **not high process risk**, crediting the tested human gate and required CI checks as an interpretation that holds while PQ-02 passes (plan section 5) |
| Starting point | Both tools already in use: interim use with nonconformities NC-2026-041 and NC-2026-042 and CAPA-2026-015, with a look-back over the whole period (plan section 9) |
| Config | [kit.config.json](kit.config.json) (`today` fixed to 2026-10-19 so the render is reproducible) |
| Package | [package/](package/): `00-shared/`, `CLAUDE/`, `CODEX/` |

## Story in 1 table

| Date | What happened | Where to look |
|---|---|---|
| 2026-01-12 / 2026-06-15 | First known use of Claude Code / OpenAI Codex, without validation | `*/01-validation-plan.md` section 9 |
| 2026-10-19 | Package rendered; tool discovery (finds an unregistered AI completion extension, removed the same day); readiness checklist; interim controls and look-back (`check_github_gates.py --commits-since`, audit-log export, model ids, released versions); suite SHA-256 fixed with `run_admission.py --list`; work instruction issued and all users trained; interim use approved | `00-shared/`, `*/01-validation-plan.md` sections 8 to 10 |
| 2026-10-20 | Plans and test records approved **before** the first test (approval records QMS-APR-2026-1187 and -1188); profile decision "lite" recorded against L1 to L9 | `*/01-validation-plan.md` sections 2 and 11 |
| 2026-10-21 | IQ-03 for both tools; code-host gate tests OQ-01 to OQ-07 once for both tools (`evidence/GEN/`, recorded in the Claude Code record), plus the steps where each agent acts | `CLAUDE/02-test-record.md`, `CODEX/02-test-record.md` |
| 2026-10-21 | 1 major deviation: IQ-03 finds the review action referenced by a tag in 1 repository, where the approved commit SHA belongs; corrected under a change record | `CLAUDE/02-test-record.md` section 3 (DEV-CLAUDE-01) |
| 2026-10-22 | Re-test of the deviation; OQ-08 and OQ-09; OQ-10 (the allow-list refuses another model for Claude Code; Codex is monitored only); MA-01 on every approved model | `*/02-test-record.md` |
| 2026-10-23 | Release decisions: both tools approved with conditions, until the PQ-01 and PQ-02 addendum is signed | `*/03-validation-report.md` section 4 |
| 2026-10-26 to 2026-11-20 | PQ-01 on the released configuration; PQ-02 re-review sample (pending in this example) | `*/02-test-record.md`, PQ-01 and PQ-02 |
| 2026-11-27 | Planned signed PQ-01 and PQ-02 addendum to both reports | `*/03-validation-report.md` section 4 |

For 2 tools that share repositories, the work before release ran from 2026-10-19 to 2026-10-23, with the prerequisites already in place (managed configuration, protected sandbox, SOUP check, push protection, accounts). That's the record of this fictional case, and your own dates will follow your own situation.

## People (fictional)

| Role in the config | Name | Does |
|---|---|---|
| Validation Engineer (executor) | Alex Example | Writes the plans, executes the test records, drafts the reports |
| Head of QA (approver) | Sam Sample | Approves interim use, plans and records before execution, the admissions and the release decisions; closes deviations |
| Engineering Lead (tool owner) | Jordan Demo | Owns configuration, the work instruction and vendor monitoring; technical review of the reports; reviews the PQ-01 outliers and re-reviews the PQ-02 sample (a different person from the approver) |
| Users A / B / C, admin | Dev One, Dev Two, Rev One, Rev Two, Casey Admin | Authors, reviewers and admin in the gate tests (real accounts; sandbox-only test accounts would also do for OQ-02 to OQ-07) |

## What is deliberately shown

- The profile decision in plan section 2, with a reason for each of L1 to L9. That includes the hard stops L8 and L9 that the kit flags from the contexts and surfaces, and the ones the kit can't read from the answers (CSA determination, notified body or customer expectations, audit findings). The plans cite the procedure clause that adopts the lite profile.
- A CSA "not high process risk" determination for product code that rests on the tested gate and CI, marked as an interpretation and tied to PQ-02. The full example determines the same product code as "high process risk".
- Either determination needs its rationale on record. If the rationale stops holding, L5 sends the team to the full profile.
- The tool's known guardrail limitations in plan section 5, with the ones accepted before execution and their compensating controls.
- A look-back over the interim period that claims only what it can show: every commit matched to a merged PR (2 pre-ruleset admin commits found), a bypass-history gap recorded, models used inside, outside or unknown, and the released device versions assessed.
- The MA-01 suite, tasks and variant fixed in the plan before execution, with the suite SHA-256 printed by `run_admission.py --list`.
- The code-host gate tests executed once for 2 tools that share repositories and recorded in the first tool's record. The second tool's record cites them and adds only the steps where that agent acts.
- 1 major deviation found by IQ-03 (a guardrail test), corrected under change control and re-tested before release.
- A model list that's enforced and tested (OQ-10) for 1 tool, and only monitored for the other, with a grace period accepted in the plan before execution.
- Steps that don't apply marked N/A with the reason (no agent identity on the code host, no cloud tasks).
- The executed test record linked to the approved version by approval record and SHA-256, with a diff showing that only results changed. Each person signs in the eQMS ("[signed in eQMS]").

## What isn't real

- Evidence files are left out. Their names follow the naming of the kit's scripts; their SHA-256 values are illustrative, computed from the file names.
- Contract, supplier, procedure, change, deviation, nonconformity, CAPA, training, approval and log references (`ACME-...`, `CR-...`, `NC-...`, `CAPA-...`, `TR-...`, `QMS-APR-...`, `IT-CHG-...`) are fictional.
- Observations about vendor behaviour that the vendors don't document are illustrative: establish your own empirically.

## Re-creating it

```bash
python3 kit.py render --config examples/acme-medsoft-lite/kit.config.json --out /tmp/acme-lite-check
```

This renders the empty lite package. The filled-in content was added by hand afterwards, so rendering straight into `examples/acme-medsoft-lite/package` would overwrite it.
