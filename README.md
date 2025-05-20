# Thunderscope Firmware Update Utility

A modern Python GUI application for updating Thunderscope device firmware, built with ttkbootstrap and tkinter.


## Usage

1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```sh
   python src/main.py
   ```

3. **Update firmware:**
   - Select a connected Thunderscope device from the dropdown menu.
   - Browse and select a valid bitstream (.bit) file.
   - Click "Update Bitstream" to start the firmware update.

## Requirements
- Python 3.8+
- ttkbootstrap, tkinter
- Thunderscope device and drivers

## Troubleshooting
- Ensure your device is connected and recognized by the system
- Run as administrator/root if you encounter permission issues
- For detailed errors, check the terminal output
