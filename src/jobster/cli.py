import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .application_packet import build_application_packet
from .brain import CareerBrain
from .doctor import doctor as run_doctor
from .models import Job, NegotiationContext
from .negotiation import negotiation_advice
from .profile import load_profile
from .recruiter import advise_recruiter_message
from .resume import tailor_resume
from .semantic import SemanticCareerBrain

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.callback()
def main():
    """Jobster personal Career Agent CLI."""
    pass


@app.command()
def evaluate(
    profile: Path = typer.Option(..., exists=True, readable=True),
    job: Path = typer.Option(..., exists=True, readable=True),
    semantic: bool = typer.Option(False, "--semantic"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Evaluate one normalized job against one CareerProfile."""
    career_profile = load_profile(profile)
    normalized_job = Job.model_validate_json(job.read_text(encoding="utf-8"))
    baseline = CareerBrain().evaluate(career_profile, normalized_job)
    result = SemanticCareerBrain().evaluate(career_profile, normalized_job, baseline) if semantic else baseline

    if json_output:
        console.print_json(result.model_dump_json())
        return

    console.print(Panel(result.summary, title="Jobster CareerBrain"))
    console.print(f"Decision: [bold]{result.pursuit_decision.value}[/bold]")
    console.print(f"Eligible: {result.eligible}")
    console.print(f"Confidence: {result.confidence:.2f}")
    console.print(f"Interest: {result.interest_score}/100")
    if result.strong_matches:
        console.print("Strong matches: " + ", ".join(result.strong_matches))
    if result.hard_blockers:
        console.print("Blockers: " + " | ".join(result.hard_blockers))
    if result.unknowns:
        console.print("Unknowns: " + " | ".join(result.unknowns))
    console.print("Next: " + result.next_action)


@app.command("prepare")
def prepare(
    profile: Path = typer.Option(..., exists=True, readable=True),
    job: Path = typer.Option(..., exists=True, readable=True),
    output: Path = typer.Option(Path("artifacts")),
    semantic: bool = typer.Option(False, "--semantic"),
):
    """Create a truthful application packet for one job."""
    career_profile = load_profile(profile)
    normalized_job = Job.model_validate_json(job.read_text(encoding="utf-8"))
    baseline = CareerBrain().evaluate(career_profile, normalized_job)
    evaluation = SemanticCareerBrain().evaluate(career_profile, normalized_job, baseline) if semantic else baseline
    result = build_application_packet(career_profile, normalized_job, evaluation, output)
    console.print_json(json.dumps(result))


@app.command("recruiter-advice")
def recruiter_advice(message: str):
    """Classify a recruiter message and draft the next response."""
    console.print_json(advise_recruiter_message(message).model_dump_json())


@app.command("negotiate")
def negotiate(
    profile: Path = typer.Option(..., exists=True, readable=True),
    context: Path = typer.Option(..., exists=True, readable=True),
):
    """Generate negotiation strategy from a structured context."""
    career_profile = load_profile(profile)
    negotiation_context = NegotiationContext.model_validate_json(context.read_text(encoding="utf-8"))
    console.print_json(negotiation_advice(career_profile, negotiation_context).model_dump_json())


@app.command("init-db")
def init_db(db: Path = typer.Option(Path("data/jobster.db"))):
    """Initialize local Jobster SQLite state."""
    from .storage import JobsterStore

    store = JobsterStore(db)
    store.init()
    console.print(f"Initialized {db}")


@app.command()
def doctor(
    profile: Path = typer.Option(Path("config/profile.yaml")),
    search: Path = typer.Option(Path("config/search.yaml")),
    db: Path = typer.Option(Path("data/jobster.db")),
):
    """Check whether the personal Jobster runtime is ready."""
    checks = run_doctor(profile, search, db)
    table = Table(title="Jobster doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    for check in checks:
        table.add_row(check["name"], "OK" if check["ok"] else "MISSING", check["detail"])
    console.print(table)


if __name__ == "__main__":
    app()
