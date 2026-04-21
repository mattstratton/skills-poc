---
name: linkedin-comments
platforms: [cowork, claude-code]
description: >
  Surface recent comments on Matty's own LinkedIn posts and draft replies in his voice
  for manual pasting back to LinkedIn. Uses Chrome browser automation to read the activity
  page (no LinkedIn API access required) and Tiger Den for voice matching. Draft-only —
  never auto-posts. Trigger when the user runs /linkedin-comments, says "check my LinkedIn
  comments", "any new LinkedIn comments?", "draft replies to my LinkedIn comments",
  "review my LinkedIn engagement", or asks for help responding to comments on recent
  LinkedIn posts. Accepts an optional day window like "/linkedin-comments 14d".
compatibility: >
  Requires the claude-in-chrome MCP extension with Chrome running and LinkedIn logged in.
  Requires Tiger Den MCP for voice profile (will fall back to generic reply style if
  unavailable). Obsidian connector is optional (used for personal context).
references:
  - brand-voice-guide
---

# LinkedIn Comments Skill

This skill reads recent comments on Matty's own LinkedIn posts via Chrome browser automation (using his real logged-in session), presents them for review, and drafts replies in his voice pulled from Tiger Den. Matty copies and pastes the replies back to LinkedIn himself — the skill never posts anything.

The flow is always: **navigate → extract → present → draft on request → manual paste.** Never write to LinkedIn. Never auto-submit anything.

---

## Why Chrome automation and not an API

LinkedIn's Community Management API is Partner-gated and unavailable for personal use. Third-party session-based LinkedIn APIs (Unipile, etc.) replay your cookie from their infrastructure and match the pattern LinkedIn's anti-bot systems flag. Driving your own Chrome browser is the lowest-risk option: same IP, same fingerprint, same user-agent as normal browsing. The cost is that the extension must be running and LinkedIn's DOM changes will periodically break things.

---

## Before You Start — Load Context

### Config values

Read `config.json` from the plugin root to get:
- `linkedin_handle` — used to build the activity URL (e.g., `mattstratton`)
- `voice_profile_slug` — Tiger Den voice profile for reply drafting (e.g., `matty`)

### Voice profile

Call `get_voice_profile` with the `voice_profile_slug` from config. This returns tone, anti-patterns, and real writing samples. You'll use this in Step 6 when drafting replies.

If Tiger Den is unavailable or the profile doesn't exist, tell the user:
> "Couldn't load your voice profile from Tiger Den. I can still draft replies, but they'll be in a generic professional tone rather than matching your voice. Want to proceed?"

If they say yes, proceed without voice context. Keep replies short, direct, and avoid any AI-voice tells.

### Personal context (optional)

If the Obsidian MCP is available, read `00 - System/Claude Context.md` silently. This helps recognize names in comments (team members, known community people). If Obsidian isn't available, skip — not critical for this skill.

---

## Step 1 — Parse the time window

Default window: **last 7 days**.

Accept overrides like `/linkedin-comments 14d`, `/linkedin-comments last 3 days`, `/linkedin-comments this week`. Convert to an absolute cutoff date (today minus N days). Hold this as `cutoff_date` for filtering later.

If the user's request is ambiguous, pick 7 days and mention it: "Pulling the last 7 days — say a different window if you want a different range."

---

## Step 2 — Load Chrome MCP tools

The claude-in-chrome tools are deferred. Before calling any of them, load them via ToolSearch. Do this once at the start:

```
ToolSearch with query: "select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__find"
```

If the load fails (Chrome extension not running), tell the user:
> "Can't reach Chrome. Make sure the claude-in-chrome extension is running and you have Chrome open, then run the skill again."

Stop. Don't proceed without chrome tools.

---

## Step 3 — Confirm a LinkedIn session

Call `tabs_context_mcp` to see what's open. Look for a tab on `linkedin.com`.

