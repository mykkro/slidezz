# Slidezz YAML Authoring Guide

Create a deck in a text editor, then import it into Slidezz to preview, refine and
export it. This guide covers every built-in slide layout and editable property.
See [README](README.md) for installation and [the visual manual](examples/manual.json)
for a longer demonstration.

## Make Your First Presentation

Fresh editors open the built-in slide manual. To start empty, choose **Editor
settings > New presentation**, then apply the empty design. You can revisit the
manual using **Editor settings > Open demo & manual** without downloading files;
review and confirm replacement first. Saved work is never replaced on startup.

1. Copy the complete deck below into a `.yaml` or `.yml` file, or paste it directly
   into **Import > Text**, with YAML selected.
2. Inspect the validation result, then choose **Apply design**. Import replaces the
   current presentation, with a confirmation and an additional warning for unsaved work.
3. Select slides in the left pane. Edit their content on the right; use **Theme**
   for shared styling and **Presentation** for document metadata.
4. Check every preview for overflow. Shorten text, reduce its font size or split a
   crowded slide. Press **Present** to rehearse the deck.
5. Download YAML/JSON for its structure, ZIP for the deck and referenced images,
   standalone HTML for an offline editor, or presentation-only HTML for a viewer.
   The Python app additionally exports editable PPTX.

YAML and JSON describe the same data: an object with `slides`, and optional
`metadata` and `theme` objects. Slides run in list order on a 16:9 canvas.
At most 200 slides are accepted. `slides: []` creates an empty deck.

## Complete Deck: All Nine Layouts

This is a complete importable document. The image filenames refer to bundled
gallery assets. Replace them with filenames from your own gallery when needed.

```yaml
metadata:
  title: A new perspective
  author: Your team
  subject: Project review
  description: A short presentation made with Slidezz.
  keywords: "review, planning, Slidezz"
  category: Team presentations
  language: en

theme:
  font_name: Lato
  default_background_image: ""
  font_style: regular
  text_alignment: left
  text_vertical_alignment: top
  footer_font_name: ""
  footer_font_style: regular
  footer_alignment: left
  footer_font_size: 10
  primary_color: "#16745C"
  background_color: "#FFFFFF"
  text_color: "#263631"
  footer_color: "#60716B"
  footer_text: Project review
  background_panel_color: "#FFFFFF"
  background_panel_transparency: 50
  title_size: 30
  subtitle_size: 18
  body_size: 20
  margin_left: 0.65
  margin_right: 0.633333
  margin_top: 0.45
  margin_bottom: 0.95
  column_gap: 0.65
  panel_padding: 0.25
  footer_margin_bottom: 0.2

slides:
  - type: image
    title: In focus
    image: teal-light-wave.png
    image_fit: cover
    image_alignment: center
    notes: "Show the visual first, then introduce the main idea."
  - type: title
    title: A new perspective
    subtitle: Ideas worth sharing
    author: Your team
    institution: Research group
    date: "2026-10-14"
    background_image: smoke-blue-blush.png

  - type: content
    title: The big picture
    markdown: |
      ## What matters

      - A clear direction
      - **Meaningful** progress
      - Room for new ideas

  - type: image_left_content
    title: A closer look
    image: blue-light-mesh.png
    image_fit: cover
    image_alignment: top_left
    markdown: |
      ## Explore the details

      A picture on the left and a **clear message** on the right.

  - type: content_left_image
    title: From evidence to action
    markdown: |
      1. Understand the challenge.
      2. Test the idea.
      3. Share the results.
    image: smoke-blue-blush.png
    image_fit: contain
    image_alignment: center

  - type: double_image_content
    title: Two perspectives
    left_image: blue-light-mesh.png
    left_image_fit: cover
    left_image_alignment: left
    right_image: smoke-blue-blush.png
    right_image_fit: contain
    right_image_alignment: bottom_right
    markdown: |
      Two views of the same story. Keep this **caption short**.

  - type: two_columns
    title: Compare and consider
    left_markdown: |
      ## Today

      - Understand the challenge
      - Gather evidence
    right_markdown: |
      ## Tomorrow

      - Test the idea
      - Share the results

  - type: quote
    title: A thought to take away
    quote: |
      Progress begins with a **good question**.
    attribution: The team

  - type: section
    title: The next chapter
    subtitle: From ideas to action
    background_image: blue-light-mesh.png
```

## Generate A Deck Programmatically

Treat a presentation as data, not as a YAML string assembled by concatenation.
Build dictionaries and lists, then let a YAML serializer handle indentation,
quotes, Unicode and multiline text. Template names and property names are exactly
the same as in the complete YAML deck above.

