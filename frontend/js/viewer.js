/* Read-only player. Embedded slides and assets never need a server or saved browser decks. */
(() => {
  "use strict";
  const config = JSON.parse(document.getElementById("viewer-config").textContent);
  if (config.presentation.metadata?.title?.trim()) document.title = config.presentation.metadata.title + " | Slidezz";
  const $ = id => document.getElementById(id);
  let index = 0, version = 0;
  const style = document.createElement("style");
  style.textContent = config.fonts.map(font => `@font-face{font-family:${JSON.stringify(font.family)};font-weight:${font.weight};font-style:${font.style};src:url(data:font/ttf;base64,${font.data}) format("truetype");}`).join("\n");
  document.head.append(style);
  function resize() {
    const stage = $("viewer-stage"), preview = $("viewer-preview");
    const width = Math.max(0, Math.min(stage.clientWidth - 32, (stage.clientHeight - 16) * 16 / 9));
    preview.style.width = width + "px";
    const canvas = preview.querySelector(".slide-canvas");
    if (canvas) canvas.style.transform = `scale(${width / 1280})`;
  }
  async function show(next) {
    const current = ++version;
    if (!config.presentation.slides.length) {
      const empty = document.createElement("div"); empty.className = "viewer-empty"; empty.textContent = "No slides yet";
      $("viewer-preview").replaceChildren(empty);
      $("viewer-position").textContent = "0 / 0";
      $("viewer-previous").disabled = $("viewer-next").disabled = true;
      resize(); return;
    }
    index = Math.max(0, Math.min(next, config.presentation.slides.length - 1));
    const built = SlidezzRenderer.canvas(config.presentation.slides[index], index + 1, config.layouts, config.presentation.theme, {
      markdown: text => Promise.resolve(Object.hasOwn(config.markdown, text) ? config.markdown[text] : ""),
      imageURL: name => Object.hasOwn(config.images, name) ? config.images[name] : "data:image/png;base64,invalid"
    });
    await built.ready;
    if (current !== version) return;
    $("viewer-preview").replaceChildren(built.canvas);
    $("viewer-position").textContent = `${index + 1} / ${config.presentation.slides.length}`;
    $("viewer-previous").disabled = index === 0;
    $("viewer-next").disabled = index === config.presentation.slides.length - 1;
    resize();
    await document.fonts.ready;
  }
  function error(reason) { $("viewer-error").textContent = reason.message; $("viewer-error").hidden = false; }
  $("viewer-previous").onclick = () => show(index - 1).catch(error);
  $("viewer-next").onclick = () => show(index + 1).catch(error);
  $("viewer-fullscreen").onclick = async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch (reason) { error(reason); }
  };
  document.addEventListener("keydown", event => {
    if (event.ctrlKey || event.altKey || event.metaKey) return;
    let next;
    if (["ArrowRight","ArrowDown","PageDown"," "].includes(event.key)) next = index + 1;
    if (["ArrowLeft","ArrowUp","PageUp"].includes(event.key)) next = index - 1;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = config.presentation.slides.length - 1;
    if (next !== undefined) { event.preventDefault(); show(next).catch(error); }
  });
  new ResizeObserver(resize).observe($("viewer-stage"));
  lucide.createIcons();
  show(0).catch(error);
})();
