import json
from pathlib import Path

from flask import (
    Flask,
    request,
    send_file,
    send_from_directory,
)

from backend.paths import (
    FRONTEND_DIR,
    PRESENTATIONS_DIR,
    EXPORTS_DIR,
    PROJECT_ROOT,
)

IMAGES_DIR = PROJECT_ROOT / "images"

PRESENTATIONS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def create_default_presentation():
    return {
        "theme": {
            "font_name": "Aptos",
            "primary_color": "#0055AA",
            "background_color": "#FFFFFF",
            "title_size": 30,
            "subtitle_size": 18
        },
        "slides": []
    }


def create_app() -> Flask:

    app = Flask(
        __name__,
        static_folder=str(FRONTEND_DIR),
        static_url_path="/static",
    )

    @app.route("/")
    def index():
        return send_from_directory(
            FRONTEND_DIR,
            "index.html",
        )

    @app.route("/api/images")
    def images():

        results = []

        for file in sorted(IMAGES_DIR.iterdir()):

            if file.suffix.lower() in [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            ]:
                results.append(file.name)

        return results

    @app.route("/images/<path:name>")
    def image(name):

        return send_from_directory(
            IMAGES_DIR,
            name,
        )

    @app.route("/api/save", methods=["POST"])
    def save():

        data = request.json

        presentation_file = (
            PRESENTATIONS_DIR
            / "current.json"
        )

        with open(
            presentation_file,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                data,
                f,
                indent=4,
            )

        return {
            "status": "ok",
        }

    @app.route("/api/export/pptx")
    def export_pptx():

        presentation_file = (
            PRESENTATIONS_DIR
            / "current.json"
        )

        if not presentation_file.exists():

            with open(
                presentation_file,
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(
                    create_default_presentation(),
                    f,
                    indent=4,
                )

        with open(
            presentation_file,
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        if "theme" not in data:
            data["theme"] = create_default_presentation()["theme"]

        from backend.services.pptx_generator import generate

        output = (
            EXPORTS_DIR
            / "presentation.pptx"
        )

        generate(
            data,
            output,
        )

        return send_file(
            output,
            as_attachment=True,
        )

    return app