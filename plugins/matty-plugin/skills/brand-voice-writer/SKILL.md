---
name: brand-voice-writer
platforms: [cowork, claude-code]
description: >
  Write marketing content in TigerData's brand voice with full context on our
  audience, positioning, and terminology. Use this skill whenever the user asks
  to write blog posts, articles, landing page copy, email campaigns, social posts,
  one-pagers, case studies, or any marketing content. Also trigger when the user
  mentions brand voice, tone, writing style, ICP, target audience, or asks for
  on-brand writing. Even if the user just says "write something about [topic]"
  without specifying brand voice, use this skill — all marketing content should
  be on-brand.
references:
  - brand-voice-guide
  - terms-glossary
  - icp-audience
  - positioning
  - marketing-strategy
  - educational-content-guide
  - white-paper-guide
---

# Brand Voice Writer

This skill gives you deep context on TigerData's brand, audience, positioning, and
terminology so you can write marketing content that sounds like us — not generic AI output.

## When to use this skill

- Any time you're writing marketing content (blog posts, articles, emails, social, landing pages, case studies, one-pagers, ad copy)
- When the user asks for "on-brand" content or mentions brand voice / tone
- When writing about TigerData products or the Timescale/PostgreSQL ecosystem
- Basically: if it's going to be published or shared externally, use this skill

## Instructions

### 1. Load the right context

Reference docs live in a shared Google Drive folder — not bundled in this plugin. Before
writing anything, fetch the reference docs relevant to the task from Drive.

**Which docs to fetch:**

- **Always fetch:** `brand-voice-guide` — this is the foundation. It defines our tone, style rules, and writing principles.
- **Always fetch:** `terms-glossary` — correct product names, capitalization, and approved terminology.
- **Fetch when writing for a specific audience:** `icp-audience` — our ideal customer profiles, personas, pain points, and what resonates with them.
- **Fetch when positioning products or making claims:** `positioning` — value propositions, differentiators, competitive context.
- **Fetch for strategic context:** `marketing-strategy` — high-level goals, key messages, campaign themes.

Don't fetch everything every time — use judgment based on the task. A quick social post might only need the voice guide and glossary. A long-form article about product positioning needs all of them.

**How to fetch reference docs:**

First, read `config.json` from the plugin root to get the `references_folder_id`. Then use the appropriate method for your runtime:

#### Cowork (Google Drive connector)

If the `google_drive_search` tool is available, you're in Cowork. To fetch a reference doc:

1. Search for the doc by name within the shared folder:
   ```
   google_drive_search(api_query: "name = '<doc-name>' and '<folder_id>' in parents")
   ```
2. The search result includes the document URI. Use it to fetch the full content:
   ```
   google_drive_fetch(document_ids: ["<uri-from-search>"])
   ```

For example, to fetch the brand voice guide:
```
google_drive_search(api_query: "name = 'brand-voice-guide' and '1DUPUkDyG8bkQgoWWI4kvoLTyMk_sT1n2' in parents")
→ returns uri: "1DcRbowyuzxhZCO4omyLZmOuQA_VBB5bldIDh0W1G3tI"

google_drive_fetch(document_ids: ["1DcRbowyuzxhZCO4omyLZmOuQA_VBB5bldIDh0W1G3tI"])
→ returns full document content
```

You can batch multiple fetches into a single `google_drive_fetch` call by passing multiple document IDs at once.

**If the Google Drive connector isn't available:** Tell the user to enable the Google Drive connector in Cowork settings (Settings → Connectors → Google Drive). It's installed by default for all TigerData teammates.

#### Claude Code (gdrive CLI)

If the `google_drive_search` tool is NOT available, you're in Claude Code. Use the `gdrive` CLI:

1. List files in the shared folder:
   ```bash
   gdrive files list --parent <folder_id>
   ```
2. Find the file ID for the doc you need from the output, then download it:
   ```bash
   gdrive files download --id <file-id> --stdout
   ```

**If `gdrive` is not installed:** Tell the user to install it (`brew install gdrive`) and authenticate (`gdrive auth`) using their Google Workspace account. This is a one-time setup.

#### If a fetch fails

If a Drive fetch fails (doc not found, permissions error, network issue), do NOT proceed silently. Tell the user which reference doc couldn't be loaded and why. The content quality depends on having the right context — better to surface the problem than write without it.

### 2. Apply brand voice consistently

After reading the reference docs, internalize the voice and tone principles. The brand voice guide is the primary authority — when in doubt, defer to it.

Key things to watch for:
- Use approved terminology from the glossary (product names, technical terms, capitalization)
- Match the tone guidance for the content type (blog posts vs. technical docs vs. social)
- Follow any structural patterns or templates defined in the voice guide

### 3. Tailor to the audience

If you know who the content is for (e.g., a specific persona from the ICP doc), adjust your approach:
- Lead with the pain points and motivations that matter to that persona
- Use the language and framing that resonates with their role
- Reference the use cases and scenarios relevant to their context

### 4. Write the content

Produce the content with the full context you've loaded. If the user hasn't specified a format, suggest one based on the topic and audience.

After writing, do a self-check:
- Does this sound like our brand voice, or generic AI?
- Are product names and technical terms correct per the glossary?
- Would this resonate with the target audience?
- Is the positioning consistent with our positioning doc?

## Optional: Tiger Den MCP integration

These features require the Tiger Den MCP server. If the tools aren't available, skip this section entirely — the skill works fine without them. See the repo README for setup instructions.

### Content search

If the `search_content` tool is available, use it to search for relevant existing content, published articles, case studies, and data points that can enrich the piece. Search for topics related to what you're writing about to find supporting material.

### Voice profiles

If the user asks to write in a specific person's voice (e.g., "write this like Matty would," "in Mike's style," "draft this as Jacky"), and the `get_voice_profile` tool is available:

1. Call `list_voice_profiles` to see who's available
2. Call `get_voice_profile` with the matching name to load their writing samples and voice notes
3. Apply that person's voice on top of the brand voice guide:
   - The voice profile takes precedence for sentence rhythm, tone, humor, paragraph style, and verbal tics
   - The brand voice guide still governs terminology, absolute rules (no em dashes), and positioning
   - Think of it as: the brand voice guide sets the floor and guardrails, the voice profile sets the personality

If the user doesn't mention a specific person, don't load a voice profile — just use the brand voice guide as the default voice.
