# Family Dashboard — Claude Code Context

See `family-dashboard.md` for full project specification.

## Build order (never skip or reorder)
1. Write Gherkin feature file in `features/`
2. Write failing tests derived from the feature file
3. Write minimum implementation to pass tests
4. Run mutation tests — no surviving mutants without documented justification
5. Confirm all tests pass

## Git workflow
- Always check current branch before starting: `git branch --show-current`
- Never write files or commit on `main` — hooks will block this
- Branch naming: `feature/<feature-name>`, cut from `main`
- Commit atomically after each logical step with conventional commit messages
- When a feature is complete and all tests pass, inform the user — do not merge or raise a PR autonomously

## General rules
- Never edit `.env` directly — hooks will block this; update `.env.example` instead
- Never use `rm -rf`, `git push --force`, or `git reset --hard` — hooks will block these
- Hooks run ruff and eslint automatically on file save — do not run them manually
- Read `/mnt/skills/public/frontend-design/SKILL.md` before writing any UI component
