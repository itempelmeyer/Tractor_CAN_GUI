#This code when ran on a system with CAN module will open a GUI over an X-server ssh bridge and...
#allow control of transmission of Tractor messages
#Created by Ian Tempelmeyer 09/15/2024

import can
import tkinter as tk
from tkinter import ttk
import threading
import time
import warnings
import sys
import os

# Suppress DeprecationWarnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Redirect standard error to suppress specific messages
sys.stderr = open(os.devnull, 'w')

class CanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CAN Interface GUI")

        self.root.bind("<Control-z>", self.quit_application)

        self.default_can_interface = "can0"
        self.default_cycle_time_ms = 100

#Frame and Widget (GUI) Setup

        # Frame for Engine RPM CAN message controls
        self.frame_original = ttk.Frame(self.root)
        self.frame_original.grid(row=0, column=0, padx=10, pady=10)

        # Engine RPM Title and Entry
        self.rpm_label = ttk.Label(self.frame_original, text="Engine RPM:")
        self.rpm_label.grid(row=0, column=0, columnspan=2, pady=5, sticky=tk.W)

        self.rpm_entry = ttk.Entry(self.frame_original, width=10)
        self.rpm_entry.grid(row=1, column=0, columnspan=2, pady=5)
        self.rpm_entry.insert(0, "0")  # Set default value to 0

        # Cycle Time and CAN Interface Labels for Engine RPM
        self.cycle_time_label = ttk.Label(self.frame_original, text=f"Cycle Time: {self.default_cycle_time_ms} ms")
        self.cycle_time_label.grid(row=2, column=0, columnspan=2, pady=5)

        self.can_interface_label = ttk.Label(self.frame_original, text=f"CAN Interface: {self.default_can_interface}")
        self.can_interface_label.grid(row=3, column=0, columnspan=2, pady=5)

        # Engine RPM CAN message Start/Stop Buttons
        self.start_button = ttk.Button(self.frame_original, text="Start", command=self.start_engine_rpm_transmission)
        self.start_button.grid(row=4, column=0, pady=5)

        self.stop_button = ttk.Button(self.frame_original, text="Stop", command=self.stop_engine_rpm_transmission)
        self.stop_button.grid(row=4, column=1, pady=5)

        # Status Label for Engine RPM CAN message
        self.original_status_label = ttk.Label(self.frame_original, text="Engine RPM CAN Message Status: Idle", foreground="red")
        self.original_status_label.grid(row=5, column=0, columnspan=2, pady=5)

        # Frame for the IVT Status CAN message controls
        self.frame_ivt = ttk.Frame(self.root)
        self.frame_ivt.grid(row=0, column=1, padx=10, pady=10)

        # IVT Status Toggle Switch
        ttk.Label(self.frame_ivt, text="IVT Status").grid(row=0, column=0, columnspan=2, pady=5)
        self.ivt_status_var = tk.StringVar(value="Not Parked")
        self.ivt_status_combobox = ttk.Combobox(self.frame_ivt, textvariable=self.ivt_status_var, values=["Parked", "Not Parked"], state="readonly")
        self.ivt_status_combobox.grid(row=1, column=0, columnspan=2, pady=5)
        self.ivt_status_combobox.bind("<<ComboboxSelected>>", self.update_ivt_status)

        # Cycle Time and CAN Interface Labels for IVT Status
        self.ivt_cycle_time_label = ttk.Label(self.frame_ivt, text=f"Cycle Time: {self.default_cycle_time_ms} ms")
        self.ivt_cycle_time_label.grid(row=2, column=0, columnspan=2, pady=5)

        self.ivt_can_interface_label = ttk.Label(self.frame_ivt, text=f"CAN Interface: {self.default_can_interface}")
        self.ivt_can_interface_label.grid(row=3, column=0, columnspan=2, pady=5)

        # IVT Status CAN message Start/Stop Buttons
        self.start_ivt_button = ttk.Button(self.frame_ivt, text="Start", command=self.start_ivt_transmission)
        self.start_ivt_button.grid(row=4, column=0, pady=5)

        self.stop_ivt_button = ttk.Button(self.frame_ivt, text="Stop", command=self.stop_ivt_transmission)
        self.stop_ivt_button.grid(row=4, column=1, pady=5)

        # Status Label for IVT Status CAN message
        self.ivt_status_label = ttk.Label(self.frame_ivt, text="IVT Status CAN Message Status: Idle", foreground="red")
        self.ivt_status_label.grid(row=5, column=0, columnspan=2, pady=5)

        # Frame for the Tractor Guidance CAN message controls
        self.frame_tractor_guidance = ttk.Frame(self.root)
        self.frame_tractor_guidance.grid(row=0, column=2, padx=10, pady=10)

        # Tractor Guidance Title and Entry
        self.tractor_guidance_label = ttk.Label(self.frame_tractor_guidance, text="Tractor Guidance (1/m):")
        self.tractor_guidance_label.grid(row=0, column=0, columnspan=2, pady=5, sticky=tk.W)

        self.tractor_guidance_entry = ttk.Entry(self.frame_tractor_guidance, width=10)
        self.tractor_guidance_entry.grid(row=1, column=0, columnspan=2, pady=5)
        self.tractor_guidance_entry.insert(0, "0")  # Set default value to 0

        # Cycle Time and CAN Interface Labels for Tractor Guidance
        self.tractor_guidance_cycle_time_label = ttk.Label(self.frame_tractor_guidance, text=f"Cycle Time: {self.default_cycle_time_ms} ms")
        self.tractor_guidance_cycle_time_label.grid(row=2, column=0, columnspan=2, pady=5)

        self.tractor_guidance_can_interface_label = ttk.Label(self.frame_tractor_guidance, text=f"CAN Interface: {self.default_can_interface}")
        self.tractor_guidance_can_interface_label.grid(row=3, column=0, columnspan=2, pady=5)

        # Tractor Guidance CAN message Start/Stop Buttons
        self.start_tractor_guidance_button = ttk.Button(self.frame_tractor_guidance, text="Start", command=self.start_tractor_guidance_transmission)
        self.start_tractor_guidance_button.grid(row=4, column=0, pady=5)

        self.stop_tractor_guidance_button = ttk.Button(self.frame_tractor_guidance, text="Stop", command=self.stop_tractor_guidance_transmission)
        self.stop_tractor_guidance_button.grid(row=4, column=1, pady=5)

        # Status Label for Tractor Guidance CAN message
        self.tractor_guidance_status_label = ttk.Label(self.frame_tractor_guidance, text="Tractor Guidance CAN Message Status: Idle", foreground="red")
        self.tractor_guidance_status_label.grid(row=5, column=0, columnspan=2, pady=5)

        # Frame for the Hand Throttle % CAN message controls
        self.frame_hand_throttle = ttk.Frame(self.root)
        self.frame_hand_throttle.grid(row=1, column=0, padx=10, pady=10)

        # Hand Throttle % Title and Entry
        self.hand_throttle_label = ttk.Label(self.frame_hand_throttle, text="Hand Throttle %:")
        self.hand_throttle_label.grid(row=0, column=0, columnspan=2, pady=5, sticky=tk.W)

        self.hand_throttle_entry = ttk.Entry(self.frame_hand_throttle, width=10)
        self.hand_throttle_entry.grid(row=1, column=0, columnspan=2, pady=5)
        self.hand_throttle_entry.insert(0, "0")  # Set default value to 0

        # Cycle Time and CAN Interface Labels for Hand Throttle %
        self.hand_throttle_cycle_time_label = ttk.Label(self.frame_hand_throttle, text=f"Cycle Time: {self.default_cycle_time_ms} ms")
        self.hand_throttle_cycle_time_label.grid(row=2, column=0, columnspan=2, pady=5)

        self.hand_throttle_can_interface_label = ttk.Label(self.frame_hand_throttle, text=f"CAN Interface: {self.default_can_interface}")
        self.hand_throttle_can_interface_label.grid(row=3, column=0, columnspan=2, pady=5)

        # Hand Throttle % CAN message Start/Stop Buttons
        self.start_hand_throttle_button = ttk.Button(self.frame_hand_throttle, text="Start", command=self.start_hand_throttle_transmission)
        self.start_hand_throttle_button.grid(row=4, column=0, pady=5)

        self.stop_hand_throttle_button = ttk.Button(self.frame_hand_throttle, text="Stop", command=self.stop_hand_throttle_transmission)
        self.stop_hand_throttle_button.grid(row=4, column=1, pady=5)

        # Status Label for Hand Throttle % CAN message
        self.hand_throttle_status_label = ttk.Label(self.frame_hand_throttle, text="Hand Throttle % CAN Message Status: Idle", foreground="red")
        self.hand_throttle_status_label.grid(row=5, column=0, columnspan=2, pady=5)

	# Frame for the Set Speed MPH CAN message controls
        self.frame_set_speed = ttk.Frame(self.root)
        self.frame_set_speed.grid(row=1, column=1, padx=10, pady=10)

        # Set Speed MPH Title
        self.set_speed_label = ttk.Label(self.frame_set_speed, text="Set Speed MPH:")
        self.set_speed_label.grid(row=0, column=0, columnspan=4, pady=5, sticky=tk.W)

        # F1 Entry and Label
        self.f1_label = ttk.Label(self.frame_set_speed, text="F1:")
        self.f1_label.grid(row=1, column=0, pady=5, sticky=tk.E)

        self.f1_entry = ttk.Entry(self.frame_set_speed, width=10)
        self.f1_entry.grid(row=1, column=1, pady=5)
        self.f1_entry.insert(0, "10.0")  # Set default value to 10.0

        # F2 Entry and Label
        self.f2_label = ttk.Label(self.frame_set_speed, text="F2:")
        self.f2_label.grid(row=1, column=2, pady=5, sticky=tk.E)

        self.f2_entry = ttk.Entry(self.frame_set_speed, width=10)
        self.f2_entry.grid(row=1, column=3, pady=5)
        self.f2_entry.insert(0, "31.0")  # Set default value to 31.0

        # Cycle Time and CAN Interface Labels for Set Speed MPH
        self.set_speed_cycle_time_label = ttk.Label(self.frame_set_speed, text=f"Cycle Time: {self.default_cycle_time_ms} ms")
        self.set_speed_cycle_time_label.grid(row=2, column=0, columnspan=4, pady=5)

        self.set_speed_can_interface_label = ttk.Label(self.frame_set_speed, text=f"CAN Interface: {self.default_can_interface}")
        self.set_speed_can_interface_label.grid(row=3, column=0, columnspan=4, pady=5)

        # Set Speed MPH CAN message Start/Stop Buttons
        self.start_set_speed_button = ttk.Button(self.frame_set_speed, text="Start", command=self.start_set_speed_transmission)
        self.start_set_speed_button.grid(row=4, column=0, columnspan=2, pady=5)

        self.stop_set_speed_button = ttk.Button(self.frame_set_speed, text="Stop", command=self.stop_set_speed_transmission)
        self.stop_set_speed_button.grid(row=4, column=2, columnspan=2, pady=5)

        # Status Label for Set Speed MPH CAN message
        self.set_speed_status_label = ttk.Label(self.frame_set_speed, text="Set Speed MPH CAN Message Status: Idle", foreground="red")
        self.set_speed_status_label.grid(row=5, column=0, columnspan=4, pady=5)

        # Frame for the Tractor Speed CAN message controls
        self.frame_tractor_speed = ttk.Frame(self.root)
        self.frame_tractor_speed.grid(row=1, column=2, padx=10, pady=10)

        # Tractor Speed Title and Entry
        self.tractor_speed_label = ttk.Label(self.frame_tractor_speed, text="Tractor Speed (m/s):")
        self.tractor_speed_label.grid(row=0, column=0, columnspan=2, pady=5, sticky=tk.W)

        self.tractor_speed_entry = ttk.Entry(self.frame_tractor_speed, width=10)
        self.tractor_speed_entry.grid(row=1, column=0, columnspan=2, pady=5)
        self.tractor_speed_entry.insert(0, "0")  # Set default value to 0

        # Cycle Time and CAN Interface Labels for Tractor Speed
        self.tractor_speed_cycle_time_label = ttk.Label(self.frame_tractor_speed, text=f"Cycle Time: {self.default_cycle_time_ms} ms")
        self.tractor_speed_cycle_time_label.grid(row=2, column=0, columnspan=2, pady=5)

        self.tractor_speed_can_interface_label = ttk.Label(self.frame_tractor_speed, text=f"CAN Interface: {self.default_can_interface}")
        self.tractor_speed_can_interface_label.grid(row=3, column=0, columnspan=2, pady=5)

        # Tractor Speed CAN message Start/Stop Buttons
        self.start_tractor_speed_button = ttk.Button(self.frame_tractor_speed, text="Start", command=self.start_tractor_speed_transmission)
        self.start_tractor_speed_button.grid(row=4, column=0, pady=5)

        self.stop_tractor_speed_button = ttk.Button(self.frame_tractor_speed, text="Stop", command=self.stop_tractor_speed_transmission)
        self.stop_tractor_speed_button.grid(row=4, column=1, pady=5)

        # Status Label for Tractor Speed CAN message
        self.tractor_speed_status_label = ttk.Label(self.frame_tractor_speed, text="Tractor Speed CAN Message Status: Idle", foreground="red")
        self.tractor_speed_status_label.grid(row=5, column=0, columnspan=2, pady=5)

