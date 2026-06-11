#!/usr/bin/env bash
# Automated setup for the family-dashboard on Raspberry Pi 5.
# Covers steps 5–16 of PI_SETUP.md — run this after cloning the repo.
# Prerequisites: Raspberry Pi OS Bookworm 64-bit Desktop, internet access.
# Usage: bash scripts/pi-setup.sh

set -euo pipefail

PROJECT_DIR="$HOME/projects/family-dashboard"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_NAME="family-dashboard"
CURRENT_USER="$(whoami)"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[setup]${NC} $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC}  $*"; }
error() { echo -e "${RED}[error]${NC} $*"; exit 1; }
step()  { echo; echo -e "${GREEN}━━━ $* ━━━${NC}"; }

[[ "$(uname -m)" == "aarch64" ]] || error "This script is for Raspberry Pi (aarch64). Current arch: $(uname -m)"

# ---------------------------------------------------------------------------
step "System packages"
# ---------------------------------------------------------------------------
info "Updating package lists..."
sudo apt-get update -q

info "Installing build and runtime dependencies..."
sudo apt-get install -y -q \
    build-essential curl git \
    libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev libffi-dev \
    liblzma-dev tk-dev chromium-browser

# ---------------------------------------------------------------------------
step "Node.js 22"
# ---------------------------------------------------------------------------
if command -v node &>/dev/null && [[ "$(node --version | cut -d. -f1 | tr -d v)" -ge 22 ]]; then
    info "Node.js $(node --version) already installed."
else
    info "Installing Node.js 22 via NodeSource..."
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
    sudo apt-get install -y nodejs
    info "Node.js $(node --version) installed."
fi

# ---------------------------------------------------------------------------
step "Python 3.14 via pyenv"
# ---------------------------------------------------------------------------
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"

if ! command -v pyenv &>/dev/null; then
    info "Installing pyenv..."
    curl https://pyenv.run | bash
    {
        echo ''
        echo 'export PYENV_ROOT="$HOME/.pyenv"'
        echo 'export PATH="$PYENV_ROOT/bin:$PATH"'
        echo 'eval "$(pyenv init -)"'
    } >> "$HOME/.bashrc"
fi

eval "$(pyenv init -)"

if pyenv versions 2>/dev/null | grep -q "3\.14"; then
    info "Python 3.14 already installed."
else
    warn "Compiling Python 3.14 from source — this takes 10–20 minutes on the Pi 5."
    pyenv install 3.14
fi

pyenv global 3.14
PYTHON="$(pyenv which python)"
info "Using $($PYTHON --version) at $PYTHON"

# ---------------------------------------------------------------------------
step "Project directory"
# ---------------------------------------------------------------------------
if [[ "$REPO_DIR" != "$PROJECT_DIR" ]]; then
    info "Copying repo to $PROJECT_DIR..."
    mkdir -p "$HOME/projects"
    rsync -a --exclude='.git' --exclude='backend/.venv' --exclude='frontend/node_modules' \
        "$REPO_DIR/" "$PROJECT_DIR/"
    info "Copied."
else
    info "Repo is already at $PROJECT_DIR."
fi

cd "$PROJECT_DIR"

# ---------------------------------------------------------------------------
step "Python virtual environment and backend dependencies"
# ---------------------------------------------------------------------------
info "Creating virtual environment..."
cd "$PROJECT_DIR/backend"
"$PYTHON" -m venv .venv
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -e ".[dev]"
deactivate
info "Backend dependencies installed."

# ---------------------------------------------------------------------------
step "Frontend production build"
# ---------------------------------------------------------------------------
info "Installing Node dependencies..."
cd "$PROJECT_DIR/frontend"
npm install --silent

info "Building frontend (outputs to frontend/dist/)..."
npm run build
info "Frontend built. FastAPI will serve these static files — no Node process needed at runtime."

# ---------------------------------------------------------------------------
step "Environment file"
# ---------------------------------------------------------------------------
cd "$PROJECT_DIR"

