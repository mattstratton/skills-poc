---
name: weekly-content
platforms: [cowork, claude-code]
description: >
  Generates weekly content roundup Slack posts for Tiger Data. Queries Tiger Den for
  published content in a given date range, optionally enriches with Asana metadata,
  and drafts two Slack posts: one for #general and one for #sales-team. Posts drafts
  to #test-matty-posts for formatting review, then posts to the real channels on
  approval. Trigger when the user runs /weekly-content with a date range (e.g.
  /weekly-content Feb 23-27), or asks to generate the weekly content update, content
  roundup, or weekly Slack posts.
compatibility: >
  Requires Tiger Den and Slack MCP connectors. Asana connector is optional (used for
  enrichment with theme and series metadata).
references:
  - sales-stage-framework
  - customer-journey-map
  - brand-voice-guide
  - terms-glossary
---

# Weekly Content Skill

This skill generates the weekly content roundup posts for Tiger Data's `#general` and
`#sales-team` Slack channels. It uses Tiger Den as the primary source of truth for what
was published (content text, metadata, publish dates), with optional Asana enrichment
for editorial metadata like theme and series grouping.

The flow is always: **draft → DM for preview → get approval → post to channels.**
Never post to channels without explicit user approval.

---

## Before You Start — Load Context

This skill depends on personal context, reference docs, and runtime config. Load them before
doing any work.

### Personal context (memory layer)

