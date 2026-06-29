---
name: draft-uncommitted
platforms: [cowork, claude-code]
description: >
  Draft an issue of Uncommitted, Matty's personal monthly newsletter.
  Fetches his Tiger Den voice profile, applies personal voice modifiers,
  and guides section-by-section drafting with a clean markdown output
  ready for Buttondown and LinkedIn. Trigger when Matty runs
  /draft-uncommitted or says "draft my newsletter", "let's write
  Uncommitted", or "time to write the newsletter".
compatibility: >
  Tiger Den MCP connector recommended for voice profile (graceful fallback
  if unavailable). BUTTONDOWN_API_KEY environment variable required for
  optional Buttondown draft creation.
references: []
---

# Draft Uncommitted

*Uncommitted* is Matty's personal monthly newsletter — not a TigerData product. The name
is a git/database pun (intentionally multi-layered). Section names "Staged Changes" and
"Untracked" continue the metaphor.

This skill guides Matty through drafting a complete issue, section by section, in his voice.
It fetches his voice profile from Tiger Den, layers Uncommitted-specific modifiers on top,
and outputs clean markdown ready to paste into Buttondown and LinkedIn.

The flow is: **preflight → main take → approval → remaining sections → approval →
assemble full draft → optional Buttondown API.**

---

## Newsletter Structure

Every issue has exactly these five sections, in this order:

| Section | Length | Character |
|---|---|---|
| **Opener** | 2–3 sentences | Personal, human, what's going on right now. No "welcome to issue N" energy. |
| **Main Take** | 300–500 words | One real point, developed and landed. Prose only — no title, no subheadings. |
| **Staged Changes** | 2–3 items, 2–5 sentences each | Shorter observations or takes, loosely on anything. Each has a bold 1–4 word label. |
| **Untracked** | 3–6 sentences | One thing completely unrelated to tech. Music, lifting, Doctor Who, games, dogs, whatever. |
| **Closer** | 2–3 sentences | Sign-off, nothing formal. Can tease next month or just say goodbye. |

---

## Voice

### Base: Tiger Den Voice Profile

Fetch Matty's voice profile via `mcp__claude_ai_Tiger_Den__get_voice_profile`. This encodes
his no-em-dash rule, short punchy sentences, dry understatement, concrete numbers over
hand-waving, and other style fundamentals.

### Uncommitted-Specific Modifiers (layer on top)

These loosen the Tiger Den profile slightly — this is personal, not brand content:

- **Less corporate, more personal.** First person throughout. "I think" and "I've noticed"
  are fine.
- **Opinions stated as opinions.** Don't hedge everything. "This is wrong" beats "this may
  be worth reconsidering."
- **Allowed to be weird.** Especially in Untracked. Doctor Who references, lifting PRs,
  punk music tangents — features, not bugs.
- **No marketing cadence.** Don't wrap every section with a tidy lesson. Sometimes the point
  is just: here's a thing I noticed.
- **Dry understatement over enthusiasm.** If something is genuinely exciting, say it once.
  Don't exclaim.
- **No AI tells.** Apply de-slop aggressively. No "it's worth noting that", no "in today's
  rapidly evolving landscape", no bullet-pointed takeaways unless Matty asks.

---

## Step 0 — Preflight

### Fetch voice profile

Call `mcp__claude_ai_Tiger_Den__list_voice_profiles` to confirm the correct slug for Matty
(the config value is `matty` but verify at runtime). Then call
`mcp__claude_ai_Tiger_Den__get_voice_profile` with the confirmed slug.

Internalize the profile silently — do not summarize it back.

If Tiger Den is unavailable: proceed using the Uncommitted-specific modifiers above as the
sole voice guidance. Note the fallback to Matty so he knows.

---

## Step 1 — Gather the Main Take Topic

Ask Matty what the main take is for this issue. He should be able to describe it in a
sentence or two. If he pastes notes, a Slack thread, or a rough draft, use that as input.

**Do not start writing yet.** Confirm you understand the point he wants to make. One
clarifying question is fine if the topic is vague. Do not ask more than one.

---

## Step 2 — Draft the Main Take

Write the Main Take first — it's the hardest and most important section. 300–500 words,
prose only, no title or subheadings.

Apply the voice profile + Uncommitted modifiers. One real point, developed and landed.
Should feel like something worth forwarding. Matty's genuine opinion, not hedged to death.

**Present it to Matty. Wait for feedback or approval before continuing.** This is the
section most worth getting right before moving on.

---

