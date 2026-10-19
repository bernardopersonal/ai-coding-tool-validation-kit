> FICTIONAL EXAMPLE - not a real validation record. Acme MedSoft, its people, repositories, results, evidence file names and SHA-256 values are invented to show what an executed package looks like. Model ids are placeholders, not real model names. Signatures are applied by each person in the eQMS and are shown here only as "[signed in eQMS]".

# Example: Acme MedSoft (fictional)

This folder shows what a validation package looks like **after** it has been executed: the documents rendered by the kit, then filled in by people as the work was done. Use it to calibrate the level of detail an auditor expects. Do not copy its results into your own records.

| Item | Value |
|---|---|
| Organisation | Acme MedSoft, a fictional manufacturer of a Class II SaMD (FDA 510(k)), EU MDR planned |
| Tools | Claude Code (tool ID `CLAUDE`) and OpenAI Codex (tool ID `CODEX`), both under the **envelope** model policy |
| Model envelope | `anthropic-model-a`, `anthropic-model-b` / `openai-model-a`, `openai-model-b` (placeholders, not real model names) |
| Contexts of use | `code_product`, `code_tooling`, `pr_review`, `doc_drafting` |
| Code host / risk model | GitHub / FDA CSA (high process risk, driven by product code) |
| Starting point | Both tools were already in use: retrospective validation with an interim-use justification, a nonconformity for use before validation (NC-2026-031, NC-2026-032) and CAPA-2026-012 |
| Config | [kit.config.json](kit.config.json) (`today` fixed to 2026-10-18 so the render is reproducible) |
| Package | [package/](package/): `00-shared/` (work instruction, tool discovery, code-host gate qualification), `CLAUDE/`, `CODEX/` |

The answers differ from `python3 kit.py init --defaults` on purpose: the full profile (`"profile": "full"`), placeholder model ids, four contexts of use, a PRRC, ISO/IEC 27001 cross-references and a 6-month periodic review. A lite-profile counterpart for a narrower intended use of the same fictional company is in [../acme-medsoft-lite/](../acme-medsoft-lite/README.md).

## Story in one table

| Date | What happened | Where to look |
|---|---|---|
| 2026-01-12 / 2026-06-15 | First known use of Claude Code / OpenAI Codex, without validation | `*/04-validation-plan.md` section 12 (NC-2026-031, NC-2026-032) |
| 2026-10-02 | Vendor monitoring routine starts (weekly) | `*/08-change-and-revalidation.md` section 5, OQ-13 |
| 2026-10-12 to 2026-10-14 | Preparation: tool discovery and survey; drafts of 01 to 05 and of the code-host gate qualification; sandbox protection copied from production with `checks/mirror_protection.py` | `00-shared/tool-discovery-checklist.md`, `00-shared/code-host-gate-qualification.md` |
| 2026-10-18 | Package rendered with the kit | `kit.config.json` |
| 2026-10-19 | Plans, protocols and the gate qualification approved **before** execution; OQ-20 probe sheets sealed; work instruction issued and all users briefed; interim controls effective | `*/04-validation-plan.md` sections 12 and 15 |
| 2026-10-20 | IQ-01 to IQ-05 and the configuration baselines; Actions retention raised to 400 days | `*/05-test-protocol.md` section 6, `*/06-configuration-baseline.md` |
| 2026-10-21 | Code-host gate qualification once for both tools (server-side merge attempts, also as admin); tool-specific agent attempts | `00-shared/code-host-gate-qualification.md`, `*/05-test-protocol.md` section 7 |
| 2026-10-22 | Local guardrails, overrides, model envelope, provenance, monitoring routine (OQ-13), citation probes, prompt injection; MA-01 on both models of each tool; RV-01 retrospective review of the in-use period | `*/05-test-protocol.md` sections 7 to 9 |
| 2026-10-22 | **One major deviation**: the provenance cross-check (OQ-11) finds one undeclared AI-assisted PR. A second sample passes, but the failure mode is unchanged, so the deviation stays open with a compensating control until the CI check CR-2026-047 is deployed | `CLAUDE/05-test-protocol.md` section 11 (DEV-CLAUDE-01), `CLAUDE/07-validation-report.md` sections 7 and 13 |
| 2026-10-23 | Release decisions: Claude Code **approved for intended use** with conditions (PQ addendum; DEV-CLAUDE-01 accepted open); OpenAI Codex **approved with restrictions** (cloud agent only on non-product repositories until the ISO 13485 clause 4.1.5 terms review of cloud execution is approved) and the PQ condition | `*/07-validation-report.md` section 13 |
| 2026-10-22 / 23 | Admission records for the two models of each tool, executed by the Validation Engineer and approved by the Head of QA | `*/08-change-and-revalidation.md` section 7 |
| 2026-10-26 to 2026-11-20 | PQ-01 and PQ-02 on the released configuration (pending in this example) | `*/05-test-protocol.md` section 9 |
| 2026-11-27 | Planned signed PQ addendum to both reports | `*/07-validation-report.md` section 5 |

