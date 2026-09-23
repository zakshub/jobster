# Jobster Onboarding V2

## Status

**APPROVED CANONICAL ONBOARDING DESIGN**

Figma page:
`11 Onboarding V2`

Canonical file:
https://www.figma.com/design/2vb3QmMUYo20C5PObeh05p/jobster

The earlier `10 Onboarding` page remains as a legacy/reference exploration and must not be used as the implementation target.

## Why V2 exists

The first onboarding was operationally correct but visually too close to the dashboard/settings language.

Onboarding has a different job:

- explain an unfamiliar personal Career Agent
- make the system feel alive
- build trust before requesting authority
- visualize invisible concepts such as evidence, flexibility, autonomy and readiness
- maintain momentum across setup
- create an emotional payoff at activation

V2 therefore uses narrative visual metaphors rather than repeating form-and-card layouts.

## External research basis

The redesign was informed by current onboarding and interactive-product patterns from:

- Dribbble SaaS onboarding case studies emphasizing step-based flows, visible progress and contextual guidance
- Dribbble agent onboarding examples emphasizing personalization and teaching the agent what matters
- Behance agentic AI / employee-onboarding case studies emphasizing visible workflow, next actions and human-centered assistance
- Awwwards interactive storytelling examples emphasizing immersive scenes, motion-ready composition and stronger narrative transitions

These references informed interaction principles only. Jobster V2 artwork and compositions are original to Jobster.

## Visual direction

V2 is an editorial, motion-ready product story.

Palette:

- obsidian
- warm cream
- cobalt
- cyan
- coral
- lime
- lavender
- mist

The palette is used to create visual identity and narrative hierarchy. Existing semantic product-state colors remain authoritative in operational dashboard surfaces.

## Approved 8-screen sequence

### 01 — Agent Awake

Purpose:
Introduce Jobster as an active career representative rather than a passive tool.

Visual metaphor:
A glowing Career Agent core surrounded by orbital opportunity fragments.

Core copy:
- Your career keeps moving even when you are not looking.
- CTA: Build my career agent

### 02 — Career DNA

Purpose:
Explain evidence extraction before profile configuration.

Visual metaphor:
A résumé is visibly scanned and converted into structured Career DNA.

Visible evidence examples:
- 15+ years in design
- Product / UX Architecture core
- Design Systems / Healthcare strength
- Figma ↔ Frontend bridge
- emerging AI Product Design

Important rule:
Nothing extracted becomes trusted truth without review.

### 03 — Career Constellation

Purpose:
Explain that job titles are signals rather than hard boundaries.

Visual metaphor:
Zak Career Core sits in the center.

Role distance communicates relationship:

Primary:
- Senior Product Designer
- UX Architect

Adjacent:
- UX Engineer
- AI Product Designer

Explore:
- Technical UI

### 04 — Worthwhile Move

Purpose:
Make Career Economics understandable immediately.

Visual metaphor:
Three dominant overlapping decision forces:

- MONEY
- GROWTH
- INTEREST

Rule:
A move is worthwhile when it materially improves at least two of the three.

Secondary satellites:
- Global exposure
- Ownership
- Remote quality
- Stability
- Portfolio value
- Learning

### 05 — Authority Perimeter

Purpose:
Explain bounded autonomy spatially.

Visual metaphor:
Concentric operating rings.

Inner:
AUTOMATIC
- search
- evaluate
- prepare
- track

Middle:
VERIFIED
- submit only with approved facts and documents

Outer:
HUMAN GATE
- work authorization
- visa
- legal
- CAPTCHA
- offer acceptance

### 06 — Opportunity Intake

Purpose:
Show why Jobster is not dependent on one job board.

Visual metaphor:
Multiple opportunity streams converge into one Jobster Intake core and emerge as normalized unique opportunities.

Sources shown:
- Remote OK
- Remotive
- We Work Remotely
- Google
- LinkedIn alerts

### 07 — Pre-flight

Purpose:
Create a visible review gate before activation.

Visual metaphor:
82% readiness core with system modules orbiting it.

Ready:
- Career Identity
- Preferences
- Sources
- Authority

Unresolved:
- Portfolio URL
- Work Authorization

Explicit message:
Two facts prevent full autonomy.

### 08 — Jobster Online

Purpose:
Deliver the activation payoff.

Visual metaphor:
The Jobster core becomes fully illuminated and active.

Telemetry examples:
- Career Model active
- 3 Sources live
- 60m discovery cycle
- Rules loaded

Primary statement:
JOBSTER ONLINE

Supporting statement:
You do not need to keep searching. Jobster starts from here.

CTA:
Enter command center

## Motion intent for implementation

V2 is designed to support motion without requiring motion for basic comprehension.

Recommended implementation behavior:

- orbital opportunity cards drift subtly
- Career DNA scan moves vertically through the résumé
- constellation links draw into place
- Career Economics circles ease and overlap
- Authority rings pulse from inner to outer
- source streams animate toward Intake core
- Pre-flight modules lock into orbit
- Online core blooms once during activation, then settles

Respect reduced-motion preferences.

## Implementation contract

The web implementation should treat:

- `11 Onboarding V2` as canonical onboarding
- `20 Dashboard` as canonical home/dashboard
- `10 Onboarding` as legacy/reference only

Do not reproduce V2 as static cards while discarding the visual metaphors. The visual storytelling is part of the onboarding UX, not optional decoration.

Do not expose internal model/provider names, prompts, hidden chain-of-thought, scoring formulas, repository internals or private learning mechanics.
