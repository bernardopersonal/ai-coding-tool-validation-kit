# AI Coding Tool Validation Kit

**Using Claude Code or Codex in a regulated team? Good. Is it validated?**

A ready-to-run kit to validate AI coding assistants as QMS and development software under ISO 13485:2016 §4.1.6 (and the FDA QMSR, which incorporates ISO 13485 by reference), with a risk-based, CSA-style approach. A wizard renders a complete validation package for your organisation. Scripts collect the evidence. A model admission suite keeps you validated when the vendor ships a new model. IQ, OQ and MA-01 in about a week; PQ over at least 4 weeks after release.

Version 0.1.0 · Python 3.9+ standard library only · Claude Code and OpenAI Codex supported out of the box, GitHub Copilot, Cursor and other tools through [docs/adapting-other-tools.md](docs/adapting-other-tools.md).

## What "validated" means here

You cannot qualify a large language model, and you do not need to. The kit validates three things:

1. **The intended use.** Who uses which tool, on which surface, for what, in which repositories, and who approves the result.
2. **The guardrails around the tool.** Human approval gates, required CI checks, permissions, sandbox, managed configuration, account ownership, attribution. These are model-independent and form the core of the validation.
3. **Verification of the output.** Every AI-assisted change is reviewed by a qualified human and passes CI before it reaches a protected branch. "You own every line you merge."

The principles behind every document:

- Assurance is proportionate to risk (FDA CSA, ISO/TR 80002-2, GAMP 5 2nd ed.). Scripted tests where process risk is high, unscripted tests (exploratory, error-guessing, historical evidence) elsewhere.
- Acceptance criteria are fixed **before** execution. When the tool computes something, the expected result is computed independently first.
- The tool never executes, concludes or approves its own validation. Executor and approver are different people. People sign for themselves in the eQMS or with an e-signature, never typed by the AI or by someone else.
- Configuration is baselined and change-controlled. Behaviour is monitored, because models change without a version bump.
- Gates are proven with **negative** tests (merge without approval, direct push, bot approval, self-approval, admin bypass) on more than one repository.
- Evidence comes from exports (API JSON, logs, SHA-256 hashes), not only from screenshots.
- The binding control lives server-side (code host and CI), not in the agent's local configuration.
- If the tool is already in use, say so: retrospective validation plus a documented interim-use justification.

## Models change every few weeks: three tiers

The validation unit is **tool + vendor + surface + context of use**, not a single model. Each tool has an approved *model envelope* (model ids or family patterns), handled as a predetermined change protocol:

1. **Initial validation** (once per tool and vendor): full IQ/OQ/PQ of the guardrails, plus the admission suite on every model in the envelope.
2. **Model admission** (hours, per new model id that matches a pre-authorised pattern fixed in the plan): rerun the fixed admission suite MA-01 headlessly. Pass: admitted with a short record, and the exact id is added to the enforced allow-list. Fail: not admitted.
3. **Re-baseline** (on triggers): new model family, guardrail-relevant tool release, new surface or context of use, admission failure or vendor terms change: MA-01 plus a targeted OQ subset. New vendor: new initial validation.

Details and a worked example: [docs/model-change-protocol.md](docs/model-change-protocol.md).

## 15-minute quick start

You need Python 3.9+, a clone of this repository, and for the checks the `gh` CLI (or a `GITHUB_TOKEN`) with read access to one of your repositories.

**1. Render your package (about 3 minutes)**

```bash
python3 kit.py init                  # wizard: organisation, roles, tools, models, contexts, risk model
# or: python3 kit.py init --defaults # fictional example answers (Acme MedSoft)
python3 kit.py render --config kit.config.json --docx   # re-render later; .docx needs pandoc
```

The documents land in `output/`. `kit.config.json` and `output/` are git-ignored: they belong in your QMS, not in this repository.

**2. Explore with the checks (about 10 minutes)**

```bash
export KIT_OPERATOR="Your Name"     # every script records who ran it on which machine
python3 checks/find_ai_footprint.py --path REPO_DIR --out evidence/_exploratory/   # AI tools and agent configs you may not know about
python3 checks/capture_baseline.py --tool claude_code --repo REPO_DIR --out evidence/_exploratory/
python3 checks/check_github_gates.py --repo OWNER/REPO --branch main --prs 20 --out evidence/_exploratory/
python3 admission/run_admission.py --tool claude_code --model <model-id> --runs 3 --out evidence/_exploratory/ --dry-run
```

