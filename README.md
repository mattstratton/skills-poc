# skills-poc

Proof-of-concept repository for a Claude skills marketplace and plugin package.

## Repository layout

- `.claude-plugin/marketplace.json`: Canonical marketplace registry used by Claude discovery.
- `marketplace.json`: Optional duplicate kept for convenience while developing.
- `plugins/matty-plugin/.claude-plugin/plugin.json`: Plugin metadata.
- `plugins/matty-plugin/skills`: Skill definitions.
- `plugins/matty-plugin/commands`: Command definitions.

## Current plugin wiring

The marketplace currently exposes one plugin:

- plugin id: `matty-plugin`
- source path: `./plugins/matty-plugin`

## Getting started

1. Add additional skills under `plugins/matty-plugin/skills`.
2. Add additional commands under `plugins/matty-plugin/commands`.
3. Register new plugins in `.claude-plugin/marketplace.json` with a unique id and source path.

## Next suggested improvements

- Add validation scripts for marketplace and plugin manifests.
- Add examples for multiple plugins in `plugins/`.
- Add CI checks to ensure plugin ids and source paths are valid.
