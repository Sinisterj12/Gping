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
- Python 3.x
- CustomTkinter
- tcping.exe (included)
- Administrator rights for network detection

## Usage

1. Run `ping_tool.py`
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