**If a LinkedIn tab already exists:** Use that tab. It's almost certainly already authenticated.

**If no LinkedIn tab:** Call `tabs_create_mcp` to open `https://www.linkedin.com/feed/`. Then ask the user:
> "I opened LinkedIn in a new tab. Confirm you're logged in before I continue — reply 'ready' when I should proceed."

Wait for confirmation. Do not proceed if LinkedIn shows a login wall — extraction will just return garbage.

---

## Step 4 — Navigate to the activity/posts page

Build the URL from config:

```
https://www.linkedin.com/in/<linkedin_handle>/recent-activity/all/
```

Use `/recent-activity/all/` (not `/posts/`) — the `/posts/` filter is inconsistent and sometimes hides posts with no explicit text. `/all/` includes everything you authored, which is what we want. We'll filter out non-posts (reshares without commentary, reactions on others' posts) during extraction.

Call `navigate` with this URL.

---

## Step 5 — Extract posts and comments

LinkedIn lazy-loads the activity feed. Before extracting, scroll a few times to trigger loading of posts within the time window.

### 5a. Scroll to load enough history

Use `javascript_tool` to scroll. A reasonable heuristic: scroll until you've loaded enough posts to cover the time window, capped at ~10 scrolls. Something like:

```javascript
(async () => {
  for (let i = 0; i < 10; i++) {
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(r => setTimeout(r, 1500));
  }
  return 'done';
})();
```

### 5b. Expand collapsed comments

LinkedIn collapses older comments behind "Load N more comments" and "See more replies" buttons. Click them all. Use `javascript_tool`:

```javascript
(async () => {
  const clickAll = () => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const clicked = buttons.filter(b => {
      const text = (b.textContent || '').toLowerCase();
      return text.includes('load more comments') ||
             text.includes('see more comments') ||
             text.includes('show more comments') ||
             text.includes('more replies');
    });
    clicked.forEach(b => b.click());
    return clicked.length;
  };
  let total = 0;
  for (let i = 0; i < 8; i++) {
    const n = clickAll();
    total += n;
    if (n === 0) break;
    await new Promise(r => setTimeout(r, 1200));
  }
  return `expanded ${total} comment sections`;
})();
```

### 5c. Read and extract

Use `read_page` with a targeted prompt rather than brittle DOM selectors. LinkedIn mangles class names but the page's accessible text structure is stable enough for extraction:

> "Extract all posts authored by the current profile owner on this page, along with their comments. For each post, return: the post's permalink URL (from the post timestamp link), the post's first ~150 characters of text as a preview, the relative timestamp shown on LinkedIn (e.g., '2d', '1w'), and a list of all visible comments on that post. For each comment, include: commenter's full name, commenter's title/subtitle if shown, the comment text in full, and the comment's relative timestamp. Skip posts the current user only reshared without adding commentary. Skip reactions (likes, etc.) — only return actual text comments. Return structured data I can parse."

### 5d. Filter by time window

Convert each post's relative timestamp (e.g., "3d", "1w") to an approximate absolute date and drop posts older than `cutoff_date`. Err on the side of including — if a timestamp is ambiguous, include the post.

Also drop posts with zero text comments (reactions only). We're here to draft replies, not celebrate likes.

---

## Step 6 — Present comments for review

Group comments by post. Keep the output scannable, not a wall of text. Use this format:

```
📝 Post from 3 days ago — 4 comments
   Preview: "Here's a thing I learned about Postgres connection pooling..."
   Link: https://www.linkedin.com/feed/update/urn:li:activity:...

  1. Jane Developer (Staff Engineer @ Acme)
     "This is a great point — we hit the same issue last quarter. Did you try PgBouncer's
     transaction mode?"

  2. Bob Operator
     "Connection pooling is underrated. Most teams don't think about it until it's on fire."

  ...
```

Number comments globally across all posts (1, 2, 3, ...) so the user can reference them in the next step.

