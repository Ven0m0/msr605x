"""MSR605X Main Window."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio
from typing import Optional
from threading import Thread

from .msr605x import MSR605XDevice, MSR605XCommands
from .msr605x.constants import Coercivity, ErrorCode
from .ui import ReadPanel, WritePanel, ErasePanel, SettingsPanel
from .utils.file_io import FileManager


class MSR605XWindow(Adw.ApplicationWindow):
    """Main application window."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize device
        self.device = MSR605XDevice()
        self.commands = MSR605XCommands(self.device)
        self.file_manager = FileManager()

        # Set callback for status changes
        self.device.set_status_callback(self._on_device_status_changed)

        # Setup window
        self.set_title("MSR605X Utility")
        self.set_default_size(900, 700)

        # Build UI
        self._build_ui()

        # Update UI state
        self._update_connection_state()

        # Start auto-detection polling
        self._start_device_polling()

    def _build_ui(self):
        """Build the main UI."""
        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        # Header bar
        self._build_header_bar()
        main_box.append(self.header)

        # Toast overlay for notifications
        self.toast_overlay = Adw.ToastOverlay()
        main_box.append(self.toast_overlay)

        # Content with sidebar navigation
        self._build_content()
        self.toast_overlay.set_child(self.content_box)

    def _build_header_bar(self):
        """Build the header bar."""
        self.header = Adw.HeaderBar()

        # Title
        title = Adw.WindowTitle(
            title="MSR605X Utility",
            subtitle="Searching for device..."
        )
        self.header.set_title_widget(title)
        self.title_widget = title

        # Left side - LED indicators only (auto-connection)
        led_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        led_box.set_margin_start(6)

        self.led_green = Gtk.DrawingArea()
        self.led_green.set_size_request(12, 12)
        self.led_green.add_css_class("led-indicator")
        self.led_green.add_css_class("led-off")
        led_box.append(self.led_green)

        self.led_yellow = Gtk.DrawingArea()
        self.led_yellow.set_size_request(12, 12)
        self.led_yellow.add_css_class("led-indicator")
        self.led_yellow.add_css_class("led-off")
        led_box.append(self.led_yellow)

        self.led_red = Gtk.DrawingArea()
        self.led_red.set_size_request(12, 12)
        self.led_red.add_css_class("led-indicator")
        self.led_red.add_css_class("led-off")
        led_box.append(self.led_red)

        self.header.pack_start(led_box)

        # Right side - Menu
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")

        menu = Gio.Menu()
        menu.append("Preferences", "app.preferences")
        menu.append("About", "app.about")
        menu.append("Quit", "app.quit")
        menu_button.set_menu_model(menu)

        self.header.pack_end(menu_button)

    def _build_content(self):
        """Build main content area with navigation."""
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Sidebar navigation
        sidebar = self._build_sidebar()
        self.content_box.append(sidebar)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.content_box.append(separator)

        # Stack for panels
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)

        # Create panels
        self.read_panel = ReadPanel(self.commands, self._show_toast, self.file_manager)
        self.write_panel = WritePanel(self.commands, self._show_toast, self.file_manager)
        self.erase_panel = ErasePanel(self.commands, self._show_toast)
        self.settings_panel = SettingsPanel(self.commands, self._show_toast)

        self.stack.add_titled(self.read_panel, "read", "Read")
        self.stack.add_titled(self.write_panel, "write", "Write")
        self.stack.add_titled(self.erase_panel, "erase", "Erase")
        self.stack.add_titled(self.settings_panel, "settings", "Settings")

        self.content_box.append(self.stack)

    def _build_sidebar(self) -> Gtk.Box:
        """Build navigation sidebar."""
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sidebar.set_margin_top(12)
        sidebar.set_margin_bottom(12)
        sidebar.set_margin_start(12)
        sidebar.set_margin_end(12)
        sidebar.set_size_request(200, -1)

        # Navigation buttons
        nav_buttons = [
            ("Read Card", "document-open-symbolic", "read"),
            ("Write Card", "document-save-symbolic", "write"),
            ("Erase Card", "edit-clear-symbolic", "erase"),
            ("Settings", "preferences-system-symbolic", "settings"),
        ]

        self.nav_button_group = []
        first = True

        for label, icon, page in nav_buttons:
            btn = Gtk.ToggleButton()
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            btn_box.set_margin_start(8)
            btn_box.set_margin_end(8)

            icon_widget = Gtk.Image.new_from_icon_name(icon)
            btn_box.append(icon_widget)

            label_widget = Gtk.Label(label=label)
            label_widget.set_xalign(0)
            label_widget.set_hexpand(True)
            btn_box.append(label_widget)

            btn.set_child(btn_box)
            btn.page_name = page

            if first:
                btn.set_active(True)
                first = False

            btn.connect("toggled", self._on_nav_toggled)

            self.nav_button_group.append(btn)
            sidebar.append(btn)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        sidebar.append(spacer)

        # Log area
        log_label = Gtk.Label(label="Activity Log")
        log_label.set_xalign(0)
        log_label.add_css_class("heading")
        sidebar.append(log_label)

        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_min_content_height(150)
        log_scroll.set_vexpand(False)

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.log_view.add_css_class("log-view")
        self.log_buffer = self.log_view.get_buffer()

        log_scroll.set_child(self.log_view)
        sidebar.append(log_scroll)

        return sidebar

    def _on_nav_toggled(self, button):
        """Handle navigation button toggle."""
        if button.get_active():
            # Deactivate other buttons
            for btn in self.nav_button_group:
                if btn != button:
                    btn.set_active(False)

            # If switching to write panel, copy read data
            if button.page_name == "write" and self.read_panel.current_tracks:
                track1 = ""
                track2 = ""
                track3 = ""
                for track in self.read_panel.current_tracks:
                    if track.track_number == 1:
                        track1 = track.data
                    elif track.track_number == 2:
                        track2 = track.data
                    elif track.track_number == 3:
                        track3 = track.data
                self.write_panel.set_track_data(track1, track2, track3)

            # Switch to selected page
            self.stack.set_visible_child_name(button.page_name)

    def _connect(self):
        """Connect to MSR605X device (automatic)."""
        self.title_widget.set_subtitle("Connecting...")

        def do_connect():
            success, message = self.device.connect()
            GLib.idle_add(self._on_connect_complete, success, message)

        thread = Thread(target=do_connect, daemon=True)
        thread.start()

    def _disconnect(self):
        """Disconnect from MSR605X device."""
        success, message = self.device.disconnect()

        if success:
            self._log("Device disconnected")

        self._update_connection_state()

    def _update_connection_state(self):
        """Update UI based on connection state."""
        connected = self.device.is_connected

        if connected:
            self.title_widget.set_subtitle("Connected")
            # Update LED indicators
            self._set_led("green", True)
            self._set_led("yellow", False)
            self._set_led("red", False)
        else:
            self.title_widget.set_subtitle("Searching for device...")
            # All LEDs off
            self._set_led("green", False)
            self._set_led("yellow", False)
            self._set_led("red", False)

        # Update panels
        self.read_panel.set_sensitive(connected)
        self.write_panel.set_sensitive(connected)
        self.erase_panel.set_sensitive(connected)
        self.settings_panel.set_sensitive(connected)

    def _set_led(self, color: str, on: bool):
        """Set LED indicator state."""
        led_widgets = {
            "green": self.led_green,
            "yellow": self.led_yellow,
            "red": self.led_red,
        }

        led = led_widgets.get(color)
        if led:
            led.remove_css_class("led-off")
            led.remove_css_class(f"led-{color}")

            if on:
                led.add_css_class(f"led-{color}")
            else:
                led.add_css_class("led-off")

    def _on_device_status_changed(self, connected: bool):
        """Callback for device connection status changes."""
        GLib.idle_add(self._update_connection_state)

    def _show_toast(self, message: str, error: bool = False):
        """Show a toast notification."""
        toast = Adw.Toast(title=message)
        if error:
            toast.set_timeout(5)
        self.toast_overlay.add_toast(toast)

    def _log(self, message: str):
        """Add message to activity log."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        text = f"[{timestamp}] {message}\n"

        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, text)

        # Scroll to bottom
        mark = self.log_buffer.create_mark(None, self.log_buffer.get_end_iter(), False)
        self.log_view.scroll_to_mark(mark, 0, False, 0, 0)

    def show_settings(self):
        """Show settings panel."""
        for btn in self.nav_button_group:
            if btn.page_name == "settings":
                btn.set_active(True)
                break

    def _start_device_polling(self):
        """Start polling for device connection."""
        self._polling_source_id = GLib.timeout_add(1000, self._check_device_connection)
        self._connecting = False

    def _check_device_connection(self) -> bool:
        """Check if device is available and auto-connect/disconnect."""
        devices = self.device.enumerate_devices()

        if self.device.is_connected:
            # Check if device was unplugged
            if not devices:
                self._log("Device unplugged")
                self._disconnect()
        else:
            # Check if device is available and try to connect
            if devices and not self._connecting:
                self._connecting = True
                self._log("Device detected, connecting...")
                self._connect()
            elif not devices:
                self._connecting = False

        return True  # Continue polling

    def _on_connect_complete(self, success: bool, message: str):
        """Handle connection result."""
        self._connecting = False

        if success:
            self._show_toast("Device connected")
            self._log(f"Connected: {message}")

            # Reset device to clean state
            self.commands.reset()

            # Get firmware version
            fw_result = self.commands.get_firmware_version()
            if fw_result.success:
                self._log(fw_result.message)

        else:
            self._log(f"Connection failed: {message}")

        self._update_connection_state()
