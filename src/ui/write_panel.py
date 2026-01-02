"""Write Panel - UI for writing magnetic stripe cards."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from typing import Callable, Optional
from threading import Thread
from pathlib import Path

from ..msr605x.commands import MSR605XCommands
from ..msr605x.parser import TrackData
from ..msr605x.constants import DataFormat, TrackSpec
from ..utils.file_io import FileManager


class WritePanel(Gtk.Box):
    """Panel for writing card data."""

    def __init__(
        self,
        commands: MSR605XCommands,
        show_toast: Callable[[str, bool], None],
        file_manager: FileManager
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.commands = commands
        self.show_toast = show_toast
        self.file_manager = file_manager

        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)

        self._build_ui()

    def _build_ui(self):
        """Build the panel UI."""
        # Title
        title = Gtk.Label(label="Write Card")
        title.add_css_class("panel-title")
        title.set_xalign(0)
        self.append(title)

        # Description
        desc = Gtk.Label(
            label="Enter data for each track, then click 'Write' and swipe a blank card."
        )
        desc.set_xalign(0)
        desc.set_wrap(True)
        desc.add_css_class("dim-label")
        self.append(desc)

        # Format selection
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        format_box.set_margin_top(12)

        format_label = Gtk.Label(label="Write Format:")
        format_box.append(format_label)

        self.format_combo = Gtk.ComboBoxText()
        self.format_combo.append("iso", "ISO (Standard)")
        self.format_combo.append("raw", "Raw Data (Hex)")
        self.format_combo.set_active_id("iso")
        self.format_combo.connect("changed", self._on_format_changed)
        format_box.append(self.format_combo)

        self.append(format_box)

        # Track inputs
        tracks_frame = Gtk.Frame()
        tracks_frame.set_label("Track Data")
        tracks_frame.set_margin_top(12)

        tracks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        tracks_box.set_margin_top(12)
        tracks_box.set_margin_bottom(12)
        tracks_box.set_margin_start(12)
        tracks_box.set_margin_end(12)

        # Track 1
        self.track1_box = self._create_track_input(
            "Track 1",
            f"Alphanumeric, max {TrackSpec.TRACK_1['max_chars']} chars",
            TrackSpec.TRACK_1['max_chars']
        )
        self.track1_entry = self._get_entry_from_box(self.track1_box)
        self.track1_check = self._get_check_from_box(self.track1_box)
        tracks_box.append(self.track1_box)

        # Track 2
        self.track2_box = self._create_track_input(
            "Track 2",
            f"Numeric, max {TrackSpec.TRACK_2['max_chars']} chars",
            TrackSpec.TRACK_2['max_chars']
        )
        self.track2_entry = self._get_entry_from_box(self.track2_box)
        self.track2_check = self._get_check_from_box(self.track2_box)
        tracks_box.append(self.track2_box)

        # Track 3
        self.track3_box = self._create_track_input(
            "Track 3",
            f"Numeric, max {TrackSpec.TRACK_3['max_chars']} chars",
            TrackSpec.TRACK_3['max_chars']
        )
        self.track3_entry = self._get_entry_from_box(self.track3_box)
        self.track3_check = self._get_check_from_box(self.track3_box)
        tracks_box.append(self.track3_box)

        tracks_frame.set_child(tracks_box)
        self.append(tracks_frame)

        # Options
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        options_box.set_margin_top(12)

        self.verify_check = Gtk.CheckButton(label="Verify after write")
        self.verify_check.set_active(True)
        options_box.append(self.verify_check)

        self.append(options_box)

        # Status
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_xalign(0)
        self.status_label.set_margin_top(8)
        self.append(self.status_label)

        # Spinner
        self.spinner = Gtk.Spinner()
        self.spinner.set_visible(False)
        self.append(self.spinner)

        # Action buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        action_box.set_margin_top(12)

        load_btn = Gtk.Button(label="Load from File")
        load_btn.connect("clicked", self._on_load_clicked)
        action_box.append(load_btn)

        clear_btn = Gtk.Button(label="Clear All")
        clear_btn.connect("clicked", self._on_clear_clicked)
        action_box.append(clear_btn)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        action_box.append(spacer)

        self.write_btn = Gtk.Button(label="Write Card")
        self.write_btn.add_css_class("suggested-action")
        self.write_btn.add_css_class("action-button")
        self.write_btn.connect("clicked", self._on_write_clicked)
        action_box.append(self.write_btn)

        self.batch_btn = Gtk.Button(label="Batch Write...")
        self.batch_btn.add_css_class("action-button")
        self.batch_btn.connect("clicked", self._on_batch_write_clicked)
        action_box.append(self.batch_btn)

        self.append(action_box)

    def _create_track_input(self, label: str, description: str, max_length: int) -> Gtk.Box:
        """Create a track input widget."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        # Header with checkbox
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        check = Gtk.CheckButton()
        check.set_active(True)
        header_box.append(check)

        track_label = Gtk.Label(label=label)
        track_label.add_css_class("track-label")
        track_label.set_xalign(0)
        header_box.append(track_label)

        desc_label = Gtk.Label(label=f"({description})")
        desc_label.add_css_class("dim-label")
        header_box.append(desc_label)

        box.append(header_box)

        # Entry
        entry = Gtk.Entry()
        entry.set_max_length(max_length)
        entry.add_css_class("track-entry")
        entry.set_placeholder_text("Enter data...")
        entry.connect("changed", self._on_entry_changed)
        box.append(entry)

        # Character count
        count_label = Gtk.Label(label=f"0/{max_length}")
        count_label.set_xalign(1)
        count_label.add_css_class("dim-label")
        entry.count_label = count_label
        entry.max_length = max_length
        box.append(count_label)

        return box

    def _get_entry_from_box(self, box: Gtk.Box) -> Gtk.Entry:
        """Get entry widget from track box."""
        child = box.get_first_child()
        while child:
            if isinstance(child, Gtk.Entry):
                return child
            child = child.get_next_sibling()
        return None

    def _get_check_from_box(self, box: Gtk.Box) -> Gtk.CheckButton:
        """Get checkbox widget from track box."""
        header = box.get_first_child()
        if header:
            child = header.get_first_child()
            if isinstance(child, Gtk.CheckButton):
                return child
        return None

    def _on_entry_changed(self, entry):
        """Update character count on entry change."""
        if hasattr(entry, 'count_label'):
            length = len(entry.get_text())
            entry.count_label.set_text(f"{length}/{entry.max_length}")

    def _on_format_changed(self, combo):
        """Handle format selection change."""
        format_id = combo.get_active_id()
        if format_id == "raw":
            self.track1_entry.set_placeholder_text("Enter hex data (e.g., 1A2B3C)...")
            self.track2_entry.set_placeholder_text("Enter hex data...")
            self.track3_entry.set_placeholder_text("Enter hex data...")
        else:
            self.track1_entry.set_placeholder_text("Enter data...")
            self.track2_entry.set_placeholder_text("Enter data...")
            self.track3_entry.set_placeholder_text("Enter data...")

    def _on_write_clicked(self, button):
        """Handle write button click."""
        # Get track data
        track1 = self.track1_entry.get_text() if self.track1_check.get_active() else None
        track2 = self.track2_entry.get_text() if self.track2_check.get_active() else None
        track3 = self.track3_entry.get_text() if self.track3_check.get_active() else None

        if not any([track1, track2, track3]):
            self.show_toast("Please enter data for at least one track", True)
            return

        self._set_writing_state(True)
        self.status_label.set_text("Waiting for card swipe...")

        format_id = self.format_combo.get_active_id()
        verify = self.verify_check.get_active()

        def do_write():
            if format_id == "raw":
                # Convert hex strings to bytes
                try:
                    t1 = bytes.fromhex(track1) if track1 else None
                    t2 = bytes.fromhex(track2) if track2 else None
                    t3 = bytes.fromhex(track3) if track3 else None
                    result = self.commands.write_raw(t1, t2, t3, timeout_ms=15000)
                except ValueError as e:
                    from ..msr605x.commands import CommandResult
                    from ..msr605x.constants import ErrorCode
                    result = CommandResult(
                        success=False,
                        error_code=ErrorCode.COMMAND_FORMAT_ERROR,
                        message=f"Invalid hex data: {e}"
                    )
            else:
                result = self.commands.write_iso(track1, track2, track3, timeout_ms=15000)

            # Verify if requested
            if result.success and verify:
                GLib.idle_add(lambda: self.status_label.set_text("Verifying... swipe card again"))
                verify_result = self.commands.compare_card(track1, track2, track3, timeout_ms=15000)
                GLib.idle_add(self._on_write_complete, result, verify_result)
            else:
                GLib.idle_add(self._on_write_complete, result, None)

        thread = Thread(target=do_write, daemon=True)
        thread.start()

    def _on_write_complete(self, write_result, verify_result=None):
        """Handle write operation result."""
        self._set_writing_state(False)

        # Reset device to idle state (turn off LEDs, cancel any pending operation)
        self.commands.reset()

        if write_result.success:
            if verify_result:
                if verify_result.success:
                    self.status_label.set_text("Write and verify successful")
                    self.show_toast("Card written and verified", False)
                else:
                    self.status_label.set_text(f"Verify failed: {verify_result.message}")
                    self.show_toast(f"Write OK, verify failed: {verify_result.message}", True)
            else:
                self.status_label.set_text("Card written successfully")
                self.show_toast("Card written successfully", False)
        else:
            self.status_label.set_text(f"Write failed: {write_result.message}")
            self.show_toast(write_result.message, True)

    def _set_writing_state(self, writing: bool):
        """Set UI state during writing."""
        self.write_btn.set_sensitive(not writing)
        self.spinner.set_visible(writing)
        if writing:
            self.spinner.start()
        else:
            self.spinner.stop()

    def _on_clear_clicked(self, button):
        """Clear all track inputs."""
        self.track1_entry.set_text("")
        self.track2_entry.set_text("")
        self.track3_entry.set_text("")
        self.status_label.set_text("Ready")

    def _on_load_clicked(self, button):
        """Load track data from file."""
        dialog = Gtk.FileChooserNative.new(
            "Load Card Data",
            self.get_root(),
            Gtk.FileChooserAction.OPEN,
            "_Open",
            "_Cancel"
        )

        # Add file filters
        json_filter = Gtk.FileFilter()
        json_filter.set_name("JSON files")
        json_filter.add_pattern("*.json")
        dialog.add_filter(json_filter)

        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        dialog.add_filter(csv_filter)

        all_filter = Gtk.FileFilter()
        all_filter.set_name("All supported files")
        all_filter.add_pattern("*.json")
        all_filter.add_pattern("*.csv")
        dialog.add_filter(all_filter)

        dialog.connect("response", self._on_load_response)
        dialog.show()

    def _on_load_response(self, dialog, response):
        """Handle load dialog response."""
        if response == Gtk.ResponseType.ACCEPT:
            filepath = Path(dialog.get_file().get_path())

            success, message, tracks = self.file_manager.load_tracks(filepath)

            if success:
                self._populate_from_tracks(tracks)
                self.show_toast(message, False)
            else:
                self.show_toast(message, True)

    def _populate_from_tracks(self, tracks: list[TrackData]):
        """Populate entries from loaded tracks."""
        entries = {
            1: self.track1_entry,
            2: self.track2_entry,
            3: self.track3_entry,
        }

        for track in tracks:
            entry = entries.get(track.track_number)
            if entry:
                entry.set_text(track.data)

    def set_track_data(self, track1: str = "", track2: str = "", track3: str = ""):
        """Set track data programmatically."""
        self.track1_entry.set_text(track1)
        self.track2_entry.set_text(track2)
        self.track3_entry.set_text(track3)

    def _on_batch_write_clicked(self, button):
        """Open batch write dialog."""
        # Get track data
        track1 = self.track1_entry.get_text() if self.track1_check.get_active() else None
        track2 = self.track2_entry.get_text() if self.track2_check.get_active() else None
        track3 = self.track3_entry.get_text() if self.track3_check.get_active() else None

        if not any([track1, track2, track3]):
            self.show_toast("Please enter data for at least one track", True)
            return

        dialog = BatchWriteDialog(
            self.get_root(),
            self.commands,
            track1, track2, track3,
            self.format_combo.get_active_id()
        )
        dialog.present()


