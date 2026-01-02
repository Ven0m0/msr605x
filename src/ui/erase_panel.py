"""Erase Panel - UI for erasing magnetic stripe cards."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from typing import Callable
from threading import Thread

from ..msr605x.commands import MSR605XCommands


class ErasePanel(Gtk.Box):
    """Panel for erasing card data."""

    def __init__(
        self,
        commands: MSR605XCommands,
        show_toast: Callable[[str, bool], None]
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.commands = commands
        self.show_toast = show_toast

        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)

        self._build_ui()

    def _build_ui(self):
        """Build the panel UI."""
        # Title
        title = Gtk.Label(label="Erase Card")
        title.add_css_class("panel-title")
        title.set_xalign(0)
        self.append(title)

        # Warning
        warning_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        warning_box.add_css_class("warning")

        warning_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
        warning_box.append(warning_icon)

        warning_label = Gtk.Label(
            label="This operation will permanently erase data from the selected tracks."
        )
        warning_label.set_wrap(True)
        warning_box.append(warning_label)

        self.append(warning_box)

        # Track selection
        tracks_frame = Gtk.Frame()
        tracks_frame.set_label("Select Tracks to Erase")
        tracks_frame.set_margin_top(16)

        tracks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        tracks_box.set_margin_top(12)
        tracks_box.set_margin_bottom(12)
        tracks_box.set_margin_start(12)
        tracks_box.set_margin_end(12)

        # All tracks option
        self.all_tracks_check = Gtk.CheckButton(label="All Tracks")
        self.all_tracks_check.set_active(True)
        self.all_tracks_check.connect("toggled", self._on_all_toggled)
        tracks_box.append(self.all_tracks_check)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        tracks_box.append(separator)

        # Individual track options
        self.track1_check = Gtk.CheckButton(label="Track 1 (Alphanumeric)")
        self.track1_check.set_active(True)
        self.track1_check.set_sensitive(False)
        self.track1_check.connect("toggled", self._on_track_toggled)
        tracks_box.append(self.track1_check)

        self.track2_check = Gtk.CheckButton(label="Track 2 (Numeric)")
        self.track2_check.set_active(True)
        self.track2_check.set_sensitive(False)
        self.track2_check.connect("toggled", self._on_track_toggled)
        tracks_box.append(self.track2_check)

        self.track3_check = Gtk.CheckButton(label="Track 3 (Numeric)")
        self.track3_check.set_active(True)
        self.track3_check.set_sensitive(False)
        self.track3_check.connect("toggled", self._on_track_toggled)
        tracks_box.append(self.track3_check)

        tracks_frame.set_child(tracks_box)
        self.append(tracks_frame)

        # Status
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_xalign(0)
        self.status_label.set_margin_top(16)
        self.append(self.status_label)

        # Spinner
        self.spinner = Gtk.Spinner()
        self.spinner.set_visible(False)
        self.append(self.spinner)

        # Erase button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(24)

        self.erase_btn = Gtk.Button(label="Erase Card")
        self.erase_btn.add_css_class("destructive-action")
        self.erase_btn.add_css_class("action-button")
        self.erase_btn.set_size_request(200, -1)
        self.erase_btn.connect("clicked", self._on_erase_clicked)
        button_box.append(self.erase_btn)

        self.append(button_box)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        self.append(spacer)

        # Info section
        info_frame = Gtk.Frame()
        info_frame.set_label("Information")

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        info_box.set_margin_top(12)
        info_box.set_margin_bottom(12)
        info_box.set_margin_start(12)
        info_box.set_margin_end(12)

        info_items = [
            "Track 1: Contains alphanumeric data (name, account info)",
            "Track 2: Contains numeric data (card number, expiry)",
            "Track 3: Contains numeric data (varies by application)",
            "",
            "Erasing writes null data pattern to the selected tracks.",
        ]

        for item in info_items:
            if item:
                label = Gtk.Label(label=item)
                label.set_xalign(0)
                label.add_css_class("dim-label")
                info_box.append(label)

        info_frame.set_child(info_box)
        self.append(info_frame)

    def _on_all_toggled(self, button):
        """Handle 'All Tracks' toggle."""
        all_active = button.get_active()

        self.track1_check.set_sensitive(not all_active)
        self.track2_check.set_sensitive(not all_active)
        self.track3_check.set_sensitive(not all_active)

        if all_active:
            self.track1_check.set_active(True)
            self.track2_check.set_active(True)
            self.track3_check.set_active(True)

    def _on_track_toggled(self, button):
        """Handle individual track toggle."""
        # Update 'All Tracks' state
        all_checked = (
            self.track1_check.get_active() and
            self.track2_check.get_active() and
            self.track3_check.get_active()
        )

        # Prevent recursion
        self.all_tracks_check.handler_block_by_func(self._on_all_toggled)
        self.all_tracks_check.set_active(all_checked)
        self.all_tracks_check.handler_unblock_by_func(self._on_all_toggled)

    def _on_erase_clicked(self, button):
        """Handle erase button click."""
        # Get selected tracks
        track1 = self.track1_check.get_active()
        track2 = self.track2_check.get_active()
        track3 = self.track3_check.get_active()

        if not any([track1, track2, track3]):
            self.show_toast("Please select at least one track to erase", True)
            return

        # Confirm erase
        self._show_confirm_dialog(track1, track2, track3)

    def _show_confirm_dialog(self, track1: bool, track2: bool, track3: bool):
        """Show confirmation dialog before erasing."""
        tracks = []
        if track1:
            tracks.append("1")
        if track2:
            tracks.append("2")
        if track3:
            tracks.append("3")

        track_str = ", ".join(tracks)

        dialog = Adw.MessageDialog(
            transient_for=self.get_root(),
            heading="Confirm Erase",
            body=f"Are you sure you want to erase track(s) {track_str}?\n\nThis action cannot be undone."
        )

        dialog.add_response("cancel", "Cancel")
        dialog.add_response("erase", "Erase")
        dialog.set_response_appearance("erase", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")

        dialog.connect("response", self._on_confirm_response, track1, track2, track3)
        dialog.present()

    def _on_confirm_response(self, dialog, response, track1, track2, track3):
        """Handle confirmation dialog response."""
        if response == "erase":
            self._do_erase(track1, track2, track3)

    def _do_erase(self, track1: bool, track2: bool, track3: bool):
        """Perform the erase operation."""
        self._set_erasing_state(True)
        self.status_label.set_text("Waiting for card swipe...")

        def do_erase():
            result = self.commands.erase(track1, track2, track3, timeout_ms=15000)
            GLib.idle_add(self._on_erase_complete, result)

        thread = Thread(target=do_erase, daemon=True)
        thread.start()

    def _on_erase_complete(self, result):
        """Handle erase operation result."""
        self._set_erasing_state(False)

        # Reset device to idle state (turn off LEDs, cancel any pending operation)
        self.commands.reset()

        if result.success:
            self.status_label.set_text("Card erased successfully")
            self.show_toast("Card erased successfully", False)
        else:
            self.status_label.set_text(f"Erase failed: {result.message}")
            self.show_toast(result.message, True)

    def _set_erasing_state(self, erasing: bool):
        """Set UI state during erasing."""
        self.erase_btn.set_sensitive(not erasing)
        self.spinner.set_visible(erasing)
        if erasing:
            self.spinner.start()
        else:
            self.spinner.stop()
