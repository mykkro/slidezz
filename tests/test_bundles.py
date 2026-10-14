from io import BytesIO
import json
from zipfile import ZipFile
import pytest
from PIL import Image
from bs4 import BeautifulSoup

from backend.app import create_app


@pytest.fixture
def client(tmp_path):
    return create_app({"TESTING": True, "PRESENTATION_FILE": tmp_path / "deck.json",
                       "IMAGES_DIR": tmp_path / "images"}).test_client()


def png(color):
    output = BytesIO()
    Image.new("RGB", (120, 80), color).save(output, "PNG")
    return output.getvalue()


def archive(files):
    output = BytesIO()
    with ZipFile(output, "w") as bundle:
        for name, raw in files.items():
            bundle.writestr(name, raw)
    return output.getvalue()


def test_zip_round_trip_contains_images_links_and_offline_editor(client):
    uploaded = client.post("/api/images", data={"image": (BytesIO(png("blue")), "photo.png")}).json["name"]
    data = {"slides": [{"type": "image_left_content", "title": "Bundle", "image": uploaded,
                       "background_image": "missing.png", "markdown": "**Portable**"}]}
    exported = client.post("/api/export/zip", json=data)
    assert exported.status_code == 200
    with ZipFile(BytesIO(exported.data)) as bundle:
        assert {"presentation.json", "manifest.json", "index.html", "images/" + uploaded} <= set(bundle.namelist())
        manifest = json.loads(bundle.read("manifest.json"))
        assert manifest["images"][uploaded] == "images/" + uploaded
        assert manifest["missing_images"] == ["missing.png"]
        soup = BeautifulSoup(bundle.read("index.html"), "html.parser")
        assert not soup.select("script[src], link[rel=stylesheet]")
        config = json.loads(soup.select_one("#static-config").string)
        assert config["images"][uploaded].startswith("data:image/png;base64,")
        assert len(config["fonts"]) == 24
        assert config["presentation"]["slides"][0]["title"] == "Bundle"
    imported = client.post("/api/import/zip", data={"archive": (BytesIO(exported.data), "deck.zip")})
    assert imported.status_code == 200
    assert imported.json["slides"][0]["image"] == uploaded


def test_zip_collision_does_not_overwrite_gallery(client):
    first = archive({"presentation.json": json.dumps({"slides": [{"type":"image_left_content","image":"photo.png"}]}),
                     "images/photo.png": png("blue")})
    assert client.post("/api/import/zip", data={"archive": (BytesIO(first), "first.zip")}).status_code == 200
    second = archive({"presentation.json": json.dumps({"slides": [{"type":"image_left_content","image":"photo.png"}]}),
                      "images/photo.png": png("red")})
    imported = client.post("/api/import/zip", data={"archive": (BytesIO(second), "second.zip")})
    assert imported.status_code == 200
    new_name = imported.json["slides"][0]["image"]
    assert new_name != "photo.png"
    assert client.get("/images/photo.png").data == png("blue")
    assert client.get("/images/" + new_name).data == png("red")


@pytest.mark.parametrize("files", [
    {"../escape.json": "{}"},
    {"presentation.json": '{"slides":[]}', "images/../../escape.png": b"bad"},
    {"presentation.json": '{"slides":[]}', "images/fake.png": b"bad"},
    {"presentation.json": '{"slides":[{"type":"invalid"}]}', "images/photo.png": png("blue")},
    {"presentation.json": '{"slides":[]}', "images/payload.svg": b"<svg/>"},
])
def test_invalid_zip_leaves_deck_and_gallery_unchanged(client, files):
    client.post("/api/save", json={"slides": [{"type": "title", "title": "Keep"}]})
    response = client.post("/api/import/zip", data={"archive": (BytesIO(archive(files)), "bad.zip")})
    assert response.status_code == 400
    assert client.get("/api/presentation").json["slides"][0]["title"] == "Keep"
    assert client.get("/api/images").json == []


def test_html_export_is_self_contained_and_escapes_embedded_data(client):
    data = {"slides": [{"type": "title", "title": "</script><script>window.hacked=true</script>"}]}
    response = client.post("/api/export/html", json=data)
    assert response.status_code == 200 and response.mimetype == "text/html"
    soup = BeautifulSoup(response.data, "html.parser")
    assert not soup.select("script[src], link[rel=stylesheet]")
    config = json.loads(soup.select_one("#static-config").string)
    assert config["presentation"]["slides"][0]["title"] == data["slides"][0]["title"]
    assert "hacked" not in [script.string for script in soup.find_all("script") if script.string == "window.hacked=true"]
def test_viewer_html_is_self_contained_without_editor(client):
    data = {"theme":{"font_name":"Lato"},"slides":[
        {"type":"content","title":"Read-only","markdown":"**Safe** <script>alert(1)</script>",
         "title_font_name":"PT Serif"}]}
    response = client.post("/api/export/viewer", json=data)
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    assert not soup.select("script[src],link[rel=stylesheet],textarea,#properties,.workspace,#import-dialog")
    config = json.loads(soup.select_one("#viewer-config").string)
    assert config["presentation"]["slides"][0]["title"] == "Read-only"
    assert len(config["fonts"]) == 8
    assert {font["family"] for font in config["fonts"]} == {"Lato","PT Serif"}
    assert "<strong>Safe</strong>" in config["markdown"][data["slides"][0]["markdown"]]
    assert "<script>" not in config["markdown"][data["slides"][0]["markdown"]]
    scripts = "\n".join(script.get_text() for script in soup.select("script:not([type='application/json'])"))
    assert "new EasyMDE" not in scripts
    assert "/api/save" not in scripts
    assert "bindImport" not in scripts


def test_viewer_export_accepts_empty_deck_and_rejects_invalid_deck(client):
    assert client.post("/api/export/viewer", json={"slides":[]}).status_code == 200
    assert client.post("/api/export/viewer", json={"slides":[{"type":"unknown"}]}).status_code == 400
