"""Focused typography and collapsible-inspector checks, online and offline."""
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
    expect(page.locator("#field-title")).to_have_value("Typography check")
    groups = page.locator("#theme-settings > details")
    expect(groups).to_have_count(5)
    page.locator("#theme-tab").click()
    group = groups.filter(has=page.locator("#theme-title_size"))
    group.locator(":scope > summary").click()
    expect(page.locator("#theme-title_size")).not_to_be_visible()
    group.locator(":scope > summary").click()
    page.locator("#slide-tab").click()
    title = page.locator("#properties > details").filter(has=page.locator("#field-title"))
    title.locator(".settings-group > summary").click()
    size = page.locator("#field-title_font_size")
    expect(size).to_be_disabled()
    page.locator("#field-title_font_size-use-theme").uncheck()
    size.fill("42")
    page.locator("#field-title_font_name-use-theme").uncheck()
    page.locator("#field-title_font_name").select_option("Lato")
    page.locator("#field-title_font_color-use-theme").uncheck()
    page.locator("#field-title_font_color").evaluate("(e) => {e.value='#123456';e.dispatchEvent(new Event('input',{bubbles:true}));}")
    expect(page.locator("#preview .title")).to_have_css("font-size", "56px")
    expect(page.locator("#preview .title")).to_have_css("font-family", "Lato")
    expect(page.locator("#preview .title")).to_have_css("color", "rgb(18, 52, 86)")
    title.locator(".settings-group > summary").click()
    page.locator("#field-title").fill("Changed")
    expect(size).not_to_be_visible()
    title.locator(".settings-group > summary").click()
    page.locator("#theme-tab").click()
    page.locator("#theme-title_size").fill("24")
    page.locator("#slide-tab").click()
    expect(page.locator("#preview .title")).to_have_css("font-size", "56px")
    page.locator("#field-title_font_size-use-theme").check()
    expect(size).to_have_value("24")
    expect(page.locator("#preview .title")).to_have_css("font-size", "32px")
    expect(page.locator("#save-status")).to_have_text("Saved")
    page.reload()
    expect(page.locator("#preview .title")).to_have_css("font-family", "Lato")
    expect(page.locator("#preview .title")).to_have_css("font-size", "32px")
    page.set_viewport_size({"width":390, "height":844})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=ROOT / "test-results" / "typography-mobile.png")


def main():
    data = validate({"theme":{"font_name":"Arial"}, "slides":[
        {"type":"content", "title":"Typography check", "markdown":"## A heading\n\n**Bold** and *italic*."}]})
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
    print("Typography and collapsed-group checks passed online and offline.")


if __name__ == "__main__":
    main()
