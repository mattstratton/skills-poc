---
name: tiger-den-update
platforms: [cowork, claude-code]
description: >
  Summarizes recent GitHub Releases from the timescale/tiger-den repo and posts a
  narrative briefing to #project-tiger-den on Slack. Covers product changes, new features,
  bug fixes, and includes a dedicated section for developer workflow updates (CI, skills,
  dev tooling). Default timeframe is the last 7 days; user can specify any range.
  Trigger when the user runs /tiger-den-update or says "tiger den update", "what shipped
  in tiger den", "tiger den releases", "what's new in tiger den", "den release notes",
  or "tiger den changelog". Also trigger for "what did tiger den ship this week" or similar.
compatibility: >
  Requires GitHub MCP connector (for reading releases from the private timescale/tiger-den
  repo) and Slack MCP connector (for posting the briefing). If either is missing, tell the
  user which connector is needed and how to connect it.
references: []
---

# Tiger Den Update Skill

This skill fetches recent GitHub Releases from the `timescale/tiger-den` repo, synthesizes
them into a narrative briefing, and posts it to `#project-tiger-den` on Slack.

The goal is NOT to copy-paste release notes. It's to help the team understand what actually
changed, why it matters, and what they should know — written like a person who read all the
releases and is catching you up over coffee.

The flow is always: **fetch releases → synthesize → draft message → get approval → post.**
Never post to Slack without explicit user approval.

---

## Before You Start — Load Context

### Personal context (memory layer)

