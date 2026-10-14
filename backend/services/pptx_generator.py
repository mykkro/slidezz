from pptx import Presentation
from pptx.util import Inches
from backend.templates.registry import get_template
from backend.services.slide_renderer import DEFAULT_THEME


def generate(data, output_file, images_dir=None):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333333), Inches(7.5)
    theme = {**DEFAULT_THEME, **data.get("theme", {})}
    for number, slide in enumerate(data["slides"], 1):
        get_template(slide["type"]).render(prs, slide, theme, number, images_dir)
    prs.save(output_file)
