---
name: morning-update
platforms: [cowork]
description: >
  Daily morning briefing that syncs tasks from Asana to Obsidian, scans yesterday's
  Slack for action items, and briefs on what's due today and this week. Trigger when
  the user runs /morning-update or says "morning update", "daily briefing", "start my
  day", "what's on my plate", or pastes the morning routine prompt from their daily
  note.
compatibility: >
  Requires Asana, Obsidian, Slack, and Google Calendar MCP connectors. All four are
  needed for the full briefing. If one is missing, run the available parts and tell the
  user what was skipped.
references:
  - brand-voice-guide
---

# Morning Update Skill

This skill runs the daily morning briefing: sync Asana tasks into Obsidian, scan Slack
for things that need attention, and brief on today's schedule and upcoming deadlines.

The flow is always: **gather data → present sync conflicts → get approval → update
Obsidian → deliver briefing.** Never write to Obsidian without explicit user approval.

---

## Step 0 — Load Context

Before doing anything else, load two context sources:

### Personal context (memory layer)

Read `00 - System/Claude Context.md` from the Obsidian vault using `obsidian_get_file_contents`.
This is the memory layer — it tells you who Matty is, his team, shorthand, active projects,
and preferences. Internalize it silently (don't summarize it back). This is the **context-loader**
skill's load mode, inlined here to avoid a separate skill invocation.

### Vault system rules

Read `CLAUDE.md` from the Obsidian vault root using `obsidian_get_file_contents`.
This contains formatting rules, folder structure, and guardrails. Pay special attention to:
- **Task formatting:** emoji format, due date as LAST token, Asana link on indented line below
- **Folder structure:** where things live (Content Production, Projects, Areas, etc.)
- **Asana ↔ Obsidian contract:** Asana = source of assignment, Obsidian = source of execution

### Config values

Read `config.json` from the plugin root to get:
- `asana_project_id` — the MKTG Content Calendar FY27 project
- `slack_user_id` — your Slack user ID (for DM delivery if needed)
- `slack_channels` — array of channel names to scan

---

## Step 1 — Asana/Obsidian Task Sync

This is the most important part of the morning update. It ensures Obsidian reflects what's
actually assigned in Asana.

### 1a. Pull Asana tasks

Use `asana_search_tasks` to find incomplete tasks assigned to the user:
- `assignee_any`: "me"
- `completed`: false
- `projects_any`: use the `asana_project_id` from config
- `opt_fields`: "name,due_on,completed,permalink_url"

### 1b. Read Obsidian Content Production

Use `obsidian_get_file_contents` to read `03 - Areas/Content Production.md`.

Parse the task list under the `## Upcoming Content` heading. Each task follows this format:

```markdown
- [ ] (Type) Task Title 📅 YYYY-MM-DD
  https://app.asana.com/0/...
```

Completed tasks look like:
```markdown
- [x] (Type) Task Title 📅 YYYY-MM-DD ✅ YYYY-MM-DD
  https://app.asana.com/0/...
```

Match Asana tasks to Obsidian tasks by comparing:
1. **Asana permalink URL** against the indented URL on the line below each task (primary match)
2. **Task name similarity** as fallback if URLs don't match exactly (Asana URLs can vary
   in format between `app.asana.com/0/project/task` and `app.asana.com/1/workspace/task/...`)

### 1c. Compare and surface conflicts

Build three lists:

**New in Asana (not in Obsidian):**
Tasks that exist in Asana but have no matching entry in Content Production.md. For each,
show the task name, due date, and Asana link.

**Date mismatches (Asana is canonical):**
Tasks where the Asana due date differs from the Obsidian due date. Show both dates. Asana
is the source of truth for dates — but don't auto-fix, because the user may have a reason
for the discrepancy.

**Completion mismatches:**
Tasks marked complete in Obsidian (`[x]`) but still open in Asana, or tasks completed in
Asana but still open in Obsidian. Both directions matter.

### 1d. Present and get approval

Show all three lists to the user clearly. For each category, ask what to do:

- **New tasks:** "These are in Asana but not in your Content Production note. Want me to
  add them?"
- **Date mismatches:** "These have different dates in Asana vs Obsidian. Asana dates shown
  first. Want me to update Obsidian to match?"
- **Completion mismatches:** "These are out of sync on completion status. Want me to update
  Obsidian?"

Wait for the user to confirm before making any changes. They may want to handle some
manually or skip certain items.

### 1e. Update Obsidian

For approved changes, use `obsidian_patch_content` to update `03 - Areas/Content Production.md`.

**Critical formatting rules** (from CLAUDE.md):
- Due dates use the 📅 emoji and must be the LAST token on the task line
- Asana URLs go on an indented line below the task (never on the same line)
- Task format: `- [ ] (Type) Task Title 📅 YYYY-MM-DD`
- Completed format: `- [x] (Type) Task Title 📅 YYYY-MM-DD ✅ YYYY-MM-DD`

**When using `obsidian_patch_content`:**
- Use the `::` separator to specify the full heading path
  (e.g., `target="Content Production::Upcoming Content"`)
- This is required because Obsidian needs the full path to identify headings correctly

**For new tasks being added:**
- Append to the `## Upcoming Content` section
- Infer the content type prefix from the Asana task name if possible (Blog, LinkedIn Article,
  Video, External, Anchor Essay, Visual Explainer, Short Post). If unclear, omit the prefix
  and note it to the user.

