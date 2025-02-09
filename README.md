# YubiKey Monitor Daemon

This project provides a Python daemon that monitors YubiKey devices by parsing the output of `lsusb`.

## Features

- Detects YubiKey devices using standard USB utilities.
- Benchmarks device detection performance.
- Runs as a systemd service for continuous monitoring.
- Has a nice notification system

## Installation

### Prerequisites

- Python 3.7 or later
- `lsusb` (commonly available on Linux)

### Package Installation

Install the package locally:

to install add something like the example.bash to your .bashrc, it does all this to prevent dual instances from running.

## Uninstallation

To remove the installed files and service, just remove the source.

## Authors

- Scarlett Samantha Verheul <scarlett.verheul@gmail.com>
