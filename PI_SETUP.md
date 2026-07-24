# Pi Setup Guide — Family Dashboard

Complete walkthrough from unboxing to a running kiosk dashboard.
Hardware assumed: **Raspberry Pi 5 (4GB) + Official Raspberry Pi Monitor SC0940 (15.6")**.

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
sudo apt install -y \
    build-essential curl git \
    libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev libffi-dev \
    liblzma-dev tk-dev chromium wlopm
```

`chromium` is the kiosk browser (note: the package is `chromium`, not `chromium-browser` — the name changed in Raspberry Pi OS Bookworm). `wlopm` is the Wayland display power tool used to control the screen on Pi 5 (note: `vcgencmd display_power` does not work on Pi 5). The rest are needed to compile Python.

---

## Part 6 — Install Python 3.14 via pyenv

Raspberry Pi OS ships with Python 3.11. The dashboard requires 3.14, which pyenv installs from source.

**6.1** Install pyenv:

```bash
curl https://pyenv.run | bash
```

**6.2** Add pyenv to your shell (the installer tells you to do this — copy its output, or paste these lines):

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc
```

**6.3** Install Python 3.14. This compiles from source on the Pi — it takes **10–20 minutes**. Start it before making a coffee:

```bash
pyenv install 3.14
```

**6.4** Set it as the default:

```bash
pyenv global 3.14
python --version
# Python 3.14.x
```

---

## Part 7 — Install Node.js 22

Node is needed to build the frontend. It is not required to run the dashboard — the build output is static files served by FastAPI.

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

Save and exit nano: `Ctrl+O`, `Enter`, `Ctrl+X`.

**9.2** Create the commute schedule:

```bash
cp commute-schedule.example.json commute-schedule.json
nano commute-schedule.json
```

Update the schedule to reflect your household — who goes to the office on which days, who does nursery drops, who does dog daycare. See `README.md` for field descriptions. Save and exit.

---

## Part 10 — Set up the Python backend

```bash
cd ~/projects/family-dashboard/backend
python -m venv .venv
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
ExecStart=/home/pi/projects/family-dashboard/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Save and exit.

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
0  22 * * * XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 wlopm --off HDMI-A-1
```

Chromium is restarted in the *same* line as `wlopm --on`, chained with `&&`, so it only ever launches once the output is confirmed live — see `scripts/restart-kiosk.sh` and Part 14 above. The nightly deploy (`deploy.sh`) does not restart Chromium at all.

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
| `wlopm` command not found | Run `sudo apt install -y wlopm` |
| `wlopm --off HDMI-A-1` gives an error | Run `wlopm` with no arguments to list output names, then substitute the correct name |
| Display stays on all day | Cron not installed — re-run step 15 and verify with `crontab -l` |
| SSH hangs after reboot | Pi takes ~30s to get network — just retry |
| Auto-deploy never runs | Check `systemctl list-timers family-dashboard-deploy.timer` and re-run step 18.2 |
| Auto-deploy ran but service is old | Check `/var/log/family-dashboard-deploy.log` for build or pull errors |
| Chromium shows a normal windowed browser (tabs, address bar) instead of fullscreen kiosk, even though `pgrep -af chromium` shows `--kiosk` in the running process | Two possible causes, in order of likelihood. (1) Chromium was launched while the Wayland output was powered off (`wlopm --off`) — its fullscreen request had nothing to negotiate against and fell back to a window, permanently, until relaunched with the display on. This is why Chromium is no longer restarted by the nightly deploy (which ran at 02:00, inside the display-off window) — it's now only restarted by `scripts/restart-kiosk.sh`, chained to `wlopm --on` (Part 15) and called from the boot autostart (Part 14), both of which guarantee — or, for the autostart case, actively check — that the display is live first. (2) An earlier unclean shutdown (SIGKILL) left Chromium session-restore state behind; `restart-kiosk.sh` wipes the disposable `--user-data-dir` profile before every launch specifically to prevent this. If you still see this after confirming both scripts are up to date, check `kiosk-restart.log` for what actually happened at the last restart attempt. |
