import argparse
import os
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional

# --- Third Party Imports ---
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QScrollArea,
    QSplitter,
    QMessageBox,
    QComboBox,
    QPushButton,
    QLineEdit,
    QTabWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QColor

# --- External Hardware Modules (Assumed Existing) ---
import serial
import serial.tools.list_ports
import pyqtgraph as pg

# ASSUMING THESE EXIST AS REQUESTED
import config
from serial_reader import SerialReader
from plumbing_diagram import RocketPlumbingWidget

# ==========================================
#      HARDWARE MAPPING CONFIGURATION
# ==========================================

# Map the String IDs used in the Diagram to the Integer IDs expected by the MCU
# CHANGE THESE INDICES TO MATCH YOUR FIRMWARE
# Map the String IDs of sensors to the index in the incoming float array
# CHANGE THESE INDICES TO MATCH YOUR PAYLOAD ORDER

# ==========================================
#           VISUAL SETTINGS
# ==========================================
COLOR_BG = Qt.black
COLOR_TEXT = Qt.white
COLOR_GOX_PIPE_DIM = QColor("#441111")
COLOR_FUEL_PIPE_DIM = QColor("#112244")
COLOR_N2_PIPE_DIM = QColor("#442200")
FLUID_GOX = QColor("#FF5252")
FLUID_FUEL = QColor("#2979FF")
FLUID_N2 = QColor("#FFD600")
COLOR_VALVE_CLOSED = Qt.white
COLOR_VALVE_OPEN = QColor("#FF0000")


# ==========================================
#           COMMAND CLASS
# ==========================================
@dataclass
class Command:
    action: int
    parameters: List[int] = field(default_factory=lambda: [0, 0, 0, 0])

    def to_bytes(self) -> bytes:
        if len(self.parameters) != 4:
            raise ValueError("Parameters must be exactly 4 bytes")
        return bytes([self.action] + self.parameters)


# ==========================================
#           TELEMETRY WIDGET
# ==========================================
class TelemetryWidget(QWidget):
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

        for sensor_name, i in sorted(config.SENSOR_MAP.items(), key=lambda x: x[1]):
            buf = deque([0.0] * history, maxlen=history)
            self.pressure_buffers.append(buf)
            pen = pg.mkPen(color=colors[i % len(colors)], width=2)
            curve = self.pg_pressure.plot(list(buf), pen=pen, name=sensor_name)
            self.pressure_curves.append(curve)
        tabs.addTab(self.pg_pressure, "Pressures")

        # Load cell tab
        self.pg_load = pg.PlotWidget(title="Load Cell")
        self.pg_load.showGrid(x=True, y=True)
        self.load_buffer = deque([0.0] * history, maxlen=history)
        self.load_curve = self.pg_load.plot(
            list(self.load_buffer), pen=pg.mkPen(color=(200, 200, 0), width=2)
        )
        tabs.addTab(self.pg_load, "Load Cell")

        self._refresh_pending = False
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(100)
        self._refresh_timer.timeout.connect(self._refresh_plots)
        self._refresh_timer.start()

    def _refresh_plots(self):
        if not self._refresh_pending:
            return
        x = list(range(-len(self.time_buffer), 0))
        for buf, curve in zip(self.pressure_buffers, self.pressure_curves):
            curve.setData(list(range(-len(buf), 0)), list(buf))
        self.load_curve.setData(
            list(range(-len(self.load_buffer), 0)), list(self.load_buffer)
        )
        self._refresh_pending = False

    def update_all(self, pressures: List[float], load: float):
        if len(pressures) != 8:
            # Pad or truncate if needed
            pressures = (pressures + [0.0] * 8)[:8]
        self._t_counter += 1
        self.time_buffer.append(self._t_counter)
        for buf, v in zip(self.pressure_buffers, pressures):
            buf.append(float(v))
        self.load_buffer.append(float(load))
        self._refresh_pending = True


