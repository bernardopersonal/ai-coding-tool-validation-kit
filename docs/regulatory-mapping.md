# Regulatory mapping

Where each clause is answered in the rendered package, and how firm the link is.

**Basis column**

- **R: requirement.** The clause requires it. Wording is paraphrased. ISO and IEC texts are paywalled, so check your licensed copy before quoting verbatim.
- **G: guidance.** Non-binding guidance or a technical report. It describes an accepted way to meet a requirement.
- **I: interpretation.** The kit's reading, or a practice the kit recommends. Defend it in your own words, or adapt it.

**Document key** (rendered package): `00-WI` work instruction, `00-TD` tool discovery checklist, `01` inventory and intended use, `02` requirements, `03` risk assessment, `04` validation plan, `05` test protocol, `06` configuration baseline, `07` validation report, `08` change and revalidation. Section names follow the template headings.

Facts were checked on 2026-10-18 against public sources. Regulator and standards sites could not always be fetched directly, so several points rest on reputable secondary summaries. These are flagged in [Verify before citing](#verify-before-citing).

## ISO 13485:2016

ISO 13485:2016 is the current edition. It was reconfirmed, and no public revision project was found as of 2026.

| Clause | Obligation (paraphrase) | Where in the kit | Basis |
|---|---|---|---|
| §4.1.6 | Documented procedures for validating the application of computer software used in the QMS | Your software-validation SOP governs. The kit supplies the per-tool validation content (01-08), the shared code-host record (00-gates) and the rules of use (00-WI). 04 References names the SOP clause that permits risk-based assurance, predetermined change protocols and retrospective validation; adaptable clause text in [model-change-protocol.md](model-change-protocol.md) | R |
| §4.1.6 | Validate before initial use | 04 Schedule; 07 Release decision; 05 execution rules (plan and protocol approved before execution) | R |
| §4.1.6 | Use before validation is a nonconformity: record it, and correct the root cause of why the tool entered use without validation | 04 Interim-use justification (mandatory NC and CAPA references); 07 Interim use before release; RV-01 Retrospective review | R |
| §4.1.6 | When the tool is already in use: retrospective validation plus a documented interim-use justification and interim controls | 04 Interim-use justification; 07 Interim use before release | I (an honest way to handle a gap; it does not replace validation before use) |
| §8.3, §8.5.2 | Nonconforming product or process handled; corrective action on the root cause, proportionate to its effects | 04 Interim-use justification (NC, CAPA); 04 Deviation handling; 05 Deviation log | R |
| §4.1.6 | Validate after changes to the software or its application, as appropriate | 08 Triggers and required actions; 08 Confirmatory subsets; 04 Predetermined change protocol for models | R |
| §4.1.6 | A new model, or a new model version, is a change to the software or its application | 04 Predetermined change protocol for models; MA-01; [model-change-protocol.md](model-change-protocol.md) | I |
| §4.1.6 | Approach and activities proportionate to the risk of using the software | 03 Criticality determination and resulting test depth; 04 Approach; 05 Test depth by risk | R |
| §4.1.6, §4.2.5 | Keep records of validation activities | 05 execution fields; 06; 07; `evidence/` exports with SHA-256 | R |
| §4.1.6 vs §7.3 | Development use of a coding assistant falls mainly under §4.1.6, with design and development controls (§7.3) applying to the product code it produces | 01 QMS-relevance determination; 07 Regulatory basis | I (public guidance has not settled this) |
| §7.5.6, §7.6 | Same validation pattern for software used in production and service provision (§7.5.6) or in monitoring and measurement (§7.6) | State in 01 which clause each use falls under. Consider §7.6 when AI-built checks are used as measuring software | R (when applicable); I (which uses are in scope) |
| §4.1.5 | Control outsourced processes that affect product conformity, proportionate to risk, including quality agreements | 01 Supplier and contractual terms; 04 Exclusions and cross-references: record a terms review, or a rationale for why cloud-executed agent runs are not an outsourced process | I |
| §4.2.4 | Documents reviewed and approved before issue; changes and revision status identified; current versions at the point of use | 06 Instruction files and hashes; 06 Who may change the configuration; 00-WI Configuration: where it lives and who may change it; REQ-06 (code-owner review of instruction files) | R (for documents) |
| §4.2.4 | Agent instruction files and managed settings are controlled documents or configuration items | 06; REQ-06; OQ-09 | I |
| §4.2.5 | Records legible, identifiable and retrievable; changes identifiable; kept at least for the device lifetime and not less than 2 years from release | 04 Evidence rules; 00-WI Records | R |
| §4.2.5 | Export code-host and CI evidence to the QMS, because platform retention is short (for example GitHub: org audit log 180 days, Git events 7 days, Actions checks and logs 90 days by default) | 04 Evidence rules; `examples/github-workflow-evidence-export.yml` | I |
| §6.2 | Documented processes for competence, training and awareness; records of training | REQ-17; 00-WI Training and competence; 07 Conditions of use | R |
| §6.2 c) | Evaluate the effectiveness of training and other actions | 00-WI Training and competence (required field); PQ-02 | R |
| §6.2 NOTE | Effectiveness method proportionate to risk | 00-WI Training and competence | G (informative note) |
| §7.4.1 | Supplier evaluation and selection criteria proportionate to risk; monitoring and re-evaluation; records | REQ-09, REQ-12; IQ-05; 01 Supplier and contractual terms. The supplier assessment itself lives in your purchasing process | R |
| §7.4.1 | The AI vendor is a supplier of a purchased product that affects the QMS. Record certificate scope and expiry, data terms, and change and deprecation notices | IQ-05; 08 Vendor release monitoring routine | I |

