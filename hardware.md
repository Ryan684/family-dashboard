# Family Dashboard — Hardware & Deployment Reference

Human reference only. Not needed during coding sessions.

---

## Hardware Options

### Recommended — Raspberry Pi 5 + Official Raspberry Pi Monitor (SC0940)

The official Pi monitor is purpose-built for the Pi 5: plug-and-play HDMI, VESA 100×100, powered via USB-C from its own supply (no draw on the Pi's USB budget), and IPS panel with 178° viewing angles. No driver configuration required.

This is not a touchscreen — interaction (adjusting config, restarting services) is done over SSH or with a wireless keyboard. For a dashboard that auto-refreshes every 60 seconds, this is not a meaningful limitation.

Viewing distance is ~1m rather than 1.5–2m; place on a counter or cabinet at arm's length rather than across the room.

| Component | Source | ~Cost |
|---|---|---|
| Raspberry Pi 5 (4GB) | The Pi Hut / Pimoroni | £55 |
| Official Raspberry Pi Monitor (SC0940) | The Pi Hut | £96 |
| Pi VESA mount bracket | Amazon / The Pi Hut / 3D print | £10–15 |
| Freestanding VESA monitor arm | Amazon | £30–50 |
| MicroSD card (32GB+) | Any | £8 |
| Official Pi 5 power supply | The Pi Hut | £12 |
| **Total** | | **~£211–236** |

**No separate storage.** A USB SSD was briefly on this list for the budget planner, whose
database was to live on it. That was dropped on 2026-08-19: the stated justification was
SD wear-out, which does not survive scrutiny at that app's write volume — single-digit MB
a month against SD endurance measured in terabytes. The real risks are power-loss
corruption and outright card death, and both take the whole system rather than just one
file. What bounds the damage there is the budget planner's offsite backup, not the storage
medium. Its database now lives at `/home/pi/budget-data/` on the SD card; the reasoning is
in that repo's README under "Create the data directory".

If you later want to reduce the probability as well as bound the impact, an old SSD in a
USB caddy drops straight in — the budget planner only needs its `DATABASE_URL` and
`BACKUP_REPO_DIR` repointed. A small UPS would address the power-loss failure mode more
directly. Note the SC0940 takes no power from the Pi, so the official 27W supply's 1.6A
USB budget is entirely available for a bus-powered drive.

**On the 4GB model**: bought and fixed. It is enough for both apps, but it is the
binding constraint on this Pi — see "Sharing the Pi with the budget planner" below for
the memory budget and the measures that keep it workable.

**Monitor spec:**

| Model | Size | Resolution | Panel | Touch | VESA | Source |
|---|---|---|---|---|---|---|
| Raspberry Pi Monitor SC0940 | 15.6" | 1920×1080 | IPS, 250 nits, anti-glare | None | 100×100 | The Pi Hut (~£96) |

### Fallback — Android Tablet (Lenovo Tab M10 Plus)

- ~£150–180, no Pi required
- Uses Fully Kiosk Browser (~£7) to lock to dashboard URL on boot
- Battery management required for permanent wall mounting
- More setup friction; less control over the OS

### Not Recommended

- **Amazon Fire HD** — locked-down OS, sideloading friction
- **iPad** — expensive for a dedicated display; kiosk mode requires workarounds
- **Pi-specific displays under 13"** — too small for multi-card dashboard readability even at 1m

---

## Chosen Hardware Path

**Raspberry Pi 5 (4GB) + Official Raspberry Pi Monitor (SC0940, 15.6")**, to be purchased once the software is stable and tested on localhost.

---

## Physical Setup

### Pi mounting

The Pi mounts on the back of the monitor using a **VESA bracket**, making the whole unit self-contained with short internal cables. Options:

- **Ready-made bracket** — search "Raspberry Pi 5 VESA mount" on Amazon or The Pi Hut; fits 75x75mm or 100x100mm VESA patterns; ~£10–15
- **3D printed bracket** — well-rated designs on Printables.com if you have printer access; free to print, perfect fit for the Pi 5 case

With the Pi VESA-mounted behind the monitor, the only external cables are one power cable to the monitor (which also powers the Pi via USB) and a HDMI cable between them.

### Temporary freestanding setup (pre-move)

Rather than wall mounting before settling into the new house, use a **freestanding VESA monitor arm** with a weighted base sitting on a kitchen counter or sideboard:

- Holds the monitor at the right height and angle with no drilling
- The Pi is hidden on the back — looks like a single unit
- Fully portable — moves to the new house in minutes
- When ready to wall mount permanently, swap the freestanding arm for a wall bracket using the same VESA holes on the monitor

Look for a single-arm freestanding VESA stand supporting up to 27" and 10kg, with a 100x100mm VESA plate — widely available on Amazon for £30–50 (e.g. VIVO, Perlegear, WALI).

### Cable management

With the freestanding arm, run both power cables (monitor + Pi) down the back of the arm pole and bundle with velcro ties. A single cable run from the base to a nearby socket keeps the setup tidy without any wall work.

---

## Raspberry Pi Setup

- OS: **Raspberry Pi OS Bookworm** (64-bit, desktop)
- Python 3.14 via **uv** (`PI_SETUP.md`, Part 6) — one interpreter, shared with the
  budget planner. Earlier revisions of this doc said "via deadsnakes PPA", which was
  never possible: deadsnakes is an Ubuntu PPA with no Debian or Raspberry Pi OS
  packages. `PI_SETUP.md` previously documented pyenv, which worked but compiles from
  source for 10–20 minutes on the Pi; uv downloads a prebuilt aarch64 build instead.
- Project lives in `~/projects/family-dashboard/`
- Virtual environment at `.venv`
- Systemd service to start the FastAPI backend on boot, bound to `127.0.0.1:8000`
- Chromium kiosk autostart after backend service is healthy

### Kiosk boot command

Chromium is not autostarted directly on boot — it's launched and relaunched by `scripts/restart-kiosk.sh`, chained onto the crontab line that powers the display on (see below). This matters: Chromium must never be launched while the display output is off (see "Known issue" under Troubleshooting).

### Display schedule (HDMI on/off via cron)

The display is on only during the morning window. A cron job on the Pi controls the HDMI output via `wlopm` (a Wayland output-power tool, talking to the compositor directly — not `vcgencmd`, despite what earlier revisions of this doc said).

```bash
crontab -e
```

```cron
# Family dashboard display schedule
30 6 * * * XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --on HDMI-A-1 && /home/pi/projects/family-dashboard/scripts/restart-kiosk.sh >> /home/pi/projects/family-dashboard/kiosk-restart.log 2>&1
0  22 * * * XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --off HDMI-A-1 && /home/pi/projects/family-dashboard/scripts/stop-kiosk.sh >> /home/pi/projects/family-dashboard/kiosk-restart.log 2>&1
```

Chromium is deliberately restarted in the *same* cron line as `wlopm --on`, right after it — this guarantees Chromium only ever launches once the output is confirmed live. It is **not** restarted by the nightly deploy (`deploy.sh`, which runs at 02:00) — see "Known issue" below for why.

The 22:00 line is the mirror image: `stop-kiosk.sh` kills Chromium once the output is
dark, freeing roughly half a gigabyte for the whole 22:00–06:30 window. That window holds
the dashboard's deploy (02:00) and two of the budget planner's backup runs (21:30 and
03:30), and on a 4GB Pi it is the difference between a build spike having room and the
kernel OOM-killing a live service. Nothing relaunches Chromium
until the 06:30 line, which is exactly right — launching it against a powered-off output
is the bug described below. See "Sharing the Pi with the budget planner".

The poll window (`POLL_WINDOW_START` / `POLL_WINDOW_END` in `.env`) should match these timings. To test the display power toggle manually:

```bash
XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --off HDMI-A-1   # turn off
XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --on HDMI-A-1    # turn on
```

---

## Sharing the Pi with the budget planner

This Pi also hosts the **budget planner** (`ryan684/budget-planner`), a FastAPI + React
app the household reaches from phones. The two are independent deployments that share
one box, one Python interpreter and one Node install. Reconciled 2026-08-17.

### Allocation

| | family-dashboard | budget-planner |
|---|---|---|
| Backend port | 8000, bound `127.0.0.1` | 8001, bound `0.0.0.0` |
| Frontend | `dist/` served by its own FastAPI | `dist/` served by its own FastAPI |
| Systemd units | `family-dashboard`, `family-dashboard-deploy.{service,timer}` | `budget-backend`, `budget-backup.{service,timer}` |
| Persistent data | none (stateless) | `/home/pi/budget-data/` (SD card) |
| Scheduled job | deploy, 02:00 | backup, 03:30 / 09:30 / 15:30 / 21:30 |
| Repo | `~/projects/family-dashboard` | `~/projects/budget-planner` |

Both backends previously bound `0.0.0.0:8000`. Whichever started second would have died
with "address already in use", and with `Restart=on-failure` it would have crash-looped
indefinitely. The budget planner moved to 8001 because this app was already deployed.

**Why the dashboard is now on `127.0.0.1`**: it is consumed only by Chromium on this
same machine — the frontend fetches a relative `/api` from the FastAPI process that
served it. It has no authentication of any kind, and the budget planner brings Tailscale
to this Pi, which would otherwise put the dashboard's calendar, commute and home-location
data on the tailnet for anything that joins it. Binding to loopback costs nothing here.
The trade-off is that the dashboard is no longer viewable from a phone on the LAN; if you
want that back, bind `0.0.0.0` again and accept the exposure, or port the budget planner's
`APP_PIN` gate across.

### Shared runtimes

Both repos target the same versions, deliberately — install each once, not per project:

| | Version | Installed by |
|---|---|---|
| Python | 3.14 | uv (`PI_SETUP.md`, Part 6) |
| Node | 22.x | NodeSource (`PI_SETUP.md`, Part 7) |

Each app keeps its own `backend/.venv` built from that one interpreter, and its own
`frontend/node_modules`. Their Python and npm dependency *sets* differ and are pinned
independently — family-dashboard is on React 18 and ESLint 9, budget-planner on React 19
and ESLint 10. That divergence is fine and should not be chased: only the `node` and
`python` binaries are actually shared.

### Memory budget (4GB)

Steady state is comfortable; the transients are what matter. Estimates, not measurements:

| | Daytime (kiosk live) | Overnight (after `stop-kiosk.sh`) |
|---|---|---|
| OS + labwc session | ~500 MB | ~500 MB |
| Chromium (kiosk, Leaflet) | ~400–700 MB | 0 |
| 2 × uvicorn | ~200–250 MB | ~200–250 MB |
| **Free of 4GB** | **~2.5–2.9 GB** | **~3.2–3.3 GB** |

The risk was never the steady state — it was `npm ci` + `vite build` at 02:00 landing on
top of a resident Chromium. Four measures address it, in order of leverage:

1. **`stop-kiosk.sh` at 22:00** removes Chromium from the overnight window entirely.
2. **`MemoryHigh=1.5G` / `MemoryMax=2G`** on `family-dashboard-deploy.service` throttles
   an overshooting build into reclaim instead of letting the OOM killer choose a victim.
3. **`NODE_OPTIONS=--max-old-space-size=1024`** in `deploy.sh` stops V8 sizing its heap
   from total RAM (~2GB on this box) when the build needs a fraction of that.
4. **Timers spaced** — deploy 02:00; the budget backup runs 6-hourly from 03:30, chosen so
   no run lands in 02:00–03:00. `npm ci` + `vite build` can run 15–30 minutes here.

**Never run mutation testing on the Pi.** mutmut re-runs the whole suite per mutant and
Stryker spawns parallel Vitest workers; either will exhaust 4GB with the kiosk live. Both
repos' `CLAUDE.md` carve this out, and `scripts/assert-not-pi.sh` refuses to run there —
which matters because Claude Code is installed on this Pi and reads `CLAUDE.md`, whose
build order otherwise says mutation tests are mandatory.

### Still recommended, not done

**Move the frontend builds off the Pi.** Building `dist/` in CI and having `deploy.sh`
fetch the artifact would remove `npm ci` — the largest transient memory consumer and the
heaviest SD-card writer — along with both `node_modules` trees. Deferred to its own task:
the measures above already remove the memory collision, so this is now an optimisation.

---

## Troubleshooting

### Resolved: Chromium doesn't go fullscreen when launched while the display is off

**Symptom**: the dashboard shows an ordinary Chromium window — tab strip, address bar, bookmarks bar — instead of the fullscreen kiosk view, even though the running process was launched correctly and had `--kiosk` in its command line the whole time.

**Root cause (confirmed, July 2026)**: Chromium was being killed and relaunched by `deploy.sh` at 02:00 — squarely inside the display-off window (was `22:00`-`06:30`, see the crontab above). Launching a brand-new Chromium window while the Wayland output is powered off (`wlopm --off`) means its fullscreen request has no live output to negotiate against, so it falls back to an ordinary window — **every single time**, not intermittently. It then just sits that way, unchanged, until the display powers back on and reveals the same already-broken window. This was confirmed directly: manually powering the display off, killing and relaunching Chromium with the display still off, then powering it back on reproduced the bug on demand; toggling the display off and on around an *already-fullscreen* Chromium left it untouched, ruling out the power toggle itself as the cause.

Earlier hypotheses along the way, ruled out in order: a missing `--kiosk` flag (confirmed present throughout), a stray boot-time autostart script (checked `~/.config/autostart/*.desktop` — wrong location, see correction below), a Pi reboot (`uptime -s` showed none — `labwc`/`lightdm` had been running for over a month), an `apt` package upgrade landing overnight (`apt-daily-upgrade.service` completed in ~1 second, a no-op), a custom `labwc` window rule (no custom `rc.xml` exists), the deploy script failing partway (logs showed a clean `Deploy complete.` every time), and — briefly — the display power toggle itself disrupting an already-good window (disproved by the test above). The actual cause was launch *timing* relative to the display's power state, not any of these.

**Correction**: there *is* a boot-time autostart trigger — `~/.config/labwc/autostart` (see `PI_SETUP.md`, Part 14) — missed initially because `~/.config/autostart/*.desktop` (the generic XDG location) was checked instead of labwc's own file. It wasn't the cause of this particular incident (the Pi hadn't rebooted in over a month), but it's a real, independent risk: it fires on every boot, at any time, including inside the display-off window. It's now been updated to call `scripts/restart-kiosk.sh` directly instead of duplicating the launch command, which means it automatically gets the same protection described below.

**Fix**: Chromium is no longer restarted by `deploy.sh`. It's now restarted by a separate script, `scripts/restart-kiosk.sh`, chained directly onto the crontab line that powers the display on:

```cron
30 6 * * * XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --on HDMI-A-1 && /home/pi/projects/family-dashboard/scripts/restart-kiosk.sh >> /home/pi/projects/family-dashboard/kiosk-restart.log 2>&1
```

This guarantees Chromium only ever launches once the output is confirmed live, regardless of whether a deploy happened that night. `restart-kiosk.sh` carries no SHA/deploy-state gating — it restarts Chromium unconditionally every morning, which is cheap and invisible (the screen has just come on) and means a fresh, clean Chromium process every single day rather than one that potentially lives for days across deploys.

`restart-kiosk.sh` is also called directly from `~/.config/labwc/autostart` on every boot (`PI_SETUP.md`, Part 14) — a trigger cron has no control over, and one that can fire at any time, including inside the display-off window. Rather than duplicate a "is the display actually on" check in that untracked, Pi-local file, the guard lives in the script itself: it checks the current time against the scheduled display-on window (default `06:30`-`22:00`, overridable via `KIOSK_ON_HHMM`/`KIOSK_OFF_HHMM`) and refuses to touch Chromium if it's outside it, logging why and exiting instead. The cron-triggered call is always safely inside the window by construction (it only ever fires right after `wlopm --on`), so this only changes behaviour for the autostart trigger.

**One-time manual steps required**: both of these live on the Pi, not in this repo:
- `crontab -e` and replace the old `wlopm --on HDMI-A-1` line with the version above (adjusting the repo path if it differs from `/home/pi/projects/family-dashboard`).
- Replace `~/.config/labwc/autostart` with the version in `PI_SETUP.md`, Part 14, so it calls `restart-kiosk.sh` instead of launching Chromium directly.

**Log file note**: the cron line above logs to `kiosk-restart.log` *inside the repo*, not `/var/log/family-dashboard-deploy.log`. That's deliberate, not a typo — `deploy.sh` can append to the `/var/log` file because it runs as a systemd service (`family-dashboard-deploy.service`), and systemd itself opens that file (as root) before dropping to the `User=pi` process, so the child just inherits an already-open, writable descriptor. Cron has no such privilege step: it runs the command as plain user `pi`, and `pi` has no write permission on that root-owned, mode-644 file — the `>>` redirect fails with "Permission denied" *before `restart-kiosk.sh` even starts running*, with the error silently discarded (`cron: (CRON) info (No MTA installed, discarding output)`), which is exactly what happened the first time this crontab line was installed: zero log output, and Chromium's `STIME` showing it had never been touched by the new mechanism at all. `kiosk-restart.log`, by contrast, is created fresh by `pi`'s own cron job the first time it runs, so `pi` owns it outright.

`restart-kiosk.sh` still logs a timestamped line noting whether the previous Chromium process exited cleanly or needed a forced kill — kept from the original mitigation, useful for spotting a stuck/crash-looping Chromium independent of this bug:

```
2026-07-22T06:30:02+01:00 chromium-relaunch: previous process exited cleanly.
```
