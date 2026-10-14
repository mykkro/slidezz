"""Document metadata editing, localization and online/offline persistence."""
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


def check(page, url, label):
    page.goto(url)
    expect(page.locator("#document-title")).to_have_text("Untitled presentation")
    page.locator("#document-title").click()
    expect(page.locator("#presentation-tab")).to_have_attribute("aria-selected","true")
    expect(page.locator("#metadata-title")).to_be_focused()
    values = {"title":"Title", "author":"Author", "subject":"Research", "description":"Document notes",
              "keywords":"slides, research", "category":"Demo", "language":"cs"}
    for key, value in values.items():
        page.locator("#metadata-"+key).fill(value)
    expect(page.locator("#save-status")).to_have_text("Saved")
    expect(page.locator("#document-title")).to_have_text("Title")
    expect(page).to_have_title("Title | Slidezz")
    expect(page.locator("#preview .title")).to_have_text("Slide title")
    with page.expect_download() as download:
        page.locator("#download-json").click()
    path = ROOT / "test-results" / f"metadata-{label}.json"
    download.value.save_as(path)
    assert json.loads(path.read_text(encoding="utf-8"))["metadata"] == values
    page.locator("#editor-settings").click()
    page.locator("#editor-language").select_option("cs")
    page.locator("#editor-settings").click()
    expect(page.locator("#presentation-tab")).to_have_text("Prezentace")
    expect(page.locator("#document-title")).to_have_text("Title")
    page.reload()
    expect(page.locator("#document-title")).to_have_text("Title")
    page.locator("#document-title").click()
    for key, value in values.items():
        expect(page.locator("#metadata-"+key)).to_have_value(value)
    page.locator("#metadata-title").fill("A"*255)
    expect(page.locator("#save-status")).to_have_text("Uloženo")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=ROOT / "test-results" / f"metadata-desktop-{label}.png")
    page.set_viewport_size({"width":390,"height":844})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    expect(page.locator("#presentation-settings")).to_be_visible()
    page.screenshot(path=ROOT / "test-results" / f"metadata-mobile-{label}.png")


def main():
    (ROOT / "test-results").mkdir(exist_ok=True)
    data = validate({"slides":[{"type":"content","title":"Slide title","markdown":"Original content"}]})
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
                for label, url in (("online",f"http://127.0.0.1:{server.server_port}"),("offline",offline.as_uri())):
                    context = browser.new_context(viewport={"width":1440,"height":900})
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    check(page, url, label)
                    assert not errors, errors
                    context.close()
                browser.close()
        finally:
            server.shutdown()
            thread.join()
    print("Presentation metadata editing, JSON export, Czech labels, persistence and responsive layouts passed online/offline.")


if __name__ == "__main__":
    main()