## FDA QMSR (21 CFR Part 820)

In force since 2 February 2026 (final rule published 2 February 2024).

| Clause | Obligation (paraphrase) | Where in the kit | Basis |
|---|---|---|---|
| §820.7, §820.10(a) | Document a QMS that complies with ISO 13485:2016, which is incorporated by reference | All ISO 13485 rows above. Cite "ISO 13485:2016 §4.1.6, as incorporated by 21 CFR 820.10" | R |
| former §820.70(i) | No longer exists. Software validation for production and QMS software now comes from ISO 13485 §4.1.6, §7.5.6 and §7.6 | 07 Regulatory basis: do not cite §820.70(i) | R |
| §820.10(c) | ISO 13485 §7.3 design and development applies to class II and class III devices, and to listed class I devices, including those automated with computer software | Context `code_product`; 01 Contexts of use | R |
| §820.35 | Adds record content for complaints, servicing and UDI on top of ISO 13485 §4.2.5. Nothing specific to software validation | Validation record content comes from §4.2.5 and the CSA guidance (05, 07) | R |
| Inspection scope | The old §820.180(c) exemption is gone. Investigators may review management review, internal audit and supplier audit reports, including records created before 2 February 2026 | Write the supplier assessment and 08 periodic review as inspectable records | R |
| Pre-QMSR records | FDA suggests a comparative analysis showing that earlier records meet the QMSR | If you adopt the kit mid-stream, add a short comparison note for earlier AI-tool records | G |
| CP 7382.850 | Replaced QSIT on 2 February 2026. Six QMS areas, including Change Control, Design and Development, and Outsourcing and Purchasing | AI-tool evidence is typically sampled under these areas: 05, 08, IQ-05 | I |
| 21 CFR §11.1(b) | Part 11 applies to records required by predicate rules (Part 820, including the ISO 13485 §4.1.6 and §4.2.5 records it incorporates) that are kept, signed or submitted electronically | Every package record kept in an eQMS; 04 References; 05 Execution rules ("Electronic records and signatures") | R |
| §11.10(a) | Validation of the system that holds the records (accuracy, reliability, consistent intended performance, detection of invalid or altered records) | The eQMS and evidence store are validated under your Part 11 program; evidence files carry SHA-256 hashes (04 Evidence rules) | R |
| §11.10(d), (g) | Access limited to authorised individuals; authority checks | eQMS roles; 04 Roles and responsibilities; 06 Who may change the configuration | R |
| §11.10(e) | Secure, computer-generated, time-stamped audit trails | eQMS audit trail; kit evidence with UTC timestamps, `executed_by` and SHA-256 (04 Evidence rules) | R |
| §11.50 | Signature manifestation: printed name, date and time, meaning | 05, 06, 07, 08 and 00-gates signature tables ("Date and time (UTC)", meaning of the signature) | R |
| §11.70 | Signatures linked to their records so they cannot be removed, copied or transferred | eQMS signature function; 07 Signatures | R |
| §11.100(c) | Certification to FDA that electronic signatures are the legally binding equivalent of handwritten signatures | Your organisation's Part 11 program (not in the kit) | R |
| §11.200, §11.300 | Components and controls of non-biometric signatures; controls for identification codes and passwords | eQMS e-signature configuration (not in the kit) | R |

