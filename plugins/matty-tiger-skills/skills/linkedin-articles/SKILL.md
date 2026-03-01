---
name: linkedin-articles
platforms: [cowork, claude-code]
description: >
  Finds recent articles relevant to TigerData's ICP and drafts LinkedIn posts using the user's
  Tiger Den voice profile. Use this skill when the user runs /linkedin-articles or asks for daily
  article picks, LinkedIn post drafts, content ideas for social media, or anything about finding
  articles to share on LinkedIn. Also trigger when the user asks things like "what should I post
  this week," "find me something to share," "any good articles today," "LinkedIn content,"
  "draft me a post about [topic]," or any variation of wanting content for LinkedIn or social
  sharing related to databases, IoT, Postgres, or the developer ecosystem. Always use this skill
  for these requests — don't attempt to do it from scratch without it.
compatibility: >
  Requires Tiger Den (for voice profile) and Slack (for output delivery).
  Optionally uses web search for article discovery.
references:
  - matty/topic-buckets
  - matty/fallback-voice-matty
  - brand-voice-guide
---

# LinkedIn Articles Skill

This skill finds fresh articles relevant to TigerData's ICP and drafts LinkedIn posts using the
user's voice profile from Tiger Den — both a subtle version and a branded version — then sends
the results to the user via Slack DM.

## Before You Start — Load Context

This skill depends on reference docs and runtime config. Load them before doing any work.

### Config values

Read `config.json` from the plugin root to get:
- `slack_user_id` — where to DM the article picks and draft posts

### Reference docs

Fetch from Google Drive using the process in `REFERENCES.md`:
- **`matty/topic-buckets`** (required) — defines the topic buckets to search across,
  including search guidance, competitive framing, and what qualifies as a good article
  for each bucket.
- **`matty/fallback-voice-matty`** (fallback only) — voice profile used when Tiger Den
  is unavailable. Only fetch this if Tiger Den can't be reached.
- **`brand-voice-guide`** (recommended) — general tone and style rules, banned words,
  and formatting conventions.

---

## Arguments

The user can pass optional arguments after `/linkedin-articles`. These modify the workflow:

- **Bucket names** — Only search specific buckets. The available bucket names are defined
  in the `matty/topic-buckets` reference doc. Pass the bucket slug (e.g. `iot`, `postgres`,
  `competitive`) to restrict the search.
- **`top1`** — Run the full search and scoring, but only draft posts for the single highest-scored article.
- **`noslack`** — Skip the Slack DM step. Output everything in the Cowork session instead.

Arguments can be combined: `/linkedin-articles postgres top1 noslack` would search only the Postgres bucket, return one article, and output inline.

If no arguments are provided, run the full workflow across all buckets.

## Workflow

### Step 1 — Pull Voice Profile from Tiger Den

Before drafting anything, use the Tiger Den connector to retrieve the current user's voice profile.
Look up the user's name to find their associated profile. This ensures posts always reflect the
latest version of their voice, not a cached or assumed version.

If the user's voice profile can't be found by name, list the available voice profiles from Tiger
Den and let the user pick one. Include a final option like "None of these — use the default voice"
which falls back to the `matty/fallback-voice-matty` reference doc.

If Tiger Den is completely unavailable (connector error, not connected, etc.), fetch the
`matty/fallback-voice-matty` reference doc from Drive and tell the user you're using it so
they know. If Drive is also unavailable, use a generic TigerData developer voice (direct,
no fluff, no corporate speak) and note the degradation.

### Step 2 — Search for Articles

Search the web for **4-5 articles published in the last 7 days** across the topic buckets
defined in the `matty/topic-buckets` reference doc.

Aim for at least one article per bucket if possible, but quality beats coverage.

