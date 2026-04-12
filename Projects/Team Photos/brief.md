# Project Brief: Team Photos

## Objective
Maintain a portrait image for every team member, used as thumbnails in the team roster UI. Images are generated via Midjourney by the owner and organised by theme.

## Directory Structure

```
Projects/Team Photos/
  brief.md
  themes/
    <theme-name>/
      prompts.txt        ← style template + placeholder prompt + one prompt per member
      placeholder.webp   ← used for new members until their image is generated
      adama.webp
      prospero.webp
      ... (one file per team member, named <name>.webp)
```

## Active Themes
- **dossier** — 1960s spy movie dossier; candid B&W surveillance photographs

## Adding a New Theme
1. Create `themes/<theme-name>/`
2. Commission Prospero to write visual descriptions for every current team member in the new theme's style
3. Commission Cicero to produce a `prompts.txt` for the new theme (style template + placeholder prompt + all member prompts)
4. Generate a `placeholder.webp` for the new theme
5. Add entries to `Owner's Inbox/pending-photos.md` for all members in the new theme

## Onboarding Integration
When a new team member is hired, **Step 5 of the Hiring Process** handles photos automatically:
- Prospero writes a description for the new member in each active theme's style
- Cicero appends a prompt to each theme's `prompts.txt`
- An entry is added to `Owner's Inbox/pending-photos.md` for the owner to action
- The UI falls back to `placeholder.webp` until the real image is dropped in

## Visual Diversity

The team portrait should reflect a genuinely diverse group of people. Left to defaults, image generation models — and the humans prompting them — reproduce the same demographic archetype repeatedly. This must be actively countered.

**The governing principle:** Each new member's visual description should be written with the existing team in mind. Add contrast, not repetition. Gender, age, and ethnicity should vary across the roster, not cluster.

**Prospero's responsibility:** When writing a visual description for a new member, explicitly specify gender, approximate age range, and ethnic/physical appearance. Do not leave these vague or implicit — vague inputs default to majority-demographic outputs. Review the existing team's descriptions before writing a new one and choose characteristics that add variety.

**Cicero's responsibility:** When converting Prospero's description into a Midjourney prompt, preserve the demographic specifics faithfully and carry them into the prompt language explicitly. If Prospero's description is ambiguous on any demographic dimension, flag it and request clarification rather than letting the model fill the gap with its own defaults.

**Theme is not an excuse:** A 1960s spy aesthetic can authentically include women, people of various ethnicities, and people across a wide age range. The Tinker Tailor Soldier Spy problem — a cast of middle-aged white men — was a failure of imagination in the prompt writing, not an inherent constraint of the theme.

---

## Image Conventions
- **Format:** `.webp`
- **Filename:** `<lowercase-name>.webp` (e.g. `adama.webp`)
- **Aspect ratio:** 2:3 (portrait)
- **To replace a placeholder:** Generate the image in Midjourney using the member's prompt, upscale, and save to the correct theme folder as `<name>.webp`

## Style Reusability
Each `prompts.txt` contains a labelled STYLE PREFIX block at the top. To regenerate all images in a new style: replace the style prefix, and reconstruct prompts as `[NEW STYLE PREFIX] + [subject block]`. Subject blocks remain unchanged between style updates.

## Status
**v1 — complete.**

## Future: v2
Automate image generation via an API (likely Flux or DALL-E 3) so the full pipeline runs without manual Midjourney execution.
