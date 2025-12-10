import struct
from dataclasses import dataclass
from typing import List

from payload import PayloadParser

SOP_BYTE = b"\xff"
EOP_BYTE = b"\xfe"

MAX_SERIAL_BUFFER_SIZE = 4096  # Prevent unbounded buffer growth


@dataclass
class SensorData:
    pt_readings: List[int]  # 7 uint16 values
    load_cell_reading: int  # uint8
    timestamp: int  # TickType_t assumed uint32


class SensorDataParser(PayloadParser):
    def get_expected_length(self) -> int:
        return 7 * 2 + 1 + 4  # 19 bytes

    def parse(self, payload: bytes) -> SensorData:
        if len(payload) != self.get_expected_length():
            raise ValueError("Invalid payload length")

        pt_readings = list(struct.unpack("<7H", payload[0:14]))
        load_cell_reading = struct.unpack("<B", payload[14:15])[0]
        timestamp = struct.unpack("<I", payload[15:19])[0]

        return SensorData(
            pt_readings=pt_readings,
            load_cell_reading=load_cell_reading,
            timestamp=timestamp,
        )


COMMAND_SOP_BYTE = b"\xff"
COMMAND_EOP_BYTE = b"\xfe"
COMMAND_ACTION_CLOSE_ALL_VALVES = 0x00
COMMAND_ACTION_OPEN_ALL_VALVES = 0x01
COMMAND_ACTION_START_IGNITION_SEQUENCE = 0x02
COMMAND_ACTION_OPEN_VALVE = 0x03
COMMAND_ACTION_CLOSE_VALVE = 0x04

VALVE_MAP = {
    "fuel_press": 0,
    "fuel_preslug": 1,
    "fuel_n2_purge": 2,
    "gox_n2_purge": 3,
    "gox_preslug": 4,
    "gox_release": 5,
    "fuel_release": 6,
}

# If a valve in the key is being opened, the valve in the value must be closed first.
VALVE_INTERLOCKS = {
    "gox_n2_purge": "gox_preslug",
    "fuel_n2_purge": "fuel_preslug",
}


SENSOR_MAP = {
    "chamber_pt": 0,
    "gox_inj_pt": 1,
    "fuel_inj_pt": 2,
    "fuel_n2_pt": 3,
    "fuel_line_pt": 4,
    "gox_reg_pt": 5,
    "gox_line_pt": 6,
}
