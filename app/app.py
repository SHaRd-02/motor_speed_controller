from textual.app import App
from textual.widgets import Static, Button, Input, Select, RichLog, Header, Footer
from textual.reactive import reactive
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import serial
import serial.tools.list_ports
import time

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class MotorControlApp(App):
    CSS_PATH = "app.tcss"
    current_speed = reactive(0)
    serial_connection = None
    rpm_buffer = []
    last_rpm = reactive(0)

    def compose(self):
        self.speed_display = Static(f"Set Speed: {self.current_speed} RPM", id="speed_display", classes="panel")
        self.rpm_display = Static("Measured RPM: 0", id="rpm_display", classes="panel")
        self.speed_input = Input(placeholder="Set Speed (RPM)", id="speed_input")
        self.start_button = Button("Start Motor", id="start_button")
        self.stop_button = Button("Stop Motor", id="stop_button")

        # Serial configuration widgets
        ports = [(port.device, port.device) for port in serial.tools.list_ports.comports()]
        self.port_select = Select(options=ports, prompt="Select Serial Port", id="port_select")
        self.baud_select = Select(
            options=[("9600", "9600"), ("19200", "19200"), ("38400", "38400"), ("57600", "57600"), ("115200", "115200")],
            prompt="Select Baudrate",
            id="baud_select"
        )
        self.connect_button = Button("Connect Serial", id="connect_serial")
        self.restart_button = Button("Restart Serial", id="restart_serial")
        self.terminal_log = RichLog(id="terminal_log", markup=True, classes="terminal")

        yield Header(show_clock=True)
        yield self.port_select
        yield self.baud_select
        yield self.connect_button
        yield self.restart_button
        yield self.speed_display
        yield self.rpm_display
        yield self.speed_input
        yield self.start_button
        yield self.stop_button
        yield self.terminal_log
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "connect_serial":
            self.connect_serial()
            return
        elif event.button.id == "restart_serial":
            self.restart_serial()
            return
        if event.button.id == "start_button":
            # Send current speed (or default 100 if 0)
            self.current_speed = 100
            self.update_speed_display()
        elif event.button.id == "stop_button":
            self.current_speed = 0
            self.speed_display.update("Set Speed: 0 RPM")
            self.send_serial_data("1\n")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "speed_input":
            try:
                speed_value = int(event.value)
                self.current_speed = speed_value
                self.update_speed_display()
            except ValueError:
                self.speed_display.update("Invalid speed value!")

    def update_speed_display(self):
        self.speed_display.update(f"Set Speed: {self.current_speed} RPM")
        # Send with newline so Arduino parseFloat/println works reliably
        self.send_serial_data(f"{self.current_speed}\n")

    def log_error(self, message: str):
        if hasattr(self, "terminal_log"):
            self.terminal_log.write(f"[ERROR] {message}")

    def save_speed_to_db(self, speed):
        try:
            supabase.table("speed_data").insert({
                "speed": speed
            }).execute()
            self.terminal_log.write(f"Record saved to DB...")

        except Exception as e:
            self.log_error(f"Supabase error: {e}")

    def connect_serial(self):
        try:
            selected_port = self.port_select.value
            selected_baud = int(self.baud_select.value)

            if not selected_port or not selected_baud:
                self.speed_display.update("Select port and baudrate first.")
                return

            self.serial_connection = serial.Serial(
                port=selected_port,
                baudrate=selected_baud,
                timeout=1
            )
            time.sleep(2)
            self.speed_display.update(f"Connected to {selected_port} @ {selected_baud}")

            # Read serial at lower frequency to avoid UI saturation
            self.set_interval(0.5, self.read_serial_data)
            self.set_interval(2, self.flush_rpm_buffer)
        except Exception as e:
            self.log_error(f"Serial connection error: {e}")

    def restart_serial(self):
        try:
            if self.serial_connection:
                self.serial_connection.close()
            self.serial_connection = None
            self.speed_display.update("Serial connection restarted.")
        except Exception as e:
            self.log_error(f"Restart error: {e}")

    def send_serial_data(self, data: str):
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.write(data.encode())
                self.terminal_log.write(f"[TX] {data.strip()}")
        except Exception as e:
            self.log_error(f"Serial send error: {e}")

    def read_serial_data(self):
        try:
            if self.serial_connection and self.serial_connection.is_open:
                rpm_values = []

                # Drain all available lines quickly
                while self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode(errors="ignore").strip()
                    if "RPM:" in line:
                        parts = line.split("RPM:")
                        if len(parts) > 1:
                            rpm_part = parts[1].split()[0]
                            try:
                                rpm_values.append(float(rpm_part))
                            except ValueError:
                                pass

                # If we received values during this interval, average them
                if rpm_values:
                    avg_rpm = sum(rpm_values) / len(rpm_values)
                    self.last_rpm = avg_rpm
                    self.rpm_display.update(f"Measured RPM (avg): {avg_rpm:.2f}")
                    self.rpm_buffer.append(avg_rpm)

        except Exception as e:
            self.log_error(f"Serial read error: {e}")

    def flush_rpm_buffer(self):
        if not self.rpm_buffer:
            return
        try:
            avg_rpm = sum(self.rpm_buffer) / len(self.rpm_buffer)
            supabase.table("speed_data").insert({
                "speed": avg_rpm
            }).execute()
            self.terminal_log.write(f"[DB] Saved avg RPM: {avg_rpm:.2f}")
            self.rpm_buffer.clear()
        except Exception as e:
            self.log_error(f"Supabase batch error: {e}")

if __name__ == "__main__":
    MotorControlApp().run()