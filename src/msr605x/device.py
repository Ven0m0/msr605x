"""MSR605X USB HID device communication handler."""

import hid
from typing import Optional, Callable
from dataclasses import dataclass
from threading import Lock
import time

from .constants import (
    VENDOR_ID, PRODUCT_ID, HID_REPORT_SIZE, HID_TIMEOUT_MS,
    ErrorCode, ERROR_MESSAGES, ESC
)


@dataclass
class DeviceInfo:
    """MSR605X device information."""
    vendor_id: int
    product_id: int
    serial_number: str
    manufacturer: str
    product: str
    path: bytes


class MSR605XDevice:
    """
    Low-level USB HID communication with MSR605X device.

    This class handles the raw USB HID communication including
    connection management, sending commands, and receiving responses.
    """

    def __init__(self):
        self._device: Optional[hid.device] = None
        self._lock = Lock()
        self._connected = False
        self._device_info: Optional[DeviceInfo] = None
        self._on_status_change: Optional[Callable[[bool], None]] = None

    @property
    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self._connected and self._device is not None

    @property
    def device_info(self) -> Optional[DeviceInfo]:
        """Get device information."""
        return self._device_info

    def set_status_callback(self, callback: Callable[[bool], None]) -> None:
        """Set callback for connection status changes."""
        self._on_status_change = callback

    def _notify_status_change(self, connected: bool) -> None:
        """Notify listeners of connection status change."""
        if self._on_status_change:
            self._on_status_change(connected)

    @staticmethod
    def enumerate_devices() -> list[DeviceInfo]:
        """
        Enumerate all connected MSR605X devices.

        Returns:
            List of DeviceInfo objects for each found device.
        """
        devices = []
        for dev in hid.enumerate(VENDOR_ID, PRODUCT_ID):
            devices.append(DeviceInfo(
                vendor_id=dev['vendor_id'],
                product_id=dev['product_id'],
                serial_number=dev.get('serial_number', ''),
                manufacturer=dev.get('manufacturer_string', 'Unknown'),
                product=dev.get('product_string', 'MSR605X'),
                path=dev['path']
            ))
        return devices

    def connect(self, path: Optional[bytes] = None) -> tuple[bool, str]:
        """
        Connect to MSR605X device.

        Args:
            path: Optional specific device path. If None, connects to first found device.

        Returns:
            Tuple of (success, message)
        """
        with self._lock:
            if self._connected:
                return False, "Already connected"

            try:
                self._device = hid.device()

                if path:
                    self._device.open_path(path)
                else:
                    self._device.open(VENDOR_ID, PRODUCT_ID)

                self._device.set_nonblocking(False)
                self._connected = True

                # Get device info
                devices = self.enumerate_devices()
                if devices:
                    self._device_info = devices[0]

                self._notify_status_change(True)
                return True, "Connected successfully"

            except Exception as e:
                self._device = None
                self._connected = False
                return False, f"Connection failed: {str(e)}"

    def disconnect(self) -> tuple[bool, str]:
        """
        Disconnect from MSR605X device.

        Returns:
            Tuple of (success, message)
        """
        with self._lock:
            if not self._connected or not self._device:
                return False, "Not connected"

            try:
                self._device.close()
                self._device = None
                self._connected = False
                self._device_info = None
                self._notify_status_change(False)
                return True, "Disconnected successfully"

            except Exception as e:
                return False, f"Disconnect failed: {str(e)}"

    def _build_packets(self, data: bytes) -> list[bytes]:
        """
        Build HID packets with MSR605X header format.

        Header byte: bit7=first, bit6=last, bit0-5=length
        Supports multi-packet messages for data > 63 bytes.
        """
        MAX_PAYLOAD = 63
        packets = []

        offset = 0
        total_len = len(data)

        while offset < total_len:
            chunk = data[offset:offset + MAX_PAYLOAD]
            chunk_len = len(chunk)

            is_first = (offset == 0)
            is_last = (offset + chunk_len >= total_len)

            header = chunk_len
            if is_first:
                header |= 0x80
            if is_last:
                header |= 0x40

            packet = bytes([header]) + chunk + bytes(MAX_PAYLOAD - chunk_len)
            packets.append(packet)

            offset += MAX_PAYLOAD

        return packets

    def _parse_packet(self, packet: list) -> bytes:
        """Extract data from HID packet with MSR605X header."""
        if not packet:
            return b''
        header = packet[0]
        length = header & 0x3F
        return bytes(packet[1:1+length])

    def send_command(self, command: bytes, data: bytes = b'') -> tuple[bool, bytes]:
        """
        Send a command to the device.

        Args:
            command: Command bytes to send
            data: Optional data payload

        Returns:
            Tuple of (success, response_bytes)
        """
        if not self.is_connected:
            return False, b''

        with self._lock:
            try:
                # Build payload and packets with MSR605X header
                payload = command + data
                packets = self._build_packets(payload)

                # Send all packets
                for packet in packets:
                    bytes_written = self._device.write(packet)
                    if bytes_written < 0:
                        return False, b''

                return True, b''

            except Exception as e:
                print(f"Send error: {e}")
                return False, b''

    def receive_response(self, timeout_ms: int = HID_TIMEOUT_MS) -> tuple[bool, bytes]:
        """
        Receive response from device.

        Simple implementation matching working MSR605X driver.

        Args:
            timeout_ms: Timeout in milliseconds

        Returns:
            Tuple of (success, response_bytes)
        """
        if not self.is_connected:
            return False, b''

        with self._lock:
            try:
                response = b''
                start_time = time.time()

                while (time.time() - start_time) * 1000 < timeout_ms:
                    # Read with 1 second chunks for responsiveness
                    data = self._device.read(HID_REPORT_SIZE, timeout_ms=1000)
                    if data:
                        # Parse packet with MSR605X header format
                        header = data[0]
                        length = header & 0x3F
                        response += bytes(data[1:1+length])

                        # Check for last packet flag
                        if header & 0x40:
                            break

                return len(response) > 0, response

            except Exception as e:
                print(f"Receive error: {e}")
                return False, b''

    def send_and_receive(
        self,
        command: bytes,
        data: bytes = b'',
        timeout_ms: int = HID_TIMEOUT_MS
    ) -> tuple[bool, bytes]:
        """
        Send command and wait for response.

        Args:
            command: Command bytes to send
            data: Optional data payload
            timeout_ms: Response timeout in milliseconds

        Returns:
            Tuple of (success, response_bytes)
        """
        success, _ = self.send_command(command, data)
        if not success:
            return False, b''

        return self.receive_response(timeout_ms)

    def flush(self) -> None:
        """Flush any pending data from the device."""
        if not self.is_connected:
            return

        with self._lock:
            try:
                # Set non-blocking mode for flush
                self._device.set_nonblocking(True)
                # Read and discard any pending data
                while self._device.read(HID_REPORT_SIZE, timeout_ms=50):
                    pass
                # Restore blocking mode
                self._device.set_nonblocking(False)
            except Exception:
                pass
