from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class JobVerification:
    state: str
    status_code: int | None
    final_url: str | None
    detail: str

    def as_dict(self) -> dict:
        return {
            "state": self.state,
            "status_code": self.status_code,
            "final_url": self.final_url,
            "detail": self.detail,
        }


_EXPIRED_MARKERS = (
    "job is no longer available",
    "job no longer available",
    "position has been filled",
    "position is no longer available",
    "no longer accepting applications",
    "this job has expired",
    "job has expired",
    "vacancy has closed",
    "page not found",
)


def verify_job_url(url: str | None, timeout: float = 12.0) -> JobVerification:
    if not url:
        return JobVerification("unverifiable", None, None, "No source URL is available")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; JobsterCareerAgent/0.2; +local-verification)"
    }

    try:
        with httpx.Client(follow_redirects=True, timeout=timeout, headers=headers) as client:
            with client.stream("GET", url) as response:
                status = response.status_code
                final_url = str(response.url)
                chunks: list[bytes] = []
                size = 0
                for chunk in response.iter_bytes():
                    chunks.append(chunk)
                    size += len(chunk)
                    if size >= 65536:
                        break
                body = b"".join(chunks).decode(response.encoding or "utf-8", errors="ignore").lower()
    except httpx.HTTPError as exc:
        return JobVerification("unreachable", None, url, str(exc))

    if status in {404, 410}:
        return JobVerification("expired", status, final_url, "Source page is no longer available")
    if status in {401, 403, 429}:
        return JobVerification(
            "protected",
            status,
            final_url,
            "Source blocked automated verification; manual opening is required",
        )
    if status >= 500:
        return JobVerification("unreachable", status, final_url, "Source returned a server error")

    for marker in _EXPIRED_MARKERS:
        if marker in body:
            return JobVerification("expired", status, final_url, f"Page indicates: {marker}")

    if 200 <= status < 400:
        return JobVerification("live", status, final_url, "Source URL is reachable and does not show an expiry marker")

    return JobVerification("needs_review", status, final_url, "Unexpected source response")