This runnable Python example generates a title, a section divider, one content
slide per topic, an image/text slide, a comparison and a closing quote. It needs
PyYAML (`python -m pip install PyYAML`), already included in the app requirements.
Run it in any directory where you want the output files created.

```python
import json
from pathlib import Path
import yaml


def make_content_slide(title, points):
    # points are Markdown fragments; keep each slide short enough to fit.
    return {
        "type": "content",
        "title": title,
        "markdown": "\n".join("- " + point for point in points),
    }


topics = [
    {"title": "What we learned", "points": ["Clear goals help.", "**Evidence** matters."]},
    {"title": "What comes next", "points": ["Test the idea.", "Share the results."]},
]

deck = {
    "metadata": {
        "title": "Generated project review",
        "author": "Your team",
        "language": "en",
    },
    "theme": {
        "font_name": "Lato",
        "primary_color": "#16745C",
        "body_size": 20,
        "footer_text": "Project review",
    },
    "slides": [
        {"type": "title", "title": "Project review", "subtitle": "From data to decisions"},
        {"type": "section", "title": "Our findings", "subtitle": "Two useful lessons"},
        *[make_content_slide(topic["title"], topic["points"]) for topic in topics],
        {
            "type": "image_left_content",
            "title": "A closer look",
            "image": "blue-light-mesh.png",
            "image_fit": "cover",
            "image_alignment": "center",
            "markdown": "## The takeaway\n\nA clear image supports a **clear message**.",
        },
        {
            "type": "two_columns",
            "title": "Compare options",
            "left_markdown": "## Option A\n\n- Start small\n- Learn quickly",
            "right_markdown": "## Option B\n\n- Broader scope\n- More preparation",
            "right_markdown_font_size": 18,
        },
        {"type": "quote", "title": "Takeaway", "quote": "Ask a **better question**.",
         "attribution": "Your team"},
    ],
}

Path("generated.yaml").write_text(
    yaml.safe_dump(deck, sort_keys=False, allow_unicode=True), encoding="utf-8"
)
Path("generated.json").write_text(
    json.dumps(deck, indent=2, ensure_ascii=False), encoding="utf-8"
)
```

Import `generated.yaml` through the editor. The serializer may choose quoted
multiline strings instead of `|` blocks; both represent the same text and import
correctly. `sort_keys=False` keeps your chosen field order for readability, while
slide order is always determined by the `slides` list.

For generated content, use this contract:

- Return one object containing `slides`, optionally `theme` and `metadata`.
- Use only supported template `type` values and the fields documented below.
- Use strings for content, filenames and metadata; numbers for sizes/spacing/
  transparency. Do not emit `null` for inherited properties: omit those keys.
- Keep metadata separate from visible title-slide content.
- Supply image files separately; creating a filename reference does not upload it.
- Treat inserted text as Markdown only in rich-text fields. Escape Markdown
  punctuation when source data should appear literally.
- Validate the structure and inspect rendered slides. Schema validation cannot
  determine whether a long paragraph fits its panel or an image crops well.

### Validate And Export From Python

When running from the Slidezz repository with its requirements installed, use the
same validator and PPTX generator as the app. This example reads the generated
YAML, validates it, and exports native editable PowerPoint objects without starting
a web server. It writes `generated.pptx` in the current directory.

```python
from pathlib import Path
import yaml
from backend.app import validate
from backend.services.pptx_generator import generate

deck = validate(yaml.safe_load(Path("generated.yaml").read_text(encoding="utf-8")))
generate(deck, Path("generated.pptx"), images_dir=Path("images"))
```

`validate` returns the normalized deck with theme defaults filled in and raises
`ValueError` for unsupported layouts or invalid field values. For untrusted YAML,
prefer the app's import endpoint/UI, which also enforces its YAML-specific input
checks; `yaml.safe_load` alone is not a substitute for those checks.

For portable HTML, use the generated **JSON** file with the existing builder:

```sh
python tools/build_static.py --presentation generated.json --output dist/generated-editor.html
python tools/build_static.py --presentation generated.json --presentation-only --output dist/generated-viewer.html
```

The builder resolves referenced images from the repository's `images/` gallery.
Put assets there before building, or import them through the app and export a
bundle from the editor. The regular HTML bundle can be edited offline; the viewer
bundle is read-only. For an automated or AI authoring pipeline, use the field
reference below as the output contract, then validate and preview before delivery.

## Slide Building Blocks

