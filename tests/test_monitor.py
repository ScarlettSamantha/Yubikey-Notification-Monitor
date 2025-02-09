#!/usr/bin/env python3
"""
Pytest tests for the Monitor module.
"""

from monitor import Monitor


class DummyDetection:
    def __init__(self, states):
        self.states = states
        self.index = 0

    def search_yubikey_exists(self) -> bool:
        state = self.states[self.index]
        if self.index < len(self.states) - 1:
            self.index += 1
        return state


def test_monitor_lock() -> None:
    # Simulate: key is initially present then becomes absent long enough to trigger a lock.
    states = [True] + [False] * 12
    dummy_detector = DummyDetection(states)
    monitor_instance = Monitor(grace_period=10, detector=dummy_detector)
    for _ in range(len(states)):
        monitor_instance.monitor_iteration()
    # After the grace period, the monitor should disable further activity.
    assert not monitor_instance.active_monitor
