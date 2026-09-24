from jobster.application_target import resolve_from_html


def test_prefers_known_ats_apply_link():
    html = """
    <html><body>
      <a href="/about">About</a>
      <a href="https://jobs.lever.co/acme/abc123">Apply now</a>
      <a href="https://example.com/careers">Careers</a>
    </body></html>
    """
    target = resolve_from_html("https://board.example/jobs/1", html)
    assert target is not None
    assert target.ats == "lever"
    assert target.confidence == "high"
    assert target.url == "https://jobs.lever.co/acme/abc123"


def test_finds_company_careers_apply_link():
    html = """
    <a href="/careers/jobs/senior-product-designer">Apply for this job</a>
    """
    target = resolve_from_html("https://acme.example/jobs/123", html)
    assert target is not None
    assert target.ats == "generic_careers"
    assert target.confidence == "high"
    assert target.url == "https://acme.example/careers/jobs/senior-product-designer"


def test_finds_explicit_email_application():
    html = """
    <a href="#apply">Apply</a>
    <a href="mailto:jobs@example.com">Apply by email</a>
    """
    target = resolve_from_html("https://example.com/jobs/1", html)
    assert target is not None
    assert target.kind == "email"
    assert target.recipient == "jobs@example.com"


def test_ignores_fragment_without_an_application_destination():
    assert resolve_from_html("https://example.com/jobs/1", '<a href="#apply">Apply</a>') is None


def test_finds_email_in_application_instructions_without_mailto():
    target = resolve_from_html(
        "https://example.com/jobs/1",
        "<p>To apply, send your resume to careers@example.com.</p>",
    )
    assert target is not None
    assert target.kind == "email"
    assert target.recipient == "careers@example.com"


def test_does_not_treat_unrelated_contact_email_as_application_route():
    assert resolve_from_html(
        "https://example.com/jobs/1",
        "<footer>Questions? Contact support@example.com.</footer>",
    ) is None
