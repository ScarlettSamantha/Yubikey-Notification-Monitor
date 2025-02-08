from typing import List, Optional, Tuple
import re
from datetime import datetime
import subprocess

class YubiDetect():
    
    # 1050 = Yubico ID
    VENDOR: str = str(1050)
    # 0402 = ? | 0405 = 5-BIO | 0407 = NFC
    PRODUCTS: List[str] = ["0402", "0405", "0407"]
    
    LSUSB_CMD: str = "lsusb"
    LSUSB_TREE: str  = f"{LSUSB_CMD} -t "
    
    # Parses lsusb output into nice groups fo reasy parsing.
    LS_USB_PARSE_EXPRESSION = r"^Bus\s+(?P<bus>\d{1,3})\s+\w+\s+(?P<device_id>\d{1,3})\:\s+ID\s+(?P<vendor>[a-f0-9]{4})\:(?P<device>[a-f0-9]{4})\s+(.+)$"
    
    def __init__(self, usb_lsusb: bool = True):
        pass
    
    def _getDeviceTree(self, validate_in_tree: bool):
        _stdout: bytes = subprocess.check_output(self.LSUSB_CMD, shell=True)
        stdout: str = _stdout.decode()
        return stdout
        
    @classmethod
    def _parseDeviceRules(cls, data: str) -> List[Tuple[str, str]] | bool: 
        list_split: List[str] = data.split('\n')
        device_list: List[Tuple] = []
        for usb_line_item in list_split:
            matches = re.search(cls.LS_USB_PARSE_EXPRESSION, usb_line_item)
            if matches is None:
                continue
            device_dict = matches.groupdict()
            device_tuple: Tuple[str, str] = (device_dict['vendor'], device_dict['device'])
            device_list.append(device_tuple)
        return device_list
    
    @classmethod
    def _searchUsbDevice(cls, data: Tuple[str, str], vendor: Optional[str] = None, device: Optional[str] = None) -> bool:
        _vendor, _device = data
        vendor_found: bool = True if device is None and vendor == _vendor else False
        device_found: bool = True if vendor is None and device == _device else False
        return any((vendor_found, device_found)) or (((vendor is not None) and (vendor == _vendor)) and ((device is not None ) and (device == _device)))
        
    def searchDevice(self, vendor: Optional[str] = None, device: Optional[str] = None) -> bool:
        _data = self._parseDeviceRules(self._getDeviceTree(False))
        if _data is None or isinstance(_data, bool) or _data is False:
            return False
        for device_data in _data:
            if self._searchUsbDevice(device_data, vendor=vendor, device=device):
                return True
        return False
        
    def search_yubikey_exists(self) -> bool:
        _devices = self.PRODUCTS
        for device in _devices:
            result = self.searchDevice(self.VENDOR, device)
            if result:
                return True
        return False
    
    def get_number_keys(self) -> int:
        count: int = 0
        _devices = self.PRODUCTS
        for device in _devices:
            result = self.searchDevice(self.VENDOR, device)
            if result:
                count += 1
        return count
    

    def get_key_data(self, all_key_data: bool = False) -> List[Tuple[str, str]] | Tuple[str, str]:
        _result: List = []
        _devices = self.PRODUCTS
        for device in _devices:
            _tmp = self.searchDevice(self.VENDOR, device)
            if _tmp is False:
                return []
            elif _tmp is True and all_key_data is False:
                return (self.VENDOR, device)
            else:
                _result.append((self.VENDOR, device))
        return _result        
        
def benchmark(iterations: int = 1000):
    instance = YubiDetect(True)
    start = datetime.now().timestamp()
    for i in range(iterations):
        instance.get_key_data()
    end: float = datetime.now().timestamp() - start
    print(f"Time taken for {iterations} iterations: {end:.4f} seconds average {round(end / iterations, 5)} seconds per iteration")
    
    
if __name__ == "__main__":
    benchmark()
    
    