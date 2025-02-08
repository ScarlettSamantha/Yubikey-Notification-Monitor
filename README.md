# YubiKey Monitor Daemon

This project provides a Python daemon that monitors YubiKey devices by parsing the output of `lsusb`.

## Features

- Detects YubiKey devices using standard USB utilities.
- Benchmarks device detection performance.
- Runs as a systemd service for continuous monitoring.

## Installation

### Prerequisites

- Python 3.7 or later
- `lsusb` (commonly available on Linux)
- systemd (for service management)

### Using Pipenv

Install dependencies using the included Pipfile:

```bash
pipenv install
```

### Package Installation

Install the package locally:

```bash
python3 -m pip install .
```

### Systemd Service Installation

Run the install script with root privileges to deploy the daemon and service:

```bash
sudo ./install.sh
```

This script copies `monitor.py` to `/usr/local/bin`, updates the systemd service file (`yubimon.service`), reloads systemd, and starts the service.

## Configuration

- **Service File:** Edit `yubimon.service` if you need to adjust the `ExecStart` path, user, or group settings.
- **Python Script:** The `monitor.py` file contains all the logic for detecting YubiKey devices.

## Usage

- **Check service status:**

```bash
sudo systemctl status yubimon.service
```

- **Restart the service:**

```bash
sudo systemctl restart yubimon.service
```

- **Stop the service:**

```bash
sudo systemctl stop yubimon.service
```

## Uninstallation

To remove the installed files and service, run:

```bash
sudo ./uninstall.sh
```

This stops and disables the service, removes the deployed files, and reloads systemd.

## Authors

- Scarlett Samantha Verheul <scarlett.verheul@gmail.com>
