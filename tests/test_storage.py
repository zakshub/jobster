import sqlite3

from jobster.brain import CareerBrain
from jobster.models import CareerProfile, Job
from jobster.storage import JobsterStore


def test_store_persists_job_and_evaluation(tmp_path):
    store = JobsterStore(tmp_path / "jobster.db")
    store.init()
    profile = CareerProfile(profile_id="p", display_name="P")
    job = Job(id="j", title="Designer", company="Acme", description="x")
    result = CareerBrain().evaluate(profile, job)
    store.save_job(job)
    store.save_evaluation(result)

    con = sqlite3.connect(tmp_path / "jobster.db")
    assert con.execute("select count(*) from jobs").fetchone()[0] == 1
    assert con.execute("select count(*) from evaluations").fetchone()[0] == 1
