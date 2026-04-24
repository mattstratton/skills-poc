---
name: context-loader
platforms: [cowork]
description: >
  Load Matty's working context at the start of any Claude session. This is the memory layer —
  it tells Claude who Matty is, his team, shorthand, active projects, and how he works.
  Primary source is Memory Engine (me); falls back to Obsidian if unavailable. Run
  automatically at the start of morning-update, or manually with /context. Also handles
  updating context when things change.
compatibility: >
  Prefers Memory Engine (me) MCP connector. Falls back to Obsidian MCP connector. If both
  are unavailable, tell the user and offer to proceed without context.
---

# Context Loader Skill

This skill manages the persistent memory layer for Claude sessions. It has two modes:

1. **Load** (default) — Pull context from Memory Engine (or Obsidian fallback) and internalize it
2. **Update** — Modify context when the user tells you something has changed

---

## Mode 1: Load Context

### Step 1: Try Memory Engine first

Search Memory Engine for all context memories using `me_memory_search`. Make the following
calls (you can do them in parallel):

**Call 1 — identity, team, people:**
```
me_memory_search({
  semantic: "who is matty his role team direct reports key people",
  tree: "matty.context.*",
  limit: 10,
  candidateLimit: 0,
  fulltext: "",
  grep: "",
  order_by: "desc"
})
```

**Call 2 — shorthand, projects, tools, preferences:**
```
me_memory_search({
  semantic: "shorthand terms active projects tools preferences workflow",
  tree: "matty.context.*",
  limit: 10,
  candidateLimit: 0,
  fulltext: "",
  grep: "",
  order_by: "desc"
})
```

> **Known quirk:** The `me_memory_search` tool in Cowork requires ALL fields to be passed.
> Pass empty strings for unused string fields (`fulltext`, `grep`). Omit `meta`, `temporal`,
> and `weights` entirely — if the tool complains they're required, pass them as empty objects.

If both calls return results, internalize the combined content and **skip Step 2**.

### Step 2: Fall back to Obsidian

If Memory Engine is unavailable or returns no results, read the Obsidian context doc:

```
obsidian_get_file_contents("00 - System/Claude Context.md")
```

This file contains the same context in markdown format.

### If both sources are unavailable

Tell the user: "I couldn't load your context — Memory Engine and Obsidian both seem
unavailable. I can still help, but I might not recognize shorthand or nicknames. Want to
proceed anyway?"

### After loading (either source)

**Do not summarize context back to the user.** Just internalize it and proceed with whatever
they asked for. The whole point is seamless — Claude just "knows" without making a
production of it.

### When to load

- **Always** at the start of `morning-update` (Step 0, before anything else)
- **Always** when the user runs `/context` explicitly
- **Recommended** as the first step of any skill that references people, teams, projects,
  or shorthand (meeting-notes, design-requests, weekly-content, etc.)

---

## Mode 2: Update Context

When the user says things like:
- "Update my context — Iain left the company"
- "Add [term] to my shorthand"
- "I'm now reporting to [person]"
- "New project: [name]"
- "/context update [change]"

Update **both** Memory Engine and Obsidian to keep them in sync.

### Step 1: Update Memory Engine

Search for the relevant memory first to get its ID:
```
me_memory_search({ fulltext: "<topic>", tree: "matty.context.*", limit: 3, candidateLimit: 0, semantic: "", grep: "", order_by: "desc" })
```

Then update it with `me_memory_update` using the ID. The tree paths are:
- `matty.context.me` — identity, role, reporting chain
- `matty.context.team` — direct reports
- `matty.context.people` — key people quick reference
- `matty.context.shorthand` — brand terms and shorthand
- `matty.context.projects` — active projects
- `matty.context.tools` — tools and systems
- `matty.context.preferences` — working preferences

### Step 2: Update Obsidian

Use `obsidian_patch_content` to modify `00 - System/Claude Context.md`.

**Update rules:**
1. **Read the note first** — always read the current state before patching
2. **Make surgical edits** — update only the relevant section
3. **Preserve the structure** — keep existing table/list format
4. **Update the `updated` frontmatter date** — patch the YAML `updated` field to today's date
5. **Confirm the change** — briefly confirm what was changed. One sentence.

### What belongs in context vs. elsewhere

| Information | Where it goes |
|------------|---------------|
| Nickname → full name mapping | Memory Engine `matty.context.people` + Obsidian |
| Person's detailed profile | `05 - People/` page in Obsidian |
| Product/brand terminology | Tiger Den `terms-glossary` reference |
| Brand voice, ICP, writing style | Tiger Den marketing references |
| Asana project IDs, Slack channel IDs | Plugin `config.json` |
| Meeting history | `04 - Meetings/` in Obsidian |
| Task assignments and due dates | Asana (source of truth) |
| Session learnings for blog posts | Memory Engine `matty.learnings.*` |

If the user asks to store something that belongs elsewhere, tell them where it should go and
offer to put it there instead.

---

## Conversational Learning (Offer Mode)

During any session, if you learn something significant that isn't in the context, you can
offer to add it. Examples:

- User mentions a new team member or a departure
- User uses a term/acronym you had to ask about
- A project gets renamed or a new one starts
- Reporting structure changes
- A new Slack channel becomes important

**How to offer:**

> "I noticed [thing]. Want me to add that to your context so I remember it next time?"

If the user says yes, switch to Update mode (updates both Memory Engine and Obsidian).
If no, move on. Don't be pushy — once per session per item is enough. Never offer during
time-sensitive flows like morning-update (save for the end or idle moments).