## FDA Computer Software Assurance guidance

"Computer Software Assurance for Production and Quality Management System Software". Final guidance issued 24 September 2025, then revised and retitled 3 February 2026 to align with the QMSR (docket FDA-2022-D-0795). It is non-binding. It covers software used as part of production or the quality management system, not device software functions, and it supersedes Section 6 of the 2002 General Principles of Software Validation. Cite the February 2026 version.

| Element | What it describes | Where in the kit | Basis |
|---|---|---|---|
| Step 1: intended use | Identify the intended use of each feature, function or operation | 01 Contexts of use; 01 Uses outside the intended use | G |
| Step 2: risk-based approach | Binary call: "high process risk" when a failure may cause a quality problem that foreseeably compromises safety; otherwise "not high". Judge by foreseeable failure, not by feature name | 03 Criticality determination (`csa` risk model) | G |
| Step 2: finer tiers | Manufacturers may use more granular internal tiers | 03 (`three_level` risk model: low / medium / high) | I |
| Step 3: assurance activities | Scripted testing (robust, or limited/hybrid) and unscripted testing (ad-hoc, error-guessing, exploratory), scaled to risk | 04 Approach; 05 test types (scripted, negative, historical, exploratory) | G |
| Step 3: other controls | Leverage supplier evidence under purchasing controls, downstream controls such as human review and CI, and automated records such as logs and audit trails | 03 controls credited per failure mode; IQ-05; PQ-01 | G |
| Step 4: record | Intended use, risk determination, activities performed, issues and their disposition, conclusion, date and name of the person, approval where appropriate. Digital records favoured over screenshots | 05 execution fields; 07; 04 Evidence rules (exports, hashes) | G |
| Applying CSA to AI coding assistants | The kit treats a coding assistant as QMS or development software within CSA's reasoning. It does not assume a lower "supporting software" assurance level | 03, 04 | I |

## ISO/TR 80002-2:2017

A technical report (guidance) on validating software for medical device quality systems. Cite it instead of the withdrawn AAMI TIR36:2007.

| Element | What it says | Where in the kit | Basis |
|---|---|---|---|
| Scope | Software used in device design, testing, component acceptance, manufacturing, labelling, packaging, distribution and complaint handling, or to automate other parts of an ISO 13485 QMS. It excludes software that is part of a device or is itself a device | 01 QMS-relevance determination. Coding assistants used to design and test device software are in scope | G (scope); I (applying it to coding assistants) |
| Approach | Risk-based critical thinking and a toolbox of confidence-building activities, chosen by complexity, risk of harm and vendor pedigree | 03; 04 Approach | G |
| Develop: Define, Implement, Test, Deploy | Define covers process and use requirements, scope and intended use, risk analysis and the validation plan. Testing is its own sub-phase | 01, 02, 03, 04 (Define); 05 (Test); 07 (Deploy) | G |
| Maintain | Keep the validated state. Monitoring of use or of configuration may be appropriate, because use and configuration drift. A change in intended use that raises risk can trigger more validation even without a software change | 08 Triggers; 08 Periodic review; PQ-01 | G |
| Retire | Remove from use and preserve data | No separate template. Use your SOP, and keep the records per §4.2.5 | G |
| IQ/OQ/PQ | Not mandated by the TR | The kit uses IQ/OQ/MA/PQ labels as a convenient structure | I |

## GAMP 5 Second Edition and the ISPE GAMP AI Guide

