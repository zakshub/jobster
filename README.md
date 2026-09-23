# Jobster

Jobster is a personal first Career Agent.

It is built first for Zak as an evidence grounded CareerBrain plus automation system that can discover remote roles, evaluate whether they are worth pursuing, prepare truthful applications, submit supported applications, track outcomes, assist with recruiter communication, and support negotiation strategy.

## Current status

**Personal MVP v0.1.0 is complete.**

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

The UI provides:

- overview metrics and operating status
- live opportunity list with CareerBrain output
- job detail drawer with matches, gaps and next action
- application-plan states and blockers
- audit activity
- SerpAPI budget visibility
- submission-window visibility
- supervised "Run search cycle" control
- application-packet preparation for evaluated jobs

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
