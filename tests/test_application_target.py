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


def test_ignores_non_web_and_same_page_links():
    html = """
    <a href="#apply">Apply</a>
    <a href="mailto:jobs@example.com">Apply by email</a>
    """
    assert resolve_from_html("https://example.com/jobs/1", html) is None
