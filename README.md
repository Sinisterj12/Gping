# GPing Tool

A modern network connectivity monitoring tool with GUI interface.

## Features

- Modern, clean GUI interface using CustomTkinter
- Real-time connection monitoring for Gateway and Google DNS
- Selective testing with checkboxes for each IP
- Clear status indicators:
  - ● Connected (Green)
  - ⬤ Disconnected (Red)
  - ◌ Starting (Orange)
  - ○ Not Running (Gray)
- Automatic log cleanup (removes logs older than 7 days)
- CSV logging with detailed connection events
- Network type detection (Public/Private)
- Configurable IP addresses with save functionality
- Improved CSV log format with clear timestamps and downtime tracking
- Memory-optimized with buffered logging
- Minimize to System Tray: Application can be minimized to the system tray for background operation.

## Recent Updates

- Simplified UI with single toggle button for Start/Stop
- Added selective testing with checkboxes for each IP
- Improved error handling and recovery detection
- Enhanced status indicators with both icons and text
- Optimized memory usage with buffered CSV writing
- Added packet loss tracking and reporting
- Improved network type detection
- Enhanced error handling for tcping operations

## Requirements

- Windows OS
- Administrator rights for network detection
- tcping.exe (included)
- pystray
- Pillow

## Installation & Setup

### Using the Pre-built Executable (Recommended)
1. Download or clone this repository
2. Run `GPing.exe` directly from the project folder

### Development Setup (UV)
If you want to modify or develop the application:

1. Install [UV](https://docs.astral.sh/uv/) package manager
2. Clone this repository
3. Install dependencies:
   ```powershell
   uv sync
   ```
4. Run the development version:
   ```powershell
   uv run ping_tool.py
   ```

### Building from Source
To create a new executable:
```powershell
uv run pyinstaller GPing.spec
```

## Usage

1. **Run the application:**
   - Double-click `GPing.exe` OR
   - Run from command line: `.\GPing.exe`
2. Enter Gateway IP (auto-detected) or use default: 192.168.1.254
3. Enter Google DNS or use default: 8.8.8.8
4. Select which IPs to monitor using the checkboxes
5. Click "Start Tests" to begin monitoring
6. View real-time status and connection log
7. Check network type using the "Check Network Type" button

## Logs

The tool creates CSV log files with the following information:
- Date and Time columns for easy filtering
- Connection events (UP, LOST, RESTORED)
- Response times and packet loss statistics
- Network type information
- Downtime duration tracking

Logs are automatically cleaned up after 7 days to manage disk space.

## Project Structure

```
GPing/
├── GPing.exe          # Main executable (ready to run)
├── ping_tool.py       # Source code
├── tcping.exe         # TCP ping utility (required)
├── pyproject.toml     # UV project configuration
├── uv.lock           # Locked dependencies
├── GPing.spec        # PyInstaller build configuration
├── gping_settings.json # Application settings
└── logs/             # Log files directory
```

## Development

This project uses [UV](https://docs.astral.sh/uv/) for dependency management. Key commands:

- `uv sync` - Install/update dependencies
- `uv add package-name` - Add new dependencies
- `uv run python ping_tool.py` - Run development version
- `uv run pyinstaller GPing.spec` - Build executable
