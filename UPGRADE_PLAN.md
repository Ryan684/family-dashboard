# Dependency Upgrade Plan

Derived from the dependency audit of 2026-07-27. Every claim marked **[verified]**
was tested by building the proposed dependency set in a scratchpad copy of
`frontend/` and running the real test suite, build, and mutation runner against
it. Claims marked **[unverified]** could not be executed in this container — see
Phase 0.

Baseline: 121/121 frontend tests pass on the current lockfile (vitest 2.1.9).

---

## Phase 0 — Environment prerequisites (blocking for backend work)

| Item | Detail |
|---|---|
| `frontend/node_modules` | Absent in a fresh clone. `npm ci` before anything else. |
| Backend install | `pyproject.toml` sets `requires-python = ">=3.14"`; this container has Python 3.11.15, so backend deps cannot be installed or tested here. `PI_SETUP.md` Part 6 documents pyenv 3.14 as the intended path. |
| Consequence | **Everything in Phase 1 is [unverified]** — the backend test suite (10 files) has not been run. Phase 1 must be validated on a 3.14 interpreter before commit. |

No source file uses 3.14-only syntax, so the floor looks conservative rather
than load-bearing — but that is a separate decision, not part of this upgrade.

### 0.1 — Deploy script gap (found while planning, fix before Phase 2 ships)

`scripts/deploy.sh` runs `npm run build` but never `npm ci` / `npm install`.
Today that is survivable because the lockfile rarely changes. After Phase 2 it
is not: the Pi's nightly deploy would build against stale `node_modules` and
either fail or silently produce a build from the old toolchain.

```diff
 cd "$REPO_DIR/frontend"
+npm ci
 npm run build
```

This is a prerequisite for Phase 2, not an optional extra.

---

## Phase 1 — Backend (highest security value, lowest risk)

No behaviour change. Existing tests are the regression net.

### 1a. Remove the unused `apscheduler` dependency

`apscheduler` is declared in `pyproject.toml` but **imported nowhere** —
`backend/scheduler.py` is a hand-rolled `asyncio` loop. Removing the
declaration eliminates exposure to **CVE-2026-31072** (RCE via insecure
deserialization in `JSONSerializer`/`CBORSerializer`, all versions incl. 3.10.x
and 4.0.0a5) outright, at zero cost.

```diff
-    "apscheduler",
```

The only other reference is a prose mention in `backend/MUTANTS.md:250`, which
should be reworded so it stops implying a dependency that no longer exists.

### 1b. Add explicit version floors

Currently every backend dependency is unconstrained. That is the real finding
here — not version drift, but that nothing guarantees a patched resolve.

Concretely, for **CVE-2026-48710 "BadHost"** (Starlette host-header auth bypass,
affects 0.8.3–1.0.0, patched in 1.0.1): FastAPI 0.140.7's own metadata requires
only `starlette>=0.46.0` **[verified]** — a range that still admits every
vulnerable version. A fresh install today happens to resolve to Starlette 1.3.1,
but nothing enforces that.

```toml
dependencies = [
    "fastapi>=0.140.7",
    "starlette>=1.0.1",     # explicit: CVE-2026-48710 floor, not implied by fastapi
    "uvicorn[standard]>=0.51.0",
    "python-dotenv>=1.2.2",
    "httpx>=0.28.1",
    "caldav>=3.2.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.1.1",
    "pytest-asyncio>=1.4.0",
    "httpx>=0.28.1",
    "ruff>=0.16.0",
    "mutmut>=3.6.0",
]
```

**Severity calibration — read before prioritising this.** BadHost bypasses
*path-based access control*. This app has none: `main.py` mounts `/health`, `/`,
`/assets` and three `/api/*` routers with no authentication of any kind, on a Pi
on a home LAN. There is nothing to bypass. Treat the pin as hygiene and
supply-chain discipline, **not** as an incident. The CVE is real and the advisory
is credible (CCB Belgium, OSTIF disclosure); its practical impact on *this*
deployment is close to nil.

API-compatibility check against the pinned versions **[verified via package
metadata, not execution]**: the `caldav` surface in use (`DAVClient`,
`principal()`, `calendars()`, `get_display_name()`, `icalendar_component`) is
stable across 1.x–3.x, and `httpx` usage is limited to `AsyncClient` and `post`.
No migration expected.

