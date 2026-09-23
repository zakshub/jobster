from jobster.ats import detect_ats
from jobster.dedupe import dedupe_jobs
from jobster.discovery import discover
from jobster.models import Job
from jobster.sources.base import JobSource
from jobster.sources.himalayas import parse_himalayas
from jobster.sources.remoteok import parse_remoteok
from jobster.sources.remotive import parse_remotive
from jobster.sources.serpapi_google_jobs import parse_google_jobs
from jobster.sources.serpapi_web import parse_serpapi_web
from jobster.sources.weworkremotely import parse_wwr


def test_remoteok_parser_skips_metadata_and_normalizes_job():
    payload = [
        {"legal": "metadata"},
        {
            "id": "123",
            "position": "Senior Product Designer",
            "company": "Acme",
            "description": "Design systems",
            "location": "Worldwide",
            "url": "https://remoteok.com/remote-jobs/123",
        },
    ]
    jobs = parse_remoteok(payload)
    assert len(jobs) == 1
    assert jobs[0].remote is True
    assert jobs[0].source == "remoteok"


def test_remotive_parser():
    jobs = parse_remotive(
        {
            "jobs": [
                {
                    "id": 7,
                    "title": "UX Architect",
                    "company_name": "Acme",
                    "description": "Remote",
                    "candidate_required_location": "Worldwide",
                    "url": "https://remotive.com/job/7",
                }
            ]
        }
    )
    assert jobs[0].title == "UX Architect"
    assert jobs[0].source == "remotive"


def test_wwr_parser():
    xml = """<?xml version='1.0'?><rss><channel><item><title>Acme: Product Designer</title><link>https://weworkremotely.com/remote-jobs/acme</link><guid>abc</guid><description><![CDATA[<p>Design a platform</p>]]></description></item></channel></rss>"""
    jobs = parse_wwr(xml)
    assert jobs[0].company == "Acme"
    assert jobs[0].title == "Product Designer"


def test_google_jobs_parser():
    payload = {
        "jobs_results": [
            {
                "job_id": "g1",
                "title": "Product Designer",
                "company_name": "Acme",
                "description": "AI product",
                "location": "Remote",
                "detected_extensions": {"work_from_home": True},
                "apply_options": [
                    {"link": "https://boards.greenhouse.io/acme/jobs/1"}
                ],
            }
        ]
    }
    jobs = parse_google_jobs(payload)
    assert jobs[0].remote is True
    assert detect_ats(jobs[0].url) == "greenhouse"


def test_himalayas_parser_normalizes_worldwide_and_annual_salary():
    payload = {
        "jobs": [
            {
                "guid": "h1",
                "title": "Senior Product Designer",
                "companyName": "Acme Health",
                "description": "<p>Healthcare product design</p>",
                "locationRestrictions": [],
                "applicationLink": "https://himalayas.app/jobs/acme-senior-product-designer",
                "minSalary": 72000,
                "maxSalary": 96000,
                "salaryPeriod": "annual",
                "currency": "USD",
            }
        ]
    }
    jobs = parse_himalayas(payload)
    assert jobs[0].source == "himalayas"
    assert jobs[0].location == "Worldwide"
    assert jobs[0].salary_min_monthly == 6000
    assert jobs[0].salary_max_monthly == 8000


def test_expanded_web_search_identifies_linkedin_source():
    payload = {
        "organic_results": [
            {
                "title": "Senior Product Designer - Acme Health | LinkedIn",
                "link": "https://www.linkedin.com/jobs/view/123456",
                "snippet": "Remote senior product designer for healthcare SaaS.",
            }
        ]
    }
    jobs = parse_serpapi_web(payload)
    assert jobs[0].source == "linkedin"
    assert jobs[0].title == "Senior Product Designer"
    assert jobs[0].company == "Acme Health"
    assert jobs[0].remote is True


def test_discovery_continues_if_one_source_fails():
    class BrokenSource(JobSource):
        name = "broken"

        def fetch(self):
            raise RuntimeError("boom")

    class GoodSource(JobSource):
        name = "good"

        def fetch(self):
            return [
                Job(
                    id="good:1",
                    title="Product Designer",
                    company="Acme",
                    description="Remote design role",
                    remote=True,
                    source="good",
                    url="https://example.com/jobs/1",
                )
            ]

    errors = []
    jobs = discover(
        [BrokenSource(), GoodSource()],
        on_error=lambda name, exc: errors.append((name, str(exc))),
    )
    assert len(jobs) == 1
    assert jobs[0].source == "good"
    assert errors == [("broken", "boom")]


def test_deduplication_uses_canonical_url():
    a = Job(
        id="1",
        title="Designer",
        company="Acme",
        description="x",
        url="https://example.com/jobs/1?utm_source=a",
    )
    b = Job(
        id="2",
        title="Designer",
        company="Acme",
        description="x",
        url="https://example.com/jobs/1?utm_source=b",
    )
    assert len(dedupe_jobs([a, b])) == 1


def test_ats_detection():
    assert detect_ats("https://jobs.lever.co/acme/123") == "lever"
    assert detect_ats("https://jobs.ashbyhq.com/acme/123") == "ashby"
    assert (
        detect_ats("https://acme.wd5.myworkdayjobs.com/en-US/jobs/job/123")
        == "workday"
    )
