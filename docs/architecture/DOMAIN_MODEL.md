# Domain Model

## Core entities

### UserProfile

Personal identity and operational settings.

### CareerProfile

Verified professional history, capabilities, role direction, preferences, flexibility, and compensation policy.

### EvidenceItem

A claim supporting or contradicting the CareerBrain model.

Fields include:

id
statement
evidence_class
source
domain
sensitivity
confidence
supports
contradicts
status
notes

### Job

Normalized opportunity independent of source.

### JobPostingSnapshot

Immutable copy or structured extraction of the posting at discovery time.

### JobEvaluation

CareerBrain analysis for one job.

### DecisionRecord

Question, options, tradeoffs, risks, evidence references, recommendation, confidence, status, and outcome.

### Application

Tracks one attempt for one job.

### ApplicationAnswer

Verified reusable answer with sensitivity and approval policy.

### DocumentVariant

Resume, cover letter, or supporting document used for an application.

### AutomationReceipt

Records what Jobster actually submitted or changed.

### RecruiterConversation

Conversation thread linked to application and employer.

### Interview

Interview stage, participants, time, preparation context, and result.

### Offer

Compensation and terms.

### NegotiationRecord

Leverage analysis, strategy, counters, approvals, and outcome.

### FeedbackEvent

Zak correction or preference feedback.

### ModelUpdateProposal

Reviewable proposed CareerBrain change.

### AuditEvent

Append only record of consequential actions.

## Ownership rule

Even in single user mode, important personal entities should have an ownership field or a clean path to adding one.

This is the main structural provision for future multi user support.

## Sensitive data rule

Public Git stores schemas, policies, and safe configuration examples.

Actual resume data, contact details, recruiter messages, application answers, offers, credentials, and private evidence belong in runtime private storage.
