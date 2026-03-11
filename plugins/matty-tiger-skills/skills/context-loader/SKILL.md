---
name: context-loader
platforms: [cowork]
description: >
  Load Matty's working context from Obsidian at the start of any Claude session. This is the
  memory layer — it tells Claude who Matty is, his team, shorthand, active projects, and
  how he works. Run this automatically at the start of morning-update, or manually with
  /context when you need Claude to "know you" in any session. Also handles updating the
  context note when things change.
compatibility: >
  Requires Obsidian MCP connector. If unavailable, tell the user their context couldn't be
  loaded and offer to proceed without it.
---

# Context Loader Skill

This skill manages the persistent memory layer stored in Obsidian. It has two modes:

1. **Load** (default) — Read the context note and internalize it for the current session
2. **Update** — Modify the context note when the user tells you something has changed

---

## Mode 1: Load Context

Read `00 - System/Claude Context.md` from the Obsidian vault using `obsidian_get_file_contents`.

This note contains:
- Who Matty is, his role, reporting chain
- Direct reports and key people (with nicknames → full names)
- Shorthand and terms that aren't obvious without context
- Active projects and where they live
- Tools and systems in use
- Preferences for how Obsidian, tasks, and content are structured

After reading, **do not summarize it back to the user.** Just internalize it and proceed with
whatever they asked for. The whole point is that this is seamless — Claude just "knows" the
context without making a production of it.

### When to load

- **Always** at the start of `morning-update` (Step 0, before anything else)
- **Always** when the user runs `/context` explicitly
- **Recommended** as the first step of any skill that references people, teams, projects,
  or shorthand (meeting-notes, design-requests, weekly-content, etc.)

### If Obsidian is unavailable

Tell the user: "I couldn't load your context from Obsidian — the connector doesn't seem to
be available. I can still help, but I might not recognize shorthand or nicknames. Want to
proceed anyway?"

---

## Mode 2: Update Context

When the user says things like:
- "Update my context — Iain left the company"
- "Add [term] to my shorthand"
- "I'm now reporting to [person]"
- "New project: [name]"
- "/context update [change]"

Use `obsidian_patch_content` to modify `00 - System/Claude Context.md`.

### Update rules

1. **Read the note first** — always read the current state before patching
2. **Make surgical edits** — update only the relevant section. Use the heading path for
   targeting (e.g., `target="Claude Context::My Team (Direct Reports)"`)
3. **Preserve the structure** — keep the existing table/list format. Don't rewrite sections
   wholesale unless the user asks for a restructure.
4. **Update the `updated` frontmatter date** — patch the YAML `updated` field to today's date
5. **Confirm the change** — after patching, briefly confirm what was changed. One sentence.

### What belongs in context vs. elsewhere

| Information | Where it goes |
|------------|---------------|
| Nickname → full name mapping | Claude Context (Key People table) |
| Person's detailed profile | `05 - People/` page in Obsidian |
| Product/brand terminology | Tiger Den `terms-glossary` reference |
| Brand voice, ICP, writing style | Tiger Den marketing references |
| Asana project IDs, Slack channel IDs | Plugin `config.json` |
| Meeting history | `04 - Meetings/` in Obsidian |
| Task assignments and due dates | Asana (source of truth) |

If the user asks to store something that belongs elsewhere, tell them where it should go and
offer to put it there instead.

---

## Conversational Learning (Offer Mode)

During any session, if you learn something significant that isn't in the context note, you
can offer to add it. Examples:

- User mentions a new team member or a departure
- User uses a term/acronym you had to ask about
- A project gets renamed or a new one starts
- Reporting structure changes
- A new Slack channel becomes important

**How to offer:**

> "I noticed [thing]. Want me to add that to your context so I remember it next time?"

If the user says yes, switch to Update mode. If no, move on. Don't be pushy about it —
once per session per item is enough. And never offer during time-sensitive flows like
morning-update (save the offers for the end or for idle moments).
