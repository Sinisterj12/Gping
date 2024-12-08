# GPing Tool

A modern network connectivity monitoring tool with GUI interface.

## Features

- Modern, clean GUI interface using CustomTkinter
- Real-time connection monitoring for Gateway and Google DNS
- Clear status indicators:
  - ✓ Connected
  - ✗ Disconnected
  - ⟳ Starting
  - ○ Not Running
- Automatic log cleanup (removes logs older than 7 days)
- CSV logging with detailed connection events
- Network type detection (Public/Private)
- Configurable IP addresses with save functionality
- Improved CSV log format with clear timestamps and downtime tracking

## Recent Updates

- Added larger, more visible Unicode status indicators
- Implemented automatic cleanup of old log files (7-day retention)
- Enhanced CSV logging with separate date/time columns and downtime tracking
- Improved error handling and network type detection
- Added modern UI elements and better spacing
- Optimized connection status updates and thread management

## Requirements

- Python 3.x
- CustomTkinter
- Other dependencies listed in requirements.txt

## Usage

1. Run `ping_tool.py`
2. Enter Gateway IP (default: 192.168.1.254)
3. Enter Google DNS (default: 8.8.8.8)
4. Click "Start Tests" to begin monitoring
5. View real-time status and connection log
6. Check network type using the "Check Network Type" button

## Logs

The tool creates CSV log files in the following format:
- Date and Time columns for easy filtering
- Connection events (UP, LOST, RESTORED)
- Response times and packet loss statistics
- Network type information
- Downtime duration tracking

Logs are automatically cleaned up after 7 days to manage disk space.
