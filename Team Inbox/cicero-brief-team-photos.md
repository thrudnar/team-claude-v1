# Brief for Cicero — Team Photos: Midjourney Prompts

**From:** Adama
**Project:** Team Photos
**Your deliverable:** A single prompt file for all 8 team members, delivered to Owner's Inbox

---

## What I Need

Convert Prospero's visual descriptions (see `prospero-team-photos-descriptions.md` in Team Inbox) into Midjourney prompts that will produce a cohesive set of portrait images for the team roster UI.

## Style Requirements

- **Aesthetic:** 1960s spy dossier — candid black and white surveillance photography
- **Use case:** Close-up portrait thumbnails in a roster UI
- **Consistency:** All images must read as the same dossier, same era, same "photographer"
- **Variation:** Each image should feel distinct — different framing, angles, lighting conditions — as specified in Prospero's descriptions
- **No color.** Not desaturated. Shot in black and white.

## Structural Requirements

1. **Reusable style block at the top of the file.** This is the portion that can be swapped to regenerate all images in a new style. Separate it clearly from the subject-specific content.
2. **One complete, ready-to-paste Midjourney prompt per team member.** Each prompt = style block + subject description integrated.
3. **No Midjourney model version pinned.** Owner will select the version at execution time.
4. **Aspect ratio:** `--ar 2:3` — portrait orientation for thumbnails.

## How to Handle Style Reusability

Design the prompts so the style is modular. The clearest approach: define the style prefix as a labelled block at the top of the file, then write each prompt as `[STYLE PREFIX] + [subject specifics]`. This way swapping the style means replacing one block, not editing 8 prompts.

## Deliverable

`Owner's Inbox/team-photos-prompts.txt`

Structure:
- Style template block (labelled, clearly separated)
- 8 prompts, one per team member, with member name as header
- Brief note per prompt explaining any subject-specific choices

---

*Full project brief at `Projects/Team Photos/brief.md`.*
