# Lite or full: choosing the validation profile

The kit renders two profiles from the same `kit.config.json` and the same answers. **Full** is the in-depth package. **Lite** is the risk-proportionate minimum for teams where every AI output is independently verified downstream, by a qualified human reviewer and required CI checks, before it takes effect. Lite uses the requirement and test IDs and the script commands of full. Under each shared ID the lite acceptance criterion equals the full one or is stricter; full runs more steps under some IDs and adds tests (section "Differences under shared IDs"). Lite evidence is therefore reused on upgrade, and only the full-only tests and steps are added.

Proportionality is not a shortcut. ISO 13485:2016 clause 4.1.6 asks for validation activities proportionate to the risk associated with the use of the software, and the FDA Computer Software Assurance (CSA) guidance asks for assurance activities matched to process risk. Lite is what that proportionality looks like when the binding controls (human gate, required checks) sit downstream of the tool and are themselves tested. When they do not, use full.

Clause 4.1.6 also asks for documented procedures. Write the rule for choosing lite (L1 to L9 below) and the model change protocol into your software validation procedure; each lite plan cites that clause in section 1 instead of setting its own proportionality.

## Comparison

| | Lite | Full |
|---|---|---|
| Use when | AI output always passes qualified human review and required CI before it takes effect, and none of L1 to L9 applies | Any context of use, including AI output used as a control or as evidence, QMS agents, AI-drafted controlled records, GxP |
| Per-tool documents | 3: `01-validation-plan`, `02-test-record`, `03-validation-report` (document IDs `...-L01` to `...-L03`) | 8: `01-inventory-and-intended-use` to `08-change-and-revalidation` (`...-01` to `...-08`) |
| Shared documents | Work instruction, tool-discovery checklist (`...-GEN-L01`, `...-GEN-L02`) | Work instruction, tool-discovery checklist, code-host gate qualification (`...-GEN-01` to `...-GEN-03`) |
| Requirements | REQ-01 to REQ-06, REQ-08, REQ-09, REQ-10, REQ-16, REQ-17; REQ-07 with a local or CI surface; REQ-15 with PR review | REQ-01 to REQ-17 (REQ-13 and REQ-14 by context) |
| Tests | 12 test records covering 14 IDs: IQ-03, OQ-01, OQ-02, OQ-03 with OQ-06, OQ-04, OQ-05, OQ-07, OQ-08 with OQ-09, OQ-10, MA-01, PQ-01, PQ-02 | IQ-01 to IQ-05, OQ-01 to OQ-13, OQ-20 and OQ-30 by context, OQ-40 when the agent reads untrusted content, MA-01, RV-01 when already in use, PQ-01, PQ-02 |
| Risk assessment | Short determination per context and the tool's known guardrail limitations, in the plan | Failure-mode table (cause, effect, control, test) and criticality per context |
| Configuration baseline | The IQ-03 capture (script JSON and hashes) is the record | Separate baseline document with manual fields and change rules |
| Model change protocol | Three tiers in short form (plan section 8); trigger list and admission record (report sections 6 and 7) | Full protocol (plan) and change and revalidation document with the admission record |
| Records per test | One compact record: criterion, evidence, steps, result with executor, date and deviation | Objective, preconditions, steps, per-step records where the determination is high |
| People and gates | One engineer, one approver and sandbox test accounts with SSO seats; approval before execution and at release; PQ addendum after release | Executor, approver, tool owner; approval before execution and at release; PQ addendum |
| Prerequisites | Readiness checklist in plan section 10 (managed configuration, protected sandbox, CODEOWNERS, SOUP check, push protection, credentials, accounts, e-signatures) | The same, in the preparation step of the plan's schedule |

The profile applies to the whole config. If only one tool needs full, keep that tool in its own config.

For a sense of scale, see the dated story of [examples/acme-medsoft-lite/](../examples/acme-medsoft-lite/README.md): two tools sharing repositories, three role holders and five test identities, with the PQ window after the release decision. It is a fictional record, not a promise.

## When lite is not enough

Section 2 of the lite plan lists L1 to L9 and records, for each, whether it applies and why. Any "yes" means full. There are three kinds:

- **Hard stops (L1, L2, L8, L9).** Read from the answers (`model_policy` `pinned`, context `agents_qms`, `agent_qms_write`, `ai_output_as_evidence`, `agent_untrusted_with_secrets`). `kit.py render --profile lite` refuses; with `--force` it renders documents marked NOT VALID FOR RELEASE with a deviation placeholder, for example to record why lite was started. The wizard then sets the profile to full.
- **Conditional triggers (L3, L4).** Read from the answers (context `doc_drafting`, GxP). The lite plan shows a prominent warning; lite stays only if section 2 answers "no, because ..." and the approver accepts it.
- **Judgement (L5 to L7).** Decided and justified in the plan. The wizard and the plan also point at L8 when `test_generation` or `code_tooling` is selected, and at L9 when a cloud agent, PR review bot or CI surface is in use.

