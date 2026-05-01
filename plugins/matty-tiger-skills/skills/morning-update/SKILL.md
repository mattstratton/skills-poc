---
name: morning-update
platforms: [cowork, claude-code]
description: >
  Daily morning briefing that syncs tasks from Asana and GitHub to Obsidian, scans
  yesterday's Slack for action items, and briefs on what's due today and this week.
  Trigger when the user runs /morning-update or says "morning update", "daily briefing",
  "start my day", "what's on my plate", or pastes the morning routine prompt from their
  daily note.
compatibility: >
  Obsidian MCP is REQUIRED — the skill will not run without it. Asana, Slack, and Google
  Calendar MCPs are needed for full coverage; if missing, those sections are skipped with
  a note. GitHub data is fetched via the `gh` CLI when running in Claude Code (Bash tool
  available), or via GitHub MCP when running in cowork; if neither is available, the
  GitHub sync is skipped.
references:
  - brand-voice-guide
---

# Morning Update Skill

This skill runs the daily morning briefing: sync Asana tasks and GitHub issues/PRs into
Obsidian, scan Slack for things that need attention, and brief on today's schedule and
upcoming deadlines.

The flow is always: **gather data → present sync conflicts → get approval → update
Obsidian → deliver briefing.** Never write to Obsidian without explicit user approval.

---

## Step 0 — Preflight Check + Load Context

### Obsidian MCP (hard gate)

Before doing anything else, verify the Obsidian MCP is available by attempting to call
`obsidian_get_file_contents` on `00 - System/Claude Context.md`. If the call fails or
the tool does not exist, **stop immediately** — do not proceed to any other step. Tell
the user:

> "This skill requires the Obsidian MCP and it isn't available in this session. To fix
> this:
> - **Claude Code:** add the Obsidian MCP server to `~/.claude/settings.json` under
>   `mcpServers` (stdio MCP — not the Desktop app config)
> - **claude.ai cowork:** connect it in your claude.ai integrations settings"

Do not run a partial briefing. Do not skip ahead to Slack or calendar. Stop here.

