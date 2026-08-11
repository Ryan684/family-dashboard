# Accepted security exceptions

Advisories that `npm audit` / `pip-audit` still report, together with why each
is accepted rather than fixed.

`MUTANTS.md` is the surviving-mutant register and deliberately does not cover
this; this file is the equivalent register for dependency advisories.

Review this file whenever `npm audit` output changes, and at minimum whenever
a revisit trigger below fires.

---

## Current status — 2026-08-11

```
npm audit             found 0 vulnerabilities
npm audit --omit=dev  found 0 vulnerabilities
pip-audit -r backend/requirements.lock   38 packages, 0 vulnerabilities
```

**There are no outstanding accepted exceptions.** Both exceptions recorded on
2026-07-27 (EX-1, EX-2) have been resolved rather than accepted; they are kept
below as history because how they resolved is worth knowing.

---

## EX-1 — `minimatch` / `brace-expansion` ReDoS and OOM — **RESOLVED 2026-08-11**

| | |
|---|---|
| **Advisories** | GHSA-3jxr-9vmj-r5cp, GHSA-mh99-v99m-4gvg, GHSA-rgw5-rvv9-x895 (added later), plus GHSA-5p4m-2wfm-xmqj (`js-yaml`, CVE-2026-59870), GHSA-7p8r-x3mc-p8w7 (`fast-uri`), GHSA-2v37-7h3g-55p8 (`nanoid`) |
| **Was** | Blocked upstream — `npm audit` named `eslint@10` as the fix, and `eslint-plugin-react@7.37.5` caps its peer at `^9.7` |
| **Now** | Fixed by a lockfile refresh alone |

**How it actually resolved.** Not via the predicted route. `eslint-plugin-react`
has still not shipped eslint 10 support — 7.37.5 remains the newest release and
still declares `peer eslint@"^3 || … || ^9.7"`. Instead, upstream backported the
fixes into the release lines our existing caret ranges already admitted:

```
brace-expansion 1.1.13/1.1.16 -> 1.1.18   (minimatch@3.1.5  wants ^1.1.7)
brace-expansion 5.0.8         -> 5.0.9    (minimatch@10.2.6 wants ^5.0.8)
js-yaml         4.3.0         -> 4.3.1    (@eslint/eslintrc wants ^4.3.0)
fast-uri        3.1.4         -> 3.1.5    (ajv@8.18.0       wants ^3.0.1)
nanoid          3.3.16        -> 3.3.18   (postcss          wants ^3.3.16)
```

A plain `npm update` therefore cleared all of them with **no `package.json`
change and no eslint upgrade**. eslint remains on 9.39.5.

**Lesson worth keeping.** The 2026-07-27 entry concluded these were blocked
because it accepted `npm audit`'s suggested remediation (`eslint@10`) as the
only one. That was true at the time, but a suggested fix naming a major
upgrade is worth re-checking against the patched-release lines periodically —
the constraint can dissolve without the blocking package moving at all.

### On eslint 10 specifically

Still not taken, and no longer security-motivated. Investigated on 2026-08-11:

- `npm install eslint@10` fails `ERESOLVE` against `eslint-plugin-react@7.37.5`.
- Forcing it with a peer override does **not** work. eslint 10 removed
  `getFilename`, `getCwd`, `getPhysicalFilename` and `getSourceCode` from the
  rule context (`lib/linter/file-context.js`), and `eslint-plugin-react` calls
  `contextOrFilename.getFilename()` unguarded in `lib/util/version.js:31`. That
  path is reached by `settings: { react: { version: 'detect' } }`, so
  `react/display-name` — which is in `flat.recommended` — crashes outright.
- A workaround exists (pin `react: { version: '18.3.1' }` instead of `detect`),
  and lint then passes with React rules firing. It is deliberately **not**
  taken: it buys nothing now that the advisories are fixed, it forces an
  unsupported peer combination, and the pinned version silently goes stale the
  moment React is upgraded.

**Revisit trigger:** `eslint-plugin-react` publishes a release supporting
eslint 10. This is now a maintenance preference, not a security need.

---

## EX-2 — `qs` DoS via `qs.stringify` — **RESOLVED 2026-08-11**

| | |
|---|---|
| **Advisory** | GHSA-q8mj-m7cp-5q26 |
| **Was** | No fix available — `@stryker-mutator/core@9.6.1` → `typed-rest-client@2.3.1` → `qs@6.15.1` |
| **Now** | Fixed by an `overrides` entry pinning `qs` to `^6.15.3` |

`typed-rest-client@2.3.1` pins `qs` at exactly `6.15.1` rather than a range, so
a lockfile refresh could not move it, and `@stryker-mutator/core` requires
`typed-rest-client ~2.3.0`, putting `typed-rest-client@3.0.0` out of reach. An
override was the only route that did not involve downgrading Stryker.

Verified safe by diffing `qs` 6.15.1 → 6.15.3: the changes are the
`comma` + `encodeValuesOnly` null guard (the advisory itself), a `formatter()`
wrapper on `strictNullHandling`, an undefined-key skip in `stringify`, and a
`delimiter` fix for `charsetSentinel`. No public API change. Stryker verified
healthy afterwards — 62 mutants on `ClockCard.jsx`, 0 errors.

Worth recording that exposure was nil regardless: `typed-rest-client` builds
its stringify options with `arrayFormat: 'repeat'` while the advisory requires
`'comma'`, and Stryker only reaches `typed-rest-client` through its optional
dashboard reporter, which `stryker.config.json` does not configure.

**Revisit trigger:** remove the override once `@stryker-mutator/core` ships a
`typed-rest-client` bump that carries a patched `qs` on its own.

---

## Standing context

All advisories recorded in this file have been **devDependencies**. The three
production dependencies — `react`, `react-dom`, `leaflet` — have never carried
one. Nothing here ships to the Raspberry Pi at runtime: the Pi serves a static
`frontend/dist/` build from FastAPI and runs no Node process in production
(`PI_SETUP.md`, Part 7).

## Backend

No advisories outstanding — `pip-audit` reports 0 across all 38 packages in the
committed `backend/requirements.lock`. The two CVEs identified in the original
audit were both resolved rather than accepted:

- **CVE-2026-48710** (Starlette host-header auth bypass, "BadHost") — fixed by
  pinning `starlette>=1.0.1` explicitly in `backend/pyproject.toml`. FastAPI's
  own metadata asks only for `starlette>=0.46.0`, a range that still admits
  every affected version, so relying on FastAPI's constraint was not enough.
  Worth recording that the practical exposure was minimal regardless: the
  advisory describes bypassing *path-based access control*, and this app has no
  authentication on any route.
- **CVE-2026-31072** (APScheduler RCE via insecure deserialization) — removed
  entirely by dropping the `apscheduler` dependency, which was declared in
  `pyproject.toml` but imported nowhere.

### Known deprecation, not an advisory

`starlette.testclient` emits `StarletteDeprecationWarning: Using httpx with
starlette.testclient is deprecated; install httpx2 instead` during the backend
test run. Not a security issue and not currently failing anything — `pytest`
sets no `filterwarnings = error`. Confirmed unchanged in Starlette 1.6.0, so a
lockfile refresh will not escalate it to an error, but it does signal a future
`httpx` → `httpx2` migration.
