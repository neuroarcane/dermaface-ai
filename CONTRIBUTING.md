# Contributing

Small team, fast sprint — keep it lightweight but disciplined.

## Workflow

We're a 7-person team on a 3-week sprint, so the process is deliberately light:
**CI is the gatekeeper, not a mandatory human reviewer.**

1. Work on a branch: `feature/<area>-<short-desc>` (e.g. `feature/data-dedup`, `feature/app-gradcam-overlay`). Avoid committing straight to `main`.
2. Open a PR. **Self-merge is fine once CI is green** (`ruff` + `pytest` must pass) — you don't need to wait on a teammate.
3. Review is *optional but encouraged*: tag the area owner if a change is risky or touches their code. Don't let a review block you.
4. Keep PRs small and focused so CI stays fast and merges stay easy.

## Commit style

Conventional-ish prefixes: `feat:`, `fix:`, `data:`, `docs:`, `exp:` (experiment), `chore:`.

## Definition of done

- Code runs and is formatted (`black`, `ruff`).
- Public functions have docstrings.
- Relevant doc updated (data/model/plan).
- No data, images, weights, or secrets committed.

## Areas & owners

See [docs/team-roles.md](docs/team-roles.md). Ping the owner of an area before large changes to it.
