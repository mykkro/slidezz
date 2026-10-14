from pptx.dml.color import RGBColor
from pptx.util import Pt

class SlideTemplate:
    def apply_font(
        self,
        paragraph,
        font_name: str,
        font_size: int,
        color: str,
    ) -> None:
        paragraph.font.name = font_name
        paragraph.font.size = Pt(font_size)
        paragraph.font.color.rgb = (
            RGBColor.from_string(
                color.replace("#", "")
            )
        )