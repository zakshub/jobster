from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

from .ats import detect_ats


@dataclass(frozen=True)
class ApplicationTarget:
    url: str
    ats: str
    confidence: str
    reason: str


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() != "a":
            return
        values = dict(attrs)
        href = values.get("href")
        if href:
            self._href = href
            self._text = []

    def handle_data(self, data: str):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None
            self._text = []


_KNOWN_ATS = {"greenhouse", "lever", "ashby", "workday"}
_APPLY_WORDS = (
    "apply",
    "apply now",
    "apply for this job",
    "apply for this position",
    "submit application",
)


def _same_page(a: str, b: str) -> bool:
    left = urlparse(a)
    right = urlparse(b)
    return (
        left.netloc.lower() == right.netloc.lower()
        and left.path.rstrip("/") == right.path.rstrip("/")
    )


def _candidate_score(source_url: str, candidate_url: str, text: str) -> tuple[int, str]:
    parsed = urlparse(candidate_url)
    if parsed.scheme not in {"http", "https"}:
        return (-1000, "not a web link")
    if _same_page(source_url, candidate_url):
        return (-1000, "same page")

    ats = detect_ats(candidate_url)
    label = text.strip().lower()
    path = parsed.path.lower()
    score = 0
    reasons: list[str] = []

    if ats in _KNOWN_ATS:
        score += 100
        reasons.append(f"known application site ({ats})")
    elif ats == "generic_careers":
        score += 55
        reasons.append("company careers page")

    if label in _APPLY_WORDS:
        score += 70
        reasons.append("explicit apply link")
    elif "apply" in label:
        score += 50
        reasons.append("apply wording")

    if any(token in path for token in ("/apply", "/application", "/jobs/", "/job/")):
        score += 20
        reasons.append("application-like URL")

    if "linkedin.com" in parsed.netloc.lower():
        score -= 15

    return score, ", ".join(reasons) or "possible application link"


def resolve_from_html(source_url: str, html_text: str) -> ApplicationTarget | None:
    parser = _LinkParser()
    parser.feed(html_text)

    candidates: list[tuple[int, str, str]] = []
    for href, text in parser.links:
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(source_url, href)
        score, reason = _candidate_score(source_url, absolute, text)
        if score > 0:
            candidates.append((score, absolute, reason))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    score, url, reason = candidates[0]
    confidence = "high" if score >= 100 else "medium" if score >= 70 else "low"
    return ApplicationTarget(
        url=url,
        ats=detect_ats(url),
        confidence=confidence,
        reason=reason,
    )


def resolve_application_target(
    source_url: str | None,
    *,
    timeout: float = 12.0,
) -> ApplicationTarget | None:
    if not source_url:
        return None

    direct_ats = detect_ats(source_url)
    if direct_ats in _KNOWN_ATS:
        return ApplicationTarget(
            url=source_url,
            ats=direct_ats,
            confidence="high",
            reason="job already points to a supported application site",
        )

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; JobsterCareerAgent/0.4; +local-application-link-check)"
    }
    try:
        response = httpx.get(
            source_url,
            timeout=timeout,
            follow_redirects=True,
            headers=headers,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return None

    final_url = str(response.url)
    final_ats = detect_ats(final_url)
    if final_ats in _KNOWN_ATS:
        return ApplicationTarget(
            url=final_url,
            ats=final_ats,
            confidence="high",
            reason="source redirected to a supported application site",
        )

    return resolve_from_html(final_url, response.text)