GAMP 5 2nd ed. (ISPE, July 2022) added Appendix M12 Critical Thinking, D8 Agile, D9 Software Tools, D10 Blockchain, D11 AI/ML and M11 IT Infrastructure (including SaaS suppliers). The software categories are unchanged and are treated as a continuum. The ISPE GAMP Guide: Artificial Intelligence (July 2025) covers the life cycle of AI-enabled computerised systems.

| Element | Where in the kit | Basis |
|---|---|---|
| Software category (1, 3, 4, 5). The kit recommends Category 4 for configurable agentic tools and asks for a justification if you choose 3 | 01 GAMP 5 category | G (categories); I (the recommendation) |
| M12 critical thinking, risk-based effort | 03; 04 Approach | G |
| D9 Software Tools: life-cycle tools assured through good practice plus a risk assessment of their use, rather than full computerised system validation | 03; 04 | I (the D9 wording could not be verified; it is paraphrased from summaries) |
| M11 IT infrastructure and SaaS suppliers; supplier involvement throughout | IQ-05; 01 Supplier and contractual terms | G |
| AI guide: define the context of use, treat prompts and instructions as controlled items, set performance criteria, qualify AI vendors | 01 Contexts of use; 06 Instruction files and hashes; MA-01 criteria; IQ-05 | I (from secondary summaries of the guide) |

## IEC 62304:2006+A1:2015

| Clause | Obligation (paraphrase) | Where in the kit | Basis |
|---|---|---|---|
| §5.1.4 (class C) | The software development plan includes or references the standards, methods and tools used for class C software items | Name the tool, the surfaces in use and the approved model envelope in your SDP, by reference to 01 | R (class C); I (good practice for classes A and B) |
| §5.1.9 (A, B, C) | Configuration management planning | 06; 08 | R |
| §5.1.10 (B, C) | Supporting items to be controlled. The note covers tools, items or settings used to develop the software that could affect it | 06 Versions per surface, permission mode, rules, sandbox, hooks, instruction files; REQ-06 | R |
| §5.1.10 | The model identifier and the agent settings files are supporting items | 06 Approved models and model policy; REQ-08 | I |
| §5.1.11 (B, C) | Control configuration items before verification | 06; OQ-09 | R |
| §5.1.12 (B, C) | Identify and avoid common software defects | REQ-03 (SAST, dependency and SOUP gate); PQ-02 | R; I (that AI-specific defects belong here) |
| §8.1.1-§8.1.3 (A, B, C) | Uniquely identify configuration items and versions, SOUP and system configuration documentation | 06 Baseline identification; REQ-03 dependency and SOUP gate (also catches hallucinated dependencies) | R |
| §8.2 (A, B, C) | Approve, implement and verify changes, with traceability | 08 Change record minimum content; REQ-05, REQ-11 | R |

A second edition of IEC 62304 is in development. Its publication was not confirmed as of October 2026, so cite 2006+A1:2015 and keep a slot for the new numbering. Check the EU harmonisation status of EN 62304 on EUR-Lex before you claim it.

## GxP option (`reg_gxp`)

Added when the wizard's GxP option is selected. EU GMP Annex 11 is medicinal-product GMP, not a device requirement. 21 CFR Part 11 is mapped under FDA QMSR above, because it applies to Part 820 records too; the templates render the Part 11 text when either option is selected.

