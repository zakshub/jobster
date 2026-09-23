from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "src" / "jobster" / "webui" / "index.html"
JS = ROOT / "src" / "jobster" / "webui" / "app.js"


def test_every_static_dollar_id_exists_in_html():
    html = HTML.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")

    html_ids = set(re.findall(r'id="([^"]+)"', html))
    referenced = set(re.findall(r'\$\("([^"]+)"\)', js))

    missing = sorted(referenced - html_ids)
    assert missing == []


def test_every_used_icon_symbol_exists():
    html = HTML.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")

    symbols = set(re.findall(r'<symbol id="i-([^"]+)"', html))
    html_uses = set(re.findall(r'href="#i-([^"]+)"', html))
    js_icons = set(re.findall(r'icon\("([^"]+)"', js))

    missing = sorted((html_uses | js_icons) - symbols)
    assert missing == []


def test_enterprise_navigation_is_present():
    html = HTML.read_text(encoding="utf-8")
    for route in (
        "today",
        "opportunities",
        "applications",
        "attention",
        "companies",
        "people",
        "interviews",
        "offers",
        "insights",
        "brain",
        "activity",
        "settings",
    ):
        assert f'data-route="{route}"' in html
        assert f'id="view-{route}"' in html


def test_pwa_assets_are_referenced():
    html = HTML.read_text(encoding="utf-8")
    assert 'rel="manifest"' in html
    assert "/manifest.webmanifest" in html


def test_omni_career_surfaces_are_present():
    html = HTML.read_text(encoding="utf-8")
    for element_id in (
        "mission-queue",
        "authority-grid",
        "companies-list",
        "contacts-list",
        "interviews-list",
        "offers-list",
        "funnel-story",
        "notification-panel",
        "compare-tray",
        "entity-modal",
        "compare-modal",
    ):
        assert f'id="{element_id}"' in html
