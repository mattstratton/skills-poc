---
name: kol-engagement-update
platforms: [cowork, claude-code]
description: >
  Scrape engagement numbers (reactions + comments) on Tiger Data KOL posts and record
  them in Tiger Den. Uses Chrome browser automation against the user's real logged-in
  session — no LinkedIn API needed. Default window is the last 4 weeks. POC scope is
  LinkedIn only; X/YouTube/other platforms are stubbed for later. Trigger when the
  user runs /kol-engagement-update, /kol-update, says "update KOL engagement",
  "scrape KOL post engagement", "refresh KOL numbers", "update LinkedIn engagement
  for KOLs", "how are our KOL posts doing", or asks to refresh social_engagements
  on KOL posts in Tiger Den. Accepts an optional window like "/kol-engagement-update 2w"
  or "/kol-engagement-update last 6 weeks".
compatibility: >
  Requires the claude-in-chrome MCP extension with Chrome running and LinkedIn logged in.
  Requires Tiger Den MCP with kols-contributor or kols-admin access (write actions need
  it). Read-only on LinkedIn — never likes, comments, reposts, or DMs.
references:
  - linkedin-comments  # similar Chrome-scraping pattern; consult its 5c selectors if LI ships a UI change
---

# KOL Engagement Update Skill

This skill updates the `social_engagements` field on Tiger Den KOL posts by visiting each post in Chrome, reading the reactions and comments counts off the page, summing them, and writing the total back via `manage_kols(action: "record_performance")`. It's read-only on the social platform — only Tiger Den gets written to.

The flow is always: **fetch posts in window → for each, navigate → extract → record_performance → human-paced pause → repeat.** Never click, like, comment, or submit anything on LinkedIn.

---

## Why Chrome automation (and why pacing matters)

LinkedIn's APIs are gated and don't expose post-level engagement counts to non-Partners. Driving the user's real Chrome session matches the same IP, fingerprint, and user-agent as their normal browsing — the lowest-risk option. The cost is fragility against UI changes and a hard requirement to **act human**: serial navigations, randomized pauses, no parallel tabs, no scrolling beyond what's needed to read the social counts bar (which is in the initial viewport for most posts).

If you ever feel the urge to fan out tabs in parallel "to go faster" — don't. The whole skill exists at the user's discretion specifically because tab-by-tab is the safe option.

---

## What gets written to Tiger Den

For each post in scope, one call:

```
manage_kols(
  action: "record_performance",
  engagement_id: "<engagement uuid>",
  post_id: "<post uuid>",
  social_engagements: <reactions + comments>,
)
```

`record_performance` creates a new performance snapshot each run — it does **not** update the previous one. That's intentional: it gives Tiger Den a history. The post's display value will reflect the most recent snapshot.

**Definition of "engagement" for this skill: reactions + comments. Reposts are NOT counted** (per user direction). Comment-level reactions and replies are NOT counted (we only look at the top-level social counts bar on the post).

If the user asks to change the definition (e.g. "include reposts"), do it for that run and note the change in the summary — but don't change the default.

---

## Before You Start — Load Context

### Config values

Read `config.json` from the plugin root if you need user-scoped values. This skill doesn't currently rely on any user-specific config, but if you add e.g. a window override or a specific KOL filter, store it there.

### Load tools

Both Tiger Den and claude-in-chrome tools are deferred. Load them via ToolSearch before anything else:

```
ToolSearch with query:
  "select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__find,mcp__claude-in-chrome__list_connected_browsers"

ToolSearch with query:
  "select:mcp__<tiger-den-prefix>__manage_kols"
```

The Tiger Den server prefix varies per session — find it from `list_connectors` or the available_skills system reminder. The action name is always `manage_kols`.

If either load fails, tell the user what's missing and stop. Don't try to proceed with half the toolchain.

### Marketing pre-flight

Per Tiger Data convention, call `marketing-preflight` (if present in the available skills list) to confirm Tiger Den connectivity and log attribution. Skip silently if the skill isn't loaded.

---

## Step 1 — Parse the time window

Default window: **last 4 weeks** (28 days).

Accept overrides like `/kol-engagement-update 2w`, `/kol-engagement-update last 6 weeks`, `/kol-engagement-update 30d`. Convert to an absolute `cutoff_date = today - N days`. Hold this for filtering in Step 3.

If the user's request is ambiguous, default to 4 weeks and mention it: "Pulling KOL posts published in the last 4 weeks — say a different window if you want a different range."

---

## Step 2 — Confirm Chrome and LinkedIn session

Call `mcp__claude-in-chrome__list_connected_browsers`. If no browser is connected:

> "Can't reach Chrome. Make sure the claude-in-chrome extension is running and you have Chrome open, then run the skill again."

Stop. Don't proceed.

Then call `tabs_context_mcp` to see what's open. If a LinkedIn tab exists, reuse it. Otherwise call `tabs_create_mcp` and navigate to `https://www.linkedin.com/feed/` (a low-friction page that confirms auth).

