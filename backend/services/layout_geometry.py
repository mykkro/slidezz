"""Resolve theme spacing once for browser preview and editable PPTX shapes."""
SETTINGS = [
    dict(name="margin_left", label="Left margin (in)", default=.65, min=.1, max=1.5, step="any"),
    dict(name="margin_right", label="Right margin (in)", default=.633333, min=.1, max=1.5, step="any"),
    dict(name="margin_top", label="Top margin (in)", default=.45, min=.1, max=1.5, step="any"),
    dict(name="margin_bottom", label="Bottom margin (in)", default=.95, min=.6, max=1.5, step="any"),
    dict(name="column_gap", label="Column gap (in)", default=.65, min=0, max=2, step="any"),
    dict(name="panel_padding", label="Panel padding (in)", default=.25, min=0, max=.5, step="any"),
    dict(name="footer_margin_bottom", label="Footer bottom margin (in)", default=.2, min=.1, max=.25, step="any"),
    dict(name="title_size", label="Title size (pt)", default=30, min=18, max=48, step=1),
    dict(name="subtitle_size", label="Subtitle size (pt)", default=18, min=12, max=32, step=1),
    dict(name="body_size", label="Body size (pt)", default=20, min=12, max=32, step=1),
]
DEFAULTS = {setting["name"]: setting["default"] for setting in SETTINGS}


def resolve_layout(template, theme):
    theme = {**DEFAULTS, **theme}
    left, top = theme["margin_left"], theme["margin_top"]
    width = 13.333333 - left - theme["margin_right"]
    height = 7.5 - top - theme["margin_bottom"]
    panels = []
    for original in template.layout:
        panel = dict(original)
        panel.update(x=left + (original["x"]-.65)*width/12.05,
                     y=top + (original["y"]-.45)*height/6.1,
                     w=original["w"]*width/12.05, h=original["h"]*height/6.1)
        scale = theme["title_size"]/30 if panel["field"] == "title" else (
            theme["subtitle_size"]/18 if panel["field"] == "subtitle" else theme["body_size"]/20)
        panel["size"] = original["size"] * scale
        panels.append(panel)
    # Equal-height, side-by-side panels share the theme's column gutter.
    for index, first in enumerate(template.layout):
        for second_index in range(index+1, len(template.layout)):
            second = template.layout[second_index]
            if first["y"] == second["y"] and first["h"] == second["h"] and first["x"] != second["x"]:
                a, b = sorted((index, second_index), key=lambda i: template.layout[i]["x"])
                column_width = (width-theme["column_gap"])/2
                panels[a].update(x=left, w=column_width)
                panels[b].update(x=left+column_width+theme["column_gap"], w=column_width)
    padding = theme["panel_padding"]
    for panel in panels:
        for key in ("x", "y", "w", "h", "size"):
            panel[key] = round(panel[key], 6)
    sx, sy = max(0, left-padding), max(0, top-padding)
    footer_y = 7.5-theme["footer_margin_bottom"]-.3
    return dict(layout=panels,
                surface=dict(x=sx, y=sy, w=min(13.333333, left+width+padding)-sx,
                             h=min(footer_y-.1, top+height+padding)-sy),
                footer=dict(x=left, y=footer_y, w=max(1, width-1), page_x=left+width-.65),
                missing_y=min(top+height+.1, footer_y-.35))
