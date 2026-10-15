"""Exercise presentation fullscreen and return-to-editor without dialog errors."""
import json
from pathlib import Path
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app import create_app, validate
from backend.services.bundles import build_static_html


def check(page,url,label):
    page.goto(url)
    expect(page.locator(".slide-item")).to_have_count(2)
    page.locator("#editor-settings").click()
    page.locator("#editor-language").select_option("cs")
    page.locator("#editor-settings").click()
    expect(page.locator("#start-presentation")).to_have_text("Prezentovat")
    for _ in range(2):
        page.locator("#start-presentation").click()
        expect(page.locator("#presentation-dialog")).to_be_visible()
        page.locator("#exit-presentation").click()
        expect(page.locator("#presentation-dialog")).not_to_be_visible()
    page.locator("#start-presentation").click()
    page.locator("#presentation-fullscreen").click()
    page.wait_for_function("document.fullscreenElement !== null")
    assert page.evaluate("document.fullscreenElement.tagName") != "DIALOG"
    expect(page.locator("#error-banner")).not_to_be_visible()
    page.locator("#presentation-next").click()
    expect(page.locator("#presentation-position")).to_have_text("2 / 2")
    page.screenshot(path=ROOT / "test-results" / f"fullscreen-{label}.png")
    page.locator("#exit-presentation").click()
    expect(page.locator("#presentation-dialog")).not_to_be_visible()
    page.wait_for_function("document.fullscreenElement === null")
    expect(page.locator(".slide-item.active")).to_contain_text("Second slide")
    expect(page.locator("#start-presentation")).to_be_focused()
    page.locator("#start-presentation").click()
    page.locator("#presentation-fullscreen").click()
    page.wait_for_function("document.fullscreenElement !== null")
    page.locator("#presentation-fullscreen").click()
    page.wait_for_function("document.fullscreenElement === null")
    expect(page.locator("#presentation-dialog")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator("#presentation-dialog")).not_to_be_visible()
    expect(page.locator("#error-banner")).not_to_be_visible()


def main():
    (ROOT / "test-results").mkdir(exist_ok=True)
    data = validate({"slides":[{"type":"title","title":"First slide"},{"type":"content","title":"Second slide","markdown":"**Details**"}]})
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        saved = root / "deck.json"
        saved.write_text(json.dumps(data),encoding="utf-8")
        offline = root / "offline.html"
        offline.write_text(build_static_html(data,{}),encoding="utf-8")
        app = create_app({"PRESENTATION_FILE":saved})
        server = make_server("127.0.0.1",0,app)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="msedge")
                for label,url in [("online",f"http://127.0.0.1:{server.server_port}"),("offline",offline.as_uri())]:
                    context = browser.new_context(viewport={"width":1440,"height":900})
                    page = context.new_page()
                    errors = []
                    page.on("pageerror",lambda error:errors.append(str(error)))
                    check(page,url,label)
                    assert not errors,errors
                    context.close()
                browser.close()
        finally:
            server.shutdown()
            thread.join()
    print("Presentation/fullscreen/back cycles, navigation and Escape passed online/offline without dialog errors.")


if __name__ == "__main__": main()
