---
name: meeting-notes
platforms: [cowork]
description: >
  Create Obsidian meeting notes for today's (or a specified day's) calendar events.
  Pulls Google Calendar events, filters out personal blocks, checks for existing notes,
  resolves attendees against the People directory for proper Dataview linking, and creates
  pre-populated meeting notes. Trigger when the user runs /meeting-notes or says "create
  meeting notes", "set up my meetings", "prep my meeting notes", "create notes for
  today's meetings", or "meeting notes for tomorrow". Can also be triggered from the
  morning-update skill.
compatibility: >
  Requires Google Calendar and Obsidian MCP connectors. Both are needed — Calendar for
  event data, Obsidian for creating the notes. If either is missing, explain what's
  needed and stop.
references: []
---

# Meeting Notes Skill

This skill creates Obsidian meeting notes for each real meeting on a given day's calendar.
It pulls events from Google Calendar, filters out personal/routine blocks, resolves
attendees against the People directory, and creates properly formatted meeting notes in
the Obsidian vault.

The flow is always: **pull calendar → filter → resolve attendees → check for existing
notes → present list → get approval → create notes (and optionally People pages).**
Never create notes without showing the user what will be created first.

---

## Before You Start — Load Context

### Obsidian context

Read the user's `CLAUDE.md` from the Obsidian vault root using `obsidian_get_file_contents`.
This contains the folder structure, meeting system design, and formatting rules.

Key points from CLAUDE.md:
- Meetings live in `04 - Meetings/`
- Templater is configured to auto-apply `Meeting.md` template on file creation in that
  folder — but since we create via MCP, Templater won't fire. We must build the content
  ourselves matching the template's output format.
- Meeting notes are chronological, not mapped to projects
- The `summary` frontmatter field is for a brief one-liner (used on People page Dataview
  queries — the query is `WHERE contains(attendees, this.file.name)`)
- People pages live in `05 - People/` and use Dataview to list meetings

### People directory

Use `obsidian_list_files_in_dir` with `dirpath: "05 - People"` to get the current list
of People pages. Strip the `.md` extension to get the names. This list is used for
attendee resolution in Step 2b.

### User timezone

The user is in **America/Chicago** (Central Time). Always use this timezone when pulling
calendar events.

---

## Step 1 — Pull Calendar Events

### Determine the target date

The user may specify a date ("tomorrow", "Friday", "March 15"). If they don't, default
to **today**.

### Fetch events

Use `gcal_list_events` with:
- `timeMin`: start of target date (`YYYY-MM-DDT00:00:00`)
- `timeMax`: end of target date (`YYYY-MM-DDT23:59:59`)
- `timeZone`: `America/Chicago`
- `condenseEventDetails`: false (we need attendees)

---

## Step 2 — Filter Events

### 2a. Events to SKIP (personal/routine blocks)

Filter out events that are not real meetings. Skip any event where:

- `eventType` is `workingLocation` (e.g., "Home")
- `eventType` is `focusTime` (e.g., "Focus")
- `transparency` is `transparent` AND the event has no attendees (personal time blocks)
- The summary matches common personal blocks (case-insensitive partial match):
  - "Walk dogs", "Lunch", "Workout", "Prepare For Day", "Commute", "Break",
    "Pick up kids", "Dinner", "EOD"

### Events to INCLUDE

Keep everything else — these are real meetings. This includes:
- 1:1s, team meetings, all-hands, external calls
- Events where the user has any response status (accepted, tentative, needsAction)
- Events marked `[EXTERNAL]` — these are real meetings with outside parties

### Events to FLAG (let the user decide)

Some events are ambiguous. Flag these but default to including them:
- Events where the user's `myResponseStatus` is `declined`
- Events where the user's `myResponseStatus` is `needsAction` AND the event has
  `optional: true` for the user (they may not attend)

### 2b. Resolve attendees against People directory

This is critical for Dataview linking. The People page Dataview query uses:
```
WHERE contains(attendees, this.file.name)
```
So the attendee list in meeting YAML must contain the **exact People page filename**
for the link to work (e.g., "Corey Fitz" not "Corey" or "corey@tigerdata.com").

For each calendar attendee across all included events:

1. **Skip self** — if `email` is `matty@tigerdata.com` or `self: true`, add as just
   `Matty` (no resolution needed).

2. **Match by email** — read each People page's frontmatter looking for a matching
   `email` field. This is the most reliable match.

3. **Match by display name** — if no email match, compare the calendar `displayName`
   against People page filenames. Use fuzzy matching to handle variations:
   - "Makineni, Charishma" → check if any People page contains "Charishma" or "Makineni"
   - "Doug Pagnutti" → direct match against "Doug Pagnutti.md"
   - Handle "Last, First" format by reversing to "First Last"

4. **No match found** — if an attendee can't be matched to a People page, track them
   separately. These will be surfaced to the user in Step 4 with an offer to create
   People pages.

