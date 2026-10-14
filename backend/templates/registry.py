"""Templates declare editable fields and a shared 16:9 layout in inches."""
from dataclasses import dataclass


def field(name, kind="text", label=None, default=""):
    return dict(name=name, type=kind, label=label or name.replace("_", " ").title(), default=default)


def box(name, kind, x, y, w, h, size=20):
    return dict(field=name, kind=kind, x=x, y=y, w=w, h=h, size=size)


@dataclass
class LayoutTemplate:
    type_name: str
    label: str
    schema: list
    layout: list

    def render(self, prs, data, theme, number, images_dir=None):
        from backend.services.slide_renderer import render_pptx
        render_pptx(prs, self, data, theme, number, images_dir)


_registry = {}

IMAGE_ALIGNMENTS = [
    dict(value="top_left", label="Top left", x=0, y=0, icon="arrow-up-left"),
    dict(value="top", label="Top", x=.5, y=0, icon="arrow-up"),
    dict(value="top_right", label="Top right", x=1, y=0, icon="arrow-up-right"),
    dict(value="left", label="Left", x=0, y=.5, icon="arrow-left"),
    dict(value="center", label="Center", x=.5, y=.5, icon="dot"),
    dict(value="right", label="Right", x=1, y=.5, icon="arrow-right"),
    dict(value="bottom_left", label="Bottom left", x=0, y=1, icon="arrow-down-left"),
    dict(value="bottom", label="Bottom", x=.5, y=1, icon="arrow-down"),
    dict(value="bottom_right", label="Bottom right", x=1, y=1, icon="arrow-down-right"),
]


def register(template):
    pane_fields = {b["field"] for b in template.layout if b["kind"] == "image"}
    schema = []
    for editable in template.schema:
        schema.append(editable)
        if editable["name"] in pane_fields:
            name, label = editable["name"], editable["label"]
            schema.append(dict(name=name + "_fit", type="choice", label=label + " fit",
                               default="contain", control="segmented", options=[
                                   dict(value="contain", label="Contain", icon="minimize"),
                                   dict(value="cover", label="Cover", icon="maximize"),
                               ]))
            schema.append(dict(name=name + "_alignment", type="choice", label=label + " alignment",
                               default="center", control="alignment", options=IMAGE_ALIGNMENTS))
    template.schema = schema
    if not any(f["name"] == "background_image" for f in template.schema):
        template.schema.append(field("background_image", "image", "Background image"))
    template.schema.extend([
        dict(**field("background_panel_color", "color", "Panel color", "#FFFFFF"),
             theme_key="background_panel_color"),
        dict(name="background_panel_transparency", type="range", label="Panel transparency",
             default=50, min=0, max=100, step=1, unit="%", theme_key="background_panel_transparency"),
    ])
    _registry[template.type_name] = template


TITLE = box("title", "text", .65, .45, 12, .85, 30)
register(LayoutTemplate("title", "Title", [
    field("title", default="A new perspective"), field("subtitle", default="Ideas worth sharing"),
    field("author"), field("institution"), field("date"), field("background_image", "image"),
], [box("title", "text", .85, 1.6, 11.6, 1.5, 44), box("subtitle", "text", .85, 3.3, 11.6, 1, 24),
    box("author", "text", .85, 5, 11.6, .4, 16), box("institution", "text", .85, 5.5, 11.6, .4, 16),
    box("date", "text", .85, 6, 11.6, .4, 16)]))
register(LayoutTemplate("content", "Content", [
    field("title", default="The big picture"),
    field("markdown", "markdown", "Content", "## What matters\n\n- A clear direction\n- **Meaningful** progress\n- Room for new ideas"),
    field("background_image", "image"),
], [TITLE, box("markdown", "markdown", .65, 1.65, 12, 4.9)]))
for name, label, ix, tx in [("image_left_content", "Image + content", .65, 7), ("content_left_image", "Content + image", 7, .65)]:
    register(LayoutTemplate(name, label, [
        field("title", default="A closer look"), field("image", "image", default="blue-light-mesh.png"),
        field("markdown", "markdown", "Content", "## Explore the details\n\nA picture and a **clear message**."),
    ], [TITLE, box("image", "image", ix, 1.65, 5.7, 4.9), box("markdown", "markdown", tx, 1.65, 5.7, 4.9)]))
register(LayoutTemplate("double_image_content", "Two images", [
    field("title", default="Two perspectives"), field("left_image", "image", default="blue-light-mesh.png"),
    field("right_image", "image", default="smoke-blue-blush.png"),
    field("markdown", "markdown", "Caption", "A different view of the same story."),
], [TITLE, box("left_image", "image", .65, 1.65, 5.8, 3.5), box("right_image", "image", 6.85, 1.65, 5.8, 3.5),
    box("markdown", "markdown", .65, 5.5, 12, 1)]))
register(LayoutTemplate("two_columns", "Two columns", [
    field("title", default="Compare and consider"),
    field("left_markdown", "markdown", "Left column", "## Today\n\n- Understand the challenge\n- Gather evidence"),
    field("right_markdown", "markdown", "Right column", "## Tomorrow\n\n- Test the idea\n- Share the results"),
], [TITLE, box("left_markdown", "markdown", .65, 1.65, 5.7, 4.9), box("right_markdown", "markdown", 7, 1.65, 5.7, 4.9)]))
register(LayoutTemplate("quote", "Quote", [
    field("title", default="A thought to take away"), field("quote", "markdown", "Quote", "Progress begins with a good question."),
    field("attribution", default="The team"),
], [TITLE, box("quote", "markdown", 1.2, 2, 10.9, 3, 32), box("attribution", "text", 1.2, 5.5, 10.9, .7, 18)]))
register(LayoutTemplate("section", "Section divider", [
    field("title", default="The next chapter"), field("subtitle", default="From ideas to action"),
], [box("title", "text", .85, 2.2, 11.6, 1.6, 44), box("subtitle", "text", .85, 4, 11.6, 1, 24)]))


def get_template(name):
    if name not in _registry:
        raise ValueError(f"Unknown slide template '{name}'")
    return _registry[name]


def get_all_templates():
    return _registry


def get_template_definitions():
    return {name: dict(type_name=name, label=t.label, fields=t.schema, layout=t.layout,
                      icon_url=f"/api/templates/{name}/icon.svg") for name, t in _registry.items()}