Exploratory runs only inform the plan. They are not test evidence: IQ-03, OQ-01 and MA-01 are re-run after the plan and protocol are approved, into `evidence/<TOOL>/<TEST-ID>/`. For a tool that is already in use, file the check of the interim controls under `evidence/<TOOL>/INTERIM/` and reference it from section 12 of the validation plan.

Use `--tool codex` for Codex. Every script has `--help`, writes JSON and Markdown evidence with a UTC timestamp, who ran it on which machine, and the SHA-256 of the JSON, and exits non-zero when a check fails. The admission dry run prints the agent commands without calling any model; remove `--dry-run` when you have your own vendor credentials. The suite never runs in this kit's CI.

**3. Execute the protocol (the rest of the week)**

Prepare on a "day 0": tool discovery, drafts of 01 to 05 and of the shared code-host record `00-shared/code-host-gate-qualification.md`, and a sandbox repository protected like production (`checks/mirror_protection.py`). Have the approver approve the plan and the protocols *before* the first test is run. Then execute IQ, OQ and MA-01 and attach the evidence. The code-host gate tests run once per code host for all tools; the canary script in `checks/canary/` drives the negative gate tests. PQ-01 and PQ-02 run after release, on the released configuration, for at least 4 weeks or 20 AI-assisted PRs, and are reported in a signed addendum.

**4. Sign the report**

Write `07-validation-report.md` with a release decision (approved for intended use / approved with restrictions / not approved), conditional on the PQ addendum. The people sign it themselves in your eQMS or with an e-signature. The AI tool does not draft the conclusion without independent review, and the report states who wrote it.

New to the topic? Read [GUIDE.md](GUIDE.md) first. It takes five minutes. To see what an executed package looks like, browse the fictional filled example in [examples/acme-medsoft/](examples/acme-medsoft/README.md).

## What you get

```
README.md, GUIDE.md          this file; a two-page guide for QA/RA leads
README_DEV.md                template syntax and variables, how the engine works
CHANGELOG.md, CONTRIBUTING.md, LICENSE, LICENSE-docs
kit.py, kit/                 CLI (init, render, example-config, vars), wizard, strict template engine
templates/                   *.md.tmpl document templates (syntax: README_DEV.md)
checks/                      evidence scripts
  check_github_gates.py        branch protection, rulesets, Actions approval setting, review record and
                               required checks of merged PRs, agent launcher
  capture_baseline.py          tool versions, config and instruction files, SHA-256 hashes, managed-source precedence
  find_ai_footprint.py         agent config files and AI workflows in a repo (optionally org app installations)
  canary/                      throwaway PR that must NOT merge without approval (server-side merge attempt)
  mirror_protection.py         export the gate configuration; copy it to a sandbox repository
  soup_gate.py                 reference dependency / SOUP gate (approved list, registry existence)
  client_regression.py         automated client regression on a candidate tool version (CS-3a)
  README.md                    usage, evidence format, exit codes, limitations
admission/                   model admission suite MA-01: run_admission.py, tasks/*.json, fixtures/, README.md
tools/claude-code/           managed-settings.example.json, client-regression probes, notes (verified keys only)
tools/codex/                 config.example.toml, requirements.example.toml, client-regression probes, notes
docs/                        regulatory mapping, model-change protocol, adapting other tools
examples/                    fictional filled example (examples/acme-medsoft/), workflows (review evidence export,
                               SOUP gate, AI-label check), PR template and CODEOWNERS example (examples/github/)
tests/                       unit tests (python3 -m unittest discover -s tests)
.github/workflows/ci.yml     runs the tests and a smoke render on Python 3.9 and 3.12
```

The rendered package, one folder per tool:

```
output/
  00-shared/
    ai-assisted-development-work-instruction.md   rules of use, data, review duty, provenance labels, training
    tool-discovery-checklist.md                   find every AI tool actually in use
    code-host-gate-qualification.md               OQ-01 to OQ-07 and OQ-12 at code-host level, once for all tools
  CLAUDE/                                         one validation package per tool (folder = tool ID)
    01-inventory-and-intended-use.md
    02-requirements.md                            REQ-01 ... REQ-17 control objectives
    03-risk-assessment.md                         AI failure modes -> controls -> tests
    04-validation-plan.md                         approach, samples, three-tier change protocol
    05-test-protocol.md                           IQ-01..05, OQ-01..13, OQ-20/30/40, MA-01, RV-01 (in use), PQ-01/02
    06-configuration-baseline.md
    07-validation-report.md
    08-change-and-revalidation.md                 triggers, release monitoring, periodic review
  CODEX/
    ...
```

