import sys
import time
from typing import Optional, List
from PySide6.QtCore import Qt, QThread, Signal, Slot
import serial
from collections import deque
from typing import List, Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QDockWidget

# /E:/Workspace/GINAv2/application/main.py
#
# Simple PySide6 GUI for controlling an MCU over serial (COM/USB).
# Requirements: PySide6, pyserial
# Install: pip install PySide6 pyserial
#
# Commands sent (simple newline-terminated ASCII):
#   OPEN_ALL_VALVES
#   CLOSE_ALL_VALVES
#   OPEN_VALVE <n>
#   CLOSE_VALVE <n>
#   START_IGNITER
#
# Adjust command format to match your MCU's firmware protocol if needed.

#define COMMAND_TARGET_SERVO 0x00
COMMAND_TARGET_SERVO = 0x00
#define COMMAND_TARGET_IGNITER 0x01
COMMAND_TARGET_IGNITER = 0x01

#define COMMAND_ACTION_SERVO_CLOSE 0x00
COMMAND_ACTION_SERVO_CLOSE = 0x00
#define COMMAND_ACTION_SERVO_OPEN 0x01
COMMAND_ACTION_SERVO_OPEN = 0x01
#define COMMAND_ACTION_SERVO_SET 0x02
COMMAND_ACTION_SERVO_SET = 0x02

#define COMMAND_ACTION_IGNITER_START 0x00
COMMAND_ACTION_IGNITER_START = 0x00

#define COMMAND_PARAM_SERVO_ALL 0xEE
COMMAND_PARAM_SERVO_ALL = 0xEE

import struct



import serial


import time


from dataclasses import dataclass





# --- Configuration ---


# NOTE: If you are running on Windows, change this to 'COMx' (e.g., 'COM3')


SERIAL_PORT = '/dev/ttyUSB0'


BAUD_RATE = 115200

STRUCT_FORMAT = '<BBB4I'
EXPECTED_SIZE = struct.calcsize(STRUCT_FORMAT)

SOP_BYTE = b'\xFF'
EOP_BYTE = b'\xFE'

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QLineEdit,
)
try:
    import serial.tools.list_ports
except Exception as e:
    raise RuntimeError("pyserial is required: pip install pyserial") from e

try:
    import pyqtgraph as pg
except Exception as e:
    raise RuntimeError("pyqtgraph is required for the telemetry UI: pip install pyqtgraph") from e

class TelemetryWidget(QWidget):
    """
    Widget containing two plots:
    - Pressures: 8 overlaid pressure transducer traces
    - Load cell: single trace

    Use update_pressures(list_of_8_floats) and update_loadcell(float)
    to feed data in (these can be called from the main thread).
    """

    def __init__(self, history: int = 100, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.history = history

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Pressures tab
        self.pg_pressure = pg.PlotWidget(title="Pressure Transducers")
        self.pg_pressure.addLegend(offset=(10, 10))
        self.pg_pressure.showGrid(x=True, y=True)
        self.pressure_curves = []
        self.pressure_buffers = []
        self.time_buffer = deque(maxlen=history)
        self._t_counter = 0
        colors = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 165, 0),
            (128, 0, 128),
            (0, 255, 255),
            (255, 192, 203),
            (128, 128, 128),
        ]
        for i in range(8):
            buf = deque([0.0] * history, maxlen=history)
            self.pressure_buffers.append(buf)
            pen = pg.mkPen(color=colors[i % len(colors)], width=2)
            curve = self.pg_pressure.plot(list(buf), pen=pen, name=f"P{i}")
            self.pressure_curves.append(curve)
        tabs.addTab(self.pg_pressure, "Pressures")

        # Load cell tab
        self.pg_load = pg.PlotWidget(title="Load Cell")
        self.pg_load.showGrid(x=True, y=True)
        self.load_buffer = deque([0.0] * history, maxlen=history)
        self.load_curve = self.pg_load.plot(list(self.load_buffer), pen=pg.mkPen(color=(200, 200, 0), width=2))
        tabs.addTab(self.pg_load, "Load Cell")

        # Small timer to refresh plots at a human-rate (avoid updating on every sample)
        self._refresh_pending = False
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(100)  # ms
        self._refresh_timer.timeout.connect(self._refresh_plots)
        self._refresh_timer.start()

    def _refresh_plots(self):
        if not self._refresh_pending:
            return
        # Update pressure curves: use X that matches each buffer length to avoid shape mismatch
        for buf, curve in zip(self.pressure_buffers, self.pressure_curves):
            x = list(range(-len(buf), 0))
            curve.setData(x, list(buf))
        # Update load curve with matching X
        self.load_curve.setData(list(range(-len(self.load_buffer), 0)), list(self.load_buffer))
        self._refresh_pending = False

    def update_pressures(self, pressures: List[float]):
        """
        Append a single sample for each of the 8 pressure channels.
        pressures must be a sequence of length 8.
        """
        if len(pressures) != 8:
            raise ValueError("pressures must be length 8")
        self._t_counter += 1
        self.time_buffer.append(self._t_counter)
        for buf, v in zip(self.pressure_buffers, pressures):
            buf.append(float(v))
        self._refresh_pending = True

    def update_loadcell(self, value: float):
        """
        Append a single sample for load cell reading.
        """
        self.load_buffer.append(float(value))
        self._refresh_pending = True

    def update_all(self, pressures: List[float], load: float):
        """
        Convenience: update both pressures and load cell with one call.
        """
        self.update_pressures(pressures)
        self.update_loadcell(load)

