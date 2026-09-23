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