Read `00 - System/Claude Context.md` from the Obsidian vault using `obsidian_get_file_contents`.
This is the memory layer — team, key people, shorthand, active projects. Internalize it
silently (don't summarize it back).

### Config values

Read `config.json` from the plugin root to get:
- `asana_project_id` — the Asana project for optional enrichment

### Reference docs

**First, check Tiger Den availability** using the process in `REFERENCES.md`: call
`list_voice_profiles()` (match by suffix — in Cowork, the tool has a UUID prefix). If it
returns results, Tiger Den is live and you can proceed to fetch reference docs.

Fetch from Tiger Den:
- **`sales-stage-framework`** (required for the #sales-team post) — contains the sales
  stages, BDR paths, and persona mapping used to write the "How to use" guidance.
- **`customer-journey-map`** (required for the #sales-team post) — maps the customer's
  buying journey to Tiger Data's sales stages, including context questions (gates) at each
  stage, disqualification criteria, team ownership, and the customer's internal framing.
  Use this to map content to the specific customer question it helps answer.
- **`brand-voice-guide`** (recommended) — tone and style rules for all TigerData content.
- **`terms-glossary`** (recommended) — correct product names, capitalization, terminology.

Fetch all four in one call:
```
get_marketing_context(slugs: ["sales-stage-framework", "customer-journey-map", "brand-voice-guide", "terms-glossary"])
```

**If Tiger Den is not available** (no tool with the `list_voice_profiles` suffix exists in
the available tools): stop and tell the user. This skill requires Tiger Den for both reference
docs and content queries — it can't run without it. Direct them to Settings → Connectors →
Den.tigerdata.com in Cowork, or `/setup` in Claude Code.

If either the sales-stage-framework or customer-journey-map docs can't be loaded, tell the
user and ask how to proceed. The #sales-team post depends on both for the stage-mapped and
journey-mapped guidance — without them, those sections will be generic and much less useful.

---

## Arguments

The user must provide a date range. Accepted formats:

- `/weekly-content Feb 23-27`
- `/weekly-content Feb 23 - Feb 27`
- `/weekly-content 2026-02-23 to 2026-02-27`

If no date range is provided, ask for one before proceeding. Don't assume the current week.

**Optional flags:**

- `nopreview` — Skip posting to #test-matty-posts; show drafts only in the conversation
- `nopost` — Generate and preview drafts, but don't offer to post to the real channels (draft-only mode)

---

## Step 1 — Query Tiger Den for Published Content

Use `list_content` to find content published in the date range. (In Cowork, match the tool
by its suffix — see `REFERENCES.md` for how to identify Tiger Den tools.) Tiger Den is the
primary source — if content is in Tiger Den with a `publishDate` in range, it was published.

**Query strategy:**

1. Call `list_content` and scan results for items where `publishDate` falls within the
   requested date range. Tiger Den returns items sorted by most recent, so paginate until
   you've passed the start of the date range.

2. Include all content types: `blog_post`, `youtube_video`, `case_study`, and any others
   that appear. The `contentType` field tells you what kind of piece it is.

3. Skip content types that aren't meaningful for the roundup (e.g. `website_content` items
   that are evergreen reference pages, not new publications).

**Extract from each qualifying item:**
- `title` — the content title
- `publishDate` — when it was published
- `url` — the canonical URL
- `author` — who wrote it
- `contentType` — blog_post, youtube_video, case_study, etc.
- `tags` — topic tags (useful for grouping and understanding coverage)
- `description` — the one-liner summary
- `id` — needed to fetch full text in Step 2

**Deduplication:** If the same content appears in multiple forms (e.g. a blog post and a
YouTube video covering the same topic with similar titles), group them. The blog/website
version is the primary entry; the video is a companion note, not a separate roundup item.
Use URL similarity, title overlap, and publish date proximity to detect duplicates.

---

## Step 2 — Get Full Content Text from Tiger Den

For each qualifying item, call `get_content_text` with the item's `id` to
retrieve the full body text. This is what you'll use to write summaries and pull snippets
for the sales-team post.

If `get_content_text` returns empty or fails for an item (e.g. a YouTube video with no
transcript indexed), note it and write the best summary you can from the `description`
and `tags` fields. Don't skip the piece.

---

## Step 3 (Optional) — Enrich with Asana Metadata

If the Asana connector is available, use it to add editorial metadata that Tiger Den
doesn't have. This step is optional — the skill works without it, but the output is
richer with it.

Use the `asana_project_id` from config.json.

Query `asana_search_tasks` with:
- `projects_any`: the project ID from config
- `due_on_after`: start of the date range
- `due_on_before`: end of the date range (inclusive)
- `opt_fields`: `name,due_on,custom_fields,custom_fields.name,custom_fields.display_value,custom_fields.text_value,custom_fields.enum_value`

**Match Asana tasks to Tiger Den items** by comparing the Published URL custom field
in Asana with the `url` from Tiger Den. Title matching is a fallback if URLs don't
align (common for YouTube shorts vs canonical URLs).

**Fields to extract from Asana (if matched):**
- `Theme` — from the Theme custom field (useful for framing)
- `Anchor Essay` — tells you what series a piece belongs to (critical for grouping)
- `Medium` — distribution channel info (e.g. "Tiger Data Blog / Website", "LinkedIn Blog")

If Asana is unavailable or a piece doesn't match, proceed without this metadata.
Use Tiger Den tags and title patterns for grouping instead.

---

## Step 4 — Generate Both Slack Posts

Generate two distinct posts: one for `#general` and one for `#sales-team`. These are different
audiences with different needs. Don't just copy one to the other.

### Grouping logic

Before writing, check whether any pieces belong to the same content series. Use (in order
of reliability):
1. Asana `Anchor Essay` field (if available from enrichment)
2. Tiger Den tags overlap
3. Thematic similarity from titles and descriptions

If multiple pieces are clearly part of a series, introduce them as a series rather than
treating each as isolated.

### `#general` post

Audience: the whole company — engineers, product, finance, ops. Not assumed to be in sales.
Tone: informative, brief, no sales framing.

Format:

```
📚 **New Content This Week — [Date Range]**

[If all pieces are part of a series, one line introducing the series theme.]

1️⃣ **[Title]** ([Content Type] · [Date])
[2-3 sentence summary of what the piece covers and why it's interesting. Plain, factual.]
[Published URL]

2️⃣ **[Title]** ([Content Type] · [Date])
[Same format]

[Repeat for each piece]
```

Rules:
- Keep summaries factual and direct — what the piece is about, not why someone should care for sales reasons
- No "How to use" section
- No stage mapping
- If a piece is a video, note it's a quick watch (give a rough duration if you can infer it from Tiger Den)
- If all pieces are from the same author, you can group the author credit at the top instead of repeating per item

### `#sales-team` post

Audience: AEs, SAs, BDRs, and sales leadership. Assume they know the sales process
and the customer journey framework.

Format:

```
📚 **New Content This Week — [Date Range]**

[1-2 sentence framing of why this week's content matters for the team — what theme it hits,
what customer conversation it enables.]

━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ **[Title]**
[Content Type] · [Date] · [Author]

**Summary:** [3-4 sentences. What the piece argues, what evidence/framing it uses, what the
reader takes away.]

**Snippet:** _"[A pull quote from the content — pick something punchy that a rep could actually
say to a prospect to frame the problem. Under 25 words.]"_

**Customer journey:** [Which customer question does this content help answer? Use the
customer-journey-map reference doc. Frame it from the customer's perspective, e.g. "Helps
the customer recognize they have a timeseries ingest bottleneck" (Stage 0) or "Gives the
customer evidence that Tiger Data can fix their Postgres bottleneck" (Stage 1).]

**How to use:**
• **Stage N ([Name]):** [2-4 sentences of stage-mapped guidance using the sales-stage-framework
and customer-journey-map reference docs. Be specific — what kind of prospect, what moment in
the conversation, what gate question it helps answer, and what it helps them do. Don't just
say "good for Stage 1" — say why and how.]

━━━━━━━━━━━━━━━━━━━━━━━━

[Repeat for each piece]
```

Rules:
- The "Customer journey" and "How to use" sections are the most important parts of the sales-team post. Spend the most effort here.
- Only map to stages that genuinely apply — don't force all stages for every piece
- Frame the customer journey mapping from the customer's perspective using the gate questions from the customer-journey-map doc
- Reference BDR Paths where relevant for top-of-funnel content (from the stage framework doc)
- Reference prospect personas where the content is persona-specific (from the stage framework doc)
- If pieces are a series, note how they sequence — which to share first, which is the deeper follow-up
- Use Slack markdown: `**bold**` for headers and labels (double asterisks), `_italic_` for snippets, `━━━` Unicode box-drawing characters for section dividers (Slack's `---` doesn't render as a horizontal rule)

---

## Step 5 — Post Drafts to Preview Channel

Post both drafts to `#test-matty-posts` as separate messages so the user can check how they
render in Slack (formatting, length, link unfurls). Use `slack_search_channels` to find the
channel ID — don't hardcode it. Do not post to `#general` or `#sales-team` yet.

Post the `#general` draft first, then the `#sales-team` draft as a separate message, so each
can be evaluated independently.

Also show both drafts in the Claude conversation so the user can read and respond without
switching to Slack.

After posting, say: "Drafts posted to #test-matty-posts so you can check formatting. Let me
know what to change, or say 'post it' when you're ready and I'll send both to the real channels."

---

## Step 6 — Iterate on Feedback

If the user requests changes, make them and show the updated draft(s) in the conversation.
Re-post to `#test-matty-posts` only if the user asks to see the updated version in Slack
(to check rendering). Don't re-post on every small edit — that gets noisy.

---

## Step 7 — Post to Channels

When the user approves (says "post it", "looks good", "ship it", or similar):

1. Post the `#general` draft to `#general`
2. Post the `#sales-team` draft to `#sales-team`
3. Confirm in the conversation: "Posted to both channels."

**To find channel IDs:** Use `slack_search_channels` with "general" and "sales-team" to get
the correct channel IDs before posting. Don't hardcode channel IDs.

**Never post to channels without explicit user approval.** If the user goes quiet after the
DM step, do nothing. Wait for confirmation in the conversation.

---

## Edge Cases

**No published content found in the date range:**
Tell the user no content in Tiger Den matches the date range. Confirm the range and offer
to check a different one. If Asana is available, mention you can cross-check there in case
content was published but not yet indexed in Tiger Den.

**Content in Tiger Den but not in Asana (or vice versa):**
Tiger Den is the primary source. If a piece exists in Tiger Den with a valid publish date
and URL, include it in the roundup regardless of its Asana status. If something is in Asana
but not Tiger Den, mention it to the user — it may not have been indexed yet.

**YouTube videos with no transcript in Tiger Den:**
Use the `description` field and tags to write the summary. Note it's a video and give a
rough sense of length if you can infer it. Don't skip it.

**Multiple Tiger Den entries for the same piece:**
Group under one entry. Use the blog/website URL as the primary. Mention other formats
(e.g. "also available as a YouTube video") as a note, not a separate item.