**Performance note:** Reading every People page's frontmatter can be slow if there are
many. To optimize:
- First try name matching (step 3) since it doesn't require reading files
- Only fall back to email matching (step 2) for attendees that didn't match by name
- Cache the People list — it's the same across all meetings for this run
- Use `obsidian_batch_get_file_contents` to read multiple People pages at once if needed

---

## Step 3 — Check for Existing Notes

For each included event, check whether a meeting note already exists. The filename
format is `YYYY-MM-DD Meeting Name.md` in `04 - Meetings/`.

Use `obsidian_list_files_in_dir` with `dirpath: "04 - Meetings"` and check for files
starting with the target date.

If a note already exists for a meeting (match by date prefix + similar name), mark it
as "already exists" and default to skipping it. The user can override this to recreate.

---

## Step 4 — Present the List

Show the user a clean list of what will be created. For each meeting:

- **Time** (in Central Time, e.g., "9:30–10:00 AM CT")
- **Meeting name** (from calendar summary)
- **Attendees** (resolved names)
- **Summary** (the one-liner that will go in frontmatter)
- **Status**: "Will create" / "Already exists — skipping" / "Flagged — you declined"

### Surface unresolved attendees

If any attendees across the day's meetings couldn't be matched to People pages, surface
them after the meeting list:

```
I found 2 meetings on your calendar for today (Mar 11). Here's what I'll create:

  9:30–10:00  Corey / Matty sync
              Attendees: Matty, Corey Fitz
              Summary: "Weekly 1:1 sync with Corey."
              → Will create

 12:00–12:30  AWS/TigerData Workshop sync
              Attendees: Matty, Doug Pagnutti + 4 external
              Summary: "Sync with AWS team on workshop collaboration."
              → Will create

Skipped (personal blocks): Prepare For Day, Walk dogs ×2, Focus, Lunch, Workout

These attendees don't have People pages yet:
  - Charishma Makineni (cmakinen@amazon.com) — in AWS/TigerData Workshop sync
  - Vijay Pawar (vppwr@amazon.com) — in AWS/TigerData Workshop sync
  - Helen Har Theisen (theisenh@amazon.com) — in AWS/TigerData Workshop sync
  - Mrinali Umashankar (umamrina@amazon.com) — in AWS/TigerData Workshop sync

Want me to create People pages for any of them? (You can say "all", list names,
or "none" to skip.)

Want me to create these 2 meeting notes? Or any changes?
```

Wait for user confirmation on both the meeting notes AND whether to create People pages.

---

## Step 5 — Create People Pages (if requested)

For any attendees the user wants to add, create a People page in `05 - People/` using
`obsidian_append_content`.

### Filename

`05 - People/Full Name.md`

Use the display name from the calendar. Clean up "Last, First" formats to "First Last".
Example: "Makineni, Charishma" → `05 - People/Charishma Makineni.md`

### File content

Match the Person.md template output:

```markdown
---
type: person
company: [infer from email domain — e.g., "Amazon" for @amazon.com, "TigerData" for @tigerdata.com]
title:
email: [their email address]
image: https://www.clker.com/cliparts/3/c/9/0/15346636991003506792default_user.png
obsidianUIMode: preview
---

# Full Name

`="![image|200](" + this.image + ")"`

## Notes

-

## Meetings

> [!SUMMARY]+ Meetings
> ```dataview
> TABLE date AS "Date", summary AS "Summary"
> FROM "04 - Meetings"
> WHERE contains(attendees, this.file.name)
> SORT date DESC
> ```
```

After creating People pages, update the internal people list so the subsequent meeting
note creation uses the correct names.

---

## Step 6 — Create Meeting Notes

For each confirmed meeting, create a file in Obsidian using `obsidian_append_content`.

### Filename

Format: `YYYY-MM-DD Meeting Name.md`

Where "Meeting Name" is the calendar event summary, with these cleanups:
- Strip `[EXTERNAL]` prefix (but keep the rest)
- Replace illegal filename characters (`\ / : * ? " < > |`) with `-`
- Collapse multiple dashes and whitespace
- Trim leading/trailing whitespace

Example: `2026-03-11 AWS-TigerData Workshop sync.md`

The full filepath is: `04 - Meetings/YYYY-MM-DD Meeting Name.md`

### File content

Build the content to match what the Meeting.md Templater template would produce:

```markdown
---
type: meeting
date: YYYY-MM-DD
summary: [one-liner summary — see below]
attendees:
  - Matty
  - Corey Fitz
  - Doug Pagnutti (doug@tigerdata.com)
---

# Meeting Name

## Context

[Brief context — see below for how to populate this]

------------------------------------------------------------------------

## Notes

Any notes for the meeting

------------------------------------------------------------------------

## Actions

- [ ]
```

### Attendee formatting in YAML

This is the most important part for Dataview linking to work correctly.

