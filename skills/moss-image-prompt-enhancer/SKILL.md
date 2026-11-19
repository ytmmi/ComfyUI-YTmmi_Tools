---
name: moss-image-prompt-enhancer
description: Expand an image-generation request into a detailed MOSS-Image caption or spatial layout, and compile a local JSON draft into a ready-to-paste prompt. Compatible with three prompt-writing styles (natural language for atmosphere/camera/narrative, tag strings for precise element control, and a recommended hybrid of both). Use for prompt enhancement, image composition and text placement; this skill does not generate images.
version: 1.3.4
---

# MOSS-Image Prompt Enhancer

Turn the user's idea into a concrete image description. Target GPT-6-family
agents with filesystem and shell tools. The agent makes creative decisions;
the bundled Python tool handles coordinate arithmetic and serialization.
No Echidna service, model API or third-party Python dependency is needed.

## Choose the deliverable

Honor an explicit request for a caption or Layout. **Otherwise default to Layout**
— the JSON form whose core idea is **a global description plus local boxes**:
`summary.caption` carries the global description of the whole image, and the flat
`items` array places each local unit in its own bounding box. Keeping the global
reading and the local placement decisions in one artifact matches how MOSS-Image
conditions on layout, so Layout is the default deliverable.

Upstream MOSS-Image leaves this choice to the user and falls back to a caption for
ordinary scenes, photography and illustration, reserving Layout for text placement,
posters, multi-panel compositions and controlled object relations. This repository
keeps Layout as the default on purpose: the local workflow consumes placement, so a
caption is the fallback rather than the norm. Everything else below follows upstream.

Fall back to a caption only when the user explicitly asks for a caption / plain
prose, or when the image is a single undivided unit with nothing to place relative
to anything else (a plain portrait, a texture, one object on a plain background)
and a box would add no information. The choice is about placement, not about
detail: a rich multi-element image uses Layout, and a simple image still uses
Layout whenever anything must sit in a specific spot.

Preserve the user's subjects, counts, relationships, medium, style, exclusions
and intended visible wording. Resolve ordinary creative gaps yourself; ask only
when a missing decision would materially change the requested image. Do not
invent factual event logistics or specifications as if the user supplied them.

Default to English for descriptive prose, following a requested output language
when given. Preserve visible text verbatim in its original language, including
punctuation, capitalization and requested line breaks. A quoted sentence in an
instruction is not necessarily text to render: distinguish visible wording from
reference material and constraints.

## Anime and character routing

For anime, 二次元, IP fan art, manga panels, character posters and multi-person
interaction requests, prefer the sibling skill `moss-anime-prompt-template`
(中文模板). It carries the stricter rules those requests need: style as an
independent opening sentence, per-character attribute grouping, camera and
spatial layering, lighting causality, Layout item splitting and a pre-delivery
checklist. In particular, for anime tasks the sibling skill uses an artist
string and, when the user did not name one, dynamically matches a main artist to the described style (medium / linework / shading / palette / era); it keeps no fixed style-to-artist table, but style-to-artist matching is the normal path.
Use this skill for general image ideas, caption-only work, and pixel-level
Layout drafting with `scripts/compile_prompt.py`; the two skills share the
same caption/Layout contract and can be combined, but do not restate the anime
rules here.

## Prompt-writing styles (three compatible schools)

The way the positive text is organized is independent of the deliverable form
(caption or Layout). Use whichever school fits the request:

- **Natural language** — best for atmosphere, camera movement and narrative
  feeling. Write who does what to whom, how the camera looks, where the light
  comes from and which visible action carries the mood. This is the default
  when the user does not ask for tags.
- **Tag string** — best for precise control of individual elements. The common
  community order is **Quality → Score → Meta → Year → Character → Series →
  Artist → General**; treat it as a reference order only — do not auto-add
  quality words or scores, and add a year only when it is given or verifiable.
  Artist is an expected slot for anime tasks: use a user-named artist if given,
  otherwise match one main artist to the style direction through the medium/linework/shading/palette/era slots (only mix when explicitly asked; no fixed style-to-artist table is kept);
  it goes after Series, before General. Here the usable order is optional
  specific-medium Meta → Character → Series → Artist (user-provided or
  auto-selected) → General.