At the end, ask:
> "Which ones should I draft replies for? You can say 'all', specific numbers like '1, 3, 5', or 'skip' to be done here."

---

## Step 7 — Draft replies in voice

For each selected comment, draft a reply using the voice profile loaded in "Before You Start."

### Drafting rules

- **Keep it short.** LinkedIn comment replies work best at 1-3 sentences. Long replies feel like blog posts jammed into a thread.
- **Match Matty's voice.** Use the tone, vocabulary, and anti-patterns from the voice profile. Check the writing samples — if his samples are casual and use lowercase, your drafts should too.
- **Don't open with "Great point!" or "Thanks for sharing."** Those are the definitive AI-reply tells. Respond to the *substance* of what the commenter said.
- **If the commenter asked a question, answer it.** If they agreed, build on it or add a new angle. If they disagreed, engage with the disagreement honestly — don't flatten it with "That's a fair perspective!"
- **Name-check commenters sparingly.** Don't start every reply with "Hey Jane —". Once feels personal, every time feels formulaic.
- **Avoid em dashes, "delve", "leverage", "utilize", "navigate the landscape of", and similar LLM slop.** Read the output once before finalizing and strip any phrase that feels AI-shaped.

### Output format

For each comment, output:

```
─────────────────────────────────
Comment #<N> from <Commenter Name>:
> <the original comment, verbatim>

On the post: <post preview or link>

DRAFT REPLY:
<the drafted reply, ready to paste>
```

Separate each comment/reply pair clearly so Matty can scan and copy-paste one at a time.

---

## Step 8 — Close the loop

After presenting the drafts, ask:
> "Any of these need a rewrite, or you want me to redraft with a different angle on any of them? Otherwise, you're good to paste them into LinkedIn."

**Do not post to LinkedIn.** This skill never writes. If the user says "post them for me" or similar, decline and remind them this is draft-only by design (lower ToS risk, keeps a human in the loop on what goes out under their name).

If they want rewrites, iterate on the drafts. If they're done, wrap up.

---

## Edge cases

**No posts in time window.** Tell the user: "No posts from the last N days found on your activity page. Either you haven't posted recently or the page didn't load right — want me to check a wider window?"

**Posts found but no comments on any of them.** Tell the user: "Found N posts in the last M days but no comments yet. Nothing to reply to right now." Don't fabricate comments or present an empty prompt.

**LinkedIn shows a login wall mid-run.** Pause. Tell the user: "LinkedIn is asking me to log in again — can you re-auth in the tab and say 'ready' when I should continue?"

**DOM extraction returns garbage or obviously-wrong structure.** LinkedIn probably shipped a UI change. Tell the user exactly what you tried and what came back: "I navigated to the activity page and ran extraction, but the result looks wrong — here's what I got: [snippet]. LinkedIn may have updated their UI. Want me to try again, or should we look at the extraction logic?" Don't silently retry forever.

**Chrome extension disconnects mid-run.** Fail cleanly. Tell the user what step you were on and that they should re-run after the extension is back.

**User has 50+ comments to reply to.** Offer to batch: "That's a lot — want me to draft the first 10 and you can ask for more if these land well?"

**A comment is in another language.** Note it and draft a short reply in the same language if possible. If you can't, tell the user and skip that one.

**Spam or obviously bad-faith comments.** Flag them: "Comment #N looks like spam/outreach — want to skip it?" Let Matty decide. Don't auto-delete or auto-hide — we're read-only.

---

## What this skill deliberately does NOT do

- **Does not post replies.** Manual paste only. Non-negotiable for v1.
- **Does not monitor replies to your comments on other people's posts.** Own posts only — can add in v2 if useful.
- **Does not dedupe across runs.** Running twice in one day will show the same comments twice. Low-priority to fix.
- **Does not run on a schedule.** Requires Chrome + the extension to be active — inherently interactive.
- **Does not cache anything to disk.** Each run is stateless.
