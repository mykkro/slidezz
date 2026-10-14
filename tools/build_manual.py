"""Build and verify the Slidezz manual without touching the user's saved deck."""
import json
from io import BytesIO
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import yaml
import pymupdf
from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app import create_app, validate, PresentationDumper
from backend.services.bundles import build_static_html, image_files, export_zip
from backend.services.pptx_generator import generate


def main():
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    results = ROOT / "test-results" / "manual"
    results.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        saved = temporary / "deck.json"
        saved.write_text((ROOT / "examples" / "presentation.json").read_text(encoding="utf-8"), encoding="utf-8")
        gallery = temporary / "images"
        gallery.mkdir()
        for image in (ROOT / "images").iterdir():
            if image.is_file() and not image.name.startswith(("upload-", "manual-")):
                shutil.copyfile(image, gallery / image.name)
        app = create_app({"PRESENTATION_FILE": saved, "IMAGES_DIR": gallery})
        server = make_server("127.0.0.1", 0, app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel="msedge")
                page = browser.new_page(viewport={"width":1440, "height":900})
                errors = []
                page.on("dialog", lambda dialog: dialog.accept())
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}")
                expect(page.locator(".slide-item")).to_have_count(8)
                page.locator(".slide-item").nth(1).click()
                page.wait_for_timeout(500)
                page.screenshot(path=ROOT / "images" / "manual-editor.png")
                page.locator("#theme-tab").click()
                page.screenshot(path=ROOT / "images" / "manual-theme.png")
                page.locator("#slide-tab").click()
                page.locator("#field-image").click()
                page.wait_for_function("Array.from(document.querySelectorAll('#gallery img')).every(i => i.complete)")
                page.locator("#gallery-dialog").screenshot(path=ROOT / "images" / "manual-gallery.png")
                page.locator("#gallery-dialog .btn-close").click()
                page.locator("#open-import").click()
                page.locator("#json-input").fill('{"theme": {}, "slides": [{"type": "title", "title": "Hello Slidezz"}]}')
                page.locator("#import-dialog").screenshot(path=ROOT / "images" / "manual-import.png")
                page.locator("#cancel-import").click()
                for screenshot in (ROOT / "images").glob("manual-*.png"):
                    shutil.copyfile(screenshot, gallery / screenshot.name)
                data = validate(json.loads((ROOT / "examples" / "manual.json").read_text(encoding="utf-8")))
                response = app.test_client().post("/api/save", json=data)
                assert response.status_code == 200
                page.reload()
                expect(page.locator(".slide-item")).to_have_count(len(data["slides"]))
                for index in range(len(data["slides"])):
                    page.locator(".slide-item").nth(index).click()
                    page.wait_for_timeout(200)
                    expect(page.locator("#overflow-status")).to_have_text("")
                    page.wait_for_function("Array.from(document.querySelectorAll('#preview img')).every(i => i.complete)")
                    assert page.locator("#preview img").evaluate_all("(images) => images.every(i => i.naturalWidth > 0)")
                    page.locator("#preview").screenshot(path=results / f"preview-{index+1:02}.png")
                page.locator(".slide-item").nth(0).click()
                page.locator("#start-presentation").click()
                expect(page.locator("#presentation-position")).to_have_text(f"1 / {len(data['slides'])}")
                page.keyboard.press("ArrowRight")
                expect(page.locator("#presentation-position")).to_have_text(f"2 / {len(data['slides'])}")
                page.locator("#presentation-dialog").screenshot(path=results / "presentation-desktop.png")
                page.keyboard.press("End")
                expect(page.locator("#presentation-position")).to_have_text(f"{len(data['slides'])} / {len(data['slides'])}")
                page.keyboard.press("Escape")
                expect(page.locator("#presentation-dialog")).not_to_be_visible()
                expect(page.locator(".slide-item.active")).to_contain_text(data["slides"][-1]["title"])
                page.set_viewport_size({"width":390, "height":844})
                page.locator("#start-presentation").click()
                expect(page.locator("#presentation-preview .slide-canvas")).to_have_count(1)
                page.wait_for_timeout(200)
                assert page.locator("#presentation-preview").evaluate("(e) => e.clientWidth > 100 && e.getBoundingClientRect().right <= innerWidth")
                page.screenshot(path=results / "presentation-mobile.png")
                assert not errors, errors
                browser.close()
        finally:
            server.shutdown()
            thread.join()
        prefix = output / "slidezz-manual"
        prefix.with_suffix(".json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        prefix.with_suffix(".yaml").write_text(yaml.dump(data, Dumper=PresentationDumper, sort_keys=False), encoding="utf-8")
        prefix.with_suffix(".html").write_text(build_static_html(data, image_files(data, ROOT / "images")), encoding="utf-8")
        prefix.with_suffix(".zip").write_bytes(export_zip(data, ROOT / "images"))
        imported = app.test_client().post("/api/import/zip", data={
            "archive": (BytesIO(prefix.with_suffix(".zip").read_bytes()), "manual.zip")})
        assert imported.status_code == 200, imported.get_data(as_text=True)
        assert imported.get_json() == data
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge")
            page = browser.new_page(viewport={"width":1440, "height":900})
            network, errors = [], []
            page.on("dialog", lambda dialog: dialog.accept())
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("request", lambda request: network.append(request.url) if request.url.startswith(("http:", "https:")) else None)
            page.goto(prefix.with_suffix(".html").as_uri())
            expect(page.locator(".slide-item")).to_have_count(len(data["slides"]))
            page.locator("#start-presentation").click()
            expect(page.locator("#presentation-position")).to_have_text("1 / 28")
            page.keyboard.press("End")
            expect(page.locator("#presentation-position")).to_have_text("28 / 28")
            page.keyboard.press("Escape")
            page.locator("#open-import").click()
            page.locator("#json-file").set_input_files(prefix.with_suffix(".zip"))
            page.locator("#apply-import").click()
            expect(page.locator("#import-dialog")).not_to_be_visible(timeout=60000)
            expect(page.locator(".slide-item")).to_have_count(28)
            assert not network and not errors, (network, errors)
            browser.close()
        generate(data, prefix.with_suffix(".pptx"), images_dir=ROOT / "images")
        subprocess.run([r"C:\Program Files\LibreOffice\program\soffice.exe",
                        "-env:UserInstallation=" + (temporary / "office").as_uri(),
                        "--headless", "--convert-to", "pdf", "--outdir", str(output),
                        str(prefix.with_suffix(".pptx"))], check=True, timeout=120)
        document = pymupdf.open(prefix.with_suffix(".pdf"))
        assert len(document) == len(data["slides"])
        for index, slide in enumerate(document):
            assert slide.get_text().strip(), f"Blank slide {index + 1}"
            for block in slide.get_text("dict")["blocks"]:
                if block["type"] == 0:
                    x0, y0, x1, y1 = block["bbox"]
                    assert min(x0, y0) >= 0 and x1 <= slide.rect.width + 1 and y1 <= slide.rect.height + 1
            slide.get_pixmap(matrix=pymupdf.Matrix(1, 1)).save(results / f"pptx-{index+1:02}.png")
        print(f"Verified {len(data['slides'])} manual slides; outputs: {prefix}.*")


if __name__ == "__main__":
    main()
