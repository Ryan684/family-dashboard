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

```bash
chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:8000
```

### Display schedule (HDMI on/off via cron)

The display is on only during the morning window. A cron job on the Pi controls HDMI power via `vcgencmd` — no smart plug required.

```bash
crontab -e
```

```cron
# Family dashboard display schedule
30 6 * * * /usr/bin/vcgencmd display_power 1   # Screen on at 06:30
0  9 * * * /usr/bin/vcgencmd display_power 0   # Screen off at 09:00
```

The poll window (`POLL_WINDOW_START` / `POLL_WINDOW_END` in `.env`) should match these timings. To test manually:

```bash
vcgencmd display_power 0   # turn off
vcgencmd display_power 1   # turn on
```

---

## Troubleshooting

### Known issue: Chromium sometimes doesn't go fullscreen on launch

**Symptom**: the dashboard shows an ordinary Chromium window — tab strip, address bar, bookmarks bar — instead of the fullscreen kiosk view, even though the running process was launched correctly.

**How to tell this is what's happening** (over SSH):

```bash
ps aux | grep -i chromium | grep -v grep
```

If the process is there with `--kiosk --user-data-dir=/home/pi/.cache/chromium-kiosk ...` in its command line, the launch itself was correct — this is not a launched-without-kiosk-flags problem (that was a different, already-fixed bug — see `3cae647` and `9f42c96` in git history, which addressed Chromium's session-restore silently reopening a previous *windowed* session after an unclean shutdown).

**What we've ruled out** (investigated on a live occurrence, July 2026):
- A missing/incorrect `--kiosk` flag — confirmed present in the running process.
- A stray boot-time autostart script outside `deploy.sh` — none exists (checked `crontab`, `~/.config/autostart`, `systemctl --user`).
- A Pi reboot re-triggering an unhardened launch path — `uptime -s` showed no reboot; the compositor (`labwc`) and display manager (`lightdm`) had been running continuously for over a month.
- An `apt` package upgrade (e.g. to Chromium or the compositor) landing overnight — `apt-daily-upgrade.service` ran but completed in ~1 second (a no-op), and `chromium` didn't appear in `/var/log/apt/history.log`.
- A custom `labwc` window rule forcing decorations — no custom `~/.config/labwc/rc.xml` exists; it's stock behaviour.
- The deploy script itself failing partway (e.g. a failed `npm run build` aborting before the Chromium restart) — the deploy log showed a clean `Deploy complete.`

**Current best explanation**: an intermittent race in Chromium's own Wayland startup handshake — it requests fullscreen (`xdg_toplevel.set_fullscreen`) before the compositor's `configure` response and its own GPU/rendering setup (the Pi's V3D driver) are ready to honour it, and falls back to a normal window instead of retrying. This is a known class of issue for Chromium kiosk deployments on Wayland in general, not specific to this project's code. Manually killing and relaunching the exact same command fixes it immediately, which is why it looks like a launch-time coin flip rather than a persistent misconfiguration.

**Current mitigation**: `deploy.sh` logs a timestamped line every time it relaunches Chromium, noting whether the previous process exited cleanly or needed a forced kill (`/var/log/family-dashboard-deploy.log`) — e.g.:

```
2026-07-22T02:00:14+01:00 chromium-relaunch: previous process exited cleanly.
```

There's no automatic recovery yet — this is intentionally observation-only for now, to build up a real incidence history (how often this actually happens) before adding retry logic. Note it only tells you a relaunch happened and whether a forced kill was needed, not whether kiosk mode was actually achieved visually — there's no cheap way to check that from a script yet (would need a screenshot tool like `grim` plus pixel sampling, neither currently installed).

**Manual recovery** (SSH in):

```bash
pkill -f chromium || true
for _ in $(seq 1 10); do
    pgrep -f chromium >/dev/null 2>&1 || break
    sleep 1
done
pkill -9 -f chromium >/dev/null 2>&1 || true

rm -rf "$HOME/.cache/chromium-kiosk"

setsid bash -c "XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 chromium --ozone-platform=wayland --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble --password-store=basic --user-data-dir='$HOME/.cache/chromium-kiosk' http://localhost:8000 >/dev/null 2>&1" &
disown
```

**Possible future improvements**, not yet implemented (revisit once the log above shows how often this actually recurs):
- Verify fullscreen state after launch (e.g. a `grim` screenshot + pixel sample against the dashboard's background colour) and retry a bounded number of times if it didn't take.
- A second scheduled relaunch shortly before the 06:30 display-on cron, independent of whether a deploy happened that night — currently Chromium is only ever relaunched when new commits are deployed, so a flake on a no-deploy night has no self-correction until the next code change.
