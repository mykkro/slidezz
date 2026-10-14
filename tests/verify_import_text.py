"""Validate pasted designs, syntax highlighting and replacement safeguards."""
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
    expect(page.locator("#field-title")).to_have_value("Original deck")
    page.locator("#open-import").click()
    expect(page.locator("#import-mode-text")).to_be_checked()
    expect(page.locator("#json-file")).not_to_be_visible()
    source = page.locator("#json-input")
    apply = page.locator("#apply-import")
    source.fill('{"slides": [')
    expect(apply).to_be_disabled()
    expect(page.locator("#import-validation")).to_have_text("Invalid design")
    source.fill('{"slides":[{"type":"unknown"}]}')
    expect(page.locator("#import-error")).to_contain_text("unknown")
    expect(apply).to_be_disabled()
    page.evaluate("""() => {
        window.validationFetch = window.fetch;
        window.fetch = async (...args) => {
            const response = await window.validationFetch(...args);
            if (args[0] === '/api/import') await new Promise(resolve => setTimeout(resolve, 750));
            return response;
        };
    }""")
    source.fill('{"slides":[]}')
    page.wait_for_timeout(400)
    source.fill('{"slides": [')
    expect(page.locator("#import-validation")).to_have_text("Invalid design")
    page.wait_for_timeout(800)
    expect(apply).to_be_disabled()
    page.evaluate("window.fetch = window.validationFetch")
    design = {"slides":[{"type":"image_left_content","title":"Imported design",
                        "image":"missing-example.png","markdown":"**Validated** content"}]}
    source.fill(json.dumps(design, indent=2))
    expect(page.locator("#import-validation")).to_have_text("Valid design: 1 slide")
    expect(apply).to_be_enabled()
    assert page.locator("#json-highlight span").count() > 0
    assert page.locator("#json-highlight").inner_text().strip() == source.input_value().strip()
    page.locator("#import-dialog").screenshot(path=ROOT / "test-results" / f"import-text-{label}.png")
    page.once("dialog", lambda dialog: dialog.dismiss())
    apply.click()
    expect(page.locator("#import-dialog")).to_be_visible()
    expect(page.locator("#field-title")).to_have_value("Original deck")
    expect(source).to_have_value(json.dumps(design, indent=2))
    page.locator("#cancel-import").click()
    page.evaluate("""() => {
        window.originalImportFetch = window.fetch;
        window.fetch = (...args) => args[0] === '/api/save'
            ? Promise.resolve(new Response(JSON.stringify({error:'Simulated save failure'}),
                {status:503,headers:{'Content-Type':'application/json'}}))
            : window.originalImportFetch(...args);
    }""")
    page.locator("#field-title").fill("Unsaved work")
    expect(page.locator("#save-status")).to_have_text("Save failed")
    page.locator("#open-import").click()
    expect(apply).to_be_enabled()
    messages = []
    def cancel(dialog):
        messages.append(dialog.message)
        dialog.dismiss()
    page.once("dialog", cancel)
    apply.click()
    assert messages and "unsaved changes" in messages[0].lower()
    expect(page.locator("#field-title")).to_have_value("Unsaved work")
    expect(page.locator("#import-dialog")).to_be_visible()
    page.evaluate("window.fetch = window.originalImportFetch")
    page.once("dialog", lambda dialog: dialog.accept())
    apply.click()
    expect(page.locator("#import-dialog")).not_to_be_visible()
    expect(page.locator("#preview .title")).to_have_text("Imported design")
    expect(page.locator("#preview")).to_contain_text("Image missing-example.png not found")
    expect(page.locator("#preview strong")).to_have_text("Validated")
    expect(page.locator("#save-status")).to_have_text("Saved")
    page.locator("#open-import").click()
    page.locator("#import-format").select_option("yaml")
    source.fill("slides: [")
    expect(page.locator("#import-validation")).to_have_text("Invalid design")
    expect(apply).to_be_disabled()
    source.fill("slides:\n  - type: title\n    title: YAML design")
    expect(page.locator("#import-validation")).to_have_text("Valid design: 1 slide")
    assert page.locator("#json-highlight span").count() > 0
    page.set_viewport_size({"width":390, "height":844})
    assert page.locator("#import-dialog").evaluate("(e) => e.getBoundingClientRect().right <= innerWidth")
    page.screenshot(path=ROOT / "test-results" / f"import-yaml-mobile-{label}.png")
    page.once("dialog", lambda dialog: dialog.accept())
    apply.click()
    expect(page.locator("#preview .title")).to_have_text("YAML design")
    expect(page.locator("#save-status")).to_have_text("Saved")


def main():
    (ROOT / "test-results").mkdir(exist_ok=True)
    data = validate({"slides":[{"type":"title","title":"Original deck"}]})
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
    print("Pasted JSON/YAML, validation, highlighting and unsaved-work safeguards passed online/offline.")


if __name__ == "__main__":
    main()