## Step 3 — Gather Remaining Section Inputs

Ask Matty for all of these in a **single message** — not four separate questions:

> "Nice. A few things I need to fill in the rest:
>
> - **Opener:** what's going on in your world right now? One sentence is enough.
> - **Staged Changes:** what 2–3 things have you been thinking about lately? Can be anything.
> - **Untracked:** what non-tech thing is currently in your brain?
> - **Closer:** anything specific you want to tease or say, or should I just write a sign-off?"

Matty can answer whatever he has and skip what he doesn't. Write unaddressed sections from
context and the voice profile.

---

## Step 4 — Draft Remaining Sections

Draft Opener, Staged Changes, Untracked, and Closer from his inputs. Present all four
together in a single message after the already-approved Main Take.

**Opener:** 2–3 sentences. Personal and human. No "welcome to issue N" energy. Can expand
from one sentence he gives you.

**Staged Changes:** 2–3 items, each 2–5 sentences. Each has a **bold label** (1–4 words)
followed by the observation. Opinionated and punchy — not a link dump. Format:

```
**Label:** Observation text here, 2–5 sentences, one tight take.
```

**Untracked:** 3–6 sentences on one thing completely unrelated to tech. This is the section
that makes the newsletter feel human rather than content-machine. Lean into Matty's
actual interests: The Cure/punk/alt music, GZCLP lifting, Doctor Who, Dungeon Crawler Carl,
Balatro, Riot Fest, Australian Shepherds, whatever he's currently on about.

**Closer:** 2–3 sentences. Nothing formal. Can tease next month or just say goodbye. No
"until next time" or "stay curious" energy.

Wait for Matty's feedback or approval on the remaining sections.

---

## Step 5 — Assemble Full Draft

Once Matty has approved or edited all sections, output the complete issue as clean markdown
in a **single code block**. No commentary before or after — just the draft, ready to paste.

```markdown
[opener prose]

---

[main take prose]

---

**Staged Changes**

**[Label]:** [observation]

**[Label]:** [observation]

**[Label]:** [observation]

---

**Untracked**

[off-brand prose]

---

[closer prose]
```

**Output format rules:**
- Plain markdown only — no HTML, no inline CSS
- Section dividers use `---`
- Section headers (**Staged Changes**, **Untracked**) are bold inline, not H2/H3
- Staged Changes item labels are bold inline: `**Label:** text`
- Paste-friendly for both Buttondown and LinkedIn

---

## Step 6 — Buttondown Draft (Optional)

After outputting the markdown, offer to create a draft issue in Buttondown:

> "Want me to create a draft in Buttondown?"

If Matty says yes:

1. Ask for a subject line if he hasn't provided one.

2. Check for `BUTTONDOWN_API_KEY` in the environment:
   ```bash
   printenv BUTTONDOWN_API_KEY
   ```
   If the command returns nothing or exits non-zero, tell Matty: "Set `BUTTONDOWN_API_KEY`
   in your environment (e.g. add it to `~/.zshenv` or your Claude Code env config) and
   re-run this step." Do not proceed without it.

3. Create the draft via the Buttondown API:
   ```bash
   curl -s -X POST https://api.buttondown.com/v1/emails \
     -H "Authorization: Token $BUTTONDOWN_API_KEY" \
     -H "Content-Type: application/json" \
     -d "{
       \"subject\": \"SUBJECT_LINE_HERE\",
       \"body\": \"MARKDOWN_BODY_HERE\",
       \"status\": \"draft\"
     }"
   ```
   **Note:** Buttondown's `status` field accepting `"draft"` was inferred from their API
   schema but not fully confirmed in docs at implementation time. If the API returns an
   error on `status`, retry without it — Buttondown may default new emails to draft.

   **Also note:** If the markdown body starts with `---` (YAML frontmatter), the API
   returns a 400 error unless you include the header
   `X-Buttondown-Live-Dangerously: true`. The assembled draft in Step 5 starts with prose,
   not `---`, so this should not be an issue in normal use.

4. If the API call succeeds, report the draft URL or ID from the response.

**LinkedIn cross-post is always manual** — Matty copies the markdown into LinkedIn's native
newsletter editor. The Step 5 output is formatted to paste cleanly without reformatting.

---

## What This Skill Does NOT Do

- Does not post or publish anything automatically
- Does not handle LinkedIn cross-posting
- Does not manage subscribers or Buttondown account settings
- Does not generate topic ideas — Matty brings the topic
- Does not fact-check or research — Matty brings the knowledge
