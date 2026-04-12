# Brief Request for Prospero — Image Processing Specialist

**From:** Adama
**Pipeline ID:** 9

## What We Need

We need to hire an Image Processing Specialist. Their first assignment is to build a fully automated pipeline that:

1. Takes a source portrait image (`.webp`, `2:3` aspect ratio) for each team member
2. Detects the face automatically
3. Crops tightly around the face
4. Outputs a `256×256px` square thumbnail (`.webp`)

The thumbnails will be used as profile picture avatars in the team roster UI. The pipeline needs to handle challenging inputs — profile shots, dramatic lighting, heavy film grain (our current image set is styled as 1960s B&W surveillance photography).

This role will also grow into the v2 scope of fully automated image generation via external API (Flux or DALL-E 3), so broader image pipeline thinking is a plus.

## Please Research and Deliver

A Candidate Brief covering:
1. Role title and summary
2. Core knowledge domains
3. Key skills and tools
4. Ways of working / professional traits
5. What distinguishes genuine expertise from surface knowledge
6. Suggested name and persona fit (for Ocean to consider)

Deliver to `Team Inbox/` as `prospero-candidate-brief-image-specialist.md` and update the DB:
```sql
UPDATE hiring_pipeline SET brief_file = 'prospero-candidate-brief-image-specialist.md' WHERE id = 9;
```
