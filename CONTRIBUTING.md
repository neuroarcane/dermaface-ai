# Contributing

Small team, fast sprint — keep it lightweight but disciplined.

## Workflow

1. `main` is protected. Never commit to it directly.
2. Branch: `feature/<area>-<short-desc>` (e.g. `feature/data-dedup`, `feature/app-gradcam-overlay`).
3. Open a PR; **one teammate reviews** before merge.
4. Keep PRs small and focused.

## Commit style

Conventional-ish prefixes: `feat:`, `fix:`, `data:`, `docs:`, `exp:` (experiment), `chore:`.

## Definition of done

- Code runs and is formatted (`black`, `ruff`).
- Public functions have docstrings.
- Relevant doc updated (data/model/plan).
- No data, images, weights, or secrets committed.

## Areas & owners

See [docs/team-roles.md](docs/team-roles.md). Ping the owner of an area before large changes to it.
