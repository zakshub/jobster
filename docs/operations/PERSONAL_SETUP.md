# Personal Setup

The repository is public. Real personal data belongs in private_data and is ignored by Git.

## Required local files

Copy:

config/profile.example.yaml
to
private_data/profile.yaml

Then replace example values with verified personal facts.

Copy:

config/search.example.yaml
to
config/search.yaml

## Career evidence

The personal profile should contain only facts that can be supported by professional records, artifacts, explicit correction, or other evidence.

Do not put secrets, work authorization details, sensitive screening answers, recruiter messages, contracts, or offer letters in Git.

## Semantic CareerBrain

Set OPENAI_API_KEY to enable semantic reasoning.

JOBSTER_OPENAI_MODEL defaults to gpt-5.6-sol and can be changed.

Semantic reasoning is only a reasoning layer. Deterministic hard blockers are preserved.

## Google Jobs

Google Jobs discovery is optional and disabled by default.

If enabled, configure SERPAPI_API_KEY.

## Browser execution

Install Chromium after Python dependencies:

playwright install chromium

Run Jobster doctor before production use.

## Recommended personal rollout

1. Run deterministic evaluation on known jobs.
2. Compare decisions with Zak.
3. Enable semantic reasoning.
4. Validate application packets.
5. Use ATS execution in non-submitting or manually supervised runs.
6. Enable automatic final submission only after the relevant answer bank is complete and a specific ATS flow has been validated.