@dataclass
class SensorData:
    pt_readings: List[int]          # 6 uint16 values
    load_cell_reading: int          # uint8
    timestamp: int                  # TickType_t assumed uint32

class SerialReader(QThread):
    # Emit parsed SensorData objects when a valid framed packet is received
    data_received = Signal(object)
    error = Signal(str)

    def __init__(self, ser: serial.Serial):
        super().__init__(parent=None)
        self._ser = ser
        self._running = True

    def run(self):
        buf = bytearray()
        # expected payload: 6 * uint16 (12) + uint8 (1) + uint32 (4) = 17 bytes
        expected_len = 6*2 + 1 + 4
        while self._running and self._ser and self._ser.is_open:
            try:
                available = self._ser.in_waiting
                if available:
                    print("available data")
                    chunk = self._ser.read(available)
                    if chunk:
                        buf.extend(chunk)

                    # process buffer looking for framed packets SOP..payload..EOP
                    while True:
                        try:
                            # find SOP (single byte)
                            sop_idx = buf.index(SOP_BYTE)
                            print("Found SOP at index", sop_idx)
                        except ValueError:
                            # no SOP yet; avoid unbounded growth
                            if len(buf) > 4096:
                                buf.clear()
                            break

                        # find EOP after SOP
                        try:
                            eop_idx = buf.index(EOP_BYTE, sop_idx + 1)
                            print("Found EOP at index", sop_idx)
                        except ValueError:
                            # wait for more data; but drop bytes before SOP to keep buffer small
                            if sop_idx > 0:
                                del buf[:sop_idx]
                            break

                        # extract payload between SOP and EOP
                        payload = bytes(buf[sop_idx + 1:eop_idx])
                        # remove processed bytes from buffer
                        del buf[:eop_idx + 1]

                        if len(payload) != expected_len:
                            print("Wrong Length:", len(payload), "expected", expected_len)
                            print("Payload:", payload)
                            # ignore unexpected-length payloads
                            continue

                        # parse payload: little-endian: 6H (uint16), B (uint8), I (uint32)
                        try:
                            # pt_readings: first 12 bytes
                            pt_vals = list(struct.unpack('<6H', payload[0:12]))
                            load = payload[12]
                            timestamp = struct.unpack('<I', payload[13:17])[0]
                            sensor = SensorData(pt_readings=pt_vals, load_cell_reading=load, timestamp=timestamp)
                            self.data_received.emit(sensor)
                        except Exception as e:
                            self.error.emit(f"Parse error: {e}")
                            continue
                else:
                    # small sleep to avoid busy loop
                    self.msleep(50)
            except Exception as e:
                self.error.emit(str(e))
                break

    def stop(self):
        self._running = False
        self.wait(200)

