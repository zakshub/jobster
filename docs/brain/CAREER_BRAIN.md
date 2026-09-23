# Jobster CareerBrain

## Definition

CareerBrain is the reasoning layer that models how a specific person evaluates and pursues career opportunities.

Zak is the first CareerBrain profile.

CareerBrain is not Zak consciousness and is not a claim that the model literally thinks exactly like him.

It is an evidence backed, correctable computational model of career judgment.

## Architecture

CareerBrain has two levels.

### Generic CareerBrain

Reusable reasoning structure that can support any future user.

### Zak Career Profile

The first personal instance containing Zak evidence, preferences, capability model, flexibility, career direction, compensation boundaries, and correction history.

Do not hard code Zak logic throughout the application.

## Reasoning dimensions

### Opportunity understanding

CareerBrain determines what the employer is actually trying to hire for.

It distinguishes:

1. Title.
2. Actual responsibilities.
3. Core capability requirements.
4. Domain knowledge.
5. Tool requirements.
6. Nice to have requirements.
7. Hidden seniority expectations.
8. Leadership expectations.
9. Implementation expectations.
10. Work arrangement and geographic constraints.

### Capability alignment

For each requirement classify the person as:

strong evidence
supported
adjacent
learnable
weak evidence
not claimed
hard blocker
unknown

This prevents simple percentage matching.

### Interest model

Estimate whether Zak is likely to find the work worthwhile.

Signals include:

1. Complex system design.
2. Product ownership.
3. UX architecture.
4. Design systems.
5. AI native product work.
6. Healthcare or other meaningful product domains.
7. Implementation aware design.
8. International product exposure.
9. Repetitive visual production.
10. Generic marketing production.
11. Learning potential.
12. Portfolio value.

Interest must remain correctable.

### Flexibility model

A missing requirement must be classified as one of:

1. Fundamental.
2. Domain specific but learnable.
3. Tool specific and learnable.
4. Terminology difference.
5. Nice to have.
6. Actual eligibility blocker.
7. Unknown.

### Career value model

Evaluate opportunities across:

1. Compensation.
2. Career growth.
3. Interesting work.
4. Scope and ownership.
5. Global exposure.
6. Future positioning.
7. Stability.
8. Remote quality.
9. Time zone burden.
10. Contract quality.
11. Benefits.
12. Portfolio value.
13. Learning value.

### Pursuit strategy

Possible outputs:

ignore
watch
low_priority
apply
high_priority
aggressive_pursuit

The decision must include a reason and confidence.

### Positioning strategy

For each pursued role choose which truthful strengths should lead the application.

Examples:

product systems thinker
UX architect
implementation aware product designer
design systems specialist
healthcare product designer
AI product designer

Positioning can change by job while underlying facts remain fixed.

## Decision output

A CareerBrain evaluation contains:

1. Summary.
2. Eligibility.
3. Role interpretation.
4. Strong matches.
5. Learnable gaps.
6. Hard blockers.
7. Interest.
8. Career value.
9. Compensation view.
10. Pursuit decision.
11. Positioning.
12. Confidence.
13. Evidence references.
14. Unknowns.
15. Next action.

## Product rule

No single numeric score is allowed to replace reasoning.

Scores may summarize dimensions, but explanation and blockers remain authoritative.
