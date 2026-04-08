# Family Dashboard

Full spec: `family-dashboard.md`. Session prompts: `session-prompts.md`.

## Commands
- Backend: `cd backend && uvicorn main:app --reload`
- Frontend: `cd frontend && npm run dev`
- Backend tests: `cd backend && python -m pytest --tb=short`
- Frontend tests: `cd frontend && npx vitest run`
- Lint check: `cd backend && ruff check . && cd ../frontend && npx eslint src/`

## MUST follow — build order
1. MUST write Gherkin feature file first, before any code
2. MUST write failing tests before implementation
3. MUST write minimum code to pass tests — nothing more
4. MUST run mutation tests after implementation; MUST NOT leave surviving mutants without documented justification
5. MUST confirm all tests pass before committing
6. MUST update `MUTANTS.md` for any surviving mutants that will not be addressed — record the mutant ID, what was mutated, and why it is acceptable

## Session startup
- Fetch deferred tools before starting any task:
  `ToolSearch: "select:AskUserQuestion,TodoWrite"`
- Confirm both tools are available before proceeding
- Check that `frontend-design` is listed in the available skills (it appears in the system-reminder skills list)
- If `frontend-design` is absent: STOP immediately. Do not proceed with any task. Tell the user:
  "The `frontend-design` skill is not available. The session-start hook failed to install it from GitHub. Please restart the session. No code will be written until the skill is available."
- Note: the session-start hook installs the skill in both web and local CLI environments.

## MUST follow — git
- MUST check current branch before starting: `git branch --show-current`
- MUST NEVER write files or commit on `main` — hooks enforce this and will block you
- MUST name branches `feature/<name>` cut from `main`
- MUST commit atomically with conventional commit messages after each logical step
- MUST inform the user when a feature is complete — NEVER merge or raise a PR autonomously
- MUST use the AskUserQuestion tool to ask clarifying questions before writing any code if anything in the current task is ambiguous. Do not guess. If the session prompt is explicit and complete, proceed without asking.

## NEVER do
- NEVER edit `.env` — hooks will block this; update `.env.example` instead
- NEVER run `rm -rf`, `git push --force`, or `git reset --hard` — hooks will block these
- NEVER run ruff or eslint manually — hooks run them automatically on file save
- NEVER implement behaviour not covered by a feature file

## Before writing any UI component
- MUST invoke the `/frontend-design` skill before writing any JSX or CSS — no exceptions
- If the skill invocation fails or the skill is not listed: STOP. Do not write any frontend code. Tell the user the skill is unavailable and that the session must be restarted
- NEVER proceed with frontend implementation without a successful `/frontend-design` invocation in the same session

## When compacting
Preserve: current branch name, list of modified files, last test run status, any surviving mutants noted.
