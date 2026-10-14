"""Generate small SVG schematics directly from template panel geometry."""
from xml.etree.ElementTree import Element, SubElement, tostring


def layout_icon(template):
    svg = Element("svg", xmlns="http://www.w3.org/2000/svg", viewBox="0 0 160 90",
                  role="img", **{"aria-label": template.label + " layout"})
    SubElement(svg, "title").text = template.label + " layout"
    SubElement(svg, "rect", x="1", y="1", width="158", height="88", rx="3",
               fill="#ffffff", stroke="#9bb7aa", **{"stroke-width": "2"})
    for panel in template.layout:
        x, y, w, h = (panel[key] * 12 for key in ("x", "y", "w", "h"))
        group = SubElement(svg, "g", **{"data-field": panel["field"], "data-kind": panel["kind"]})
        if panel["kind"] == "image":
            SubElement(group, "rect", x=str(x), y=str(y), width=str(w), height=str(h),
                       rx="1.5", fill="#dcece4", stroke="#76a58e")
            cx, cy = x + w / 2, y + h / 2
            SubElement(group, "path", d=f"M {cx-9} {cy+6} L {cx-2} {cy-3} L {cx+2} {cy+1} L {cx+6} {cy-4} L {cx+12} {cy+6} Z",
                       fill="#76a58e")
            SubElement(group, "circle", cx=str(cx-7), cy=str(cy-5), r="2", fill="#76a58e")
        elif panel["kind"] == "markdown":
            SubElement(group, "rect", x=str(x), y=str(y), width=str(w), height=str(h),
                       rx="1.5", fill="#f1f5f3", stroke="#b5c9bf")
            for line in range(min(4, max(1, int(h / 8)))):
                SubElement(group, "rect", x=str(x+4), y=str(y+5+line*7),
                           width=str(max(1, (w-8) * (0.72 if line == 3 else .9))),
                           height="2", rx="1", fill="#91ad9e")
        else:
            SubElement(group, "rect", x=str(x), y=str(y+min(3, h/4)),
                       width=str(w * (.78 if panel["field"] == "title" else .52)),
                       height=str(min(4 if panel["field"] == "title" else 2, h/2)),
                       rx="1", fill="#16745c" if panel["field"] == "title" else "#91ad9e")
    return tostring(svg, encoding="unicode")