If LinkedIn shows a login wall on navigate, pause and ask the user to log in:

> "LinkedIn is asking me to log in. Sign in in the tab and say 'ready' when I should continue."

Do not proceed past this point if extraction returns nothing — that means we're either logged out or rate-limited.

---

## Step 3 — Fetch KOL engagements from Tiger Den

Pull KOL engagements in stages most likely to have live posts. Start with `published`. If the user signals they also want approved/in-flight posts (rare), add `approved`.

```
manage_kols(action: "list_engagements", stage: "published", limit: 100, offset: 0)
```

**Pagination warning — important.** The list_engagements response includes a `total` field. The current Tiger Den implementation can return responses well over 100k characters even with limit=100, which exceeds the harness token limit and gets dumped to a file. When this happens, do **not** try to read the file inline — delegate to a subagent (via the Agent tool) with explicit instructions to extract only:

- post `id`, `engagementId`, `kolId`, `platform`, `url`, `publishDate`, `social_engagements`
- the engagement `title`

Tell the subagent the exact target window (cutoff date) and ask for a flat list of matching posts. Keeps your main context clean.

Paginate by bumping `offset` until you've covered `total` entries. Within each page, filter posts where:

- `platform == "linkedin"` (POC scope — see "Platform extensibility" at the bottom for X/YouTube)
- `publishDate != null` AND `publishDate >= cutoff_date`
- `url != null` AND `url` starts with `https://www.linkedin.com/`

Track separately, for the end-of-run summary:

- **skipped (null url)** — can't scrape, but worth surfacing to the user
- **skipped (null publishDate)** — date-filter blind spot; user may want to backfill the date and re-run
- **skipped (other platform)** — not relevant to LinkedIn POC

---

## Step 4 — Confirm with the user before scraping

Show the in-scope list before going to LinkedIn. Format:

```
Found 9 LinkedIn KOL posts published in the last 4 weeks.

  1. Jan Siekierski (2026-05-13) — Freeman & Forrest May 2026
  2. Hariharnath (2026-04-20) — Freeman & Forrest April 2026
  ...

Skipping 3 posts:
  - 2 posts have no URL recorded (Hong Wei [2026-04-08], Sahn Lam [2026-04-12])
  - 1 post has no publishDate (Ronald Van Loon — "IIoT 2026 KOL campaign")

Ready to scrape? This will open each post sequentially in Chrome with a 5–15s pause
between, total runtime ~2 minutes.
```

Wait for confirmation. If they say no, stop. If they want to narrow further ("just Freeman & Forrest"), let them.

---

## Step 5 — Scrape and record (the main loop)

For each in-scope post, in order:

### 5a. Navigate

Call `navigate` with the post URL on the existing tab. Reuse one tab for the whole run — don't open a new tab per post.

### 5b. Find the social counts bar

