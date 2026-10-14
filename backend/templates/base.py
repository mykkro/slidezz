from pptx.dml.color import RGBColor
from pptx.util import Pt


from pptx.util import Inches

from backend.paths import PROJECT_ROOT

from pptx.util import Pt

from backend.services.markdown_renderer import (
    MarkdownRenderer,
)

from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

from pathlib import Path

from backend.paths import PROJECT_ROOT


class SlideTemplate:
    type_name = "base"

    supports_background = False

    def get_image_path(
        self,
        image_name: str,
    ) -> Path | None:

        if not image_name:
            return None

        path = (
            PROJECT_ROOT
            / "images"
            / image_name
        )

        if not path.exists():
            print(
                f"Image not found: {path}"
            )
            return None

        return path


    def render(
        self,
        prs,
        slide_data,
        theme,
        page_number,
    ):
        raise NotImplementedError

    def add_title(
        self,
        slide,
        title,
        theme,
    ):
        title_box = slide.shapes.add_textbox(
            Inches(0.5),
            Inches(0.3),
            Inches(11),
            Inches(0.5),
        )

        text_frame = title_box.text_frame
        text_frame.text = title

        paragraph = text_frame.paragraphs[0]

        paragraph.font.name = (
            theme["font_name"]
        )

        paragraph.font.size = Pt(24)

        color = (
            theme.get(
                "primary_color",
                "#0055AA"
            )
            .replace("#", "")
        )

        paragraph.font.color.rgb = (
            RGBColor.from_string(
                color
            )
        )
        

    def fill_markdown(
        self,
        textbox,
        markdown_text,
    ):
        blocks = MarkdownRenderer.parse(
            markdown_text
        )

        frame = textbox.text_frame

        frame.clear()

        first = True

        for block_type, text in blocks:

            if first:
                paragraph = frame.paragraphs[0]
                first = False
            else:
                paragraph = frame.add_paragraph()

            paragraph.text = text

            if block_type == "h1":
                paragraph.font.size = Pt(24)

            elif block_type == "h2":
                paragraph.font.size = Pt(20)

            elif block_type == "li":
                paragraph.level = 1

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

    def add_footer(
        self,
        slide,
        prs,
        text: str,
    ) -> None:
        footer = slide.shapes.add_textbox(
            Inches(0.3),
            prs.slide_height - Inches(0.45),
            Inches(8),
            Inches(0.25),
        )

        footer.text_frame.text = text

    def add_page_number(
        self,
        slide,
        prs,
        page_number: int,
    ) -> None:
        width = Inches(0.6)

        page_box = slide.shapes.add_textbox(
            prs.slide_width - width - Inches(0.2),
            prs.slide_height - Inches(0.45),
            width,
            Inches(0.25),
        )

        page_box.text_frame.text = str(page_number)


    def add_background(
        self,
        slide,
        prs,
        slide_data,
    ):
        image_name = slide_data.get(
            "background_image"
        )

        if not image_name:
            return False

        image_path = self.get_image_path(
            slide_data.get("image")
        )

        if not image_path.exists():
            return False

        slide.shapes.add_picture(
            str(image_path),
            0,
            0,
            prs.slide_width,
            prs.slide_height,
        )

        return True

