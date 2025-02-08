#!/usr/bin/env python3
"""
Monitor key state via /tmp/triggered.txt and send notifications accordingly.
If the file contains "untriggered", the key is assumed to be inserted.
If it changes to "triggered", a countdown starts before locking the screen,
which is canceled if the file reverts to "untriggered" within the countdown.
"""

import os
import time
import subprocess
from typing import Optional
from yubikey import YubiDetect

class Monitor:
    
    NOTIFICATION_TITLE: str = "Yubikey Notification Service"
    
    
    def __init__(self, seconds: int = 10) -> None:
        self.detection_instance = YubiDetect(True)
        self.key_present: bool = self.detection_instance.search_yubikey_exists()
        self.previous_present = self.key_present
        self.active_countdown: bool = False
        self.countdown_iteration: int = 0
        self.seconds_grace: int = seconds
        self.last_countdown_notification: Optional[str] = None
        self.active_monitor: bool = True

    def send_notification(
        self, title: str, message: str, replace: Optional[str] = None
    ) -> Optional[str]:
        if not replace:
            cmd = ["notify-send", "-p", "-e", str(title), str(message)]
        else:
            cmd = ["notify-send", f"--replace-id={str(replace)}", "-e" , str(title), str(message)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        #if result.stderr:
            #print(f"Error: {result.stderr}")
            #print(f"stdout: {result.stdout}")
        return result.stdout.strip() if result.returncode == 0 else None

    def _reset(self):
        self.countdown_iteration = 0
        self.active_countdown = False
        self.last_countdown_notification = None

    def reset_from_login(self):
        self._reset()
        self.active_monitor = True

    def lock_screen(self) -> None:
        """
        Lock the screen after the countdown expires.
        Detects the GUI environment and executes the corresponding lock command.
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

        def _detect_gui() -> Optional[str]:
            """
            Detect the current GUI environment.

            Returns:
                A string identifying the GUI ('gnome', 'kde', 'xfce', 'cinnamon', 'mate', 'lxde', 'sway')
                or None if unrecognized.
            """
            desktop: str = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
            if "gnome" in desktop:
                return "gnome"
            elif "kde" in desktop:
                return "kde"
            elif "xfce" in desktop:
                return "xfce"
            elif "cinnamon" in desktop:
                return "cinnamon"
            elif "mate" in desktop:
                return "mate"
            elif "lxde" in desktop:
                return "lxde"
            elif "sway" in desktop or os.environ.get("WAYLAND_DISPLAY") is not None:
                return "sway"
            else:
                return None

        # Detect the GUI and execute the corresponding lock function.
        gui: Optional[str] = _detect_gui()
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
                # Fallback: attempt to lock the session using loginctl.
                subprocess.run(["loginctl", "lock-session"], check=False)
        except Exception:
            lock_default()

        # Update the state and notify the user.
        self.active_monitor = False
        self.send_notification(
            self.NOTIFICATION_TITLE,
            "Key removed to lock, locking screen",
            str(self.last_countdown_notification)
        )
        self._reset()


    def key_reinserted(self) -> None:
        """
        Handle key insertion by updating the state and sending a notification.
        """
        self.countdown_iteration = 0
        self.active_countdown = False
        self.send_notification(self.NOTIFICATION_TITLE, "Key re-inserted", str(self.last_countdown_notification))
        self.last_countdown_notification = None
        self.active_monitor = True

    def key_gone(self) -> None:
        """
        Start the removal process with a countdown.
        If the key is reinserted during the countdown, cancel the removal.
        """
        if self.countdown_iteration == 0:
            self.last_countdown_notification = self.send_notification(self.NOTIFICATION_TITLE, "Key has been removed", None)
        else:
            self.send_notification(self.NOTIFICATION_TITLE, f"Key has been gone for {str(self.countdown_iteration)}/{(self.seconds_grace)}", self.last_countdown_notification)
        self.countdown_iteration += 1
            
    def detect_if_should_lock(self) -> bool:
        return self.countdown_iteration > self.seconds_grace
        
    def monitor(self) -> None:
        """
        Continuously poll the trigger file and perform state transitions.
        """
        while True:
            present = self.detection_instance.search_yubikey_exists()
           # Key change
            if present is True and self.previous_present is False:
                self.key_reinserted()
            elif present is False and self.previous_present is False and self.active_monitor is True:
                self.key_gone()
                if self.detect_if_should_lock():
                    self.lock_screen()
            else:
                time.sleep(4)
            self.previous_present = present
            time.sleep(1)
            
           
if __name__ == "__main__":
    instance = Monitor(10)
    instance.monitor()