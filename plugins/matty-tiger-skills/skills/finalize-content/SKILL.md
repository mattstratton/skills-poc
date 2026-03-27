---
name: finalize-content
platforms: [cowork, claude-code]
description: >
  Finalizes a published content piece by updating its Asana task on the MKTG Content Calendar.
  Sets the status to "Published!", adds the published URL, completes the "Add final published
  link" subtask, and marks the task done. Optionally announces the publication in
  #content-flywheel on Slack. Trigger when the user says they've published a blog post,
  LinkedIn article, or other content and want to update the Asana card — or when they mention
  "finalize", "mark as published", "close out the content task", "update the card", "it's
  live", or similar. Also trigger if the user runs /finalize-content.
compatibility: >
  Requires Asana MCP connector. Slack connector needed for the optional #content-flywheel
  announcement.
references: []
---

# Finalize Content

This skill handles the "last mile" after a piece of content (blog post, LinkedIn article, video, etc.) goes live. It updates the Asana task on the MKTG Content Calendar so the board accurately reflects what's been published, and optionally announces it to the team in Slack.

---

## Before You Start — Load Context

### Personal context (memory layer)

Read `00 - System/Claude Context.md` from the Obsidian vault using `obsidian_get_file_contents`.
This is the memory layer — team, key people, shorthand, active projects. Internalize it
silently (don't summarize it back).

### Config values

Read `config.json` from the plugin root to get:
- `asana_project_id` — the MKTG Content Calendar project (used to scope task searches)
- `slack_channels` — list of known Slack channels (includes #content-flywheel)

### Asana custom field GIDs

These are specific to the MKTG Content Calendar and don't change:
- **Status** custom field: `1213144715555970` (enum)
- **"Published!"** enum option: `1213144715555975`
- **Published URL** custom field: `1213474863169563` (text)

### Slack channel

- **#content-flywheel** channel ID: `C08R4GCABHU`

---

### Asana custom field GIDs (for filtering)

These are used during task discovery to narrow results:
- **Content Type** custom field: `1213144715555977` (enum)
  - Short Post: `1213144715555978` (covers blog posts and LinkedIn articles)
  - Anchor Essay: `1213144715555980`
  - Video: `1213144715555979`
  - Social Post: `1213144715555982`
- **Status** enum options for "ready" content:
  - Ready to publish: `1213144715555974`
  - In review: `1213144715555973`

---

## What you need from the user

You need two things: which task and the published URL. The Slack announcement is optional. Here's how to gather them efficiently.

### 1. Which content piece

The user might identify the task in several ways — and some are more specific than others. Handle each case:

**User gave you an Asana URL or task GID:** Skip straight to Step 2 (fetch the task directly).

**User named a specific post:** Search for it — see Step 1 below.

**User didn't specify a task (just said "finalize" or "mark something as published"):**
Proactively show them their finalize-ready tasks. Use `search_tasks_preview` with:
- `projects_any`: the `asana_project_id` from config
- `assignee_any`: "me"
- `completed`: false

This gives the user a list of their open content tasks to pick from. The Asana MCP's `search_tasks_preview` renders a nice preview card — after calling it, just ask the user which one they want to finalize. Don't try to summarize or list the tasks yourself; the preview card handles that.

### 2. The published URL

The live link where the content was published (e.g. `https://www.tigerdata.com/blog/some-post` or a LinkedIn article URL). If the user hasn't provided it, ask.

### 3. Slack announcement? (optional)

Ask whether they'd like to post an announcement to #content-flywheel. Default to offering it (it's the team norm), but always confirm before sending.

---

## The workflow

### Step 1: Find the Asana task

Use the `asana_project_id` from config.json to scope searches to the content calendar.

**If the user named a specific post:** use `search_tasks_preview` with:
- `projects_any`: the `asana_project_id` from config
- `text`: keywords from what the user said
- `completed`: false

If multiple results match and it's not obvious which one, the preview card will show the user the options — ask them to pick. If nothing matches, try `search_objects` (resource_type: task) with different keywords as a fallback.

**If the user didn't specify:** show them the proactive list as described above, then wait for them to pick.

### Step 2: Fetch full task details

Once you've identified the right task, use `get_task` with `include_subtasks: true` and `include_comments: false` to get:
- The task name (for the Slack message and summary)
- Custom fields like Content Type and Medium (helpful context for the announcement)
- The subtask list (to find "Add final published link")
- The task's `permalink_url` (to include in the summary)

### Step 3: Update the Asana task

Use `update_tasks` to do all of the following in a single call:

```json
{
  "tasks": [{
    "task": "<task_gid>",
    "completed": true,
    "custom_fields": {
      "1213144715555970": "1213144715555975",
      "1213474863169563": "<the_published_url>"
    }
  }]
}
```

This single call sets the status to "Published!", fills in the Published URL, and marks the task complete.

### Step 4: Complete the "Add final published link" subtask

Look through the subtasks from Step 2 for one named "Add final published link" — match case-insensitively and be a little fuzzy (it might be worded slightly differently across tasks). If you find it and it's incomplete, mark it complete:

```json
{
  "tasks": [{
    "task": "<subtask_gid>",
    "completed": true
  }]
}
```

If this subtask doesn't exist or is already completed, skip silently. It's not worth mentioning to the user.

### Step 5 (optional): Announce in #content-flywheel

If the user wants a Slack announcement, send a message to **#content-flywheel** (`C08R4GCABHU`).

Keep it short and not annoyingly corporate. Include the content title and the published URL. Something like:

> :rocket: New content published: **[Task Name]** — <published_url>

Vary the emoji and phrasing so it doesn't feel like a bot every time. If you know the content type from the task's custom fields, work it in naturally (e.g. "New blog post published" vs "New LinkedIn article published" vs "New video published"). One to two lines max.

Use `slack_send_message` (not `slack_send_message_draft`) since this is a simple factual announcement, not something that needs user review before sending. That said — you already confirmed the user wants to send it in the earlier step, so this is expected.

---

## Error handling

- If `update_tasks` fails: tell the user what went wrong and stop. Don't send the Slack message if the Asana update didn't go through.
- If the subtask completion fails: mention it briefly but continue with the rest of the workflow. It's not critical.
- If the Slack message fails: let the user know — they can post manually.

---

## Summary

After everything's done, give the user a quick recap:
- Which task was updated (include the Asana permalink)
- That the status is now "Published!" and the URL was added
- Whether the subtask was found and completed (or didn't exist)
- Whether the Slack announcement was sent (include a link to the message if possible)

Keep it concise — a few lines, not a dissertation.
