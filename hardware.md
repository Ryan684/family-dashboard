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
- Python 3.14 via deadsnakes PPA (consistent with existing home automation project setup)
- Project lives in `~/projects/family-dashboard/`
- Virtual environment at `.venv`
- Systemd service to start the FastAPI backend on boot
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
0  22 * * * XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --off HDMI-A-1
```

Chromium is deliberately restarted in the *same* cron line as `wlopm --on`, right after it — this guarantees Chromium only ever launches once the output is confirmed live. It is **not** restarted by the nightly deploy (`deploy.sh`, which runs at 02:00) — see "Known issue" below for why.

The poll window (`POLL_WINDOW_START` / `POLL_WINDOW_END` in `.env`) should match these timings. To test the display power toggle manually:

```bash
XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --off HDMI-A-1   # turn off
XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --on HDMI-A-1    # turn on
```

---

## Troubleshooting

### Resolved: Chromium doesn't go fullscreen when launched while the display is off

**Symptom**: the dashboard shows an ordinary Chromium window — tab strip, address bar, bookmarks bar — instead of the fullscreen kiosk view, even though the running process was launched correctly and had `--kiosk` in its command line the whole time.

**Root cause (confirmed, July 2026)**: Chromium was being killed and relaunched by `deploy.sh` at 02:00 — squarely inside the display-off window (was `22:00`-`06:30`, see the crontab above). Launching a brand-new Chromium window while the Wayland output is powered off (`wlopm --off`) means its fullscreen request has no live output to negotiate against, so it falls back to an ordinary window — **every single time**, not intermittently. It then just sits that way, unchanged, until the display powers back on and reveals the same already-broken window. This was confirmed directly: manually powering the display off, killing and relaunching Chromium with the display still off, then powering it back on reproduced the bug on demand; toggling the display off and on around an *already-fullscreen* Chromium left it untouched, ruling out the power toggle itself as the cause.

Earlier hypotheses along the way, ruled out in order: a missing `--kiosk` flag (confirmed present throughout), a stray boot-time autostart script (none exists), a Pi reboot (`uptime -s` showed none — `labwc`/`lightdm` had been running for over a month), an `apt` package upgrade landing overnight (`apt-daily-upgrade.service` completed in ~1 second, a no-op), a custom `labwc` window rule (no custom `rc.xml` exists), the deploy script failing partway (logs showed a clean `Deploy complete.` every time), and — briefly — the display power toggle itself disrupting an already-good window (disproved by the test above). The actual cause was launch *timing* relative to the display's power state, not any of these.

**Fix**: Chromium is no longer restarted by `deploy.sh`. It's now restarted by a separate script, `scripts/restart-kiosk.sh`, chained directly onto the crontab line that powers the display on:

```cron
30 6 * * * XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --on HDMI-A-1 && /home/pi/projects/family-dashboard/scripts/restart-kiosk.sh >> /home/pi/projects/family-dashboard/kiosk-restart.log 2>&1
```

This guarantees Chromium only ever launches once the output is confirmed live, regardless of whether a deploy happened that night. `restart-kiosk.sh` carries no SHA/deploy-state gating — it restarts Chromium unconditionally every morning, which is cheap and invisible (the screen has just come on) and means a fresh, clean Chromium process every single day rather than one that potentially lives for days across deploys.

**One-time manual step required**: this crontab change lives on the Pi, not in this repo — `crontab -e` and replace the old `wlopm --on HDMI-A-1` line with the version above (adjusting the repo path if it differs from `/home/pi/projects/family-dashboard`).

**Log file note**: the cron line above logs to `kiosk-restart.log` *inside the repo*, not `/var/log/family-dashboard-deploy.log`. That's deliberate, not a typo — `deploy.sh` can append to the `/var/log` file because it runs as a systemd service (`family-dashboard-deploy.service`), and systemd itself opens that file (as root) before dropping to the `User=pi` process, so the child just inherits an already-open, writable descriptor. Cron has no such privilege step: it runs the command as plain user `pi`, and `pi` has no write permission on that root-owned, mode-644 file — the `>>` redirect fails with "Permission denied" *before `restart-kiosk.sh` even starts running*, with the error silently discarded (`cron: (CRON) info (No MTA installed, discarding output)`), which is exactly what happened the first time this crontab line was installed: zero log output, and Chromium's `STIME` showing it had never been touched by the new mechanism at all. `kiosk-restart.log`, by contrast, is created fresh by `pi`'s own cron job the first time it runs, so `pi` owns it outright.

`restart-kiosk.sh` still logs a timestamped line noting whether the previous Chromium process exited cleanly or needed a forced kill — kept from the original mitigation, useful for spotting a stuck/crash-looping Chromium independent of this bug:

```
2026-07-22T06:30:02+01:00 chromium-relaunch: previous process exited cleanly.
```
