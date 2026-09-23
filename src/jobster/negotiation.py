from __future__ import annotations

from .models import CareerProfile, NegotiationAdvice, NegotiationContext


def negotiation_advice(profile: CareerProfile, context: NegotiationContext) -> NegotiationAdvice:
    score = 0
    if context.company_initiated:
        score += 2
    score += min(context.interview_rounds, 4)
    score += min(context.urgency_signals, 2)
    score += min(context.strong_positive_signals, 3)
    score += min(context.competing_processes, 2)

    if score <= 2:
        leverage = "weak"
    elif score <= 4:
        leverage = "limited"
    elif score <= 6:
        leverage = "balanced"
    elif score <= 9:
        leverage = "strong"
    else:
        leverage = "very_strong"

    policy = profile.compensation
    offer = context.current_offer_monthly
    target = policy.target_monthly
    minimum = policy.minimum_monthly
    anchor = policy.anchor_monthly
    unknowns = []
    strategy = []
    counter = None

    if offer is None:
        unknowns.append("Current offer amount is unknown")
        strategy.append("Ask for the approved compensation range before naming a number when possible")
    else:
        if minimum is not None and offer < minimum:
            strategy.append("The current offer is below the configured minimum")
        if target is not None:
            if offer < target:
                counter = target
                strategy.append("Counter toward the configured target rather than negotiating from the current offer")
            else:
                counter = max(target, round(offer * 1.08, 2))
                strategy.append("The offer meets target, so use a measured value based counter rather than immediate acceptance")
        if anchor is not None:
            counter = anchor if counter is None else min(max(counter, offer or 0), anchor)

    if context.published_max_monthly is not None and counter is not None:
        counter = min(counter, context.published_max_monthly)
        strategy.append("Keep the counter within the known published range")

    if leverage in {"strong", "very_strong"}:
        strategy.append("Preserve optionality and avoid making unnecessary concessions early")
    if context.company_initiated:
        strategy.append("Employer initiated contact, which is a legitimate leverage signal but not proof of unlimited budget")
    if context.interview_rounds >= 3:
        strategy.append("The company has invested materially in the process; use that investment carefully in negotiation")

    non_salary = context.non_salary_priorities or [
        "bonus",
        "paid leave",
        "equipment budget",
        "compensation review timing",
        "contract security",
        "working hour flexibility",
        "title or scope",
    ]

    return NegotiationAdvice(
        leverage=leverage,
        recommended_counter_monthly=counter,
        walk_away_below_monthly=minimum,
        strategy=strategy,
        non_salary_levers=non_salary,
        unknowns=unknowns,
        requires_approval=True,
    )
