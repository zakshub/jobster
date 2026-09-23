from __future__ import annotations

import re

from .models import RecruiterAdvice


def advise_recruiter_message(message: str) -> RecruiterAdvice:
    low = message.lower()
    leverage = []
    risks = []

    if any(k in low for k in ["offer", "compensation package", "base salary"]):
        stage = "offer"
        intent = "Employer is discussing an offer or concrete compensation"
    elif any(k in low for k in ["salary expectation", "expected salary", "compensation expectations", "current salary"]):
        stage = "compensation"
        intent = "Recruiter is trying to establish compensation expectations"
    elif any(k in low for k in ["interview", "meet with", "hiring manager", "technical round", "portfolio review"]):
        stage = "interview"
        intent = "Recruiter is advancing the candidate into an interview stage"
    elif any(k in low for k in ["following up", "follow up", "checking in"]):
        stage = "follow_up"
        intent = "Recruiter is following up on an existing process"
    elif any(k in low for k in ["quick chat", "intro call", "screening", "learn more about you"]):
        stage = "screening"
        intent = "Recruiter is requesting an initial screening conversation"
    else:
        stage = "unknown"
        intent = "Recruiter intent needs manual review"

    if any(k in low for k in ["urgent", "as soon as possible", "immediately", "this week"]):
        leverage.append("Hiring urgency is visible")
    if any(k in low for k in ["impressed", "strong fit", "great fit", "very interested"]):
        leverage.append("Positive interest signal is explicit")
    if "current salary" in low:
        risks.append("Current salary disclosure can weaken negotiation position")

    if stage == "compensation":
        action = "Keep interest high, avoid unnecessary salary history disclosure, and ask for the approved range when the range is unknown."
        draft = (
            "Thanks for raising compensation. I am interested in the role and would like to align expectations with "
            "the scope and level of the position. Could you share the approved compensation range for the role? "
            "That will help us confirm alignment efficiently."
        )
    elif stage == "offer":
        action = "Do not accept immediately. Build the full offer and leverage context, then run NegotiationBrain."
        draft = (
            "Thank you for the offer. I am pleased to see the process reach this stage and I remain very interested. "
            "I would like to review the complete compensation and terms carefully before confirming. "
            "I will come back with any questions or points for discussion."
        )
    elif stage == "interview":
        action = "Confirm interest and logistics without overselling or adding unsupported claims."
        draft = (
            "Thanks for the update. I am interested in continuing the conversation. "
            "Please share the interview format, participants, and any areas you would like me to prepare in advance."
        )
    else:
        action = "Respond briefly, preserve optionality, and request the information needed for the next decision."
        draft = (
            "Thanks for reaching out. I am open to learning more. "
            "Please share the role scope, team context, location or remote expectations, and the next step in the process."
        )

    return RecruiterAdvice(
        stage=stage,
        intent=intent,
        leverage_signals=leverage,
        risks=risks,
        recommended_action=action,
        draft_reply=draft,
    )
