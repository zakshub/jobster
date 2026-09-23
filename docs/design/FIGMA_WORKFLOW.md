# Figma Workflow

## Canonical file

https://www.figma.com/design/2vb3QmMUYo20C5PObeh05p/jobster

Current state observed during planning:

Page 1 exists and contains no designed interface yet.

## Rule

Do not build a decorative dashboard before the backend loop needs a human interface.

The frontend exists to support operational decisions.

## First justified UI surfaces

### Today

Shows discovered, rejected, shortlisted, blocked, submitted, recruiter reply, and interview counts.

### Opportunity detail

Shows posting facts separately from CareerBrain reasoning.

### Application queue

Shows ready, blocked, failed, and submitted applications.

### Exceptions

Shows questions Jobster cannot responsibly answer by itself.

### CareerBrain

Shows current profile assumptions, capability confidence, preferences, and pending model update proposals.

### Recruiter and negotiation workspace

Shows thread context, leverage analysis, strategy, and draft responses.

### Settings

Sources, autonomy policy, compensation boundaries, documents, and answer bank.

## UX principles

1. Reasoning must be inspectable.
2. Fact and inference must be visually separated.
3. Unknowns must be obvious.
4. Automated actions must have receipts.
5. High impact actions must expose authority state.
6. The interface should optimize review and correction, not decoration.
7. Avoid generic AI dashboard patterns unless they genuinely fit the task.

## Design implementation relationship

Git docs define behavior.

Figma defines approved interface design.

Frontend code implements the approved design and consumes the same backend services used by CLI and workers.
