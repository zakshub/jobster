# Jobster Status

## Status

**PERSONAL MVP COMPLETE — v0.1.0**

Validated on GitHub Actions after the final application-orchestration fix.

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
- [x] CI passing on the final code state
- [x] Figma design system and foundations
- [x] Complete eight-screen onboarding design
- [x] Home web-dashboard design

## Frontend state

The approved Figma specification is complete.

This is a design milestone, not a claim that the HTML/React web frontend has already been implemented or deployed.

Canonical design:
https://www.figma.com/design/2vb3QmMUYo20C5PObeh05p/jobster

Frontend specification:
docs/design/FRONTEND_V1.md

## Default safety state

Automatic final submission is OFF by default.

Turning it on does not bypass truth or sensitive-question gates.

## Owner deployment inputs

The software MVP is complete.

Live personal operation still requires owner-controlled runtime inputs:

1. private_data/profile.yaml with verified personal facts
2. private_data/answer_bank.yaml with approved answers
3. valid resume/document paths and portfolio URL
4. OPENAI_API_KEY for semantic CareerBrain
5. SERPAPI_API_KEY only if Google Jobs provider is enabled
6. supervised validation of each ATS against live forms before unattended auto-submit
7. VPS deployment

The coded web frontend is also a separate implementation/deployment step after the approved Figma design.

These are deployment inputs and implementation follow-through, not missing CareerAgent workflow architecture.
