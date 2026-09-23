# Job Source Research

Verified on 2026 09 23.

## Remote OK

Public JSON feed:

https://remoteok.com/api

Public RSS feed:

https://remoteok.com/remote-jobs.rss

Remote OK asks aggregators and feed users to credit Remote OK and link candidates back to the original job post.

## We Work Remotely

Public all jobs RSS feed:

https://weworkremotely.com/remote-jobs.rss

Category feeds are also available.

We Work Remotely asks feed users to attribute links back to We Work Remotely.

## Remotive

Public remote jobs API documentation:

https://remotive.com/remote-jobs/api

The public feed is delayed and comes with attribution and redistribution conditions. Jobster should preserve the Remotive source and original URL.

## Google Jobs

Jobster does not depend on direct Google scraping.

The initial replaceable provider implementation uses SerpApi Google Jobs when an API key is configured:

https://serpapi.com/google-jobs-api

Provider interface design means this can be replaced later.

## LinkedIn

LinkedIn is an intake source, not Jobster core infrastructure.

Preferred inputs:

1. User supplied job URLs.
2. Job alert email intake.
3. Other permitted user initiated workflows.

Jobster should not depend on unauthorized LinkedIn scraping, automated messaging, or CAPTCHA bypass.
