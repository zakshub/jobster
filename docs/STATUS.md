# Jobster Status

## Personal MVP capability checklist

- [x] Documentation source of truth
- [x] CareerBrain deterministic baseline
- [x] Optional semantic CareerBrain
- [x] Evidence and unknown preservation
- [x] Multi source discovery adapters
- [x] Deduplication
- [x] ATS detection
- [x] SQLite workflow state
- [x] Application safety policy
- [x] Reusable verified answer bank with aliases
- [x] Resume tailoring from verified profile facts
- [x] Application packet generation
- [x] Greenhouse browser executor foundation
- [x] Lever browser executor foundation
- [x] Ashby browser executor foundation
- [x] Workday inspection-only safety boundary
- [x] Autonomous worker application orchestration
- [x] Submission receipts and verification state
- [x] Recruiter message classification and draft guidance
- [x] Negotiation strategy engine
- [x] Repeatable worker runtime
- [x] Docker and Compose
- [x] Runtime doctor command
- [x] CI configuration

## Default safety state

Automatic final submission is OFF by default.

Turning it on does not bypass truth or sensitive-question gates.

## Remaining owner deployment inputs

The software MVP is complete when code and CI pass. Live personal operation additionally requires owner-controlled data and credentials:

1. private_data/profile.yaml with verified personal facts
2. private_data/answer_bank.yaml with approved answers
3. valid resume/document paths and portfolio URL
4. OPENAI_API_KEY for semantic CareerBrain
5. SERPAPI_API_KEY only if Google Jobs provider is enabled
6. supervised validation of each ATS against live forms before unattended auto-submit
7. VPS deployment

These are deployment inputs rather than missing core workflow code.
