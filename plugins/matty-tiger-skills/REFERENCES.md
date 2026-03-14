# How to Fetch Reference Docs

Skills in this plugin declare which reference docs they need in their frontmatter. The docs themselves live outside the plugin. This file explains how to fetch them.

## Two kinds of reference docs

**Remote references** are proprietary docs stored in Tiger Den (brand voice guide, sales stage framework, customer journey map, etc.). These are fetched at runtime using Tiger Den MCP tools. Every skill that needs them declares their slugs in frontmatter.

**Local references** are non-proprietary docs bundled in a skill's `references/` directory (topic bucket definitions, fallback voice profiles, formatting examples, etc.). These are committed to the repo because they contain no confidential content. Skills read them directly from disk — no MCP call needed.

This file covers remote references only. If a skill has a `references/` directory, it reads those files directly.

## Checking Tiger Den availability

Before fetching reference docs, confirm Tiger Den is connected by calling `list_voice_profiles()`. This is the definitive availability check — it's a Tiger Den-specific tool that no other connector exposes.

**How to find the tool:** In Cowork, MCP tools appear with UUID-based prefixes (e.g. `mcp__2fef16dd-...__list_voice_profiles`). Don't look for a tool with "tiger_den" or "Tiger Den" in the prefix — the connector is named "Den.tigerdata.com" in Cowork settings, and the prefix is a UUID. Identify Tiger Den tools by their **function name suffix**: `list_voice_profiles`, `get_marketing_context`, `get_voice_profile`, `search_content`, `get_content_text`, `list_content`, `build_linkedin_prompt`, `list_marketing_references`, `get_marketing_reference`.

If you see any of these suffixes in the available tools list, Tiger Den is connected. If none of these suffixes appear, Tiger Den is not connected.

## Fetching from Tiger Den

Tiger Den is the source for all remote reference docs. Use the MCP tools described below.

**Fetch all declared references in one call (preferred):**

```
get_marketing_context(slugs: ["sales-stage-framework", "customer-journey-map", "brand-voice-guide"])
```

The slugs match the reference names in the skill's frontmatter. Pass all of them as an array and you get everything in a single round-trip.

**If you only need one doc**, use `get_marketing_reference` instead:

```
get_marketing_reference(slug: "brand-voice-guide")
```

**If you're not sure what's available**, use `list_marketing_references` to see all available reference docs and their slugs.

## Error handling

If Tiger Den tools are not available or return an error, do NOT proceed silently and do NOT attempt to write content without the reference docs. Tell the user what happened and how to fix it:

- **Tiger Den not available (no matching tools):** Call `list_voice_profiles()` — if no tool with that suffix exists in the available tools, Tiger Den isn't connected. Tell the user: "This skill needs Tiger Den to load reference docs, but the Tiger Den connector isn't available. In Cowork, go to Settings → Connectors → find Den.tigerdata.com → click Connect. In Claude Code, run `/setup` to get it configured."
- **Tiger Den connection error (tool exists but call fails):** "Tiger Den returned an error. Check that the connector is still authorized. Run `/doctor` to diagnose the issue."
- **Specific doc not found:** "Could not find '[slug]' in Tiger Den. Check that it exists at den.tigerdata.com. Available docs: [call list_marketing_references and show results]."

Reference docs contain the brand voice, positioning, terminology, sales process context, and quality standards that skills depend on. Writing without them produces generic, off-brand output — it's better to surface the error and help the user fix it than to proceed without context.