if [[ ! -f .env ]]; then
    cp .env.example .env
    warn ".env created from .env.example."
    warn "You MUST fill in your credentials before starting the service:"
    warn "  nano $PROJECT_DIR/.env"
    warn ""
    warn "Required values: GOOGLE_MAPS_API_KEY, HOME_LAT/LON, work/nursery/dog"
    warn "  coordinates, APPLE_CALDAV_USERNAME/PASSWORD, APPLE_CALDAV_CALENDAR_NAME"
else
    info ".env already exists — not overwriting."
fi

if [[ ! -f commute-schedule.json ]]; then
    cp commute-schedule.example.json commute-schedule.json
    warn "commute-schedule.json created from example."
    warn "Update it to match your household: nano $PROJECT_DIR/commute-schedule.json"
else
    info "commute-schedule.json already exists — not overwriting."
fi

# ---------------------------------------------------------------------------
step "Systemd service"
# ---------------------------------------------------------------------------
info "Installing family-dashboard.service..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=Family Dashboard Backend
After=network-online.target
Wants=network-online.target

[Service]
User=${CURRENT_USER}
WorkingDirectory=${PROJECT_DIR}/backend
ExecStart=${PROJECT_DIR}/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
info "Service enabled. It will start automatically on next boot."
info "To start now (after filling in .env): sudo systemctl start $SERVICE_NAME"

# ---------------------------------------------------------------------------
step "Chromium kiosk autostart"
# ---------------------------------------------------------------------------
info "Configuring kiosk autostart..."
mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/kiosk.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Dashboard Kiosk
Exec=bash -c "sleep 10 && chromium-browser --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble http://localhost:8000"
X-GNOME-Autostart-enabled=true
EOF
info "Kiosk will launch 10 seconds after the desktop loads (gives the backend time to start)."

# ---------------------------------------------------------------------------
step "Display on/off cron schedule (Mon–Fri 06:30–09:00)"
# ---------------------------------------------------------------------------
info "Installing display schedule cron jobs..."
( crontab -l 2>/dev/null | grep -v 'display_power\|family-dashboard display'; \
  echo "# family-dashboard display schedule"; \
  echo "30 6 * * 1-5 /usr/bin/vcgencmd display_power 1"; \
  echo "0  9 * * 1-5 /usr/bin/vcgencmd display_power 0" \
) | crontab -
info "Display: on at 06:30, off at 09:00, Mon–Fri. Edit with: crontab -e"

# ---------------------------------------------------------------------------
step "Claude Code (optional)"
# ---------------------------------------------------------------------------
echo
read -r -p "Install Claude Code CLI on this Pi? Lets you SSH in and ask for help directly. (y/N) " install_claude
if [[ "${install_claude,,}" == "y" ]]; then
    info "Installing Claude Code..."
    npm install -g @anthropic-ai/claude-code
    info "Claude Code installed."
    warn "Add your Anthropic API key:"
    warn "  echo 'export ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE' >> ~/.bashrc"
    warn "  source ~/.bashrc"
    warn "Then run 'claude' from $PROJECT_DIR to get in-context help on the Pi."
fi

# ---------------------------------------------------------------------------
step "Setup complete"
# ---------------------------------------------------------------------------
echo
echo "  What to do next:"
echo ""
echo "  1. Fill in API keys and coordinates:"
echo "       nano $PROJECT_DIR/.env"
echo ""
echo "  2. Update the commute schedule for your household:"
echo "       nano $PROJECT_DIR/commute-schedule.json"
echo ""
echo "  3. Start the backend and check it's healthy:"
echo "       sudo systemctl start $SERVICE_NAME"
echo "       sudo systemctl status $SERVICE_NAME"
echo "       curl http://localhost:8000/api/travel"
echo ""
echo "  4. Reboot to test that everything comes up automatically:"
echo "       sudo reboot"
echo ""
echo "  See PI_SETUP.md for a troubleshooting reference."
echo ""
warn "Display schedule: Mon–Fri 06:30 on / 09:00 off. Adjust with: crontab -e"