If the call succeeds, internalize the context silently (don't summarize it back) and
continue.

### Personal context (memory layer)

Run the **context-loader** skill in load mode. This searches Memory Engine first, with
Obsidian as fallback. Internalize silently — do not summarize back to the user.

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
- `github_org` — the GitHub organization to query for issues and PRs (e.g., "timescale")

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
If the Slack scan (Step 3) surfaces action items that become tasks, and those tasks are
personal in nature (not work-related), add `#personal` to the task line:
```markdown
- [ ] Schedule dentist appointment #personal 📅 2026-03-20
```
This ensures the Dashboard and daily note templates correctly categorize them.

If `obsidian_patch_content` fails (it can be finicky with complex edits), fall back to
providing paste-ready markdown text that the user can add manually. Don't silently fail.

---

## Step 2 — GitHub/Obsidian Sync

Before doing anything in this step, ask the user:

> "Want me to sync GitHub too, or skip straight to Slack?"

If they say no / skip / anything in that direction — jump directly to Step 3. Do not
make any GitHub API calls or read any GitHub-related Obsidian files.

This step syncs GitHub issues assigned to the user and PRs awaiting their review into
`03 - Areas/GitHub.md`. GitHub is the source of truth — Obsidian tracks what's on your
plate so it flows into the Dashboard alongside Asana tasks.

### 2a. Pull GitHub data

Use the `github_org` value from config. How you fetch the data depends on your context:

**If the Bash tool is available (Claude Code):**
Use the `gh` CLI. Run these three commands:

```bash
# Issues assigned to you
gh search issues --assignee @me --owner {github_org} --state open --json number,title,url,repository,labels --limit 50

# PRs awaiting your review
gh search prs --review-requested @me --owner {github_org} --state open --json number,title,url,repository,labels --limit 50

# Your own open PRs
gh search prs --assignee @me --owner {github_org} --state open --json number,title,url,repository,labels --limit 50
```

**If the Bash tool is NOT available (cowork):**
Use GitHub MCP tools if available:
- `search_issues` with query: `assignee:@me org:{github_org} state:open`, sort by `updated` desc
- `search_pull_requests` with query: `review-requested:@me org:{github_org} state:open`, sort by `updated` desc
- `search_pull_requests` with query: `assignee:@me org:{github_org} state:open`, sort by `updated` desc

**If neither is available:**
Skip Step 2 entirely. Note it in the briefing: "GitHub sync skipped — no `gh` CLI or
GitHub MCP available." GitHub is not a hard gate; the briefing can proceed without it.

From each result, extract: `title`, `number`, `html_url` (or `url`), `state`, and the
repo name. Also extract `labels` if present.

### 2b. Read Obsidian GitHub note

Use `obsidian_get_file_contents` to read `03 - Areas/GitHub.md`.

Parse the task lists under `## Issues` and `## Review Requests`. Tasks use inline links:

```markdown
- [ ] Task title [#43](https://github.com/timescale/marketing-skills-issues/issues/43)
```

Or with an optional due date:
```markdown
- [ ] Task title [#43](https://github.com/timescale/marketing-skills-issues/issues/43) 📅 2026-03-20
```

Completed tasks:
```markdown
- [x] Task title [#43](https://github.com/timescale/marketing-skills-issues/issues/43) 📅 2026-03-20 ✅ 2026-03-22
```

Issues are grouped under repo-name headings (### level) within `## Issues`. Review
Requests are flat under `## Review Requests` and use the format
`[repo-name#number](url)` to identify the repo:

```markdown
- [ ] Fix caching logic [timescale/tiger-den#247](https://github.com/timescale/tiger-den/pull/247)
```

Match GitHub items to Obsidian tasks by extracting the URL from the inline markdown
link and comparing to the `html_url` from the API.

### 2c. Compare and surface conflicts

Build three lists:

**New in GitHub (not in Obsidian):**
Issues or PRs that exist in GitHub but have no matching entry in GitHub.md. For each,
show the title, repo, number, and link.

**Closed in GitHub (still open in Obsidian):**
Items marked `[ ]` or `[/]` in Obsidian but whose GitHub state is `closed`. These
should be marked complete. Show each one.

**In Obsidian but gone from GitHub (unassigned/transferred):**
Items in Obsidian that no longer appear in the GitHub search results. These may have
been reassigned, transferred, or the user was removed. Flag them — don't auto-remove.

### 2d. Present and get approval

Show all three lists. For each category:

- **New issues/PRs:** "These are assigned to you in GitHub but not tracked in Obsidian.
  Want me to add them?" For each new item, ask: **"Any due date you want to set?"**
  If the user provides a date, include it as `📅 YYYY-MM-DD` at the end of the task
  line (must be the LAST token). If they say no or skip, omit the due date.
- **Closed items:** "These are closed in GitHub but still open in your GitHub note.
  Want me to mark them done?"
- **Gone items:** "These are in your GitHub note but no longer assigned to you in
  GitHub. Want me to remove them, or keep tracking them?"

Wait for confirmation before making changes.

### 2e. Update Obsidian

For approved changes, use `obsidian_patch_content` to update `03 - Areas/GitHub.md`.

**Task format — Issues (grouped by repo):**
```markdown
### timescale/marketing-skills-issues
- [ ] Add guard to release.yml [#43](https://github.com/timescale/marketing-skills-issues/issues/43)
- [ ] Create PR reviewer docs [#33](https://github.com/timescale/marketing-skills-issues/issues/33) 📅 2026-03-20
```

**Task format — Review Requests (flat list):**
```markdown
- [ ] Fix caching logic [timescale/tiger-den#247](https://github.com/timescale/tiger-den/pull/247)
```

**Key formatting rules:**
- Due dates use the 📅 emoji and must be the LAST token on the task line
- The inline link `[#number](url)` or `[repo#number](url)` is both the display text
  and the sync key — never break this format
- New repo headings (### level) are created automatically under `## Issues` when an
  issue appears in a repo not yet represented
- If a repo heading has no remaining open tasks after sync, remove the empty heading
- Use `obsidian_patch_content` with `target="GitHub::Issues"` or
  `target="GitHub::Review Requests"` as appropriate

**Marking items complete:**
Change `- [ ]` to `- [x]` and append `✅ YYYY-MM-DD` (today's date). Keep due dates
in their original position (before the ✅).

If `obsidian_patch_content` fails, fall back to providing paste-ready markdown. Don't
silently fail.

---

## Step 3 — Slack Scan

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

## Step 4 — Today's Briefing

### In Progress tasks

Before anything else, check Obsidian for any tasks currently marked `[/]` (in-progress
status from Task Genius). Use `obsidian_simple_search` with query `[/]` or scan the
Content Production and GitHub data already loaded. Surface these first — they represent
work already started and should be top of mind. Present as: "You have N tasks in progress: ..."

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

Also check Obsidian for any non-Asana tasks due today (including GitHub tasks with due
dates) — use `obsidian_simple_search` with today's date in 📅 format, or rely on the
Content Production and GitHub data already loaded.

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

## Step 5 — Deliver the Briefing

Present everything in a single, scannable briefing. Structure it as:

1. **Task Sync Summary** — What was synced (Asana + GitHub), conflicts found, what was updated
2. **In Progress** — Tasks currently marked `[/]` that are already underway
3. **Slack Highlights** — Actionable items from yesterday, grouped by channel
4. **Today's Schedule** — Calendar overview
5. **Due Today** — Tasks due today (from both Asana and GitHub)
6. **Due This Week** — Upcoming deadlines (from both Asana and GitHub)
7. **Overdue** — Past-due items needing attention
8. **GitHub Review Requests** — Open PRs awaiting your review (always surface these even if none are due — they're blocking someone else)

Keep the tone direct and useful — this is a morning briefing, not a report. Think "chief
of staff handing you a one-pager" not "quarterly business review."

### Offer to create meeting notes

After delivering the briefing, if there are real meetings on today's calendar, ask:

> "Want me to create meeting notes for today's meetings?"

If the user says yes, hand off to the **meeting-notes** skill. The calendar data already
fetched in Step 4 can be reused — pass the events to the meeting-notes flow starting at
its Step 2 (filter events). This avoids a redundant calendar API call.

If the user says no or doesn't respond, move on. This is a convenience offer, not a
required step.

---

## Edge Cases

**Obsidian MCP unavailable (HARD STOP):**
Do not proceed. See the preflight check in Step 0 for the exact stop message and setup
instructions. This is not a graceful degradation — Obsidian is the core of this skill.

**Asana MCP unavailable:**
Skip the Asana task sync and Asana-based due date sections. Run GitHub sync + Slack +
Calendar + whatever Obsidian data is available. Note the gap.

**GitHub unavailable (no `gh` CLI and no GitHub MCP):**
Skip Step 2 entirely. Note it in the briefing. If GitHub.md already has tasks from a
previous sync, those still flow into the briefing via Obsidian — mention the data may
be stale.

**Slack MCP unavailable:**
Skip the Slack scan. Run everything else. Note it.

**Calendar MCP unavailable:**
Skip the calendar section. Run everything else. Note it.

**No conflicts found in task sync:**
Great — say "Asana and Obsidian are in sync, no changes needed" and move on. Don't pad
the briefing.

**User says "skip sync" or "just brief me":**
Skip Steps 1 and 2 entirely and go straight to Slack scan + briefing.

**Weekend or no meetings:**
Adjust the Slack scan window if it's Monday (scan Friday + weekend). If there are no
meetings today, say so — don't fabricate a schedule section.
