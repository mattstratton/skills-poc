# How to Fetch Reference Docs from Google Drive

Skills in this plugin declare which reference docs they need in their frontmatter. The docs
themselves live in a shared Google Drive folder — not bundled in the plugin. This file
explains how to fetch them.

## Step 1: Get the folder ID

Read `config.json` from the plugin root. It contains the shared Drive folder ID:

```json
{
  "references_folder_id": "1DUPUkDyG8bkQgoWWI4kvoLTyMk_sT1n2"
}
```

## Step 2: Detect your runtime and fetch

### Cowork (Google Drive connector)

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

You can batch multiple fetches into a single `google_drive_fetch` call by passing multiple
document IDs at once. When a skill needs several reference docs, search for all of them
first, collect the URIs, then fetch them in one call.

**If the Google Drive connector isn't available:** Tell the user to enable the Google Drive
connector in Cowork settings (Settings → Connectors → Google Drive). It's installed by
default for all TigerData teammates.

### Claude Code (gdrive CLI)

If the `google_drive_search` tool is NOT available, you're in Claude Code. Use the `gdrive` CLI:

1. List files in the shared folder:
   ```bash
   gdrive files list --parent <folder_id>
   ```
2. Find the file ID for the doc you need from the output, then download it:
   ```bash
   gdrive files download --id <file-id> --stdout
   ```

**If `gdrive` is not installed:** Tell the user to install it (`brew install gdrive`) and
authenticate (`gdrive auth`) using their Google Workspace account. This is a one-time setup.

## Error handling

If a Drive fetch fails (doc not found, permissions error, network issue), do NOT proceed
silently. Tell the user which reference doc couldn't be loaded and why. The content quality
depends on having the right context — better to surface the problem than write without it.
