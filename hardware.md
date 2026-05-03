# Family Dashboard — Hardware & Deployment Reference

Human reference only. Not needed during coding sessions.

---

## Hardware Options

### Recommended — Raspberry Pi 5 + Official Raspberry Pi 15.6" Monitor (SC0940)

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

With the Pi VESA-mounted behind the monitor, the only external cables are one power cable to the monitor and one to the Pi.

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
