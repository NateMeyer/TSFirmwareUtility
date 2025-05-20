import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import filedialog  # Correct import for filedialog
from tsagent import TSAgent
import threading
import traceback  # Ensure traceback is imported once

class FWUWindow(ttkb.Window):
    """Device Firmware Update Main Window"""
    def __init__(self):
        super().__init__(themename="pulse")  # Set a ttkbootstrap theme

        self.ts_agent = TSAgent()  # Initialize TSAgent

        self.title("Thunderscope Firmware Utility")
        self.geometry("650x450")  # Increased height by 50 pixels

        self.fwu_frame = ttkb.Frame(self)
        self.fwu_frame.pack(side=TOP, fill=BOTH, expand=True)  # Add expand=True to fill window

        self.label_title = ttkb.Label(self.fwu_frame,
                                      text="ThunderScope Firmware Update Utility",
                                      font=("System", 16))
        self.label_title.place(relx=0.5, y=20, anchor=CENTER)

        self.frame_device = DevicePicker(self.fwu_frame, self.ts_agent, self)
        self.frame_device.place(x=50, y=50, width=580)

        self.frame_bitstream = FilePicker(self.fwu_frame, self)
        self.frame_bitstream.place(x=50, y=100, width=580)

        self.save_config = ttkb.Button(self.fwu_frame, text="Download Factory\n    Calibration", state=DISABLED)
        self.save_config.place(x=90, y=170, height=60, width=145)

        self.load_update = ttkb.Button(self.fwu_frame, text=" Update\nBitstream", state=DISABLED, command=self.start_firmware_update)
        self.load_update.place(x=415, y=170, height=60, width=145)

        self.device_info = tk.Text(self.fwu_frame, borderwidth=2, relief="solid", font=("TkDefaultFont", 8), padx=8, pady=6)
        self.device_info.place(x=20, y=270, height=150, width=285)
        self.device_info.config(state=tk.DISABLED)

        # Health frames: Temperature, Int Voltage, Aux Voltage, BRAM Voltage
        self.health_frames = []
        health_titles = ["Temperature", "Int Voltage", "Aux Voltage", "BRAM Voltage"]
        for i, title in enumerate(health_titles):
            frame = ttkb.Labelframe(self.fwu_frame, text=title, width=130, height=65)
            frame.place(x=345 + (i % 2) * 145, y=270 + (i // 2) * 75, width=140, height=70)
            label = ttkb.Label(frame, text="--", font=("TkDefaultFont", 11))
            label.pack(expand=True, fill="both")
            self.health_frames.append((frame, label))

        self.frame_status = StatusBar(self)
        self.frame_status.set_status("Disconnected")
        self.frame_status.set_progress(0)

        self.resizable(0, 0)

    def destroy(self):
        """Override destroy to disconnect the device before closing."""
        self.ts_agent.disconnect_device()
        super().destroy()

    def start_firmware_update(self):
        """Begin firmware update and poll progress using Tkinter's after for safe GUI updates."""
        bitstream_file = self.frame_bitstream.file
        if not bitstream_file or not self.ts_agent.device_handle:
            return
        try:
            self.frame_status.set_status("Updating firmware...")
            self.frame_status.set_progress(0)
            self.load_update.config(state=DISABLED)
        except Exception as e:
            print(f"Error initializing status bar: {e}")
            traceback.print_exc()
        self._fw_update_polling = True
        self._fw_update_result = [None]
        def fw_update():
            try:
                self._fw_update_result[0] = self.ts_agent.perform_firmware_update(bitstream_file)
            except Exception as e:
                print(f"Firmware update error: {e}")
                traceback.print_exc()
                self._fw_update_result[0] = False
            self._fw_update_polling = False
        threading.Thread(target=fw_update, daemon=True).start()
        def poll_progress():
            progress = None
            if self.ts_agent.device_handle is not None:
                progress = getattr(self.ts_agent.device_handle, 'firmwareProgress', None)
            print(f"[DEBUG] Polling progress: {progress}")  # Debug print
            if progress is not None:
                try:
                    self.frame_status.set_progress(progress)
                    self.frame_status.set_status(f"Updating firmware... {progress}%")
                except Exception as e:
                    print(f"Error updating status bar: {e}")
                    traceback.print_exc()
            if self._fw_update_polling:
                self.after(400, poll_progress)
            else:
                try:
                    self.frame_status.set_progress(100)
                    result = self._fw_update_result[0]
                    self.frame_status.set_status("Firmware update complete" if result else "Firmware update failed")
                    self.load_update.config(state=NORMAL)
                except Exception as e:
                    print(f"Error updating status bar after update: {e}")
                    traceback.print_exc()
        # Wait 500ms before starting poll
        self.after(500, poll_progress)

class DevicePicker(ttkb.Frame):
    """Frame for Selecting the Device"""
    def __init__(self, master, ts_agent, root_window):
        super().__init__(master)
        self.root_window = root_window  # Store reference to the FWUWindow instance
        self.ts_agent = ts_agent
        self.available_ts_devs = []

        self.variable = ttkb.StringVar()
        self.dev_connect = ttkb.Button(self, text="Connect", width=12, state=DISABLED, command=self.device_connect)
        self.dev_connect.grid(column=1, row=0, sticky=E)

        self.variable.trace_add("write", self.on_device_selected)  # Add trace to monitor selection

        self.dev_picker = ttkb.Combobox(self, textvariable=self.variable, values=self.available_ts_devs, width=300, state='readonly')
        self.dev_picker.set("Select Available Device...")
        self.dev_picker.grid(column=0, row=0, padx=20)
        self.dev_picker.bind("<Button-1>", lambda event: self.update_device_list())  # Update list on click

        self.grid_columnconfigure(0, weight=1)

        self.update_device_list()

        self._polling = False
        self._poll_thread = None

    def update_device_list(self):
        """Update the available devices list using TSAgent."""
        devices = self.ts_agent.get_devices()
        self.available_ts_devs = [device[0] for device in devices]
        self.dev_picker["values"] = self.available_ts_devs

    def on_device_selected(self, *args):
        """Enable the connect button when a device is selected."""
        if self.variable.get() != "Select Available Device...":
            self.dev_connect.config(state=NORMAL)
        else:
            self.dev_connect.config(state=DISABLED)

    def select_device(self):
        # Enable Connect Button
        self.dev_connect.config(state='enabled')

    def device_connect(self):
        """Try to connect to the selected device."""
        selected_device = self.variable.get()
        if selected_device != "Select Available Device...":
            success = self.ts_agent.connect_device(selected_device)
            if success:
                print(f"Successfully connected to {selected_device}")
                try:
                    self.root_window.frame_status.set_status(f"Connected to {selected_device}")
                    self.root_window.frame_status.set_progress(0)
                except Exception as e:
                    print(f"Error updating status bar: {e}")

                # Enable save_config button
                self.root_window.save_config.config(state=NORMAL)

                # Enable load_update button if a file is already selected
                if self.root_window.frame_bitstream.file:
                    self.root_window.load_update.config(state=NORMAL)

                # Populate device_info text widget
                device_info = self.ts_agent.device_info
                self.root_window.device_info.config(state=tk.NORMAL)
                self.root_window.device_info.delete(1.0, ttkb.END)
                for key, value in device_info.items():
                    self.root_window.device_info.insert(ttkb.END, f"{key}: {value}\n")
                self.root_window.device_info.config(state=tk.DISABLED)

                # Disable combobox and change connect button to disconnect
                self.dev_picker.config(state='disabled')
                self.dev_connect.config(text="Disconnect", command=self.device_disconnect, state=NORMAL)

                # Start polling device status
                self.poll_device_status()
            else:
                print(f"Failed to connect to {selected_device}")

    def poll_device_status(self):
        """Poll the device status every second and update health frames with mapped values."""
        def status_poll_fn():
            while self._polling and self.ts_agent.device_handle:
                try:
                    status = self.ts_agent.query_device_status()
                    if status:
                        temp = status.get("sys_health.temp_c", "--")
                        volt_int = status.get("sys_health.vcc_int", "--")
                        volt_aux = status.get("sys_health.vcc_aux", "--")
                        volt_bram = status.get("sys_health.vcc_bram", "--")
                        temp_str = f"{temp/1000:.1f} °C" if isinstance(temp, (int, float)) else temp
                        vint_str = f"{volt_int} mV"
                        vaux_str = f"{volt_aux} mV"
                        vbram_str = f"{volt_bram} mV"
                        health_texts = [temp_str, vint_str, vaux_str, vbram_str]
                        for i, (frame, label) in enumerate(self.root_window.health_frames):
                            label.config(text=health_texts[i])
                except Exception as e:
                    print(f"Error polling device status: {e}")
                threading.Event().wait(1)

        self._polling = True
        self._poll_thread = threading.Thread(target=status_poll_fn, daemon=True)
        self._poll_thread.start()

    def device_disconnect(self):
        # Close active Connection and stop polling
        self._polling = False
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=0.2)
        if self.ts_agent.device_handle:
            self.ts_agent.disconnect_device()
            try:
                self.root_window.frame_status.set_status("Disconnected")
                self.root_window.frame_status.set_progress(0)
            except Exception as e:
                print(f"Error updating status bar: {e}")
                traceback.print_exc()
        # Re-enable combobox and reset connect button
        self.dev_picker.config(state='readonly')
        self.dev_connect.config(text="Connect", command=self.device_connect, state=NORMAL)
        # Clear device_info box
        self.root_window.device_info.config(state=tk.NORMAL)
        self.root_window.device_info.delete(1.0, ttkb.END)
        self.root_window.device_info.config(state=tk.DISABLED)
        # Set device health text to --
        for frame, label in self.root_window.health_frames:
            label.config(text="--")
        # Disable the download factory calibration button
        self.root_window.save_config.config(state=DISABLED)

class FilePicker(ttkb.Frame):
    """Frame for Selecting the Device"""
    def __init__(self, master, root_window):
        super().__init__(master)
        self.root_window = root_window  # Reference to FWUWindow
        self.file = None
        
        self.file_label = ttkb.Label(self, text="Bitstream Path:")
        self.file_label.grid(column=0, row=0)
        self.file_box = ttkb.Entry(self, width=300)
        self.file_box.grid(column=1, row=0, padx=20)

        self.browse = ttkb.Button(self, width=12, text="Browse...", command=self.file_browse)
        self.browse.grid(column=2, row=0, sticky=E)

        self.grid_columnconfigure(1, weight=1)

    def clear_file(self):
        """Clear the selected file and disable the load_update button."""
        self.file_box.delete(0, ttkb.END)
        self.file = None
        self.root_window.load_update.config(state=DISABLED)

    def file_browse(self):
        """Browse for a file"""
        self.file = filedialog.askopenfilename(initialdir="",
            title="Select a File",
            filetypes=(("Bitstream files", "*.bit"),
                       ("All Files", "*.*")))

        if self.file:
            # Verify valid bitstream file
            self.file_box.delete(0, ttkb.END)
            self.file_box.insert(ttkb.END, self.file)
            # Enable load_update button if a device is connected
            if self.root_window.ts_agent.device_handle:
                self.root_window.load_update.config(state=NORMAL)
        else:
            self.clear_file()


class StatusBar(ttkb.Frame):
    """Status bar at the bottom of the window using ttkbootstrap Floodgauge"""
    def __init__(self, master):
        super().__init__(master, borderwidth=1, relief="solid", height=30)
        self.pack_propagate(False)

        # Floodgauge for progress and status
        self.flood = ttkb.Floodgauge(self, bootstyle="primary", orient="horizontal", maximum=100, value=0, text="Disconnected", font=("TkDefaultFont", 8))
        self.flood.pack(fill=BOTH, expand=True, padx=2, pady=2)
        self.pack(side=BOTTOM, fill=X)

    def set_status(self, status=""):
        """Set the status text on the Floodgauge"""
        self.flood.configure(text=status)

    def set_progress(self, value):
        """Set the Floodgauge value (0-100) immediately, disabling animation."""
        self.flood.stop()  # Ensure animation is off
        self.flood.configure(value=value)

