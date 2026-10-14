"""Portable archives and self-contained offline HTML editors."""
import base64
import hashlib
import json
import mimetypes
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile

from bs4 import BeautifulSoup, Comment
from PIL import Image, UnidentifiedImageError

from backend.paths import FRONTEND_DIR, PROJECT_ROOT
from backend.templates.registry import get_template_definitions, get_all_templates
from backend.services.layout_icons import layout_icon
from backend.services.layout_geometry import SETTINGS
from backend.services.slide_renderer import DEFAULT_THEME

MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def referenced_images(data):
    definitions = get_template_definitions()
    return sorted({slide.get(field["name"]) for slide in data["slides"]
                   for field in definitions[slide["type"]]["fields"]
                   if field["type"] == "image" and slide.get(field["name"])})


def image_files(data, root):
    root = root.resolve()
    result = {}
    for name in referenced_images(data):
        path = (root / name).resolve()
        if path.parent == root and path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            result[name] = path.read_bytes()
    return result


def data_url(content, mime):
    return f"data:{mime};base64," + base64.b64encode(content).decode("ascii")


def build_static_html(data, images):
    soup = BeautifulSoup((FRONTEND_DIR / "index.html").read_text(encoding="utf-8"), "html.parser")
    for asset in soup.select('img[src^="/static/"], link[rel="icon"][href^="/static/"]'):
        attribute = "src" if asset.name == "img" else "href"
        path = FRONTEND_DIR / asset[attribute].removeprefix("/static/")
        asset[attribute] = data_url(path.read_bytes(), mimetypes.guess_type(path.name)[0] or "image/png")
    for link in soup.select('link[rel="stylesheet"]'):
        relative = link["href"].removeprefix("/static/")
        if relative == "fonts/fonts.css":
            link.decompose()
            continue
        style = soup.new_tag("style")
        style.string = (FRONTEND_DIR / relative).read_text(encoding="utf-8").replace("</style", "<\\/style")
        link.replace_with(style)
    scripts = []
    for script in list(soup.find_all("script", src=True)):
        relative = script["src"].removeprefix("/static/")
        scripts.append(relative)
        script.decompose()
    offline_dependencies = [
        "vendor/marked/marked.min.js", "vendor/js-yaml/js-yaml.min.js",
        "vendor/fflate/fflate.min.js", "vendor/dompurify/purify.min.js", "js/static-runtime.js",
    ]
    # Inline scripts execute after the body exists; the offline adapter precedes app.js.
    for relative in scripts[:-1] + offline_dependencies + scripts[-1:]:
        script = soup.new_tag("script")
        script.string = (FRONTEND_DIR / relative).read_text(encoding="utf-8").replace("</script", "<\\/script")
        soup.body.append(script)
    soup.head.append(Comment("STATIC_CONFIG"))
    shell = str(soup)
    definitions = get_template_definitions()
    for name, definition in definitions.items():
        definition["icon_url"] = data_url(layout_icon(get_all_templates()[name]).encode(), "image/svg+xml")
    fonts, licenses = bundled_fonts()
    config = dict(presentation=data, defaults=DEFAULT_THEME, templates=definitions,
                  settings=SETTINGS, images={name: data_url(raw, mimetypes.guess_type(name)[0] or "image/png")
                                            for name, raw in images.items()},
                  fonts=fonts, licenses=licenses, shell=shell, viewer_shell=build_viewer_shell(),
                  id=hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:24])
    encoded = json.dumps(config, ensure_ascii=True).replace("<", "\\u003c")
    return shell.replace("<!--STATIC_CONFIG-->",
                         '<script id="static-config" type="application/json">' + encoded + "</script>", 1)


def export_zip(data, root):
    images = image_files(data, root)
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("presentation.json", json.dumps(data, indent=2, ensure_ascii=False))
        archive.writestr("manifest.json", json.dumps(dict(
            images={name: "images/" + name for name in images},
            missing_images=[name for name in referenced_images(data) if name not in images]), indent=2))
        for name, raw in images.items():
            archive.writestr("images/" + name, raw)
        archive.writestr("index.html", build_static_html(data, images))
    return output.getvalue()