#        label = tk.label(root, text="Pres Ctrl+Z to quite the GUI")
#        label.pack()

# CAN Message Initialization defaults

        self.engine_rpm_transmission_active = False
        self.ivt_transmission_active = False
        self.tractor_guidance_transmission_active = False
        self.hand_throttle_transmission_active = False
        self.set_speed_transmission_active = False
        self.tractor_speed_transmission_active = False

#        self.signal_tread = threading.Thread(target=self.setup_signal_handling)
#        self.signal_thread.start()

#    def setup_signal_handling(self):
#        signal.signal(signal.SIGINT, self.signal_handler)

#    def signal_handler(self, signum, frame):
#        print("\nInterrupt signal received. Closing application...")
#        self.root.quit()
#        sys.exit(0)

    def quit_application(self, event=None):
        self.root.destroy()
        print("Application Quit. Closing GUI")

    def start_engine_rpm_transmission(self):
        if not self.engine_rpm_transmission_active:
            self.engine_rpm_transmission_active = True
            self.engine_rpm_transmission_bus = can.interface.Bus(channel=self.default_can_interface, interface='socketcan')
            self.engine_rpm_transmission_thread = threading.Thread(target=self.cyclic_engine_rpm_transmission)
            self.engine_rpm_transmission_thread.start()
            self.update_status("Engine RPM", "Sending")
            print("Engine RPM CAN message started.")

    def stop_engine_rpm_transmission(self):
        if self.engine_rpm_transmission_active:
            self.engine_rpm_transmission_active = False
            if self.engine_rpm_transmission_thread:
                self.engine_rpm_transmission_thread.join()
            if self.engine_rpm_transmission_bus:
                self.update_status("Engine RPM", "Idle")
            print("Engine RPM CAN message stopped.")

    def start_ivt_transmission(self):
        if not self.ivt_transmission_active:
            self.ivt_transmission_active = True
            self.ivt_transmission_thread = threading.Thread(target=self.cyclic_ivt_transmission)
            self.ivt_transmission_thread.start()
            self.update_status("IVT", "Sending")
            print("IVT Status CAN message started.")

    def stop_ivt_transmission(self):
        if self.ivt_transmission_active:
            self.ivt_transmission_active = False
            if self.ivt_transmission_thread:
                self.ivt_transmission_thread.join()
            self.update_status("IVT", "Idle")
            print("IVT Status CAN message stopped.")

    def start_tractor_guidance_transmission(self):
        if not self.tractor_guidance_transmission_active:
            self.tractor_guidance_transmission_active = True
            self.tractor_guidance_transmission_thread = threading.Thread(target=self.cyclic_tractor_guidance_transmission)
            self.tractor_guidance_transmission_thread.start()
            self.update_status("Tractor Guidance", "Sending")
            print("Tractor Guidance CAN message started.")

    def stop_tractor_guidance_transmission(self):
        if self.tractor_guidance_transmission_active:
            self.tractor_guidance_transmission_active = False
            if self.tractor_guidance_transmission_thread:
                self.tractor_guidance_transmission_thread.join()
            self.update_status("Tractor Guidance", "Idle")
            print("Tractor Guidance CAN message stopped.")

    def start_hand_throttle_transmission(self):
        if not self.hand_throttle_transmission_active:
            self.hand_throttle_transmission_active = True
            self.hand_throttle_transmission_thread = threading.Thread(target=self.cyclic_hand_throttle_transmission)
            self.hand_throttle_transmission_thread.start()
            self.update_status("Hand Throttle", "Sending")
            print("Hand Throttle % CAN message started.")

    def stop_hand_throttle_transmission(self):
        if self.hand_throttle_transmission_active:
            self.hand_throttle_transmission_active = False
            if self.hand_throttle_transmission_thread:
                self.hand_throttle_transmission_thread.join()
            self.update_status("Hand Throttle", "Idle")
            print("Hand Throttle % CAN message stopped.")

    def start_set_speed_transmission(self):
        if not self.set_speed_transmission_active:
            self.set_speed_transmission_active = True
            self.set_speed_transmission_thread = threading.Thread(target=self.cyclic_set_speed_transmission)
            self.set_speed_transmission_thread.start()
            self.update_status("Set Speed", "Sending")
            print("Set Speed MPH CAN message started.")

    def stop_set_speed_transmission(self):
        if self.set_speed_transmission_active:
            self.set_speed_transmission_active = False
            if self.set_speed_transmission_thread:
                self.set_speed_transmission_thread.join()
            self.update_status("Set Speed", "Idle")
            print("Set Speed MPH CAN message stopped.")

    def start_tractor_speed_transmission(self):
        if not self.tractor_speed_transmission_active:
           self.tractor_speed_transmission_active = True
           self.tractor_speed_transmission_thread = threading.Thread(target=self.cyclic_tractor_speed_transmission)
           self.tractor_speed_transmission_thread.start()
           self.update_status("Tractor Speed", "Sending")
           print("Tractor Speed CAN message started.")

    def stop_tractor_speed_transmission(self):
        if self.tractor_speed_transmission_active:
            self.tractor_speed_transmission_active = False
            if self.tractor_speed_transmission_thread:
                 self.tractor_speed_transmission_thread.join()
            self.update_status("Tractor Speed", "Idle")
            print("Tractor Speed CAN message stopped.")


