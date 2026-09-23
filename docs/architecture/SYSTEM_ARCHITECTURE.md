# System Architecture

## Principle

Separate intelligence from automation.

Automation performs mechanical work.

CareerBrain decides what should happen and why.

## High level flow

job sources
then normalization
then deduplication
then factual extraction
then eligibility
then CareerBrain evaluation
then pursuit policy
then application preparation
then ATS execution
then receipt
then tracking
then recruiter workflow
then negotiation intelligence
then outcome learning

## Major modules

### Source adapters

Every source implements one normalized interface.

Initial source families:

public remote feeds
company career pages
direct ATS listings
web search provider
LinkedIn alert intake
user supplied links

### Job normalizer

Converts every source into the same job contract.

### Deduplicator

Uses source ids, canonical URLs, employer, title, location, and content fingerprints.

### Fact extractor

Separates posting facts from CareerBrain interpretation.

### Eligibility engine

Handles hard constraints before semantic preference reasoning.

### CareerBrain

Produces opportunity understanding, capability alignment, interest, flexibility, career value, pursuit strategy, positioning, uncertainty, and evidence references.

### Application planner

Chooses documents, answer set, and ATS executor.

### ATS executors

Provider interface by ATS family.

Initial executors:

Greenhouse
Lever
Ashby

Workday comes after the first three are stable.

### Application tracker

Durable application state machine plus audit events.

### Communication engine

Classifies recruiter communication, retrieves context, drafts responses, and records actions.

### Negotiation engine

Builds leverage context and strategy.

### Learning engine

Turns explicit user feedback and actual outcomes into proposed CareerBrain model updates.

## Personal runtime

First version can use:

Python 3.11 or newer
FastAPI when an HTTP boundary becomes useful
SQLite for local state
Playwright for supported browser application flows
scheduled worker process
local file storage for approved documents
Docker for VPS deployment

Do not add PostgreSQL, Redis, Kubernetes, or distributed workers until the personal workload justifies them.

## Future scale seams

Preserve interfaces for:

user ownership
PostgreSQL
queue workers
object storage
authentication
subscription plans
rate limits
web frontend
admin operations

These are boundaries, not MVP features.

## Model provider rule

LLM providers are replaceable reasoning engines.

CareerBrain evidence, decisions, policies, and memory must not depend on one AI vendor.