`type` is required and must be one of the names below. Other content fields are
optional strings. Missing text/image content becomes empty, not the sample text
shown when adding a new slide through the GUI. Quote number-like values and dates
when they are text. Each content string is limited to 20,000 characters.

| Type | Content fields | Structure |
| --- | --- | --- |
| `title` | `title`, `subtitle`, `author`, `institution`, `date` | Large title/subtitle, with three detail lines below. |
| `content` | `title`, `markdown` | Heading above one full-width rich-text panel. |
| `image` | `title`, `image` | Heading above one large image pane, with no text column. |
| `image_left_content` | `title`, `image`, `markdown` | Image left, rich text right. |
| `content_left_image` | `title`, `markdown`, `image` | Rich text left, image right. |
| `double_image_content` | `title`, `left_image`, `right_image`, `markdown` | Two images with a short full-width caption underneath. |
| `two_columns` | `title`, `left_markdown`, `right_markdown` | Two independent rich-text columns. |
| `quote` | `title`, `quote`, `attribution` | Large rich-text quote and attribution below. |
| `section` | `title`, `subtitle` | Large central heading/subheading for a section break. |

`markdown`, `left_markdown`, `right_markdown` and `quote` are rich-text fields.
All other text content fields are plain text. The following shared settings apply
to all layouts.

### Backgrounds And Panels

Every slide accepts `background_image`, `background_panel_color` and
`background_panel_transparency`. This complete example demonstrates overrides:

```yaml
theme:
  background_panel_color: "#FFFFFF"
  background_panel_transparency: 50
slides:
  - type: content
    title: A readable message over an image
    background_image: smoke-blue-blush.png
    background_panel_color: "#FFFFFF"
    background_panel_transparency: 25
    markdown: |
      Less transparency makes the panel more opaque.
```

The panel appears only over an available background image. Its color and
transparency inherit the theme unless explicitly specified on the slide.
Transparency is a number from 0 (opaque) to 100 (fully transparent), default 50.
Text and image panes remain opaque. `background_color` is the theme's slide color,
not a per-slide field. Background images fill the slide; they do not have the
independent fit/alignment controls used by image panes.

### Image Panes

For each pane image field, append `_fit` and `_alignment` to its name:

| Image field | Fit property | Alignment property |
| --- | --- | --- |
| `image` | `image_fit` | `image_alignment` |
| `left_image` | `left_image_fit` | `left_image_alignment` |
| `right_image` | `right_image_fit` | `right_image_alignment` |

Fit is `contain` (show the whole image, default) or `cover` (crop to fill the pane).
Alignment is one of these nine strings, default `center`:

| Top row | Middle row | Bottom row |
| --- | --- | --- |
| `top_left` | `left` | `bottom_left` |
| `top` | `center` | `bottom` |
| `top_right` | `right` | `bottom_right` |

For contain, alignment positions the image in unused space. For cover, it chooses
which part remains visible after cropping. Controls work independently per pane.

Use a gallery **filename**, not an HTTP URL, an absolute path or an `images/` prefix.
Image bytes are not embedded in YAML. In the Python app, upload PNG/JPEG/WebP through
an image field's gallery, then use its stored filename. Offline, add images through
a ZIP import. Download **ZIP with images** to transfer everything together.
Unavailable pane images show `Image <name> not found`; unavailable backgrounds
produce a warning rather than stopping the presentation. Older `blue.jpg` and
`smoke.jpg` references map to their replacement assets.

### Typography Overrides

Every plain-text or rich-text panel has these optional font properties:
`<field>_font_name`, `<field>_font_size`, and `<field>_font_color`.
For example, `title_font_size` changes only that slide's title, not other titles.

| Layout | Fields that support all three typography properties |
| --- | --- |
| `title` | `title`, `subtitle`, `author`, `institution`, `date` |
| `content` | `title`, `markdown` |
| `image` | `title` |
| `image_left_content` | `title`, `markdown` |
| `content_left_image` | `title`, `markdown` |
| `double_image_content` | `title`, `markdown` |
| `two_columns` | `title`, `left_markdown`, `right_markdown` |
| `quote` | `title`, `quote`, `attribution` |
| `section` | `title`, `subtitle` |

Font names are nonempty strings of at most 200 characters, sizes are numeric
8-96 points (fractional sizes are allowed), and colors are quoted `"#RRGGBB"` values.
Omit a property to inherit; do not use `null` or `"Use theme"`. In the GUI,
re-enabling **Use theme** removes the corresponding override.

