"""Build one HTML file that opens directly in a browser, without a server."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app import validate
from backend.services.bundles import build_static_html, image_files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--presentation", type=Path, default=ROOT / "examples" / "presentation.json")
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "slidezz.html")
    args = parser.parse_args()
    data = validate(json.loads(args.presentation.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_static_html(data, image_files(data, ROOT / "images")), encoding="utf-8")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
