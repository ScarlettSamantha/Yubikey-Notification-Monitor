#!/usr/bin/env bash
# install.sh - Install YubiKey Monitor Daemon

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

# Verify that monitor.py exists in the current directory.
if [[ ! -f "${PYTHON_SCRIPT}" ]]; then
    echo "Error: ${PYTHON_SCRIPT} not found in the current directory."
    exit 1
fi

# Copy monitor.py to /usr/local/bin and set execute permissions.
cp "${PYTHON_SCRIPT}" "${INSTALL_PATH}"
chmod +x "${INSTALL_PATH}"

# Verify that the service file exists.
if [[ ! -f "${SERVICE_NAME}" ]]; then
    echo "Error: ${SERVICE_NAME} not found in the current directory."
    exit 1
fi

# Create a temporary service file with the updated ExecStart path.
TEMP_SERVICE=$(mktemp)
sed "s|/path/to/monitor.py|${INSTALL_PATH}|g" "${SERVICE_NAME}" > "${TEMP_SERVICE}"

# Install the updated service file.
cp "${TEMP_SERVICE}" "${SERVICE_DEST}/${SERVICE_NAME}"
rm "${TEMP_SERVICE}"

# Reload systemd, enable and start the service.
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl start "${SERVICE_NAME}"

echo "Installation complete. Service '${SERVICE_NAME}' is now active."