# Status Labels

    def update_status(self, message_type, status):
        if message_type == "Engine RPM":
            self.original_status_label.config(text=f"Engine RPM CAN Message Status: {status}", foreground="green" if status == "Sending" else "red")
        elif message_type == "IVT":
            self.ivt_status_label.config(text=f"IVT Status CAN Message Status: {status}", foreground="green" if status == "Sending" else "red")
        elif message_type == "Tractor Guidance":
            self.tractor_guidance_status_label.config(text=f"Tractor Guidance CAN Message Status: {status}", foreground="green" if status == "Sending" else "red")
        elif message_type == "Hand Throttle":
            self.hand_throttle_status_label.config(text=f"Hand Throttle % CAN Message Status: {status}", foreground="green" if status == "Sending" else "red")
        elif message_type == "Set Speed":
            self.set_speed_status_label.config(text=f"Set Speed MPH CAN Message Status: {status}", foreground="green" if status == "Sending" else "red")
        elif message_type == "Tractor Speed":
            self.tractor_speed_status_label.config(text=f"Set Tractor Speed CAN Message Status: {status}", foreground="green" if status == "Sending" else "red") 

# CAN message Defenitions

    def cyclic_engine_rpm_transmission(self):
        bus = can.interface.Bus(channel=self.default_can_interface, interface='socketcan')
        while self.engine_rpm_transmission_active:
            rpm_value = self.rpm_entry.get() or "0"
            rpm = int(rpm_value)
            rpm_data = int(rpm / 0.125)
            message = can.Message(
                arbitration_id=0x0CF004FE,
                data=[0, 0, 0, rpm_data & 0xFF, (rpm_data >> 8) & 0xFF, 0, 0, 0],
                is_extended_id=True
            )
            try:
                bus.send(message)
            except can.CanError:
                print("Failed to send Engine RPM CAN message")
            except ValueError:
                print("Invalid Engine RPM value entered.")
            time.sleep(self.default_cycle_time_ms / 1000)

    def cyclic_ivt_transmission(self):
        bus = can.interface.Bus(channel=self.default_can_interface, interface='socketcan')
        while self.ivt_transmission_active:
            ivt_status_value = 0xCD if self.ivt_status_var.get() == "Parked" else 0xCC
            message = can.Message(
                arbitration_id=0x0CFFFE03,
                data=[0, 0, 0, ivt_status_value, 0, 0, 0, 0],
                is_extended_id=True
            )
            try:
                bus.send(message)
            except can.CanError:
                print("Failed to send IVT Status CAN message")
            time.sleep(self.default_cycle_time_ms / 1000)

    def cyclic_tractor_guidance_transmission(self):
        bus = can.interface.Bus(channel=self.default_can_interface, interface='socketcan')
        while self.tractor_guidance_transmission_active:
            try:
                guidance_value = self.tractor_guidance_entry.get() or "0"
                guidance = float(guidance_value)
                guidance_data = int((guidance * .25) - (8352 * 4))
                message = can.Message(
                    arbitration_id=0x0CAC00FE,
                    data=[guidance_data & 0xFF, (guidance_data >> 8) & 0xFF, 0, 0, 0, 0, 0, 0],
                    is_extended_id=True
                )
                bus.send(message)
            except can.CanError:
                print("Failed to send Tractor Guidance CAN message")
            except ValueError:
                print("Invalid Tractor Guidance value entered.")
            time.sleep(self.default_cycle_time_ms / 1000)

    def cyclic_hand_throttle_transmission(self):
        bus = can.interface.Bus(channel=self.default_can_interface, interface='socketcan')
        while self.hand_throttle_transmission_active:
            throttle_value = self.hand_throttle_entry.get() or "0"
            try:
                throttle = float(throttle_value)
                throttle_data = int(throttle / 0.4)
                message = can.Message(
                    arbitration_id=0x0CFFFF8C,
                    data=[0x4D, 0, 0, throttle_data & 0xFF, (throttle_data >> 8) & 0xFF, 0, 0, 0],
                    is_extended_id=True
                )
                bus.send(message)
            except can.CanError:
                print("Failed to send Hand Throttle % CAN message")
            except ValueError:
                print("Invalid Hand Throttle % value entered.")
            time.sleep(self.default_cycle_time_ms / 1000)

    def cyclic_set_speed_transmission(self):
        bus = can.interface.Bus(channel=self.default_can_interface, interface='socketcan')
        while self.set_speed_transmission_active:
            try:
                f1_value = self.f1_entry.get() or "10.0"
                f2_value = self.f2_entry.get() or "31.0"
                f1 = float(f1_value)
                f2 = float(f2_value)
                f1_data = int(f1 / 0.00124277943490)
                f2_data = int(f2 / 0.00124277943490)
                message = can.Message(
                    arbitration_id=0x18FFFF05,
                    data=[0x20, f1_data & 0xFF, (f1_data >> 8) & 0xFF, f2_data & 0xFF, (f2_data >> 8) & 0xFF, 0, 0, 0],
                    is_extended_id=True
                )
                try:
                    bus.send(message)
                except can.CanError:
                    print("Failed to send Set Speed MPH CAN message")
                time.sleep(self.default_cycle_time_ms / 1000)
            except ValueError:
                print("Invalid Set Speed MPH value")

    def cyclic_tractor_speed_transmission(self):
         bus = can.interface.Bus(channel=self.default_can_interface, interface='socketcan')
         while self.tractor_speed_transmission_active:
            speed_value = self.tractor_speed_entry.get() or "0"
            try:
                 speed = float(speed_value)
                 speed_data = int((speed * 3.6) / 0.00390625)
                 message = can.Message(
                     arbitration_id=0x18FEF1FE,
                     data=[0, speed_data & 0xFF, (speed_data >> 8) & 0xFF, 0, 0, 0, 0, 0],
                     is_extended_id=True
                 )
                 bus.send(message)
            except can.CanError:
                 print("Failed to send Tractor Speed (m/s) CAN message")
            except ValueError:
                 print("Invalid Tractor Speed (m/s) value entered.")
            time.sleep(self.default_cycle_time_ms / 1000)


    def update_ivt_status(self, event):
        if self.ivt_transmission_active:
            self.stop_ivt_transmission()
            self.start_ivt_transmission()

    def on_closing(self):
        self.stop_engine_rpm_transmission()
        self.stop_ivt_transmission()
        self.stop_tractor_guidance_transmission()
        self.stop_hand_throttle_transmission()
        self.stop_tractor_speed_transmission()
        self.root.destroy()

if __name__ == "__main__":
    print("Starting GUI application.")
    root = tk.Tk()
    app = CanApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
    print("GUI application closed.")
