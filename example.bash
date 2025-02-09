#!/bin/bash
PID_FILE="/tmp/yubimonitor.pid"

# If PID file exists, try to gracefully terminate the running process.
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"            # Attempt graceful termination.
        sleep 1                # Give it a moment to exit.
        if kill -0 "$PID" 2>/dev/null; then
            kill -9 "$PID"     # Force kill if still running.
        fi
    fi
    rm -f "$PID_FILE"          # Remove the PID file after stopping the process.
fi

# Start the daemon in a new session and redirect I/O.
setsid /usr/bin/python /home/scarlett/Code/yubikey_monitor/monitor.py </dev/null &>/dev/null &

indent_message 2 "$SUCCESS_EMOJI Yubikey tracking daemon has been started"
