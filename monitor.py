#!/usr/bin/env python3
"""
Monitor YubiKey presence and lock the screen if the key remains absent beyond a grace period.
"""

import os
import time
import subprocess
from typing import Optional, Protocol

from yubi_detect import YubiDetect


class YubiDetector(Protocol):
    def search_yubikey_exists(self) -> bool:
        ...


class Monitor:
    """
    Monitors the YubiKey state and triggers screen locking upon prolonged absence.
    """

    NOTIFICATION_TITLE: str = "Yubikey Notification Service"

    def __init__(self, grace_period: int = 10, detector: Optional[YubiDetector] = None) -> None:
        # Allow injection of a custom detector for testing purposes.
        self.detection_instance: YubiDetector = detector if detector is not None else YubiDetect(True)
        self.key_present: bool = self.detection_instance.search_yubikey_exists()
        self.previous_present: bool = self.key_present
        self.active_countdown: bool = False
        self.countdown_iteration: int = 0
        self.seconds_grace: int = grace_period
        self.last_notification_id: Optional[str] = None
        self.active_monitor: bool = True

    def send_notification(self, title: str, message: str, replace: Optional[str] = None) -> Optional[str]:
        """
        Send a desktop notification.
        """
        cmd = ["notify-send"]
        if replace:
            cmd.append(f"--replace-id={replace}")
        cmd.extend(["-p", title, message])
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None

    def _reset_countdown(self) -> None:
        """
        Reset the countdown state.
        """
        self.countdown_iteration = 0
        self.active_countdown = False
        self.last_notification_id = None

    def reset_from_login(self) -> None:
        """
        Reset the monitor state, typically after a user logs in.
        """
        self._reset_countdown()
        self.active_monitor = True

    def lock_screen(self) -> None:
        """
        Lock the screen using the detected desktop environment's lock command.
        """
        def lock_gnome() -> None:
            subprocess.run(["gnome-screensaver-command", "-l"], check=False)

        def lock_kde() -> None:
            subprocess.run(["qdbus-qt6", "org.freedesktop.ScreenSaver", "/ScreenSaver", "Lock"], check=False)

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
            desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
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

        gui = detect_gui()
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

        self.active_monitor = False
        self.send_notification(self.NOTIFICATION_TITLE, "Key removed. Locking screen.", self.last_notification_id or "")
        self._reset_countdown()

    def key_reinserted(self) -> None:
        """
        Handle the event when the key is reinserted.
        """
        self._reset_countdown()
        self.send_notification(self.NOTIFICATION_TITLE, "Key reinserted.", self.last_notification_id or "")
        self.active_monitor = True

    def key_absent(self) -> None:
        """
        Increment the countdown when the key is absent and send a notification.
        """
        if self.countdown_iteration == 0:
            self.last_notification_id = self.send_notification(self.NOTIFICATION_TITLE, "Key has been removed.")
        else:
            self.send_notification(
                self.NOTIFICATION_TITLE,
                f"Key absent for {self.countdown_iteration} second(s) out of {self.seconds_grace}.",
                self.last_notification_id or ""
            )
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
        present = self.detection_instance.search_yubikey_exists()
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
        Continuously monitor the YubiKey state and trigger actions on state changes.
        """
        while True:
            self.monitor_iteration()
            time.sleep(1)


if __name__ == "__main__":
    monitor_instance = Monitor(grace_period=10)
    monitor_instance.monitor()
