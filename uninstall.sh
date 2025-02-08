#!/usr/bin/env bash
# uninstall.sh - Uninstall YubiKey Monitor Daemon

set -euo pipefail

# Ensure the script runs with root privileges.
if [[ $EUID -ne 0 ]]; then
    echo "Please run as root or use sudo."
    exit 1
fi

# Variables
INSTALL_DIR="/usr/local/bin"
SERVICE_DEST="/etc/systemd/system"
SERVICE_NAME="yubimon.service"
PYTHON_SCRIPT="monitor.py"
INSTALL_PATH="${INSTALL_DIR}/${PYTHON_SCRIPT}"

# Stop and disable the service (ignore errors if not running).
systemctl stop "${SERVICE_NAME}" || true
systemctl disable "${SERVICE_NAME}" || true

# Remove the service file and the installed Python script.
rm -f "${SERVICE_DEST}/${SERVICE_NAME}"
rm -f "${INSTALL_PATH}"

# Reload systemd to apply changes.
systemctl daemon-reload

echo "Uninstallation complete. '${SERVICE_NAME}' and '${PYTHON_SCRIPT}' have been removed."
