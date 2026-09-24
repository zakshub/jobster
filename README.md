# Jobster

Jobster is a personal first Career Agent.

It is built first for Zak as an evidence grounded CareerBrain plus automation system that can discover remote roles, evaluate whether they are worth pursuing, prepare truthful applications, submit supported applications, track outcomes, assist with recruiter communication, and support negotiation strategy.

## Current status

**Personal runtime plus enterprise command center is implemented.**

The repository contains the full personal MVP workflow:

discovery
→ normalization and deduplication
→ CareerBrain evaluation
→ semantic reasoning when configured
→ application preparation
→ ATS inspection and safe execution
→ persistent tracking and receipts
→ recruiter guidance
→ negotiation strategy
→ repeatable worker runtime

Automatic final submission remains OFF by default until the personal answer bank and live ATS flows are validated.

## Web command center

Jobster now includes a local browser UI connected directly to the existing Python runtime and SQLite state.

The visual language is derived from the canonical Figma Jobster cover: dark `#12141a` brand surface, `#3955f6` primary action, Inter typography, restrained borders, evidence-first hierarchy and the original product copy.

Run it locally:

```powershell
$env:JOBSTER_PROFILE="private_data/profile.yaml"
$env:JOBSTER_SEARCH="config/search.yaml"
$env:JOBSTER_DB="data/jobster.db"
jobster ui
```

Then open `http://127.0.0.1:8765`.

The UI now uses a strict career-lane intake gate before semantic evaluation, so broad job-board feeds do not flood the database with unrelated engineering, sales, HR, support or course/content roles. It also includes a draggable/resizable live research terminal and on-demand source verification.

The enterprise command center provides:

- Today view focused on useful actions rather than dashboard decoration
- strict opportunity filtering and source diversity
- saved jobs, hidden jobs and private job notes
- opportunity sorting, source filters and live-check status
- application pipeline
- first-class "Needs you" queue for questions and blockers
- Career Brain readiness and application-site capability view
- activity history
- plain-English settings summary
- Ctrl/Cmd + K command menu
- original Jobster SVG icon language
- original Career Orbit system artwork
- subtle micro-interactions with reduced-motion support
- one-click job search with a draggable/resizable live activity window
- source verification before application preparation
- application-packet preparation for evaluated jobs
- visible application filling that stops for your final review and Submit click
- Gmail application drafts with contextual copy and an approved resume attachment

See `docs/design/ENTERPRISE_COMMAND_CENTER.md` for the current design and interaction contract.

See `docs/product/SUPERVISED_APPLICATIONS.md` for application redirects,
LinkedIn boundaries, login/account handoffs, and Gmail draft setup.

The UI does not expose private keys, internal prompts or hidden reasoning.

## Discovery coverage

Direct adapters are included for Remote OK, Remotive, We Work Remotely, and Himalayas.

Optional expanded discovery can search LinkedIn Jobs, Wellfound, YC, remote boards, design boards, general boards, and direct ATS-hosted company listings through grouped domain-restricted web search. This requires a private `SERPAPI_API_KEY`.

See `docs/SOURCE_REGISTRY.md` for the complete source universe and operating rules.

## Source of truth

Read `docs/INDEX.md` first.

Current implementation status is recorded in `docs/STATUS.md`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp config/profile.example.yaml private_data/profile.yaml
cp config/answer_bank.example.yaml private_data/answer_bank.yaml
cp config/search.example.yaml config/search.yaml
jobster doctor --profile private_data/profile.yaml --search config/search.yaml
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item config\profile.example.yaml private_data\profile.yaml
Copy-Item config\answer_bank.example.yaml private_data\answer_bank.yaml
Copy-Item config\search.example.yaml config\search.yaml
jobster doctor --profile private_data\profile.yaml --search config\search.yaml
```

## Privacy

This repository is public.

Do not commit real private CareerBrain evidence, personal application answers, browser sessions, recruiter messages, contracts, offers, or secrets.