Use `find` with this exact query (it's stable against minor LI updates):

```
social counts bar — reactions count and comments count buttons on the main post
(e.g. '147 reactions', 'N comments on someone's post', or 'X and N others')
```

Two buttons matter:

- **Reactions button** — text varies:
  - `"147 reactions"` — clean integer (common above ~20 reactions, sometimes with K/M suffix)
  - `"Christina Pacheco, MBA and 11 others"` — name + count (common below ~20 reactions)
  - `"Christina Pacheco"` alone — 1 reaction
- **Comments button** — text is always `"N comments on <Author>'s post"` when N >= 1. **When there are 0 comments, the button simply doesn't exist** — treat absence as 0.

There's also a Reposts button. **Ignore it** per definition.

### 5c. Parse the counts (pseudo-code)

```
parseReactions(text):
  text = text.trim()
  if matches /^([\d.,]+[KMkm]?)\s+reactions?$/:
    return parseSuffixed(group 1)   // e.g. "1.2K" → 1200
  if matches /\band\s+(\d+)\s+others?$/:
    return 1 + int(group 1)         // "Name and 11 others" → 12
  if non-empty (just a name):
    return 1
  else:
    return 0

parseComments(text):
  if text matches /^(\d+)\s+comments?\s+on\b/:
    return int(group 1)
  return 0  // button absent or unparseable

total = reactions + comments
```

If parsing fails on a post (e.g. text is in a weird format you can't match), don't guess. Skip the post and add it to the "manual review needed" bucket in the final report.

### 5d. Record the performance

```
manage_kols(
  action: "record_performance",
  engagement_id: post.engagementId,
  post_id: post.id,
  social_engagements: total,
)
```

`record_performance` requires **both** engagement_id and post_id — it will reject if you pass only one. This is a known Tiger Den ergonomics gap (see `IMPROVEMENT_IDEAS.md` for the open ticket idea).

Capture the response — it includes the new performance record id and `recorded_at`. You'll show this in the summary.

### 5e. Human pace

Between posts, pause 5–15 seconds randomized. The natural latency of `find` + `record_performance` already gives ~5–10s, so you don't need an explicit sleep in most cases — just **don't batch navigates**. If you find yourself wanting to send multiple navigate actions in a single browser_batch, stop. One post at a time.

Optional explicit jitter via `javascript_tool`:

```javascript
await new Promise(r => setTimeout(r, 5000 + Math.floor(Math.random() * 10000)));
```

But honestly, the natural pace works. The point is: never do parallel tabs, never blow through 10 posts in 30 seconds.

---

## Step 6 — Final report

Show a summary table grouped by KOL with the values you wrote, plus skip reasons. Format:

```
✅ Updated 9 LinkedIn KOL posts (last 4 weeks)

| KOL                  | Reactions | Comments | Total | Recorded |
|----------------------|-----------|----------|-------|----------|
| Jan Siekierski       |        12 |        8 |    20 | ✓        |
| Hariharnath          |        71 |        6 |    77 | ✓        |
| Andreas Kretz        |       114 |       12 |   126 | ✓        |
| Khuyen Tran          |       107 |        4 |   111 | ✓        |
| Abhishek Veeramalla  |       429 |        7 |   436 | ✓        |
| Data Engineer Things |        25 |        0 |    25 | ✓        |
| Melvin Francis       |        33 |        1 |    34 | ✓        |
| 4.0 Solutions        |        29 |        6 |    35 | ✓        |
| Justin Mitchel       |        54 |        7 |    61 | ✓        |

Total engagement across run: 925

Skipped (3):
  • Hong Wei — null url
  • Sahn Lam — null url
  • Ronald Van Loon — null publishDate
```

If the user wants to dig into a specific post (e.g. "what was Abhishek's again?"), the data is in the conversation — answer from memory.

---

## Edge cases

**Login wall mid-run.** If `find` returns no social-counts buttons on a post, check the page title or look for a login form. If logged out, pause and ask the user to re-auth before continuing.

**LinkedIn DOM change.** If `find` consistently returns garbage or no matching buttons across multiple posts, LinkedIn shipped a UI update. Fail loudly:

> "Find isn't returning reactions/comments buttons on Post #N. LinkedIn may have updated their UI. Want me to try a different selector or stop here?"

Don't silently retry forever — that's how skills rot. Document what the buttons currently look like and update Step 5b's query.

**0 reactions.** If neither a "N reactions" button nor a "Name and N others" button is found, treat reactions as 0. Combined with 0 comments → total is 0. Still write it (so Tiger Den knows we checked).

**A post returns counts that look obviously wrong** (e.g. millions). LinkedIn's anti-bot may be showing a different layout. Cap at a sanity threshold (say 50,000) and ask the user to verify before writing.

**Same post recorded twice in one day.** `record_performance` creates a new snapshot every call — re-running the skill in the same day will leave two snapshots from today. That's fine; Tiger Den will use the latest. No dedupe logic needed.

**A Tiger Den engagement has `kol: null`** (multi-KOL agency bucket like Freeman & Forrest). Posts inside have their own `kolId`. Use the post's own kolId when displaying the KOL name — you may need to call `manage_kols(action: "get", id: kolId)` for the display name if the engagement-level kol object is null.

**The user passes a window of 0 days or a future date.** Default to 4 weeks and warn them.

**Chrome extension disconnects mid-run.** Tell the user which post number you were on and what's left, then stop. They can re-run with the remaining posts after Chrome is back.

---

## Platform extensibility (post-POC)

This skill is LinkedIn-only for v1. To add a platform:

1. **Add a platform handler** in Step 5b. The accessibility tree pattern (`find` query + count parsing) is platform-specific. Suggested handlers:
   - **X / Twitter:** look for "N likes", "N replies", "N reposts" — main post engagement is under a status URL. Quote-tweets are separate.
   - **YouTube:** look for view count, likes, and comment count. Skill should probably target the video page directly (`youtu.be/...` or `youtube.com/watch?v=...`).
   - **Other:** punt and skip; the user can manually update.

2. **Update Step 3's filter.** Currently `platform == "linkedin"`. Generalize to a `target_platforms` array (default `["linkedin"]`).

3. **Test the find queries** before shipping — X and YouTube DOMs change more often than LinkedIn's.

4. **Anti-bot caution still applies on X.** Tab-by-tab, human-paced, read-only.

5. **YouTube has a public Data API** — for that platform, a real API call may be safer than browser scraping. Consider that for v2.

---

## What this skill deliberately does NOT do

- **Does not click "like" or comment on anything.** Read-only.
- **Does not write to LinkedIn in any way.** Same reason `linkedin-comments` is draft-only.
- **Does not scroll the post page beyond initial viewport.** The social counts bar is above the fold on every post.
- **Does not open comment threads.** Top-level counts only.
- **Does not count reposts.** Per user direction. Reactions + comments only.
- **Does not run on a schedule.** Requires Chrome + extension to be active — interactive only. (If scheduling is requested later, consider a separate skill that runs from a server-side context and uses an API rather than browser automation.)
- **Does not dedupe across runs.** Running daily will create one new performance snapshot per post per day. That's the desired behavior.