## People (fictional)

| Role in the config | Name | Does |
|---|---|---|
| Validation Engineer (executor) | Alex Example | Executes the tests, records results, drafts the reports |
| Head of QA (approver) | Sam Sample | Approves plan and protocol before execution, approves reports, admissions and the release decision |
| Engineering Lead (tool owner) | Jordan Demo | Owns configuration, baselines and vendor monitoring |
| Regulatory Affairs Manager (PRRC) | Robin Specimen | Informed of the release decisions |
| Independent reviewer (PQ-02) | Taylor Test | Post-merge re-review of sampled AI-assisted PRs (RV-01 now, PQ-02 after release) |
| Documentation Specialist (OQ-20 probe preparer) | Morgan Writer | Prepares and seals the OQ-20 probe sheets before protocol approval; does not drive the probe sessions |
| Users A / B / C, admin | Dev One, Dev Two, Rev One, Rev Two, Casey Admin | Authors, reviewers and admin in the negative gate tests |

## What is deliberately shown

- Plan and protocol approved on 2026-10-19, before the first test on 2026-10-20; executor and approver are different people; every signature is "[signed in eQMS]", never a typed name standing in for a signature.
- Use before validation treated as a nonconformity against ISO 13485 clause 4.1.6, with a CAPA on the root cause and a retrospective review (RV-01) that lists what can no longer be checked, separate from PQ.
- The code-host gates qualified once for both tools, with server-side negative tests on two repositories, including an admin identity; each tool protocol adds only its agent attempts.
- A validated version that is exactly the tested version, and a model allow-list of admitted exact ids for the tool that can enforce it.
- A known guardrail limitation reproduced instead of hidden (`sh -c` passes a Claude Code Bash deny rule; Codex hooks fail open; Codex command rules do not cover commands inside the sandbox, so the MA-01 denied-command check is N/A), each listed before execution with its compensating control.
- A model envelope that is **enforced** for one tool (managed `availableModels`, exact match) and only **monitored** for the other (no verified client-side enforcement), with detection and a time-boxed admission rule.
- A major deviation whose re-test on a new sample does not close it, accepted open at release with a compensating control and a target date.
- PQ-01 and PQ-02 after release on the released configuration, so both decisions carry a PQ condition until the signed addendum.

## What is not real

- Evidence files are not included. Their names follow the naming of the kit's scripts and of the protocol; their SHA-256 values are illustrative (computed from the file names, not from content).
- Contract, supplier, change, deviation, nonconformity, CAPA and procedure references (`ACME-...`, `CR-...`, `INV-SW-...`, `NC-...`, `CAPA-...`) are fictional.
- Observations about vendor behaviour that the vendors do not document (for example the identity used by cloud tasks) are marked as illustrative: establish your own empirically.

## Re-creating it

```bash
python3 kit.py render --config examples/acme-medsoft/kit.config.json --out /tmp/acme-check
```

This renders the empty package. The filled-in content was added by hand afterwards, so rendering straight into `examples/acme-medsoft/package` would overwrite it.
