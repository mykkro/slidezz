/* Editor-only preferences and localization; presentation data is never translated. */
(() => {
  "use strict";
  const messages = {
  "Image with title": "Obrázek s titulkem",
  "Speaker notes": "Poznámky přednášejícího",
  "Font style": "Řez písma",
  "Regular": "Normální",
  "Bold italic": "Tučné kurzívou",
  "Text alignment": "Zarovnání textu",
  "Vertical alignment": "Svislé zarovnání",
  "Middle": "Na střed",
  "Justify": "Do bloku",
  "Footer font": "Písmo zápatí",
  "Footer font style": "Řez písma zápatí",
  "Footer font size (pt)": "Velikost písma zápatí (pt)",
  "Footer alignment": "Zarovnání zápatí",
  "Use theme font": "Použít písmo motivu",
  "Theme preset": "Přednastavený motiv",
  "Apply preset": "Použít motiv",
  "Replace existing slide backgrounds": "Nahradit pozadí stávajících snímků",
  "Reset slide typography and panel overrides": "Obnovit typografii a panely snímků podle motivu",
  "New slide background image": "Obrázek pozadí nových snímků",
  "Editor settings": "Nastavení editoru",
  "Language": "Jazyk",
  "Dark mode": "Tmavý režim",
  "Untitled presentation": "Nepojmenovaná prezentace",
  "Ready": "Připraveno",
  "Present": "Prezentovat",
  "Import": "Importovat",
  "Bundle": "Balíček",
  "ZIP with images": "ZIP s obrázky",
  "Standalone HTML": "Samostatné HTML",
  "Presentation-only HTML": "HTML pouze pro promítání",
  "Export PPTX": "Exportovat PPTX",
  "Slides": "Snímky",
  "Slide": "Snímek",
  "Slide template": "Šablona snímku",
  "Choose slide layout": "Vybrat rozvržení snímku",
  "Add slide": "Přidat snímek",
  "Move slide up": "Posunout snímek nahoru",
  "Move slide down": "Posunout snímek dolů",
  "Duplicate slide": "Duplikovat snímek",
  "Delete slide": "Odstranit snímek",
  "Slide preview": "Náhled snímku",
  "No slides yet": "Zatím žádné snímky",
  "Previous slide": "Předchozí snímek",
  "Next slide": "Další snímek",
  "Slide editor": "Editor snímku",
  "Inspector": "Vlastnosti",
  "Theme": "Motiv",
  "Export theme JSON": "Exportovat motiv JSON",
  "Font": "Písmo",
  "Bundled free fonts": "Přibalená svobodná písma",
  "System fonts": "Systémová písma",
  "Download fonts (TTF)": "Stáhnout písma (TTF)",
  "Accent color": "Barva zvýraznění",
  "Slide background": "Pozadí snímku",
  "Text color": "Barva textu",
  "Footer color": "Barva zápatí",
  "Panel color": "Barva panelu",
  "Panel transparency": "Průhlednost panelu",
  "Footer": "Zápatí",
  "Back to editor": "Zpět do editoru",
  "Toggle fullscreen": "Přepnout celou obrazovku",
  "Presentation": "Prezentace",
  "Presentation details": "Údaje o prezentaci",
  "Subject": "Předmět",
  "Description": "Popis",
  "Keywords": "Klíčová slova",
  "Category": "Kategorie",
  "Document language": "Jazyk dokumentu",
  "Metadata must be an object.": "Metadata musí být objekt.",
  "Import presentation": "Importovat prezentaci",
  "Close": "Zavřít",
  "Import source": "Zdroj importu",
  "Text": "Text",
  "File": "Soubor",
  "Format": "Formát",
  "Presentation file": "Soubor prezentace",
  "Presentation source": "Zdroj prezentace",
  "Cancel": "Zrušit",
  "Apply design": "Použít návrh",
  "Image gallery": "Galerie obrázků",
  "Upload image": "Nahrát obrázek",
  "Clear image": "Odebrat obrázek",
  "Typography": "Typografie",
  "Colors": "Barvy",
  "Background": "Pozadí",
  "Spacing": "Rozestupy",
  "Details": "Podrobnosti",
  "Title": "Titulek",
  "Subtitle": "Podtitulek",
  "Author": "Autor",
  "Institution": "Instituce",
  "Date": "Datum",
  "Content": "Obsah",
  "Image": "Obrázek",
  "Background image": "Obrázek pozadí",
  "Image + content": "Obrázek + obsah",
  "Content + image": "Obsah + obrázek",
  "Two images": "Dva obrázky",
  "Two columns": "Dva sloupce",
  "Section divider": "Předěl oddílu",
  "Quote": "Citace",
  "Attribution": "Zdroj citace",
  "Caption": "Popisek",
  "Left column": "Levý sloupec",
  "Right column": "Pravý sloupec",
  "Left image": "Levý obrázek",
  "Right image": "Pravý obrázek",
  "Font size": "Velikost písma",
  "Use theme": "Použít motiv",
  "Contain": "Celý obrázek",
  "Cover": "Vyplnit",
  "Top left": "Vlevo nahoře",
  "Top": "Nahoře",
  "Top right": "Vpravo nahoře",
  "Left": "Vlevo",
  "Center": "Uprostřed",
  "Right": "Vpravo",
  "Bottom left": "Vlevo dole",
  "Bottom": "Dole",
  "Bottom right": "Vpravo dole",
  "Image fit": "Zobrazení obrázku",
  "Image alignment": "Zarovnání obrázku",
  "Left image fit": "Zobrazení levého obrázku",
  "Right image fit": "Zobrazení pravého obrázku",
  "Left image alignment": "Zarovnání levého obrázku",
  "Right image alignment": "Zarovnání pravého obrázku",
  "Left margin (in)": "Levý okraj (in)",
  "Right margin (in)": "Pravý okraj (in)",
  "Top margin (in)": "Horní okraj (in)",
  "Bottom margin (in)": "Dolní okraj (in)",
  "Column gap (in)": "Mezera mezi sloupci (in)",
  "Panel padding (in)": "Odsazení panelu (in)",
  "Footer bottom margin (in)": "Dolní okraj zápatí (in)",
  "Title size (pt)": "Velikost titulku (pt)",
  "Subtitle size (pt)": "Velikost podtitulku (pt)",
  "Body size (pt)": "Velikost textu (pt)",
  "Choose": "Vybrat",
  "No image": "Bez obrázku",
  "No images": "Žádné obrázky",
  "No slide selected": "Není vybrán snímek",
  "Text exceeds the slide area": "Text přesahuje oblast snímku",
  "Unsaved changes": "Neuložené změny",
  "Saving...": "Ukládání...",
  "Saved": "Uloženo",
  "Save failed": "Uložení selhalo",
  "Bold": "Tučně",
  "Italic": "Kurzíva",
  "Heading": "Nadpis",
  "Bullet list": "Odrážky",
  "Numbered list": "Číslovaný seznam",
  "Link": "Odkaz",
  "Preview Markdown": "Náhled Markdownu",
  "Uploading...": "Nahrávání...",
  "No source": "Prázdný zdroj",
  "Checking design...": "Kontrola návrhu...",
  "Invalid design": "Neplatný návrh",
  "ZIP bundle ready": "Balíček ZIP je připraven",
  "No ZIP bundle selected": "Není vybrán balíček ZIP",
  "Maximum 200 slides.": "Nejvýše 200 snímků.",
  "You have unsaved changes. Discard them and apply this design?": "Máte neuložené změny. Zahodit je a použít tento návrh?",
  "Replace the current presentation with this design?": "Nahradit aktuální prezentaci tímto návrhem?",
  "Choose a ZIP bundle.": "Vyberte balíček ZIP.",
  "Expected an object with a slides array.": "Očekává se objekt s polem slides.",
  "Theme must be an object.": "Motiv musí být objekt.",
  "unknown or missing template type.": "neznámý nebo chybějící typ šablony.",
  "This action requires the Python app.": "Tato akce vyžaduje Python aplikaci."
};
  const key = "SlidezzEditorPreferences";
  let preferences = {language:"en", appearance:"light"};
  try {
    const saved = JSON.parse(localStorage.getItem(key) || "null");
    if (saved?.language === "cs") preferences.language = "cs";
    if (saved?.appearance === "dark") preferences.appearance = "dark";
  } catch (_) {}
  const originals = new WeakMap(), attributes = new WeakMap();
  const excluded = "[data-user-content],.slide-canvas,.slide-caption .title,.gallery-item span,#font-name option,select[id$='_font_name'] option,textarea,.CodeMirror,.editor-preview,#json-highlight,script,style";
  function translate(text) {
    if (preferences.language !== "cs") return text;
    if (messages[text]) return messages[text];
    let match = text.match(/^Valid design: (\d+) slides?$/);
    if (match) return "Platný návrh: " + match[1] + " " + (match[1] === "1" ? "snímek" : +match[1] < 5 && +match[1] > 1 ? "snímky" : "snímků");
    match = text.match(/^Slide (\d+): (.*)$/s);
    if (match) return "Snímek " + match[1] + ": " + translate(match[2]);
    match = text.match(/^Invalid YAML: (.*)$/s);
    if (match) return "Neplatný YAML: " + match[1];
    match = text.match(/^Invalid JSON: (.*)$/s);
    if (match) return "Neplatný JSON: " + match[1];
    match = text.match(/^Request failed \((\d+)\)$/);
    if (match) return "Požadavek selhal (" + match[1] + ")";
    match = text.match(/^(.+): (.+)$/s);
    if (match && (messages[match[1]] || messages[match[2]])) return translate(match[1]) + ": " + translate(match[2]);
    return text;
  }
  function value(source, state) {
    const original = state && source === state.rendered ? state.source : source;
    const match = original.match(/^(\s*)(.*?)(\s*)$/s);
    const rendered = match[1] + translate(match[2]) + match[3];
    return {source:original, rendered};
  }
  let observer;
  function localize() {
    observer?.disconnect();
    document.documentElement.lang = preferences.language;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (node.nodeType === Node.ELEMENT_NODE && node.matches(excluded)) return NodeFilter.FILTER_REJECT;
        return node.nodeType === Node.TEXT_NODE ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
      }
    });
    while (walker.nextNode()) {
      const node = walker.currentNode;
      const state = value(node.nodeValue, originals.get(node));
      originals.set(node, state);
      if (node.nodeValue !== state.rendered) node.nodeValue = state.rendered;
    }
    for (const element of document.body.querySelectorAll("[title],[aria-label],optgroup[label],[placeholder]")) {
      if (element.closest(".slide-canvas,.slide-caption .title,.gallery-item")) continue;
      const states = attributes.get(element) || {};
      for (const name of ["title","aria-label","label","placeholder"]) {
        if (!element.hasAttribute(name)) continue;
        const state = value(element.getAttribute(name), states[name]);
        if (name === "aria-label" && element.classList.contains("slide-item") && preferences.language === "cs") {
          state.rendered = state.source.replace(/^Slide (\d+): /, "Snímek $1: ");
        }
        states[name] = state;
        if (element.getAttribute(name) !== state.rendered) element.setAttribute(name, state.rendered);
      }
      attributes.set(element, states);
    }
    observer?.observe(document.body, {subtree:true,childList:true,characterData:true,
      attributes:true,attributeFilter:["title","aria-label","label","placeholder"]});
  }
  function apply() {
    document.documentElement.dataset.bsTheme = preferences.appearance;
    const appearance = document.getElementById("editor-dark-mode"), language = document.getElementById("editor-language");
    if (appearance) appearance.checked = preferences.appearance === "dark";
    if (language) language.value = preferences.language;
    localize();
    try { localStorage.setItem(key, JSON.stringify(preferences)); } catch (_) {}
  }
  window.SlidezzUI = {translate};
  document.getElementById("editor-dark-mode")?.addEventListener("change", event => {
    preferences.appearance = event.target.checked ? "dark" : "light";
    apply();
  });
  document.getElementById("editor-language")?.addEventListener("change", event => {
    preferences.language = event.target.value;
    apply();
  });
  observer = new MutationObserver(localize);
  apply();
})();
