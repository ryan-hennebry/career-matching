from __future__ import annotations

import json
from threading import Thread
from types import SimpleNamespace

import pytest
from playwright.sync_api import expect, sync_playwright

import career_match
from preview_board import open_server


@pytest.fixture
def dashboard(monkeypatch, tmp_path):
    monkeypatch.setattr(career_match, "OUTPUT", tmp_path / "output")
    career_match._demo(SimpleNamespace(run="demo", date="2026-01-15"))
    run = tmp_path / "output" / "demo" / "ranked"
    with open_server(run, 0) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


def test_dashboard_on_desktop_and_mobile(dashboard):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 940, "height": 800})
        errors = []
        requests = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: requests.append(request.url))
        page.goto(dashboard)
        expect(page.get_by_role("heading", name="Your shortlist")).to_be_visible()
        expect(page.get_by_text("fictional roles", exact=False)).to_be_visible()
        expect(page.get_by_role("heading", name="Customer Operations Manager")).to_be_visible()
        expect(page.get_by_role("heading", name="Implementation Operations Lead")).to_have_count(0)

        page.keyboard.press("Tab")
        expect(page.get_by_role("link", name="Skip to shortlist")).to_be_focused()
        page.keyboard.press("Tab")
        details = page.get_by_label("Review evidence for Customer Operations Manager")
        expect(details).to_be_focused()
        page.keyboard.press("Enter")
        expect(page.get_by_text("Earliest publication found Jan 11, 2026")).to_be_visible()

        page.set_viewport_size({"width": 360, "height": 760})
        assert page.evaluate("document.documentElement.scrollWidth === window.innerWidth")
        expect(page.get_by_role("heading", name="Search coverage")).to_be_visible()
        assert page.locator("#matches .role").count() == 2
        assert page.locator("details a").count() == 0
        assert not errors
        assert all(url.startswith(dashboard + "/") for url in requests)
        browser.close()


def test_dashboard_serves_only_the_shortlist_and_assets(dashboard):
    with sync_playwright() as playwright:
        request = playwright.request.new_context()
        for path in ("/context.md", "/.git/config", "/output/demo/candidates.json", "/api/context"):
            assert request.get(dashboard + path).status == 404
        assert request.get(dashboard + "/board.json", headers={"Origin": "https://other.example.org"}).status == 403
        root = request.get(dashboard)
        assert "frame-ancestors 'none'" in root.headers["content-security-policy"]
        assert request.post(dashboard + "/board.json", data={"status": "applied"}).status == 501
        response = request.get(dashboard + "/board.json")
        assert response.ok
        body = response.json()
        assert body["synthetic"]
        assert "description" not in json.dumps(body)
        request.dispose()


def test_dashboard_empty_and_error_states(dashboard):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.route("**/board.json", lambda route: route.fulfill(json={
            "run_date": "2026-01-15", "synthetic": True, "main": [], "appendix": [],
            "coverage": {key: 0 for key in (
                "candidates", "pending", "skipped", "stale", "sources", "caps_hit", "blocked_sources"
            )},
        }))
        page.goto(dashboard)
        expect(page.get_by_text("No confirmed matches in this run.", exact=False)).to_be_visible()
        expect(page.get_by_role("heading", name="Appendix")).to_have_count(0)

        page.unroute("**/board.json")
        page.route("**/board.json", lambda route: route.fulfill(status=503))
        page.reload()
        expect(page.get_by_role("status")).to_contain_text("Restart the local preview")
        browser.close()
