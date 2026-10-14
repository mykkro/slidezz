"""Download unmodified, openly licensed TTFs at one recorded Google Fonts commit."""
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1] / "frontend" / "fonts"
FAMILIES = [
    ("lato", "Lato", "Lato"),
    ("firasans", "Fira Sans", "FiraSans"),
    ("ptsans", "PT Sans", "PT_Sans-Web"),
    ("ptserif", "PT Serif", "PT_Serif-Web"),
    ("barlow", "Barlow", "Barlow"),
    ("ibmplexmono", "IBM Plex Mono", "IBMPlexMono"),
]
STYLES = [("Regular", 400, "normal"), ("Bold", 700, "normal"),
          ("Italic", 400, "italic"), ("BoldItalic", 700, "italic")]


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "Slidezz-font-vendor"}), timeout=60) as response:
        return response.read()


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "manifest.json"
    if manifest_path.exists():
        commit = json.loads(manifest_path.read_text())["commit"]
    else:
        commit = json.loads(fetch("https://api.github.com/repos/google/fonts/commits/main"))["sha"]
    manifest = {"repository": "https://github.com/google/fonts", "commit": commit, "families": []}
    css = []
    for folder, family, filename in FAMILIES:
        destination = ROOT / folder
        destination.mkdir(exist_ok=True)
        base = f"https://raw.githubusercontent.com/google/fonts/{commit}/ofl/{folder}"
        files = []
        for suffix, weight, style in STYLES:
            name = f"{filename}-{suffix}.ttf"
            data = fetch(f"{base}/{name}")
            if data[:4] not in (b"\x00\x01\x00\x00", b"OTTO"):
                raise ValueError(f"Invalid font: {name}")
            (destination / name).write_bytes(data)
            files.append(name)
            css.append(f"@font-face {{ font-family:'{family}'; font-style:{style}; font-weight:{weight}; font-display:swap; src:url('./{folder}/{name}') format('truetype'); }}")
        (destination / "OFL.txt").write_bytes(fetch(f"{base}/OFL.txt"))
        manifest["families"].append({"name": family, "directory": folder, "files": files, "license": "OFL.txt"})
        print(f"Vendored {family}: four styles and license")
    (ROOT / "fonts.css").write_text("\n".join(css) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