Read `00 - System/Claude Context.md` from the Obsidian vault using `obsidian_get_file_contents`.
This is the memory layer — team, key people, shorthand, active projects. Internalize it
silently (don't summarize it back).

### Config values

Read `config.json` from the plugin root to get:
- `github_org` — the GitHub organization (should be `timescale`)

---

## Arguments

The user can provide a timeframe. Accepted formats:

- `/tiger-den-update` (defaults to last 7 days)
- `/tiger-den-update last 2 weeks`
- `/tiger-den-update March 1-15`
- `/tiger-den-update 2026-03-01 to 2026-03-15`
- `/tiger-den-update since last Monday`

If no timeframe is provided, default to the last 7 days from today. Don't ask — just use
the default and mention the date range in your response so the user can adjust if needed.

---

## Step 1 — Fetch GitHub Releases

Use the GitHub MCP tools to get releases from `timescale/tiger-den`.

**How to find releases:**

Use `list_releases` with:
- `owner`: `timescale`
- `repo`: `tiger-den`

This returns releases sorted by most recent first. Paginate if needed until you've passed
the start of the requested timeframe.

**For each release in the timeframe, extract:**
- `tag_name` — the version tag
- `name` — the release title
- `body` — the full release notes (markdown)
- `published_at` — when it was published
- `author` — who published it
- `html_url` — link to the release on GitHub

**Filter by date:** Only include releases where `published_at` falls within the requested
timeframe. If a release is right on the boundary, include it — better to over-include than
miss something.

**If no releases are found in the timeframe:** Tell the user. Suggest they try a wider
range. Don't fabricate content.

---

## Step 2 — Analyze and Group Releases

Read through all the release bodies and understand what actually shipped. Don't treat each
release as an isolated item — look for patterns, themes, and connections across releases.

### Grouping strategy

Group changes thematically, not chronologically or by release tag. Common groupings might
include:

- **New features / capabilities** — net-new functionality users can now do
- **Improvements / enhancements** — existing features that got better (performance, UX, etc.)
- **Bug fixes** — things that were broken and are now fixed
- **Infrastructure / reliability** — backend changes, stability improvements, scaling work

Don't force these exact categories — let the actual content dictate the groupings. If all
the releases are bug fixes, don't invent a "New features" section with nothing in it. If
there's a clear theme across multiple releases (e.g. "this was a big week for search
improvements"), lead with that.

### Identifying developer workflow changes

Scan every release body for changes that affect how people *develop* Tiger Den itself. These
go in the dedicated "For Tiger Den Developers" section at the end. Look for:

- **Claude Code skill updates** — changes to `/pr`, `/review`, or any other skills in the
  repo. Things like "the /pr skill now does X before pushing" or "added a new /deploy skill"
- **CI/CD changes** — updates to GitHub Actions, release workflows, test pipelines, deploy
  processes
- **Development workflow changes** — new conventions, branch policies, PR review process
  changes, linting rules, pre-commit hooks
- **Dev tooling** — changes to local dev setup, Docker configs, dev dependencies, Makefile
  updates
- **Contributing guidelines** — updates to how people should contribute, code review norms,
  documentation requirements

These are things a developer working on Tiger Den would need to know to avoid surprises in
their workflow. If a release mentions "updated the CI pipeline to require X" or "the /pr
skill now checks Y before pushing," that belongs here.

If there are no developer workflow changes in the timeframe, omit the section entirely.
Don't include it with "no changes this period" — that's noise.

---

## Step 3 — Draft the Slack Message

Write a single Slack message for `#project-tiger-den`. This is a narrative briefing, not
a changelog dump.

### Tone and style

- Write like you're catching a teammate up on what shipped. Conversational, direct,
  informative.
- Contextualize changes — don't just say "added X", explain briefly what problem it solves
  or why someone would care.
- Group related changes together even if they came from different releases.
- Call out anything particularly noteworthy or high-impact at the top.
- Keep it scannable — people should be able to skim the bold lines and get the gist.

### Message format

```
:package: **Tiger Den Update — [Date Range]**

[1-2 sentence overview: what was the theme of this period? Was it a big feature week, a
stability push, a bunch of quality-of-life improvements? Set the scene.]

[If one thing stands out as the headline, call it out here with a brief explanation of
why it matters.]

━━━━━━━━━━━━━━━━━━━━━━━━

**[Thematic Group 1 Name]**

[Narrative paragraph covering the changes in this group. 2-4 sentences. Mention specific
features/fixes by name but explain them in context. Link to individual releases where
helpful using the `html_url`.]


**[Thematic Group 2 Name]**

[Same treatment]

[Repeat as needed — aim for 2-4 groups. Fewer is better if the changes are closely related.
IMPORTANT: always leave a blank line AFTER each section header and a blank line BETWEEN
sections for readability. Slack collapses dense text into a wall — spacing is how you fight it.]

━━━━━━━━━━━━━━━━━━━━━━━━

:hammer_and_wrench: **For Tiger Den Developers**

[Narrative paragraph covering workflow/tooling/CI changes that affect how people build
Tiger Den. Be specific — if a skill changed behavior, say exactly what's different. If
CI now requires something new, say what developers need to do (if anything). 2-5 sentences
depending on volume. If there are multiple discrete items, break them into short paragraphs
with blank lines between them rather than one dense block.]

━━━━━━━━━━━━━━━━━━━━━━━━

_Covers releases [earliest tag] through [latest tag] · [N] releases total_
```

### Formatting rules

- The Slack MCP tool uses **standard markdown**, not Slack's native mrkdwn format. This
  means: `**double asterisks**` for bold (NOT single), `_underscores_` for italic, `` `code` ``
  for version tags and technical terms. This is critical — single `*asterisks*` will render
  as italic, not bold.
- **Section headers must stand alone on their own line with a blank line after them.** Don't
  run the header directly into the paragraph — Slack needs the whitespace to make headers
  visually distinct from body text.
- **Leave a blank line between every section/group.** Two consecutive paragraphs with no
  space between them are unreadable in Slack. When in doubt, add more space, not less.
- Use `━━━` Unicode box-drawing characters for section dividers (Slack's `---` doesn't
  render as a horizontal rule)
- Use `:package:` as the opening emoji. (If a `:tiger-den:` custom emoji is added to the
  workspace in the future, switch to that.)
- Keep the total message under ~2000 characters if possible. If it's a huge release period
  with tons of changes, it's okay to go longer, but err on the side of concise. People can
  click through to the release links for details.
- Don't use bullet points for the main content — write in prose. Bullets are okay in the
  developer section if there are multiple discrete workflow changes that read better as a list.

### What NOT to include

- Don't list every single commit or minor version bump. Synthesize.
- Don't copy-paste release note text verbatim. Rewrite in your own words with context.
- Don't include dependency bumps or trivial maintenance unless they have user-facing impact.
- Don't include the developer section if there are no dev workflow changes.
- Don't editorialize about quality or praise the team — just describe what shipped and why
  it matters.

---

## Step 4 — Present Draft for Approval

Show the full draft message in the conversation. Also mention:
- How many releases were covered
- The date range scanned
- Whether a developer section was included (and why/why not)

Ask: "Want me to post this to #project-tiger-den, or want to tweak anything first?"

Wait for explicit approval before posting. If the user wants changes, revise and show
the updated draft. Repeat until they're happy.

---

## Step 5 — Post to Slack

When the user approves (says "post it", "looks good", "ship it", "send it", or similar):

1. Use `slack_search_channels` to find the `#project-tiger-den` channel ID. Don't hardcode it.
2. Post the message using `slack_send_message`.
3. Confirm in the conversation: "Posted to #project-tiger-den."

**Never post without explicit user approval.**

---

## Edge Cases

**No releases in the timeframe:**
Tell the user: "No releases found in timescale/tiger-den for [date range]. Want me to try
a wider range?" Don't post an empty update.

**Only one release:**
Still write a narrative summary — don't just forward the release notes. Even a single
release deserves contextualization.

**GitHub MCP not available:**
Stop and tell the user: "I need the GitHub connector to read releases from the private
timescale/tiger-den repo. In Cowork, go to Settings -> Connectors and connect GitHub. In
Claude Code, make sure the GitHub MCP is configured."

**Slack MCP not available:**
Generate the draft and show it in the conversation. Tell the user: "I can't post to Slack
because the Slack connector isn't available. Here's the draft — you can copy-paste it to
#project-tiger-den manually. To connect Slack, go to Settings -> Connectors."

**Release notes are empty or minimal:**
Some releases might have sparse notes. Do your best with what's there — use the tag name,
title, and any context from surrounding releases. If a release truly has no useful info,
you can skip it but mention that you did: "Skipped vX.Y.Z (empty release notes)."

**Very large number of releases (10+):**
Be more aggressive about grouping and summarizing. Don't try to mention every release
individually. Focus on the themes and highlight the most impactful changes. Mention the
total count so people know the scope.

**User asks for a specific release only:**
If the user says something like "what's in v2.5.0", fetch just that release and summarize
it. Skip the Slack posting flow — just answer the question directly in the conversation.
Only offer to post if they ask.