The templates adapt to your answers: risk model (CSA high / not high, or low / medium / high), contexts of use (product code, internal tooling, advisory PR review, test generation, document drafting, QMS agents), surfaces (local CLI/IDE, cloud agent, PR review bot, CI/headless), code host (GitHub, GitLab, other), model policy (envelope or pinned), GxP, and whether the tool is already in use.

## What the kit checks

| Control | Where |
|---|---|
| Use before validation | Interim-use justification with nonconformity and CAPA (04), release decision (07) |
| Unregistered AI tools | Discovery checklist and `checks/find_ai_footprint.py` (00-shared, 08) |
| Model changes | Envelope, pre-authorised patterns, MA-01, triggers (02, 04, 08) |
| Strength of the human gate | Negative tests OQ-02 to OQ-07 on 2 or more repositories (00-shared code-host record); OQ-01; PQ-01 |
| Configuration control | Hashed baseline (06, IQ-03) |
| Signatures and independence | Signatures by the people themselves; authorship and independence statement (07) |

## Regulatory mapping (summary)

| Framework | What it asks | Where the kit answers |
|---|---|---|
| ISO 13485:2016 §4.1.6 | Documented procedure; validate QMS software before initial use and after changes; risk-proportionate; records | The whole package; 04 plan, 05 protocol, 07 report, 08 change and revalidation |
| FDA QMSR (21 CFR 820, in force 2 Feb 2026) | ISO 13485 incorporated by reference (§820.7, §820.10); the old §820.70(i) no longer exists | Same documents; cite ISO 13485 §4.1.6 "as incorporated by 21 CFR 820.10" |
| FDA CSA guidance (final Sep 2025, revised Feb 2026) | Intended use, risk-based approach, assurance activities, lean record | 01 intended use, 03 risk determination, 04/05 scripted vs unscripted, 07 record |
| ISO 13485 §4.2.4, §4.2.5, §6.2, §7.4 | Document and record control, competence, supplier control | 06 baseline and instruction-file hashes, evidence rules, work instruction and training, IQ-05 vendor terms |
| ISO/TR 80002-2:2017, GAMP 5 2nd ed., ISPE GAMP AI guide | Critical thinking, risk-based toolbox, life cycle, category, supplier involvement | 01 GAMP category, 03, 04, 08 |
| IEC 62304 §5.1.4, §5.1.10, §8 | Tools in the development plan (class C), supporting items and settings under configuration control | 01 identification, 06 baseline, 08 change control |
| 21 CFR Part 11 (FDA QMSR and GxP options) | Electronic records and signatures for Part 820 records kept or signed electronically | Evidence rules, signature tables (name, date and time, meaning), Part 11 text when either option is selected |
| EU GMP Annex 11 (GxP option) | Computerised systems in medicinal-product GMP | Added when the GxP option is selected |

Full clause-by-clause table, with requirement and interpretation marked separately: [docs/regulatory-mapping.md](docs/regulatory-mapping.md).

## Tool-specific notes

- [tools/claude-code/](tools/claude-code/README.md): managed settings that matter for a validated state, per-surface delivery caveats, known guardrail limits.
- [tools/codex/](tools/codex/README.md): user defaults versus admin-enforced requirements, breaking changes in recent releases, known guardrail limits.
- [docs/adapting-other-tools.md](docs/adapting-other-tools.md): GitHub Copilot, Cursor and a checklist for any other tool, including how to drive it from the admission runner.

Vendor facts were verified against vendor documentation and source code on 2026-10-18. These tools ship new releases weekly, sometimes daily, so re-verify before you rely on a setting. Where a fact could not be verified, the kit says "verify against the vendor's current documentation" and does not guess.

## Disclaimer

This kit is not legal advice. It is a starting point, so adapt it to your QMS: your software validation procedure, document control, e-signature system and risk method take precedence over anything here. Using the kit does not by itself make a tool validated. People executing, reviewing and approving the records do.

## Licence

- Code (`kit.py`, `kit/`, `checks/`, `admission/`, `tests/`, configuration examples in `tools/` and `examples/`): [MIT](LICENSE).
- Templates and documentation (`templates/`, `docs/`, `README.md`, `GUIDE.md`, other Markdown files): [CC BY 4.0](LICENSE-docs).

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md). Developer notes: [README_DEV.md](README_DEV.md).

---

Maintained by Bernardo Plaza - regulatory, quality and security for software medical devices.
Contact: [contact placeholder]
