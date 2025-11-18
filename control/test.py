import struct
import serial
import time
from dataclasses import dataclass

# --- Configuration ---
# NOTE: If you are running on Windows, change this to 'COMx' (e.g., 'COM3')
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200

# The packed C struct definition:
# typedef struct __attribute__((packed)) {
#   uint8_t command_type;
#   uint8_t address;
#   uint8_t target;
#   uint32_t parameters[4];
# } command_t;
# Total size: 19 bytes

# Struct format string for Python's 'struct' module:
# '<' = Little-Endian (Standard for most microcontrollers, including ESP32)
# 'B' = uint8_t (unsigned char)
# '4I' = 4 x uint32_t (unsigned integer)
STRUCT_FORMAT = '<BBB4I'
EXPECTED_SIZE = struct.calcsize(STRUCT_FORMAT)

SOP_BYTE = b'\xFF'
EOP_BYTE = b'\xFE'

@dataclass
class Command:
    """Represents the data to be packed into the command_t struct."""
    command_type: int
    address: int
    target: int
    param0: int
    param1: int
    param2: int
    param3: int

def create_packed_payload(command_data: Command) -> bytes:
    """
    Packs the Command dataclass into a raw binary payload.
    """
    print(f"Packing data into binary struct (Format: {STRUCT_FORMAT})...")
    
    # Pack the fields according to the struct format
    payload = struct.pack(
        STRUCT_FORMAT,
        command_data.command_type,
        command_data.address,
        command_data.target,
        command_data.param0,
        command_data.param1,
        command_data.param2,
        command_data.param3
    )

    payload = SOP_BYTE + payload + EOP_BYTE
    
    # Sanity check
    if len(payload) != EXPECTED_SIZE + 2:
        raise ValueError(f"Packed size mismatch: expected {EXPECTED_SIZE} bytes, got {len(payload)}")

    print(f"Payload created successfully ({len(payload)} bytes):")
    # Print the hex representation of the payload for verification
    print(f"  HEX: {payload.hex()}")
    
    return payload

def send_payload(payload: bytes):
    """
    Initializes the serial port and sends the raw byte payload.
    """
    print(f"\nAttempting to open serial port: {SERIAL_PORT} @ {BAUD_RATE}...")
    try:
        # Open the serial port
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        
        # Clear any potential junk in the buffer
        ser.reset_output_buffer()
        time.sleep(0.1)
        
        # Send the data
        bytes_sent = ser.write(payload)
        ser.flush() # Wait until all data is written
        
        print(f"Success! Sent {bytes_sent} bytes to the device.")

        # Optional: Read back any immediate response (e.g., logs)
        print("--- Reading device output for 0.5s ---")
        time.sleep(0.5)
        response = ser.read_all()
        if response:
            print(response.decode(errors='ignore'))
        
        ser.close()
        
    except serial.SerialException as e:
        print(f"\n!!! ERROR: Could not open or communicate with {SERIAL_PORT}.")
        print(f"!!! Check: 1. Port name is correct. 2. Device is connected. 3. Port is not in use.")
        print(f"Details: {e}")

if __name__ == '__main__':
    # --- Define the command data to send ---
    # We use non-zero values (1, 2, 3) to easily verify correct parsing on the device.
    command_to_send = Command(
        command_type=0, # 0x01
        address=2,      # 0x02
        target=3,       # 0x03
        param0=0xDEADBEEF, # Example non-zero uint32
        param1=0,
        param2=0,
        param3=0
    )

    # 1. Create the binary payload
    binary_payload = create_packed_payload(command_to_send)
    
    # 2. Send the payload
    # NOTE: You must have the 'pyserial' library installed: pip install pyserial
    send_payload(binary_payload)
    
    print("\nScript finished.")
