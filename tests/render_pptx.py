"""Render actual PPTX slides through LibreOffice, then inspect PDF page bounds."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pymupdf
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", default="all-templates", choices=["all-templates", "image-modes"])
    args = parser.parse_args()
    prefix = "export" if args.deck == "all-templates" else args.deck
    results = ROOT / "test-results"
    executable = shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.exe"
    if not Path(executable).exists():
        raise SystemExit("Install LibreOffice or put soffice on PATH to render the exported deck.")
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([executable, "-env:UserInstallation=" + Path(profile).as_uri(),
                        "--headless", "--convert-to", "pdf", "--outdir", str(results),
                        str(results / f"{args.deck}.pptx")], check=True, timeout=60)
    document = pymupdf.open(results / f"{args.deck}.pdf")
    assert len(document) == 8
    sheet = Image.new("RGB", (1200, 4 * 370), "#e8eeea")
    draw = ImageDraw.Draw(sheet)
    for index, page in enumerate(document):
        assert abs(page.rect.width / page.rect.height - 16 / 9) < .01
        text = page.get_text()
        assert text.strip(), f"Slide {index+1} is blank"
        for block in page.get_text("dict")["blocks"]:
            if block["type"] == 0:
                x0, y0, x1, y1 = block["bbox"]
                assert x0 >= 0 and y0 >= 0 and x1 <= page.rect.width + 1 and y1 <= page.rect.height + 1
        pix = page.get_pixmap(matrix=pymupdf.Matrix(1.3, 1.3))
        pix.save(results / f"{prefix}-{index+1:02}.png")
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        assert image.getextrema() != ((255,255),(255,255),(255,255))
        image.thumbnail((570,321))
        x, y = (index % 2) * 600 + 15, (index // 2) * 370 + 30
        sheet.paste(image, (x, y))
        draw.text((x, y - 20), f"Slide {index+1:02}", fill="#263631")
    sheet.save(results / f"{prefix}-contact-sheet.png")
    print("All eight PPTX slides rendered; text and shape bounds are valid.")


if __name__ == "__main__":
    main()
