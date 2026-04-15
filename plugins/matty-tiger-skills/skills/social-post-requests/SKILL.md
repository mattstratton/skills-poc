---
name: social-post-requests
platforms: [cowork]
description: >
  Draft social media posts for a published blog post and submit a Social Promotion Request
  in Asana. The user provides an Asana card URL from the MKTG Content Calendar FY27.
  Claude fetches the published URL from that card, invokes the social-post-writer skill
  to generate LinkedIn and X posts, asks the user when they want the posts scheduled,
  then creates a task on the Social Promotion Requests (LinkedIn and X) board and
  comments back on the original blog post card. Trigger when the user says "social posts
  for this blog", "submit a social promotion request", "request social posts", "social
  media posts for my blog post", or provides an Asana content calendar card URL and asks
  for social posts.
compatibility: >
  Requires Asana MCP connector. Also requires the tigerdata-marketing-skills plugin to be
  installed (uses the social-post-writer skill).
references: []
---

# Social Post Requests

This skill drafts social media posts for a published blog post and submits a formal Social
Promotion Request on the Asana "Social Promotion Requests - LinkedIn and X" board. It
bridges the MKTG Content Calendar (where blog posts live) and the social promotion
workflow (where the social team picks up requests).

The flow is always: **fetch card → generate posts → user approves → get schedule date →
create request → comment back.** Never submit the Asana request without explicit user
approval of the social posts.

---

## Before You Start — Load Context

### Config values

Read `config.json` from the plugin root to get:
- `asana_project_id` — the MKTG Content Calendar FY27 project
- `social_promotion_project_id` — the Social Promotion Requests (LinkedIn and X) project

### Asana custom field GIDs

These are specific to the MKTG Content Calendar and don't change:
- **Published URL** custom field: `1213474863169563` (text)

---

## Step 1 — Get the Asana card URL from the user

The user should provide the URL of the blog post's Asana card from the MKTG Content
Calendar FY27. If they haven't, ask for it.

Parse the task GID from the URL. Asana task URLs follow the pattern:
`https://app.asana.com/0/<project_id>/<task_gid>/f` or similar. Extract the last numeric
segment before `/f` as the task GID.

---

## Step 2 — Fetch the blog post task details

Use `asana_get_task` with the task GID to retrieve:
- `name` — the blog post title (strip any `[Blog]` prefix for display purposes)
- Custom field `1213474863169563` — the Published URL
- `permalink_url` — to use when commenting back

If the Published URL custom field is empty or missing, stop and tell the user:
> "The Published URL field on that Asana card is empty — the post may not be published yet,
> or the field wasn't filled in. Can you paste the published URL directly?"

If the user provides the URL directly, use that.

---

## Step 3 — Generate social posts with social-post-writer

Invoke the `tigerdata-marketing-skills:social-post-writer` skill to draft the social posts.

Tell the skill you are working in **repurpose mode** and provide:
- The published blog post URL (from Step 2)
- That you want both LinkedIn and X posts

The social-post-writer skill will handle fetching brand context, drafting posts, and running
the brand voice cross-check. Follow its output format: each post as a labeled section with
platform, copy, hashtags (if any), and a UTM-tagged link.

Wait for the social-post-writer skill to complete and present its drafts to the user.

---

## Step 4 — Get user approval on the posts

Present the drafted posts clearly and ask the user:

> "Do these look good? Any changes before I submit the request?"

If the user wants edits, work with them to refine the posts. Once they confirm the posts
are good, proceed.

---

## Step 5 — Ask for the scheduling date

Ask the user:

> "When do you want these posts to be scheduled?"

Accept any natural-language date input (e.g., "next Tuesday", "April 22nd", "end of the
week") and convert it to `YYYY-MM-DD` format for Asana. This date will be used as both
the scheduling date in the task description AND the task due date.

---

## Step 6 — Create the Social Promotion Request task

Use `asana_create_task` to create a task on the social promotion board.

### Task fields

- `name`: `Social Promotion Requests (Linkedin and X) for <blog post title>`
  - Use the blog post title from Step 2 (without any `[Blog]` prefix)
- `project_id`: use `social_promotion_project_id` from config
- `due_on`: the scheduling date from Step 5 (YYYY-MM-DD format)
- `html_notes`: use the description template below

### Description template

The description must match the format used by the social promotion request form, which
dumps all fields into the task's description as plain text. Use `html_notes`:

```html
<body>
<strong>Name:</strong>
Matty Stratton

<strong>Email address:</strong>
matty@tigerdata.com

<strong>Due date:</strong>
[Scheduling date in "Mon DD, YYYY" format, e.g., "Apr 22, 2026"]

<strong>Copy:</strong>
[Full text of the approved social posts — LinkedIn and X versions, clearly labeled]
</body>
```

For the Copy section, paste in both the LinkedIn post(s) and X post(s) from the
social-post-writer output, labeled clearly:

```
--- LinkedIn ---
[LinkedIn post copy, including hashtags]

--- X ---
[X post copy]
```

If social-post-writer produced multiple LinkedIn angles or an X thread, include all of
them, each labeled.

---

## Step 7 — Comment on the original blog post card

After the social promotion request task is created, use `asana_create_task_story` to add
a comment to the original blog post task in the MKTG Content Calendar:

- `task_id`: the original blog post task GID (from Step 1)
- `html_text`: `<body>Social media posts requested — <a href="[PERMALINK_URL_OF_NEW_TASK]">[PERMALINK_URL_OF_NEW_TASK]</a></body>`

Use the `permalink_url` returned from the new task creation in Step 6.

---

## Summary

After everything's done, give the user a quick recap:

- Which blog post was processed (link to the original Asana card)
- That the social promotion request was created (link to the new task)
- The scheduled date
- That a comment was added to the original card

Keep it short — a few lines.

---

## Error handling

- **Published URL missing:** Ask the user to provide it directly (see Step 2).
- **social-post-writer fails or Tiger Den is unreachable:** Surface the error to the user.
  Do not continue to create the Asana task with no posts.
- **Task creation fails:** Tell the user what went wrong. Do not comment on the original
  card if the request task wasn't created.
- **Comment fails:** Let the user know — it's not critical, but they should manually add
  the link so the original card stays up to date.
