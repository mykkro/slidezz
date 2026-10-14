from pptx.util import Inches

from backend.templates.base import SlideTemplate


class DoubleImageContentTemplate(
    SlideTemplate
):
    type_name = "double_image_content"

    supports_background = True

    schema = [
        {
            "name": "title",
            "type": "text",
        },
        {
            "name": "left_image",
            "type": "image",
        },
        {
            "name": "right_image",
            "type": "image",
        },
        {
            "name": "markdown",
            "type": "markdown",
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

        self.add_title(
            slide,
            slide_data.get(
                "title",
                ""
            ),
            theme,
        )

        top_image_path = self.get_image_path(
            slide_data.get("image_top")
        )

        bottom_image_path = self.get_image_path(
            slide_data.get("image_bottom")
        )

        slide.shapes.add_picture(
            str(top_image_path),
            Inches(0.5),
            Inches(1.2),
            width=Inches(4.5),
        )

        slide.shapes.add_picture(
            str(bottom_image_path),
            Inches(0.5),
            Inches(3.4),
            width=Inches(4.5),
        )

        content_box = (
            slide.shapes.add_textbox(
                Inches(5.5),
                Inches(1.2),
                Inches(6.5),
                Inches(5),
            )
        )

        self.fill_markdown(
            content_box,
            slide_data["markdown"]
        )