```yaml
theme:
  font_name: Lato
  primary_color: "#16745C"
  body_size: 20
slides:
  - type: two_columns
    title: One slide, two voices
    title_font_name: Barlow
    title_font_size: 34
    title_font_color: "#16745C"
    left_markdown: |
      **The main point**, in the theme font.
    right_markdown: |
      A smaller supporting observation.
    right_markdown_font_name: PT Serif
    right_markdown_font_size: 17.5
    right_markdown_font_color: "#263631"
```

Inherited sizes scale the template's baseline sizes, rather than making all boxes
identical. With default theme sizes, title/section large titles are 44 pt and their
subtitles 24 pt; other slide titles are 30 pt, normal body panels 20 pt, quote text
32 pt, attribution 18 pt, and title-slide detail lines 16 pt. Markdown headings
also receive heading styling. Keep enough space for their larger type.

Additional panel controls are `<field>_font_style` (`regular`, `bold`, `italic`,
`bold_italic`), `<field>_alignment` (`left`, `center`, `right`, `justify`) and
`<field>_vertical_alignment` (`top`, `middle`, `bottom`). Omit them to inherit
`font_style`, `text_alignment` and `text_vertical_alignment` from the theme.
Alignment positions text within its existing panel; it does not move the panel's
coordinates. Image pane positioning remains controlled by image alignment.
Markdown emphasis is retained in addition to the panel's selected font style.

Every slide accepts `notes`, a plain-text string of up to 20,000 characters.
Edit it in the collapsed **Speaker notes** group. Notes are not drawn on slides;
PPTX exports put them in PowerPoint speaker notes. JSON/YAML and HTML/ZIP retain
them as data, so do not treat them as confidential when sharing a bundle.

## Theme Reference

The complete deck above demonstrates every supported theme property. Omitted
properties use these defaults. Lengths are inches on a 13.333333 x 7.5 inch slide;
font sizes are points. Numeric ranges include their endpoints.

| Property | Default | Accepted values / effect |
| --- | --- | --- |
| `font_name` | `Aptos` | Font family string, at most 200 characters. |
| `font_style` | `regular` | `regular`, `bold`, `italic`, `bold_italic`. |
| `text_alignment` | `left` | `left`, `center`, `right`, `justify`. |
| `text_vertical_alignment` | `top` | `top`, `middle`, `bottom`. |
| `footer_font_name` | `""` | Empty inherits the theme font; otherwise font family, at most 200 characters. |
| `footer_font_size` | `10` | 6-32 pt; adjusts footer box height. |
| `footer_font_style` | `regular` | `regular`, `bold`, `italic`, `bold_italic`. |
| `footer_alignment` | `left` | `left`, `center`, `right`, `justify`, within footer/page-number boxes. |
| `default_background_image` | `""` | Gallery filename copied onto newly added slides; at most 200 characters. Does not retroactively change slides. |
| `primary_color` | `"#16745C"` | Accent, titles and Markdown headings. |
| `background_color` | `"#FFFFFF"` | Solid slide background. |
| `text_color` | `"#263631"` | Body and detail text. |
| `footer_color` | `"#263631"` | Footer and page-number text. |
| `footer_text` | `""` | Footer string, at most 200 characters. |
| `background_panel_color` | `"#FFFFFF"` | Overlay panel fill over background images. |
| `background_panel_transparency` | `50` | 0-100 percent transparency. |
| `title_size` | `30` | 18-48 pt; scales title boxes. |
| `subtitle_size` | `18` | 12-32 pt; scales subtitle boxes. |
| `body_size` | `20` | 12-32 pt; scales other text boxes. |
| `margin_left` | `0.65` | 0.1-1.5 in. |
| `margin_right` | `0.633333` | 0.1-1.5 in. |
| `margin_top` | `0.45` | 0.1-1.5 in. |
| `margin_bottom` | `0.95` | 0.6-1.5 in. |
| `column_gap` | `0.65` | 0-2 in; shared gutter for side-by-side panels. |
| `panel_padding` | `0.25` | 0-0.5 in; background overlay extends beyond content. |
| `footer_margin_bottom` | `0.2` | 0.1-1.5 in; moves the footer upward as it increases. Content area shrinks when needed to avoid overlap. |

All color properties use six-digit hexadecimal strings. Quote them: an unquoted
`#` starts a YAML comment. Per-panel overrides take precedence over shared theme
typography; per-slide overlay overrides take precedence over theme overlay settings.
There are no per-slide margin/gap overrides or arbitrary layout coordinates.