- **Hybrid** — recommended most: use tags as compact anchors for identity,
  appearance and key elements ("what must be present"), then natural-language
  sentences for relations, camera, lighting and emotion ("where it goes and
  what it is doing"), without stating the same content twice; keeping each
  concern in its own block makes faulty parts easy to replace. MOSS's text
  encoder reads left to right, so put global light/color-temperature/material
  conditions before character and clothing nouns. Keep count and core state
  tags verbatim; in multi-character scenes describe the main subject first and
  explicitly contrast the second to avoid attribute bleed. Keep the style as
  an independent opening sentence and do not import other models' weight /
  `BREAK` / per-character / region syntax. For anime and 二次元 work, the
  sibling `moss-anime-prompt-template` carries the hard-rule version of these
  three styles.

## Develop the image

Describe visible choices: subject and action, relevant appearance, setting,
camera/framing, medium, lighting, materials, palette and mood. Add detail where
it makes the requested image more specific. Avoid redundant quality tags,
unrequested style changes, arbitrary word budgets and invisible process notes.
Keep an explicit minimalist brief minimalist; develop a rich brief without
turning it into a generic title/hero/footer template.
Keep explanations of JSON, bounding-box annotations and conversion steps out of
image-description fields; those are tool instructions, not depicted content.

For designed images, compose the information and imagery together. Establish
reading order, relative prominence, coherent groups and readable text at the
chosen pixels. Write the intended copy rather than placeholders such as
"headline here" or "some explanatory text". Do not import unrelated names,
watermarks or copy from a reference. Use supplied references when useful; outside
research is optional unless needed for factual accuracy or requested by the user.

## Caption

Write a UTF-8 JSON file containing exactly `{"caption":"..."}`. The caption is
cohesive prose, with spatial relations in words and any visible wording quoted
exactly. It may contain paragraphs; do not add coordinates or JSON-layout fields
to a caption just to make it look structured.

## Layout

Read [references/layout.md](references/layout.md) before writing a Layout draft.
Write readable JSON with `summary`, a flat `items` array, concrete `width` and
`height`, `bbox_coord_space="abs"` and `bbox_format="xyxy"`.

**Draft boxes use `[x_min,y_min,x_max,y_max]` in actual pixels, from the canvas
top-left.** Keep x in `0..width` and y in `0..height`. Do not use normalized
coordinates or manually center, reorder or quantize the boxes.

Honor supplied dimensions. With only an aspect ratio, choose compatible pixel
dimensions; without either, use 1024×1024 unless the requested medium suggests
another shape. MOSS-Image dimensions must be positive multiples of 16. Do not
silently change explicit dimensions that are incompatible; surface the conflict.
Use the same width and height in the image-generation workflow.

Use boxes for coherent visible units, splitting only when independent placement
matters. Grouping should preserve content and relationships, not erase them.

Item granularity, in practice:

- Split only when the parts must be placed **independently** — a title, a body block
  and a footer each become their own `text` item when their position and size are
  decided separately;
- Keep units that always move, scale or occlude **together** in one item (a character
  plus the prop they hold, a logo lockup, a caption plus its rule);
- Do not box every object for completeness: extra boxes fragment the layout and invite
  the model to draw borders around things that should read as one image;
- A `text` item carries the exact visible characters; if two strings must be typeset
  separately, they are two items rather than one string with a line break.
Natural occlusion and overlap are allowed. A box is a placement annotation,
not an instruction to draw a border, panel or sticker. Describe appearance in
captions and global treatment in `summary.caption`; let boxes agree with any
spatial descriptions. Keep exact visible strings in text items' `text` fields.

## Compile and deliver

Save the draft to a user-appropriate working directory, then run the tool bundled
beside this SKILL.md. Resolve the script path from the skill location, not the
user's working directory:

```bash
python3 /path/to/moss-image-prompt-enhancer/scripts/compile_prompt.py \
  draft.json --output prompt.txt
```

Use an actual path in the invocation. Keep the editable JSON draft and compiled
output separate. Read the result and check the subject, exact text, intended
geometry and chosen canvas before delivering. Fix validation errors in the draft
and rerun; do not bypass a failed conversion by hand-writing centered JSON.

For captions, the output is plain text. For Layout, it is one physical line of
JSON with flat `items`, integer `abs_centralized` / `yxyx` boxes and no canvas
metadata. The tool encloses fractional pixel edges before subtracting the center,
matching Echidna's generation conversion. It rejects invalid or out-of-bounds
boxes instead of silently clipping them. String newlines are escaped in the JSON
while remaining actual newlines in the decoded text.

Return the ready-to-paste prompt or a link to its file, and retain a link to the
draft when useful for editing. For Layout also state the required width×height
outside the prompt; the model prompt itself does not contain these dimensions.
If showing Layout JSON inline, use the compiled output without reformatting it.
Only the caption or compiled Layout belongs in MOSS-Image's positive prompt.
Creating these files does not submit image generation or publish anything.
