# skills-poc

Plugin repository for Matty's personal Claude skills at TigerData. Houses the
`matty-tiger-skills` plugin — a set of Cowork skills for morning briefings, content
production, meeting prep, and daily workflows. Also serves as a pattern reference for the
team-wide marketing skills plugin.

## Repository layout

```
plugins/
  matty-tiger-skills/
    .claude-plugin/
      plugin.json           ← plugin metadata and version
    config.json             ← runtime config (Asana project IDs, Slack IDs, etc.)
    REFERENCES.md           ← how skills fetch reference docs from Tiger Den
    skills/
      context-loader/       ← memory layer: loads personal context from Obsidian
      morning-update/       ← daily briefing: Asana sync, Slack scan, calendar, deadlines
      meeting-notes/        ← create pre-populated meeting notes in Obsidian from calendar
      design-requests/      ← automate blog thumbnail design requests in Asana
      weekly-content/       ← generate weekly content roundup Slack posts
      linkedin-articles/    ← find articles and draft LinkedIn posts
references/
  claude-cowork/            ← archived: original productivity plugin memory (migrated to Obsidian)
```

## Architecture

Skills are orchestration files that define workflows and which MCP tools to call.
Confidential context lives outside this repo in three places:

### Tiger Den (marketing references)
Brand voice, ICP profiles, terminology glossary, and other marketing references live in
Tiger Den and are fetched at runtime via MCP. Skills declare which references they need in
their frontmatter. See `REFERENCES.md` for the fetch protocol.

### Obsidian (personal memory layer)
The persistent memory layer lives in Obsidian at `00 - System/Claude Context.md`. This note
contains Matty's role, team, key people, shorthand/terms, active projects, tools, and
preferences. It's read at the start of every session (via `context-loader` or inlined in
`morning-update`) so Claude "knows" the working context regardless of which folder is
selected in Cowork.

The memory note is maintained manually or via the context-loader skill's update mode. When
Claude learns something new in a session (new team member, new acronym, project change), it
can offer to update the note.

Obsidian also provides:
- People directory (`05 - People/`) — attendee resolution, meeting history via Dataview
- Meeting notes (`04 - Meetings/`) — pre-populated by the meeting-notes skill
- Vault system rules (`CLAUDE.md` at vault root) — formatting, folder structure, guardrails
- Content tasks (`03 - Areas/Content Production.md`) — synced from Asana by morning-update

### Config values
`config.json` stores non-secret runtime identifiers (Asana project IDs, Slack user IDs,
channel names). These are access-controlled by their respective services and safe to store
in a public repo.

## Current plugin

**matty-tiger-skills** (v2.7.0)

Skills:

- **context-loader** — loads personal context from Obsidian; also handles updates to the memory note. Run with `/context` or loaded automatically by morning-update.
- **morning-update** — daily briefing: syncs Asana tasks to Obsidian, scans Slack for action items, briefs on calendar and deadlines. Offers to create meeting notes afterward.
- **meeting-notes** — pulls today's calendar, resolves attendees against Obsidian People directory, creates pre-populated meeting notes with context.
- **design-requests** — searches the Content Calendar for blog posts, creates formatted design request tasks in Asana's Marketing Design Requests project.
- **weekly-content** — generates weekly #general and #sales-team Slack posts from published content in Tiger Den.
- **linkedin-articles** — finds ICP-relevant articles and drafts LinkedIn posts using Tiger Den voice profiles.

## Installation

The plugin can disappear from Claude Code after restarts due to the
`RemotePluginManager` wipe cycle. To install it persistently into the local
plugin cache:

```bash
git clone https://github.com/mattstratton/skills-poc.git
python3 skills-poc/scripts/install.py
```

If you already have the repo cloned, just run the script directly:

```bash
python3 scripts/install.py
```

This copies the plugin into `~/.claude/plugins/cache/`, registers it in
`installed_plugins.json`, and creates an install manifest so it survives
restarts. **Restart Claude Code after running.**

Re-run the script any time you pull a new version to update the cache.

## Connectors required

- **Obsidian** — memory layer, meeting notes, task sync, People directory
- **Asana** — task management, content calendar, design requests
- **Slack** — message scanning, post delivery, search
- **Google Calendar** — daily schedule, meeting notes
- **Tiger Den** — marketing references, content library, voice profiles, UTM links
- **Gmail** — used by some workflows (not all skills need it)

## Adding skills

1. Create a new folder under `plugins/matty-tiger-skills/skills/`
2. Add a `SKILL.md` with frontmatter (name, description, references)
3. If the skill needs Tiger Den references, declare slugs in frontmatter (see `REFERENCES.md`)
4. If the skill needs new config values, add them to `config.json`
5. If the skill reads/writes Obsidian, document which notes it touches
6. Bump the version in `plugin.json`
