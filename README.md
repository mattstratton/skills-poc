# skills-poc

Marketplace and plugin repository for Claude skills. Currently houses Matty's personal
TigerData content and marketing skills. Also serves as a pattern reference for the
team-wide marketing skills plugin (coming later).

## Repository layout

```
.claude-plugin/
  marketplace.json          ← marketplace registry (lists all plugins)

plugins/
  matty-tiger-skills/
    .claude-plugin/
      plugin.json           ← plugin metadata and version
    config.json             ← runtime config (Drive folder ID, Asana project ID, etc.)
    REFERENCES.md           ← how to fetch reference docs from Google Drive
    DRIVE-DOCS-NEEDED.md    ← documents which Drive docs must exist for skills to work
    skills/
      brand-voice-writer/   ← write marketing content in TigerData's brand voice
      weekly-content/       ← generate weekly content roundup Slack posts
      linkedin-articles/    ← find articles and draft LinkedIn posts
```

## How it works

Skills are thin orchestration files. They define *what to do* and *which tools to call*,
but confidential context (brand voice details, sales frameworks, competitive positioning,
voice profiles) lives in Google Drive reference docs — not in this repo.

Each skill declares its references in frontmatter. At runtime, the skill reads
`REFERENCES.md` to learn how to fetch those docs from the shared Drive folder. This
keeps the repo public-safe while giving skills full context when they run.

### Reference doc paths

References can be simple names (`brand-voice-guide`) for docs at the root of the Drive
folder, or paths with subfolders (`matty/topic-buckets`) for user-specific docs. See
`REFERENCES.md` for the full fetch protocol.

### Config values

`config.json` stores non-secret runtime identifiers (Asana project IDs, Slack user IDs,
the Drive folder ID). These are access-controlled by their respective services and are
safe to store in a public repo.

## Current plugin

**matty-tiger-skills** (v2.0.0)

Skills:
- **brand-voice-writer** — writes marketing content using TigerData brand voice docs
- **weekly-content** — generates weekly #general and #sales-team Slack posts from the Asana content calendar
- **linkedin-articles** — finds ICP-relevant articles and drafts LinkedIn posts with voice profiles

## Setting up

1. Ensure the Google Drive connector is enabled (Cowork) or `gdrive` CLI is installed (Claude Code)
2. Ensure the reference docs exist in the shared Drive folder (see `DRIVE-DOCS-NEEDED.md`)
3. Ensure the Asana, Tiger Den, and Slack connectors are available for skills that need them

## Adding skills

1. Create a new folder under `plugins/matty-tiger-skills/skills/`
2. Add a `SKILL.md` with frontmatter (name, description, references)
3. If the skill needs new reference docs, add them to Drive and document in `DRIVE-DOCS-NEEDED.md`
4. If the skill needs new config values, add them to `config.json`
5. Bump the version in `plugin.json`
