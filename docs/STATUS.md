# Jobster Status

## Status

**PERSONAL RUNTIME + ENTERPRISE COMMAND CENTER IMPLEMENTED**

Validated on GitHub Actions after the final application-orchestration fix.

## Personal MVP capability checklist

- [x] Documentation source of truth
- [x] CareerBrain deterministic baseline
- [x] Optional semantic CareerBrain
- [x] Evidence and unknown preservation
- [x] Multi source discovery adapters
- [x] Himalayas public API discovery
- [x] Expanded source registry including LinkedIn, startup, remote, design, general and ATS-hosted listings
- [x] Source failure isolation
- [x] Source-level caching for long-running worker
- [x] Persistent SerpAPI quota guard: 250 plan, 25-query reserve, max 7/day over 30 days
- [x] Automatic submission blackout: Friday 18:00 through Monday 09:00 Asia/Karachi
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

The local production web interface is now implemented and connected to live Jobster runtime data. VPS deployment remains separate.

## Default safety state

Automatic final submission is OFF by default.

Turning it on does not bypass truth or sensitive-question gates.

## Owner deployment inputs

Live personal operation still requires owner-controlled runtime inputs:

1. private_data/profile.yaml with verified personal facts
2. private_data/answer_bank.yaml with approved answers
3. valid resume/document paths and portfolio URL
4. OPENAI_API_KEY for semantic CareerBrain
5. SERPAPI_API_KEY if Google Jobs or expanded web-source discovery is enabled
6. supervised validation of each ATS against live forms before unattended auto-submit
7. VPS deployment

Local coded frontend implementation is complete. VPS hosting remains separate.

## Web command center

- [x] Figma-derived visual system implemented
- [x] Local FastAPI web runtime
- [x] Live SQLite dashboard metrics
- [x] Opportunity list and detail view
- [x] Application-plan visibility
- [x] Audit trail
- [x] Search quota and submission-window status
- [x] Manual run-cycle control
- [x] Application-packet preparation from UI
- [x] Default localhost-only binding
- [x] Auto-submit remains governed by the existing application policy

## Intelligent research console

- [x] Strict career-lane title intake before semantic evaluation
- [x] Per-source and per-cycle relevance caps
- [x] Existing irrelevant stored jobs hidden from the default opportunity view
- [x] Source-diversity visibility
- [x] Live cycle event stream
- [x] Draggable, resizable, minimizable and closable terminal window
- [x] Source URL verification with live/protected/expired/unreachable states
- [x] Application preparation re-verifies source before creating artifacts
- [x] Common job-feed text encoding repair
- [x] Reduced-motion accessibility for UI animations

## Plain-English product language

- [x] User-facing copy is English-only
- [x] User-facing wording avoids developer jargon where a simple phrase is available
- [x] Beginner, junior, senior and non-technical users should be able to understand core actions without knowing APIs, ATS terminology, semantic scoring or backend architecture
- [x] Technical names remain internal unless they are necessary to explain a real limitation


## Enterprise command center

- [x] Enterprise information architecture: Today, Opportunities, Applications, Needs you, Career Brain, Activity, Settings
- [x] Original inline SVG icon system
- [x] Career Orbit operational artwork
- [x] Saved jobs
- [x] Hidden jobs
- [x] Private job notes
- [x] Source filter, match filter and sorting
- [x] First-class human decision queue
- [x] Application pipeline summaries
- [x] Career Brain readiness
- [x] Application-site capability visibility
- [x] Ctrl/Cmd + K command menu
- [x] Persistent draggable/resizable live job-search window
- [x] Display preferences for reduced motion, compact list and live-window behavior
- [x] Responsive desktop/tablet/mobile layout
- [x] DOM/icon contract tests
- [x] Plain-English interface standard

Canonical enterprise UI specification:
`docs/design/ENTERPRISE_COMMAND_CENTER.md`