| # | Trigger | Why lite is not enough | Anchor |
|---|---|---|---|
| L1 | Model policy `pinned`: the AI output itself counts as a control or as evidence (AI reviewer counted as verification, LLM as judge, AI results used without independent recomputation) | Lite credits downstream human review and CI as the verification. When the AI output is the verification, nothing downstream catches its errors, so the model's behaviour must be tested and pinned, and every model change needs an OQ subset plus MA-01 before use | ISO 13485:2016 clause 4.1.6 (proportionate to the risk of use); GAMP 5 Second Edition, appendix D9 (software tools) and appendix D11 (AI/ML), and the ISPE GAMP AI guide (performance criteria for AI-enabled functions) |
| L2 | `agents_qms`, or any agent write path to QMS systems outside the code-host gate, interactive or autonomous (`agent_qms_write`), for example an MCP server or API token that writes to the eQMS, the issue tracker or a document system | Such writes never pass the code-host gate, which is the main control lite credits. Full adds bounded write scope (REQ-14) and oracle-based verification with known positives and negatives (OQ-30) | FDA CSA (interpretation): a failure that can compromise safety through a QMS record points to high process risk; GAMP 5 Second Edition, appendix M12 (critical thinking) |
| L3 | `doc_drafting` where the AI drafts controlled records without independent verification of each draft against its sources | Document approval checks a document's adequacy, not every factual claim against its source. An invented citation can enter a controlled record unnoticed. Full adds source citation and preview before write (REQ-13) and unannounced citation probes (OQ-20) | ISO 13485:2016 clauses 4.1.6 and 4.2.4; regulatory signal: the April 2026 FDA warning letter on AI-written GMP documents without quality-unit review ([regulatory-mapping.md](regulatory-mapping.md), "Signals, not requirements") |
| L4 | GxP in scope with high-impact use | Annex 11 expects the extent of validation to follow a documented risk assessment of product quality, patient safety and data integrity, and a risk-based supplier assessment. Lite records the vendor terms but does not test them (IQ-05), and has no failure-mode table | EU GMP Annex 11 clauses 1, 3, 4 and 11; 21 CFR Part 11; GAMP 5 Second Edition (GxP impact); EU GMP draft Annex 22 (consultation draft of July 2025, may change), which excludes generative AI and large language models from critical GMP applications |
| L5 | The plan's risk determination is CSA "high process risk" (three-level model: "high") | For high process risk the CSA guidance points to more rigour, such as robust scripted testing or a scripted and unscripted hybrid. Lite runs limited scripted gate tests with compact records; full adds per-step records and the complete catalogue | FDA CSA guidance (final September 2025, revised February 2026): high versus not high process risk |
| L6 | A notified body, the FDA or a customer expects more depth | Proportionality is the manufacturer's decision, but the record must convince its reader. A lite record that the auditor does not accept has to be redone as full | ISO 13485:2016 clause 4.1.6 (documented, justified approach); the customer's supplier controls under ISO 13485:2016 clause 7.4, usually in a quality agreement |
| L7 | Previous audit findings on this tool or on AI tool validation | Corrective action must remove the cause and prevent recurrence; a lighter package after a finding is hard to defend | ISO 13485:2016 clause 8.5.2; GAMP 5 Second Edition, appendix M12 (critical thinking) |
| L8 | AI-generated tests or other AI output used as verification evidence or as QMS records without independent review of their adequacy (`ai_output_as_evidence`), including internal tooling whose output is evidence | The AI output is then evidence, the L1 situation: generated tests that cannot fail, or a tool output nobody rechecks, give assurance that is not there | ISO 13485:2016 clause 7.3.6 (design verification); IEC 62304 clauses 5.5 to 5.7 (unit, integration and system testing); the L1 rationale |
| L9 | An agent that holds write credentials or secrets beyond the pull-request path reads untrusted content (`agent_untrusted_with_secrets`): CI or cloud agents, a PR bot triggered by outside comments, MCP results | The downstream gate does not catch effects that never go through a PR: secret exfiltration, writes through APIs, MCP or CI tokens. Full adds the prompt-injection smoke test OQ-40 | ISO 13485:2016 clause 4.1.6 (risk-proportionate); the kit's REQ-07 and OQ-40 rationale |