| Clause | Topic | Where in the kit | Basis |
|---|---|---|---|
| Annex 11 (2011) §1 | Risk management (product quality, patient safety, data integrity) | 03 | R (GxP) |
| Annex 11 §2 | Personnel | REQ-17; 00-WI Training and competence | R (GxP) |
| Annex 11 §3 | Suppliers and service providers: formal agreements, assessment, audit need based on risk | IQ-05; 01 Supplier and contractual terms | R (GxP) |
| Annex 11 §4, §4.5 | Validation; assess that the system was developed under an appropriate QMS (supplier assessment) | 04, 05, 07; IQ-05 | R (GxP) |
| Annex 11 §10 | Change and configuration management | 06; 08 | R (GxP) |
| Annex 11 §11 | Periodic evaluation | 08 Periodic review | R (GxP) |
| Annex 11 §12 | Security | REQ-16, REQ-09; IQ-02 | R (GxP) |
| Annex 11 §13 | Incident management | 00-WI Reporting problems; 05 Deviation log | R (GxP) |
| Annex 11 §17 | Archiving | 04 Evidence rules | R (GxP) |
| Annex 11 revision and new Annex 22 (drafts, July 2025) | Not final as of October 2026. Draft Annex 22 excludes generative AI and LLMs from critical GMP applications. Non-critical use is allowed when qualified people confirm the output is fit for its intended use | Human approval gate (REQ-01, REQ-02); keep AI out of critical GMP decisions | G (draft); may change |
| 21 CFR Part 11 | For GMP predicate records, as above under FDA QMSR (the clause rows apply in the same way) | See the FDA QMSR section | R |
| 21 CFR Part 11 and logs | If agent session logs, hook output or CI logs serve as validation or review evidence, state whether they are QMS records and how their integrity and attribution are ensured | 04 Evidence rules; 06 Logging, telemetry and retention | I |

## Other references

| Reference | Relevance | Where in the kit | Basis |
|---|---|---|---|
| EU MDR Art. 10(8) | Technical documentation, the EU declaration of conformity and certificates are kept at least 10 years after the last device is placed on the market (15 for implantables). Validation records that support the technical file should follow this period | 04 Evidence rules; 00-WI Records | R (EU devices) |
| EU AI Act Art. 4 (AI literacy) | Reportedly softened by Regulation (EU) 2026/1744, so that deployers take measures to support AI literacy. Check the Official Journal text before quoting | 00-WI Training and competence, alongside ISO 13485 §6.2 | I |
| ISO/IEC 27001, ISO/IEC 42001 (options) | Cross-references for information security and AI management systems | Added by the wizard options; 04 Exclusions and cross-references | I |

## Signals, not requirements

- No regulator or notified body had published guidance specifically on validating AI coding assistants as of October 2026.
- An FDA warning letter dated 2 April 2026 cited a drug manufacturer whose AI agents generated specifications, procedures and master production and control records without quality-unit review. FDA rejected the defence that the AI had not flagged the gap, and it did not prohibit AI. The lesson is a mandatory qualified human review gate plus validation for intended use (REQ-01, REQ-13, OQ-20).
- FDA and EMA published 10 guiding principles of Good AI Practice in drug development (January 2026). These are high-level policy principles, not guidance.
- FDA's discussion paper on generative AI-enabled medical devices (August 2026) is about AI inside devices, not coding tools.
- Team-NB/IG-NB's AI questionnaire (November 2024) and MDCG 2025-6 (June 2025) concern AI in devices and the interplay of the MDR/IVDR with the AI Act. MDCG 2025-6 allows AI Act controls to be integrated into the existing QMS.

## Supplier evidence (input to IQ-05)

Record the certificate scope text and expiry from the vendor's trust portal, and check that the scope covers the product and surface you actually use.

- **Anthropic** announced ISO/IEC 42001:2023 certification in January 2025. Its support article lists ISO/IEC 27001:2022, ISO/IEC 42001:2023 and SOC 2 Type I and Type II for its commercial products. No public statement names Claude Code within these scopes. Source: trust.anthropic.com.
- **OpenAI**'s trust portal lists a SOC 2 Type 2 report and ISO/IEC 27001, 27017, 27018 and 27701 certifications. The API is covered and ISO/IEC 42001 is claimed. Coverage of Codex was not verified. Source: trust.openai.com.

## Verify before citing

- The exact February 2026 CSA text. Some summaries say it names AI/ML tools and adds a Part 11 section and a software-changes subsection. Check the FDA PDF before quoting.
- Whether the final CSA text keeps the draft's examples of "supporting" software, such as development tools that automate testing.
- The wording of GAMP 5 Appendix D9 and of the GAMP AI guide (paywalled).
- The final text of Annex 11 and Annex 22, and the status of IEC 62304 Edition 2.
- The exact subsection cited in the April 2026 warning letter (21 CFR 211.22(c) according to commentators; one record lists (d)).

Not legal advice. Adapt the mapping to your QMS and to your notified body's or investigator's expectations.
