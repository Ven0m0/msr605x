#!/bin/bash
# MSR605X Utility Installation Script for Ubuntu

set -e

echo "=========================================="
echo "MSR605X Utility Installer for Ubuntu"
echo "=========================================="

# Check if running as root for system-wide install
INSTALL_SYSTEM=false
if [ "$EUID" -eq 0 ]; then
    INSTALL_SYSTEM=true
    echo "Running as root - will install system-wide"
else
    echo "Running as user - will install to user directory"
fi

# Check for required system packages
echo ""
echo "Checking system dependencies..."

MISSING_DEPS=""

if ! dpkg -l | grep -q python3-gi; then
    MISSING_DEPS="$MISSING_DEPS python3-gi"
fi

if ! dpkg -l | grep -q gir1.2-gtk-4.0; then
    MISSING_DEPS="$MISSING_DEPS gir1.2-gtk-4.0"
fi

if ! dpkg -l | grep -q gir1.2-adw-1; then
    MISSING_DEPS="$MISSING_DEPS gir1.2-adw-1"
fi

if ! dpkg -l | grep -q libhidapi-hidraw0; then
    MISSING_DEPS="$MISSING_DEPS libhidapi-hidraw0"
    if ! command -v apt-get >/dev/null 2>&1 && command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sq --noconfirm python-hidapi python-hid
    fi
fi


if [ -n "$MISSING_DEPS" ]; then
    echo "Missing system packages:$MISSING_DEPS"
    echo ""
    if $INSTALL_SYSTEM; then
        echo "Installing missing packages..."
        apt-get update
        apt-get install -y $MISSING_DEPS
    else
        echo "Please install the missing packages:"
        echo "  sudo apt install$MISSING_DEPS"
        exit 1
    fi
else
    echo "All system dependencies are installed."
fi

# Install Python package
echo ""
echo "Installing MSR605X Utility..."

if $INSTALL_SYSTEM; then
    pip3 install --system .
else
    pip3 install --user .
fi

# Install udev rules
echo ""
echo "Installing udev rules for device access..."

if $INSTALL_SYSTEM; then
    cp data/99-msr605x.rules /etc/udev/rules.d/
    udevadm control --reload-rules
    udevadm trigger
    echo "udev rules installed."
else
    echo "To allow non-root access to the device, run:"
    echo "  sudo cp data/99-msr605x.rules /etc/udev/rules.d/"
    echo "  sudo udevadm control --reload-rules"
    echo "  sudo udevadm trigger"
fi

# Install desktop entry and icon
echo ""
echo "Installing desktop entry and icon..."

if $INSTALL_SYSTEM; then
    cp data/com.github.msr605x.desktop /usr/share/applications/
    cp data/com.github.msr605x.svg /usr/share/icons/hicolor/scalable/apps/
    gtk-update-icon-cache /usr/share/icons/hicolor/
else
    mkdir -p ~/.local/share/applications
    mkdir -p ~/.local/share/icons/hicolor/scalable/apps
    cp data/com.github.msr605x.desktop ~/.local/share/applications/
    cp data/com.github.msr605x.svg ~/.local/share/icons/hicolor/scalable/apps/
    gtk-update-icon-cache ~/.local/share/icons/hicolor/ 2>/dev/null || true
fi

# Add user to plugdev group
echo ""
if ! groups | grep -q plugdev; then
    if $INSTALL_SYSTEM; then
        usermod -aG plugdev $SUDO_USER
        echo "Added user $SUDO_USER to plugdev group."
        echo "Please log out and log back in for group changes to take effect."
    else
        echo "To access the device without root, add yourself to the plugdev group:"
        echo "  sudo usermod -aG plugdev \$USER"
        echo "Then log out and log back in."
    fi
fi

echo ""
echo "=========================================="
echo "Installation complete!"
echo ""
echo "You can now run the application with:"
echo "  msr605x-gui"
echo ""
echo "Or find it in your application menu as 'MSR605X Utility'"
echo "=========================================="
