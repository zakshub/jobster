# Figma Workflow

## Canonical file

https://www.figma.com/design/2vb3QmMUYo20C5PObeh05p/jobster

## Current approved state

The v1 personal web interface is now designed in Figma.

Pages:

- 00 Cover
- 01 Foundations
- 02 Components
- 10 Onboarding
- 20 Dashboard

The approved design includes the complete eight-screen onboarding flow and the desktop Home dashboard.

Detailed screen specification:
docs/design/FRONTEND_V1.md

## Rule

The frontend exists to support operational decisions, review, correction, and safe automation.

It must not become decorative AI theater.

## UX principles

1. Reasoning outputs must be inspectable without exposing hidden chain-of-thought.
2. Facts, inferences, unknowns, and blockers should remain visually distinguishable.
3. Unknowns must be obvious.
4. Automated actions must have receipts/history.
5. High-impact actions must expose authority state.
6. The interface should optimize review and correction, not decoration.
7. State colors are semantic, not ornamental.
8. Internal provider/model names, prompts, routing formulas, and repository mechanics remain hidden.
9. User-facing language describes outcomes and actions: preparing context, processing, quality check, needs review.
10. Figma demo data is illustrative; production UI consumes live Jobster state.

## Design implementation relationship

Git docs define behavior and product truth.

Figma defines the approved visual and interaction specification.

Frontend code should implement Figma through reusable UI components while consuming the same Jobster services used by CLI and workers.

The current Figma design does not by itself mean the web frontend code is deployed. Implementation and VPS hosting are separate delivery steps.