**Where to look**: Dev blogs, Hacker News, The New Stack, InfoQ, personal engineering blogs,
database-focused publications (like Percona's blog, Planet PostgreSQL), and industry outlets
covering manufacturing/energy tech. Twitter/X threads from practitioners can work too if
they're substantive. Avoid vendor marketing blogs unless they contain real technical depth.

**Search quality bar**: Prioritize articles with real technical substance or genuine practitioner
perspective. Skip PR fluff, press releases, and anything that reads like it was written for SEO.

**Dry weeks**: Some buckets won't always have fresh content. That's fine. Don't force bad articles
into the results just to fill a bucket. If a bucket has nothing worth sharing this week, say so
in the output and move on. Three strong articles from two buckets beats five mediocre ones
spread across three.

### Step 3 — Score and Rank Articles

For each article, assess **commentary value** — how much genuine perspective can the user add
beyond "here's an interesting article"? Score 1-5:

- **5** — Strong opinion opportunity, directly relevant to TigerData's ICP, clear POV available
- **4** — Good hook, relevant problem space, easy to riff on
- **3** — Interesting but niche, or requires more context to be useful
- **2** — Tangentially relevant, thin commentary value
- **1** — Skip

Drop anything scored 1-2. Present remaining articles ranked highest to lowest.

### Step 4 — Draft LinkedIn Posts

For each article (score 3+), write two post variants using the user's voice profile:

**Variant A — SUBTLE**
- No brand mentions (no TigerData, TimescaleDB, Tiger Cloud)
- Developer-to-developer tone — sharing something genuinely worth reading
- Lead with the insight or problem, not "I found this article"
- 150-250 words is the sweet spot
- End with a question or observation that invites discussion, not a CTA

**Variant B — BRANDED**
- Same voice and directness — still sounds like the author, not a press release
- Works in TigerData, TimescaleDB, or Tiger Cloud only where it fits naturally
- The connection to TigerData should feel earned, not forced
- If the connection is a stretch, say so and keep it minimal
- Same length guidance as Variant A

**Links**: Every post must include the article URL. Place it naturally in the body of the post
where the reader would want to click through (after the hook, not buried at the end). LinkedIn
renders link previews, so the URL placement matters for how the post looks in-feed.

**Hashtags**: End each post with 3-5 relevant hashtags. Pick ones that actually have traffic on
LinkedIn (e.g., #PostgreSQL, #IoT, #TimeSeries, #DevOps, #DataEngineering). Skip obscure or
overly specific tags that nobody follows. Don't use hashtags inline in the post body, only at
the end. If no hashtags feel natural for a particular post, skip them rather than forcing it.

**Voice rules for both variants** (supplement with Tiger Den profile and brand-voice-guide):
- Short sentences. No bullet walls in the post itself.
- No em-dashes
- Never use: "genuinely," "honestly," "straightforward," "dive in," "in the ever-evolving landscape," "it's worth noting"
- No headers inside the post
- Avoid hollow openers like "Hot take:" or "Unpopular opinion:" unless the take actually earns it
- Dry humor is fine. Forced enthusiasm is not.
- If the article is dumb or wrong, say so — that's also a post
- If a draft leans on a well-worn framing ("just use Postgres," "hot take," etc.), flag it in
  the output so the user can decide whether to rework the hook. The user may have recently
  published something with a similar angle.

### Step 5 — Send to Slack

Use the `slack_user_id` from config.json.

Send the full output as a DM to this user ID — not to a channel. Never post drafts to
a public or shared channel; the drafted posts are for the author to review and edit before
they go anywhere public.

Format the DM clearly. The Slack connector uses standard markdown, not Slack's native mrkdwn.
This means:

- `**text**` (double asterisks) for bold
- `_text_` for italic
- Plain URLs are clickable (no need for special link syntax)
- Blank lines for visual separation between sections (no `---` or other divider hacks)

Template:

```
**LinkedIn Article Picks — [Today's Date]**

**#1 — [ARTICLE TITLE]**
[URL]

Topic: [Bucket name] | Commentary value: [X/5]
Why: [1 sentence on why it's worth sharing]

**Subtle:**
[Post text]

**Branded:**
[Post text]


**#2 — [ARTICLE TITLE]**
[URL]

[Repeat same structure]
```

Keep it scannable — the user should be able to skim the DM and grab a post in under a minute.
Use double blank lines between articles for visual breathing room.

If the Slack DM fails, output the full result in the Cowork session instead and let the
user know.
