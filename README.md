# Jobster

Jobster is a personal first Career Agent.

It is being built first for Zak as an evidence grounded CareerBrain plus automation system that can discover remote roles, evaluate whether they are worth pursuing, prepare truthful applications, submit supported applications, track outcomes, assist with recruiter communication, and support negotiation strategy.

## Current status

Phase 0 documentation is established.

Phase 1 CareerBrain foundation is active.

## Source of truth

Read `docs/INDEX.md` first.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
jobster evaluate --profile config/profile.example.yaml --job config/job.example.json
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
jobster evaluate --profile config/profile.example.yaml --job config/job.example.json
```

## Privacy

This repository is public.

Do not commit real private CareerBrain evidence, personal application answers, browser sessions, recruiter messages, contracts, offers, or secrets.
