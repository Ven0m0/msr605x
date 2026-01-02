"""Read Panel - UI for reading magnetic stripe cards."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from typing import Callable, Optional
from threading import Thread

from ..msr605x.commands import MSR605XCommands
from ..msr605x.parser import TrackData
from ..msr605x.constants import DataFormat
from ..utils.file_io import FileManager


class ReadPanel(Gtk.Box):
    """Panel for reading card data."""

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
        self.current_tracks: list[TrackData] = []

        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)

        self._build_ui()

    def _build_ui(self):
        """Build the panel UI."""
        # Title
        title = Gtk.Label(label="Read Card")
        title.add_css_class("panel-title")
        title.set_xalign(0)
        self.append(title)

        # Description
        desc = Gtk.Label(
            label="Click 'Read' and swipe a card to read its magnetic stripe data."
        )
        desc.set_xalign(0)
        desc.set_wrap(True)
        desc.add_css_class("dim-label")
        self.append(desc)

        # Format selection
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        format_box.set_margin_top(12)

        format_label = Gtk.Label(label="Read Format:")
        format_box.append(format_label)

        self.format_combo = Gtk.ComboBoxText()
        self.format_combo.append("iso", "ISO (Standard)")
        self.format_combo.append("raw", "Raw Data")
        self.format_combo.set_active_id("iso")
        format_box.append(self.format_combo)

        self.append(format_box)

        # Read button
        self.read_btn = Gtk.Button(label="Read Card")
        self.read_btn.add_css_class("suggested-action")
        self.read_btn.add_css_class("action-button")
        self.read_btn.set_margin_top(12)
        self.read_btn.connect("clicked", self._on_read_clicked)
        self.append(self.read_btn)

        # Status
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_xalign(0)
        self.status_label.set_margin_top(8)
        self.append(self.status_label)

        # Spinner for loading state
        self.spinner = Gtk.Spinner()
        self.spinner.set_visible(False)
        self.append(self.spinner)

        # Track data display
        tracks_frame = Gtk.Frame()
        tracks_frame.set_label("Track Data")
        tracks_frame.set_margin_top(16)

        tracks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        tracks_box.set_margin_top(12)
        tracks_box.set_margin_bottom(12)
        tracks_box.set_margin_start(12)
        tracks_box.set_margin_end(12)

        # Track 1
        track1_box = self._create_track_display("Track 1", "alphanumeric")
        self.track1_entry = track1_box.get_first_child().get_next_sibling()
        tracks_box.append(track1_box)

        # Track 2
        track2_box = self._create_track_display("Track 2", "numeric")
        self.track2_entry = track2_box.get_first_child().get_next_sibling()
        tracks_box.append(track2_box)

        # Track 3
        track3_box = self._create_track_display("Track 3", "numeric")
        self.track3_entry = track3_box.get_first_child().get_next_sibling()
        tracks_box.append(track3_box)

        tracks_frame.set_child(tracks_box)
        self.append(tracks_frame)

        # Action buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        action_box.set_margin_top(12)
        action_box.set_halign(Gtk.Align.END)

        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", self._on_clear_clicked)
        action_box.append(clear_btn)

        copy_btn = Gtk.Button(label="Copy to Clipboard")
        copy_btn.connect("clicked", self._on_copy_clicked)
        action_box.append(copy_btn)

        save_btn = Gtk.Button(label="Save to File")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save_clicked)
        action_box.append(save_btn)

        self.append(action_box)

    def _create_track_display(self, label: str, description: str) -> Gtk.Box:
        """Create a track data display widget."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        # Label with description
        label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        track_label = Gtk.Label(label=label)
        track_label.add_css_class("track-label")
        track_label.set_xalign(0)
        label_box.append(track_label)

        desc_label = Gtk.Label(label=f"({description})")
        desc_label.add_css_class("dim-label")
        label_box.append(desc_label)

        box.append(label_box)

        # Entry for data
        entry = Gtk.Entry()
        entry.set_editable(False)
        entry.add_css_class("track-entry")
        entry.set_placeholder_text("No data")
        box.append(entry)

        return box

    def _on_read_clicked(self, button):
        """Handle read button click."""
        self._set_reading_state(True)
        self._clear_tracks()
        self.status_label.set_text("Waiting for card swipe...")

        format_id = self.format_combo.get_active_id()

        def do_read():
            if format_id == "raw":
                result = self.commands.read_raw(timeout_ms=15000)
            else:
                result = self.commands.read_iso(timeout_ms=15000)

            GLib.idle_add(self._on_read_complete, result)

        thread = Thread(target=do_read, daemon=True)
        thread.start()

    def _on_read_complete(self, result):
        """Handle read operation result."""
        self._set_reading_state(False)

        # Reset device to idle state (turn off LEDs, cancel any pending operation)
        self.commands.reset()

        if result.success and result.tracks:
            self.current_tracks = result.tracks
            self._display_tracks(result.tracks)
            self.status_label.set_text("Card read successfully")
            self.show_toast("Card read successfully", False)
        else:
            self.status_label.set_text(f"Read failed: {result.message}")
            self.show_toast(result.message, True)

    def _set_reading_state(self, reading: bool):
        """Set UI state during reading."""
        self.read_btn.set_sensitive(not reading)
        self.spinner.set_visible(reading)
        if reading:
            self.spinner.start()
        else:
            self.spinner.stop()

    def _display_tracks(self, tracks: list[TrackData]):
        """Display track data in the UI."""
        entries = {
            1: self.track1_entry,
            2: self.track2_entry,
            3: self.track3_entry,
        }

        for track in tracks:
            entry = entries.get(track.track_number)
            if entry:
                entry.set_text(track.data)

                # Set style based on validity
                entry.remove_css_class("success")
                entry.remove_css_class("error")
                if track.is_valid:
                    entry.add_css_class("success")
                else:
                    entry.add_css_class("error")

    def _clear_tracks(self):
        """Clear track display."""
        self.track1_entry.set_text("")
        self.track2_entry.set_text("")
        self.track3_entry.set_text("")
        self.current_tracks = []

    def _on_clear_clicked(self, button):
        """Handle clear button click."""
        self._clear_tracks()
        self.status_label.set_text("Ready")

    def _on_copy_clicked(self, button):
        """Copy track data to clipboard."""
        if not self.current_tracks:
            self.show_toast("No data to copy", True)
            return

        text_lines = []
        for track in self.current_tracks:
            text_lines.append(f"Track {track.track_number}: {track.data}")

        text = "\n".join(text_lines)

        clipboard = self.get_clipboard()
        clipboard.set(text)
        self.show_toast("Copied to clipboard", False)

    def _on_save_clicked(self, button):
        """Save track data to file."""
        if not self.current_tracks:
            self.show_toast("No data to save", True)
            return

        dialog = Gtk.FileChooserNative.new(
            "Save Card Data",
            self.get_root(),
            Gtk.FileChooserAction.SAVE,
            "_Save",
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

        dialog.set_current_name("card_data.json")
        dialog.connect("response", self._on_save_response)
        dialog.show()

    def _on_save_response(self, dialog, response):
        """Handle save dialog response."""
        if response == Gtk.ResponseType.ACCEPT:
            filepath = dialog.get_file().get_path()

            from pathlib import Path
            success, message = self.file_manager.save_tracks(
                Path(filepath),
                self.current_tracks
            )

            if success:
                self.show_toast(message, False)
            else:
                self.show_toast(message, True)
