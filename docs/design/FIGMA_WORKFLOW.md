# Figma Workflow

## Canonical file

https://www.figma.com/design/2vb3QmMUYo20C5PObeh05p/jobster

## Current approved state

Pages:

- 00 Cover
- 01 Foundations
- 02 Components
- 10 Onboarding — legacy/reference
- 11 Onboarding V2 — canonical onboarding
- 20 Dashboard — canonical Home dashboard

Specifications:

- docs/design/ONBOARDING_V2.md
- docs/design/FRONTEND_V1.md

## Rule

Git docs define product behavior and implementation authority.

Figma defines the approved visual and interaction specification.

### Onboarding

Onboarding may use richer editorial storytelling, bespoke artwork and motion-ready compositions when they clarify the Career Agent concept.

Visual metaphors are allowed when they explain real product behavior.

### Operational product surfaces

Dashboard, applications, exceptions, settings and review workflows remain more restrained.

They prioritize:

- state
- evidence
- risk
- approval
- next action
- auditability

## UX principles

1. Facts, inferences, unknowns and blockers remain distinguishable.
2. Unknowns must be obvious.
3. Automated actions must have receipts/history.
4. High-impact actions must expose authority state.
5. Visual richness must explain or reinforce product meaning.
6. Internal provider/model names, prompts, hidden chain-of-thought, routing formulas and repository mechanics remain hidden.
7. Figma demo data is illustrative; production UI consumes live Jobster state.
8. Reduced-motion preferences must be respected when V2 motion concepts are implemented.

## Implementation relationship

Use `11 Onboarding V2` for onboarding implementation.

Do not implement `10 Onboarding` as the production onboarding.

Use `20 Dashboard` for the initial daily command-center Home surface.

The Figma designs do not by themselves mean the coded web frontend is deployed. Implementation and VPS hosting remain separate delivery steps.
