from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE

from backend.templates.base import SlideTemplate
from backend.paths import PROJECT_ROOT


class TitleTemplate(SlideTemplate):

    type_name = "title"

    supports_background = True

    schema = [
        {
            "name": "title",
            "type": "text",
            "label": "Title",
        },
        {
            "name": "subtitle",
            "type": "text",
            "label": "Subtitle",
        },
        {
            "name": "author",
            "type": "text",
            "label": "Author",
        },
        {
            "name": "institution",
            "type": "text",
            "label": "Institution",
        },
        {
            "name": "date",
            "type": "text",
            "label": "Date",
        },
        {
            "name": "background_image",
            "type": "image",
            "label": "Background Image",
        },
    ]

    def render(
        self,
        prs,
        slide_data,
        theme,
        page_number,
    ):
        slide = prs.slides.add_slide(
            prs.slide_layouts[6]
        )

        has_background = False
        if self.supports_background:
            has_background = self.add_background(
                slide,
                prs,
                slide_data,
            )

        title_box = slide.shapes.add_textbox(
            Inches(0.8),
            Inches(1.8),
            Inches(10),
            Inches(1),
        )

        title_frame = title_box.text_frame
        title_frame.clear()

        title_paragraph = title_frame.paragraphs[0]
        title_paragraph.text = slide_data.get(
            "title",
            "",
        )

        title_font = title_paragraph.font
        title_font.name = theme["font_name"]
        title_font.size = Pt(
            theme["title_size"]
        )

        if has_background:
            title_font.color.rgb = RGBColor(
                255,
                255,
                255,
            )
        else:
            title_font.color.rgb = RGBColor.from_string(
                theme["primary_color"].replace(
                    "#",
                    "",
                )
            )

        subtitle_box = slide.shapes.add_textbox(
            Inches(0.8),
            Inches(3.0),
            Inches(10),
            Inches(1),
        )

        subtitle_frame = subtitle_box.text_frame
        subtitle_frame.clear()

        subtitle_paragraph = (
            subtitle_frame.paragraphs[0]
        )

        subtitle_paragraph.text = slide_data.get(
            "subtitle",
            "",
        )

        subtitle_font = subtitle_paragraph.font
        subtitle_font.name = theme["font_name"]
        subtitle_font.size = Pt(
            theme["subtitle_size"]
        )

        if has_background:
            subtitle_font.color.rgb = RGBColor(
                255,
                255,
                255,
            )
        else:
            subtitle_font.color.rgb = RGBColor(
                80,
                80,
                80,
            )

        author = slide_data.get(
            "author",
            "",
        )

        institution = slide_data.get(
            "institution",
            "",
        )

        date = slide_data.get(
            "date",
            "",
        )

        footer_lines = []

        if author:
            footer_lines.append(author)

        if institution:
            footer_lines.append(institution)

        if date:
            footer_lines.append(date)

        footer_text = "\n".join(
            footer_lines
        )

        if footer_text:
            footer_box = slide.shapes.add_textbox(
                Inches(0.8),
                Inches(4.8),
                Inches(6),
                Inches(1.2),
            )

            footer_frame = footer_box.text_frame
            footer_frame.clear()

            footer_frame.paragraphs[0].text = footer_text

            footer_font = (
                footer_frame.paragraphs[0].font
            )

            footer_font.name = theme["font_name"]
            footer_font.size = Pt(16)

            if image_name:
                footer_font.color.rgb = RGBColor(
                    255,
                    255,
                    255,
                )
            else:
                footer_font.color.rgb = RGBColor(
                    100,
                    100,
                    100,
                )