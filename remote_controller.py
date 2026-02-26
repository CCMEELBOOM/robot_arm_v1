import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import queue
import time
import serial.tools.list_ports
for p in serial.tools.list_ports.comports():
    print(p.device, "-", p.description)
BAUD = 115200
#Communiates with Arduino at 115200 bits/second (BAUD RATE)
JOINT_NAMES = ["Gripper", "Wrist", "Twist", "Elbow", "Shoulder", "Base"]

class ArmGUI:
    def __init__(self, root):
        self.root = root
        root.title("Robot Arm Controller (6 Servos)")

        self.ser = None
        self.reader_thread = None
        self.stop_reader = threading.Event()
        self.rx_queue = queue.Queue()

        # --- Top bar: port dropdown + connect button ---
        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Port:").pack(side="left")

        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(top, textvariable=self.port_var, width=25, state="readonly")
        self.port_combo.pack(side="left", padx=6)

        self.refresh_button = ttk.Button(top, text="Refresh", command=self.refresh_ports)
        self.refresh_button.pack(side="left", padx=6)

        self.connect_button = ttk.Button(top, text="Connect", command=self.toggle_connection)
        self.connect_button.pack(side="left", padx=6)

        self.status_var = tk.StringVar(value="Not connected")
        ttk.Label(top, textvariable=self.status_var).pack(side="left", padx=12)

        # --- Sliders ---
        sliders = ttk.LabelFrame(root, text="Joint Angles", padding=10)
        sliders.pack(fill="x", padx=10, pady=6)

        self.slider_vars = []
        self.debounce_jobs = [None] * 6

        for j in range(6):
            row = ttk.Frame(sliders)
            row.pack(fill="x", pady=4)

            ttk.Label(row, text=f"{j}: {JOINT_NAMES[j]}", width=14).pack(side="left")

            var = tk.IntVar(value=90)
            self.slider_vars.append(var)

            scale = tk.Scale(
                row,
                from_=0, to=180,
                orient="horizontal",
                length=360,
                variable=var,
                command=lambda v, jj=j: self.on_slider(jj, v)
            )
            scale.pack(side="left", fill="x", expand=True, padx=8)

            val_label = ttk.Label(row, width=4, anchor="e")
            val_label.pack(side="right")
            var.trace_add("write", lambda *_args, vv=var, lab=val_label: lab.config(text=str(vv.get())))

        # --- Buttons ---
        buttons = ttk.Frame(root, padding=(10, 0, 10, 10))
        buttons.pack(fill="x")

        self.home_button = ttk.Button(buttons, text="Send All (Current)", command=self.send_all)
        self.home_button.pack(side="left")

        self.pose90_button = ttk.Button(buttons, text="Set All to 90°", command=self.set_all_90)
        self.pose90_button.pack(side="left", padx=8)

        # --- Output log ---
        log_frame = ttk.LabelFrame(root, text="Serial Output / Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.log = tk.Text(log_frame, height=10, wrap="word")
        self.log.pack(fill="both", expand=True)

        self.refresh_ports()
        self.root.after(50, self.process_rx_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.enable_controls(False)

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])
        self.log_line(f"Ports found: {ports if ports else 'None'}")

    def enable_controls(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for child in self.root.winfo_children():
            # leave top controls available
            pass
        self.home_button.configure(state=state)
        self.pose90_button.configure(state=state)

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        port = self.port_var.get()
        if not port:
            self.log_line("No port selected.")
            return
        try:
            self.ser = serial.Serial(port, BAUD, timeout=0.1)
            # Arduino resets when serial opens; give it a moment
            time.sleep(2.0)

            self.stop_reader.clear()
            self.reader_thread = threading.Thread(target=self.reader_loop, daemon=True)
            self.reader_thread.start()

            self.connect_button.configure(text="Disconnect")
            self.status_var.set(f"Connected to {port} @ {BAUD}")
            self.log_line(f"Connected to {port} @ {BAUD}")

            self.enable_controls(True)

            # Optional: send current slider values immediately
            self.send_all()

        except Exception as e:
            self.log_line(f"Connect failed: {e}")
            self.status_var.set("Not connected")
            self.ser = None
            self.enable_controls(False)

    def disconnect(self):
        self.enable_controls(False)
        self.stop_reader.set()
        try:
            if self.ser:
                self.ser.close()
        except Exception:
            pass
        self.ser = None
        self.connect_button.configure(text="Connect")
        self.status_var.set("Not connected")
        self.log_line("Disconnected.")

    def send_cmd(self, joint: int, angle: int):
        """Send: J <joint> <angle>\\n"""
        if not self.ser or not self.ser.is_open:
            return
        angle = max(0, min(180, int(angle)))
        msg = f"J {joint} {angle}\n"
        try:
            self.ser.write(msg.encode("utf-8"))
            self.log_line(f"TX: {msg.strip()}")
        except Exception as e:
            self.log_line(f"TX error: {e}")

    def on_slider(self, joint: int, value):
        """Debounce slider movement to avoid spamming serial."""
        angle = int(float(value))

        if self.debounce_jobs[joint] is not None:
            self.root.after_cancel(self.debounce_jobs[joint])

        # Send 40 ms after last movement
        self.debounce_jobs[joint] = self.root.after(
            40, lambda j=joint, a=angle: self.send_cmd(j, a)
        )

    def send_all(self):
        for j in range(6):
            self.send_cmd(j, self.slider_vars[j].get())

    def set_all_90(self):
        for v in self.slider_vars:
            v.set(90)
        self.send_all()

    def reader_loop(self):
        """Background thread: read Arduino output and push to queue."""
        while not self.stop_reader.is_set():
            try:
                if self.ser and self.ser.is_open:
                    line = self.ser.readline().decode("utf-8", errors="replace").strip()
                    if line:
                        self.rx_queue.put(line)
                else:
                    time.sleep(0.05)
            except Exception as e:
                self.rx_queue.put(f"RX error: {e}")
                time.sleep(0.2)

    def process_rx_queue(self):
        """UI thread: display received lines."""
        try:
            while True:
                line = self.rx_queue.get_nowait()
                self.log_line(f"RX: {line}")
        except queue.Empty:
            pass
        self.root.after(50, self.process_rx_queue)

    def log_line(self, text: str):
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def on_close(self):
        self.disconnect()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ArmGUI(root)
    root.mainloop()