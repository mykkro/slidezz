from pptx import Presentation
from datetime import datetime, timezone
from backend.services.presentation_metadata import FIELDS, validate_metadata
from pptx.util import Inches
from backend.templates.registry import get_template
from backend.services.slide_renderer import DEFAULT_THEME


def generate(data, output_file, images_dir=None):
    prs = Presentation()
    metadata = validate_metadata(data.get("metadata", {}))
    for name, property_name in FIELDS.items():
        setattr(prs.core_properties, property_name, metadata.get(name, ""))
    prs.core_properties.last_modified_by = metadata.get("author", "")
    prs.core_properties.created = prs.core_properties.modified = datetime.now(timezone.utc)
    prs.slide_width, prs.slide_height = Inches(13.333333), Inches(7.5)
    theme = {**DEFAULT_THEME, **data.get("theme", {})}
    for number, slide in enumerate(data["slides"], 1):
        get_template(slide["type"]).render(prs, slide, theme, number, images_dir)
    prs.save(output_file)
