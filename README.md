# AI Coding Tool Validation Kit

**Using Claude Code or Codex in a regulated team? Good. Is it validated?**

New to this? [Terms you'll meet](#terms-youll-meet) explains each term in 1 line, and [GUIDE.md](GUIDE.md) is a 2-page intro.

### Why it matters

Tools that write or change your product code, tests or quality records have a direct impact on quality. ISO 13485:2016 clause 4.1.6 requires you to validate [QMS](#terms-youll-meet) software before initial use and, as appropriate, after changes, proportionate to risk.

Do it properly and your QA/RA lead will be enormously grateful.

**No shadow AI.** An AI tool the organisation doesn't know about can't be validated, controlled or defended in an audit. That covers unsanctioned tools, personal accounts and AI-assisted changes that were never declared.

So declare every tool, use organisation accounts and label AI-assisted changes. The [tool-discovery checklist](examples/acme-medsoft-lite/package/00-shared/tool-discovery-checklist.md) and `checks/find_ai_footprint.py` (step 2 of [Quick start](#quick-start)) help you find what's already in use.

### Why I built this

In my work with software and medical-device companies I keep seeing the same thing: every team already writes code with AI, and many of them haven't validated the tools doing it. In a regulated environment that can't stay that way.

This kit is a small first step. Validating the tools is one piece of using AI responsibly in regulated software, next to design controls, risk management, cybersecurity and how you review what the AI produces.

I hope it helps. Feedback and contributions are very welcome.

### What the kit does

It's a ready-to-run kit that validates AI coding assistants as QMS and development software under ISO 13485:2016 (and the FDA QMSR, which incorporates ISO 13485 by reference). The approach is risk-based, in the style of FDA CSA.

A wizard renders a validation package for your organisation, lite or full. Scripts collect the evidence. A model admission suite keeps you validated when the vendor ships a new model.

Version 0.2.0 · Python 3.9+ standard library only · Claude Code and OpenAI Codex supported out of the box; GitHub Copilot, Cursor and other tools through [docs/adapting-other-tools.md](docs/adapting-other-tools.md).

Start here: [Quick start](#quick-start).

## 2 profiles: lite and full

Both profiles come from the same wizard answers and run the same scripts. Lite is the smallest package that still proves the controls work. Full is the audit-depth package.

| | Lite | Full |
|---|---|---|
| Documents per tool | 3: a validation plan, a test record and a validation report | 8: inventory and intended use, requirements, risk assessment, validation plan, test protocol, configuration baseline, validation report, change and revalidation |
| Shared by all tools | A work instruction for AI-assisted development and a tool-discovery checklist | The same 2, plus a record that tests the code-host gates once for every tool |
| Tests that try to get past the gates | A merge without approval, a direct push, a bot or the author approving, an admin bypass, a change that fails CI, a denied command, a model outside the approved list (where the tool can block it) | The same tests |
| Other checks | A check of real merged PRs, a hashed configuration baseline, the model admission check and monitoring after release. 1 short record per test | Everything in lite, plus installation, account and identity checks per surface, the vendor's data terms, the labels on AI-assisted changes, undoing an AI-assisted change and vendor monitoring. More tests switch on with your use: AI-drafted documents, QMS agents, agents that read untrusted content, a tool that was in use before validation. Step-by-step records where the risk is high |
| Risk and change records | Kept short, inside the plan and the report | A separate risk assessment with a failure-mode table, a configuration baseline and a change document |
| Who it's for | Teams where a qualified human reviews every AI-assisted change, and required CI checks pass, before it reaches a protected branch. People: 1 engineer, 1 approver and sandbox test accounts | Teams where the AI output carries weight on its own (the situations below), or whose auditor, notified body or customer expects the deeper package |

Lite reuses full's test numbering and commands. For every test the 2 profiles share, lite's pass criterion is the same as full's or stricter. So your lite evidence carries over when you move to full, and you run only what full adds.

Lite documents carry their own document numbers (for example `ACME-VAL-CLAUDE-L01`), so a number always names 1 document. When you move to full, the full documents supersede the lite ones.

**When you need full.** `kit.py render` refuses lite in 4 situations, unless you pass `--force`, which marks the documents NOT VALID FOR RELEASE:

- The AI output itself counts as a check or as evidence: an AI reviewer counted as verification, an LLM acting as judge, AI results used without independent recomputation. This is the wizard's "pinned" model policy: 1 exact model id, changed only under change control.
- An agent can write to QMS systems (eQMS, issue tracker, document system) by any route other than a pull request through the code-host gate. QMS agents (autonomous or scheduled agents that act on QMS systems, such as filing tickets or editing controlled documents) count here.
- AI-generated tests or other AI output serve as verification evidence or as QMS records, and no one independently reviews whether they're adequate.
- An agent that holds write credentials or secrets beyond the pull-request path reads untrusted content: a CI or cloud agent, a PR bot that outside comments can trigger, MCP results.

Full is also required when:

- the AI drafts controlled records and each draft isn't independently checked against its sources;
- GxP rules apply (for example EU GMP Annex 11) and the use is high-impact;
- your risk determination under FDA CSA is "high process risk";
- a notified body, the FDA or a customer expects more depth;
- earlier audits found issues with this tool or with how you validate AI tools.

The lite plan records a yes or no for each situation, with the reason, and warns you prominently when your answers point to one. The profile applies to the whole config: if only 1 tool needs full, give that tool its own config.

**How the wizard recommends one.** New configs default to lite, and the wizard recommends full when any answer points to it. It asks about your tools, surfaces, contexts of use, model policy and GxP, plus a yes/no question for each of the 4 situations where `kit.py render` refuses lite.

When one of those 4 applies, the wizard sets full without asking. In every other case you choose, with the recommendation as the default, and the wizard reminds you of the 3 situations it can't read from your answers (a "high process risk" determination, a reader expecting more depth, earlier audit findings).

The exact test list of each profile, the situations with their regulatory anchors, what lite leaves out and the upgrade path: [docs/lite-vs-full.md](docs/lite-vs-full.md).

## Terms you'll meet

| Term | In plain words | In depth |
|---|---|---|
| Validation package | The set of documents that shows a tool is fit for the way you use it: plan, tests, evidence, report and the rules for users. The kit renders it from your answers | [What you get](#what-you-get); filled examples: [lite](examples/acme-medsoft-lite/README.md), [full](examples/acme-medsoft/README.md) |
| Intended use | Who uses which tool, on which surface (CLI, IDE, cloud agent, CI), for what, in which repositories, and who approves the result. It sets the scope for everything else | [Inventory and intended use](examples/acme-medsoft/package/CLAUDE/01-inventory-and-intended-use.md) ([template](templates/full/01-inventory-and-intended-use.md.tmpl)) |
| Gates (guardrails) | The controls around the tool that don't depend on the model: branch protection, required human review, required CI checks, permissions, sandbox, managed settings. The binding ones sit on the code host and in CI | [Code-host gate qualification](examples/acme-medsoft/package/00-shared/code-host-gate-qualification.md), [requirements](examples/acme-medsoft/package/CLAUDE/02-requirements.md) |
| IQ, OQ, PQ | Installation qualification (installed and configured as approved: a deploy check), operational qualification (the gates behave as configured, including refusing what they must refuse: negative tests) and performance qualification (it keeps working in real use after release: production monitoring) | [Test protocol](examples/acme-medsoft/package/CLAUDE/05-test-protocol.md), [lite test record](examples/acme-medsoft-lite/package/CLAUDE/02-test-record.md) |
| Test IDs | A prefix plus a number, such as OQ-02. IQ = installation, OQ = operational, PQ = performance, MA = model admission, RV = retrospective review. Lite and full use the same number for the same test | [Test protocol](examples/acme-medsoft/package/CLAUDE/05-test-protocol.md) |
| Model admission check (MA-01) | A fixed, automated set of agent tasks that every model must pass before you use it. A regression suite for models, run headless with your own credentials | [admission/README.md](admission/README.md) |
| Approved model list ("model envelope") | The model ids or family patterns a tool may use, like a dependency allow-list. A new id gets in only after it passes the admission check | [docs/model-change-protocol.md](docs/model-change-protocol.md#terms) |
| Retrospective review of interim use (RV-01) | For a tool that was in use before validation: a look back at every change merged in that period (qualified human approval, bypasses, which model wrote it) | [RV-01 in the test protocol](examples/acme-medsoft/package/CLAUDE/05-test-protocol.md#rv-01-retrospective-review-tool-already-in-use) |
| SOUP | Software of unknown provenance (IEC 62304): third-party code you didn't build under your own process, such as a pip or npm package. The kit's SOUP gate fails a PR that adds a dependency missing from your approved list | [checks/README.md](checks/README.md#soup_gatepy) |
| QA/RA | Quality assurance and regulatory affairs: the people who own the QMS and talk to auditors | [GUIDE.md](GUIDE.md), written for QA/RA leads |
| QMS, eQMS | Quality management system: the procedures, documents and records a medical-device company runs under ISO 13485. An eQMS is the software where those documents, records and signatures live, and your validation records go there | [docs/regulatory-mapping.md](docs/regulatory-mapping.md#iso-134852016) |
| Notified body | The independent organisation, designated under the EU MDR, that audits your QMS and certifies your device for the EU market | [docs/lite-vs-full.md](docs/lite-vs-full.md) (when its expectations call for full) |
| FDA QMSR | The US Quality Management System Regulation, 21 CFR 820 (CFR: Code of Federal Regulations). Since 2 Feb 2026 it incorporates ISO 13485 by reference, so the same validation duty applies in the US | [docs/regulatory-mapping.md](docs/regulatory-mapping.md#fda-qmsr-21-cfr-part-820) |
| FDA CSA | FDA's Computer Software Assurance guidance: test production and QMS software in proportion to process risk, with scripted tests where a failure could compromise safety | [docs/regulatory-mapping.md](docs/regulatory-mapping.md#fda-computer-software-assurance-guidance) |
| IEC 62304, class C | IEC 62304 is the life-cycle standard for medical-device software. Class C is its highest software safety class: a failure can lead to death or serious injury | [docs/regulatory-mapping.md](docs/regulatory-mapping.md#iec-623042006a12015) |
| GAMP 5 | ISPE's good-practice guide for validating computerised systems (2nd edition). It sorts software into categories, from infrastructure to custom code, and the inventory records the tool's category | [docs/regulatory-mapping.md](docs/regulatory-mapping.md) (GAMP 5 section) |
| GxP, EU GMP Annex 11 | The "good practice" rules for regulated life-science work, such as GMP for manufacturing medicines. EU GMP Annex 11 covers the computerised systems used under GMP | [GxP option](docs/regulatory-mapping.md#gxp-option-reg_gxp) |

## What "validated" means here

The kit validates the 3 things around the model that you control. They stay put when the model changes:

1. The intended use: who uses which tool, on which surface, for what, where, and who approves the result.
2. The guardrails around the tool: approval gates, required CI checks, permissions, sandbox, managed configuration, accounts, attribution. They're model-independent, and they're the core of the validation.
3. Verification of the output: a qualified human reviews every AI-assisted change, and it passes CI before it reaches a protected branch. "You own every line you merge."

The principles behind every document:

- Assurance is proportionate to risk (FDA CSA, ISO/TR 80002-2, GAMP 5 2nd ed.): scripted tests (written steps, expected results fixed first) where process risk is high, unscripted tests (exploratory or error-guessing, with a short record) elsewhere.
- Acceptance criteria are fixed **before** execution, and expected results are computed independently first.
- Only people execute, conclude and approve the validation: the executor and the approver are 2 different people, and each signs for themselves.
- Configuration is baselined and change-controlled. Behaviour is monitored too, because models change without a version bump.
- **Negative** tests prove the gates (merge without approval, direct push, bot approval, self-approval, admin bypass) on at least 2 repositories.
- Evidence comes from exports (API JSON, logs, SHA-256 hashes), with screenshots as a supplement.
- The binding control lives server-side, on the code host and in CI. The agent's local configuration is a second layer.
- If the tool's already in use, say so: retrospective validation plus a documented interim-use justification.

Next: [Quick start](#quick-start).

## Models change often: 3 tiers

The validation unit is **tool + vendor + surface + context of use**. Models come and go inside it: each tool has an [approved model list](#terms-youll-meet) (the "model envelope": ids or family patterns).

Both profiles handle model changes with a change protocol the plan approves in advance, so a new id that matches a pre-authorised pattern gets in through the admission check (tier 2 below).

1. Initial validation (once per tool and vendor): the [IQ, OQ and PQ](#terms-youll-meet) tests of the guardrails, plus the [model admission check (MA-01)](#terms-youll-meet) on every model in the envelope.
2. Model admission (a new id matching a pattern pre-authorised in the plan): rerun MA-01 headlessly. Pass: a short admission record, and the exact id joins the allow-list, enforced where the tool can enforce it.
3. Re-baseline: MA-01 plus a targeted set of operational (OQ) tests. It applies to a new model family, a tool release that changes a guardrail (permissions, sandbox, managed settings, approval flow), a new surface or context, an admission failure or a change to the vendor's terms. A new vendor gets a new initial validation.

Details: [docs/model-change-protocol.md](docs/model-change-protocol.md).

## Quick start

You need Python 3.9+, a clone of this repository and, for the checks, the `gh` CLI (or a `GITHUB_TOKEN`). Read access covers rulesets and PRs. Branch protection and the Actions settings may need admin rights, and without them `check_github_gates.py` reports those items as `inconclusive` (see [checks/README.md](checks/README.md#check_github_gatespy)).

### 1. Render your package

```bash
python3 kit.py init                   # wizard: organisation, roles, tools, models, contexts, risk model, profile
# or: python3 kit.py init --defaults  # fictional example answers (Acme MedSoft), lite profile
python3 kit.py render --config kit.config.json --docx                            # re-render; .docx needs pandoc
python3 kit.py render --config kit.config.json --profile full --out output-full  # --profile lite|full overrides the config
```

Documents land in `output/`. Render each profile into its own directory: `render` refuses to overwrite the other profile's documents, and refuses lite in the 4 situations above, unless you pass `--force`.

`init --profile lite|full` stores the profile without asking, and a 0.1.0 config (no `profile` key) renders as full. `kit.config.json`, `output/` and `output-*/` are git-ignored, because they belong in your QMS.

### 2. Explore with the checks

```bash
export KIT_OPERATOR="Your Name"     # recorded in every evidence file
python3 checks/find_ai_footprint.py --path REPO_DIR --out evidence/_exploratory/   # AI tools you may not know about
python3 checks/capture_baseline.py --tool claude_code --repo REPO_DIR --out evidence/_exploratory/
python3 checks/check_github_gates.py --repo OWNER/REPO --branch main --prs 20 --out evidence/_exploratory/
python3 admission/run_admission.py --tool claude_code --model <model-id> --runs 3 --out evidence/_exploratory/ --dry-run
```

Exploratory runs feed the plan. Once the plan is approved, you re-run 3 of them as formal tests into `evidence/<TOOL>/<TEST-ID>/`: the configuration baseline (IQ-03, from `capture_baseline.py`), the review record of real AI-assisted PRs (OQ-01, from `check_github_gates.py`) and the [model admission check](#terms-youll-meet) (MA-01, from `run_admission.py`).

For a tool that's already in use, check the interim controls before the plan is approved: the gates on every in-scope repository (`check_github_gates.py`), organisation accounts, the data rules, and the work instruction issued with users briefed. File the results under `evidence/<TOOL>/INTERIM/`; the plan's interim-use table lists them.

Use `--tool codex` for Codex. Every script has `--help`, writes JSON and Markdown evidence (UTC timestamp, operator, machine, SHA-256) and exits non-zero when a check fails.

The admission dry run calls no model; drop `--dry-run` once you have your own vendor credentials. For `<model-id>`, use an exact id from your approved model list, as the tool accepts it ([admission/README.md](admission/README.md) has examples, and `--list` shows the tasks). The suite never runs in this kit's CI.

### 3. Execute

Fill in the tool-discovery checklist and the `[fill in]` fields of the plan. Set up a sandbox repository protected like production (`checks/mirror_protection.py` copies the protection settings over); the lite plan has a readiness checklist. The approver approves the plan and the test record (lite) or protocols (full) *before* the first test.

Then run the installation and operational tests ([IQ and OQ](#terms-youll-meet)) and the model admission check (MA-01), with [checks/canary/](checks/canary/README.md) driving the tests that try to get past the gates.

Tools that share repositories run the code-host gate tests once. Record them in the first tool's test record (lite) or in `00-shared/code-host-gate-qualification.md` (full), and file the evidence under `evidence/GEN/` (`GEN` holds the evidence that several tools share).

The 2 performance tests ([PQ](#terms-youll-meet)) run after release: PQ-01 watches real use (every merge approved by a qualified human, no bypass, only approved models) and PQ-02 re-reviews a sample of merged AI-assisted PRs to show that review catches defects. A signed addendum reports them.

### 4. Sign the report

The validation report (lite: [03-validation-report.md](examples/acme-medsoft-lite/package/CLAUDE/03-validation-report.md), full: [07-validation-report.md](examples/acme-medsoft/package/CLAUDE/07-validation-report.md)) carries the release decision: approved with conditions, approved with restrictions, or not approved. An approval starts as "approved with conditions" and becomes "approved for intended use" once the signed addendum with the 2 performance tests (PQ-01, PQ-02) is in.

People sign it themselves, in your eQMS or with an e-signature. Any conclusion the AI tool drafts gets independent review, and the report states who wrote it.

Executed fictional packages: [examples/acme-medsoft-lite/](examples/acme-medsoft-lite/README.md) (lite) and [examples/acme-medsoft/](examples/acme-medsoft/README.md) (full).

## What you get

```
README.md, GUIDE.md          this file; a 2-page guide for QA/RA leads (print copy: docs/GUIDE.pdf)
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
  soup_gate.py                 reference SOUP gate
  client_regression.py         regression check of a new AI tool CLI version before you roll it out
admission/                   model admission suite (MA-01): runner, tasks, fixtures
tools/claude-code/, tools/codex/   verified configuration examples and notes
docs/                        lite vs full, regulatory mapping, model-change protocol, adapting other tools, GUIDE.pdf
examples/                    filled fictional packages (acme-medsoft-lite/, acme-medsoft/), workflows, PR template
tests/                       unit tests (python3 -m unittest discover -s tests)
.github/workflows/ci.yml     runs the tests and smoke renders on Python 3.9 and 3.12
```

The rendered package has 1 folder per tool (folder = tool ID). Lite:

```
output/
  00-shared/ai-assisted-development-work-instruction.md, tool-discovery-checklist.md
  CLAUDE/
    01-validation-plan.md      inventory, intended use, when lite isn't enough, risk and known limits, requirements, model change protocol, readiness
    02-test-record.md          the lite tests, each with its commands, pass criterion and result
    03-validation-report.md    results, model list, release decision, signatures, change triggers, admission record
  CODEX/ ...
```

Full:

```
output-full/
  00-shared/                   the same 2, plus code-host-gate-qualification.md (gate tests, run once for all tools)
  CLAUDE/
    01-inventory-and-intended-use.md   02-requirements.md (17 requirements)   03-risk-assessment.md
    04-validation-plan.md              05-test-protocol.md                    06-configuration-baseline.md
    07-validation-report.md            08-change-and-revalidation.md
  CODEX/ ...
```

## What the kit checks

Each document links to the filled fictional example (Acme MedSoft, Claude Code folder), with the template it was rendered from in parentheses.

| Problem | What the kit gives you | Lite | Full |
|---|---|---|---|
| The tool was in use before anyone validated it | The gap recorded as a nonconformity (a logged deviation from your own procedures) with a CAPA (corrective and preventive action), a look back at what was merged in that period, and a release decision on whether use may go on | [Plan][l-01] ([template][l-01-t]), [report][l-03] ([template][l-03-t]) | [Plan][f-04] ([template][f-04-t]), [test protocol][f-05] ([template][f-05-t]), [report][f-07] ([template][f-07-t]) |
| People use AI tools the organisation doesn't know about | A tool-discovery checklist (code host, repositories, purchasing, endpoints, people) and `checks/find_ai_footprint.py`, which finds agent config files and AI workflows in a repository | [Discovery checklist][l-disc] ([template][l-disc-t]) | [Discovery checklist][f-disc] ([template][f-disc-t]), [change and revalidation][f-08] ([template][f-08-t]) |
| The vendor ships a new model, sometimes behind the same tool version | An approved model list, the id patterns the plan pre-authorises, a test that the tool refuses other models where it can, the model admission check, and triggers that say what to re-test | [Plan][l-01] ([template][l-01-t]), [test record][l-02] ([template][l-02-t]), [report][l-03] ([template][l-03-t]) | [Requirements][f-02] ([template][f-02-t]), [plan][f-04] ([template][f-04-t]), [test protocol][f-05] ([template][f-05-t]), [change and revalidation][f-08] ([template][f-08-t]) |
| An AI-assisted change reaches the protected branch without a real human review | Tests that try to get past the gate (no approval, direct push, bot approval, self-approval, admin bypass) on 2 repositories when available, a check of real merged PRs, monitoring after release, and a re-review of sampled PRs to show that reviewers catch defects | [Test record][l-02] ([template][l-02-t]) | [Code-host gate qualification][f-gates] ([template][f-gates-t]), [test protocol][f-05] ([template][f-05-t]) |
| Someone changes the tool's settings or instruction files and it goes unnoticed | A configuration baseline captured by `checks/capture_baseline.py`, with a SHA-256 hash per file, to compare against later | [Test record][l-02] ([template][l-02-t]) | [Test protocol][f-05] ([template][f-05-t]), [configuration baseline][f-06] ([template][f-06-t]) |
| Someone signs on another person's behalf, or the AI tool concludes on its own validation | Signature tables that people sign themselves, and an authorship and independence statement that says who wrote what | [Report][l-03] ([template][l-03-t]) | [Report][f-07] ([template][f-07-t]) |

[l-disc]: examples/acme-medsoft-lite/package/00-shared/tool-discovery-checklist.md
[l-disc-t]: templates/lite/00-tool-discovery-checklist.md.tmpl
[l-01]: examples/acme-medsoft-lite/package/CLAUDE/01-validation-plan.md
[l-01-t]: templates/lite/01-validation-plan.md.tmpl
[l-02]: examples/acme-medsoft-lite/package/CLAUDE/02-test-record.md
[l-02-t]: templates/lite/02-test-record.md.tmpl
[l-03]: examples/acme-medsoft-lite/package/CLAUDE/03-validation-report.md
[l-03-t]: templates/lite/03-validation-report.md.tmpl
[f-disc]: examples/acme-medsoft/package/00-shared/tool-discovery-checklist.md
[f-disc-t]: templates/full/00-tool-discovery-checklist.md.tmpl
[f-gates]: examples/acme-medsoft/package/00-shared/code-host-gate-qualification.md
[f-gates-t]: templates/full/00-code-host-gate-qualification.md.tmpl
[f-02]: examples/acme-medsoft/package/CLAUDE/02-requirements.md
[f-02-t]: templates/full/02-requirements.md.tmpl
[f-04]: examples/acme-medsoft/package/CLAUDE/04-validation-plan.md
[f-04-t]: templates/full/04-validation-plan.md.tmpl
[f-05]: examples/acme-medsoft/package/CLAUDE/05-test-protocol.md
[f-05-t]: templates/full/05-test-protocol.md.tmpl
[f-06]: examples/acme-medsoft/package/CLAUDE/06-configuration-baseline.md
[f-06-t]: templates/full/06-configuration-baseline.md.tmpl
[f-07]: examples/acme-medsoft/package/CLAUDE/07-validation-report.md
[f-07-t]: templates/full/07-validation-report.md.tmpl
[f-08]: examples/acme-medsoft/package/CLAUDE/08-change-and-revalidation.md
[f-08-t]: templates/full/08-change-and-revalidation.md.tmpl

## Regulatory mapping (summary)

The links go to the filled full-profile example. Its templates are in [templates/full/](templates/full/), and the lite plan, test record and report condense the same content ([templates/lite/](templates/lite/)).

| Framework | What it asks, in plain words | Where the kit answers |
|---|---|---|
| ISO 13485:2016 clause 4.1.6 | Have a written procedure for validating software you use in your quality system. Validate it before first use and after changes, in proportion to risk, and keep records | The whole package, mainly the [validation plan][f-04], [test protocol][f-05], [validation report][f-07] and [change and revalidation][f-08] |
| FDA QMSR (21 CFR 820, in force 2 Feb 2026) | The US rule now incorporates ISO 13485 by reference (21 CFR 820.7, 820.10), so the same validation duty applies. The old software validation clause, 21 CFR 820.70(i), no longer exists | The same documents. The [report's regulatory basis](examples/acme-medsoft/package/CLAUDE/07-validation-report.md#2-regulatory-basis) shows the citation; in your records, cite ISO 13485 clause 4.1.6 "as incorporated by 21 CFR 820.10" |
| FDA CSA guidance (final Sep 2025, revised Feb 2026) | Start from the intended use, decide how risky a failure would be, choose test activities to match, and keep a lean record | [Intended use][f-01], the risk determination in the [risk assessment][f-03], scripted and unscripted tests in the [plan][f-04] and [protocol][f-05], the [report][f-07]; the lite profile as a whole |
| ISO 13485 clauses 4.2.4, 4.2.5, 6.2, 7.4 | Control your documents and records, make sure people are competent and trained, and evaluate suppliers (here, the AI vendor) | File hashes in the [configuration baseline][f-06], the [evidence rules](examples/acme-medsoft/package/CLAUDE/04-validation-plan.md#9-evidence-rules), training in the [work instruction][f-wi], the vendor terms test ([IQ-05](examples/acme-medsoft/package/CLAUDE/05-test-protocol.md#iq-05-vendor-data-terms-recorded-and-matched-to-contract)) |
| ISO/TR 80002-2:2017, GAMP 5 2nd ed., ISPE GAMP AI guide | Think critically about risk, pick from a toolbox of assurance activities, manage the whole life cycle, and classify the software | The GAMP category in the [inventory][f-01], the [risk assessment][f-03], the [plan][f-04], [change and revalidation][f-08] |
| IEC 62304 clauses 5.1.4, 5.1.10, 8 | Name your development tools in the software development plan (class C) and keep tool settings under configuration control | [Inventory][f-01], [configuration baseline][f-06], [change and revalidation][f-08] |
| 21 CFR Part 11 (FDA QMSR and GxP options) | Electronic records and signatures you can trust | The [evidence rules](examples/acme-medsoft/package/CLAUDE/04-validation-plan.md#9-evidence-rules) and signature tables with name, date and time, and meaning (for example in the [report](examples/acme-medsoft/package/CLAUDE/07-validation-report.md#15-signatures)) |
| EU GMP Annex 11 (GxP option) | Rules for computerised systems in medicinal-product manufacturing | Added to the documents when you select the GxP option ([mapping](docs/regulatory-mapping.md#gxp-option-reg_gxp)) |

[f-wi]: examples/acme-medsoft/package/00-shared/ai-assisted-development-work-instruction.md
[f-01]: examples/acme-medsoft/package/CLAUDE/01-inventory-and-intended-use.md
[f-03]: examples/acme-medsoft/package/CLAUDE/03-risk-assessment.md

Clause by clause, with requirement and interpretation marked separately: [docs/regulatory-mapping.md](docs/regulatory-mapping.md).

## Tool-specific notes

- [tools/claude-code/](tools/claude-code/README.md): managed settings for a validated state, per-surface delivery caveats, known guardrail limits.
- [tools/codex/](tools/codex/README.md): user defaults versus admin-enforced requirements, recent breaking changes, known guardrail limits.
- [docs/adapting-other-tools.md](docs/adapting-other-tools.md): GitHub Copilot, Cursor and any other tool, including the admission runner.

Vendor facts were checked against vendor documentation and source code on 2026-10-18. Vendors move fast, so re-verify before you rely on a setting. Where a fact couldn't be verified, the kit says so plainly: "verify against the vendor's current documentation".

## Disclaimer

Treat the kit as a starting point and adapt it to your QMS. Your software validation procedure, document control, e-signature system and risk method take precedence over anything here.

A tool becomes validated when people execute, review and approve the records; the kit gives them templates and scripts to do it with. It's general information, so take legal questions to a lawyer.

## Licence

- Code (`kit.py`, `kit/`, `checks/`, `admission/`, `tests/`, configuration examples in `tools/` and `examples/`): [MIT](LICENSE).
- Templates and documentation (`templates/`, `docs/`, `README.md`, `GUIDE.md`, other Markdown files): [CC BY 4.0](LICENSE-docs).

Contributing: [CONTRIBUTING.md](CONTRIBUTING.md). Changes: [CHANGELOG.md](CHANGELOG.md). Developer notes: [README_DEV.md](README_DEV.md).

---

Maintained by Bernardo Plaza, regulatory, quality and security for software medical devices · [plazatrillo.es](https://plazatrillo.es)
