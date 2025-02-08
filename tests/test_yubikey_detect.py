#!/usr/bin/env python3
"""
Pytest tests for the YubiDetect module.
"""

from yubi_detect import YubiDetect

def test_parse_device_rules_empty() -> None:
    data = ""
    result = YubiDetect._parse_device_rules(data)
    assert result == []

def test_parse_device_rules_valid() -> None:
    sample_line = "Bus 001 Device 002: ID 1050:0405 Yubico"
    data = sample_line + "\n"
    result = YubiDetect._parse_device_rules(data)
    assert ("1050", "0405") in result

def test_search_usb_device() -> None:
    device_data = ("1050", "0405")
    assert YubiDetect._search_usb_device(device_data, vendor="1050", device="0405")
    assert YubiDetect._search_usb_device(device_data, vendor="1050")
    assert YubiDetect._search_usb_device(device_data, device="0405")
    assert not YubiDetect._search_usb_device(device_data, vendor="9999")
    assert not YubiDetect._search_usb_device(device_data, device="0000")
