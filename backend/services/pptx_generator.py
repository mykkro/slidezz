from pptx import Presentation

from backend.templates.registry import get_template


def generate(data, output_file):

    prs = Presentation()

    theme = data["theme"]

    for slide_data in data["slides"]:

        template = get_template(
            slide_data["type"]
        )

        template.render(
            prs,
            slide_data,
            theme
        )

    prs.save(output_file)