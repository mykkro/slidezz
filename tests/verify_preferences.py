"""Editor appearance/localization checks without changing slide content."""
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
    expect(page.locator("#preview .title")).to_have_text("Title")
    expect(page.locator("#preview strong")).to_have_text("Theme")
    original = page.evaluate("JSON.stringify(presentation)")
    canvas = page.locator("#preview .slide-canvas").inner_html()
    page.locator("#editor-settings").click()
    page.locator("#editor-dark-mode").check()
    page.locator("#editor-language").select_option("cs")
    expect(page.locator("html")).to_have_attribute("lang", "cs")
    expect(page.locator("html")).to_have_attribute("data-bs-theme", "dark")
    expect(page.locator("#open-import")).to_have_text("Importovat")
    expect(page.locator("#editor-settings")).to_have_attribute("title", "Nastavení editoru")
    expect(page.locator(".slide-item")).to_have_attribute("aria-label", "Snímek 1: Title")
    expect(page.locator(".topbar")).to_have_css("background-color", "rgb(34, 41, 35)")
    expect(page.locator("body")).to_have_css("color", "rgb(226, 234, 229)")
    brand = page.locator(".brand")
    expect(brand).to_have_css("color", "rgb(242, 247, 244)")
    expect(brand.locator("span")).to_have_css("color", "rgb(242, 247, 244)")
    expect(brand.locator("img")).to_have_css("background-color", "rgb(242, 247, 244)")
    brand.hover()
    expect(brand).to_have_css("color", "rgb(242, 247, 244)")
    brand.focus()
    expect(brand).to_have_css("color", "rgb(242, 247, 244)")
    page.locator("#editor-settings").focus()
    assert page.evaluate("JSON.stringify(presentation)") == original
    assert page.locator("#preview .slide-canvas").inner_html() == canvas
    page.locator("#editor-settings").click()
    page.locator("#theme-tab").click()
    expect(page.locator("#theme-settings > details > summary").first).to_have_text("Typografie")
    for width, height in [(1440,900),(1024,768),(390,844)]:
        page.set_viewport_size({"width":width,"height":height})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (label,width)
        page.screenshot(path=ROOT / "test-results" / f"editor-dark-cs-{label}-{width}.png")
    page.set_viewport_size({"width":1440,"height":900})
    page.locator("#slide-tab").click()
    page.locator("#field-title").fill("Own content")
    expect(page.locator("#save-status")).to_have_text("Uloženo")
    page.locator("#field-title").fill("Title")
    expect(page.locator("#save-status")).to_have_text("Uloženo")
    page.locator("#open-import").click()
    page.locator("#json-input").fill('{"slides":[{"type":"unknown"}]}')
    expect(page.locator("#import-error")).to_contain_text("Snímek 1")
    page.locator("#json-input").fill('{"slides":[{"type":"title","title":"Czech UI only"}]}')
    expect(page.locator("#import-validation")).to_have_text("Platný návrh: 1 snímek")
    expect(page.locator("#apply-import")).to_have_text("Použít návrh")
    messages = []
    def cancel(dialog):
        messages.append(dialog.message)
        dialog.dismiss()
    page.once("dialog", cancel)
    page.locator("#apply-import").click()
    assert messages == ["Nahradit aktuální prezentaci tímto návrhem?"]
    page.locator("#cancel-import").click()
    page.reload()
    expect(page.locator("html")).to_have_attribute("lang", "cs")
    expect(page.locator("html")).to_have_attribute("data-bs-theme", "dark")
    expect(page.locator("#preview .title")).to_have_text("Title")
    page.locator("#editor-settings").click()
    expect(page.locator("#editor-dark-mode")).to_be_checked()
    page.locator("#editor-dark-mode").uncheck()
    page.locator("#editor-language").select_option("en")
    expect(page.locator("#open-import")).to_have_text("Import")
    expect(page.locator("#editor-settings")).to_have_attribute("title", "Editor settings")
    expect(page.locator(".topbar")).to_have_css("background-color", "rgb(255, 255, 255)")
    expect(page.locator(".brand")).to_have_css("color", "rgb(38, 54, 49)")
    expect(page.locator(".brand img")).to_have_css("background-color", "rgba(0, 0, 0, 0)")
    assert page.evaluate("JSON.stringify(presentation)") == original


def main():
    (ROOT / "test-results").mkdir(exist_ok=True)
    data = validate({"slides":[{"type":"content","title":"Title","markdown":"**Theme**"}]})
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
                    errors, network = [], []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.on("request", lambda request: network.append(request.url) if request.url.startswith(("http:","https:")) else None)
                    check(page, url, label)
                    assert not errors, errors
                    if label == "offline":
                        assert not network, network
                    context.close()
                browser.close()
        finally:
            server.shutdown()
            thread.join()
    print("Light/dark, Czech localization, persistence and unchanged slide-content checks passed online/offline.")


if __name__ == "__main__":
    main()