- **Attendees with People pages:** Use the **exact People page filename** as the
  attendee entry. This ensures `contains(attendees, this.file.name)` matches.
  - If you want to also show the email, append it in parentheses AFTER the full name:
    `Corey Fitz (corey@tigerdata.com)` — this still matches because `contains()` does
    substring matching and "Corey Fitz" is contained in "Corey Fitz (corey@tigerdata.com)"
  - For the user, just `Matty` (no email)

- **Attendees WITHOUT People pages (user declined to create):** Use the display name
  and email: `Charishma Makineni (cmakinen@amazon.com)`. If the user later creates a
  People page, the Dataview query will start matching automatically as long as the
  filename is contained in this string.

- **Attendees with no display name:** Derive from email: `cmakinen (cmakinen@amazon.com)`

### Summary frontmatter

The `summary` field is a brief one-liner that appears in Dataview TABLE queries on
People pages. It should be short and descriptive — think "what was this meeting about"
in 5-10 words.

Populate based on what you can infer:

- **Recurring 1:1s** (names like "X and Y 1-1", "X / Y sync"):
  "Weekly 1:1 sync with [other person]." or "Bi-weekly sync with [other person]."
- **Team meetings** (names like "Marketing All Weekly", "GTM All"):
  "Weekly marketing team all-hands." / "GTM alignment meeting."
- **External meetings** (`[EXTERNAL]` prefix or non-tigerdata attendees):
  "Sync with [company] on [topic from title]."
- **Named topics** (event title is descriptive): Derive from the title.
  E.g., "KOL Contract Check-in" → "KOL contract status check-in."
- **Everything else**: Leave blank rather than fabricate. The user will fill it in
  after the meeting.

### Context section

The `## Context` section is longer than the summary — it's a paragraph that gives you
context when you open the note before the meeting starts.

- **Recurring 1:1s**: "Weekly 1:1 sync between Matty and [other person]."
- **Team meetings**: Use the event description if available (first sentence or meaningful
  excerpt). If no description, write a generic context like "Weekly marketing team
  all-hands."
- **External meetings**: Note the external company and topic.
  E.g., "Sync with AWS team on workshop collaboration."
- **Everything else**: Leave as "What is this meeting about?" (template default) if
  there's not enough context to write something useful. Don't fabricate.

---

## Step 7 — Summary

After creating all notes, present a summary:

```
Done! Created 2 meeting notes in 04 - Meetings/:

  9:30  2026-03-11 Corey - Matty sync.md
        Attendees: Matty, Corey Fitz
        Summary: "Weekly 1:1 sync with Corey."

 12:00  2026-03-11 AWS-TigerData Workshop sync.md
        Attendees: Matty, Doug Pagnutti + 4 others
        Summary: "Sync with AWS team on workshop collaboration."

Also created 2 People pages: Charishma Makineni, Vijay Pawar

Skipped: 6 personal blocks, 0 already existed
```

---

## Integration with Morning Update

The morning-update skill pulls calendar data for the daily briefing. After presenting
the briefing (Step 4 of morning-update), it should ask:

> "Want me to create meeting notes for today's meetings?"

If the user says yes, morning-update should hand off to this skill. The calendar data
already fetched by morning-update can be reused — no need to pull it again. The flow
picks up from Step 2 (filter events) using the already-fetched events.

This is optional — the user can also run /meeting-notes independently at any time.

---

## Edge Cases

**No meetings today:**
If all events are personal blocks, say "No meetings on your calendar for [date] — just
personal time blocks. Nothing to create."

**Event with no attendees (but is a real meeting):**
Some calendar events are just placeholders the user created without inviting anyone. If
it passed the filter (not a personal block), create the note but leave attendees as just
`- Matty` and note it to the user.

**Very long event summary:**
If the summary is excessively long (>80 chars), truncate the filename but keep the full
name in the note's `# Heading`. Add a note about the truncation.

**Multiple meetings with the same name:**
If two events share a name (e.g., recurring meetings that got duplicated), append the
time to disambiguate: `2026-03-11 Team Sync (2pm).md`

**User asks for a different day:**
Support "tomorrow", "Friday", "March 15", "next Monday" etc. Parse the date and adjust
the calendar query accordingly.

**Obsidian append_content creates the file if it doesn't exist:**
This is the expected behavior. `obsidian_append_content` with a filepath that doesn't
exist will create the file. This is what we want.

**Calendar event was declined:**
Default to skipping declined events but mention them. The user can ask to include them.

**All-day events:**
Skip all-day events — these are typically working locations, OOO markers, or holidays,
not meetings.

**Large number of external attendees:**
For meetings with many external attendees (>5), don't offer to create People pages for
all of them individually. Instead, offer a bulk option: "This meeting has 12 external
attendees. Want me to create People pages for all of them, or just specific ones?"

**People page already exists with different name format:**
If a calendar displayName is "Doug Pagnutti" and the People page is "Doug Pagnutti.md",
that's a direct match. But if the calendar says "Pagnutti, Doug" and the file is
"Doug Pagnutti.md", the fuzzy matching in Step 2b should catch this by reversing
"Last, First" to "First Last".
