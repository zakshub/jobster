# Frontend v1 — Onboarding and Home Dashboard

## Canonical design

Figma:
https://www.figma.com/design/2vb3QmMUYo20C5PObeh05p/jobster

The approved v1 interface is designed for a 1440px desktop web app deployed on the personal VPS.

## Design direction

Jobster is a career command center, not a generic AI dashboard.

The design uses:

- off-white operational workspace
- deep ink navigation
- one controlled electric-blue action color
- semantic green, amber, and red only when state meaning exists
- Inter typography
- thin borders and restrained elevation
- dense but calm operational layouts
- evidence, state, warnings, approvals, outputs, and next actions as the visible product language

The frontend must not expose internal provider/model names, prompts, hidden chain-of-thought, routing weights, scoring formulas, repository internals, or private learning mechanics.

## Figma page map

- 00 Cover
- 01 Foundations
- 02 Components
- 10 Onboarding
- 20 Dashboard

## Onboarding

Eight desktop screens are approved:

1. Welcome
2. Profile & Evidence
3. Career Direction
4. Preferences & Boundaries
5. Application Authority
6. Connections & Sources
7. Review & Activate
8. Ready

### Welcome

Explains the product promise and three trust rules:

- only verified career facts
- consequential actions stay inside user-defined authority
- recommendations remain reviewable and correctable

### Profile & Evidence

Captures or imports the career source of truth.

The screen visibly distinguishes verified evidence from missing facts such as portfolio URL.

### Career Direction

Defines target role direction and work boundaries without treating job titles as absolute filters.

### Preferences & Boundaries

Models positive and negative work preferences plus the career-economics rule.

The current personal design shows the USD 6.5k monthly target and deliberately leaves the minimum unresolved.

### Application Authority

Shows three explicit autonomy levels:

- Automatic
- Can auto-submit when verified
- Always ask

Auto-submit is visibly OFF during supervised rollout.

### Connections & Sources

Shows:

- Remote OK
- Remotive
- We Work Remotely
- optional Google Jobs provider
- LinkedIn alerts and user-supplied links

LinkedIn is not presented as a hidden scraping dependency.

### Review & Activate

Summarizes career and automation setup and exposes unresolved facts before activation.

### Ready

Confirms that discovery/evaluation can start while unattended auto-submit remains disabled until ATS validation is complete.

## Home dashboard

The approved Dashboard / Home frame is 1440 x 1100.

### Sidebar

Destinations:

- Today
- Opportunities
- Applications
- Exceptions
- Conversations
- Career Brain
- Settings

Worker state and last-cycle time appear at the bottom.

### Header

Shows:

- personal greeting
- active-representation statement
- VPS online state
- Run discovery now action

### Operational metrics

Four summary metrics:

- New opportunities
- High priority
- Submitted
- Needs you

These are operational metrics, not vanity analytics.

### Priority opportunities

Shows opportunity decisions such as:

- High priority
- Apply
- Watch

Each role includes short evidence/reason cues rather than one opaque numeric score.

### Needs your decision

Surfaces blocked work such as:

- unresolved work authorization
- missing compensation range

The language states that Jobster stopped instead of guessing.

### Pipeline

Shows the current application flow from discovered through interview.

### Recent activity

Shows worker actions and links to the complete audit history.

### Career Brain

Shows evidence quality, stable direction, unresolved facts, and correction access without exposing model/provider internals.

## Local design system

The file contains reusable local components:

- Button / Primary
- Button / Secondary
- Input / Default
- Status / Success
- Navigation / Active
- Metric / Tile
- Onboarding / Rail Content

The file also contains local color, spacing, radius, typography, and elevation tokens.

## Implementation contract

The coded web app should reproduce these approved frames using reusable frontend components mapped to backend state.

Do not implement static fake dashboard data as production truth. Demo values in Figma are layout examples. Runtime values must come from Jobster services and SQLite/API state.

The frontend must preserve the autonomy and truth boundaries defined in:

- docs/product/AUTONOMY_POLICY.md
- docs/security/PRIVACY_AND_TRUTH.md
- docs/brain/CAREER_BRAIN.md
