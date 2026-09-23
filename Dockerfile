FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config

RUN pip install --no-cache-dir .     && python -m playwright install --with-deps chromium

ENV JOBSTER_PROFILE=/app/private_data/profile.yaml
ENV JOBSTER_SEARCH=/app/config/search.yaml
ENV JOBSTER_DB=/app/data/jobster.db

CMD ["python", "-m", "jobster.worker"]
