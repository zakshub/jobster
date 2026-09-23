import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from .brain import CareerBrain
from .models import Job
from .profile import load_profile

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
    json_output: bool = typer.Option(False, "--json"),
):
    """Evaluate one normalized job against one CareerProfile."""
    career_profile = load_profile(profile)
    job_data = json.loads(job.read_text(encoding="utf-8"))
    normalized_job = Job.model_validate(job_data)
    result = CareerBrain().evaluate(career_profile, normalized_job)

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


if __name__ == "__main__":
    app()
