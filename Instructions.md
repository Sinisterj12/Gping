# AI Instructions for GPing Project

## Project Overview
GPing is a critical network monitoring tool designed for Windows environments, specifically used in grocery stores for network diagnostics. The tool uses tcping.exe for TCP-based connectivity testing and provides real-time monitoring with a modern GUI interface.

## Core Requirements

### Environment and Dependencies
- Windows-only environment
- Requires tcping.exe in root directory
- Python with CustomTkinter for modern UI
- Administrator rights needed for network detection

### CSV Logging System
- Files must follow format: `GPingMMDDYYYY.csv` (current date)
- Location: Root directory only (critical for ISP/NCR troubleshooting)
- Never overwrite existing logs
- Headers required:
  ```
  Date,Time,Type,IP Address,Event,Response Time,Network Type,Downtime,Packet Loss %,Details
  ```
- Buffer writes to optimize performance
- Auto-cleanup after 7 days

### Network Testing
- Gateway IP:
  - Must auto-detect using PowerShell
  - Allow manual override
  - Test using TCP port 80
- Google DNS (8.8.8.8):
  - Fixed entry as fallback
  - Test using TCP port 53
- Connection States:
  - UP: 2 successful pings required
  - DOWN: 3 consecutive failures required
  - Track packet loss and response times

### GUI Implementation
- Status Display:
  - ● Connected (Green)
  - ⬤ Disconnected (Red)
  - ◌ Starting (Orange)
  - ○ Not Running (Gray)
- Controls:
  - Single toggle button for Start/Stop
  - Checkboxes for enabling/disabling each IP test
  - Network type check button
- Connection Log:
  - Real-time updates
  - Formatted timestamps
  - Clear status messages

## Critical Behaviors

### Error Handling
- Handle tcping.exe not found
- Manage network detection failures
- Buffer CSV writes for performance
- Clean recovery from connection drops

### Performance Considerations
- Throttle GUI updates (350ms minimum interval)
- Buffer log writes (10 entries or 5 seconds)
- Cleanup memory during log maintenance
- Use daemon threads for ping operations

### User Experience
- Clear status indicators
- Immediate feedback on actions
- Proper thread cleanup on exit
- Save user preferences

## Code Structure
- TCPingHandler: Core ping operations (DO NOT MODIFY)
- PingTool: Main application class
  - Network frame: Profile checking
  - IP frame: Address configuration
  - Control frame: Start/Stop operations
  - Results frame: Live monitoring

## Future Considerations
- Speed test integration planned
- Enhanced network profiling
- Additional monitoring metrics
- Custom IP configuration options

Remember: This tool is critical for store operations. Maintain reliability and performance while ensuring clear status reporting for technicians.