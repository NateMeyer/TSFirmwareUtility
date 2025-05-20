import tslitex

class TSAgent:
    def __init__(self):
        # Initialize the TSAgent with any necessary state or configuration
        self.devices = []
        self.device_handle = None
        self.device_info = {}

    def __del__(self):
        """Ensure the device handle is closed when the instance is deleted."""
        if self.device_handle:
            print("Closing device handle")
            self.device_handle = None

    def get_devices(self):
        """Retrieve a list of available devices."""
        self.devices = []
        idx = 0
        while True:
            res, dev_info = tslitex.ThunderscopeListDevs(idx)
            if res == -1:    
                break
            else:
                print(f"Found device {idx}: {dev_info}")
                self.devices.append((f"{dev_info['device_path'].decode('utf-8')}", dev_info))
                idx += 1
        return self.devices

    def connect_device(self, device_name):
        if self.device_handle:
            """Disconnect the current device before connecting to a new one."""
            self.disconnect_device()
        """Connect to a specific device."""
        if device_name in self.devices[:][0]:
            index = next((i for i, item in enumerate(self.devices) if item[0] == device_name), -1)
            self.device_handle = tslitex.Thunderscope(dev_idx=index, skip_init=True)
            self.device_info = self.devices[index][1]
            print(f"Connected to {device_name}")
            return True
        else:
            print(f"Device {device_name} not found")
            return False

    def disconnect_device(self):
        """Disconnect"""
        if self.device_handle:
            del self.device_handle
            self.device_handle = None  # Simulate closing the handle
            print(f"Disconnected from {self.device_info['device_path']}")
            return True
        else:
            print(f"Device not connected")
            return False

    def query_device_status(self):
        sys_health = {}
        # Define the keys from tsScopeState_t
        keys = ["sys_health.temp_c", "sys_health.vcc_int", "sys_health.vcc_aux",
        "sys_health.vcc_bram", "sys_health.frontend_power_good", "sys_health.acq_power_good"
        ]
        """Query the status of a specific device."""
        if self.device_handle:
            status = self.device_handle.Status()
            for key in keys:
                value = status
                for part in key.split('.'):
                    value = value.get(part, "N/A")
                sys_health[key] = value
        
        return sys_health

    def perform_firmware_update(self, firmware_path):
        """Perform a firmware update on a specific device."""
        if self.device_handle:
            print(f"Updating firmware with {firmware_path}")
            with open(firmware_path, "rb") as f:
                bitstream_bytes = f.read()
            if 0 == self.device_handle.firmwareUpdate(bitstream_bytes):
                return True
            else:
                print(f"Firmware update failed")
        else:
            print(f"Not Connected to a device")

        return False
