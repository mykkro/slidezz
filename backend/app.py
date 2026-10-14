import json
import re
import uuid
import yaml
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from flask import Flask, Response, abort, jsonify, request, send_file, send_from_directory
from PIL import Image, UnidentifiedImageError
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

from backend.paths import FRONTEND_DIR, PRESENTATIONS_DIR, PROJECT_ROOT
from backend.templates.registry import get_template_definitions, get_all_templates
from backend.services.layout_icons import layout_icon
from backend.services.layout_geometry import SETTINGS as LAYOUT_SETTINGS, resolve_layout
from backend.services.slide_renderer import DEFAULT_THEME, markdown_html
from backend.services.presentation_metadata import validate_metadata

IMAGES_DIR = PROJECT_ROOT / "images"


class PresentationDumper(yaml.SafeDumper):
    pass


def yaml_text(dumper, value):
    return dumper.represent_scalar("tag:yaml.org,2002:str", value,
                                   style="|" if "\n" in value else None)


PresentationDumper.add_representer(str, yaml_text)


def validate(data):
    if not isinstance(data, dict) or not isinstance(data.get("slides"), list):
        raise ValueError("Expected an object with a slides array.")
    if len(data["slides"]) > 200:
        raise ValueError("A presentation can contain at most 200 slides.")
    theme = data.get("theme", {})
    if not isinstance(theme, dict):
        raise ValueError("Theme must be an object.")
    theme = {**DEFAULT_THEME, **theme}
    for key in ("primary_color", "background_color", "background_panel_color", "text_color", "footer_color"):
        if not isinstance(theme[key], str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", theme[key]):
            raise ValueError(f"Invalid {key}.")
    transparency = theme["background_panel_transparency"]
    if isinstance(transparency, bool) or not isinstance(transparency, (int, float)) or not 0 <= transparency <= 100:
        raise ValueError("Theme background_panel_transparency must be between 0 and 100.")
    for setting in LAYOUT_SETTINGS:
        value = theme[setting["name"]]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not setting["min"] <= value <= setting["max"]:
            raise ValueError(f"Theme {setting['name']} must be between {setting['min']} and {setting['max']}.")
    for key in ("font_name", "footer_text"):
        if not isinstance(theme[key], str) or len(theme[key]) > 200:
            raise ValueError(f"Invalid {key}.")
    definitions = get_template_definitions()
    slides = []
    for index, slide in enumerate(data["slides"]):
        if not isinstance(slide, dict) or not isinstance(slide.get("type"), str) or slide["type"] not in definitions:
            raise ValueError(f"Slide {index + 1}: unknown or missing template type.")
        normalized = dict(slide)
        for field in definitions[slide["type"]]["fields"]:
            if field.get("theme_key") and field["name"] not in slide:
                continue
            value = slide.get(field["name"], field["default"] if field["type"] in ("choice", "color", "range") else "")
            if field["type"] == "range":
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not field["min"] <= value <= field["max"]:
                    raise ValueError(f"Slide {index + 1}: {field['name']} must be between {field['min']} and {field['max']}.")
                normalized[field["name"]] = value
                continue
            if not isinstance(value, str) or len(value) > 20000:
                raise ValueError(f"Slide {index + 1}: {field['name']} must be text (max 20000 characters).")
            if field["type"] == "font" and (not value.strip() or len(value) > 200):
                raise ValueError(f"Slide {index + 1}: {field['name']} must be a font name (1-200 characters).")
            if field["type"] == "choice" and value not in {option["value"] for option in field["options"]}:
                raise ValueError(f"Slide {index + 1}: invalid {field['name']}.")
            if field["type"] == "color" and not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
                raise ValueError(f"Slide {index + 1}: invalid {field['name']}.")
            if field["type"] == "image":
                value = {"blue.jpg": "blue-light-mesh.png", "smoke.jpg": "smoke-blue-blush.png"}.get(value, value)
            normalized[field["name"]] = value
        slides.append(normalized)
    result = dict(theme=theme, slides=slides)
    if "metadata" in data:
        result["metadata"] = validate_metadata(data["metadata"])
    return result


def create_default_presentation():
    return dict(theme=DEFAULT_THEME.copy(), slides=[])


def create_app(test_config=None):
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="/static")
    app.config.update(MAX_CONTENT_LENGTH=16 * 1024 * 1024,
                      PRESENTATION_FILE=PRESENTATIONS_DIR / "current.json", IMAGES_DIR=IMAGES_DIR)
    if test_config:
        app.config.update(test_config)

    @app.errorhandler(ValueError)
    def invalid(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/api/templates")
    def templates():
        return get_template_definitions()

    @app.get("/api/theme/layout")
    def theme_layout_settings():
        return LAYOUT_SETTINGS

    @app.post("/api/layouts")
    def layouts():
        theme = validate({"theme": request.get_json(), "slides": []})["theme"]
        return {name: {**definition, **resolve_layout(get_all_templates()[name], theme)}
                for name, definition in get_template_definitions().items()}

    @app.get("/api/presentation")
    def presentation():
        path = app.config["PRESENTATION_FILE"]
        return validate(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else create_default_presentation()

    @app.get("/api/templates/<name>/icon.svg")
    def template_icon(name):
        template = get_all_templates().get(name)
        if template is None:
            abort(404)
        return Response(layout_icon(template), mimetype="image/svg+xml",
                        headers={"Cache-Control": "no-cache"})

    @app.post("/api/save")
    def save():
        data = validate(request.get_json())
        path = app.config["PRESENTATION_FILE"]
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{uuid.uuid4().hex}.tmp")
        temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temporary.replace(path)
        return dict(status="ok")

    @app.post("/api/import")
    def import_json():
        return validate(request.get_json())

    @app.post("/api/import/yaml")
    def import_yaml():
        payload = request.get_json()
        text = payload.get("text") if isinstance(payload, dict) else None
        if not isinstance(text, str):
            raise ValueError("Expected YAML text.")
        try:
            data = yaml.safe_load(text)
            # Reject recursive aliases, dates, non-string keys and other values
            # that cannot round-trip through the presentation's JSON storage.
            encoded = json.dumps(data, allow_nan=False)
            compatible = json.loads(encoded)
            if compatible != data:
                raise ValueError("YAML object keys must be strings.")
        except (yaml.YAMLError, TypeError, ValueError, RecursionError) as error:
            raise ValueError(f"Invalid YAML: {error}")
        return validate(compatible)

    @app.post("/api/export/yaml")
    def export_yaml():
        data = validate(request.get_json())
        return Response(yaml.dump(data, Dumper=PresentationDumper, sort_keys=False, allow_unicode=True),
                        mimetype="application/yaml",
                        headers={"Content-Disposition": 'attachment; filename="presentation.yaml"'})

    @app.post("/api/export/zip")
    def export_bundle():
        from backend.services.bundles import export_zip
        raw = export_zip(validate(request.get_json()), app.config["IMAGES_DIR"])
        return send_file(BytesIO(raw), as_attachment=True, download_name="presentation.zip", mimetype="application/zip")

    @app.post("/api/export/html")
    def export_html():
        from backend.services.bundles import build_static_html, image_files
        data = validate(request.get_json())
        html = build_static_html(data, image_files(data, app.config["IMAGES_DIR"]))
        return send_file(BytesIO(html.encode("utf-8")), as_attachment=True,
                         download_name="presentation.html", mimetype="text/html")

    @app.post("/api/export/viewer")
    def export_viewer():
        from backend.services.bundles import build_viewer_html, image_files
        data = validate(request.get_json())
        html = build_viewer_html(data, image_files(data, app.config["IMAGES_DIR"]))
        return send_file(BytesIO(html.encode("utf-8")), as_attachment=True,
                         download_name="presentation-viewer.html", mimetype="text/html")

    @app.post("/api/import/zip")
    def import_bundle():
        from backend.services.bundles import read_zip
        request.max_content_length = 32 * 1024 * 1024
        file = request.files.get("archive")
        if not file:
            raise ValueError("Choose a ZIP bundle.")
        original, images = read_zip(file.read())
        data = validate(original)
        root = app.config["IMAGES_DIR"]
        rename = {}
        pending = {}
        for name, raw in images.items():
            path = root / name
            target = name
            if path.exists() and path.read_bytes() != raw:
                target = f"upload-{uuid.uuid4().hex[:12]}-{secure_filename(name)}"
            rename[name] = target
            pending[target] = raw
        definitions = get_template_definitions()
        for slide in data["slides"]:
            for field in definitions[slide["type"]]["fields"]:
                if field["type"] == "image" and slide.get(field["name"]) in rename:
                    slide[field["name"]] = rename[slide[field["name"]]]
        root.mkdir(parents=True, exist_ok=True)
        for name, raw in pending.items():
            (root / name).write_bytes(raw)
        return data

    @app.post("/api/markdown")
    def render_markdown():
        payload = request.get_json()
        text = payload.get("text", "") if isinstance(payload, dict) else None
        if not isinstance(text, str) or len(text) > 20000:
            raise ValueError("Markdown must be text (max 20000 characters).")
        return dict(html=markdown_html(text))

    @app.get("/api/images")
    def images():
        root = app.config["IMAGES_DIR"]
        return sorted(p.name for p in root.iterdir() if p.is_file() and p.suffix.lower() in
                      (".jpg", ".jpeg", ".png", ".webp")) if root.exists() else []

    @app.get("/api/fonts/download")
    def download_fonts():
        root = FRONTEND_DIR / "fonts"
        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.suffix in (".ttf", ".txt", ".json"):
                    archive.write(path, path.relative_to(root).as_posix())
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="slidezz-fonts.zip", mimetype="application/zip")

    @app.post("/api/images")
    def upload():
        file = request.files.get("image")
        if not file or not file.filename:
            raise ValueError("Choose an image to upload.")
        raw = file.read()
        try:
            with Image.open(BytesIO(raw)) as img:
                img.verify()
                extension = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(img.format)
                if not extension:
                    raise ValueError("Use a PNG, JPEG or WebP image.")
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
            raise ValueError("The uploaded file is not a valid image.")
        name = f"upload-{uuid.uuid4().hex[:12]}-{secure_filename(file.filename).rsplit('.', 1)[0][:60]}{extension}"
        root = app.config["IMAGES_DIR"]
        root.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(raw)
        return dict(name=name), 201

    @app.get("/images/<path:name>")
    def image(name):
        return send_from_directory(app.config["IMAGES_DIR"], name)

    @app.route("/api/export/pptx", methods=["GET", "POST"])
    def export():
        from backend.services.pptx_generator import generate
        if request.method == "POST":
            data = validate(request.get_json())
        else:
            path = app.config["PRESENTATION_FILE"]
            data = validate(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else create_default_presentation()
        output = BytesIO()
        generate(data, output, app.config["IMAGES_DIR"])
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="presentation.pptx",
                         mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation")

    return app
