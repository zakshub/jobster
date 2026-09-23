from jobster.recruiter import advise_recruiter_message


def test_salary_question_is_classified():
    advice = advise_recruiter_message("What are your salary expectations for this role?")
    assert advice.stage == "compensation"
    assert "approved compensation range" in advice.draft_reply
