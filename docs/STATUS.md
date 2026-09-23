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
- [x] Home web-dashboard design
- [x] Legacy onboarding exploration
- [x] Research-informed Onboarding V2
- [x] Onboarding V2: 8/8 screens complete
- [x] Onboarding V2: visual QA complete
- [x] Onboarding V2: zero remaining placeholders

## Frontend state

Canonical onboarding:
`11 Onboarding V2`

Canonical daily Home:
`20 Dashboard`

Legacy onboarding:
`10 Onboarding`

Canonical Figma:
https://www.figma.com/design/2vb3QmMUYo20C5PObeh05p/jobster

Specifications:

- docs/design/ONBOARDING_V2.md
- docs/design/FRONTEND_V1.md

The Figma specification is complete.

This is a design milestone, not a claim that the HTML/React web frontend has already been implemented or deployed.

## Default safety state

Automatic final submission is OFF by default.

Turning it on does not bypass truth or sensitive-question gates.

## Owner deployment inputs

Live personal operation still requires owner-controlled runtime inputs:

1. private_data/profile.yaml with verified personal facts
2. private_data/answer_bank.yaml with approved answers
3. valid resume/document paths and portfolio URL
4. OPENAI_API_KEY for semantic CareerBrain
5. SERPAPI_API_KEY only if Google Jobs provider is enabled
6. supervised validation of each ATS against live forms before unattended auto-submit
7. VPS deployment

Coded web frontend implementation and hosting remain separate from the approved Figma design.
