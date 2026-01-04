import sys
import re
import argparse
from typing import List
from dataclasses import dataclass

from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import QTimer, Qt, QObject, QEvent
from PySide6.QtGui import QKeyEvent

# --- Project Imports ---
import config
from main import MainWindow


@dataclass
class MockSensorData:
    timestamp: int
    pt_readings: List[float]
    load_cell_reading: float


class KeyInterceptor(QObject):
    """Intercepts key presses globally across the window."""

    def __init__(self, replayer):
        super().__init__()
        self.replayer = replayer

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key_event = QKeyEvent(event)
            if key_event.key() == Qt.Key_Space:
                self.replayer.toggle_pause()
                return True  # Event handled
            elif key_event.key() == Qt.Key_Right:
                self.replayer.force_pause()
                self.replayer.step_forward()
                return True
            elif key_event.key() == Qt.Key_Left:
                self.replayer.force_pause()
                self.replayer.step_backward()
                return True
        return super().eventFilter(obj, event)


class ReplayController:
    def __init__(
        self, log_path: str, speed_factor: float = 1.0, starting_index: int = 0
    ):
        self.window = None
        self.log_path = log_path
        self.speed_factor = speed_factor
        self.events: List[MockSensorData] = []
        self.current_index = starting_index
        self.is_paused = True

        self.rx_pattern = re.compile(
            r"RX: Time=(?P<t>\d+)ms, PT0=(?P<pt0>[-\d.]+)psi, PT1=(?P<pt1>[-\d.]+)psi, "
            r"PT2=(?P<pt2>[-\d.]+)psi, PT3=(?P<pt3>[-\d.]+)psi, PT4=(?P<pt4>[-\d.]+)psi, "
            r"PT5=(?P<pt5>[-\d.]+)psi, PT6=(?P<pt6>[-\d.]+)psi, LoadCell=(?P<lc>[-\d.]+)lbs"
        )

        self.timer = QTimer()
        self.timer.timeout.connect(self.play_next_auto)

    def set_window(self, window: MainWindow):
        self.window = window
        self.status_label = QLabel("PAUSED | Space: Start", self.window)
        self.status_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #00FF00; 
                font-family: 'Courier New', monospace; 
                font-weight: bold; 
                font-size: 14px;
                padding: 10px; 
                background: rgba(0, 0, 0, 200);
                border: 2px solid #00FF00;
                border-radius: 4px;
            }
        """
        )
        self.status_label.show()
        self.reposition_overlay()

        # Install the global key interceptor
        self.interceptor = KeyInterceptor(self)
        self.window.installEventFilter(self.interceptor)

        self.window.command_connect_btn.setEnabled(False)
        self.window.setWindowTitle(f"REPLAY: {self.log_path}")

    def reposition_overlay(self):
        if self.window and self.status_label:
            self.status_label.adjustSize()
            x = self.window.width() - self.status_label.width() - 30
            y = self.window.height() - self.status_label.height() - 30
            self.status_label.move(x, y)

    def parse_file(self):
        try:
            with open(self.log_path, "r") as f:
                for line in f:
                    if not line.startswith("RX:"):
                        continue
                    match = self.rx_pattern.search(line)
                    if match:
                        d = match.groupdict()
                        self.events.append(
                            MockSensorData(
                                timestamp=int(d["t"]),
                                pt_readings=[float(d[f"pt{i}"]) for i in range(7)]
                                + [0.0],
                                load_cell_reading=float(d["lc"]),
                            )
                        )
            self.events.sort(key=lambda x: x.timestamp)
        except Exception as e:
            print(f"File Error: {e}")

    def update_status(self):
        mode = "PAUSED" if self.is_paused else "PLAYING"
        progress = f"{self.current_index}/{len(self.events)}"
        time_val = (
            self.events[self.current_index].timestamp
            if self.events and self.current_index < len(self.events)
            else 0
        )
        self.status_label.setText(
            f" {mode} | T+{time_val}ms | Frame {progress} | Arrows to Step "
        )
        self.reposition_overlay()

    def play_next_auto(self):
        if self.is_paused or self.current_index >= len(self.events):
            return
        self.step_forward()

    def step_forward(self):
        if self.current_index < len(self.events):
            curr_event = self.events[self.current_index]
            self.window.on_data_received(curr_event)
            if not self.is_paused and self.current_index + 1 < len(self.events):
                next_event = self.events[self.current_index + 1]
                delta = max(
                    1,
                    int(
                        (next_event.timestamp - curr_event.timestamp)
                        / self.speed_factor
                    ),
                )
                self.timer.setInterval(delta)
            self.current_index += 1
            self.update_status()

    def step_backward(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.window.on_data_received(self.events[self.current_index])
            self.update_status()

    def force_pause(self):
        """Used by arrow keys to ensure auto-play stops during manual stepping."""
        self.is_paused = True
        self.timer.stop()
        self.update_status()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if not self.is_paused:
            self.timer.start(1)
        else:
            self.timer.stop()
        self.update_status()


class ReplayWindow(MainWindow):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "replayer"):
            self.replayer.reposition_overlay()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--starting_index", type=int, default=0)
    args = parser.parse_args()

    app = QApplication(sys.argv)
    replayer = ReplayController(args.file, args.speed, args.starting_index)
    replayer.parse_file()

    window = ReplayWindow("replay_out.log")
    window.replayer = replayer  # Link for resize events
    replayer.set_window(window)

    window.show()
    sys.exit(app.exec())
