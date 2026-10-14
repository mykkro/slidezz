"""Exercise query-string presentation mode and editor-free HTML exports."""
import json
import argparse
from pathlib import Path
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app import create_app, validate
from backend.services.bundles import build_static_html, build_viewer_html, image_files


def player(page, path, data, query=False):
    page.goto(path.as_uri() + ("?mode=presentation" if query else ""))
    counter = "#presentation-position" if query else "#viewer-position"
    preview = "#presentation-preview" if query else "#viewer-preview"
    expect(page.locator(counter)).to_have_text(f"1 / {len(data['slides'])}")
    if query:
        expect(page.locator(".workspace")).not_to_be_visible()
        expect(page.locator("#exit-presentation")).not_to_be_visible()
        page.keyboard.press("Escape")
        expect(page.locator("#presentation-dialog")).to_be_visible()
    else:
        expect(page.locator("#properties,.workspace,textarea")).to_have_count(0)
        assert page.evaluate("typeof EasyMDE === 'undefined' && typeof CodeMirror === 'undefined'")
    for index, slide in enumerate(data["slides"]):
        expect(page.locator(preview + " .title")).to_have_text(slide["title"])
        page.wait_for_function("(id) => Array.from(document.querySelectorAll(id+' img')).every(i=>i.complete && i.naturalWidth>0)", arg=preview)
        assert page.locator(preview + " .slide-canvas").evaluate("(e) => e.getBoundingClientRect().width > 100")
        if index + 1 < len(data["slides"]):
            page.keyboard.press("ArrowRight")
            expect(page.locator(counter)).to_have_text(f"{index+2} / {len(data['slides'])}")
    page.keyboard.press("Home")
    expect(page.locator(counter)).to_have_text(f"1 / {len(data['slides'])}")
    for width,height in [(1440,900),(390,844)]:
        page.set_viewport_size({"width":width,"height":height})
        page.wait_for_function("""(id) => {
            const e=document.querySelector(id), stage=e.parentElement, r=e.getBoundingClientRect();
            const expected=Math.min(stage.clientWidth-32,(stage.clientHeight-16)*16/9);
            return Math.abs(r.width-expected)<1 && r.left>=0 && r.right<=innerWidth+1;
        }""", arg=preview)
        assert page.locator(preview).evaluate("(e) => {const r=e.getBoundingClientRect();return r.width>100 && r.left>=0 && r.right<=innerWidth+1 && r.bottom<=innerHeight+1}")
        page.screenshot(path=ROOT / "test-results" / f"viewer-{'query' if query else 'only'}-{width}.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-url")
    args = parser.parse_args()
    (ROOT / "test-results").mkdir(exist_ok=True)
    data = validate(json.loads((ROOT / "examples" / "presentation.json").read_text(encoding="utf-8")))
    data["slides"][2]["title"] += " $& $' $" + chr(96)
    images = image_files(data, ROOT / "images")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        editor = root / "editor.html"
        editor.write_text(build_static_html(data, images), encoding="utf-8")
        viewer = root / "viewer.html"
        viewer.write_text(build_viewer_html(data, images), encoding="utf-8")
        app = create_app({"PRESENTATION_FILE":root / "deck.json","IMAGES_DIR":ROOT / "images"})
        server = make_server("127.0.0.1", 0, app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel="msedge")
                context = browser.new_context(viewport={"width":1440,"height":900})
                page = context.new_page()
                errors, network = [], []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("request", lambda request: network.append(request.url) if request.url.startswith(("http:","https:")) else None)
                page.goto(editor.as_uri())
                page.locator("#field-title").fill("Browser-saved edit")
                expect(page.locator("#save-status")).to_have_text("Saved")
                player(page, editor, data, query=True)
                player(page, viewer, data)
                page.goto(editor.as_uri())
                expect(page.locator("#field-title")).to_have_value("Browser-saved edit")
                page.locator("#bundle-menu-button").click()
                exported = root / "exported-viewer.html"
                with page.expect_download() as download:
                    page.locator("#export-viewer").click()
                download.value.save_as(exported)
                changed = json.loads(json.dumps(data))
                changed["slides"][0]["title"] = "Browser-saved edit"
                player(page, exported, changed)
                assert not errors and not network, (errors,network)
                empty = root / "empty.html"
                empty.write_text(build_viewer_html(validate({"slides":[]}), {}), encoding="utf-8")
                page.goto(empty.as_uri())
                expect(page.locator("#viewer-position")).to_have_text("0 / 0")
                expect(page.locator("#viewer-next")).to_be_disabled()
                missing = root / "missing.html"
                missing.write_text(build_viewer_html(validate({"slides":[{"type":"image_left_content","image":"absent.png"}]}), {}), encoding="utf-8")
                page.goto(missing.as_uri())
                expect(page.locator("#viewer-preview")).to_contain_text("Image absent.png not found")
                client = playwright.request.new_context(base_url=args.live_url or f"http://127.0.0.1:{server.server_port}")
                response = client.post("/api/export/viewer", data=data)
                assert response.status == 200
                server_file = root / "server-viewer.html"
                server_file.write_bytes(response.body())
                player(page, server_file, data)
                client.dispose()
                context.close()
                browser.close()
        finally:
            server.shutdown()
            thread.join()
    print("Viewer-only HTML and URL presentation mode passed: all layouts, images, navigation, responsive framing and no network.")


if __name__ == "__main__":
    main()
