# Jobster Source Registry

Jobster uses a layered discovery strategy instead of relying on one job board.

## Direct sources

These are machine-readable sources with dedicated adapters:

- Remote OK
- Remotive
- We Work Remotely
- Himalayas

Himalayas uses its public remote-jobs API. It is cached in the long-running worker because the upstream data is refreshed on a slower cadence.

## Google Jobs

Google Jobs discovery is available through SerpAPI when enabled.

## Expanded web-source discovery

When `sources.web_search.enabled: true` and `SERPAPI_API_KEY` is present, Jobster searches the following source universe through grouped domain-restricted web searches:

### Primary / remote / startup

- LinkedIn Jobs
- Wellfound
- YC Work at a Startup
- Working Nomads
- Remote.co
- Jobspresso
- JustRemote
- Dynamite Jobs
- FlexJobs
- Contra
- Arc
- Built In

### Design / UX

- Dribbble Jobs
- Behance Jobs
- Coroflot
- UX Jobs Board

### General boards

- Indeed
- Glassdoor
- ZipRecruiter
- Monster

### Direct company ATS listings

- Greenhouse
- Lever
- Ashby
- Workday
- SmartRecruiters
- Workable
- Jobvite
- BambooHR

## LinkedIn policy

Jobster does not use brittle or aggressive direct LinkedIn scraping.

LinkedIn opportunities are discovered through domain-restricted web search, plus manually supplied/public job URLs and future alert-intake workflows.

This keeps discovery useful while avoiding a dependency on an unofficial LinkedIn scraper.

## Failure isolation

One failed source must not stop the whole discovery cycle.

Source errors are written to the audit log and the remaining sources continue.

## Caching

Long-running worker instances keep source objects alive so source-level caches persist between cycles.

Current defaults:

- Himalayas: 24 hours
- Expanded web search: 6 hours

The main worker can still run every 60 minutes; slower sources return cached results between refreshes.

## Privacy and cost

Expanded web search requires a private `SERPAPI_API_KEY`.

Never commit API keys to this public repository.

Domain search can consume paid search-provider quota. Tune `group_size`, `results_per_group`, `cache_hours`, and the `sites` list in the private search configuration.
