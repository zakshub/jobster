# Jobster Enterprise Command Center

## Status

Production implementation target for the daily Jobster experience.

The interface remains English-only and uses plain language that a first-time, non-technical user can understand.

## Product principle

The command center is not a decorative dashboard.

It must answer five questions quickly:

1. What did Jobster find?
2. Which jobs are actually worth attention?
3. What is happening right now?
4. What needs the user's decision?
5. What has already been prepared or sent?

## Information architecture

Primary navigation:

- Today
- Opportunities
- Applications
- Needs you
- Career Brain
- Activity
- Settings

The "Needs you" area is a first-class destination. Human decisions are not hidden inside error states.

## Visual language

### Core palette

- Obsidian: #101218
- Ink: #171A22
- Cobalt: #3955F6
- Cyan: #45C2FF
- Coral: #FF7868
- Lime: #9DCC65
- Lavender: #9B87F5
- Warm white surfaces on a very light neutral background

Operational colors remain semantic:

- green = safe / live / complete
- amber = waiting / manual check
- red = blocked / expired / failed
- cobalt = primary action / active system state

### Typography

Inter/system sans-serif stack.

Hierarchy is intentionally restrained:

- Page title: 25–31px
- Section title: 14–19px
- Body: 9–13px depending on density
- Metadata: 8–10px

The daily command center prioritizes scanability over marketing scale.

### Spacing

A 4px base rhythm is used through compact operational layouts.

Primary spacing steps:

4, 8, 12, 16, 20, 24, 32, 40.

### Radius

- small controls: 6–9px
- panels: 12–13px
- major narrative surfaces: 18–24px

### Elevation

Shadows are used only to communicate hierarchy:

- normal panels: almost flat
- hover / focused opportunity: low lift
- drawer / command menu / live search window: clear overlay elevation

## Icon language

Icons are original inline SVG line icons owned by the Jobster interface.

Rules:

- 24x24 viewBox
- rounded line caps and joins
- default stroke around 1.75–1.8
- no mixed filled/outlined third-party icon styles
- filled state is reserved for an active saved/bookmarked job
- icons support labels; they do not replace important words

Core symbols cover:

Today, opportunities, applications, needs-you, Career Brain, activity, settings, search, refresh, find jobs, save, verify, open source, privacy, live job search, notes and navigation.

## Artwork language

Operational surfaces stay restrained.

Original Jobster artwork is used only where it explains system behavior.

The Today screen uses the Career Orbit:

- Career Agent core at the center
- quiet orbital rings
- opportunity signals around the core
- subtle movement indicating continuous activity

This is the operational descendant of the Career Agent / constellation language defined in Onboarding V2.

It must never compete with live job data.

## Motion language

Motion communicates state, not decoration.

Included behaviors:

- view entrance: short fade + 4px rise
- opportunity cards: staggered entrance on load
- hover: 1–2px lift maximum
- running state: low-frequency pulse
- Career Orbit: slow ambient orbit
- drawer: horizontal slide
- command menu: short fade / scale
- live search lines: lightweight line entrance
- metric values: short count transition

Reduced-motion preference disables non-essential movement.

## Enterprise interaction patterns

### Command menu

Ctrl/Cmd + K opens one place for:

- page navigation
- Find jobs
- live job search window
- quick job lookup

### Job preferences

Users can:

- save a job
- add a private note
- hide a job

These preferences persist in SQLite.

### Human checkpoint queue

"Needs you" surfaces:

- unanswered required questions
- sensitive questions that need approval
- expired / unreachable job pages
- application blockers

### Career Brain readiness

The interface shows whether these are ready without exposing secrets:

- career profile
- approved application answers
- job sources
- advanced job review
- expanded web search

### Application capability

The interface explains actual support:

- Greenhouse: fill + submit foundation
- Lever: fill + submit foundation
- Ashby: fill + submit foundation
- Workday: check only

The UI must never imply support that the runtime does not have.

## Live job search window

The floating window is a real runtime activity surface.

It is:

- draggable
- resizable
- minimizable
- closable
- reopenable
- persistent in position/size in the local browser

It reports plain-English runtime events rather than fake progress.

## Accessibility

Required behaviors:

- visible keyboard focus
- Ctrl/Cmd + K keyboard navigation
- Escape closes overlays
- semantic button labels
- responsive layout
- reduced-motion support
- no color-only critical meaning
- plain-English action labels

## Truth and privacy

The UI may show status, outcomes and approved profile facts.

It must not expose:

- API keys
- hidden prompts
- hidden chain-of-thought
- private model routing
- repository internals
- private answer values unless specifically needed in an approved workflow

## Current enterprise features

- Today command center
- relevant opportunity list
- saved jobs
- private job notes
- hidden jobs
- source filtering
- match / decision filters
- sorting
- live source verification state
- application pipeline
- Needs-you queue
- Career Brain readiness
- application-site capability view
- activity history
- safe settings summary
- local display preferences
- command menu
- live job search window
- responsive design