Bundled free families are **Lato**, **Fira Sans**, **PT Sans**, **PT Serif**,
**Barlow** and **IBM Plex Mono**, including bold and italic variants.
Other font names require the font to be installed where the deck is viewed.
For PPTX, install the selected fonts on the recipient computer: fonts are not
embedded in PowerPoint files. Use the app's **Download fonts (TTF)** action.
Editor light/dark appearance and English/Czech localization are browser preferences,
not presentation theme fields, and do not alter exported slide styling.

The Theme tab also offers six coordinated presets: Blue Horizon, Sage Studio,
Ink Network (dark), Rose Editorial, Sky Notes and Ribbon Report. Select one and
press **Apply preset**. Shared fonts, font sizes and colors update; footer text and
custom spacing are retained. **Replace existing slide backgrounds** copies the
preset background to every existing slide (enabled by default). **Reset slide
typography and panel overrides** removes local overrides so those slides fully
inherit the new style (disabled by default). Image panes and slide content remain
unchanged. New slides receive the chosen `default_background_image`, even after
reload or import. Clearing this default affects future slides only.

Background filenames are copied onto slides, not live-linked to this default:
editing an individual slide background remains independent. The default reference
is included in portable image bundles, and standalone editors include the six
preset backgrounds so all presets work offline. Preset names are UI choices;
YAML stores the actual theme values and slide filenames, not a preset identifier.

## Presentation Metadata

The optional `metadata` object describes the whole document, not a slide:

| Property | Meaning |
| --- | --- |
| `title` | Top-bar name and browser document title. |
| `author` | Document author. |
| `subject` | Document subject. |
| `description` | Document summary; exported to PPTX comments. |
| `keywords` | Search terms as one string, not a YAML list. |
| `category` | Document category. |
| `language` | Document language string, such as `en` or `cs`; does not translate text. |

Each standard metadata value is a string of at most 255 characters. Forbidden
control characters are rejected. These properties survive JSON/YAML, ZIP and HTML
exports and populate PPTX document properties. Custom metadata keys are preserved
but are not editable in the standard form or written to standard PPTX properties.
Missing metadata leaves the editor title as **Untitled presentation**. Metadata
`author` and `title` do not automatically fill a title slide's `author` or `title`.

## Markdown And YAML Text

Use `|` for multiline rich text; indent every line under the field. Blank lines
separate paragraphs. `|-` also works, removing the final newline. Avoid `>` for
Markdown when folding line breaks would change lists or code blocks.

```yaml
slides:
  - type: content
    title: Rich text example
    markdown: |
      ## A heading

      **Bold**, *italic*, and `inline code`.

      - First point
      - [Read more](https://example.com)

      1. First step
      2. Next step

      > A short quotation.
```

Supported content includes paragraphs, headings, bold, italic, links, bullet and
numbered lists, block quotes, inline code and fenced code blocks. Preview and PPTX
can wrap differently; a Markdown feature is not a new slide layout. Raw HTML is
shown as text, unsafe link schemes are removed, and Markdown image syntax produces
a notice: use the template's gallery image fields instead. Do not rely on tables,
embedded HTML or external images for portable slide composition.

Use spaces, not tabs, for YAML indentation. Quote plain strings such as `"yes"`,
`"2026-10-14"` or `"123"` when the YAML parser could interpret them as another type.
Use string mapping keys and JSON-compatible values. Custom YAML tags, date values
and recursive aliases are rejected. An explicit `null` does not mean inheritance.
Unknown properties are not new building blocks; use the schema names in this guide.

## Reuse And Share

To reuse a style, export **Theme > Export theme JSON** and place that object's keys
under another deck's `theme` mapping. To reuse a slide, copy its entire YAML list
item, including any explicit overrides. Reorder list items to change slide order.

JSON/YAML carries structure only. A ZIP download includes `presentation.json`,
referenced `images/`, a link/missing-image manifest and the offline `index.html`.
Prefer an app-exported ZIP to hand-building an archive. Import ZIP in either app
version to restore images and structure together. Standalone HTML embeds the deck,
images, fonts and editor; presentation-only HTML includes navigation without editing.
For an editor bundle, `?mode=presentation` displays its embedded deck read-only,
not any later edits saved in browser storage.

In the Python app, wait for **Saved** before closing; its current deck is stored
in `storage/presentations/current.json`. Offline changes stay in browser storage.
Always export a portable copy before moving computers or clearing browser data.
Importing YAML is supported by the UI; the static builder's `--presentation` flag
currently reads JSON, so export JSON first when using that command-line tool.

To add a genuinely new building block, register a template in Python, rather than
inventing a YAML `type`. See [Add A Template](README.md#add-a-template).
