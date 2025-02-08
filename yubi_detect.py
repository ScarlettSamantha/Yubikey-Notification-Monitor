#!/usr/bin/env python3
"""
Module for detecting YubiKey devices via lsusb.
"""

import re
import subprocess
from datetime import datetime
from typing import List, Tuple, Optional, Union


class YubiDetect:
    """
    Detects YubiKey devices by parsing lsusb output.
    """

    VENDOR: str = "1050"  # Yubico vendor ID.
    PRODUCTS: List[str] = ["0402", "0405", "0407"]  # Supported product codes.

    LSUSB_CMD: str = "lsusb"
    LS_USB_PARSE_EXPRESSION: str = (
        r"^Bus\s+(?P<bus>\d{1,3})\s+\w+\s+(?P<device_id>\d{1,3}):\s+ID\s+"
        r"(?P<vendor>[a-f0-9]{4}):(?P<device>[a-f0-9]{4})\s+(.+)$"
    )

    def __init__(self, use_lsusb: bool = True) -> None:
        self.use_lsusb = use_lsusb

    def _get_device_tree(self) -> str:
        """
        Retrieve the lsusb output.
        """
        output_bytes: bytes = subprocess.check_output(self.LSUSB_CMD, shell=True)
        return output_bytes.decode()

    @classmethod
    def _parse_device_rules(cls, data: str) -> List[Tuple[str, str]]:
        """
        Parse lsusb output and extract vendor and device IDs.
        """
        device_list: List[Tuple[str, str]] = []
        for line in data.splitlines():
            match = re.search(cls.LS_USB_PARSE_EXPRESSION, line)
            if match:
                groups = match.groupdict()
                device_list.append((groups["vendor"], groups["device"]))
        return device_list

    @classmethod
    def _search_usb_device(
        cls, device_data: Tuple[str, str], vendor: Optional[str] = None, device: Optional[str] = None
    ) -> bool:
        """
        Check if a device matches the specified vendor and/or device IDs.
        """
        current_vendor, current_device = device_data
        if vendor is not None and device is not None:
            return vendor == current_vendor and device == current_device
        if vendor is not None:
            return vendor == current_vendor
        if device is not None:
            return device == current_device
        return False

    def search_device(self, vendor: Optional[str] = None, device: Optional[str] = None) -> bool:
        """
        Search for a device matching the given vendor and device IDs.
        """
        tree = self._get_device_tree()
        devices = self._parse_device_rules(tree)
        return any(self._search_usb_device(dev, vendor, device) for dev in devices)

    def search_yubikey_exists(self) -> bool:
        """
        Determine if any supported YubiKey is present.
        """
        return any(self.search_device(self.VENDOR, prod) for prod in self.PRODUCTS)

    def get_number_keys(self) -> int:
        """
        Count the number of detected YubiKeys.
        """
        return sum(1 for prod in self.PRODUCTS if self.search_device(self.VENDOR, prod))

    def get_key_data(
        self, all_key_data: bool = False
    ) -> Union[List[Tuple[str, str]], Optional[Tuple[str, str]]]:
        """
        Retrieve YubiKey data.
        """
        found = [(self.VENDOR, prod) for prod in self.PRODUCTS if self.search_device(self.VENDOR, prod)]
        return found if all_key_data else (found[0] if found else None)


def benchmark(iterations: int = 1000) -> None:
    """
    Benchmark the get_key_data method.
    """
    instance = YubiDetect(True)
    start = datetime.now().timestamp()
    for _ in range(iterations):
        instance.get_key_data()
    total = datetime.now().timestamp() - start
    avg = total / iterations
    print(f"Time for {iterations} iterations: {total:.4f} sec, average {avg:.5f} sec per iteration")


if __name__ == "__main__":
    benchmark()
