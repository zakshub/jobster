from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import httpx

from jobster.models import Job
from jobster.text_utils import repair_text
from .base import JobSource


WWR_RSS = "https://weworkremotely.com/remote-jobs.rss"


def _clean_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value or "").replace("  ", " ").strip()


def parse_wwr(xml_text: str) -> list[Job]:
    root = ET.fromstring(xml_text)
    jobs: list[Job] = []
    for item in root.findall("./channel/item"):
        title = repair_text(item.findtext("title") or "")
        link = item.findtext("link") or ""
        guid = item.findtext("guid") or link or title
        description = _clean_html(item.findtext("description") or "")

        company = "Unknown company"
        role_title = title
        if ":" in title:
            company, role_title = [part.strip() for part in title.split(":", 1)]

        jobs.append(
            Job(
                id=f"wwr:{guid}",
                title=role_title,
                company=company,
                description=description,
                location="Remote",
                remote=True,
                source="weworkremotely",
                url=link or None,
            )
        )
    return jobs


class WeWorkRemotelySource(JobSource):
    name = "weworkremotely"

    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    def fetch(self) -> list[Job]:
        response = httpx.get(WWR_RSS, timeout=self.timeout)
        response.raise_for_status()
        return parse_wwr(response.text)