### 1c. Add a lockfile

Floors alone don't give reproducible builds. `uv lock` or `pip-compile` →
committed lockfile, and `deploy.sh` switches to installing from it. This is what
actually closes the supply-chain gap; 1b only sets a safety floor.

### 1d. `on_event` → `lifespan` (deprecation cleanup, optional)

`main.py:22` uses `@app.on_event("startup")`. Starlette 1.3.1 has **removed**
`on_event`/`add_event_handler` entirely, but FastAPI 0.140.7 **re-implements
them internally** specifically to preserve backward compatibility
(`fastapi/routing.py:6351`, referencing Kludex/starlette#3117) **[verified by
reading both packages' source]**. So this still works on the pinned versions —
it emits a `DeprecationWarning` and is not a blocker. `pytest` has no
`filterwarnings = error`, so it will not fail the suite.

Worth doing as its own commit, since it is a behaviour-preserving refactor
covered by `features/scheduler.feature` and `tests/test_scheduler.py`.

---

## Phase 2 — Frontend dev toolchain (clears the critical + 7 of 8 highs)

This is the one that matters for the audit numbers, and it is **near
drop-in**: verified with **zero changes to any file under `src/`** and with
`vite.config.js` untouched.

| Package | From | To | Note |
|---|---|---|---|
| `vitest` | 2.1.8 | **4.1.10** | fixes the critical |
| `vite` | 6.0.3 | **8.1.5** | forced to 8.x by plugin-react 6 peer |
| `@vitejs/plugin-react` | 4.3.4 | **6.0.4** | peer: `vite ^8.0.0` |
| `@stryker-mutator/core` | 8.6.0 | **9.6.1** | |
| `@stryker-mutator/vitest-runner` | 8.6.0 | **9.6.1** | peer: `vitest >=2.0.0` |
| `eslint` | 8.57.1 | **9.39.5** | **not 10** — see constraint below |
| `eslint-plugin-react` | 7.37.2 | **7.37.5** | |
| `eslint-plugin-react-hooks` | 4.6.2 | **7.1.1** | |
| `jsdom` | 25.0.1 | **30.0.0** | engines: node `^22.22.2 \|\| ^24.15.0 \|\| >=26` |
| `@testing-library/jest-dom` | 6.6.3 | **7.0.0** | |
| `@testing-library/react` | 16.1.0 | **16.3.2** | supports React 18 *and* 19 |
| `@testing-library/user-event` | 14.5.2 | **14.6.1** | |
| `prettier` | 3.3.3 | **3.9.6** | |
| `react` / `react-dom` | 18.3.1 | *unchanged* | deferred to Phase 4 |

### Hard constraint discovered: eslint cannot go to 10

`eslint-plugin-react@7.37.5` (the latest release) declares
`peer eslint@"^3 || ... || ^9.7"` **[verified — npm install fails with ERESOLVE
on eslint 10]**. There is no newer `eslint-plugin-react`. So eslint 9 is the
ceiling until that plugin ships eslint 10 support. This is what leaves 6 of the
8 residual vulnerabilities in Phase 3 unfixable.

### The only manual code change in this phase

eslint 9 defaults to flat config. The repo has legacy `frontend/.eslintrc.js`,
which must become `frontend/eslint.config.js`. Note it currently uses
`module.exports` while `package.json` sets `"type": "module"` — so the migration
must produce genuine ESM (`export default [...]`), not a renamed CJS file.
`eslint-plugin-react-hooks` 4→7 also changes how its recommended config is
consumed under flat config.

Per `CLAUDE.md`, do not run eslint by hand to check this — let the save hook run
it.

### Verified outcomes of Phase 2

Run in a scratchpad copy with the exact versions above:

- **121/121 tests pass** (vitest 4.1.10) — no source or config edits
- `vite build` succeeds — 160.69 kB raw / 50.42 kB gzip
- `stryker run` completes against `ClockCard.jsx` — 62 mutants, **0 errors**,
  runner healthy on vitest 4
- `npm audit`: **21 → 8** vulnerabilities; **critical eliminated**; high 8 → 6,
  moderate 7 → 2, low 5 → 0

### Correction to the audit report

The audit report said `brace-expansion` was "fixable now with `npm audit fix`,
no breaking change," on the strength of npm's `fixAvailable: true`. That is
wrong in practice. Verified on a throwaway copy: plain `npm audit fix` leaves
`package.json` **unchanged**, resolves **zero** of the 21, and reports **24**
afterwards (it adds optional platform-specific rollup packages, which introduce
further advisory paths). There is no free fix — Phase 2 is the fix.

---

## Phase 3 — Residual risk to accept and document

After Phase 2, 8 dev-only advisories remain, from exactly two roots:

**Root 1 — `minimatch` / `brace-expansion` DoS (6 high).** Reached via
`eslint@9` → `@eslint/config-array`, `@eslint/eslintrc`, and via
`eslint-plugin-react`. npm reports the fix as `eslint@10`, which the plugin
peer-range forbids (above). Genuinely blocked upstream.

**Root 2 — `qs` DoS (2 moderate).** `@stryker-mutator/core@9.6.1` →
`typed-rest-client@2.3.1` → `qs@6.15.1` **[verified via `npm ls`]**. Already on
the newest Stryker; nothing to bump.

Accepted-risk rationale: all 8 are **devDependencies**. Production dependency
audit is **`found 0 vulnerabilities`** both before and after **[verified with
`npm audit --omit=dev`]** — `react`, `react-dom`, `leaflet` are clean, and the
Pi serves a static build with no Node process running in production
(`PI_SETUP.md:148`). Both roots are denial-of-service reachable only through
crafted glob patterns or HTTP payloads inside lint/mutation tooling, on
developer machines.

`MUTANTS.md` is specifically the surviving-mutant register, so this does not
belong there. Record it in a short `SECURITY-EXCEPTIONS.md` (advisory ID, root
package, why blocked, revisit trigger) and set the revisit trigger to
"`eslint-plugin-react` ships eslint 10 support."

---

## Phase 4 — React 18 → 19 (separate, optional)

Not security-driven — React 18.3.1 has **no** advisories against it. Do this
only when there is appetite for it, and never in the same commit as Phase 2.

**Migration surface is unusually small.** The whole app is already on modern
APIs: hooks only (`useState`, `useEffect`, `useRef`), `createRoot` already in
`main.jsx`, and **no** `propTypes`, `defaultProps`, `forwardRef`,
`findDOMNode`, string refs, or legacy context anywhere in `src/` **[verified by
grep]**. Nothing React 19 removed is in use.

**[verified]** with `react@19.2.8` / `react-dom@19.2.8` on top of the Phase 2
tree: **121/121 tests pass**, `vite build` succeeds, audit unchanged at 8.

**The one real cost — bundle size.** 160.69 kB → **210.44 kB** raw, 50.42 kB →
**64.63 kB** gzipped: **+31% raw / +28% gzip** for zero functional gain. On a
Raspberry Pi kiosk loading over a LAN this is probably tolerable, but it is a
straight regression with no upside for this app. Recommend deferring Phase 4
until something actually needs a React 19 feature.

---

## Sequencing

```
0.1 deploy.sh npm ci ──┐
                       ├─→ Phase 2 (toolchain + eslint flat config) ─→ Phase 3 (document)
1a apscheduler removal ┤
1b version floors      ├─→ (needs Python 3.14 to verify)
1c lockfile            │
1d lifespan refactor  ─┘

Phase 4 — independent, defer
```

Commit atomically, conventional messages, one concern each:
`chore(deps)` for 1a/1b/1c/2, `refactor(backend)` for 1d, `docs` for Phase 3.

## Two process points needing a decision

1. **`CLAUDE.md` build order** mandates Gherkin-feature-first, then failing
   tests, then implementation. Phases 1a–1c and 2 introduce **no behaviour** —
   they are dependency metadata, and the existing 121 frontend + 10 backend test
   files are the regression net. Writing feature files for them would be
   ceremony. Phase 1d (`on_event` → `lifespan`) *is* a code change, but it is
   behaviour-preserving and already covered by `features/scheduler.feature`.
   Recommend: treat 1a–1c and 2 as exempt, and confirm that reading before
   starting. Mutation testing (rule 4) still applies to any file touched.

2. **Branch naming conflict.** `CLAUDE.md` requires `feature/<name>` cut from
   `main`; this session is pinned to `claude/festive-einstein-dvu5gk`. Needs an
   explicit call on which wins before any commit lands.