Lite is a reasonable choice for `code_product` under CSA "not high process risk" when the determination credits the tested gate and CI as independent verification and the plan records that rationale. This is an interpretation: quote the risk-determination section of the CSA guidance (February 2026 revision) in your own plan. The credit holds while PQ-02 shows that review catches defects; if the rationale does not hold, L5 applies.

## What lite deliberately leaves out

Lite keeps every test that proves a gate negatively, the model allow-list test (OQ-10), the reviewer effectiveness check (PQ-02) and every model control. It leaves out tests whose risk is covered by a control that lite does test, and accepts the residual risk below. The approver accepts it with the release decision (`03-validation-report`, section 2).

| Left out (full IDs) | Residual risk accepted | What still covers it in lite |
|---|---|---|
| IQ-01 installation and version per surface | A surface runs an untested version without being noticed | Validated version and update control in the plan inventory; IQ-03 `--compare` at periodic review; trigger T7a |
| IQ-02 account ownership and SSO (as a test) | Personal accounts in use between reviews | Inventory facts and seat reconciliation (REQ-16) in the plan; tool-discovery checklist; trigger T14 |
| IQ-04 surface to identity mapping | An agent identity writes somewhere unexpected | OQ-04 and OQ-05 on the identities used; attribution checked in OQ-01; hard stops L2 and L9 |
| IQ-05 vendor data terms (as a test) | Terms differ from the contract or change unnoticed | Terms recorded in the plan inventory against the supplier evaluation; trigger T13 |
| OQ-11 provenance label (separate historical test) | Undeclared AI-assisted changes in a larger population | Label criterion in OQ-01 and PQ-01; an undeclared change is a deviation |
| OQ-12 reversibility | A revert path is not demonstrated | Standard version control; force push and deletion refused (OQ-03) |
| OQ-13 vendor monitoring routine | A guardrail-relevant release is missed | Vendor release screening by the tool owner, logged (report section 6) |
| OQ-20 and REQ-13, where `doc_drafting` stays in lite (L3 "no") | An unsourced claim in a draft is missed | Each draft independently verified against its sources by the document owner (the L3 rationale); MA-01 citation probe per model |
| OQ-40 prompt-injection smoke test | Injected instructions produce a harmful change | Hard stop L9 for agents with credentials or secrets beyond the PR path; work instruction rule on untrusted content; review and CI catch the effect; local guardrails (OQ-08) |
| RV-01 retrospective review | Fewer historical changes examined per PR when the tool is already in use | Plan section 9 look-back (every commit matched to an approved merged PR, bypass history, models, product impact); OQ-01 sample over the period; nonconformity and CAPA mandatory |
| Separate requirements, risk, baseline and change documents | Less traceable rationale per failure mode | Condensed into the plan and report; same requirement and test IDs as full |

OQ-30 is not left out: `agents_qms` (L2) requires full.

## Differences under shared IDs

Lite criteria equal or exceed full under each shared ID; full runs more steps under some IDs, and keeps per-step records under every test when the determination is high (not repeated below). On upgrade, execute the full-only steps in the right column even when the lite record of that ID passed. `tests/test_lite.py` checks that every lite test ID appears in this table.

| ID | Lite criterion compared with full | Full-only steps under the same ID |
|---|---|---|
| IQ-03 | Same | Claude Code: resolved managed-settings hash from telemetry, managed-source order and drop-ins confirmed against `/status` |
| OQ-01 | Full criterion plus the provenance label on every sampled PR (from OQ-11) and approver training dated before the approval (REQ-17) | Per-PR review metrics in the shared gate record |
| OQ-02 | Same | None |
| OQ-03, OQ-06 | Same | Organisation audit-log export of an authorised test bypass; push-protection exemptions |
| OQ-04 | Same | GitHub ruleset `copilot_code_review` rule and "Default policy for new features" screenshots; GitLab Duo review trigger |
| OQ-05 | Same | GitLab approval-rule change attempt |
| OQ-07 | Same | `security_and_analysis` and check-retention exports |
| OQ-08, OQ-09 | Same; lite also tests a non-allowed domain from a cloud agent of any tool | Claude Code: auto mode, fail-closed sandbox, policy-hook failure, path-rule anchoring, hook, MCP and plugin restrictions; Codex: policy-hook failure, project-local denylist, managed hooks; Copilot: cloud agent workflow approval |
| OQ-10 | Same | Fallback model settings (Claude Code `fallbackModel`, `switchModelsOnFlag`); per-surface recording sources |
| MA-01 | Same, including the run count of full plan section 5.4 for model-only tasks | At least one organisation-private task per criterion class |
| PQ-01 | Same; model ids primarily from telemetry, session logs or vendor exports | None |
| PQ-02 | Same | None |

