from jobster.models import Job
from jobster.review_sessions import ReviewSession


def _session():
    return ReviewSession(
        Job(id="job", title="Designer", company="Acme", description="x", url="https://example.com/job"),
        [],
        "private_data/test-browser",
    )


def test_apply_link_outside_form_is_a_navigation_control():
    class Control:
        def evaluate(self, script):
            return {"tag": "a", "inForm": False, "href": "https://ats.example/apply"}

    assert _session()._is_route_control(Control()) is True


def test_submit_control_inside_form_is_never_clicked_as_navigation():
    class Control:
        def evaluate(self, script):
            return {"tag": "button", "inForm": True, "href": ""}

    assert _session()._is_route_control(Control()) is False
