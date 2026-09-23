# Jobster Vision

## Product statement

Jobster is a personal Career Agent that continuously searches for suitable remote work, understands opportunities in context, reasons about whether they are worth pursuing for a specific person, prepares truthful applications, submits supported applications, tracks outcomes, assists with recruiter communication, and develops negotiation strategy.

For the first implementation, that person is Zak.

## North star experience

Zak should be able to leave Jobster running and later see:

Jobs discovered
Clearly irrelevant
Worth examining
Strong fit
High priority
Applications submitted
Need Zak input
Recruiter replies

The value is not the number of applications.

The value is how much high quality career work Jobster completes while preserving Zak judgment and factual accuracy.

## What makes Jobster different

Jobster is not primarily a keyword matcher.

It should understand:

1. What the role actually requires.
2. Which requirements are fundamental.
3. Which gaps are realistically learnable.
4. Whether Zak would enjoy the work.
5. Whether the role improves money, growth, interesting work, scope, global exposure, stability, or future positioning.
6. Whether location, time zone, contract structure, work authorization, and compensation are realistic.
7. Whether the company and role deserve aggressive pursuit, cautious pursuit, or rejection.
8. What truthful positioning should lead the application.
9. How recruiter behavior changes negotiation leverage.
10. When Jobster should act automatically and when it should stop.

## Personal first, product later

Version one is for one person.

Do not build yet:

1. Billing.
2. Public sign up.
3. Teams.
4. Multi tenant administration.
5. Marketing website.
6. General purpose onboarding.
7. Complex organization permissions.

Preserve:

1. A generic CareerBrain interface.
2. Per user isolated profile data.
3. Provider adapters.
4. API boundaries.
5. Durable audit records.
6. Replaceable model providers.
7. Storage that can later migrate from local single user mode to hosted multi user mode.

## Success metrics

1. Relevant opportunities discovered.
2. High quality applications submitted.
3. Recruiter response rate.
4. Interview conversion rate.
5. Offer conversion rate.
6. Manual intervention rate.
7. False factual answer count.
8. Duplicate application count.
9. CareerBrain decision agreement with Zak after review.
10. Negotiation outcome quality when enough evidence exists.