Lite credits some requirements to plan records where full has a separate test, marked "lite:" in plan section 6: REQ-05 (IQ-02, IQ-04), REQ-09 (IQ-05), REQ-10 (OQ-11), REQ-16 (IQ-02).

## Upgrade path: lite to full

1. **Raise a change record** naming the trigger (new context, changed risk determination, auditor expectation, audit finding). The lite release stays valid for its intended use unless the trigger calls it into question (for example a "high process risk" determination or an audit finding on the tool); then the approver decides on restrictions until the full release. A new context of use that caused the upgrade is not used until the full release decision.
2. **Render full into its own directory**: `python3 kit.py render --config kit.config.json --profile full --out output-full` (or set `"profile": "full"`). `render` refuses to write into a directory that holds the other profile's documents unless `--force`.
3. **Document IDs.** Lite and full never share a document ID, so an ID always names one document. The full documents get new IDs (`...-01` to `...-08`, `...-GEN-01` to `...-GEN-03`) and supersede the lite documents, which keep their own IDs (`...-L01` to `...-L03`, `...-GEN-L01`, `...-GEN-L02`). The lite documents stay effective until the full release (step 7), the lite work instruction until `...-GEN-01` is issued and its users are trained; then mark them superseded in your document register (ISO 13485:2016 clause 4.2.4). Evidence and deviation IDs are reused: IQ-03, OQ-xx, MA-01 and PQ-xx keep their IDs and evidence paths (step 5); a re-run adds new evidence files beside the lite ones and never replaces a file the lite record cites; new deviations continue the lite `DEV-<TOOL>-nn` numbering.
4. **Carry the content over** section by section:

   | Lite | Full |
   |---|---|
   | Plan sections 3 and 4 (inventory, intended use) | `01-inventory-and-intended-use` |
   | Plan section 6 (requirement subset) | `02-requirements` (add REQ-11 to REQ-14 as they apply) |
   | Plan section 5 (risk determination, known limitations) | `03-risk-assessment` (add the failure-mode table) |
   | Plan sections 7 to 11 (approach, model protocol, interim use, readiness, schedule) | `04-validation-plan` |
   | Test record, code-host steps of OQ-01 to OQ-07 (`evidence/GEN/`) | `00-shared/code-host-gate-qualification` |
   | Test record, tool steps (IQ-03, OQ-01 to OQ-10, MA-01, PQ-01, PQ-02) | `05-test-protocol` execution records, citing the same evidence paths |
   | IQ-03 capture | `06-configuration-baseline` |
   | Report sections 1 to 5 | `07-validation-report` (the lite report, by its `L03` ID, is the previous validation) |
   | Report sections 6 and 7 (a subset of triggers T1 to T19, same numbers; admission records) | `08-change-and-revalidation` |
   | Shared work instruction and tool-discovery checklist (`GEN-L01`, `GEN-L02`) | Full work instruction and checklist (`GEN-01`, `GEN-02`); train users where the rules differ (REQ-17) |

5. **Reuse lite evidence** under `evidence/<TOOL>/<TEST-ID>/` (or `evidence/GEN/<TEST-ID>/`) only if the tool version and the IQ-03 baseline SHA-256 are unchanged since execution and no change trigger has fired since. Otherwise re-run the test. If the risk determination became high (L5), re-execute the scripted gate tests with per-step records.
6. **Execute only the delta**: IQ-01, IQ-02, IQ-04, IQ-05, OQ-11 to OQ-13, the context tests the trigger brings in (OQ-20, OQ-30, OQ-40), RV-01 if the tool was in use before validation, and the full-only steps under shared IDs (table above).
7. **Release under full** with a new report. The lite package is superseded, not deleted: keep it as a record, identified as superseded (ISO 13485:2016 clauses 4.2.4 and 4.2.5).

## Downgrade: full to lite

Not allowed after release without a documented change. The full release decision rested on the full set of tests; dropping them changes the validated state, and ISO 13485:2016 clause 4.1.6 requires revalidation, as appropriate, after changes to the software or its application. The change record must show that none of L1 to L9 applies (including that the reason for choosing full has gone away), list the full-only controls that will no longer be tested with the residual risk accepted, and be approved by the approver before the next periodic review uses the lite record set. The full records stay as records. Before the first release, switching profile is a plan revision approved like any other.
