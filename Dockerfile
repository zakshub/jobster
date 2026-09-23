FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
RUN pip install --no-cache-dir .

ENV JOBSTER_PROFILE=/app/config/profile.yaml
ENV JOBSTER_SEARCH=/app/config/search.yaml
ENV JOBSTER_DB=/app/data/jobster.db

CMD ["python", "-m", "jobster.worker"]
