# Family Dashboard

Full spec: `family-dashboard.md`. Hardware and deployment: `hardware.md`, `PI_SETUP.md`.

## Commands
- Backend: `cd backend && uvicorn main:app --reload`
- Frontend: `cd frontend && npm run dev`
- Backend tests: `cd backend && python -m pytest --tb=short`
- Frontend tests: `cd frontend && npx vitest run`
- Lint check: `cd backend && ruff check . && cd ../frontend && npx eslint src/`
- Mutation tests (**dev machine only** — see below): `cd frontend && npm run test:mutation`

## Shared Raspberry Pi
This app shares a 4GB Pi 5 with the **budget planner** (`ryan684/budget-planner`).
Full detail in `hardware.md`, "Sharing the Pi with the budget planner". What matters here:

- **Port 8000 belongs to this app**, bound to `127.0.0.1` in production (the only consumer
  is the local Chromium kiosk, and this app has no auth). The budget planner owns 8001.
- **Python 3.14 and Node 22 are shared installs** — one interpreter, one Node, a separate
  `backend/.venv` and `frontend/node_modules` per app. Don't align the two apps' npm
  dependency sets; only the binaries are shared.
- **Memory is the binding constraint.** Don't add anything long-running to the Pi, and
  don't move the nightly deploy timer (02:00) closer to the budget planner's backup (03:30).

## MUST follow — build order
1. MUST write Gherkin feature file first, before any code
2. MUST write failing tests before implementation
3. MUST write minimum code to pass tests — nothing more
4. MUST run mutation tests after implementation; MUST NOT leave surviving mutants without documented justification
5. MUST confirm all tests pass before committing
6. MUST update `MUTANTS.md` for any surviving mutants that will not be addressed — record the mutant ID, what was mutated, and why it is acceptable

## MUST NOT run mutation tests on the Raspberry Pi
Step 4 above is a **development-machine** step. This Pi is a 4GB Pi 5 shared with the
budget planner, running two backends and a Chromium kiosk; mutmut re-runs the whole
suite per mutant and Stryker spawns parallel Vitest workers, and either will exhaust
memory and take the OOM killer to a live service.

If you are running on the Pi (Claude Code is installed there — `PI_SETUP.md`, Part 17):
do steps 1–3, 5 and 6, commit, and run mutation tests later on a laptop. Do not treat
step 4 as blocking. `scripts/assert-not-pi.sh` guards `npm run test:mutation` and should
prefix any `mutmut run`; do not work around it.

## Session startup
- Fetch deferred tools before starting any task:
  `ToolSearch: "select:AskUserQuestion,TodoWrite"`
- Confirm both tools are available before proceeding

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
- MUST identify the purpose, audience, and tone of the component before writing any JSX or CSS
- MUST choose a deliberate aesthetic direction and state it — NEVER default to "clean and minimal" without justification
- MUST use tabular/monospaced numerals for times and figures so they align across cards
- MUST reuse existing spacing scale (multiples of 4 px or 8 px) and colour variables — NEVER set arbitrary values inline
- MUST keep internal padding consistent across all cards
- MUST use the existing delay colour system (green / amber / red) for any status indicators
- NEVER use Inter, Roboto, or Arial as the primary display face
- NEVER use purple gradients on white backgrounds
- NEVER add animation that does not communicate meaning; if animating, use transform/opacity only (150–300 ms, ease-out on enter)
- NEVER add decorative elements not justified by the design rationale

## When compacting
Preserve: current branch name, list of modified files, last test run status, any surviving mutants noted.
