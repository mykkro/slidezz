"""Exercise a file:// standalone editor with no backend and no network."""
from pathlib import Path
import argparse
import json
from zipfile import ZipFile
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-url", default=None)
    args = parser.parse_args()
    results = ROOT / "test-results"
    results.mkdir(exist_ok=True)
    with sync_playwright() as p:
        if args.live_url:
            client = p.request.new_context(base_url=args.live_url)
            data = json.loads((ROOT / "examples" / "presentation.json").read_text())
            for format in ("zip", "html"):
                response = client.post("/api/export/" + format, data=data, timeout=60000)
                assert response.status == 200, response.status
                raw = response.body()
                assert len(raw) > 1000
                if format == "zip":
                    from io import BytesIO
                    with ZipFile(BytesIO(raw)) as archive:
                        assert "index.html" in archive.namelist()
                else:
                    assert raw.startswith(b"<!DOCTYPE")
            client.dispose()
            print("Live server ZIP and HTML downloads: 200 OK, complete bodies.")
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width":1440,"height":900})
        errors, network = [], []
        page.on("dialog", lambda dialog: dialog.accept())
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: network.append(request.url) if request.url.startswith(("http:","https:")) else None)
        page.goto((ROOT / "dist" / "slidezz.html").as_uri())
        expect(page).to_have_title("Slidezz")
        page.wait_for_function("document.querySelector('.brand-symbol').complete && document.querySelector('.brand-symbol').naturalWidth > 0")
        try:
            expect(page.locator(".slide-item")).to_have_count(8)
        except AssertionError:
            print("Browser errors:", errors)
            print("App error:", page.locator("#error-banner").inner_text())
            raise
        expect(page.locator("#export-pptx")).not_to_be_visible()
        page.locator("#start-presentation").click()
        expect(page.locator("#presentation-position")).to_have_text("1 / 8")
        page.keyboard.press("ArrowRight")
        expect(page.locator("#presentation-position")).to_have_text("2 / 8")
        assert page.locator("#presentation-preview .slide-canvas").evaluate("(e) => e.getBoundingClientRect().width > 100")
        page.keyboard.press("Escape")
        expect(page.locator("#presentation-dialog")).not_to_be_visible()
        expect(page.locator(".slide-item.active")).to_contain_text("Make room for discovery")
        page.locator(".slide-item").nth(0).click()
        page.locator("#field-title").fill("Offline edit")
        expect(page.locator("#preview .title")).to_have_text("Offline edit")
        expect(page.locator("#save-status")).to_have_text("Saved")
        page.reload()
        expect(page.locator("#preview .title")).to_have_text("Offline edit")
        page.locator(".slide-item").nth(1).click()
        page.wait_for_function("Array.from(document.querySelectorAll('#preview img')).every(i => i.complete && i.naturalWidth > 0)")
        expect(page.locator("#preview strong")).to_have_text("important details")
        page.locator("#theme-tab").click()
        page.locator("#theme-column_gap").fill("1.2")
        page.locator("#font-name").select_option("Lato")
        expect(page.locator("#save-status")).to_have_text("Saved")
        page.locator("#slide-tab").click()
        page.locator("#bundle-menu-button").click()
        with page.expect_download() as downloaded:
            page.locator("#export-zip").click()
        downloaded.value.save_as(str(results / "offline.zip"))
        with ZipFile(results / "offline.zip") as bundle:
            assert "presentation.json" in bundle.namelist()
            assert "images/blue-light-mesh.png" in bundle.namelist()
            assert "index.html" in bundle.namelist()
        page.locator("#open-import").click()
        page.locator("#json-input").fill('{"slides":[{"type":"title","title":"Replacement"}]}')
        page.locator("#apply-import").click()
        expect(page.locator(".slide-item")).to_have_count(1)
        page.locator("#open-import").click()
        page.locator("#json-file").set_input_files(results / "offline.zip")
        expect(page.locator("#import-format")).to_have_value("zip")
        page.locator("#apply-import").click()
        expect(page.locator(".slide-item")).to_have_count(8)
        expect(page.locator("#preview .title")).to_have_text("Offline edit")
        page.locator("#bundle-menu-button").click()
        with page.expect_download() as downloaded:
            page.locator("#export-html").click()
        downloaded.value.save_as(str(results / "offline-export.html"))
        other = browser.new_page()
        other.on("pageerror", lambda error: errors.append(str(error)))
        other.on("request", lambda request: network.append(request.url) if request.url.startswith(("http:","https:")) else None)
        other.goto((results / "offline-export.html").as_uri())
        expect(other.locator(".slide-item")).to_have_count(8)
        expect(other.locator("#preview .title")).to_have_text("Offline edit")
        other.close()
        page.locator("#open-import").click()
        page.locator("#import-format").select_option("yaml")
        page.locator("#json-input").fill("slides:\n  - type: image_left_content\n    title: Offline YAML\n    image: absent.png\n    markdown: '**Safe** content'")
        page.locator("#apply-import").click()
        expect(page.locator("#preview")).to_contain_text("Image absent.png not found")
        expect(page.locator("#preview strong")).to_have_text("Safe")
        page.locator("#open-import").click()
        page.locator("#json-file").set_input_files(results / "offline.zip")
        page.locator("#apply-import").click()
        expect(page.locator(".slide-item")).to_have_count(8)
        for width, height, name in [(1440,900,"offline-desktop"),(390,844,"offline-mobile")]:
            page.set_viewport_size({"width":width,"height":height})
            page.locator(".slide-item").nth(1).click()
            page.wait_for_timeout(200)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(results / f"{name}.png"),full_page=True)
        assert not network, network
        assert not errors, errors
        browser.close()
        print("Standalone checks passed: no backend/network, editing, persistence, themes, ZIP/HTML export, ZIP/YAML import and responsive layouts.")


if __name__ == "__main__":
    main()
