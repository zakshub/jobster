# Frontend v1 — Onboarding and Home Dashboard

## Canonical design

Figma:
https://www.figma.com/design/2vb3QmMUYo20C5PObeh05p/jobster

The approved personal interface is designed for a 1440px desktop web app deployed on the personal VPS.

## Canonical Figma pages

- 00 Cover
- 01 Foundations
- 02 Components
- 10 Onboarding — legacy/reference
- 11 Onboarding V2 — **canonical onboarding**
- 20 Dashboard — **canonical Home dashboard**

Detailed onboarding specification:
docs/design/ONBOARDING_V2.md

## Product design split

Onboarding and the daily command center intentionally use different visual intensity.

### Onboarding

High visual storytelling.

Its job is to:

- explain the Career Agent concept
- show invisible system behavior
- build trust
- make autonomy understandable
- create activation momentum

Implementation target:
`11 Onboarding V2`

### Dashboard

Controlled operational density.

Its job is to:

- surface live state
- prioritize work
- expose exceptions
- show evidence and auditability
- minimize distraction during daily use

Implementation target:
`20 Dashboard`

## Home dashboard

The approved Dashboard / Home frame is 1440 x 1100.

Sidebar destinations:

- Today
- Opportunities
- Applications
- Exceptions
- Conversations
- Career Brain
- Settings

Core Home content:

- VPS / worker state
- Run discovery action
- New opportunities
- High priority
- Submitted
- Needs you
- Priority opportunities
- Needs your decision
- Pipeline
- Recent activity
- Career Brain status

## Local design system

Reusable local components include:

- Button / Primary
- Button / Secondary
- Input / Default
- Status / Success
- Navigation / Active
- Metric / Tile
- Onboarding / Rail Content

The file also contains local color, spacing, radius, typography and elevation tokens plus the Jobster V2 Visual palette.

## Implementation contract

Runtime values must come from Jobster services and SQLite/API state.

Figma demo values are composition examples, not production data.

The frontend must preserve the authority and truth boundaries defined in:

- docs/product/AUTONOMY_POLICY.md
- docs/security/PRIVACY_AND_TRUTH.md
- docs/brain/CAREER_BRAIN.md

Do not expose internal provider/model names, prompts, hidden chain-of-thought, routing weights, scoring formulas, repository internals, or private learning mechanics.
