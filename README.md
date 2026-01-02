# MSR605X Utility for Ubuntu

A native GTK4 application for Ubuntu to read, write, and manage magnetic stripe cards using the MSR605X device.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![GTK](https://img.shields.io/badge/GTK-4.0-orange.svg)
![Platform](https://img.shields.io/badge/platform-Ubuntu%2022.04+-purple.svg)

## Overview

MSR605X Utility is an open source alternative to the Windows utility for the MSR605X magnetic card reader/writer. The application is designed to work natively on Ubuntu and other Linux distributions compatible with GTK4.

**Tested with firmware**: REVH7.31

## Features

### Card Operations
- **Read**: Read all 3 tracks (ISO and raw data)
- **Write**: Write data to all 3 tracks
- **Erase**: Selective track erasure
- **Clone**: Clone cards (read + write)

### Automatic Connection
- **Plug & Play**: Device is automatically detected and connected
- **Hot-plug**: Automatic detection when device is plugged/unplugged
- **No Connect button**: Simplified interface, connection is handled automatically

### Supported Formats
- **ISO 7811** - International standard for magnetic cards
- **Raw Data** - Direct bit access

### Configuration
- **Coercivity**: Hi-Co (2750-4000 Oe) / Lo-Co (300 Oe)
- **BPI**: 75 or 210 bits per inch per track
- **BPC**: 5, 7, or 8 bits per character per track

### File Management
- Save data in JSON format
- Save data in CSV format
- Load data from file

### User Interface
- Modern design with GTK4 and libadwaita
- Automatic light/dark theme support
- LED status indicators
- Real-time operation log
- Toast notifications for immediate feedback

## System Requirements

- **Operating System**: Ubuntu 22.04+ (or other Linux distributions with GTK4)
- **Python**: 3.10 or higher
- **Hardware**: MSR605X device connected via USB

## Installation

### Method 1: Debian Package (.deb) - Recommended

The easiest way to install the application on Ubuntu/Debian:

```bash
# Download the .deb package from the Releases page
wget https://github.com/Sam4000133/msr605x-ubuntu/releases/latest/download/msr605x-utility_1.0.0-1_all.deb

# Install the package
sudo dpkg -i msr605x-utility_1.0.0-1_all.deb

# Install any missing dependencies
sudo apt-get install -f
```

After installation, the application will be available in the applications menu.

### Method 2: Installation Script

```bash
# Clone the repository
git clone https://github.com/Sam4000133/msr605x-ubuntu.git
cd msr605x-ubuntu

# Run the installation script
chmod +x install.sh
sudo ./install.sh
```

### Method 3: Manual Installation

#### 1. Install system dependencies

```bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 libhidapi-hidraw0 libhidapi-dev
```

#### 2. Clone the repository

```bash
git clone https://github.com/Sam4000133/msr605x-ubuntu.git
cd msr605x-ubuntu
```

#### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

#### 4. Install the application

```bash
pip install -e .
```

#### 5. Configure udev permissions (required for non-root access)

```bash
# Copy udev rules
sudo cp data/99-msr605x.rules /etc/udev/rules.d/

# Reload rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add your user to the plugdev group
sudo usermod -aG plugdev $USER
```

**Important**: Log out and log back in to apply the group changes.

## Usage

### Starting the Application

```bash
# From terminal
python -m src.main

# Or after installation
msr605x-gui
```

The application will also be available in the applications menu as "MSR605X Utility".

### Quick Guide

1. **Connection**: The device is automatically detected and connected when plugged via USB
2. **Reading**:
   - Go to the "Read Card" panel
   - Select the format (ISO or Raw)
   - Click "Read Card" and swipe the card
3. **Writing**:
   - Go to the "Write Card" panel
   - Enter data for each track (without sentinels %, ;, ? - they are added automatically)
   - Click "Write Card" and swipe a blank card
4. **Erasing**:
   - Go to the "Erase Card" panel
   - Select the tracks to erase
   - Confirm and swipe the card
5. **Settings**:
   - Configure coercivity (Hi-Co/Lo-Co)
   - Run diagnostic tests on the device

## Project Structure

```
msr605x-ubuntu/
├── src/
│   ├── main.py              # Entry point
│   ├── app.py               # GtkApplication class
│   ├── window.py            # Main window
│   ├── msr605x/             # Device communication module
│   │   ├── device.py        # USB HID communication
│   │   ├── commands.py      # High-level commands
│   │   ├── constants.py     # Protocol constants
│   │   └── parser.py        # Track data parser
│   ├── ui/                  # Interface components
│   │   ├── read_panel.py    # Read panel
│   │   ├── write_panel.py   # Write panel
│   │   ├── erase_panel.py   # Erase panel
│   │   └── settings_panel.py # Settings panel
│   └── utils/
│       └── file_io.py       # File management
├── data/
│   ├── com.github.msr605x.desktop  # Desktop entry
│   ├── com.github.msr605x.svg      # Icon
│   ├── style.css                   # CSS styles
│   └── 99-msr605x.rules            # Udev rules
├── tests/
│   └── test_parser.py       # Unit tests
├── pyproject.toml           # Project configuration
├── requirements.txt         # Python dependencies
├── install.sh               # Installation script
├── LICENSE                  # MIT License
└── README.md                # This file
```

## Technical Specifications

### Magnetic Tracks

| Track   | BPI | BPC | Max Characters | Data Type    |
|---------|-----|-----|----------------|--------------|
| Track 1 | 210 | 7   | 79             | Alphanumeric |
| Track 2 | 75  | 5   | 40             | Numeric      |
| Track 3 | 210 | 5   | 107            | Numeric      |

### Device Commands

| Command | Description |
|---------|-------------|
| ESC a   | Reset device |
| ESC e   | Communication test |
| ESC v   | Firmware version |
| ESC r   | ISO read |
| ESC m   | Raw read |
| ESC w   | ISO write |
| ESC n   | Raw write |
| ESC c   | Erase (mask: 0x01=T1, 0x02=T2, 0x04=T3) |
| ESC x   | Set Hi-Co |
| ESC y   | Set Lo-Co |

### Important Technical Notes

- **Sentinels**: Do NOT include sentinels (%, ;, ?) in write data - the device adds them automatically
- **ISO Write Format**: `ESC w ESC s ESC 01 [data] ESC 02 [data] ESC 03 [data] ? FS`
- **HID Protocol**: 64-byte packets with header (bit7=first, bit6=last, bits0-5=length)

### Coercivity

- **Hi-Co (High Coercivity)**: 2750-4000 Oe
  - More resistant to demagnetization
  - Used for cards requiring greater durability

- **Lo-Co (Low Coercivity)**: 300 Oe
  - Standard for most cards
  - Easier to encode

## Troubleshooting

### Device not detected

1. Verify the device is connected:
   ```bash
   lsusb | grep -i "0801:0003"
   ```

2. Check permissions:
   ```bash
   ls -la /dev/hidraw*
   ```

3. Make sure udev rules are installed:
   ```bash
   cat /etc/udev/rules.d/99-msr605x.rules
   ```

4. Reload udev rules:
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

### "Permission denied" error

Make sure you are in the `plugdev` group:
```bash
groups $USER
sudo usermod -aG plugdev $USER
# Log out and log back in
```

### GUI doesn't start

Verify that GTK4 and libadwaita are installed:
```bash
sudo apt install gir1.2-gtk-4.0 gir1.2-adw-1
```

### Read/write errors

- Clean the reader head
- Swipe the card at a constant speed
- Verify the card is not damaged
- Try changing the coercivity in settings

## Development

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/NewFeature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push the branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.

## Credits

- Inspired by projects [eucalyp/MSR605](https://github.com/eucalyp/MSR605) and [bentbot/MSR605-GUI](https://github.com/bentbot/MSR605-GUI)
- Original UI design and icons

## Disclaimer

This software is provided solely for educational and legitimate purposes. Users are responsible for ensuring compliance with all applicable laws and regulations regarding the use of magnetic stripe card technology.

## Contact

- **Repository**: [https://github.com/Sam4000133/msr605x-ubuntu](https://github.com/Sam4000133/msr605x-ubuntu)
- **Issues**: [https://github.com/Sam4000133/msr605x-ubuntu/issues](https://github.com/Sam4000133/msr605x-ubuntu/issues)

---

Developed with ❤️ for the Linux community
