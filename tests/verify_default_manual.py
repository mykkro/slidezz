"""First-run manual, empty decks, safe replacement and offline rediscovery."""
from pathlib import Path
import sys
import tempfile
import threading
from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app import create_app


def command(page, name):
    page.locator("#editor-settings").click()
    page.locator(name).click()
    expect(page.locator("#apply-import")).to_be_enabled()


def check(page,url,label):
    page.goto(url)
    expect(page.locator(".slide-item")).to_have_count(31)
    expect(page.locator("#preview .title")).to_have_text("Slidezz")
    expect(page.locator("#document-title")).to_have_text("Slidezz Demo and Manual")
    command(page,"#new-presentation")
    page.once("dialog",lambda dialog:dialog.dismiss())
    page.locator("#apply-import").click()
    expect(page.locator(".slide-item")).to_have_count(31)
    page.once("dialog",lambda dialog:dialog.accept())
    page.locator("#apply-import").click()
    expect(page.locator(".slide-item")).to_have_count(0)
    expect(page.locator("#save-status")).to_have_text("Saved")
    page.reload()
    expect(page.locator("#add-slide")).to_be_visible()
    expect(page.locator(".slide-item")).to_have_count(0)
    page.locator("#add-slide").click()
    page.locator("#field-title").fill("My own presentation")
    expect(page.locator("#save-status")).to_have_text("Saved")
    # Offline re-exports must keep the manual's built-in asset library.
    if label == "offline":
        page.locator("#bundle-menu-button").click()
        with page.expect_download() as download: page.locator("#export-html").click()
        target = ROOT / "test-results/manual-rediscovery.html"
        download.value.save_as(target)
        page.goto(target.as_uri())
        expect(page.locator("#preview .title")).to_have_text("My own presentation")
    command(page,"#load-manual")
    expect(page.locator(".slide-item")).to_have_count(1)
    page.once("dialog",lambda dialog:dialog.dismiss())
    page.locator("#apply-import").click()
    expect(page.locator("#preview .title")).to_have_text("My own presentation")
    page.once("dialog",lambda dialog:dialog.accept())
    page.locator("#apply-import").click()
    expect(page.locator(".slide-item")).to_have_count(31)
    expect(page.locator("#preview .title")).to_have_text("Slidezz")
    page.wait_for_function("Array.from(document.querySelectorAll('#preview img')).every(i=>i.complete && i.naturalWidth>0)")
    page.locator("#start-presentation").click()
    expect(page.locator("#presentation-position")).to_have_text("1 / 31")
    page.keyboard.press("End")
    expect(page.locator("#presentation-position")).to_have_text("31 / 31")
    page.keyboard.press("Escape")


def main():
    (ROOT / "test-results").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        app = create_app({"PRESENTATION_FILE":Path(directory) / "deck.json"})
        server = make_server("127.0.0.1",0,app)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="msedge")
                for label,url in [("online",f"http://127.0.0.1:{server.server_port}"),("offline",(ROOT / "dist/slidezz.html").as_uri())]:
                    context = browser.new_context(viewport={"width":1440,"height":900})
                    page = context.new_page()
                    errors,network = [],[]
                    page.on("pageerror",lambda error:errors.append(str(error)))
                    page.on("request",lambda r:network.append(r.url) if r.url.startswith(("http:","https:")) else None)
                    check(page,url,label)
                    assert not errors,errors
                    if label == "offline": assert not network,network
                    context.close()
                browser.close()
        finally:
            server.shutdown()
            thread.join()
    print("Default manual, saved empty decks, safe replacement and offline HTML rediscovery passed.")


if __name__ == "__main__": main()