# ==========================================
#           MAIN INTEGRATION
# ==========================================
class MainWindow(QMainWindow):
    DEFAULT_BAUD = 115200

    def __init__(self, log_file: str):
        super().__init__()

        # If log file exists, add timestamp to filename
        if os.path.exists(log_file):
            base, ext = os.path.splitext(log_file)
            log_file = f"{base}_{int(time.time())}{ext}"

        self.log_file = open(log_file, "w")

        self.setWindowTitle("Rocket Engine P&ID - Integrated Control")
        self.resize(1200, 800)
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #212121; color: white; }
            QCheckBox { font-weight: bold; font-size: 13px; margin: 3px; }
            QGroupBox { border: 1px solid #555; font-weight: bold; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; top: -5px; left: 10px; padding: 0 5px; background-color: #212121; }
            QPushButton { background-color: #444; border: 1px solid #666; padding: 5px; color: white; }
            QPushButton:hover { background-color: #555; }
            QPushButton:pressed { background-color: #333; }
            QPushButton:disabled { background-color: #2a2a2a; color: #555; }
            QLineEdit, QComboBox { background-color: #333; color: white; border: 1px solid #555; padding: 3px; }
            QSplitter::handle { background-color: #444; width: 2px; } /* Style the drag bar */
        """
        )

        # Serial Vars
        self._serial: Optional[serial.Serial] = None
        self._reader: Optional[SerialReader] = None

        # UI Setup
        central = QWidget()
        self.setCentralWidget(central)

        # Main Layout is now a wrapper for the Splitter
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Maximize space

        # --- SPLITTER SETUP ---
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # 1. LEFT: P&ID Diagram
        self.pid = RocketPlumbingWidget(
            valve_press_callback=(
                lambda key, is_open: self.handle_valve_toggle(
                    2 if is_open else 0, key, self.checkboxes[key]
                )
            )
        )
        self.splitter.addWidget(self.pid)

        # 2. RIGHT: Control & Telemetry Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)

        # Telemetry Graph Widget
        self.telemetry = TelemetryWidget()
        self.telemetry.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # Set a minimum height for graphs so they don't vanish
        self.telemetry.setMinimumHeight(200)
        right_layout.addWidget(self.telemetry)

        # Connection Group
        self.setup_connection_ui(right_layout)

        # Valve Controls Group
        self.setup_valve_ui(right_layout)

        self.splitter.addWidget(right_panel)

        # --- ADJUST SIZES ---
        # Set the splitter handle to give P&ID most space (e.g., 1000px vs 300px)
        self.splitter.setSizes([900, 300])
        self.splitter.setCollapsible(
            1, True
        )  # Allow right panel to hide completely if dragged

        # Initial Logic Check
        self.pid.check_flow_logic()
        self.refresh_ports()
        self._set_controls_enabled(False)

    def setup_connection_ui(self, parent_layout):
        conn_group = QGroupBox("Connection")
        l = QGridLayout(conn_group)

        self.port_combo = QComboBox()
        l.addWidget(QLabel("Port:"), 0, 0)
        l.addWidget(self.port_combo, 0, 1)

        refresh_btn = QPushButton("R")
        refresh_btn.setFixedWidth(30)
        refresh_btn.clicked.connect(self.refresh_ports)
        l.addWidget(refresh_btn, 0, 2)

        self.baud_input = QLineEdit(str(self.DEFAULT_BAUD))
        l.addWidget(QLabel("Baud:"), 1, 0)
        l.addWidget(self.baud_input, 1, 1, 1, 2)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        l.addWidget(self.connect_btn, 2, 0, 1, 3)

        parent_layout.addWidget(conn_group)

    def setup_valve_ui(self, parent_layout):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Remove border from scroll area to look cleaner in the panel
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        v_layout = QVBoxLayout(content)
        v_layout.setContentsMargins(0, 0, 0, 0)

        # Global Commands
        self.open_all_btn = QPushButton("OPEN ALL")
        self.open_all_btn.setStyleSheet("background-color: #500; color: white;")
        self.open_all_btn.clicked.connect(
            lambda: self.send_global_command(config.COMMAND_ACTION_OPEN_ALL_VALVES)
        )
        v_layout.addWidget(self.open_all_btn)

        self.close_all_btn = QPushButton("CLOSE ALL")
        self.close_all_btn.setStyleSheet("background-color: #050; color: white;")
        self.close_all_btn.clicked.connect(
            lambda: self.send_global_command(config.COMMAND_ACTION_CLOSE_ALL_VALVES)
        )
        v_layout.addWidget(self.close_all_btn)

        self.ignition_btn = QPushButton("START IGNITION SEQUENCE")
        self.ignition_btn.setStyleSheet("background-color: #005; color: white;")
        self.ignition_btn.clicked.connect(
            lambda: self.send_global_command(
                config.COMMAND_ACTION_START_IGNITION_SEQUENCE
            )
        )
        v_layout.addWidget(self.ignition_btn)

        # Valve Checkboxes
        grp_valves = QGroupBox("Manual Valve Control")
        gv_layout = QVBoxLayout()
        sorted_keys = sorted(self.pid.valves.keys())
        self.checkboxes = {}

        for k in sorted_keys:
            # It's possible for the diagram to have valves not mapped in config.
            # e.g. PRV's are treated as valves but not controllable via commands.
            if k not in config.VALVE_MAP:
                continue
            v = self.pid.valves[k]
            cb = QCheckBox(v.name)
            cb.stateChanged.connect(
                lambda state, key=k, btn=cb: self.handle_valve_toggle(state, key, btn)
            )
            gv_layout.addWidget(cb)
            self.checkboxes[k] = cb

        grp_valves.setLayout(gv_layout)
        v_layout.addWidget(grp_valves)
        v_layout.addStretch()

        content.setLayout(v_layout)
        scroll.setWidget(content)
        parent_layout.addWidget(scroll)

    # --- SERIAL LOGIC ---

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.port_combo.addItem(f"{p.device} ({p.description})", p.device)
        if not ports:
            self.port_combo.addItem("No ports", "")

    def toggle_connection(self):
        if self._serial and self._serial.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port_data = self.port_combo.currentData()
        if not port_data:
            return

        try:
            baud = int(self.baud_input.text())
            self._serial = serial.Serial(port=port_data, baudrate=baud, timeout=0.1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed: {e}")
            return

        # Start Reader Thread
        self._reader = SerialReader(
            ser=self._serial,
            sop_byte=config.SOP_BYTE,
            eop_byte=config.EOP_BYTE,
            payload_parser=config.SensorDataParser(),
            max_buffer_size=config.MAX_SERIAL_BUFFER_SIZE,
        )
        self._reader.data_received.connect(self.on_data_received)
        self._reader.error.connect(
            lambda msg: QMessageBox.warning(self, "Serial Error", msg)
        )
        self._reader.start()

        self.connect_btn.setText("Disconnect")
        self.connect_btn.setStyleSheet("background-color: #004400;")
        self._set_controls_enabled(True)

    def disconnect_serial(self):
        if self._reader:
            self._reader.stop()
        if self._serial:
            self._serial.close()
        self._serial = None
        self._reader = None
        self.connect_btn.setText("Connect")
        self.connect_btn.setStyleSheet("")
        self._set_controls_enabled(False)

    def _set_controls_enabled(self, enabled):
        self.open_all_btn.setEnabled(enabled)
        self.close_all_btn.setEnabled(enabled)
        for cb in self.checkboxes.values():
            cb.setEnabled(enabled)

    def send_command(self, cmd: Command):
        if not (self._serial and self._serial.is_open):
            print("Serial not connected, command ignored.")
            return

        try:
            payload = config.COMMAND_SOP_BYTE + cmd.to_bytes() + config.COMMAND_EOP_BYTE
            self._serial.write(payload)
            print(f"TX: {cmd}")
            # Write to log file
            self.log_file.write(f"TX: {cmd}\n")
            self.log_file.flush()
        except Exception as e:
            print(f"Write failed: {e}")

    # --- HANDLERS ---

    def handle_valve_toggle(self, state: int, key: str, checkbox: QCheckBox):
        """
        State = 0 (Unchecked), 2 (Checked)

        Intercepts checkbox toggles.
        1. Checks Safety Logic (Purge vs Preslug).
        2. Sends Serial Command.
        3. Updates Visual Diagram.
        """
        is_opening = state == 2

        # --- 1. SAFETY CHECKS ---
        if is_opening and key in config.VALVE_INTERLOCKS:
            conflicting_valve_key = config.VALVE_INTERLOCKS[key]
            if self.pid.valves[conflicting_valve_key].is_open:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Safety Interlock Warning")
                msg.setText(
                    f"DANGER: {self.pid.valves[conflicting_valve_key].name} is OPEN."
                )
                msg.setInformativeText(
                    "Opening Purge while Preslug is open may cause backflow.\n\nProceed?"
                )
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.No)
                msg.setStyleSheet("background-color: #333; color: white;")

                if msg.exec() == QMessageBox.No:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
                    return

        checkbox.blockSignals(True)
        checkbox.setChecked(is_opening)
        checkbox.blockSignals(False)
        # --- 2. SEND SERIAL COMMAND ---
        if key in config.VALVE_MAP:
            valve_id = config.VALVE_MAP[key]
            action = (
                config.COMMAND_ACTION_OPEN_VALVE
                if is_opening
                else config.COMMAND_ACTION_CLOSE_VALVE
            )
            self.send_command(Command(action=action, parameters=[valve_id, 0, 0, 0]))
        else:
            print(f"Warning: Valve '{key}' not found in VALVE_MAP.")

        # --- 3. UPDATE VISUALS ---
        self.pid.set_valve_state(key, is_opening)

    def send_global_command(self, action):
        self.send_command(Command(action=action))
        # Update UI Optimistically on valve open/close
        if (
            action == config.COMMAND_ACTION_CLOSE_ALL_VALVES
            or action == config.COMMAND_ACTION_OPEN_ALL_VALVES
        ):
            target_state = action == config.COMMAND_ACTION_OPEN_ALL_VALVES
            for k, cb in self.checkboxes.items():
                cb.blockSignals(True)
                cb.setChecked(target_state)
                cb.blockSignals(False)
                self.pid.set_valve_state(k, target_state)

        if action == config.COMMAND_ACTION_START_IGNITION_SEQUENCE:
            self.pid.set_valve_state("gox_release", True)
            self.pid.set_valve_state("fuel_release", True)
            self.checkboxes["gox_release"].blockSignals(True)
            self.checkboxes["gox_release"].setChecked(True)
            self.checkboxes["gox_release"].blockSignals(False)
            self.checkboxes["fuel_release"].blockSignals(True)
            self.checkboxes["fuel_release"].setChecked(True)
            self.checkboxes["fuel_release"].blockSignals(False)

    @Slot(object)
    def on_data_received(self, sensor: config.SensorData):
        """
        Updates both the Telemetry Graphs and the P&ID Sensors
        """
        # Parse Readings
        try:
            pressures = [float(x) for x in sensor.pt_readings]
            load = float(sensor.load_cell_reading)

            # Update Graphs
            self.telemetry.update_all(pressures, load)

            # Update P&ID Numbers
            # Map the array index to the specific P&ID sensor ID
            for sensor_key, index in config.SENSOR_MAP.items():
                if index < len(pressures):
                    self.pid.set_sensor_value(sensor_key, pressures[index])

            # Log to file
            log_line = (
                f"RX: Time={sensor.timestamp}ms, "
                + ", ".join([f"PT{i}={p}psi" for i, p in enumerate(sensor.pt_readings)])
                + f", LoadCell={sensor.load_cell_reading}lbs\n"
            )
        except Exception as e:
            print(f"Error parsing sensor data: {e}")

    def closeEvent(self, event):
        self.disconnect_serial()
        event.accept()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rocket Engine P&ID Control Application"
    )

    # Add the --log_file argument
    parser.add_argument(
        "--log_file",
        type=str,
        help="Path to the log file. If not specified, logs will be printed to the console.",
        default=None,
    )

    # Parse the command-line arguments
    args = parser.parse_args()
    if not args.log_file:
        print("Error: --log_file argument is required.")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = MainWindow(log_file=args.log_file)
    window.show()
    sys.exit(app.exec())
