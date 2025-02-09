#!/usr/bin/env python3
"""
Monitor YubiKey presence and lock the screen if the key remains absent beyond a grace period.

This script runs as a daemon and continuously monitors the YubiKey status.
If the key remains absent beyond the specified grace period, it locks the screen.
"""

import os
import subprocess
import time
import signal
from typing import Optional
import notify2
import daemon
import daemon.pidfile
from yubi_detect import YubiDetect


class Monitor:
    """
    Monitors the YubiKey state and triggers screen locking upon prolonged absence.
    """
    NOTIFICATION_TITLE: str = "Yubikey Notification Service"

    def __init__(self, grace_period: int = 10, detector: Optional[YubiDetect] = None) -> None:
        notify2.init('Yubikey pressense tracker')
        
        self.detection_instance: YubiDetect = detector if detector is not None else YubiDetect(True)
        self.key_present: bool = self.detection_instance.search_yubikey_exists()
        self.previous_present: bool = self.key_present
        self.active_countdown: bool = False
        self.countdown_iteration: int = 0
        self.seconds_grace: int = grace_period
        self.last_notification_id: notify2.Notification = notify2.Notification("", "", "")
        self.active_monitor: bool = True
        self.running: bool = True  # Controls the main monitoring loop


    def send_notification(self, title: str, message: str) -> Optional[str]:
        """
        Send a desktop notification using notify-send.
        """
        self.last_notification_id.update(title, message)
        self.last_notification_id.show()

    def _reset_countdown(self) -> None:
        """
        Reset the countdown state.
        """
        self.countdown_iteration = 0
        self.active_countdown = False

    def reset_from_login(self) -> None:
        """
        Reset the monitor state, typically after a user logs in.
        """
        self._reset_countdown()
        self.active_monitor = True
        self.key_present = self.detection_instance.search_yubikey_exists()
        self.previous_present = self.key_present

    def lock_screen(self) -> None:
        """
        Lock the screen using the detected desktop environment's lock command.
        """
        def lock_gnome() -> None:
            subprocess.run(["gnome-screensaver-command", "-l"], check=False)

        def lock_kde() -> None:
            lock_default()

        def lock_xfce() -> None:
            subprocess.run(["xflock4"], check=False)

        def lock_cinnamon() -> None:
            subprocess.run(["cinnamon-screensaver-command", "-l"], check=False)

        def lock_mate() -> None:
            subprocess.run(["mate-screensaver-command", "-l"], check=False)

        def lock_lxde() -> None:
            subprocess.run(["lxlock"], check=False)

        def lock_sway() -> None:
            subprocess.run(["swaylock"], check=False)

        def lock_default() -> None:
            subprocess.run(["loginctl", "lock-session"], check=False)

        def detect_gui() -> Optional[str]:
            """
            Detect the current GUI environment.
            """
            desktop: str = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
            if "gnome" in desktop:
                return "gnome"
            if "kde" in desktop:
                return "kde"
            if "xfce" in desktop:
                return "xfce"
            if "cinnamon" in desktop:
                return "cinnamon"
            if "mate" in desktop:
                return "mate"
            if "lxde" in desktop:
                return "lxde"
            if "sway" in desktop or os.environ.get("WAYLAND_DISPLAY"):
                return "sway"
            return None

        gui: Optional[str] = detect_gui()
        try:
            if gui == "gnome":
                lock_gnome()
            elif gui == "kde":
                lock_kde()
            elif gui == "xfce":
                lock_xfce()
            elif gui == "cinnamon":
                lock_cinnamon()
            elif gui == "mate":
                lock_mate()
            elif gui == "lxde":
                lock_lxde()
            elif gui == "sway":
                lock_sway()
            else:
                lock_default()
        except Exception:
            lock_default()

        self.active_monitor = False  # Prevent further actions after locking
        self.send_notification(self.NOTIFICATION_TITLE, "YubiKey removed. Locking screen.")
        self._reset_countdown()

    def key_reinserted(self) -> None:
        """
        Handle the event when the key is reinserted.
        """
        self._reset_countdown()
        self.send_notification(self.NOTIFICATION_TITLE, "YubiKey has been reinserted.")
        self.active_monitor = True
        time.sleep(3)
        self.last_notification_id.close()
        self.last_notification_id = notify2.Notification("", "", "")

    def key_absent(self) -> None:
        """
        Increment the countdown when the key is absent and send a notification.
        """
        if self.countdown_iteration == 0:
            self.send_notification(self.NOTIFICATION_TITLE, "Key has been removed.")
        else:
            self.send_notification(self.NOTIFICATION_TITLE, f"Key absent for {self.countdown_iteration} second(s) out of {self.seconds_grace}.")
        self.countdown_iteration += 1

    def should_lock(self) -> bool:
        """
        Determine if the screen should be locked based on the countdown.
        """
        return self.countdown_iteration > self.seconds_grace

    def monitor_iteration(self) -> None:
        """
        Execute one iteration of the monitoring loop.
        """
        present: bool = self.detection_instance.search_yubikey_exists()
        if present:
            if not self.previous_present:
                self.key_reinserted()
        else:
            if self.active_monitor:
                self.key_absent()
                if self.should_lock():
                    self.lock_screen()
        self.previous_present = present

    def monitor(self) -> None:
        """
        Continuously monitor the YubiKey state until the daemon is stopped.
        """ 
        while self.running:
            self.monitor_iteration()
            time.sleep(1)


def main() -> None:
    """
    Main function to run the monitor daemon.
    Sets up signal handling for a graceful shutdown.
    """
    monitor_instance: Monitor = Monitor(grace_period=10)

    # Signal handler to set the running flag to False for graceful exit.
    def handle_sigterm(signum: int, frame: Optional[object]) -> None:
        monitor_instance.running = False
   
    signal.signal(signal.SIGTERM, handle_sigterm)
    monitor_instance.monitor()


if __name__ == "__main__":
    # Open log files for stdout and stderr redirection.
    stdout_log = open("/tmp/yubimonitor.log", "a+")
    stderr_log = open("/tmp/yubimonitor.err", "a+")

    # Create a daemon context with a PID file for proper daemon management.
    with daemon.DaemonContext(working_directory="/", umask=0o002, pidfile=daemon.pidfile.PIDLockFile("/tmp/yubimonitor.pid", timeout=3600), stdout=stdout_log, stderr=stderr_log):
        main()
