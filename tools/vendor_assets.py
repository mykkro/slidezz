"""Fetch pinned npm distributions once; the app serves all assets locally."""
from io import BytesIO
from pathlib import Path
import tarfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1] / "frontend" / "vendor"
PACKAGES = {
    "marked": ("12.0.2", {
        "package/lib/marked.umd.js": "marked.min.js",
        "package/LICENSE.md": "LICENSE",
    }),
    "js-yaml": ("4.1.0", {
        "package/dist/js-yaml.min.js": "js-yaml.min.js",
        "package/LICENSE": "LICENSE",
    }),
    "fflate": ("0.8.2", {
        "package/umd/index.js": "fflate.min.js",
        "package/LICENSE": "LICENSE",
    }),
    "dompurify": ("3.2.6", {
        "package/dist/purify.min.js": "purify.min.js",
        "package/LICENSE": "LICENSE",
    }),
    "bootstrap": ("5.3.8", {
        "package/dist/css/bootstrap.min.css": "bootstrap.min.css",
        "package/dist/js/bootstrap.bundle.min.js": "bootstrap.bundle.min.js",
        "package/LICENSE": "LICENSE",
    }),
    "easymde": ("2.20.0", {
        "package/dist/easymde.min.js": "easymde.min.js",
        "package/dist/easymde.min.css": "easymde.min.css",
        "package/LICENSE": "LICENSE",
    }),
    "lucide": ("0.468.0", {
        "package/dist/umd/lucide.min.js": "lucide.min.js",
        "package/LICENSE": "LICENSE",
    }),
}


def main():
    for name, (version, files) in PACKAGES.items():
        url = f"https://registry.npmjs.org/{name}/-/{name}-{version}.tgz"
        with urlopen(url, timeout=60) as response:
            archive_bytes = response.read()
        with tarfile.open(fileobj=BytesIO(archive_bytes), mode="r:gz") as archive:
            for source, destination in files.items():
                member = archive.extractfile(source)
                target = ROOT / name / destination
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(member.read())
        print(f"Vendored {name} {version}")


if __name__ == "__main__":
    main()
