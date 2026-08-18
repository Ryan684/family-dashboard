#!/usr/bin/env bash
# Refuse to run on the Raspberry Pi.
#
# Guards the mutation-test commands (mutmut, Stryker). Both are far heavier than
# anything else in this repo: Stryker spawns parallel Vitest workers and mutmut
# re-runs the whole suite once per mutant. The Pi is a 4GB Pi 5 shared with the
# family dashboard, running two backends and a Chromium kiosk, so either one will
# exhaust memory and take the OOM killer to a live service.
#
# This matters because Claude Code is installed on the Pi (PI_SETUP.md, Part 17)
# and picks up CLAUDE.md automatically, whose build order says mutation tests are
# mandatory. The carve-out is documented there; this is the backstop that catches
# a session which missed it.
#
# Usage: scripts/assert-not-pi.sh && mutmut run
#
# Override with ALLOW_PI_HEAVY_TESTS=1 if you really mean it (e.g. the kiosk is
# stopped and you are willing to wait).
set -euo pipefail

if [ "${ALLOW_PI_HEAVY_TESTS:-0}" = "1" ]; then
    exit 0
fi

# The device tree model is the reliable signal — the hostname is user-chosen. The
# file is NUL-terminated, hence the tr. PI_MODEL_FILE is overridable for testing.
MODEL_FILE="${PI_MODEL_FILE:-/proc/device-tree/model}"

if [ -r "$MODEL_FILE" ] && tr -d '\0' <"$MODEL_FILE" | grep -qi "raspberry pi"; then
    cat >&2 <<'EOF'
Refusing to run: this is the Raspberry Pi.

Mutation testing (mutmut / Stryker) needs far more memory than the Pi has spare
while the kiosk and both app backends are running, and will trigger the OOM
killer against a live service. Run it on your development machine instead.

If you are certain (kiosk stopped, happy to wait): ALLOW_PI_HEAVY_TESTS=1
EOF
    exit 1
fi
