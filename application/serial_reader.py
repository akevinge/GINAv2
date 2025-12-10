"""
Serial Reader Module for Framed Protocol Communication

This module provides a threaded serial reader that parses framed packets
with the format: SOP_BYTE + PAYLOAD + EOP_BYTE

Expected payload structure:
- 7 × uint16 (pressure transducer readings)
- 1 × uint8 (load cell reading)
- 1 × uint32 (timestamp)
Total: 19 bytes
"""

import struct
import serial
from PySide6.QtCore import QThread, Signal

from payload import PayloadParser


class SerialReader(QThread):
    """
    Background thread that continuously reads from a serial port,
    parses framed packets, and emits parsed SensorData objects.

    Signals:
        data_received: Emitted when a valid SensorData packet is parsed
        error: Emitted when an error occurs (parsing or I/O)
    """

    # Signals
    data_received = Signal(object)  # Emits SensorData objects
    error = Signal(str)  # Emits error messages

    def __init__(
        self,
        ser: serial.Serial,
        sop_byte: bytes,
        eop_byte: bytes,
        payload_parser: PayloadParser,
        max_buffer_size: int = 4096,
        parent=None,
    ):
        """
        Initialize the serial reader thread.

        Args:
            ser: An open serial.Serial instance
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._ser = ser
        self.sop_byte = sop_byte
        self.eop_byte = eop_byte
        self.payload_parser = payload_parser
        self.max_buffer_size = max_buffer_size
        self._running = True

    def run(self):
        """Main thread loop - reads and parses serial data"""
        buf = bytearray()

        while self._running and self._ser and self._ser.is_open:
            try:
                available = self._ser.in_waiting
                if available:
                    chunk = self._ser.read(available)
                    if chunk:
                        buf.extend(chunk)

                    # Process buffer looking for framed packets
                    self._process_buffer(buf)
                else:
                    # Small sleep to avoid busy loop
                    self.msleep(50)

            except Exception as e:
                self.error.emit(f"Serial read error: {e}")
                break

    def _process_buffer(self, buf: bytearray):
        """
        Process the buffer looking for complete framed packets.

        Args:
            buf: The buffer to process (modified in-place)
        """
        while True:
            # Find SOP (start of packet)
            try:
                sop_idx = buf.index(self.sop_byte)
            except ValueError:
                # No SOP found; clear old data to prevent unbounded growth
                if len(buf) > self.max_buffer_size:
                    buf.clear()
                break

            # Find EOP (end of packet) after SOP
            try:
                eop_idx = buf.index(self.eop_byte, sop_idx + 1)
            except ValueError:
                # Wait for more data; drop bytes before SOP to keep buffer small
                if sop_idx > 0:
                    del buf[:sop_idx]
                break

            # Extract payload between SOP and EOP
            raw_payload = bytes(buf[sop_idx + 1 : eop_idx])

            # Remove processed bytes from buffer
            del buf[: eop_idx + 1]

            # Validate and parse payload
            if len(raw_payload) == self.payload_parser.get_expected_length():
                self._parse_payload(raw_payload)
            # else:
            #     self.error.emit(
            #         f"Invalid payload length: {len(raw_payload)} "
            #         f"(expected {self.payload_parser.get_expected_length()})"
            # )

    def _parse_payload(self, payload: bytes):
        """
        Parse a valid payload and emit the data_received signal.

        Args:
            payload: The payload bytes to parse
        """
        try:
            data = self.payload_parser.parse(payload)
            self.data_received.emit(data)

        except Exception as e:
            self.error.emit(f"Payload parse error: {e}")

    def stop(self):
        """Stop the reader thread gracefully"""
        self._running = False
        self.wait(200)  # Wait up to 200ms for thread to finish
