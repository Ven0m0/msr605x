"""MSR605X protocol constants and command codes."""

from enum import Enum, IntEnum
from typing import Final

# USB HID Device identifiers
VENDOR_ID: Final[int] = 0x0801
PRODUCT_ID: Final[int] = 0x0003

# Protocol constants
ESC: Final[bytes] = b'\x1b'
FS: Final[bytes] = b'\x1c'  # Field separator
GS: Final[bytes] = b'\x1d'  # Group separator
RS: Final[bytes] = b'\x1e'  # Record separator
US: Final[bytes] = b'\x1f'  # Unit separator

# Response status bytes
STATUS_OK: Final[bytes] = b'\x1b0'
STATUS_ERROR: Final[bytes] = b'\x1b1'


class Command(bytes, Enum):
    """MSR605X command codes."""
    # Device control
    RESET = ESC + b'a'
    TEST_COMM = ESC + b'e'
    TEST_RAM = ESC + b't'
    TEST_SENSOR = ESC + b'\x86'
    GET_MODEL = ESC + b't'
    GET_FIRMWARE = ESC + b'v'

    # LED control
    LED_ALL_OFF = ESC + b'\x81'
    LED_ALL_ON = ESC + b'\x82'
    LED_GREEN_ON = ESC + b'\x83'
    LED_YELLOW_ON = ESC + b'\x84'
    LED_RED_ON = ESC + b'\x85'

    # Read operations
    READ_ISO = ESC + b'r'
    READ_RAW = ESC + b'm'

    # Write operations
    WRITE_ISO = ESC + b'w'
    WRITE_RAW = ESC + b'n'

    # Erase operations
    ERASE_CARD = ESC + b'c'

    # Configuration
    SET_HICO = ESC + b'x'      # Hi-Co mode
    SET_LOCO = ESC + b'y'      # Lo-Co mode
    SET_COERCIVITY = ESC + b'x'  # Alias for Hi-Co (backward compatibility)
    GET_COERCIVITY = ESC + b'd'
    SET_BPI = ESC + b'b'
    SET_BPC = ESC + b'o'
    SET_LEADING_ZERO = ESC + b'z'
    GET_LEADING_ZERO = ESC + b'l'


class Coercivity(IntEnum):
    """Card coercivity levels."""
    LOW = 0   # Lo-Co: 300 Oe
    HIGH = 1  # Hi-Co: 2750-4000 Oe


class TrackNumber(IntEnum):
    """Track identifiers."""
    TRACK_1 = 1
    TRACK_2 = 2
    TRACK_3 = 3
    ALL_TRACKS = 0


class BPI(IntEnum):
    """Bits Per Inch settings."""
    BPI_75 = 75
    BPI_210 = 210


class BPC(IntEnum):
    """Bits Per Character settings."""
    BPC_5 = 5
    BPC_7 = 7
    BPC_8 = 8


class DataFormat(str, Enum):
    """Data format types."""
    ISO = "iso"
    AAMVA = "aamva"
    CA_DMV = "ca_dmv"
    RAW = "raw"
    USER = "user"


# Track specifications (ISO 7811)
class TrackSpec:
    """Track specifications according to ISO 7811."""

    TRACK_1 = {
        "name": "Track 1",
        "bpi": 210,
        "bpc": 7,
        "max_chars": 79,
        "start_sentinel": "%",
        "end_sentinel": "?",
        "char_set": "alphanumeric",
        "encoding": "DEC SIXBIT",
    }

    TRACK_2 = {
        "name": "Track 2",
        "bpi": 75,
        "bpc": 5,
        "max_chars": 40,
        "start_sentinel": ";",
        "end_sentinel": "?",
        "char_set": "numeric",
        "encoding": "BCD",
    }

    TRACK_3 = {
        "name": "Track 3",
        "bpi": 210,
        "bpc": 5,
        "max_chars": 107,
        "start_sentinel": ";",
        "end_sentinel": "?",
        "char_set": "numeric",
        "encoding": "BCD",
    }


# Error codes
class ErrorCode(IntEnum):
    """MSR605X error codes."""
    SUCCESS = 0
    READ_WRITE_ERROR = 1
    COMMAND_FORMAT_ERROR = 2
    INVALID_COMMAND = 3
    INVALID_CARD_SWIPE = 4
    SET_ERROR = 5
    COMMUNICATION_ERROR = 6
    DEVICE_NOT_FOUND = 7
    DEVICE_BUSY = 8
    UNKNOWN_ERROR = 99


ERROR_MESSAGES = {
    ErrorCode.SUCCESS: "Operation completed successfully",
    ErrorCode.READ_WRITE_ERROR: "Read/write error occurred",
    ErrorCode.COMMAND_FORMAT_ERROR: "Invalid command format",
    ErrorCode.INVALID_COMMAND: "Invalid command",
    ErrorCode.INVALID_CARD_SWIPE: "Invalid card swipe - please try again",
    ErrorCode.SET_ERROR: "Configuration setting error",
    ErrorCode.COMMUNICATION_ERROR: "Communication error with device",
    ErrorCode.DEVICE_NOT_FOUND: "MSR605X device not found",
    ErrorCode.DEVICE_BUSY: "Device is busy",
    ErrorCode.UNKNOWN_ERROR: "Unknown error occurred",
}


# Track data delimiters for parsing
TRACK_START_MARKERS = {
    1: b'\x1b\x01',  # ESC + track number
    2: b'\x1b\x02',
    3: b'\x1b\x03',
}

TRACK_END_MARKER = b'\x1c'  # FS (Field Separator)

# Response parsing
RESPONSE_START = b'\x1b\x73'  # ESC + 's' (start of data)
RESPONSE_END = b'\x3f\x1c'    # '?' + FS (end sentinel + separator)

# HID report size
HID_REPORT_SIZE: Final[int] = 64
HID_TIMEOUT_MS: Final[int] = 5000
