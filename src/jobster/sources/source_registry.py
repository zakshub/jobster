from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    label: str
    domain: str
    method: str
    priority: str


SOURCE_REGISTRY: tuple[SourceDefinition, ...] = (
    SourceDefinition("linkedin", "LinkedIn Jobs", "linkedin.com/jobs", "web_search", "primary"),
    SourceDefinition("wellfound", "Wellfound", "wellfound.com/jobs", "web_search", "primary"),
    SourceDefinition("yc", "YC Work at a Startup", "ycombinator.com/jobs", "web_search", "primary"),
    SourceDefinition("himalayas", "Himalayas", "himalayas.app/jobs", "direct_api", "primary"),
    SourceDefinition("remoteok", "Remote OK", "remoteok.com", "direct_api", "primary"),
    SourceDefinition("remotive", "Remotive", "remotive.com", "direct_api", "primary"),
    SourceDefinition("weworkremotely", "We Work Remotely", "weworkremotely.com", "direct_rss", "primary"),
    SourceDefinition("workingnomads", "Working Nomads", "workingnomads.com", "web_search", "secondary"),
    SourceDefinition("remote_co", "Remote.co", "remote.co/remote-jobs", "web_search", "secondary"),
    SourceDefinition("jobspresso", "Jobspresso", "jobspresso.co", "web_search", "secondary"),
    SourceDefinition("justremote", "JustRemote", "justremote.co", "web_search", "secondary"),
    SourceDefinition("dynamitejobs", "Dynamite Jobs", "dynamitejobs.com", "web_search", "secondary"),
    SourceDefinition("flexjobs", "FlexJobs", "flexjobs.com", "web_search", "secondary"),
    SourceDefinition("dribbble", "Dribbble Jobs", "dribbble.com/jobs", "web_search", "design"),
    SourceDefinition("behance", "Behance Jobs", "behance.net/joblist", "web_search", "design"),
    SourceDefinition("coroflot", "Coroflot Jobs", "coroflot.com/design-jobs", "web_search", "design"),
    SourceDefinition("uxjobsboard", "UX Jobs Board", "uxjobsboard.com", "web_search", "design"),
    SourceDefinition("contra", "Contra", "contra.com/opportunities", "web_search", "startup"),
    SourceDefinition("arc", "Arc", "arc.dev/remote-jobs", "web_search", "startup"),
    SourceDefinition("builtin", "Built In", "builtin.com/jobs/remote", "web_search", "startup"),
    SourceDefinition("indeed", "Indeed", "indeed.com", "web_search", "general"),
    SourceDefinition("glassdoor", "Glassdoor", "glassdoor.com/Job", "web_search", "general"),
    SourceDefinition("ziprecruiter", "ZipRecruiter", "ziprecruiter.com/jobs-search", "web_search", "general"),
    SourceDefinition("monster", "Monster", "monster.com/jobs", "web_search", "general"),
    SourceDefinition("greenhouse", "Greenhouse-hosted company jobs", "boards.greenhouse.io", "ats_web_search", "ats"),
    SourceDefinition("lever", "Lever-hosted company jobs", "jobs.lever.co", "ats_web_search", "ats"),
    SourceDefinition("ashby", "Ashby-hosted company jobs", "jobs.ashbyhq.com", "ats_web_search", "ats"),
    SourceDefinition("workday", "Workday-hosted company jobs", "myworkdayjobs.com", "ats_web_search", "ats"),
    SourceDefinition("smartrecruiters", "SmartRecruiters-hosted company jobs", "jobs.smartrecruiters.com", "ats_web_search", "ats"),
    SourceDefinition("workable", "Workable-hosted company jobs", "apply.workable.com", "ats_web_search", "ats"),
    SourceDefinition("jobvite", "Jobvite-hosted company jobs", "jobs.jobvite.com", "ats_web_search", "ats"),
    SourceDefinition("bamboohr", "BambooHR-hosted company jobs", "bamboohr.com/careers", "ats_web_search", "ats"),
)

WEB_SEARCH_DOMAINS: tuple[str, ...] = tuple(
    item.domain for item in SOURCE_REGISTRY if item.method in {"web_search", "ats_web_search"}
)
