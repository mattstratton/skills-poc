# Google Drive Reference Docs to Create

This file documents the reference docs that need to exist in the shared Google Drive folder
for skills to work. Create these as Google Docs in the Drive folder specified by
`config.json` → `references_folder_id`.

## Root-level docs (shared across skills)

These already exist for the brand-voice-writer skill:

- `brand-voice-guide` — tone, style rules, writing principles
- `terms-glossary` — product names, capitalization, approved terminology
- `icp-audience` — ideal customer profiles, personas, pain points
- `positioning` — value propositions, differentiators, competitive context
- `marketing-strategy` — high-level goals, key messages, campaign themes
- `educational-content-guide` — guidance for educational content
- `white-paper-guide` — guidance for white papers

### New root-level doc needed:

**`sales-stage-framework`** — Used by: `weekly-content`

Contents to include:
- Stage 0 (Discovery): customer question, goal of first call, content role, good fit
  content types, persona fit, relevant BDR paths
- Stage 1 (Evaluation): same structure — what customers ask, call goal, content role,
  good fit, persona fit
- Stage 2 (Tech Validation): same structure
- Stage 3 (Commercials): same structure
- BDR Path Reference: Path A (all-in Postgres, no bottlenecks yet), Path B (scaling
  managed Postgres), Path C (added second system), Path D (added supporting systems)
- For each path: the framing angle and what kind of content resonates

Source material: the "Stage Reference" section from the original weekly-content skill
(the full text was in the uploaded SKILL.md, lines 176-219).

---

## `matty/` subfolder docs

Create a subfolder called `matty` inside the shared references folder.

**`matty/topic-buckets`** — Used by: `linkedin-articles`

Contents to include:
- Bucket 1 (IoT / Industrial Time-Series): search topics, what qualifies, examples
- Bucket 2 (Postgres / Database Ecosystem): search topics, what qualifies, examples
- Bucket 3 (ClickHouse / MongoDB Competitive): search topics, competitive framing,
  what kind of articles to look for
- For each bucket: the search guidance and quality bar

Source material: the "Step 2 — Search for Articles" bucket definitions from the original
linkedin-articles skill (the uploaded SKILL.md, lines 57-86).

**`matty/fallback-voice-matty`** — Used by: `linkedin-articles` (fallback only)

Contents to include:
- Matty's voice description: background (Head of DevRel, former DevOps, Arrested DevOps
  podcast), writing style (direct, no fluff, no corporate speak, strong opinions earned
  not performed, comfortable calling things broken)
- TigerData product context: what TimescaleDB is, what Tiger Cloud is, the core narrative
- Competitive positioning notes for ClickHouse and MongoDB

Source material: the "Fallback Voice Profile" section from the original linkedin-articles
skill (the uploaded SKILL.md, lines 192-208).

---

## Checklist

- [ ] `sales-stage-framework` created at root level
- [ ] `matty` subfolder created
- [ ] `matty/topic-buckets` created in subfolder
- [ ] `matty/fallback-voice-matty` created in subfolder
- [ ] Verify existing root docs still exist: brand-voice-guide, terms-glossary,
      icp-audience, positioning, marketing-strategy
