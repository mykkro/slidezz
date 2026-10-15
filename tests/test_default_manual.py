import json
from pathlib import Path
from bs4 import BeautifulSoup

from backend.app import create_app, create_default_presentation
from backend.services.bundles import build_static_html, referenced_images


def test_fresh_app_uses_manual_without_overwriting_saved_work(tmp_path):
    path = tmp_path / "deck.json"
    client = create_app({"TESTING":True,"PRESENTATION_FILE":path}).test_client()
    default = client.get("/api/presentation").json
    assert default == client.get("/api/manual").json == create_default_presentation()
    assert len(default["slides"]) == 31
    assert default["slides"][0]["title"] == "Slidezz"
    assert default["metadata"]["title"] == "Slidezz Demo and Manual"
    assert not path.exists()
    for data in ({"slides":[]}, {"slides":[{"type":"title","title":"My work"}]}):
        source = json.dumps(data)
        path.write_text(source,encoding="utf-8")
        assert len(client.get("/api/presentation").json["slides"]) == len(data["slides"])
        client.get("/api/manual")
        assert path.read_text(encoding="utf-8") == source


def test_manual_and_its_assets_are_available_in_any_editor_bundle():
    config = json.loads(BeautifulSoup(build_static_html({"slides":[]},{}),"html.parser").select_one("#static-config").string)
    assert len(config["manual"]["slides"]) == 31
    root = Path(__file__).resolve().parents[1] / "images"
    for name in referenced_images(config["manual"]):
        if (root / name).is_file():
            assert name in config["library_names"]
            assert config["images"][name].startswith("data:image/")
