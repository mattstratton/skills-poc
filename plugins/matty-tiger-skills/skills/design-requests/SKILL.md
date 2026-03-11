---
name: design-requests
platforms: [cowork]
description: >
  Create blog thumbnail design requests in Asana for upcoming blog posts. Searches the
  MKTG Content Calendar for [Blog] tasks assigned to you, shows the list for confirmation,
  then creates design request tasks in the Marketing Design Requests project with the
  correct format, and comments back on the original card. Trigger when the user runs
  /design-requests or says "create design requests", "submit thumbnail requests",
  "blog thumbnails", "design request for blog", or "I need thumbnails for my posts".
compatibility: >
  Requires Asana MCP connector. The user must have access to both the MKTG Content
  Calendar FY27 project and the Marketing Design Requests project in Asana.
references: []
---

# Design Requests Skill

This skill automates the creation of blog thumbnail design requests in Asana. It bridges
two projects: the MKTG Content Calendar (where blog posts live) and the Marketing Design
Requests project (where the design team picks up work).

The flow is always: **search → present → confirm → create → comment back.** Never create
a design request without explicit user approval.

---

## Before You Start — Load Context

### Personal context (memory layer)

Read `00 - System/Claude Context.md` from the Obsidian vault using `obsidian_get_file_contents`.
This is the memory layer — team, key people, shorthand, active projects. Internalize it
silently (don't summarize it back).

### Config values

Read `config.json` from the plugin root to get:
- `asana_project_id` — the MKTG Content Calendar FY27 project
- `design_requests_project_id` — the Marketing Design Requests project
- `design_requests_section_id` — the "Requests" section within that project

### Other constants

These are specific to the Marketing Design Requests project and don't change:
- **Type custom field (Blog):** field GID `1211314814025776`, enum option GID `1211314814025780`
- **Design request form URL:** `https://form.asana.com/?k=rMVzx68ZHPz5yv6yHwNqkw&d=341543771842144`

### User identity

The user's name is **Matty Stratton** and email is **matty@tigerdata.com**. These go into
the design request description.

---

## Step 1 — Find Blog Posts Needing Thumbnails

### 1a. Determine the date range

The user may specify a date range (e.g., "next two weeks", "through end of March"). If
they don't, default to **today through 30 days out**.

### 1b. Search the Content Calendar

Use `asana_search_tasks` to find blog posts:
- `projects_any`: use the `asana_project_id` from config
- `assignee_any`: "me"
- `completed`: false
- `text`: "[Blog]"
- `due_on_after`: start of range (today)
- `due_on_before`: end of range
- `opt_fields`: "name,due_on,notes,permalink_url"

### 1c. Parse draft links

For each task returned, check the `notes` field for a draft link. The pattern is:
```
draft link: https://docs.google.com/...
```
The draft link can appear anywhere in the notes. Extract it by looking for a line
containing `draft link:` and grabbing the URL that follows.

If no draft link is found in the notes, mark this task as **"needs draft link"**.

### 1d. Filter out tasks that already have design requests

Before presenting the list, check whether a design request already exists for each blog
post. Use `asana_get_stories_for_task` on the original blog task and look for a comment
containing "thumbnail request submitted". If found, this blog post already has a design
request — skip it unless the user explicitly asks to recreate it.

---

## Step 2 — Present the List and Get Approval

Show the user a clean list of blog posts that need design requests. For each one, show:

- **Task name** (without the `[Blog]` prefix in the display)
- **Due date** from the Content Calendar
- **Draft link status:** either the link itself or "No draft link — will ask before creating"
- **Design request due date:** one day before the blog post's due date

Example presentation:

```
I found 3 blog posts that need thumbnail design requests:

1. Why Adding More Indexes Eventually Makes Things Worse
   Due: Mar 11 → Design request due: Mar 10
   Draft: https://docs.google.com/document/d/1j8B...

2. The Best Time to Migrate Was at 10M Rows
   Due: Apr 7 → Design request due: Apr 6
   Draft: No draft link found — I'll ask before creating

3. Five Warning Signs Your Database Needs Different Architecture
   Due: Apr 8 → Design request due: Apr 7
   Draft: No draft link found — I'll ask before creating

Want me to create design requests for all of these, or just specific ones?
```

Wait for the user to confirm which tasks to process.

---

## Step 3 — Handle Missing Draft Links

For any confirmed task that has **no draft link**, ask the user for it before creating
the design request:

```
"The Best Time to Migrate Was at 10M Rows" doesn't have a draft link in its Asana card.
Can you paste the Google Doc link? (Or say "skip" to create the request without one.)
```

If the user provides a link, use it in the design request description. If they say "skip",
create the request without a draft link but note in the description that no draft was
available at time of submission.

---

## Step 4 — Create Design Request Tasks

For each approved blog post, create a task in the Marketing Design Requests project.

### Task creation

Use `asana_create_task` with:
- `name`: `Blog Thumbnail - [Blog Post Title]`
  - Strip the `[Blog]` prefix from the original title
  - Example: `Blog Thumbnail - Why Adding More Indexes Eventually Makes Things Worse`
- `project_id`: use `design_requests_project_id` from config
- `section_id`: use `design_requests_section_id` from config (Requests section)
- `due_on`: one day before the blog post's due date (YYYY-MM-DD format)
- `custom_fields`: `{"1211314814025776": "1211314814025780"}` (Type = Blog)
- `html_notes`: use the description template below

### Description template

The description must match the format used by the Marketing Design Requests form. Use
`html_notes` to create the formatted description:

```html
<body>
<strong>Request title:</strong>
Blog Thumbnail - [Blog Post Title]

<strong>Name:</strong>
Matty Stratton

<strong>Email address:</strong>
<a href="mailto:matty@tigerdata.com">matty@tigerdata.com</a>

<strong>Due date:</strong>
[Due date in "Mon DD, YYYY" format, e.g., "Mar 10, 2026"]

<strong>Level of urgency:</strong>
Medium (4-10 day turnaround)

<strong>Request type:</strong>
Blog thumbnail and/or diagram(s)

<strong>Project description and specs:</strong>
Please create a blog thumbnail image for this upcoming post. We need the image in both:
• Blog thumbnail size (standard)
• LinkedIn article header size

[If draft link available:]
Draft copy: <a href="[DRAFT_URL]">[DRAFT_URL]</a>

[If no draft link:]
Draft copy not yet available — will follow up when ready.

———————————————
This task was submitted through <strong>Marketing Design Requests</strong>
<a href="https://form.asana.com/?k=rMVzx68ZHPz5yv6yHwNqkw&amp;d=341543771842144">https://form.asana.com/?k=rMVzx68ZHPz5yv6yHwNqkw&amp;d=341543771842144</a>
</body>
```

### After each creation

After successfully creating a design request task, **comment on the original blog post
task** in the Content Calendar using `asana_create_task_story`:

- `task_id`: the original blog post task GID
- `html_text`: `<body>Thumbnail request submitted — <a data-asana-gid="[NEW_TASK_GID]"/></body>`

This creates a linked comment that lets anyone on the blog post card jump straight to
the design request.

---

## Step 5 — Summary

After all design requests are created, present a summary:

```
Done! Created 3 design requests:

1. Blog Thumbnail - Why Adding More Indexes Eventually Makes Things Worse
   → Due Mar 10 | Link: [Asana link]

2. Blog Thumbnail - The Best Time to Migrate Was at 10M Rows
   → Due Apr 6 | Link: [Asana link]

3. Blog Thumbnail - Five Warning Signs Your Database Needs Different Architecture
   → Due Apr 7 | Link: [Asana link]

Comments added to all original cards in the Content Calendar.
```

---

## Edge Cases

**No blog posts found:**
If the search returns no `[Blog]` tasks in the date range, say so and ask if the user
wants to widen the range or check a different assignee.

**Blog post due tomorrow or today:**
If the blog post is due tomorrow, the design request would be due today — flag this to
the user as potentially too tight and ask if they want to proceed. If it's due today,
the design request due date would be yesterday — flag this clearly and let the user
decide on a due date.

**All tasks already have design requests:**
If every blog post in the range already has a "thumbnail request submitted" comment,
tell the user and ask if they want to recreate any.

**Asana rate limits or errors:**
If task creation fails, report which ones succeeded and which failed. Don't silently
drop failures. Offer to retry the failed ones.

**User wants to customize the description:**
If the user asks to change any part of the description template (urgency level, request
type, additional specs), accommodate it for that run. Don't permanently change the
template in the skill.

**"Submit design requests / create thumbnails" subtasks:**
The Content Calendar may have subtasks with this name under blog posts. These are
reminders, not actual blog tasks. The skill should only process top-level tasks whose
name starts with `[Blog]`. Use `is_subtask: false` in the search if needed to filter
these out.