def read_zip(raw):
    try:
        with ZipFile(BytesIO(raw)) as archive:
            entries = archive.infolist()
            if len(entries) > 256 or sum(entry.file_size for entry in entries) > MAX_ARCHIVE_BYTES:
                raise ValueError("ZIP contents exceed the 64 MB / 256 file limit.")
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)):
                raise ValueError("ZIP contains duplicate file names.")
            for name in names:
                path = PurePosixPath(name)
                if "\\" in name or path.is_absolute() or ".." in path.parts or ":" in name:
                    raise ValueError("ZIP contains an unsafe path.")
            if "presentation.json" not in names:
                raise ValueError("ZIP must contain presentation.json.")
            data = json.loads(archive.read("presentation.json"))
            images = {}
            for entry in entries:
                path = PurePosixPath(entry.filename)
                if len(path.parts) == 2 and path.parts[0] == "images" and not entry.is_dir():
                    if path.suffix.lower() not in IMAGE_EXTENSIONS:
                        raise ValueError("ZIP gallery images must be PNG, JPEG or WebP.")
                    image_raw = archive.read(entry)
                    with Image.open(BytesIO(image_raw)) as image:
                        if image.format not in ("PNG", "JPEG", "WEBP"):
                            raise ValueError("Unsupported image format in ZIP.")
                        image.verify()
                    images[path.name] = image_raw
            return data, images
    except (BadZipFile, KeyError, UnicodeError, json.JSONDecodeError,
            UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValueError(f"Invalid ZIP bundle: {error}")
def bundled_fonts():
    manifest = json.loads((FRONTEND_DIR / "fonts" / "manifest.json").read_text())
    fonts, licenses = [], {"Slidezz": (PROJECT_ROOT / "LICENSE").read_text()}
    for family in manifest["families"]:
        root = FRONTEND_DIR / "fonts" / family["directory"]
        licenses[family["name"]] = (root / "OFL.txt").read_text(encoding="utf-8")
        for filename in family["files"]:
            fonts.append(dict(path=family["directory"] + "/" + filename, family=family["name"],
                              weight=700 if "Bold" in filename else 400,
                              style="italic" if "Italic" in filename else "normal",
                              data=base64.b64encode((root / filename).read_bytes()).decode("ascii")))
    for path in sorted((FRONTEND_DIR / "vendor").glob("*/LICENSE")):
        licenses[path.parent.name] = path.read_text(encoding="utf-8")
    return fonts, licenses


def build_viewer_shell():
    soup = BeautifulSoup((FRONTEND_DIR / "viewer.html").read_text(encoding="utf-8"), "html.parser")
    favicon = soup.select_one('link[rel="icon"]')
    favicon["href"] = data_url((FRONTEND_DIR / "assets" / "slidezz-mark.png").read_bytes(), "image/png")
    for link in soup.select('link[rel="stylesheet"]'):
        style = soup.new_tag("style")
        style.string = (FRONTEND_DIR / link["href"].removeprefix("/static/")).read_text(encoding="utf-8").replace("</style", "<\\/style")
        link.replace_with(style)
    for source in list(soup.select("script[src]")):
        script = soup.new_tag("script")
        script.string = (FRONTEND_DIR / source["src"].removeprefix("/static/")).read_text(encoding="utf-8").replace("</script", "<\\/script")
        source.decompose()
        soup.body.append(script)
    soup.head.append(Comment("VIEWER_CONFIG"))
    return str(soup)


def build_viewer_html(data, images):
    from backend.services.layout_geometry import resolve_layout
    from backend.services.slide_renderer import markdown_html
    fonts, licenses = bundled_fonts()
    names = {data["theme"]["font_name"].strip().lower()}
    definitions = get_template_definitions()
    for slide in data["slides"]:
        names.update(slide[field["name"]].strip().lower() for field in definitions[slide["type"]]["fields"]
                     if field["type"] == "font" and slide.get(field["name"]))
    markdown = {slide.get(item["field"], ""): markdown_html(slide.get(item["field"], ""))
                for slide in data["slides"] for item in get_all_templates()[slide["type"]].layout
                if item["kind"] == "markdown"}
    config = dict(presentation=data,
                  layouts={name: {**definitions[name], **resolve_layout(template, data["theme"])}
                           for name, template in get_all_templates().items()},
                  markdown=markdown,
                  images={name: data_url(raw, mimetypes.guess_type(name)[0] or "image/png")
                          for name, raw in images.items()},
                  fonts=[font for font in fonts if font["family"].lower() in names],
                  licenses=licenses)
    encoded = json.dumps(config, ensure_ascii=True).replace("<", "\\u003c")
    return build_viewer_shell().replace("<!--VIEWER_CONFIG-->",
        '<script id="viewer-config" type="application/json">' + encoded + "</script>", 1)
