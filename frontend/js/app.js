/* Schema-driven editor. Slide layout comes directly from the Python registry. */
"use strict";
const $ = id => document.getElementById(id);
let presentation, templates, layoutSettings, imageList = [], selected = 0, editors = [], galleryField = null;
let resolvedLayoutKey = null, resolvedLayouts = null;
let importArchive = null;
let saveTimer, renderTimer, renderVersion = 0, changeVersion = 0;
let saveQueue = Promise.resolve();
const markdownCache = new Map();
const icons = () => lucide.createIcons();
const resizeObserver = new ResizeObserver(entries => {
  for (const entry of entries) {
    const canvas = entry.target.querySelector(".slide-canvas");
    if (canvas) canvas.style.transform = `scale(${entry.contentRect.width / 1280})`;
  }
  checkOverflow();
});
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function icon(name) {
  const node = element("i");
  node.dataset.lucide = name;
  return node;
}
function showError(error) {
  $("error-banner").textContent = error.message || String(error);
  $("error-banner").hidden = false;
}
async function api(path, data, method) {
  const response = await fetch(path, data === undefined ? {} : {
    method: method || "POST",
    headers: data instanceof FormData ? {} : {"Content-Type":"application/json"},
    body: data instanceof FormData ? data : JSON.stringify(data)
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `Request failed (${response.status})`);
  }
  return response;
}
async function json(path, data) { return (await api(path, data)).json(); }
function current() { return presentation.slides[selected]; }
function layoutImage(template) {
  const image = element("img", "layout-icon");
  image.src = template.icon_url;
  image.alt = "";
  return image;
}
function selectTemplate(name) {
  $("template-select").value = name;
  $("selected-template-icon").src = templates[name].icon_url;
  $("selected-template-name").textContent = templates[name].label;
  for (const button of $("template-menu").querySelectorAll("button")) {
    button.classList.toggle("active", button.dataset.template === name);
    button.setAttribute("aria-pressed", String(button.dataset.template === name));
  }
}
function newSlide(type) {
  const slide = {type};
  for (const field of templates[type].fields) {
    if (!field.theme_key) slide[field.name] = field.default ?? "";
  }
  return slide;
}
function changed() {
  changeVersion++;
  $("save-status").textContent = "Unsaved changes";
  clearTimeout(saveTimer);
  saveTimer = setTimeout(save, 500);
  clearTimeout(renderTimer);
  renderTimer = setTimeout(render, 100);
}
function save() {
  const snapshot = JSON.parse(JSON.stringify(presentation));
  const version = changeVersion;
  $("save-status").textContent = "Saving...";
  saveQueue = saveQueue.catch(() => {}).then(async () => {
    await api("/api/save", snapshot);
    if (version === changeVersion) {
      $("save-status").textContent = "Saved";
      $("error-banner").hidden = true;
    }
  }).catch(error => {
    $("save-status").textContent = "Save failed";
    showError(error);
  });
  return saveQueue;
}
async function markdown(text) {
  if (!markdownCache.has(text)) {
    const pending = json("/api/markdown", {text}).then(data => data.html).catch(error => {
      markdownCache.delete(text);
      throw error;
    });
    markdownCache.set(text, pending);
    if (markdownCache.size > 250) markdownCache.delete(markdownCache.keys().next().value);
  }
  return markdownCache.get(text);
}
function imageURL(name) {
  return window.SlidezzStatic ? window.SlidezzStatic.imageURL(name) : "/images/" + encodeURIComponent(name);
}
function slideCanvas(slide, number, layouts) {
  const template = layouts[slide.type];
  const canvas = element("div", "slide-canvas");
  canvas.style.backgroundColor = presentation.theme.background_color;
  canvas.style.fontFamily = presentation.theme.font_name;
  canvas.style.color = presentation.theme.text_color;
  canvas.style.setProperty("--slide-footer-color", presentation.theme.footer_color);
  canvas.style.setProperty("--slide-accent", presentation.theme.primary_color);
  const tasks = [];
  if (slide.background_image) {
    const background = element("img", "slide-background");
    background.src = imageURL(slide.background_image);
    background.alt = "";
    const surface = element("div", "slide-surface");
    for (const [key, property] of [["x", "left"], ["y", "top"], ["w", "width"], ["h", "height"]]) {
      surface.style[property] = template.surface[key] * 96 + "px";
    }
    surface.style.backgroundColor = slide.background_panel_color ?? presentation.theme.background_panel_color;
    surface.style.opacity = 1 - (slide.background_panel_transparency ?? presentation.theme.background_panel_transparency) / 100;
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
    if (box.field === "title") node.style.color = presentation.theme.primary_color;
    if (box.kind === "image") {
      if (value) {
        const image = element("img");
        image.alt = value;
        image.src = imageURL(value);
        image.style.objectFit = slide[box.field + "_fit"] || "contain";
        const alignmentField = template.fields.find(field => field.name === box.field + "_alignment");
        const alignment = alignmentField.options.find(option =>
          option.value === (slide[box.field + "_alignment"] || "center"));
        image.style.objectPosition = `${alignment.x * 100}% ${alignment.y * 100}%`;
        image.onerror = () => { node.replaceChildren(document.createTextNode(`Image ${value} not found`)); };
        image.onload = () => { node.style.background = "transparent"; node.style.padding = "0"; };
        node.append(image);
      } else node.textContent = "Image (not selected) not found";
    } else if (box.kind === "markdown") {
      tasks.push(markdown(value).then(html => { node.innerHTML = html; }));
    } else node.textContent = value;
    canvas.append(node);
  }
  const footer = element("div", "slide-footer", presentation.theme.footer_text || "");
  const page = element("div", "slide-footer slide-page", String(number).padStart(2, "0"));
  footer.style.left = template.footer.x * 96 + "px";
  footer.style.maxWidth = template.footer.w * 96 + "px";
  page.style.left = template.footer.page_x * 96 + "px";
  footer.style.top = page.style.top = template.footer.y * 96 + "px";
  canvas.append(footer, page);
  return {canvas, ready: Promise.all(tasks)};
}
function mount(viewport, canvas) {
  viewport.replaceChildren(canvas);
  canvas.style.transform = `scale(${viewport.getBoundingClientRect().width / 1280})`;
  resizeObserver.observe(viewport);
}
function checkOverflow() {
  const nodes = [...$("preview").querySelectorAll(".slide-block:not(.image)")];
  const overflow = nodes.some(node => node.scrollHeight > node.clientHeight + 2 || node.scrollWidth > node.clientWidth + 2);
  $("overflow-status").textContent = overflow ? "Text exceeds the slide area" : "";
}
async function render() {
  const version = ++renderVersion;
  let layouts;
  try {
    const key = JSON.stringify(layoutSettings.map(setting => presentation.theme[setting.name]));
    if (key !== resolvedLayoutKey) {
      resolvedLayoutKey = key;
      resolvedLayouts = json("/api/layouts", presentation.theme).catch(error => {
        if (resolvedLayoutKey === key) resolvedLayoutKey = null;
        throw error;
      });
    }
    layouts = await resolvedLayouts;
  } catch (error) { showError(error); return; }
  if (version !== renderVersion) return;
  resizeObserver.disconnect();
  $("slides").replaceChildren();
  $("slide-count").textContent = presentation.slides.length;
  const ready = [];
  presentation.slides.forEach((slide, index) => {
    const item = element("button", "slide-item" + (index === selected ? " active" : ""));
    item.type = "button";
    item.setAttribute("aria-label", `Slide ${index + 1}: ${slide.title || templates[slide.type].label}`);
    item.setAttribute("aria-current", index === selected ? "true" : "false");
    item.draggable = true;
    item.ondragstart = event => event.dataTransfer.setData("text/plain", String(index));
    item.ondragover = event => event.preventDefault();
    item.ondrop = event => {
      event.preventDefault();
      const from = Number(event.dataTransfer.getData("text/plain"));
      if (!Number.isInteger(from) || from < 0 || from >= presentation.slides.length) return;
      const [moved] = presentation.slides.splice(from, 1);
      presentation.slides.splice(index, 0, moved);
      selected = index; selectSlide(selected); changed();
    };
    const viewport = element("div", "slide-viewport");
    viewport.setAttribute("aria-hidden", "true");
    const caption = element("div", "slide-caption");
    caption.append(element("span", "number", String(index + 1).padStart(2, "0")),
      element("span", "title", slide.title || templates[slide.type].label));
    item.append(viewport, caption);
    item.onclick = () => selectSlide(index);
    $("slides").append(item);
    const built = slideCanvas(slide, index + 1, layouts);
    mount(viewport, built.canvas);
    ready.push(built.ready);
  });
  const slide = current();
  $("preview").hidden = !slide;
  $("empty-preview").hidden = !!slide;
  $("preview-label").textContent = slide ? templates[slide.type].label : "Slide preview";
  $("slide-position").textContent = `${slide ? selected + 1 : 0} / ${presentation.slides.length}`;
  $("move-up").disabled = !slide || selected === 0;
  $("move-down").disabled = !slide || selected >= presentation.slides.length - 1;
  $("previous-slide").disabled = $("move-up").disabled;
  $("next-slide").disabled = $("move-down").disabled;
  for (const id of ["delete-slide", "duplicate-slide", "export-pptx", "start-presentation"]) $(id).disabled = !slide;
  if (slide) {
    const built = slideCanvas(slide, selected + 1, layouts);
    mount($("preview"), built.canvas);
    ready.push(built.ready);
  } else $("preview").replaceChildren();
  try {
    await Promise.all(ready);
    await document.fonts.ready;
    if (version === renderVersion) checkOverflow();
  } catch (error) { if (version === renderVersion) showError(error); }
}
function selectSlide(index) {
  selected = index;
  render();
  renderForm();
}
function markdownField(wrapper, input, slide, field) {
  const toolbar = element("div", "markdown-toolbar");
  wrapper.insertBefore(toolbar, input);
  const editor = new EasyMDE({
    element: input, initialValue: slide[field.name] || "", toolbar:false, status:false,
    spellChecker:false, autoDownloadFontAwesome:false, minHeight:"150px",
    renderingConfig:{singleLineBreaks:false}, forceSync:true,
    previewRender: (text, preview) => {
      markdown(text).then(html => { if (preview.isConnected) preview.innerHTML = html; }).catch(showError);
      return "";
    }
  });
  const actions = [
    ["bold", "Bold", "**", "**"], ["italic", "Italic", "*", "*"],
    ["heading-2", "Heading", "## ", ""], ["list", "Bullet list", "- ", ""],
    ["list-ordered", "Numbered list", "1. ", ""], ["link", "Link", "[", "](https://example.com)"],
    ["quote", "Quote", "> ", ""], ["eye", "Preview Markdown"]
  ];
  for (const [name, title, before, after] of actions) {
    const button = element("button");
    button.type = "button"; button.title = title; button.setAttribute("aria-label", title);
    button.append(icon(name));
    button.onclick = () => {
      if (name === "eye") { editor.togglePreview(); return; }
      const cm = editor.codemirror;
      cm.replaceSelection(before + (cm.getSelection() || "text") + after);
      cm.focus();
    };
    toolbar.append(button);
  }
  editor.codemirror.on("change", () => { slide[field.name] = editor.value(); changed(); });
  editor.codemirror.getInputField().setAttribute("aria-label", field.label);
  editors.push(editor);
}
function renderForm() {
  for (const editor of editors) editor.toTextArea();
  editors = [];
  $("properties").replaceChildren();
  $("template-label").replaceChildren();
  const slide = current();
  if (!slide) { $("properties").textContent = "No slide selected"; return; }
  const template = templates[slide.type];
  $("template-label").append(layoutImage(template), document.createTextNode(template.label));
  for (const field of template.fields) {
    const wrapper = element("div", "field-wrapper");
    const label = element("label", "form-label", field.label);
    const id = "field-" + field.name;
    label.htmlFor = id;
    wrapper.append(label);
    if (field.type === "color" || field.type === "range") {
      const input = element("input", field.type === "color" ? "form-control form-control-color" : "form-range");
      input.id = id;
      input.type = field.type === "color" ? "color" : "range";
      input.value = slide[field.name] ?? (field.theme_key ? presentation.theme[field.theme_key] : field.default);
      let output;
      if (field.type === "range") {
        input.min = field.min; input.max = field.max; input.step = field.step;
        output = element("output", "range-value", input.value + field.unit);
        output.setAttribute("for", id);
        wrapper.append(output);
      }
      input.oninput = () => {
        slide[field.name] = field.type === "range" ? Number(input.value) : input.value;
        if (output) output.textContent = input.value + field.unit;
        changed();
      };
      wrapper.append(input);
      if (field.theme_key) {
        const inherited = element("label", "theme-inheritance");
        const checkbox = element("input", "form-check-input");
        checkbox.type = "checkbox"; checkbox.id = id + "-use-theme";
        checkbox.checked = !Object.hasOwn(slide, field.name);
        checkbox.setAttribute("aria-label", field.label + ": Use theme");
        input.disabled = checkbox.checked;
        inherited.append(checkbox, document.createTextNode("Use theme"));
        checkbox.onchange = () => {
          if (checkbox.checked) delete slide[field.name];
          else slide[field.name] = field.type === "range" ? Number(input.value) : input.value;
          input.disabled = checkbox.checked;
          if (checkbox.checked) input.value = presentation.theme[field.theme_key];
          if (output) output.textContent = input.value + field.unit;
          changed();
        };
        wrapper.append(inherited);
      }
    } else if (field.type === "choice") {
      const controls = element("div", field.control === "alignment" ? "alignment-grid" : "fit-segments");
      controls.id = id;
      controls.setAttribute("role", "group");
      controls.setAttribute("aria-label", field.label);
      for (const option of field.options) {
        const button = element("button", "choice-button");
        button.type = "button";
        button.title = field.label + ": " + option.label;
        button.setAttribute("aria-label", button.title);
        button.setAttribute("aria-pressed", String((slide[field.name] || field.default) === option.value));
        button.append(icon(option.icon));
        if (field.control !== "alignment") button.append(document.createTextNode(option.label));
        button.onclick = () => {
          slide[field.name] = option.value;
          for (const sibling of controls.children) sibling.setAttribute("aria-pressed", "false");
          button.setAttribute("aria-pressed", "true");
          changed();
        };
        controls.append(button);
      }
      wrapper.append(controls);
    } else if (field.type === "image") {
      const row = element("div", "image-field");
      row.append(element("span", "image-name", slide[field.name] || "No image"));
      const choose = element("button", "btn btn-light btn-sm", "Choose");
      choose.id = id; choose.type = "button"; choose.prepend(icon("image"));
      choose.onclick = () => {
        galleryField = field.name;
        $("gallery-error").textContent = "";
        renderGallery();
        $("gallery-dialog").showModal();
      };
      row.append(choose); wrapper.append(row);
    } else {
      const input = element(field.type === "markdown" ? "textarea" : "input", "form-control");
      input.id = id; input.value = slide[field.name] || ""; input.maxLength = 20000;
      if (field.type !== "markdown") input.type = "text";
      wrapper.append(input);
      $("properties").append(wrapper);
      if (field.type === "markdown") markdownField(wrapper, input, slide, field);
      else input.oninput = () => { slide[field.name] = input.value; changed(); };
      continue;
    }
    $("properties").append(wrapper);
  }
  icons();
}
function renderGallery() {
  $("gallery").replaceChildren();
  if (!imageList.length) $("gallery").textContent = "No images";
  for (const name of imageList) {
    const button = element("button", "gallery-item" + (current()?.[galleryField] === name ? " active" : ""));
    const img = element("img"); img.src = imageURL(name); img.alt = name;
    button.append(img, element("span", "", name)); button.title = name;
    button.onclick = () => {
      current()[galleryField] = name;
      $("gallery-dialog").close(); renderForm(); changed();
    };
    $("gallery").append(button);
  }
  icons();
}
function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const link = element("a"); link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
let presentedIndex = 0, presenterVersion = 0;
function sizePresentation() {
  const stage = $("presentation-stage"), viewport = $("presentation-preview");
  const width = Math.max(0, Math.min(stage.clientWidth - 32, (stage.clientHeight - 16) * 16 / 9));
  viewport.style.width = width + "px";
  const canvas = viewport.querySelector(".slide-canvas");
  if (canvas) canvas.style.transform = `scale(${width / 1280})`;
}
async function presentSlide(index) {
  if (!presentation.slides.length) return;
  presentedIndex = Math.max(0, Math.min(index, presentation.slides.length - 1));
  const version = ++presenterVersion;
  const layouts = await json("/api/layouts", presentation.theme);
  const built = slideCanvas(presentation.slides[presentedIndex], presentedIndex + 1, layouts);
  await built.ready;
  if (version !== presenterVersion || !$("presentation-dialog").open) return;
  $("presentation-preview").replaceChildren(built.canvas);
  $("presentation-position").textContent = `${presentedIndex + 1} / ${presentation.slides.length}`;
  $("presentation-previous").disabled = presentedIndex === 0;
  $("presentation-next").disabled = presentedIndex === presentation.slides.length - 1;
  sizePresentation();
}
function closePresentation() {
  presenterVersion++;
  $("presentation-dialog").close();
  if (document.fullscreenElement === $("presentation-dialog")) document.exitFullscreen().catch(() => {});
  if (presentation.slides.length) selectSlide(presentedIndex);
  $("start-presentation").focus();
}
function bindPresentation() {
  $("start-presentation").onclick = () => {
    if (!presentation.slides.length) return;
    $("presentation-dialog").showModal();
    presentSlide(selected).catch(showError);
  };
  $("exit-presentation").onclick = closePresentation;
  $("presentation-dialog").addEventListener("cancel", event => { event.preventDefault(); closePresentation(); });
  $("presentation-previous").onclick = () => presentSlide(presentedIndex - 1).catch(showError);
  $("presentation-next").onclick = () => presentSlide(presentedIndex + 1).catch(showError);
  $("presentation-fullscreen").onclick = async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await $("presentation-dialog").requestFullscreen();
    } catch (error) { showError(error); }
  };
  $("presentation-dialog").addEventListener("keydown", event => {
    let index;
    if (["ArrowRight", "ArrowDown", "PageDown", " "].includes(event.key)) index = presentedIndex + 1;
    if (["ArrowLeft", "ArrowUp", "PageUp"].includes(event.key)) index = presentedIndex - 1;
    if (event.key === "Home") index = 0;
    if (event.key === "End") index = presentation.slides.length - 1;
    if (index !== undefined) { event.preventDefault(); presentSlide(index).catch(showError); }
  });
  new ResizeObserver(sizePresentation).observe($("presentation-stage"));
}
function bind() {
  bindPresentation();
  for (const setting of layoutSettings) {
    $("theme-" + setting.name).oninput = event => {
      if (event.target.value === "" || !event.target.validity.valid) return;
      presentation.theme[setting.name] = Number(event.target.value);
      changed();
    };
  }
  $("properties").onsubmit = event => event.preventDefault();
  $("add-slide").onclick = () => {
    if (presentation.slides.length >= 200) return showError(new Error("Maximum 200 slides."));
    presentation.slides.push(newSlide($("template-select").value));
    selectSlide(presentation.slides.length - 1); changed();
  };
  $("delete-slide").onclick = () => {
    presentation.slides.splice(selected, 1);
    selectSlide(Math.max(0, Math.min(selected, presentation.slides.length - 1))); changed();
  };
  $("duplicate-slide").onclick = () => {
    if (presentation.slides.length >= 200) return showError(new Error("Maximum 200 slides."));
    presentation.slides.splice(selected + 1, 0, structuredClone(current()));
    selectSlide(selected + 1); changed();
  };
  for (const [id, offset] of [["move-up", -1], ["move-down", 1]]) {
    $(id).onclick = () => {
      const target = selected + offset;
      [presentation.slides[selected], presentation.slides[target]] = [presentation.slides[target], presentation.slides[selected]];
      selectSlide(target); changed();
    };
  }
  $("previous-slide").onclick = () => selectSlide(selected - 1);
  $("next-slide").onclick = () => selectSlide(selected + 1);
  for (const [id, key] of [["font-name", "font_name"], ["primary-color", "primary_color"],
                           ["background-color", "background_color"], ["footer-text", "footer_text"],
                           ["text-color", "text_color"], ["footer-color", "footer_color"],
                           ["panel-color", "background_panel_color"], ["panel-transparency", "background_panel_transparency"]]) {
    $(id).oninput = () => {
      presentation.theme[key] = id === "panel-transparency" ? Number($(id).value) : $(id).value;
      $("theme-panel-value").textContent = presentation.theme.background_panel_transparency + "%";
      renderForm(); changed();
    };
  }
  for (const [id, other, pane, otherPane] of [
    ["slide-tab", "theme-tab", "slide-settings", "theme-settings"],
    ["theme-tab", "slide-tab", "theme-settings", "slide-settings"]
  ]) {
    $(id).onclick = () => {
      $(id).classList.add("active"); $(other).classList.remove("active");
      $(id).setAttribute("aria-selected", "true"); $(other).setAttribute("aria-selected", "false");
      $(pane).hidden = false; $(otherPane).hidden = true;
      for (const editor of editors) editor.codemirror.refresh();
    };
    $(id).onkeydown = event => {
      if (["ArrowLeft", "ArrowRight"].includes(event.key)) { $(other).click(); $(other).focus(); }
    };
  }
  $("download-json").onclick = () => download(new Blob([JSON.stringify(presentation, null, 2)], {type:"application/json"}), "presentation.json");
  $("download-theme").onclick = () => download(new Blob([JSON.stringify(presentation.theme, null, 2)], {type:"application/json"}), "theme.json");
  $("download-yaml").onclick = async () => {
    try {
      download(await (await api("/api/export/yaml", presentation)).blob(), "presentation.yaml");
    } catch (error) { showError(error); }
  };
  for (const [id, format, filename] of [["export-zip", "zip", "presentation.zip"],
                                       ["export-html", "html", "presentation.html"]]) {
    $(id).onclick = async () => {
      $(id).disabled = true;
      try {
        download(await (await api("/api/export/" + format, presentation)).blob(), filename);
      } catch (error) { showError(error); }
      finally { $(id).disabled = false; }
    };
  }
  $("export-pptx").onclick = async () => {
    $("export-pptx").disabled = true;
    try {
      const response = await api("/api/export/pptx", presentation);
      download(await response.blob(), "presentation.pptx");
    } catch (error) { showError(error); }
    finally { $("export-pptx").disabled = !current(); }
  };
  $("open-import").onclick = () => {
    $("import-error").textContent = "";
    $("json-file").value = "";
    importArchive = null;
    $("import-dialog").showModal();
  };
  $("cancel-import").onclick = () => $("import-dialog").close();
  $("import-format").onchange = () => { $("import-source").hidden = $("import-format").value === "zip"; };
  $("json-file").onchange = async event => {
    const file = event.target.files[0];
    if (file) {
      importArchive = /\.zip$/i.test(file.name) ? file : null;
      if (!importArchive) $("json-input").value = await file.text();
      $("import-format").value = importArchive ? "zip" : /\.ya?ml$/i.test(file.name) ? "yaml" : "json";
      $("import-format").onchange();
    }
  };
  $("apply-import").onclick = async () => {
    try {
      let data;
      if ($("import-format").value === "zip") {
        if (!importArchive) throw new Error("Choose a ZIP bundle.");
        const form = new FormData(); form.append("archive", importArchive);
        data = await json("/api/import/zip", form);
        imageList = await json("/api/images");
      } else data = $("import-format").value === "yaml"
          ? await json("/api/import/yaml", {text: $("json-input").value})
          : await json("/api/import", JSON.parse($("json-input").value));
      presentation = data; selectSlide(0); syncTheme(); changed(); $("import-dialog").close();
    } catch (error) { $("import-error").textContent = error.message; }
  };
  $("clear-image").onclick = () => {
    current()[galleryField] = ""; $("gallery-dialog").close(); renderForm(); changed();
  };
  $("image-upload").onchange = async event => {
    const file = event.target.files[0]; if (!file) return;
    const form = new FormData(); form.append("image", file);
    $("gallery-error").textContent = "Uploading...";
    try {
      const result = await json("/api/images", form);
      imageList = await json("/api/images");
      current()[galleryField] = result.name;
      renderGallery(); renderForm(); changed(); $("gallery-error").textContent = "";
    } catch (error) { $("gallery-error").textContent = error.message; }
    finally { event.target.value = ""; }
  };
  window.addEventListener("beforeunload", event => {
    if ($("save-status").textContent !== "Saved" && $("save-status").textContent !== "Ready") {
      event.preventDefault(); event.returnValue = "";
    }
  });
}
function syncTheme() {
  for (const setting of layoutSettings) $("theme-" + setting.name).value = presentation.theme[setting.name];
  const font = $("font-name");
  if (![...font.options].some(option => option.value === presentation.theme.font_name)) {
    font.add(new Option(presentation.theme.font_name, presentation.theme.font_name));
  }
  for (const [id, key] of [["font-name", "font_name"], ["primary-color", "primary_color"],
                           ["background-color", "background_color"], ["footer-text", "footer_text"],
                           ["text-color", "text_color"], ["footer-color", "footer_color"],
                           ["panel-color", "background_panel_color"], ["panel-transparency", "background_panel_transparency"]]) $(id).value = presentation.theme[key];
  $("theme-panel-value").textContent = presentation.theme.background_panel_transparency + "%";
}
async function initialize() {
  try {
    [templates, imageList, presentation, layoutSettings] = await Promise.all([
      json("/api/templates"), json("/api/images"), json("/api/presentation"), json("/api/theme/layout")
    ]);
    for (const setting of layoutSettings) {
      const wrapper = element("div", "mb-3");
      const label = element("label", "form-label", setting.label);
      const input = element("input", "form-control");
      input.id = "theme-" + setting.name; input.type = "number";
      input.min = setting.min; input.max = setting.max; input.step = setting.step;
      label.htmlFor = input.id; wrapper.append(label, input);
      $("layout-settings").append(wrapper);
    }
    for (const [name, definition] of Object.entries(templates)) {
      $("template-select").add(new Option(definition.label, name));
      const item = element("li");
      const button = element("button", "dropdown-item template-option");
      button.type = "button"; button.dataset.template = name;
      button.append(layoutImage(definition), element("span", "", definition.label));
      button.onclick = () => selectTemplate(name);
      item.append(button); $("template-menu").append(item);
    }
    selectTemplate($("template-select").value);
    $("template-select").onchange = () => selectTemplate($("template-select").value);
    syncTheme(); bind(); selectSlide(0); icons();
  } catch (error) { showError(error); }
}
initialize();
