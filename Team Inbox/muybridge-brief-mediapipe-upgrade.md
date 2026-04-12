# Brief: Upgrade Face Detection to MediaPipe

**To:** Muybridge
**From:** Adama
**Date:** 2026-04-01
**Re:** Replace Haar cascade detection with MediaPipe in `generate_thumbnails.py`

---

## Background

The current thumbnail pipeline uses OpenCV Haar cascades for face detection. This is producing a high false-positive rate on the dossier theme images — six of ten team members currently require manual `overrides.json` entries to get a correct crop. The latest failure was Iain: a false positive in the mid-body region scored larger than the actual face and won the "largest bbox" selection.

Haar cascades were designed for photographs. The dossier images are illustrated, high-contrast, graphic portraits — a style that reliably generates false positives on clothing and background texture.

---

## Task

Upgrade `Projects/Team Photos/generate_thumbnails.py` to use **MediaPipe Face Detection** as the primary detection method, with Haar cascades retained as a fallback.

**Specifics:**

1. Use `mediapipe.solutions.face_detection` (short-range model, `model_selection=0`) as the primary detector. It returns normalised bounding boxes — convert to pixel coordinates.

2. If MediaPipe returns no face, fall back to the existing Haar cascade logic (do not remove it — it's the safety net).

3. The `overrides.json` mechanism stays and continues to take highest priority — it overrides both MediaPipe and Haar results.

4. Log clearly which method was used for each image: `face-crop (mediapipe)`, `face-crop (haar fallback)`, `face-crop (manual override)`, or `centre-crop (no face detected)`.

5. Add `mediapipe` to the `Dependencies` section of the module docstring.

6. Test by running the full dossier theme with `--dry-run` first to inspect crop coordinates without writing files, then run for real and visually inspect every output thumbnail before reporting done.

7. Existing `overrides.json` entries for the current six members should still produce identical results (the override path is unchanged). Verify this.

---

## Success Criteria

- All existing thumbnails that currently require overrides continue to produce correct crops
- New hires processed without overrides should have the face correctly centred in the majority of cases (target: no false positives on the current dossier set)
- Iain's thumbnail (now fixed via override) should also be verified as correct after the upgrade

---

## Dependency

```
pip install mediapipe
```

Confirm it's available in the team's Python environment before proceeding. If not, note the install step in the script's docstring.

---

## Output

Updated `Projects/Team Photos/generate_thumbnails.py`. Report back with:
- Confirmation that all current thumbnails look correct after the upgrade run
- Any members who still needed overrides (or where the override was adjusted)
- Whether MediaPipe is reliably detecting faces without overrides for the existing set
