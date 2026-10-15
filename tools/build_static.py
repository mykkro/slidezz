"""Build one HTML file that opens directly in a browser, without a server."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app import validate
from backend.services.bundles import build_static_html, build_viewer_html, image_files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--presentation", type=Path, default=ROOT / "examples" / "manual.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--presentation-only", action="store_true", help="Build a read-only player without the editor.")
    args = parser.parse_args()
    args.output = args.output or ROOT / "dist" / ("slidezz-presentation.html" if args.presentation_only else "index.html")
    data = validate(json.loads(args.presentation.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    builder = build_viewer_html if args.presentation_only else build_static_html
    args.output.write_text(builder(data, image_files(data, ROOT / "images")), encoding="utf-8")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
