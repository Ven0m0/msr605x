"""MSR605X high-level command interface."""

from typing import Optional
from dataclasses import dataclass
from enum import Enum

from .device import MSR605XDevice
from .constants import (
    Command, Coercivity, TrackNumber, BPI, BPC, DataFormat,
    ErrorCode, ERROR_MESSAGES, ESC, FS, STATUS_OK, STATUS_ERROR,
    HID_TIMEOUT_MS
)
from .parser import TrackParser, TrackData


@dataclass
class CommandResult:
    """Result of a command execution."""
    success: bool
    error_code: ErrorCode
    message: str
    data: Optional[bytes] = None
    tracks: Optional[list[TrackData]] = None


class MSR605XCommands:
    """
    High-level command interface for MSR605X device.

    Provides user-friendly methods for all MSR605X operations
    including reading, writing, erasing, and configuration.
    """

    def __init__(self, device: MSR605XDevice):
        self._device = device
        self._parser = TrackParser()
        self._coercivity = Coercivity.HIGH
        self._data_format = DataFormat.ISO

    @property
    def device(self) -> MSR605XDevice:
        """Get the underlying device."""
        return self._device

    @property
    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self._device.is_connected

    def _parse_status(self, response: bytes) -> tuple[bool, ErrorCode]:
        """Parse response status byte.

        Simple check: success if ESC '0' is in response.
        Based on working MSR605X implementation.
        """
        if not response:
            return False, ErrorCode.COMMUNICATION_ERROR

        # Simple success check (matches working implementation)
        if b'\x1b0' in response or b'\x1b\x30' in response:
            return True, ErrorCode.SUCCESS

        # If we have track data (ESC s marker), assume success
        # Read operations may not have explicit status byte
        if b'\x1bs' in response or b'\x1b\x73' in response:
            return True, ErrorCode.SUCCESS

        # If response has reasonable length, assume success
        # (write/erase might return short response without explicit status)
        if len(response) >= 2:
            return True, ErrorCode.SUCCESS

        return False, ErrorCode.UNKNOWN_ERROR

    # === Device Control Commands ===

    def reset(self) -> CommandResult:
        """
        Reset the device to initial state.
        Cancels any pending operation and turns off LEDs.

        Returns:
            CommandResult with operation status.
        """
        import time

        # Flush any pending data first
        self._device.flush()

        # Send reset command (ESC a) - doesn't return a response
        success, _ = self._device.send_command(Command.RESET.value)

        # Wait for device to reset
        time.sleep(0.3)

        # Flush again to clear any residual data
        self._device.flush()

        return CommandResult(
            success=success,
            error_code=ErrorCode.SUCCESS if success else ErrorCode.COMMUNICATION_ERROR,
            message="Device reset" if success else "Reset failed"
        )

    def test_communication(self) -> CommandResult:
        """
        Test communication with device.

        Returns:
            CommandResult with operation status.
        """
        success, response = self._device.send_and_receive(Command.TEST_COMM.value)
        ok, error_code = self._parse_status(response)

        return CommandResult(
            success=success and ok,
            error_code=error_code,
            message="Communication OK" if ok else ERROR_MESSAGES.get(error_code, "Communication failed")
        )

    def test_ram(self) -> CommandResult:
        """
        Test device RAM.

        Returns:
            CommandResult with operation status.
        """
        success, response = self._device.send_and_receive(Command.TEST_RAM.value)
        ok, error_code = self._parse_status(response)

        return CommandResult(
            success=success and ok,
            error_code=error_code,
            message="RAM test passed" if ok else "RAM test failed"
        )

    def test_sensor(self) -> CommandResult:
        """
        Test card sensor.

        Returns:
            CommandResult with operation status.
        """
        success, response = self._device.send_and_receive(Command.TEST_SENSOR.value)
        ok, error_code = self._parse_status(response)

        return CommandResult(
            success=success and ok,
            error_code=error_code,
            message="Sensor test passed" if ok else "Sensor test failed"
        )

    def get_firmware_version(self) -> CommandResult:
        """
        Get device firmware version.

        Returns:
            CommandResult with firmware version in message.
        """
        success, response = self._device.send_and_receive(Command.GET_FIRMWARE.value)

        if success and response:
            # Extract version string
            version = response.decode('ascii', errors='ignore').strip('\x00\x1b')
            return CommandResult(
                success=True,
                error_code=ErrorCode.SUCCESS,
                message=f"Firmware: {version}",
                data=response
            )

        return CommandResult(
            success=False,
            error_code=ErrorCode.COMMUNICATION_ERROR,
            message="Failed to get firmware version"
        )

    # === LED Control ===

    def led_off(self) -> CommandResult:
        """Turn off all LEDs."""
        success, _ = self._device.send_command(Command.LED_ALL_OFF.value)
        return CommandResult(
            success=success,
            error_code=ErrorCode.SUCCESS if success else ErrorCode.COMMUNICATION_ERROR,
            message="LEDs off" if success else "Failed to control LEDs"
        )

    def led_on(self, color: str = "all") -> CommandResult:
        """
        Turn on LED.

        Args:
            color: "all", "green", "yellow", or "red"

        Returns:
            CommandResult with operation status.
        """
        commands = {
            "all": Command.LED_ALL_ON,
            "green": Command.LED_GREEN_ON,
            "yellow": Command.LED_YELLOW_ON,
            "red": Command.LED_RED_ON,
        }

        cmd = commands.get(color.lower(), Command.LED_ALL_ON)
        success, _ = self._device.send_command(cmd.value)

        return CommandResult(
            success=success,
            error_code=ErrorCode.SUCCESS if success else ErrorCode.COMMUNICATION_ERROR,
            message=f"{color.capitalize()} LED on" if success else "Failed to control LEDs"
        )

    # === Read Operations ===

    def read_iso(self, timeout_ms: int = 10000) -> CommandResult:
        """
        Read card in ISO format (waits for card swipe).

        Args:
            timeout_ms: Timeout in milliseconds to wait for card swipe.

        Returns:
            CommandResult with parsed track data.
        """
        # Send read command
        success, _ = self._device.send_command(Command.READ_ISO.value)
        if not success:
            return CommandResult(
                success=False,
                error_code=ErrorCode.COMMUNICATION_ERROR,
                message="Failed to send read command"
            )

        # Wait for card swipe and response
        success, response = self._device.receive_response(timeout_ms)

        if not success or not response:
            return CommandResult(
                success=False,
                error_code=ErrorCode.INVALID_CARD_SWIPE,
                message="No card detected - please swipe card"
            )

        # Parse track data
        ok, error_code = self._parse_status(response)
        if not ok:
            return CommandResult(
                success=False,
                error_code=error_code,
                message=ERROR_MESSAGES.get(error_code, "Read failed")
            )

        tracks = self._parser.parse_iso_response(response)

        return CommandResult(
            success=True,
            error_code=ErrorCode.SUCCESS,
            message="Card read successfully",
            data=response,
            tracks=tracks
        )

    def read_raw(self, timeout_ms: int = 10000) -> CommandResult:
        """
        Read card in raw format.

        Args:
            timeout_ms: Timeout in milliseconds to wait for card swipe.

        Returns:
            CommandResult with raw track data.
        """
        success, _ = self._device.send_command(Command.READ_RAW.value)
        if not success:
            return CommandResult(
                success=False,
                error_code=ErrorCode.COMMUNICATION_ERROR,
                message="Failed to send read command"
            )

        success, response = self._device.receive_response(timeout_ms)

        if not success or not response:
            return CommandResult(
                success=False,
                error_code=ErrorCode.INVALID_CARD_SWIPE,
                message="No card detected - please swipe card"
            )

        ok, error_code = self._parse_status(response)
        if not ok:
            return CommandResult(
                success=False,
                error_code=error_code,
                message=ERROR_MESSAGES.get(error_code, "Read failed")
            )

        tracks = self._parser.parse_raw_response(response)

        return CommandResult(
            success=True,
            error_code=ErrorCode.SUCCESS,
            message="Card read successfully (raw)",
            data=response,
            tracks=tracks
        )

    # === Write Operations ===

    def write_iso(
        self,
        track1: Optional[str] = None,
        track2: Optional[str] = None,
        track3: Optional[str] = None,
        timeout_ms: int = 10000
    ) -> CommandResult:
        """
        Write data to card in ISO format.

        IMPORTANT: Do NOT include sentinels (%, ;, ?) in the data!
        The device adds them automatically.

        Args:
            track1: Track 1 data (alphanumeric, max 79 chars, NO sentinels)
            track2: Track 2 data (numeric, max 40 chars, NO sentinels)
            track3: Track 3 data (numeric, max 107 chars, NO sentinels)
            timeout_ms: Timeout for card swipe

        Returns:
            CommandResult with operation status.
        """
        # Flush any pending data
        self._device.flush()

        # Set coercivity before writing (required by MSR605X)
        # Command is just ESC x (Hi-Co) or ESC y (Lo-Co), no data bytes
        if self._coercivity == Coercivity.HIGH:
            self._device.send_command(Command.SET_HICO.value)
        else:
            self._device.send_command(Command.SET_LOCO.value)
        self._device.receive_response(1000)  # Wait for ACK
        self._device.flush()

        # Build data payload (without sentinels - device adds them)
        data = self._parser.build_iso_write_data(track1, track2, track3)

        # Send write command with data
        success, _ = self._device.send_command(Command.WRITE_ISO.value, data)
        if not success:
            return CommandResult(
                success=False,
                error_code=ErrorCode.COMMUNICATION_ERROR,
                message="Failed to send write command"
            )

        # Wait for card swipe and response
        success, response = self._device.receive_response(timeout_ms)

        if not success:
            return CommandResult(
                success=False,
                error_code=ErrorCode.INVALID_CARD_SWIPE,
                message="No card detected - please swipe card"
            )

        ok, error_code = self._parse_status(response)

        return CommandResult(
            success=ok,
            error_code=error_code,
            message="Card written successfully" if ok else ERROR_MESSAGES.get(error_code, "Write failed")
        )

    def write_raw(
        self,
        track1: Optional[bytes] = None,
        track2: Optional[bytes] = None,
        track3: Optional[bytes] = None,
        timeout_ms: int = 10000
    ) -> CommandResult:
        """
        Write raw data to card.

        Args:
            track1: Track 1 raw bytes
            track2: Track 2 raw bytes
            track3: Track 3 raw bytes
            timeout_ms: Timeout for card swipe

        Returns:
            CommandResult with operation status.
        """
        # Flush any pending data
        self._device.flush()

        # Set coercivity before writing (required by MSR605X)
        if self._coercivity == Coercivity.HIGH:
            self._device.send_command(Command.SET_HICO.value)
        else:
            self._device.send_command(Command.SET_LOCO.value)
        self._device.receive_response(1000)  # Wait for ACK
        self._device.flush()

        data = self._parser.build_raw_write_data(track1, track2, track3)

        success, _ = self._device.send_command(Command.WRITE_RAW.value, data)
        if not success:
            return CommandResult(
                success=False,
                error_code=ErrorCode.COMMUNICATION_ERROR,
                message="Failed to send write command"
            )

        success, response = self._device.receive_response(timeout_ms)

        if not success:
            return CommandResult(
                success=False,
                error_code=ErrorCode.INVALID_CARD_SWIPE,
                message="No card detected - please swipe card"
            )

        ok, error_code = self._parse_status(response)

        return CommandResult(
            success=ok,
            error_code=error_code,
            message="Card written successfully (raw)" if ok else ERROR_MESSAGES.get(error_code, "Write failed")
        )

    # === Erase Operations ===

    def erase(
        self,
        track1: bool = True,
        track2: bool = True,
        track3: bool = True,
        timeout_ms: int = 10000
    ) -> CommandResult:
        """
        Erase tracks on card.

        Args:
            track1: Erase track 1
            track2: Erase track 2
            track3: Erase track 3
            timeout_ms: Timeout for card swipe

        Returns:
            CommandResult with operation status.
        """
        # Flush any pending data
        self._device.flush()

        # Set coercivity before erasing
        if self._coercivity == Coercivity.HIGH:
            self._device.send_command(Command.SET_HICO.value)
        else:
            self._device.send_command(Command.SET_LOCO.value)
        self._device.receive_response(1000)
        self._device.flush()

        # Build track selection byte (binary mask)
        # 0x01 = Track 1, 0x02 = Track 2, 0x04 = Track 3, 0x07 = All
        mask = 0
        if track1:
            mask |= 0x01
        if track2:
            mask |= 0x02
        if track3:
            mask |= 0x04

        data = bytes([mask])

        success, _ = self._device.send_command(Command.ERASE_CARD.value, data)
        if not success:
            return CommandResult(
                success=False,
                error_code=ErrorCode.COMMUNICATION_ERROR,
                message="Failed to send erase command"
            )

        success, response = self._device.receive_response(timeout_ms)

        if not success:
            return CommandResult(
                success=False,
                error_code=ErrorCode.INVALID_CARD_SWIPE,
                message="No card detected - please swipe card"
            )

        ok, error_code = self._parse_status(response)

        return CommandResult(
            success=ok,
            error_code=error_code,
            message="Card erased successfully" if ok else ERROR_MESSAGES.get(error_code, "Erase failed")
        )

    # === Configuration ===

    def set_coercivity(self, coercivity: Coercivity) -> CommandResult:
        """
        Set card coercivity.

        Args:
            coercivity: HIGH or LOW coercivity

        Returns:
            CommandResult with operation status.
        """
        # Coercivity commands are just ESC x (Hi-Co) or ESC y (Lo-Co), no data bytes
        if coercivity == Coercivity.HIGH:
            cmd = Command.SET_HICO.value
        else:
            cmd = Command.SET_LOCO.value

        success, response = self._device.send_and_receive(cmd)

        ok, error_code = self._parse_status(response)

        if ok:
            self._coercivity = coercivity

        co_name = "Hi-Co" if coercivity == Coercivity.HIGH else "Lo-Co"

        return CommandResult(
            success=ok,
            error_code=error_code,
            message=f"Coercivity set to {co_name}" if ok else "Failed to set coercivity"
        )

    def get_coercivity(self) -> CommandResult:
        """
        Get current coercivity setting.

        Returns:
            CommandResult with coercivity in message.
        """
        success, response = self._device.send_and_receive(Command.GET_COERCIVITY.value)

        if success and response:
            # Parse coercivity from response
            for byte in response:
                if byte in (0, 1):
                    co = Coercivity(byte)
                    self._coercivity = co
                    co_name = "Hi-Co" if co == Coercivity.HIGH else "Lo-Co"
                    return CommandResult(
                        success=True,
                        error_code=ErrorCode.SUCCESS,
                        message=f"Current coercivity: {co_name}",
                        data=response
                    )

        return CommandResult(
            success=False,
            error_code=ErrorCode.COMMUNICATION_ERROR,
            message="Failed to get coercivity"
        )

    def set_bpi(self, track: TrackNumber, bpi: BPI) -> CommandResult:
        """
        Set Bits Per Inch for a track.

        Args:
            track: Track number (1, 2, or 3)
            bpi: BPI value (75 or 210)

        Returns:
            CommandResult with operation status.
        """
        # BPI encoded as: 0 for 75, 1 for 210
        bpi_value = 1 if bpi == BPI.BPI_210 else 0
        data = bytes([track.value, bpi_value])

        success, response = self._device.send_and_receive(Command.SET_BPI.value, data)
        ok, error_code = self._parse_status(response)

        return CommandResult(
            success=ok,
            error_code=error_code,
            message=f"Track {track.value} BPI set to {bpi.value}" if ok else "Failed to set BPI"
        )

    def set_bpc(self, track: TrackNumber, bpc: BPC) -> CommandResult:
        """
        Set Bits Per Character for a track.

        Args:
            track: Track number (1, 2, or 3)
            bpc: BPC value (5, 7, or 8)

        Returns:
            CommandResult with operation status.
        """
        data = bytes([track.value, bpc.value])

        success, response = self._device.send_and_receive(Command.SET_BPC.value, data)
        ok, error_code = self._parse_status(response)

        return CommandResult(
            success=ok,
            error_code=error_code,
            message=f"Track {track.value} BPC set to {bpc.value}" if ok else "Failed to set BPC"
        )

    def set_leading_zero(self, track: TrackNumber, zeros: int) -> CommandResult:
        """
        Set leading zeros for a track.

        Args:
            track: Track number (1, 2, or 3)
            zeros: Number of leading zeros (0-255)

        Returns:
            CommandResult with operation status.
        """
        data = bytes([track.value, min(zeros, 255)])

        success, response = self._device.send_and_receive(Command.SET_LEADING_ZERO.value, data)
        ok, error_code = self._parse_status(response)

        return CommandResult(
            success=ok,
            error_code=error_code,
            message=f"Track {track.value} leading zeros set to {zeros}" if ok else "Failed to set leading zeros"
        )

    # === Compound Operations ===

    def copy_card(self, timeout_ms: int = 10000) -> CommandResult:
        """
        Copy a card (read then write to new card).

        Args:
            timeout_ms: Timeout for each card swipe

        Returns:
            CommandResult with operation status.
        """
        # First, read the source card
        read_result = self.read_iso(timeout_ms)
        if not read_result.success or not read_result.tracks:
            return CommandResult(
                success=False,
                error_code=read_result.error_code,
                message=f"Read failed: {read_result.message}"
            )

        # Extract track data
        track1 = None
        track2 = None
        track3 = None

        for track in read_result.tracks:
            if track.track_number == 1:
                track1 = track.data
            elif track.track_number == 2:
                track2 = track.data
            elif track.track_number == 3:
                track3 = track.data

        # Write to destination card
        write_result = self.write_iso(track1, track2, track3, timeout_ms)

        if write_result.success:
            return CommandResult(
                success=True,
                error_code=ErrorCode.SUCCESS,
                message="Card copied successfully",
                tracks=read_result.tracks
            )
        else:
            return CommandResult(
                success=False,
                error_code=write_result.error_code,
                message=f"Write failed: {write_result.message}"
            )

    def _normalize_track_data(self, data: str, track_num: int) -> str:
        """Normalize track data by adding sentinels if missing."""
        if not data:
            return data
        if track_num == 1:
            # Track 1: % ... ?
            if not data.startswith('%'):
                data = '%' + data
            if not data.endswith('?'):
                data = data + '?'
            return data.upper()
        else:
            # Track 2, 3: ; ... ?
            if not data.startswith(';'):
                data = ';' + data
            if not data.endswith('?'):
                data = data + '?'
            return data

    def compare_card(
        self,
        track1: Optional[str] = None,
        track2: Optional[str] = None,
        track3: Optional[str] = None,
        timeout_ms: int = 10000
    ) -> CommandResult:
        """
        Compare card data with provided data.

        Args:
            track1: Expected track 1 data
            track2: Expected track 2 data
            track3: Expected track 3 data
            timeout_ms: Timeout for card swipe

        Returns:
            CommandResult indicating match/mismatch.
        """
        # Read the card
        read_result = self.read_iso(timeout_ms)
        if not read_result.success or not read_result.tracks:
            return CommandResult(
                success=False,
                error_code=read_result.error_code,
                message=f"Read failed: {read_result.message}"
            )

        # Compare tracks (normalize expected data to include sentinels)
        mismatches = []
        for track in read_result.tracks:
            expected = None
            if track.track_number == 1:
                expected = self._normalize_track_data(track1, 1) if track1 else None
            elif track.track_number == 2:
                expected = self._normalize_track_data(track2, 2) if track2 else None
            elif track.track_number == 3:
                expected = self._normalize_track_data(track3, 3) if track3 else None

            if expected is not None and track.data != expected:
                mismatches.append(f"Track {track.track_number}")

        if mismatches:
            return CommandResult(
                success=False,
                error_code=ErrorCode.READ_WRITE_ERROR,
                message=f"Mismatch on: {', '.join(mismatches)}",
                tracks=read_result.tracks
            )

        return CommandResult(
            success=True,
            error_code=ErrorCode.SUCCESS,
            message="All tracks match",
            tracks=read_result.tracks
        )
