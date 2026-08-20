# Pi Setup Guide — Family Dashboard

Complete walkthrough from unboxing to a running kiosk dashboard.
Hardware assumed: **Raspberry Pi 5 (4GB) + Official Raspberry Pi Monitor SC0940 (15.6")**.
No separate storage — the budget planner sharing this Pi keeps its database on the SD
card (see `hardware.md`).

> **Already have this Pi running?** Don't re-run this guide. Parts 5, 6, 10, 13 and 15
> changed on 2026-08-17 when the budget planner was reconciled onto the same box — the
> backend moved to `127.0.0.1`, Python moved from pyenv to uv, and Chromium is now
> stopped overnight. **Part 19 lists exactly what to change on a running Pi, in order.**

---

## Part 1 — Flash the SD card (on your laptop, before touching the Pi)

This is done on your laptop. The imager lets you pre-configure WiFi and SSH so the Pi is ready to connect immediately on first boot — no keyboard or separate monitor needed.

**1.1** Download and install [Raspberry Pi Imager](https://www.raspberrypi.com/software/) on your laptop.

**1.2** Insert your microSD card (32 GB or larger) into your laptop.

**1.3** Open Raspberry Pi Imager and choose:
- **Device:** Raspberry Pi 5
- **OS:** Raspberry Pi OS (64-bit) — the Desktop version under "Raspberry Pi OS (other)"
- **Storage:** your SD card

**1.4** Click the **edit settings** (gear icon) before writing. Configure:

| Setting | Value |
|---|---|
| Hostname | `dashboard` (or whatever you prefer) |
| Username | `pi` |
| Password | a password you'll remember |
| WiFi SSID | your home WiFi name |
| WiFi password | your home WiFi password |
| WiFi country | GB |
| Enable SSH | yes — use password authentication |

**1.5** Click **Save**, then **Yes** to apply settings, then **Write**. Wait for the write and verify to complete (~5 minutes).

**1.6** Remove the SD card from your laptop.

---

## Part 2 — Physical assembly

**2.1** Attach the Pi 5 to the VESA mount bracket. The bracket screws onto the Pi's four mounting holes and exposes a VESA 75×75 or 100×100 pattern on the other side.

**2.2** Mount the bracket (with the Pi on it) to the back of the SC0940 monitor using the monitor's VESA 100×100 holes. The Pi sits neatly behind the screen with no dangling cables.

**2.3** Connect a short **HDMI cable** from the Pi's HDMI port to the monitor's HDMI input.

**2.4** The monitor powers itself from its own USB-C supply. The Pi uses the official **Pi 5 USB-C power supply**. Plug both into their respective cables — you'll have two power cables total.

**2.5** Insert the flashed SD card into the Pi's SD slot.

**2.6** Sit the whole unit on the freestanding VESA arm. Run both power cables down the back of the arm and bundle with a velcro tie.

---

## Part 3 — First boot

**3.1** Plug in the monitor's power cable and the Pi's power cable. The Pi boots as soon as power is connected — there is no power button.

**3.2** The monitor should display the Pi desktop. First boot takes 2–3 minutes and may reboot once automatically.

**3.3** From your laptop, find the Pi on your network and SSH in:

```bash
ssh pi@dashboard.local
```

If `.local` doesn't resolve after a minute, check your router's admin page for the IP address assigned to `dashboard`, then use `ssh pi@<ip-address>` instead.

**3.4** Accept the SSH fingerprint prompt and enter your password.

You're now connected to the Pi. The rest of this guide runs over SSH — the Pi's monitor just shows the desktop idling. You can leave it displaying the desktop for now.

---

## Part 4 — System update

Run these immediately after first boot.

```bash
sudo apt update && sudo apt full-upgrade -y
```

This takes a few minutes. When it finishes, reboot:

```bash
sudo reboot
```

Wait ~30 seconds, then SSH back in:

```bash
ssh pi@dashboard.local
```

---

## Part 5 — Install system dependencies

```bash
sudo apt install -y build-essential curl git sqlite3 chromium wlopm
```

`chromium` is the kiosk browser (note: the package is `chromium`, not `chromium-browser` — the name changed in Raspberry Pi OS Bookworm). `wlopm` is the Wayland display power tool used to control the screen on Pi 5 (note: `vcgencmd display_power` does not work on Pi 5). `sqlite3` is the CLI, used by the budget planner that shares this Pi (see `hardware.md`, "Sharing the Pi with the budget planner"); the dashboard itself doesn't need it. `build-essential` and `curl` cover any Python package without a prebuilt aarch64 wheel.

This list used to carry a long set of Python build dependencies (`libssl-dev`, `zlib1g-dev`, `libbz2-dev`, `libreadline-dev`, `libsqlite3-dev`, `libffi-dev`, `liblzma-dev`, `tk-dev`). Those existed only to compile CPython from source under pyenv. Part 6 now uses uv, which downloads a prebuilt build — so they are no longer needed. Reinstate them if you ever fall back to pyenv.

---

## Part 6 — Install Python 3.14 via uv

Raspberry Pi OS ships with Python 3.11. Both the dashboard and the budget planner
require 3.14 (`requires-python = ">=3.14"` in each `pyproject.toml`). **Install it once
and let both apps build their virtualenvs from it** — two interpreters installed two
different ways is exactly the drift this step exists to prevent.

This used to use pyenv, which compiles CPython from source and takes 10–20 minutes on
the Pi. uv downloads a prebuilt aarch64 build in seconds, and the dashboard already uses
uv to generate `backend/requirements.lock`, so it is one tool rather than two.

**6.1** Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

**6.2** Install Python 3.14:

```bash
uv python install 3.14
uv python find 3.14
# /home/pi/.local/share/uv/python/cpython-3.14.*/bin/python3.14
```

**6.3** Note that path — Part 10 uses it to create the venv, and the budget planner's
README uses the same one. To save typing:

```bash
echo "export PY314=\$(uv python find 3.14)" >> ~/.bashrc
source ~/.bashrc
$PY314 --version
# Python 3.14.x
```

> **Already on pyenv?** If pyenv 3.14 is installed and working, you can keep it — the
> point is one interpreter, not which tool provided it. Just make sure the budget
> planner's venv is built from the same one, and ignore the uv references in both
> READMEs. If you do switch, recreate both apps' `backend/.venv` from the uv
> interpreter (Part 10) and afterwards remove `~/.pyenv` to reclaim the disk.

---

## Part 7 — Install Node.js 22

Node is needed to build the frontend. It is not required to run the dashboard — the build output is static files served by FastAPI. **Install it once**: the budget planner sharing this Pi targets the same Node 22 and uses this same install. Do not re-run the NodeSource script per project.

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node --version
# v22.x.x
```

---

## Part 8 — Clone the repo

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/ryan684/family-dashboard.git
cd family-dashboard
```

---

## Part 9 — Configure your credentials and schedule

**9.1** Create the environment file:

```bash
cp .env.example .env
nano .env
```

Fill in every value. The ones you need:

| Variable | Where to get it |
|---|---|
| `GOOGLE_MAPS_API_KEY` | Google Cloud Console → APIs & Services → Credentials |
| `HOME_LAT` / `HOME_LON` | Google Maps → right-click your address → copy coordinates |
| `COMMUTER_1_WORK_LAT/LON` | Same — right-click the work address |
| `COMMUTER_2_WORK_LAT/LON` | Same for the second commuter |
| `NURSERY_LAT/LON` | Same for the nursery address |
| `DOG_DAYCARE_LAT/LON` | Same for the dog daycare address |
| `APPLE_CALDAV_USERNAME` | Your Apple ID email |
| `APPLE_CALDAV_PASSWORD` | appleid.apple.com → Sign-In and Security → App-Specific Passwords → generate one for "Family Dashboard" |
| `APPLE_CALDAV_CALENDAR_NAME` | Name of the shared iCloud calendar (e.g. `Family`) |
| `MET_OFFICE_NSWWS_API_KEY` | Optional — Met Office contact form, requesting access to the NSWWS Public API. Leave blank until it arrives; the warnings banner simply stays hidden |

Save and exit nano: `Ctrl+O`, `Enter`, `Ctrl+X`.

**9.2 Adding a credential to a Pi that is already running.** `deploy.sh` never touches
`.env`, so a variable added to `.env.example` in a later commit will deploy with no value
on the device. To add one, SSH in and edit the file in place, then restart:

```bash
cd ~/projects/family-dashboard
nano .env                       # add the new line
sudo systemctl restart family-dashboard
```

Optional variables — `HERE_API_KEY`, `MET_OFFICE_NSWWS_API_KEY` — can be left out
entirely; the features they drive stay switched off and nothing else is affected.
Variables marked "Required — no default" in `.env.example` are read at import time and
the backend will refuse to start without them, so never deploy a commit that adds one
without editing `.env` in the same sitting.

**9.2** Create the commute schedule:

```bash
cp commute-schedule.example.json commute-schedule.json
nano commute-schedule.json
```

Update the schedule to reflect your household — who goes to the office on which days, who does nursery drops, who does dog daycare. See `README.md` for field descriptions. Save and exit.

---

## Part 10 — Set up the Python backend

Build the venv from the 3.14 interpreter installed in Part 6 — not from the system
`python3`, which is 3.11 and will be rejected by `requires-python`:

```bash
cd ~/projects/family-dashboard/backend
"$PY314" -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
deactivate
```

---

## Part 11 — Build the frontend

This creates the production static files that FastAPI will serve. You only need to run this when the code changes — it does not need to run on every boot.

```bash
cd ~/projects/family-dashboard/frontend
npm install
npm run build
```

The output goes to `frontend/dist/`. FastAPI serves this at `http://localhost:8000` — no Node process runs on the Pi in production.

---

## Part 12 — Test the backend manually

Before automating, verify the backend responds correctly. The SC0940 monitor has no USB ports for a mouse, so test over SSH rather than opening Chromium directly.

```bash
sudo systemctl start family-dashboard
curl http://localhost:8000/api/travel
```

This should return JSON (even if the commuters array is empty outside poll hours). If you get a connection refused error, check the service logs:

```bash
sudo journalctl -u family-dashboard -n 30
```

Stop the service again before the next step:

```bash
sudo systemctl stop family-dashboard
```

---

## Part 13 — Install the systemd service

The service starts the backend automatically on boot and restarts it if it crashes.

**13.1** Create the service file:

```bash
sudo nano /etc/systemd/system/family-dashboard.service
```

Paste this exactly, replacing `pi` with your username if different:

```ini
[Unit]
Description=Family Dashboard Backend
After=network-online.target
Wants=network-online.target

[Service]
User=pi
WorkingDirectory=/home/pi/projects/family-dashboard/backend
ExecStart=/home/pi/projects/family-dashboard/backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5
# Bound a leak so it can never reach the kiosk or the budget planner's backend on
# this 4GB Pi. On breach the kernel kills this service and Restart=on-failure
# brings it back — a far better failure mode than the whole box thrashing.
MemoryMax=512M

[Install]
WantedBy=multi-user.target
```

Save and exit.

**Note the two changes from earlier revisions**, both from sharing this Pi with the budget planner (`hardware.md`, "Sharing the Pi with the budget planner"):

- `--host 127.0.0.1`, not `0.0.0.0`. The only consumer is Chromium on this same machine — the frontend fetches a relative `/api` from the FastAPI process that served it — and this app has no authentication. Tailscale (a budget-planner prerequisite) would otherwise expose it to anything on the tailnet. The cost is that you can no longer open the dashboard from a phone; if you want that, put `0.0.0.0` back knowingly.
- Port 8000 stays with this app. The budget planner moved to 8001, since this one was deployed first.

**13.2** Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable family-dashboard
sudo systemctl start family-dashboard
```

**13.3** Check it's running:

```bash
sudo systemctl status family-dashboard
```

You should see `active (running)`. If there are errors, check the logs:

```bash
sudo journalctl -u family-dashboard -n 50
```

Common issues:
- `.env` file missing or has a blank required value
- `commute-schedule.json` not created from the example
- A Python import error (likely a missing pip package — re-run `pip install -e ".[dev]"`)

---

## Part 14 — Configure Chromium kiosk autostart

Raspberry Pi OS Bookworm uses **labwc** (a Wayland compositor), not a GNOME-based session. The standard `~/.config/autostart/*.desktop` mechanism is not used — labwc has its own autostart file.

This file used to duplicate Chromium's full launch command directly. It's now a thin wrapper that just calls `scripts/restart-kiosk.sh` (the same script the display-on cron uses — see Part 15) instead of repeating the launch logic:

```bash
mkdir -p ~/.config/labwc
cat > ~/.config/labwc/autostart <<'EOF'
sleep 10
/home/pi/projects/family-dashboard/scripts/restart-kiosk.sh >> /home/pi/projects/family-dashboard/kiosk-restart.log 2>&1 &
EOF
```

- `sleep 10` — gives the systemd backend time to start before Chromium loads
- `restart-kiosk.sh` does the actual work: kills any stray Chromium process, waits for it to exit (falling back to SIGKILL after a bounded wait), wipes the disposable `--user-data-dir` profile, and relaunches with `--kiosk`. See `scripts/restart-kiosk.sh` for the exact flags and why each one matters.

**Why this matters**: unlike the cron-triggered restart (which only ever fires right after `wlopm --on`, so the display is always confirmed live), this autostart trigger fires on *every boot* — which could happen at any time, including inside the 22:00-06:30 display-off window (a reboot from a power blip, a kernel update, anything). Launching Chromium while the Wayland output is off leaves it permanently windowed instead of fullscreen (see "Chromium doesn't go fullscreen" in the troubleshooting table below) — so `restart-kiosk.sh` itself refuses to launch Chromium unless it's currently within the scheduled display-on window, logging and exiting instead. If a reboot happens overnight, Chromium is simply left unstarted until the next scheduled `06:30` cron run, rather than launched broken.

---

## Part 15 — Set up the display schedule

The screen turns on at 06:30 and off at 22:00 every day, matching the `WEATHER_POLL_WINDOW_END` default. Travel and calendar data stop refreshing at 09:30 (`POLL_WINDOW_END`), but weather stays live until 22:00 — so the screen stays on as long as fresh data is being served.

If you change `WEATHER_POLL_WINDOW_END` in `.env`, update the off time in the cron entry below to match.

```bash
crontab -e
```

If prompted to choose an editor, select `nano`. Add these two lines at the bottom:

```cron
# Family dashboard display schedule
30 6  * * * XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --on HDMI-A-1 && /home/pi/projects/family-dashboard/scripts/restart-kiosk.sh >> /home/pi/projects/family-dashboard/kiosk-restart.log 2>&1
0  22 * * * XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --off HDMI-A-1 && /home/pi/projects/family-dashboard/scripts/stop-kiosk.sh >> /home/pi/projects/family-dashboard/kiosk-restart.log 2>&1
```

Chromium is restarted in the *same* line as `wlopm --on`, chained with `&&`, so it only ever launches once the output is confirmed live — see `scripts/restart-kiosk.sh` and Part 14 above. The nightly deploy (`deploy.sh`) does not restart Chromium at all.

The 22:00 line is the mirror: `stop-kiosk.sh` kills Chromium once the output is dark. From 22:00 to 06:30 nobody is looking at it, but it holds roughly half a gigabyte — and the nightly deploy (02:00) and the budget planner's backup (03:30) both run inside that window on a 4GB Pi. Nothing relaunches Chromium until 06:30, which is deliberate: launching it against a powered-off output is the fullscreen bug documented in `hardware.md`. `stop-kiosk.sh` is safe to run at any time and is a no-op if Chromium isn't running.

If you power the display on by hand overnight you will find no browser. To get it back outside the scheduled window:

```bash
KIOSK_OFF_HHMM=2359 /home/pi/projects/family-dashboard/scripts/restart-kiosk.sh
```

Note the log path is `kiosk-restart.log`, not `/var/log/family-dashboard-deploy.log` — that file is owned by `root:root` (systemd opens it as root for the deploy service), and cron runs this line as plain user `pi`, who has no write permission on it. The `>>` redirect would fail with "Permission denied" before the script even started, silently discarded since there's no mail transfer agent installed. `kiosk-restart.log` is created fresh by this cron job, so `pi` owns it outright.

Save and exit. To test display control manually:

```bash
XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --off HDMI-A-1   # screen off
XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --on HDMI-A-1    # screen back on
```

If `wlopm --off HDMI-A-1` gives an error, run `wlopm` with no arguments to list available output names and substitute accordingly.

---

## Part 16 — Final reboot and verify

```bash
sudo reboot
```

After ~30 seconds, SSH back in and check the service came up:

```bash
sudo systemctl status family-dashboard
```

After ~60 seconds from boot, the Pi's desktop should be showing the dashboard in full-screen kiosk mode. If you're SSHed in without a screen, you can verify the backend is responding:

```bash
curl http://localhost:8000/api/travel
# should return JSON, not an error
```

---

## Part 17 — Install Claude Code on the Pi (optional)

With Claude Code installed, you can SSH into the Pi and get help debugging the service, adjusting configuration, or making changes directly on the device.

```bash
npm install -g @anthropic-ai/claude-code
```

Add your Anthropic API key to your shell profile:

```bash
echo 'export ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE' >> ~/.bashrc
source ~/.bashrc
```

To use it: SSH into the Pi, navigate to the project, and run `claude`:

```bash
cd ~/projects/family-dashboard
claude
```

Claude Code will pick up the `CLAUDE.md` in the project root automatically and have full context of the project.

---

## Part 18 — Nightly auto-deploy

The deploy script checks once a night (at 02:00) whether new commits have been pushed to `main`. If the local SHA differs it pulls, rebuilds the frontend, reinstalls the backend, and restarts the service — all without any manual SSH. If the Pi was off at 02:00 the timer runs on next boot (`Persistent=true`).

### 18.1 — Allow the Pi user to restart the service without a password

Add a sudoers rule so the deploy script can call `systemctl restart` unattended:

```bash
sudo visudo -f /etc/sudoers.d/family-dashboard-deploy
```

Add this single line (replace `pi` with your username if different):

```
pi ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart family-dashboard
```

### 18.2 — Install the systemd units

Copy the bundled unit files into place:

```bash
sudo cp ~/family-dashboard/scripts/family-dashboard-deploy.service /etc/systemd/system/
sudo cp ~/family-dashboard/scripts/family-dashboard-deploy.timer   /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now family-dashboard-deploy.timer
```

Verify the timer is scheduled:

```bash
systemctl list-timers family-dashboard-deploy.timer
```

### 18.3 — Test a manual deploy run

```bash
sudo systemctl start family-dashboard-deploy.service
sudo journalctl -u family-dashboard-deploy.service -n 30
```

If the repo was already up to date you will see "Already up to date". Push a change from your laptop, then re-run to confirm the full deploy path works.

### 18.4 — Deploy logs

All output (stdout + stderr) goes to:

```
/var/log/family-dashboard-deploy.log
```

This file is not rotated by default — see Part 20.

---

## Part 19 — Migrating a running Pi to the shared setup

Do this once, on a Pi that already runs the dashboard, to make room for the budget
planner. Ordered so the kiosk is never left broken. Roughly 30 minutes, most of it
waiting on the venv rebuild.

**19.1 — Pull the changes**

```bash
cd ~/projects/family-dashboard
git pull origin main
```

**19.2 — Move the backend to loopback and cap its memory**

```bash
sudo nano /etc/systemd/system/family-dashboard.service
```

Change `--host 0.0.0.0` to `--host 127.0.0.1` and add `MemoryMax=512M` under
`[Service]` (Part 13 has the full file). Then:

```bash
sudo systemctl daemon-reload
sudo systemctl restart family-dashboard
curl -s http://localhost:8000/api/travel | head -c 100   # still JSON?
```

**19.3 — Install the new deploy unit (memory caps)**

```bash
sudo cp ~/projects/family-dashboard/scripts/family-dashboard-deploy.service /etc/systemd/system/
sudo systemctl daemon-reload
systemctl cat family-dashboard-deploy.service | grep Memory   # MemoryHigh/MemoryMax present
```

**19.4 — Add the overnight Chromium stop**

```bash
crontab -e
```

Replace the `wlopm --off` line with the version in Part 15 (the one chaining
`stop-kiosk.sh`). Verify without waiting for 22:00 — this kills the kiosk, so expect a
blank screen until you bring it back on the next line:

```bash
~/projects/family-dashboard/scripts/stop-kiosk.sh
KIOSK_OFF_HHMM=2359 ~/projects/family-dashboard/scripts/restart-kiosk.sh
```

**19.5 — Switch Python to uv** (skip if you are keeping pyenv — see the note in Part 6)

Follow Part 6, then rebuild this app's venv from the new interpreter:

```bash
cd ~/projects/family-dashboard/backend
rm -rf .venv
"$PY314" -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/pip install -e . --no-deps
sudo systemctl restart family-dashboard
sudo systemctl status family-dashboard --no-pager
```

Once both apps' venvs are rebuilt and running, reclaim the pyenv disk:

```bash
rm -rf ~/.pyenv
```

**19.6 — Then set up the budget planner**

Follow `budget-planner/README.md` from its "Fresh-Pi setup" section, starting at step 2.
It expects Python 3.14 and Node 22 to already exist — they now do, and it needs no
storage hardware beyond this Pi's SD card.

---

## Part 20 — Memory and log hardening (4GB)

**20.1 — zram instead of SD-card swap**

Raspberry Pi OS swaps to a file on the SD card by default: slow, and it burns write
cycles on the component you can least afford to lose. zram is compressed swap in RAM —
no I/O at all, typically 2–3× compression.

```bash
sudo apt install -y zram-tools
sudo nano /etc/default/zramswap
```

Set `ALGO=zstd` and `PERCENT=50` (≈2GB on a 4GB Pi), then:

```bash
sudo systemctl restart zramswap
sudo systemctl disable --now dphys-swapfile
sudo swapon --show     # should list /dev/zram0 and nothing on the SD card
```

Counterintuitively, zram wants a *high* swappiness — swapping to compressed RAM is cheap:

```bash
echo 'vm.swappiness=150' | sudo tee /etc/sysctl.d/99-zram.conf
sudo sysctl --system
```

Do not add an SD-card swap file as a backstop — that is the write pattern that genuinely
wears a card, and it is what zram is here to avoid. If you ever add a USB drive, a swap
file on that is fine.

**20.2 — Turn off what this Pi doesn't use**

```bash
sudo systemctl disable --now bluetooth ModemManager triggerhappy cups cups-browsed
```

Keep `avahi-daemon` — `dashboard.local` resolution depends on it.

**20.3 — Rotate the logs**

Three logs now grow without bound, and one of them is read by an app: the budget
planner's dashboard parses the last line of its backup log to decide whether to show a
"backup failing" banner. Use `copytruncate` so the file always exists — a rotated-away
log reads as `unknown`, which shows no banner and would quietly hide a failing backup.

```bash
sudo nano /etc/logrotate.d/pi-apps
```

```
/var/log/family-dashboard-deploy.log
/home/pi/projects/family-dashboard/kiosk-restart.log
/var/log/budget-backup.log
{
    weekly
    rotate 8
    compress
    missingok
    notifempty
    copytruncate
    su pi pi
}
```

Adjust the third path to match `BACKUP_LOG_FILE` in the budget planner's
`.env.production`. Test without waiting a week:

```bash
sudo logrotate -d /etc/logrotate.d/pi-apps    # dry run, prints what it would do
```

---

## Troubleshooting quick reference

| Symptom | Check |
|---|---|
| Dashboard shows "stale data" indicator | You're outside the poll window (06:30–09:30) — this is normal |
| Dashboard shows no travel cards | Both commuters are WFH or off today — correct by design |
| Backend won't start | `sudo journalctl -u family-dashboard -n 50` — usually a bad `.env` value |
| Chromium shows "site can't be reached" | Service hasn't started yet — wait a few more seconds or check `systemctl status` |
| Chromium shows a "Choose password for new keyring" popup on screen | Missing `--password-store=basic` flag — this now lives inside `scripts/restart-kiosk.sh`, not the autostart file. Check the script has it and re-run it (or reboot). |
| Chromium doesn't launch on boot | Check `~/.config/labwc/autostart` exists and calls `scripts/restart-kiosk.sh` (Part 14). Also check `kiosk-restart.log` for a "skipped" line — if the reboot happened outside the 06:30-22:00 display-on window, this is expected: Chromium is deliberately left unstarted until the next scheduled cron run, not launched against a powered-off display. |
| Dashboard no longer loads from a phone | Expected since 2026-08-17 — the backend binds `127.0.0.1` (Part 13). The kiosk is unaffected. Put `0.0.0.0` back if you want phone access, knowing it has no auth. |
| No browser on screen if you turn the display on overnight | Expected — `stop-kiosk.sh` stops Chromium at 22:00 (Part 15). Bring it back with `KIOSK_OFF_HHMM=2359 scripts/restart-kiosk.sh`. |
| Backend won't start after switching to uv | The venv was probably rebuilt from system `python3` (3.11), which `requires-python = ">=3.14"` rejects. Rebuild with `"$PY314" -m venv .venv` (Part 19.5). |
| Budget planner backend crash-loops on "address already in use" | It is on 8000 instead of 8001. Both apps cannot share a port — see `hardware.md`, "Sharing the Pi with the budget planner". |
| A build or test run killed a live service | Almost certainly mutation testing on the Pi — never do this (`scripts/assert-not-pi.sh` now refuses). Otherwise check `MemoryHigh` is set on the deploy unit (Part 19.3) and that the 22:00 `stop-kiosk.sh` line is in the crontab. |
| `wlopm` command not found | Run `sudo apt install -y wlopm` |
| `wlopm --off HDMI-A-1` gives an error | Run `wlopm` with no arguments to list output names, then substitute the correct name |
| Display stays on all day | Cron not installed — re-run step 15 and verify with `crontab -l` |
| SSH hangs after reboot | Pi takes ~30s to get network — just retry |
| Auto-deploy never runs | Check `systemctl list-timers family-dashboard-deploy.timer` and re-run step 18.2 |
| Auto-deploy ran but service is old | Check `/var/log/family-dashboard-deploy.log` for build or pull errors |
| Chromium shows a normal windowed browser (tabs, address bar) instead of fullscreen kiosk, even though `pgrep -af chromium` shows `--kiosk` in the running process | Two possible causes, in order of likelihood. (1) Chromium was launched while the Wayland output was powered off (`wlopm --off`) — its fullscreen request had nothing to negotiate against and fell back to a window, permanently, until relaunched with the display on. This is why Chromium is no longer restarted by the nightly deploy (which ran at 02:00, inside the display-off window) — it's now only restarted by `scripts/restart-kiosk.sh`, chained to `wlopm --on` (Part 15) and called from the boot autostart (Part 14), both of which guarantee — or, for the autostart case, actively check — that the display is live first. (2) An earlier unclean shutdown (SIGKILL) left Chromium session-restore state behind; `restart-kiosk.sh` wipes the disposable `--user-data-dir` profile before every launch specifically to prevent this. If you still see this after confirming both scripts are up to date, check `kiosk-restart.log` for what actually happened at the last restart attempt. |
