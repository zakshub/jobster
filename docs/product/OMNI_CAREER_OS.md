# Jobster Omni Career OS

## Purpose

Jobster is evolving from a job finder into a private career operating system.

The intended loop is:

**See → Understand → Filter → Decide → Prepare → Act within permission → Track → Learn → Explain → Ask only when human judgment is needed.**

"Omni" does not mean unlimited or infallible intelligence. It means the product connects the major parts of a career workflow without hiding uncertainty or taking authority away from the user.

## Current implemented product areas

### Daily command center

- Today's focus / mission queue
- Agent pulse
- strong opportunities
- human checkpoints
- application pipeline
- source health / usage
- notifications

### Opportunity intelligence

- strict role relevance before semantic review
- job fit score and decision
- requirement-by-requirement assessment when available
- decision confidence
- career-value dimensions
- live job-page verification
- job comparison
- saved jobs
- private notes
- hidden jobs
- explicit user feedback
- source, salary, freshness and application state

### Career intelligence

- application funnel
- funnel bottleneck diagnosis
- source performance
- role-family signals
- salary evidence from stored matching jobs
- repeated gap signals
- Career Brain evidence health
- company activity signals
- career goals

### Companies and relationships

- company watchlist
- company summaries from observed jobs
- contacts
- recruiter-message interpretation and reply drafting
- outreach draft queue

### Interview and offer work

- interview records
- STAR story bank
- offer records
- negotiation advice using the existing compensation policy
- offer decision workspace

### Application automation

- direct supported application pages
- job-board-to-real-application-link discovery
- Greenhouse, Lever and Ashby application foundations
- generic company career forms can be inspected/prepared under supervision
- Workday remains inspection-only
- multi-page application navigation for supported ATS flows
- later-page unknown questions become human checkpoints
- login and CAPTCHA stop automation
- final submission confirmation detection
- local screenshot proof after a confirmed submission
- application artifacts associated with the job

### Authority and safety

Separate permissions exist for:

- search
- application preparation
- final submission
- contact
- follow-up

Each action can be Off, Ask, or Auto at the product level.

Final application submission still also requires the private configuration to enable auto-submit. The UI permission alone cannot silently turn submission on.

Emergency Stop turns every automatic action permission off without deleting data.

### Personal workflow

- command menu
- notifications
- watch rules
- data export
- installable PWA shell
- reduced motion
- compact job list
- responsive desktop/tablet/mobile layout
- live draggable/resizable job-search window

## Design language

The Omni Career OS intentionally avoids generic AI-dashboard styling.

### Human editorial direction

- warm paper background rather than cold white SaaS canvas
- off-white operational surfaces
- charcoal navigation
- cobalt primary actions with restrained coral/lime/lavender semantic accents
- Inter/system sans for operational reading
- editorial serif headings for authored hierarchy
- asymmetric-but-controlled corner geometry
- subtle grain
- small imperfect editorial marks
- original line icon set
- original Career Orbit / network artwork
- motion used to explain state rather than decorate empty space

The UI remains enterprise-readable and accessible. "Human" does not mean messy or nostalgic.

## Truth boundaries

The following are **not** represented as completed integrations when they are not actually connected:

### Email sending

Jobster can store outreach drafts and reason about recruiter messages.

It does not send email until an authenticated mail connector/provider is connected and the Contact authority permits the action.

### Calendar sync

Jobster can store interview records.

It does not claim live Google/Outlook calendar synchronization until a calendar connection is explicitly configured.

### LinkedIn messaging

Job discovery may include LinkedIn-indexed pages through approved web search.

Jobster does not claim a direct LinkedIn messaging or scraping integration.

### Workday

Workday remains inspection-only until a dedicated multi-step flow has been validated.

### Arbitrary career websites

Jobster can locate many real application links and prepare ordinary company career forms, but arbitrary custom forms are not treated as safely auto-submittable without validation.

### CAPTCHA and login

Automation stops and asks for a human check.

### Salary intelligence

Salary analysis uses stored job salary data. It does not silently convert currencies or invent market data.

### Career learning

User feedback is stored as evidence. It does not silently mutate identity, legal answers, or career preferences.

## Auto-apply conditions

A final automatic submission requires all of the following:

1. the job is eligible and selected for pursuit
2. application preparation is allowed
3. the application site supports submission
4. every required answer is approved
5. sensitive answers have explicit permission
6. no CAPTCHA/login/manual checkpoint is present
7. the private config has `auto_submit: true`
8. Submit authority is enabled and set to Auto
9. the submission time window is open
10. the per-cycle application limit has not been reached
11. Jobster can detect a real final submission control

A confirmed submission is recorded only when the post-submit page contains a supported confirmation signal.

## Current next hardening frontier

The product is broad, but the remaining engineering frontier is depth:

- site-specific validation for more application systems
- richer custom form widgets
- authenticated email connector
- calendar connector
- reply ingestion
- public recruiter/contact enrichment providers
- richer interview debrief/outcome learning
- production deployment, authentication and encrypted multi-user storage if Jobster becomes a shared SaaS product

For the personal local-first product, the current architecture intentionally prioritizes correctness, explainability and user authority over maximum unattended action.
