# Accepted security exceptions

Advisories that `npm audit` / `pip-audit` still report after the 2026-07-27
dependency upgrade, together with why each is accepted rather than fixed.

`MUTANTS.md` is the surviving-mutant register and deliberately does not cover
this; this file is the equivalent register for dependency advisories.

Review this file whenever `npm audit` output changes, and at minimum whenever
the revisit trigger below fires.

---

## Scope: all remaining advisories are devDependencies

```
npm audit             8 vulnerabilities (6 high, 2 moderate)
npm audit --omit=dev  found 0 vulnerabilities
```

The three production dependencies — `react`, `react-dom`, `leaflet` — have no
advisories against them. Nothing below ships to the Raspberry Pi at runtime:
the Pi serves a static `frontend/dist/` build from FastAPI and runs no Node
process in production (`PI_SETUP.md`, Part 7). Every advisory below is
reachable only inside lint or mutation-testing tooling on a developer machine.

---

## EX-1 — `minimatch` / `brace-expansion` ReDoS and OOM (6 high)

| | |
|---|---|
| **Advisories** | GHSA-3jxr-9vmj-r5cp (exponential-time expansion of consecutive non-expanding `{}` groups), GHSA-mh99-v99m-4gvg (unbounded expansion length → OOM crash) |
| **Reported packages** | `brace-expansion`, `minimatch`, `@eslint/config-array`, `@eslint/eslintrc`, `eslint`, `eslint-plugin-react` |
| **Severity** | high (CVSS 5.3 and 7.5, both availability-only) |
| **Status** | **Blocked upstream** |

`npm audit` names `eslint@10` as the fix. We cannot take it:
`eslint-plugin-react@7.37.5` is the newest release and declares
`peer eslint@"^3 || … || ^9.7"`, so installing eslint 10 fails with
`ERESOLVE`. There is no newer `eslint-plugin-react`. eslint 9.39.5 is
therefore the ceiling, and it pulls `minimatch@3.1.5` transitively:

```
eslint@9.39.5
  +-- @eslint/config-array@0.21.2 -> minimatch@3.1.5
  +-- @eslint/eslintrc@3.3.6     -> minimatch@3.1.5
  `-- minimatch@3.1.5
eslint-plugin-react@7.37.5       -> minimatch@3.1.5
@stryker-mutator/core@9.6.1      -> minimatch@10.2.6
```

**Why accepted.** Both advisories are denial-of-service only — no
confidentiality or integrity impact. Reaching them requires feeding a crafted
glob pattern to `minimatch`, and the only globs in play are the ones written
in `eslint.config.js` and `stryker.config.json`, both committed to this repo
and both authored by us. There is no path by which dashboard data, a CalDAV
response, or a travel/weather API payload reaches a glob parser. The worst
outcome is a developer hanging their own lint run.

**Revisit trigger:** `eslint-plugin-react` publishes a release supporting
eslint 10. Then upgrade both together and this exception disappears.
Alternatively, `npm audit fix --force` would downgrade `eslint-plugin-react`
to 7.22.0 — a *downgrade* presented as a fix, and not worth taking.

---

## EX-2 — `qs` DoS via `qs.stringify` (2 moderate)

| | |
|---|---|
| **Advisory** | GHSA-q8mj-m7cp-5q26 — `qs.stringify` crashes with `TypeError` on null/undefined entries in comma-format arrays when `encodeValuesOnly` is set |
| **Reported packages** | `qs`, `typed-rest-client` |
| **Severity** | moderate |
| **Status** | **No fix available** |

```
@stryker-mutator/core@9.6.1 -> typed-rest-client@2.3.1 -> qs@6.15.1
```

**Why accepted.** Already on the newest Stryker (9.6.1); the vulnerable `qs`
arrives through its HTTP client and there is nothing to bump. The affected
code path is `qs.stringify` with `encodeValuesOnly`, used by Stryker only when
talking to its own optional dashboard reporter — which this project does not
use (`stryker.config.json` configures `html`, `clear-text`, and `progress`
reporters only).

**Revisit trigger:** `@stryker-mutator/core` ships a `typed-rest-client` bump.

---

## Backend

No advisories outstanding. The two CVEs identified in the audit were both
resolved rather than accepted:

- **CVE-2026-48710** (Starlette host-header auth bypass, "BadHost") — fixed by
  pinning `starlette>=1.0.1` explicitly in `backend/pyproject.toml`. FastAPI's
  own metadata asks only for `starlette>=0.46.0`, a range that still admits
  every affected version, so relying on FastAPI's constraint was not enough.
  Resolved version is 1.3.1. Worth recording that the practical exposure was
  minimal regardless: the advisory describes bypassing *path-based access
  control*, and this app has no authentication on any route.
- **CVE-2026-31072** (APScheduler RCE via insecure deserialization) — removed
  entirely by dropping the `apscheduler` dependency, which was declared in
  `pyproject.toml` but imported nowhere.

### Known deprecation, not an advisory

`starlette.testclient` emits `StarletteDeprecationWarning: Using httpx with
starlette.testclient is deprecated; install httpx2 instead` during the backend
test run. Not a security issue and not currently failing anything — `pytest`
sets no `filterwarnings = error` — but it signals a future `httpx` → `httpx2`
migration.