class BatchWriteDialog(Adw.Window):
    """Dialog for batch writing multiple cards."""

    def __init__(self, parent, commands, track1, track2, track3, format_id):
        super().__init__()

        self.commands = commands
        self.track1 = track1
        self.track2 = track2
        self.track3 = track3
        self.format_id = format_id
        self.cards_written = 0
        self.is_running = False
        self.has_error = False

        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title("Batch Write")
        self.set_default_size(400, 300)

        self._build_ui()

    def _build_ui(self):
        """Build dialog UI."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(24)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        self.set_content(main_box)

        # Title
        title = Gtk.Label(label="Batch Write Mode")
        title.add_css_class("title-1")
        main_box.append(title)

        # Counter display
        counter_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        counter_box.set_margin_top(24)

        self.counter_label = Gtk.Label(label="0")
        self.counter_label.add_css_class("title-1")
        self.counter_label.set_markup("<span size='xx-large' weight='bold'>0</span>")
        counter_box.append(self.counter_label)

        counter_desc = Gtk.Label(label="Cards Written Successfully")
        counter_desc.add_css_class("dim-label")
        counter_box.append(counter_desc)

        main_box.append(counter_box)

        # Status
        self.status_label = Gtk.Label(label="Click Start to begin writing cards")
        self.status_label.set_margin_top(16)
        self.status_label.set_wrap(True)
        main_box.append(self.status_label)

        # Spinner
        self.spinner = Gtk.Spinner()
        self.spinner.set_visible(False)
        main_box.append(self.spinner)

        # Error display
        self.error_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.error_box.set_visible(False)
        self.error_box.set_margin_top(16)

        error_icon = Gtk.Image.new_from_icon_name("dialog-error-symbolic")
        error_icon.set_icon_size(Gtk.IconSize.LARGE)
        self.error_box.append(error_icon)

        self.error_label = Gtk.Label()
        self.error_label.add_css_class("error")
        self.error_label.set_wrap(True)
        self.error_box.append(self.error_label)

        main_box.append(self.error_box)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        main_box.append(spacer)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.CENTER)

        self.start_btn = Gtk.Button(label="Start")
        self.start_btn.add_css_class("suggested-action")
        self.start_btn.add_css_class("pill")
        self.start_btn.connect("clicked", self._on_start_clicked)
        button_box.append(self.start_btn)

        self.stop_btn = Gtk.Button(label="Stop")
        self.stop_btn.add_css_class("destructive-action")
        self.stop_btn.add_css_class("pill")
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", self._on_stop_clicked)
        button_box.append(self.stop_btn)

        self.close_btn = Gtk.Button(label="Close")
        self.close_btn.add_css_class("pill")
        self.close_btn.connect("clicked", lambda b: self.close())
        button_box.append(self.close_btn)

        main_box.append(button_box)

    def _on_start_clicked(self, button):
        """Start batch writing."""
        self.is_running = True
        self.has_error = False
        self.error_box.set_visible(False)
        self.start_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.close_btn.set_sensitive(False)
        self.spinner.set_visible(True)
        self.spinner.start()

        self._write_next_card()

    def _on_stop_clicked(self, button):
        """Stop batch writing."""
        self.is_running = False
        self._update_stopped_state()

    def _update_stopped_state(self):
        """Update UI when stopped."""
        self.spinner.stop()
        self.spinner.set_visible(False)
        self.start_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self.close_btn.set_sensitive(True)

        # Reset device to idle state (turn off LEDs)
        self.commands.reset()

        if self.has_error:
            self.status_label.set_text(f"Stopped due to error after {self.cards_written} cards")
        else:
            self.status_label.set_text(f"Stopped. {self.cards_written} cards written.")

    def _write_next_card(self):
        """Write and verify next card."""
        if not self.is_running:
            return

        self.status_label.set_text("Swipe card to write...")

        def do_write():
            # Write card
            if self.format_id == "raw":
                try:
                    t1 = bytes.fromhex(self.track1) if self.track1 else None
                    t2 = bytes.fromhex(self.track2) if self.track2 else None
                    t3 = bytes.fromhex(self.track3) if self.track3 else None
                    result = self.commands.write_raw(t1, t2, t3, timeout_ms=30000)
                except ValueError as e:
                    from ..msr605x.commands import CommandResult
                    from ..msr605x.constants import ErrorCode
                    result = CommandResult(
                        success=False,
                        error_code=ErrorCode.COMMAND_FORMAT_ERROR,
                        message=f"Invalid hex: {e}"
                    )
            else:
                result = self.commands.write_iso(self.track1, self.track2, self.track3, timeout_ms=30000)

            if not result.success:
                GLib.idle_add(self._on_write_error, f"Write failed: {result.message}")
                return

            # Verify by reading back
            GLib.idle_add(lambda: self.status_label.set_text("Verifying... swipe again"))

            verify_result = self.commands.compare_card(self.track1, self.track2, self.track3, timeout_ms=30000)

            if verify_result.success:
                GLib.idle_add(self._on_card_success)
            else:
                GLib.idle_add(self._on_write_error, f"Verify failed: {verify_result.message}")

        thread = Thread(target=do_write, daemon=True)
        thread.start()

    def _on_card_success(self):
        """Handle successful write+verify."""
        self.cards_written += 1
        self.counter_label.set_markup(f"<span size='xx-large' weight='bold'>{self.cards_written}</span>")
        self.status_label.set_text("Card written successfully! Swipe next card...")

        if self.is_running:
            # Continue with next card
            self._write_next_card()

    def _on_write_error(self, message):
        """Handle write error - stop batch."""
        self.has_error = True
        self.is_running = False
        self.error_label.set_text(message)
        self.error_box.set_visible(True)
        self._update_stopped_state()