**Personal tasks from Slack:**
If the Slack scan (Step 2) surfaces action items that become tasks, and those tasks are
personal in nature (not work-related), add `#personal` to the task line:
```markdown
- [ ] Schedule dentist appointment #personal 📅 2026-03-20
```
This ensures the Dashboard and daily note templates correctly categorize them.

If `obsidian_patch_content` fails (it can be finicky with complex edits), fall back to
providing paste-ready markdown text that the user can add manually. Don't silently fail.

---

## Step 2 — Slack Scan

Scan yesterday's messages in the configured Slack channels for anything the user needs to
act on. The channels to scan are defined in config.json under `slack_channels`.

Default channels:
- `#team-devrel-private`
- `#content-flywheel`
- `#marketing-leadership`
- `#marketing-private`

### What to look for

Use `slack_search_public_and_private` with appropriate date filters (after: yesterday's
date, before: today's date) and channel filters.

Flag messages that are **actionable for the user specifically**:
- Direct mentions or @-mentions of the user
- Questions directed at the user (by name or role)
- Decisions that affect the user's work
- Requests or asks from leadership
- Deadlines or commitments mentioned
- FYIs that require acknowledgment

**Do NOT flag:**
- General chatter or social messages
- Announcements that are purely informational with no action needed
- Threads the user is already participating in (they've seen it)
- Bot messages unless they contain something genuinely actionable

### How to present

Group by channel. For each actionable item, show:
- Channel name
- Who said it and when
- One-line summary of what needs attention
- A link to the message/thread

Keep it tight. The goal is "here's what you missed that matters" — not a transcript.

---

## Step 3 — Today's Briefing

### In Progress tasks

Before anything else, check Obsidian for any tasks currently marked `[/]` (in-progress
status from Task Genius). Use `obsidian_simple_search` with query `[/]` or scan the
Content Production data already loaded. Surface these first — they represent work already
started and should be top of mind. Present as: "You have N tasks in progress: ..."

### Focus tasks

Check for any tasks tagged `#focus` in Obsidian. These are intentionally capped at 3 and
represent the user's near-term priorities. Call these out separately if present.

### Calendar

Use `gcal_list_events` to pull today's calendar. Present a clean list of meetings with
time, title, and attendees count. Skip personal blocks if they're obviously non-work
(use judgment — things like "Lunch", "Walk dogs", "Commute" can be skipped; anything
ambiguous should be included).

### Due today

From the Asana data already pulled in Step 1, list tasks due today.

Also check Obsidian for any non-Asana tasks due today — use `obsidian_simple_search` with
today's date in 📅 format, or rely on the Content Production data already loaded.

### Due this week

List tasks due through the end of this week (Sunday). Group by day. Highlight anything
that looks tight (due tomorrow with no draft link, multiple items due the same day, etc.).

### Overdue

Surface any tasks past their due date that are still incomplete. These need attention.

### Work vs Personal labeling

When presenting tasks in any of the above sections, note whether each is **work** or
**personal**. Tasks from `03 - Areas/Home.md` or tagged `#personal` are personal;
everything else is work. A simple inline label like "(personal)" is enough — don't
over-format it.

---

## Step 4 — Deliver the Briefing

Present everything in a single, scannable briefing. Structure it as:

1. **Task Sync Summary** — What was synced, what conflicts were found, what was updated
2. **In Progress** — Tasks currently marked `[/]` that are already underway
3. **Slack Highlights** — Actionable items from yesterday, grouped by channel
4. **Today's Schedule** — Calendar overview
5. **Due Today** — Tasks due today
6. **Due This Week** — Upcoming deadlines
7. **Overdue** — Past-due items needing attention

Keep the tone direct and useful — this is a morning briefing, not a report. Think "chief
of staff handing you a one-pager" not "quarterly business review."

### Offer to create meeting notes

After delivering the briefing, if there are real meetings on today's calendar, ask:

> "Want me to create meeting notes for today's meetings?"

If the user says yes, hand off to the **meeting-notes** skill. The calendar data already
fetched in Step 3 can be reused — pass the events to the meeting-notes flow starting at
its Step 2 (filter events). This avoids a redundant calendar API call.

If the user says no or doesn't respond, move on. This is a convenience offer, not a
required step.

---

## Edge Cases

**Obsidian MCP unavailable:**
Skip the task sync and Obsidian reads. Run Asana + Slack + Calendar portions and tell the
user the Obsidian sync was skipped because the connector isn't available.

**Asana MCP unavailable:**
Skip the task sync and Asana-based due date sections. Run Slack + Calendar + whatever
Obsidian data is available. Note the gap.

**Slack MCP unavailable:**
Skip the Slack scan. Run everything else. Note it.

**Calendar MCP unavailable:**
Skip the calendar section. Run everything else. Note it.

**No conflicts found in task sync:**
Great — say "Asana and Obsidian are in sync, no changes needed" and move on. Don't pad
the briefing.

**User says "skip sync" or "just brief me":**
Skip Step 1 entirely and go straight to Slack scan + briefing.

**Weekend or no meetings:**
Adjust the Slack scan window if it's Monday (scan Friday + weekend). If there are no
meetings today, say so — don't fabricate a schedule section.
