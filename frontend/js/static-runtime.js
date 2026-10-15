/* Offline API adapter; no requests leave the standalone HTML document. */
(() => {
  "use strict";
  const config = JSON.parse(document.getElementById("static-config").textContent);
  const presentationOnly = new URLSearchParams(location.search).get("mode") === "presentation";
  const clone = value => structuredClone(value);
  let deck = clone(config.presentation), images = {...config.images}, database = null;
  const bytes = encoded => Uint8Array.from(atob(encoded), c => c.charCodeAt(0));
  const dataBytes = url => bytes(url.split(",")[1]);
  const encode = raw => {
    let text = "";
    for (let index = 0; index < raw.length; index += 16384) text += String.fromCharCode(...raw.subarray(index, index+16384));
    return btoa(text);
  };
  const imageData = (name, raw) => "data:" + (/\.webp$/i.test(name) ? "image/webp" : /\.jpe?g$/i.test(name) ? "image/jpeg" : "image/png") + ";base64," + encode(raw);
  function jsonCompatible(value, seen = new WeakSet()) {
    if (typeof value === "number" && !Number.isFinite(value)) throw new Error("Use finite JSON-compatible numbers.");
    if (value && typeof value === "object") {
      if (seen.has(value)) throw new Error("Recursive YAML aliases are not supported.");
      if (!Array.isArray(value) && Object.getPrototypeOf(value) !== Object.prototype) throw new Error("Use JSON-compatible YAML values.");
      seen.add(value);
      for (const child of Object.values(value)) jsonCompatible(child, seen);
      seen.delete(value);
    }
  }
  function validate(data) {
    jsonCompatible(data);
    if (!data || typeof data !== "object" || !Array.isArray(data.slides)) throw new Error("Expected an object with a slides array.");
    if (data.slides.length > 200) throw new Error("A presentation can contain at most 200 slides.");
    if (data.theme !== undefined && (!data.theme || Array.isArray(data.theme) || typeof data.theme !== "object")) throw new Error("Theme must be an object.");
    const theme = {...config.defaults, ...data.theme};
    for (const key of ["primary_color", "background_color", "background_panel_color", "text_color", "footer_color"]) {
      if (typeof theme[key] !== "string" || !/^#[0-9a-f]{6}$/i.test(theme[key])) throw new Error("Invalid " + key + ".");
    }
    for (const key of ["font_name", "footer_font_name", "footer_text", "default_background_image"]) {
      if (typeof theme[key] !== "string" || theme[key].length > 200) throw new Error("Invalid " + key + ".");
    }
    for (const setting of [...config.settings, {name:"background_panel_transparency",min:0,max:100}]) {
      const value = theme[setting.name];
      if (typeof value !== "number" || !Number.isFinite(value) || value < setting.min || value > setting.max) throw new Error("Invalid theme " + setting.name + ".");
    }
    for (const [key, options] of Object.entries({font_style:["regular","bold","italic","bold_italic"],footer_font_style:["regular","bold","italic","bold_italic"],text_alignment:["left","center","right","justify"],footer_alignment:["left","center","right","justify"],text_vertical_alignment:["top","middle","bottom"]})) {
      if (!options.includes(theme[key])) throw new Error("Invalid " + key + ".");
    }
    const slides = data.slides.map((slide, index) => {
      if (!slide || typeof slide.type !== "string" || !Object.hasOwn(config.templates, slide.type)) throw new Error("Slide " + (index+1) + ": unknown or missing template type.");
      const result = {...slide};
      for (const field of config.templates[slide.type].fields) {
        if (field.theme_key && !Object.hasOwn(slide, field.name)) continue;
        const value = Object.hasOwn(slide, field.name) ? slide[field.name] : ["choice","color","range"].includes(field.type) ? field.default : "";
        if (field.type === "range") {
          if (typeof value !== "number" || !Number.isFinite(value) || value < field.min || value > field.max) throw new Error("Invalid " + field.name + ".");
        } else {
          if (typeof value !== "string" || value.length > 20000) throw new Error(field.name + " must be text (max 20000 characters).");
          if (field.type === "font" && (!value.trim() || value.length > 200)) throw new Error(field.name + " must be a font name (1-200 characters).");
          if (field.type === "choice" && !field.options.some(option => option.value === value)) throw new Error("Invalid " + field.name + ".");
          if (field.type === "color" && !/^#[0-9a-f]{6}$/i.test(value)) throw new Error("Invalid " + field.name + ".");
        }
        result[field.name] = field.type === "image" ? ({"blue.jpg":"blue-light-mesh.png", "smoke.jpg":"smoke-blue-blush.png"}[value] || value) : value;
      }
      return result;
    });
    const result = {theme, slides};
    if (Object.hasOwn(data, "metadata")) {
      if (!data.metadata || Array.isArray(data.metadata) || typeof data.metadata !== "object") throw new Error("Metadata must be an object.");
      result.metadata = {...data.metadata};
      for (const name of ["title","author","subject","description","keywords","category","language"]) {
        if (!Object.hasOwn(result.metadata, name)) continue;
        const value = result.metadata[name];
        if (typeof value !== "string" || [...value].length > 255 || /[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(value)) throw new Error("Metadata " + name + " must be text (max 255 characters, no control characters).");
      }
    }
    return result;
  }
  function layouts(theme) {
    const left = theme.margin_left, top = theme.margin_top;
    const footerHeight = Math.max(.3, theme.footer_font_size * 1.2 / 72);
    const footerY = 7.5-theme.footer_margin_bottom-footerHeight;
    const width = 13.333333-left-theme.margin_right, height = Math.min(7.5-theme.margin_bottom,footerY-.1)-top;
    const result = {};
    for (const [name, template] of Object.entries(config.templates)) {
      const panels = template.layout.map(original => {
        const scale = original.field === "title" ? theme.title_size/30 : original.field === "subtitle" ? theme.subtitle_size/18 : theme.body_size/20;
        return {...original, x:left+(original.x-.65)*width/12.05, y:top+(original.y-.45)*height/6.1,
          w:original.w*width/12.05, h:original.h*height/6.1, size:original.size*scale};
      });
      for (let a = 0; a < template.layout.length; a++) {
        for (let b = a+1; b < template.layout.length; b++) {
          const first = template.layout[a], second = template.layout[b];
          if (first.y === second.y && first.h === second.h && first.x !== second.x) {
            const [i,j] = first.x < second.x ? [a,b] : [b,a];
            const columnWidth = (width-theme.column_gap)/2;
            Object.assign(panels[i], {x:left,w:columnWidth});
            Object.assign(panels[j], {x:left+columnWidth+theme.column_gap,w:columnWidth});
          }
        }
      }
      for (const panel of panels) for (const key of ["x","y","w","h","size"]) panel[key] = Math.round(panel[key]*1e6)/1e6;
      const padding = theme.panel_padding, sx = Math.max(0,left-padding), sy = Math.max(0,top-padding);
      const pageWidth = Math.max(.65,theme.footer_font_size*2.2/72);
      result[name] = {...template, layout:panels,
        surface:{x:sx,y:sy,w:Math.min(13.333333,left+width+padding)-sx,h:Math.min(footerY-.1,top+height+padding)-sy},
        footer:{x:left,y:footerY,h:footerHeight,w:Math.max(1,width-pageWidth-.35),page_x:left+width-pageWidth,page_w:pageWidth},
        missing_y:Math.min(top+height+.1,footerY-.35)};
    }
    return result;
  }
  function references(data) {
    return [...new Set([data.theme?.default_background_image, ...data.slides.flatMap(slide => config.templates[slide.type].fields.filter(field => field.type === "image").map(field => slide[field.name]))].filter(Boolean))].sort();
  }
  function htmlBundle(data, selectedImages) {
    const next = {...config, presentation:validate(data), images:selectedImages, id:crypto.randomUUID()};
    const encoded = JSON.stringify(next).replace(/</g, "\\u003c");
    return config.shell.replace("<!--STATIC_CONFIG-->", () => '<script id="static-config" type="application/json">' + encoded + '<' + '/script>');
  }
function renderedMarkdown(text) {
    const escaped = text.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#x27;");
    const wrapper = document.createElement("div");
    wrapper.innerHTML = DOMPurify.sanitize(marked.parse(escaped),{FORBID_TAGS:["style","script"]});
    for (const image of wrapper.querySelectorAll("img")) image.replaceWith(document.createTextNode("[Image "+image.alt+": use a gallery image field]"));
    for (const link of wrapper.querySelectorAll("a")) if (!/^(https?:\/\/|mailto:|#)/i.test(link.getAttribute("href") || "")) link.removeAttribute("href");
    return wrapper.innerHTML;
  }
  function viewerBundle(data) {
    data = validate(data);
    const names = new Set([data.theme.font_name.trim().toLowerCase()]);
    if (data.theme.footer_font_name) names.add(data.theme.footer_font_name.trim().toLowerCase());
    const markdown = {}, selectedImages = {};
    for (const slide of data.slides) {
      for (const field of config.templates[slide.type].fields) {
        if (field.type === "font" && slide[field.name]) names.add(slide[field.name].trim().toLowerCase());
        if (field.type === "markdown") Object.defineProperty(markdown, slide[field.name] || "", {value:renderedMarkdown(slide[field.name] || ""), enumerable:true, configurable:true});
      }
    }
    for (const name of references(data)) if (Object.hasOwn(images, name)) selectedImages[name] = images[name];
    const next = {presentation:data, layouts:layouts(data.theme), markdown, images:selectedImages,
      fonts:config.fonts.filter(font => names.has(font.family.toLowerCase())), licenses:config.licenses};
    const encoded = JSON.stringify(next).replace(/</g, "\\u003c");
    return config.viewer_shell.replace("<!--VIEWER_CONFIG-->", () => '<script id="viewer-config" type="application/json">' + encoded + '<' + '/script>');
  }
  function zipBundle(data) {
    data = validate(data);
    const selectedImages = {};
    const files = {"presentation.json":fflate.strToU8(JSON.stringify(data,null,2))};
    const manifest = {images:{},missing_images:[]};
    for (const name of references(data)) {
      if (Object.hasOwn(images, name)) {
        selectedImages[name] = images[name];
        files["images/"+name] = dataBytes(images[name]);
        manifest.images[name] = "images/"+name;
      } else manifest.missing_images.push(name);
    }
    files["manifest.json"] = fflate.strToU8(JSON.stringify(manifest,null,2));
    files["index.html"] = fflate.strToU8(htmlBundle(data,selectedImages));
    return fflate.zipSync(files, {level:6});
  }
  async function importZip(file) {
    if (!file || file.size > 32*1024*1024) throw new Error("Choose a ZIP bundle under 32 MB.");
    let total = 0, entries = 0;
    const unpacked = fflate.unzipSync(new Uint8Array(await file.arrayBuffer()), {filter:entry => {
      entries++; total += entry.originalSize;
      if (entries > 256 || total > 64*1024*1024) throw new Error("ZIP contents exceed the 64 MB / 256 file limit.");
      if (entry.name.includes("\\") || entry.name.startsWith("/") || entry.name.includes(":") || entry.name.split("/").includes("..")) throw new Error("ZIP contains an unsafe path.");
      return entry.name === "presentation.json" || /^images\/[^/]+$/.test(entry.name);
    }});
    if (!unpacked["presentation.json"]) throw new Error("ZIP must contain presentation.json.");
    const data = validate(JSON.parse(fflate.strFromU8(unpacked["presentation.json"])));
    const additions = {}, rename = {};
    for (const [path, raw] of Object.entries(unpacked)) {
      if (!path.startsWith("images/")) continue;
      const name = path.slice(7);
      if (!/\.(png|jpe?g|webp)$/i.test(name)) throw new Error("ZIP images must be PNG, JPEG or WebP.");
      const png = raw[0] === 137 && raw[1] === 80 && raw[2] === 78 && raw[3] === 71;
      const jpeg = raw[0] === 255 && raw[1] === 216;
      const webp = fflate.strFromU8(raw.subarray(0,4)) === "RIFF" && fflate.strFromU8(raw.subarray(8,12)) === "WEBP";
      if (!png && !jpeg && !webp) throw new Error("Invalid image in ZIP.");
      const url = imageData(name,raw);
      await new Promise((resolve,reject) => {
        const image = new Image(); image.onload = resolve; image.onerror = () => reject(new Error("Invalid image in ZIP.")); image.src = url;
      });
      const target = images[name] && images[name] !== url ? "upload-"+crypto.randomUUID()+"-"+name : name;
      additions[target] = url; rename[name] = target;
    }
    for (const slide of data.slides) for (const field of config.templates[slide.type].fields) {
      if (field.type === "image" && Object.hasOwn(rename,slide[field.name])) slide[field.name] = rename[slide[field.name]];
    }
    if (Object.hasOwn(rename,data.theme.default_background_image)) data.theme.default_background_image = rename[data.theme.default_background_image];
    images = {...images,...additions};
    return data;
  }
  async function persist(data) {
    if (!database) throw new Error("Browser storage is unavailable. Export JSON or ZIP to keep your changes.");
    await new Promise((resolve,reject) => {
      const transaction = database.transaction("decks","readwrite");
      transaction.objectStore("decks").put({presentation:data,images},config.id);
      transaction.oncomplete = resolve; transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(new Error("Browser storage could not save this deck."));
    });
  }
  const ready = (async () => {
    if (presentationOnly) return;
    for (const font of config.fonts) {
      const face = new FontFace(font.family,bytes(font.data).buffer,{weight:String(font.weight),style:font.style});
      document.fonts.add(face);
      await face.load();
    }
    try {
      database = await new Promise((resolve,reject) => {
        // Keep the original database name so existing offline decks survive the rename.
        const request = indexedDB.open("SlidesGenOffline",1);
        request.onupgradeneeded = () => request.result.createObjectStore("decks");
        request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error);
        request.onblocked = () => reject(new Error("Browser storage blocked."));
      });
      const saved = await new Promise((resolve,reject) => {
        const request = database.transaction("decks","readonly").objectStore("decks").get(config.id);
        request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error);
      });
      if (saved) { deck = validate(saved.presentation); images = {...images,...saved.images}; }
    } catch { database = null; }
  })();
  const response = (data,status=200,type="application/json") => new Response(type === "application/json" ? JSON.stringify(data) : data,{status,headers:{"Content-Type":type}});
  window.SlidezzStatic = {presentationOnly, imageURL:name => Object.hasOwn(images,name) ? images[name] : "data:image/png;base64,invalid"};
  window.fetch = async (path,options={}) => {
    await ready;
    try {
      const body = options.body instanceof FormData ? options.body : options.body ? JSON.parse(options.body) : null;
      switch (String(path)) {
        case "/api/templates": return response(config.templates);
        case "/api/theme/layout": return response(config.settings);
        case "/api/theme/presets": return response(config.presets);
        case "/api/presentation": return response(validate(deck));
        case "/api/images":
          if (options.method === "POST") throw new Error("Image upload is available in the Python app. Import a ZIP to add images offline.");
          return response(Object.keys(images).sort());
        case "/api/layouts": return response(layouts(validate({theme:body,slides:[]}).theme));
        case "/api/save": deck = validate(body); await persist(deck); return response({status:"ok"});
        case "/api/import": return response(validate(body));
        case "/api/import/yaml": return response(validate(jsyaml.load(body.text,{schema:jsyaml.JSON_SCHEMA})));
        case "/api/import/zip": return response(await importZip(body.get("archive")));
        case "/api/export/yaml": return response(jsyaml.dump(validate(body),{lineWidth:-1,noRefs:true}),200,"application/yaml");
        case "/api/export/viewer": return response(viewerBundle(body),200,"text/html");
        case "/api/export/zip": return response(zipBundle(body),200,"application/zip");
        case "/api/export/html": {
          const selectedImages = Object.fromEntries(references(body).filter(name => Object.hasOwn(images,name)).map(name => [name,images[name]]));
          return response(htmlBundle(body,selectedImages),200,"text/html");
        }
        case "/api/markdown": {
          if (typeof body.text !== "string" || body.text.length > 20000) throw new Error("Markdown must be text (max 20000 characters).");
          return response({html:renderedMarkdown(body.text)});
        }
        default: throw new Error("This action requires the Python app.");
      }
    } catch (error) { return response({error:error.message},400); }
  };
  document.getElementById("export-pptx").hidden = true;
  document.getElementById("image-upload").closest("label").hidden = true;
  document.querySelector(".brand").href = "#";
  const fontLink = document.querySelector('a[href="/api/fonts/download"]');
  fontLink.onclick = event => {
    event.preventDefault();
    const files = {};
    for (const font of config.fonts) files[font.path] = bytes(font.data);
    for (const [name,license] of Object.entries(config.licenses)) files["licenses/"+name+".txt"] = fflate.strToU8(license);
    const url = URL.createObjectURL(new Blob([fflate.zipSync(files)],{type:"application/zip"}));
    const link = document.createElement("a"); link.href = url; link.download = "slidezz-fonts.zip"; link.click();
    setTimeout(() => URL.revokeObjectURL(url),1000);
  };
})();
