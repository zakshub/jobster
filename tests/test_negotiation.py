from jobster.models import CareerProfile, CompensationPolicy, NegotiationContext
from jobster.negotiation import negotiation_advice


def test_negotiation_uses_target_and_requires_approval():
    profile = CareerProfile(
        profile_id="p",
        display_name="Candidate",
        compensation=CompensationPolicy(currency="USD", minimum_monthly=5000, target_monthly=6500, anchor_monthly=7500),
    )
    context = NegotiationContext(
        current_offer_monthly=6000,
        company_initiated=True,
        interview_rounds=3,
        strong_positive_signals=2,
    )
    advice = negotiation_advice(profile, context)
    assert advice.recommended_counter_monthly == 6500
    assert advice.requires_approval is True
    assert advice.leverage in {"balanced", "strong", "very_strong"}
