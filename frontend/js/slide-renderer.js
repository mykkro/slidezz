/* Shared slide canvas for the editor and read-only HTML presentations. */
(() => {
"use strict";
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function canvas(slide, number, layouts, theme, resources) {
  const template = layouts[slide.type];
  const canvas = element("div", "slide-canvas");
  canvas.style.backgroundColor = theme.background_color;
  canvas.style.fontFamily = theme.font_name;
  canvas.style.color = theme.text_color;
  canvas.style.setProperty("--slide-footer-color", theme.footer_color);
  canvas.style.setProperty("--slide-accent", theme.primary_color);
  const tasks = [];
  if (slide.background_image) {
    const background = element("img", "slide-background");
    background.src = resources.imageURL(slide.background_image);
    background.alt = "";
    const surface = element("div", "slide-surface");
    for (const [key, property] of [["x", "left"], ["y", "top"], ["w", "width"], ["h", "height"]]) {
      surface.style[property] = template.surface[key] * 96 + "px";
    }
    surface.style.backgroundColor = slide.background_panel_color ?? theme.background_panel_color;
    surface.style.opacity = 1 - (slide.background_panel_transparency ?? theme.background_panel_transparency) / 100;
    background.onerror = () => {
      background.remove(); surface.remove();
      const missing = element("div", "background-missing", `Image ${slide.background_image} not found`);
      missing.style.left = template.footer.x * 96 + "px";
      missing.style.top = template.missing_y * 96 + "px";
      canvas.append(missing);
    };
    canvas.append(background, surface);
  }
  for (const box of template.layout) {
    const value = slide[box.field] || "";
    const node = element("div", "slide-block " + box.kind + (box.field === "title" ? " title" : ""));
    node.style.left = box.x * 96 + "px";
    node.style.top = box.y * 96 + "px";
    node.style.width = box.w * 96 + "px";
    node.style.height = box.h * 96 + "px";
    node.style.fontSize = box.size * 4 / 3 + "px";
    if (box.field === "title") node.style.color = theme.primary_color;
    if (box.kind !== "image") {
      const style = slide[box.field + "_font_style"] ?? theme.font_style ?? "regular";
      node.style.fontWeight = ["bold","bold_italic"].includes(style) ? "700" : "400";
      node.style.fontStyle = ["italic","bold_italic"].includes(style) ? "italic" : "normal";
      node.style.textAlign = slide[box.field + "_alignment"] ?? theme.text_alignment ?? "left";
      node.style.display = "flex"; node.style.flexDirection = "column";
      node.style.justifyContent = ({top:"flex-start",middle:"safe center",bottom:"safe flex-end"})[slide[box.field + "_vertical_alignment"] ?? theme.text_vertical_alignment ?? "top"];
      node.style.fontFamily = slide[box.field + "_font_name"] || theme.font_name;
      node.style.fontSize = (slide[box.field + "_font_size"] ?? box.size) * 4 / 3 + "px";
      if (slide[box.field + "_font_color"]) {
        node.style.color = slide[box.field + "_font_color"];
        node.style.setProperty("--slide-accent", slide[box.field + "_font_color"]);
      }
    }
    if (box.kind === "image") {
      if (value) {
        const image = element("img");
        image.alt = value;
        image.src = resources.imageURL(value);
        image.style.objectFit = slide[box.field + "_fit"] || "contain";
        const alignmentField = template.fields.find(field => field.name === box.field + "_alignment");
        const alignment = alignmentField.options.find(option =>
          option.value === (slide[box.field + "_alignment"] || "center"));
        image.style.objectPosition = `${alignment.x * 100}% ${alignment.y * 100}%`;
        image.onerror = () => { node.replaceChildren(document.createTextNode(`Image ${value} not found`)); };
        image.onload = () => { node.style.background = "transparent"; node.style.padding = "0"; };
        node.append(image);
      } else node.textContent = "Image (not selected) not found";
    } else {
      const content = element("div", "slide-text-content");
      node.append(content);
      if (box.kind === "markdown") tasks.push(resources.markdown(value).then(html => { content.innerHTML = html; }));
      else content.textContent = value;
    }
    canvas.append(node);
  }
  const footer = element("div", "slide-footer", theme.footer_text || "");
  const page = element("div", "slide-footer slide-page", String(number).padStart(2, "0"));
  for (const node of [footer,page]) {
    node.style.fontFamily = theme.footer_font_name || theme.font_name;
    node.style.fontSize = (theme.footer_font_size ?? 10) * 4 / 3 + "px";
    node.style.fontWeight = ["bold","bold_italic"].includes(theme.footer_font_style) ? "700" : "400";
    node.style.fontStyle = ["italic","bold_italic"].includes(theme.footer_font_style) ? "italic" : "normal";
    node.style.textAlign = theme.footer_alignment || "left";
    node.style.height = (template.footer.h ?? .3) * 96 + "px";
  }
  footer.style.left = template.footer.x * 96 + "px";
  footer.style.maxWidth = template.footer.w * 96 + "px";
  page.style.left = template.footer.page_x * 96 + "px";
  footer.style.width = template.footer.w * 96 + "px";
  page.style.width = (template.footer.page_w ?? .65) * 96 + "px";
  footer.style.top = page.style.top = template.footer.y * 96 + "px";
  canvas.append(footer, page);
  return {canvas, ready: Promise.all(tasks)};
}
window.SlidezzRenderer = {canvas};
})();
