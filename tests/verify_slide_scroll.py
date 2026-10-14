"""Regression checks for thumbnail scrolling, with and without a backend."""
import json
from pathlib import Path
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app import create_app, validate
from backend.services.bundles import build_static_html


def check(page, url):
    page.goto(url)
    expect(page.locator(".slide-item")).to_have_count(30)
    target = page.locator(".slide-item").nth(24)
    target.scroll_into_view_if_needed()
    top = page.locator("#slides").evaluate("(e) => e.scrollTop")
    assert top > 1000
    target.click()
    expect(page.locator(".slide-item.active")).to_contain_text("Slide 25")
    assert abs(page.locator("#slides").evaluate("(e) => e.scrollTop") - top) <= 2
    expect(page.locator(".slide-item.active")).to_be_focused()
    page.locator("#field-title").fill("Edited slide 25")
    expect(page.locator("#preview .title")).to_have_text("Edited slide 25")
    assert abs(page.locator("#slides").evaluate("(e) => e.scrollTop") - top) <= 2
    expect(page.locator("#field-title")).to_be_focused()
    page.locator("#previous-slide").click()
    expect(page.locator(".slide-item.active")).to_contain_text("Slide 24")
    assert page.locator(".slide-item.active").evaluate("""(e) => {
        const item = e.getBoundingClientRect(), list = e.parentElement.getBoundingClientRect();
        return item.top >= list.top - 1 && item.bottom <= list.bottom + 1;
    }""")
    page.locator("#start-presentation").click()
    page.keyboard.press("Home")
    expect(page.locator("#presentation-position")).to_have_text("1 / 30")
    page.keyboard.press("Escape")
    expect(page.locator(".slide-item.active")).to_contain_text("Slide 1")
    assert page.locator("#slides").evaluate("(e) => e.scrollTop") <= 2


def main():
    data = validate({"slides":[{"type":"title","title":f"Slide {index+1}"} for index in range(30)]})
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        saved = root / "deck.json"
        saved.write_text(json.dumps(data), encoding="utf-8")
        offline = root / "offline.html"
        offline.write_text(build_static_html(data, {}), encoding="utf-8")
        app = create_app({"PRESENTATION_FILE":saved,"IMAGES_DIR":root / "images"})
        server = make_server("127.0.0.1", 0, app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel="msedge")
                for url in (f"http://127.0.0.1:{server.server_port}", offline.as_uri()):
                    context = browser.new_context(viewport={"width":1440,"height":900})
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    check(page, url)
                    assert not errors, errors
                    context.close()
                browser.close()
        finally:
            server.shutdown()
            thread.join()
    print("Slide-list scroll and focus checks passed online and offline.")


if __name__ == "__main__":
    main()
