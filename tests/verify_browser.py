"""End-to-end browser checks with isolated storage; generates README screenshot."""
import argparse
import json
import re
import shutil
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image
from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server
from backend.app import create_app


def assert_layout(page):
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Horizontal page overflow"
    blocks = page.locator("#preview .slide-block")
    assert blocks.count() > 0
    assert page.locator("#overflow-status").inner_text() == ""
    assert page.locator("#preview").evaluate("(e) => e.clientWidth > 100 && e.clientHeight > 50")
    if page.viewport_size["width"] > 800:
        assert page.locator(".workspace").evaluate("(e) => e.getBoundingClientRect().bottom <= innerHeight + 1")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default=None, help="Use an installed browser, e.g. chrome or msedge")
    args = parser.parse_args()
    results = ROOT / "test-results"
    results.mkdir(exist_ok=True)
    (ROOT / "docs").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        gallery = tmp / "images"
        gallery.mkdir()
        for name in ("blue-light-mesh.png", "smoke-blue-blush.png"):
            shutil.copyfile(ROOT / "images" / name, gallery / name)
        app = create_app({"PRESENTATION_FILE": tmp / "deck.json", "IMAGES_DIR": gallery})
        server = make_server("127.0.0.1", 0, app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel=args.channel)
                page = browser.new_page(viewport={"width":1440, "height":900}, device_scale_factor=1)
                errors, external = [], []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("request", lambda request: external.append(request.url) if not request.url.startswith(
                    f"http://127.0.0.1:{server.server_port}") and not request.url.startswith("blob:") else None)
                page.goto(f"http://127.0.0.1:{server.server_port}")
                expect(page).to_have_title("Slidezz")
                expect(page.locator(".brand")).to_have_text("Slidezz")
                page.wait_for_function("document.querySelector('.brand-symbol').complete && document.querySelector('.brand-symbol').naturalWidth > 0")
                expect(page.locator("#template-select option")).to_have_count(8)
                page.locator("#template-picker").click()
                expect(page.locator("#template-menu")).to_be_visible()
                expect(page.locator("#template-menu img")).to_have_count(8)
                page.wait_for_function("Array.from(document.querySelectorAll('#template-menu img')).every(i=>i.complete && i.naturalWidth>0)")
                page.locator("#template-menu button[data-template='title']").click()
                expect(page.locator("#selected-template-name")).to_have_text("Title")
                expect(page.locator("#template-menu")).not_to_be_visible()
                page.locator("#add-slide").click()
                page.locator("#field-title").fill("Edited title")
                expect(page.locator("#preview .title")).to_have_text("Edited title")
                page.locator("#duplicate-slide").click()
                expect(page.locator(".slide-item")).to_have_count(2)
                page.locator("#move-up").click()
                page.locator("#delete-slide").click()
                expect(page.locator(".slide-item")).to_have_count(1)
                page.locator("#open-import").click()
                page.locator("#json-input").fill('{"slides":[{"type":"unknown"}]}')
                page.locator("#apply-import").click()
                expect(page.locator("#import-error")).to_contain_text("unknown")
                expect(page.locator(".slide-item")).to_have_count(1)
                page.locator("#json-file").set_input_files(ROOT / "examples" / "presentation.json")
                expect(page.locator("#json-input")).to_have_value(re.compile("Make room for discovery"))
                page.locator("#apply-import").click()
                expect(page.locator(".slide-item")).to_have_count(8)
                page.locator(".slide-item").nth(1).click()
                expect(page.locator("#preview strong")).to_have_text("important details")
                page.wait_for_function("Array.from(document.querySelectorAll('#preview img')).every(i=>i.complete && i.naturalWidth>0)")
                assert_layout(page)
                expect(page.locator("#save-status")).to_have_text("Saved")
                page.screenshot(path=str(ROOT / "docs" / "editor.png"), full_page=True)
                page.locator("#field-background_image").click()
                page.locator(".gallery-item[title='smoke-blue-blush.png']").click()
                expect(page.locator("#preview .slide-surface")).to_have_css("opacity", "0.5")
                page.locator("#theme-tab").click()
                for font in ["Lato", "Fira Sans", "PT Sans", "PT Serif", "Barlow", "IBM Plex Mono"]:
                    page.locator("#font-name").select_option(font)
                    loaded = page.evaluate("""async (family) => {
                        const faces = await document.fonts.load('20px "' + family + '"', 'Prague');
                        await document.fonts.load('bold 20px "' + family + '"');
                        await document.fonts.load('italic 20px "' + family + '"');
                        await document.fonts.load('italic bold 20px "' + family + '"');
                        return faces.length > 0 && document.fonts.check('20px "' + family + '"');
                    }""", font)
                    assert loaded, font
                page.locator("#font-name").select_option("Arial")
                page.locator("#theme-column_gap").fill("1.2")
                page.locator("#theme-margin_left").fill("0.9")
                page.wait_for_function("""() => {
                    const boxes = document.querySelectorAll('#preview .slide-block');
                    return boxes.length > 2 && Math.abs(parseFloat(boxes[1].style.left) - 86.4) < .01
                      && Math.abs(parseFloat(boxes[2].style.left) - parseFloat(boxes[1].style.left)
                         - parseFloat(boxes[1].style.width) - 115.2) < .01;
                }""")
                page.locator("#theme-column_gap").fill("0.65")
                page.locator("#theme-margin_left").fill("0.65")
                page.locator("#panel-color").fill("#e8f4ea")
                page.locator("#panel-transparency").fill("60")
                with page.expect_download() as theme_download:
                    page.locator("#download-theme").click()
                theme_download.value.save_as(str(results / "theme.json"))
                exported_theme = json.loads((results / "theme.json").read_text())
                assert exported_theme["background_panel_color"] == "#e8f4ea"
                assert exported_theme["background_panel_transparency"] == 60
                assert exported_theme["font_name"] == "Arial"
                assert "slides" not in exported_theme
                expect(page.locator("#preview .slide-surface")).to_have_css("opacity", "0.4")
                expect(page.locator("#preview .slide-surface")).to_have_css("background-color", "rgb(232, 244, 234)")
                page.locator("#slide-tab").click()
                page.locator("#field-background_panel_color-use-theme").uncheck()
                page.locator("#field-background_panel_transparency-use-theme").uncheck()
                page.locator("#field-background_panel_color").fill("#d9f4ff")
                page.locator("#field-background_panel_transparency").fill("75")
                expect(page.locator("#preview .slide-surface")).to_have_css("opacity", "0.25")
                expect(page.locator("#preview .slide-surface")).to_have_css("background-color", "rgb(217, 244, 255)")
                page.locator("#preview").screenshot(path=str(results / "background-panel.png"))
                page.locator("#field-background_panel_transparency").fill("0")
                expect(page.locator("#preview .slide-surface")).to_have_css("opacity", "1")
                page.locator("#field-background_panel_transparency").fill("50")
                expect(page.locator("#preview .slide-surface")).to_have_css("opacity", "0.5")
                page.locator("#field-background_panel_color-use-theme").check()
                page.locator("#field-background_panel_transparency-use-theme").check()
                expect(page.locator("#preview .slide-surface")).to_have_css("opacity", "0.4")
                expect(page.locator("#preview .slide-surface")).to_have_css("background-color", "rgb(232, 244, 234)")
                page.get_by_role("button", name="Image fit: Cover", exact=True).click()
                page.get_by_role("button", name="Image alignment: Bottom right", exact=True).click()
                expect(page.locator("#preview .image img")).to_have_css("object-fit", "cover")
                expect(page.locator("#preview .image img")).to_have_css("object-position", "100% 100%")
                page.locator("#preview").screenshot(path=str(results / "image-cover-bottom-right.png"))
                page.get_by_role("button", name="Image fit: Contain", exact=True).click()
                page.get_by_role("button", name="Image alignment: Top left", exact=True).click()
                expect(page.locator("#preview .image img")).to_have_css("object-fit", "contain")
                expect(page.locator("#preview .image img")).to_have_css("object-position", "0% 0%")
                page.locator("#preview").screenshot(path=str(results / "image-contain-top-left.png"))
                page.locator(".slide-item").nth(4).click()
                page.get_by_role("button", name="Left Image fit: Cover", exact=True).click()
                page.get_by_role("button", name="Left Image alignment: Left", exact=True).click()
                page.get_by_role("button", name="Right Image alignment: Bottom right", exact=True).click()
                expect(page.locator("#preview .image img").nth(0)).to_have_css("object-fit", "cover")
                expect(page.locator("#preview .image img").nth(1)).to_have_css("object-fit", "contain")
                with page.expect_download() as download:
                    page.locator("#export-pptx").click()
                download.value.save_as(str(results / "image-modes.pptx"))
                for index in range(8):
                    page.locator(".slide-item").nth(index).click()
                    page.wait_for_timeout(150)
                    assert_layout(page)
                    page.locator("#preview").screenshot(path=str(results / f"preview-{index+1:02}.png"))
                page.locator(".slide-item").nth(5).click()
                expect(page.locator(".EasyMDEContainer")).to_have_count(2)
                page.locator(".CodeMirror").nth(0).click()
                page.keyboard.press("Control+End")
                page.keyboard.type("\n\n**Independent edit**")
                expect(page.locator("#preview strong")).to_have_text("Independent edit")
                page.locator(".slide-item").nth(1).click()
                page.locator("#field-image").click()
                raw = BytesIO()
                Image.new("RGB", (180, 120), (30, 140, 100)).save(raw, "WEBP")
                page.locator("#image-upload").set_input_files({"name":"browser-test.webp", "mimeType":"image/webp", "buffer":raw.getvalue()})
                expect(page.locator(".image-name").first).to_contain_text("browser-test")
                page.locator("#gallery-dialog .btn-close").click()
                page.wait_for_function("Array.from(document.querySelectorAll('#preview img')).every(i=>i.complete && i.naturalWidth>0)")
                with page.expect_download() as download:
                    page.locator("#export-pptx").click()
                download.value.save_as(str(results / "upload-test.pptx"))
                uploaded = page.locator(".image-name").first.inner_text()
                (gallery / uploaded).unlink()
                page.locator("#open-import").click()
                missing = {"slides":[{"type":"image_left_content","title":"Missing image","image":"absent.png","markdown":"Still readable"}]}
                page.locator("#json-input").fill(json.dumps(missing))
                page.locator("#apply-import").click()
                expect(page.locator("#preview")).to_contain_text("Image absent.png not found")
                # Restore sample before capturing the actual exported deck.
                page.locator("#open-import").click()
                page.locator("#json-input").fill((ROOT / "examples" / "presentation.json").read_text())
                page.locator("#apply-import").click()
                with page.expect_download() as download:
                    page.locator("#export-pptx").click()
                download.value.save_as(str(results / "all-templates.pptx"))
                with page.expect_download() as download:
                    page.locator("#download-json").click()
                download.value.save_as(str(results / "round-trip.json"))
                assert len(json.loads((results / "round-trip.json").read_text())["slides"]) == 8
                page.locator("#bundle-menu-button").click()
                with page.expect_download() as bundle_download:
                    page.locator("#export-zip").click()
                bundle_download.value.save_as(str(results / "server-bundle.zip"))
                page.locator("#bundle-menu-button").click()
                with page.expect_download() as html_download:
                    page.locator("#export-html").click()
                html_download.value.save_as(str(results / "server-bundle.html"))
                page.locator("#open-import").click()
                page.locator("#json-file").set_input_files(results / "server-bundle.zip")
                expect(page.locator("#import-format")).to_have_value("zip")
                page.locator("#apply-import").click()
                expect(page.locator(".slide-item")).to_have_count(8)
                page.locator("#open-import").click()
                page.locator("#import-format").select_option("json")
                page.locator("#cancel-import").click()
                with page.expect_download() as yaml_download:
                    page.locator("#download-yaml").click()
                yaml_download.value.save_as(str(results / "round-trip.yaml"))
                page.locator("#open-import").click()
                page.locator("#json-file").set_input_files(results / "round-trip.yaml")
                expect(page.locator("#import-format")).to_have_value("yaml")
                page.locator("#apply-import").click()
                expect(page.locator(".slide-item")).to_have_count(8)
                page.locator("#open-import").click()
                page.locator("#import-format").select_option("yaml")
                page.locator("#json-input").fill("slides:\n  - type: title\n    title: Pasted YAML")
                page.locator("#apply-import").click()
                expect(page.locator("#preview .title")).to_have_text("Pasted YAML")
                page.locator("#open-import").click()
                page.locator("#json-file").set_input_files(results / "round-trip.yaml")
                page.locator("#apply-import").click()
                expect(page.locator(".slide-item")).to_have_count(8)
                expect(page.locator("#save-status")).to_have_text("Saved")
                page.reload()
                expect(page.locator(".slide-item")).to_have_count(8)
                for width, height, name in [(390,844,"mobile"),(768,1024,"tablet"),(1920,1080,"wide")]:
                    page.set_viewport_size({"width":width,"height":height})
                    page.locator(".slide-item").nth(1).click()
                    page.wait_for_timeout(150)
                    assert_layout(page)
                    page.screenshot(path=str(results / f"{name}.png"), full_page=True)
                assert not errors, errors
                assert not external, external
                browser.close()
                print("Browser checks passed: edits, reorder, Markdown, imports, uploads, downloads, reload and responsive layouts.")
        finally:
            server.shutdown()
            thread.join()


if __name__ == "__main__":
    main()
