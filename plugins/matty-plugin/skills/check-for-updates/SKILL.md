# check-for-updates

## Purpose

Review plugin or skills metadata and suggest improvements for versioning and release readiness.

## Inputs

- Current plugin manifest (`.claude-plugin/plugin.json`)
- Current marketplace manifest (`marketplace.json`)
- Any release notes or versioning context

## Expected behavior

- Identify mismatched ids, names, and source paths
- Flag missing metadata that could affect discoverability
- Suggest a minimal, actionable update checklist

## Example prompts

- "Check this plugin for release readiness"
- "Do my marketplace and plugin ids match?"
- "What should I update before publishing?"
