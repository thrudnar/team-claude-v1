# Brief for Muybridge — Face-Crop Thumbnail Pipeline

**From:** Adama
**Project:** Team Photos

---

## Assignment

Build an automated Python script that generates `256×256px` square WebP thumbnails from team member portrait images. The thumbnails will be used as avatar/profile pictures in the roster UI.

## Input

Source portraits live at:
```
Projects/Team Photos/themes/<theme>/
  adama.webp
  prospero.webp
  ocean.webp
  thoth.webp
  iris.webp
  argus.webp
  mycroft.webp
  cicero.webp
  placeholder.webp
```

Current active theme: `dossier`. The pipeline should be theme-agnostic — it should work by pointing at any theme directory.

Images are `2:3` portrait ratio. They are 1960s-style B&W surveillance photography — high grain, high contrast, some are profile shots, some have dramatic upward or low-key lighting. Face detection must handle these conditions robustly.

## Output

```
Projects/Team Photos/themes/<theme>/thumbnails/<name>.webp
```

- `256×256px` square
- WebP format
- Named identically to the source file (e.g. `adama.webp` → `thumbnails/adama.webp`)
- `thumbnails/` directory created if it doesn't exist

## Face Crop Behaviour

- Detect the face in the source image
- Crop tightly around the face with some padding (padding should be a tunable parameter, suggested default: 40% of face bounding box on each side)
- Centre the face in the square output
- **If no face is detected** (e.g. `placeholder.webp`): fall back to a centred crop of the full image — do not fail or skip

## Script Location

```
Projects/Team Photos/generate_thumbnails.py
```

## Requirements

- Command-line invocable: `python generate_thumbnails.py --theme dossier`
- Logs each file processed: success (with crop coordinates), fallback used, or failure
- Never crashes the batch on a single bad file — log and continue
- Dry-run mode: `--dry-run` prints what would be done without writing files
- Dependencies should be standard: `Pillow`, `opencv-python` or `mediapipe` — whichever gives the most robust results on this image set

## Suggested Approach

Given the challenging nature of the inputs (profile shots, heavy grain, dramatic lighting), prefer a DNN-based or MediaPipe face detector over Haar cascades. Haar cascades will miss profile-facing subjects like Prospero and Iris.

## When Done

- Run the pipeline against the `dossier` theme
- Confirm all 9 images (8 members + placeholder) processed correctly in your report to Adama
- Flag any thumbnails that may need a manual review

---

*Read `Projects/Team Photos/brief.md` for full project context.*
*Read `Team/muybridge.md` for your profile and role.*