class MainWindow(QMainWindow):
    DEFAULT_BAUD = 115200
    VALVE_COUNT = 8

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCU COM Controller")
        self._serial: Optional[serial.Serial] = None
        self._reader: Optional[SerialReader] = None
        self.valve_states: List[bool] = [False] * self.VALVE_COUNT  # False = closed

        self._init_ui()
        self.refresh_ports()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Connection controls
        conn_group = QGroupBox("Connection")
        conn_layout = QHBoxLayout(conn_group)
        conn_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        conn_layout.addWidget(self.port_combo)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        conn_layout.addWidget(self.refresh_btn)

        conn_layout.addWidget(QLabel("Baud:"))
        self.baud_input = QLineEdit(str(self.DEFAULT_BAUD))
        self.baud_input.setMaximumWidth(100)
        conn_layout.addWidget(self.baud_input)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)

        self.status_label = QLabel("Disconnected")
        conn_layout.addWidget(self.status_label)
        conn_layout.addStretch()
        main_layout.addWidget(conn_group)

        # Top command buttons
        cmd_group = QGroupBox("Commands")
        cmd_layout = QHBoxLayout(cmd_group)
        self.open_all_btn = QPushButton("OPEN ALL VALVES")
        self.open_all_btn.clicked.connect(self.open_all_valves)
        cmd_layout.addWidget(self.open_all_btn)

        self.close_all_btn = QPushButton("CLOSE ALL VALVES")
        self.close_all_btn.clicked.connect(self.close_all_valves)
        cmd_layout.addWidget(self.close_all_btn)

        self.start_igniter_btn = QPushButton("START IGNITER")
        self.start_igniter_btn.clicked.connect(self.start_igniter)
        cmd_layout.addWidget(self.start_igniter_btn)
        cmd_layout.addStretch()
        main_layout.addWidget(cmd_group)

        # Valve grid
        valves_group = QGroupBox(f"Per-valve control (0..{self.VALVE_COUNT - 1})")
        valves_layout = QGridLayout(valves_group)
        self.valve_buttons = []
        for i in range(self.VALVE_COUNT):
            btn = QPushButton(f"Valve {i}: CLOSED")
            btn.setCheckable(True)
            btn.setProperty("index", i)
            btn.clicked.connect(self.toggle_valve)
            self.valve_buttons.append(btn)
            row = i // 4
            col = i % 4
            valves_layout.addWidget(btn, row, col)
        main_layout.addWidget(valves_group)

        # Optional numeric direct control
        direct_group = QGroupBox("Direct valve control")
        direct_layout = QHBoxLayout(direct_group)
        direct_layout.addWidget(QLabel("Valve #:"))
        self.direct_spin = QSpinBox()
        self.direct_spin.setRange(0, self.VALVE_COUNT - 1)
        direct_layout.addWidget(self.direct_spin)
        self.direct_open_btn = QPushButton("Open")
        self.direct_open_btn.clicked.connect(self.direct_open)
        direct_layout.addWidget(self.direct_open_btn)
        self.direct_close_btn = QPushButton("Close")
        self.direct_close_btn.clicked.connect(self.direct_close)
        direct_layout.addWidget(self.direct_close_btn)
        main_layout.addWidget(direct_group)

        # Log area
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)

        # Telemetry setup
        self.telemetry_widget = TelemetryWidget(parent=self)
        main_layout.addWidget(self.telemetry_widget)

        # Disable command widgets until connected
        self._set_controls_enabled(False)

    def attach_telemetry_dock(main_window, area: Qt.DockWidgetArea = Qt.RightDockWidgetArea) -> QDockWidget:
        """
        Attach a telemetry dock to the given QMainWindow and return the created QDockWidget.
        Call like: attach_telemetry_dock(self) from MainWindow.__init__ (or after creating the window).
        """
        dock = QDockWidget("Telemetry", main_window)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        widget = TelemetryWidget(parent=dock)
        dock.setWidget(widget)
        main_window.addDockWidget(area, dock)

        # Expose easy accessors on the main_window instance
        main_window.telemetry_dock = dock
        main_window.telemetry_widget = widget

        return dock

    def _set_controls_enabled(self, enabled: bool):
        for w in [
            self.open_all_btn,
            self.close_all_btn,
            self.start_igniter_btn,
            *self.valve_buttons,
            self.direct_open_btn,
            self.direct_close_btn,
        ]:
            w.setEnabled(enabled)

    def log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {msg}")

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            # label ports as UART devices in the UI
            self.port_combo.addItem(f"UART: {p.device} - {p.description}", p.device)
        if self.port_combo.count() == 0:
            self.port_combo.addItem("No UART ports found", "")
        self.log("UART port list refreshed")

    def toggle_connection(self):
        if self._serial and self._serial.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port_data = self.port_combo.currentData()
        port = port_data if port_data else self.port_combo.currentText()
        # if the displayed text contains the "UART:" prefix, strip it
        if isinstance(port, str) and port.startswith("UART:"):
            # expected format "UART: <device> - <desc>"
            parts = port.split(":", 1)[1].strip().split(" - ", 1)
            port = parts[0].strip() if parts else port
        if not port:
            QMessageBox.warning(self, "No Port", "Select a valid UART port first.")
            return
        try:
            baud = int(self.baud_input.text())
        except ValueError:
            baud = self.DEFAULT_BAUD
            self.baud_input.setText(str(baud))
        try:
            # open as a UART device (uses same pyserial Serial API)
            self._serial = serial.Serial(port=port.strip(), baudrate=baud, timeout=0.1)
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Could not open UART port: {e}")
            self.log(f"Failed to open {port}: {e}")
            self._serial = None
            return

        self._reader = SerialReader(self._serial)
        self._reader.data_received.connect(self.on_data_received)
        self._reader.error.connect(self.on_serial_error)
        self._reader.start()

        self.connect_btn.setText("Disconnect")
        self.status_label.setText(f"Connected (UART): {self._serial.port} @ {self._serial.baudrate}")
        self.log(f"Connected to UART {self._serial.port} @ {self._serial.baudrate}")
        self._set_controls_enabled(True)

    def disconnect_serial(self):
        if self._reader:
            self._reader.stop()
            self._reader = None
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass
            self.log(f"Disconnected {self._serial.port}")
            self._serial = None
        self.connect_btn.setText("Connect")
        self.status_label.setText("Disconnected")
        self._set_controls_enabled(False)

    @Slot(object)
    def on_data_received(self, sensor):
        # If an unexpected type is received, log generically
        if not isinstance(sensor, SensorData):
            self.log(f"RX (unknown): {sensor}")
            return

        # Log and forward to telemetry widget (pad to 8 pressure channels)
        self.log(f"RX Sensor - ts={sensor.timestamp} load={sensor.load_cell_reading} pts={sensor.pt_readings}")
        pressures = [float(x) for x in sensor.pt_readings]
        # pad to 8 channels with zeros if needed
        if len(pressures) < 8:
            pressures += [0.0] * (8 - len(pressures))
        self.telemetry_widget.update_all(
            pressures=pressures[:8],
            load=float(sensor.load_cell_reading),
        )

    @Slot(str)
    def on_serial_error(self, msg: str):
        self.log(f"Serial error: {msg}")
        QMessageBox.warning(self, "Serial Error", msg)
        self.disconnect_serial()

    def closeEvent(self, event):
        # cleanup
        if self._reader:
            self._reader.stop()
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass
        event.accept()

    def send_command(self, cmd: bytearray):
        payload = SOP_BYTE + cmd + EOP_BYTE
        if not (self._serial and self._serial.is_open):
            QMessageBox.warning(self, "Not connected", "UART port is not connected.")
            return
        try:
            self._serial.write(payload)
            self.log(f"TX: {payload}")
        except Exception as e:
            self.log(f"Write failed: {e}")
            QMessageBox.critical(self, "Write Error", str(e))
            self.disconnect_serial()

    # Command handlers
    def open_all_valves(self):
        values = bytearray([COMMAND_TARGET_SERVO, COMMAND_ACTION_SERVO_OPEN, COMMAND_PARAM_SERVO_ALL])
        self.send_command(values)
        # update UI states assuming MCU accepted command
        self.valve_states = [True] * self.VALVE_COUNT
        self._update_valve_buttons()

    def close_all_valves(self):
        values = bytearray([COMMAND_TARGET_SERVO, COMMAND_ACTION_SERVO_CLOSE, COMMAND_PARAM_SERVO_ALL])
        self.send_command(values)
        self.valve_states = [False] * self.VALVE_COUNT
        self._update_valve_buttons()

    def start_igniter(self):
        values = bytearray([COMMAND_TARGET_IGNITER, COMMAND_ACTION_IGNITER_START, 0x00])
        self.send_command(values)

    def toggle_valve(self):
        btn = self.sender()
        if not isinstance(btn, QPushButton):
            return
        idx = int(btn.property("index"))
        new_state = btn.isChecked()
        if new_state:
            values = bytearray([COMMAND_TARGET_SERVO, COMMAND_ACTION_SERVO_OPEN, idx])
        else:
            values = bytearray([COMMAND_TARGET_SERVO, COMMAND_ACTION_SERVO_CLOSE, idx])
        self.send_command(values)
        self.valve_states[idx] = new_state
        self._update_valve_buttons()

    def direct_open(self):
        values = bytearray([COMMAND_TARGET_SERVO, COMMAND_ACTION_SERVO_CLOSE, COMMAND_PARAM_SERVO_ALL])
        self.send_command(values)
        idx = self.direct_spin.value()
        self.valve_states[idx] = True
        self._update_valve_buttons()

    def direct_close(self):
        idx = self.direct_spin.value()
        values = bytearray([COMMAND_TARGET_SERVO, COMMAND_ACTION_SERVO_CLOSE, COMMAND_PARAM_SERVO_ALL])
        self.send_command(values)
        self.valve_states[idx] = False
        self._update_valve_buttons()

    def _update_valve_buttons(self):
        for i, btn in enumerate(self.valve_buttons):
            state = self.valve_states[i]
            btn.setChecked(state)
            btn.setText(f"Valve {i}: {'OPEN' if state else 'CLOSED'}")


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(800, 600)
    win.show()
    app.exec()


if __name__ == "__main__":
    main()