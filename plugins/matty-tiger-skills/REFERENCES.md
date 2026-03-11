# How to Fetch Reference Docs

Skills in this plugin declare which reference docs they need in their frontmatter. The docs themselves live outside the plugin. This file explains how to fetch them.

## Two kinds of reference docs

**Remote references** are proprietary docs stored in Tiger Den (brand voice guide, sales stage framework, customer journey map, etc.). These are fetched at runtime using Tiger Den MCP tools. Every skill that needs them declares their slugs in frontmatter.

**Local references** are non-proprietary docs bundled in a skill's `references/` directory (topic bucket definitions, fallback voice profiles, formatting examples, etc.). These are committed to the repo because they contain no confidential content. Skills read them directly from disk — no MCP call needed.

This file covers remote references only. If a skill has a `references/` directory, it reads those files directly.

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

- **Tiger Den not available (tools missing):** "This skill needs Tiger Den to load reference docs, but the Tiger Den MCP server isn't connected. Run `/setup` to get it configured — it takes about two minutes."
- **Tiger Den connection error (tools exist but call fails):** "Tiger Den returned an error. Check that the MCP server is running and your API key is valid. Run `/doctor` to diagnose the issue."
- **Specific doc not found:** "Could not find '[slug]' in Tiger Den. Check that it exists at tiger-den.vercel.app. Available docs: [call list_marketing_references and show results]."

Reference docs contain the brand voice, positioning, terminology, sales process context, and quality standards that skills depend on. Writing without them produces generic, off-brand output — it's better to surface the error and help the user fix it than to proceed without context.
