#################################################################
# GPING TOOL - Network Connectivity Monitor
# 
# This tool monitors network connectivity using TCP pings to both
# gateway and LAN addresses. It provides real-time status updates
# and logs connection events for troubleshooting.
#
# Structure:
# 1. TCPingHandler: Core ping functionality (DO NOT MODIFY)
# 2. PingTool: GUI and monitoring implementation
#    - Network checking (expandable for future features)
#    - IP configuration
#    - Status monitoring and logging
#
# Future Additions Planned:
# - Additional network checks under network profile section
# - Enhanced ping functionality (coming soon)
# - More GUI features for better monitoring
#################################################################

#################################################################
# CORE FUNCTIONALITY - MODIFY ONLY WHEN CHANGING PING BEHAVIOR
#################################################################

import subprocess
import threading
import time
import csv
import os
import json
from datetime import datetime, timedelta
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import re
import socket
import ctypes
import sys

class TCPingHandler:
    """TCPing implementation for network connectivity testing
    
    This class handles the core ping functionality using tcping.exe.
    It's designed to be simple and reliable for network testing.
    
    Note: Any changes here will affect ALL ping behavior in the application"""
    def __init__(self, tcping_path=None):
        if tcping_path is None:
            # Get the directory where the executable is located
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                base_path = os.path.dirname(sys.executable)
            else:
                # Running as script
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            self.tcping_path = os.path.join(base_path, "tcping.exe")
        else:
            self.tcping_path = tcping_path
            
        if not os.path.exists(self.tcping_path):
            raise FileNotFoundError(f"Error: tcping.exe not found at {self.tcping_path}")
        
    def ping_address(self, ip_address, ping_type=None):
        """Execute a TCP ping and return (is_successful, ping_time_ms)"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # Use port 80 for gateway and port 53 for DNS (8.8.8.8)
            port = "53" if ip_address == "8.8.8.8" else "80"
            
            # TCPing with 1 attempt, 500ms timeout
            ping_process = subprocess.run(
                [self.tcping_path, "-n", "1", "-w", "500", ip_address, port],
                capture_output=True,
                text=True,
                timeout=1,
                startupinfo=startupinfo
            )
            
            # TCPing specific output parsing
            output = ping_process.stdout.lower()
            is_up = "port is open" in output or "connected to" in output
            ping_time = None
            
            if is_up:
                time_match = re.search(r"time[=<](\d+\.?\d*)ms", output)
                if time_match:
                    ping_time = float(time_match.group(1))
            
            return is_up, ping_time
            
        except subprocess.TimeoutExpired:
            return False, None
        except Exception as e:
            print(f"Error pinging {ip_address}: {str(e)}")
            return False, None

#################################################################
# END OF CORE PING HANDLER - DO NOT MODIFY WITHOUT DISCUSSION
#################################################################

#################################################################
# GUI IMPLEMENTATION - DO NOT MODIFY UNLESS EXPLICITLY REQUESTED
# 
# The GUI is built using customtkinter for a modern look.
# Each section (frames) handles different aspects:
# - Network Frame: Shows network profile (more features coming)
# - IP Frame: Configure gateway and LAN IPs
# - Control Frame: Start/Stop button
# - Results Frame: Real-time log display
#################################################################

class PingTool:
    """Main application class handling GUI and ping monitoring
    
    This class ties everything together:
    1. Creates and manages the GUI
    2. Handles network profile checking (expandable section)
    3. Manages ping tests and logging
    4. Tracks connection status and packet loss
    
    Note: Most modifications should focus on adding features,
    not changing existing core functionality
    """
    def __init__(self, root):
        self.root = root
        self.root.title("GPing by James")
        
        # Initialize TCPing handler
        try:
            self.ping_handler = TCPingHandler()
        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e))
            self.root.destroy()
            return
            
        # Status icons dictionary
        self.status_icons = {
            "up": "●",         # Solid circle
            "down": "⬤",       # Black circle
            "starting": "◌",   # Dotted circle
            "not_running": "○"  # Empty circle
        }
        
        self.status_colors = {
            "up": "#00B050",      # Green
            "down": "#FF0000",    # Red
            "starting": "#FFA500", # Orange
            "not_running": "gray"  # Gray
        }
        
        # Use system appearance mode
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        
        # Get base path for executable or script
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
            
        # Set file paths
        self.settings_file = os.path.join(self.base_path, "gping_settings.json")
        self.logs_dir = os.path.join(self.base_path, "logs")
        
        self.load_settings()
        
        # Initialize tracking variables
        self.current_date = datetime.now().strftime('%m%d%Y')
        self.csv_filename = f"GPing{self.current_date}.csv"
        
        # Packet loss tracking
        self.total_pings = {}  # Total pings per IP
        self.failed_pings = {}  # Failed pings per IP
        
        self.root.geometry("650x550")
        self.root.minsize(650, 550)
        
        # Main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create frames
        self.create_network_frame()
        self.create_ip_frame()
        self.create_control_frame()
        self.create_results_frame()
        
        # Initialize other tracking variables
        self.is_running = False
        self.last_csv_log_time = 0
        self.csv_log_interval = 300  # Log every 5 minutes
        self.failure_logged = {}
        self.ip_status = {}
        self.down_start_times = {}
        self.total_downtime = {}
        
        # Create logs directory and cleanup old logs
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        self.cleanup_old_logs()
            
        # Initialize CSV
        self.init_csv_log()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    #################################################################
    # GUI Creation Methods - DO NOT MODIFY
    # These methods create and manage the GUI components
    #################################################################

    def init_csv_log(self):
        """Initialize CSV log file if it doesn't exist"""
        try:
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir)
                
            if not os.path.exists(self.csv_filename):
                with open(self.csv_filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([
                        'Date',
                        'Time',
                        'Type',           # GATEWAY or GOOGLE_DNS
                        'IP Address',
                        'Event',          # UP, LOST, RESTORED
                        'Response Time',
                        'Network Type',
                        'Downtime',       # How long connection was down
                        'Packet Loss %',
                        'Details'         # Additional info like start/stop markers
                    ])
        except PermissionError:
            messagebox.showerror("Error", "Cannot create log file. Please run as administrator or check folder permissions.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize log file: {str(e)}")

    def calculate_packet_loss(self, ip_address):
        """Calculate packet loss percentage for an IP"""
        if ip_address not in self.total_pings:
            self.total_pings[ip_address] = 0
            self.failed_pings[ip_address] = 0
        
        if self.total_pings[ip_address] == 0:
            return 0.0
            
        return round((self.failed_pings[ip_address] / self.total_pings[ip_address]) * 100, 1)

    def log_to_csv(self, event_type, ip_address, status, response_time=None, network_type=None, details=None, skip_packet_loss=False):
        """Log events to CSV file with buffering for better performance"""
        try:
            # Initialize buffer if needed
            if not hasattr(self, '_csv_buffer'):
                self._csv_buffer = []
                self._last_flush = time.time()
            
            now = datetime.now()
            date = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            
            response_time_str = f"{response_time:.1f}ms" if response_time is not None else ''
            packet_loss = f"{self.calculate_packet_loss(ip_address)}%" if not skip_packet_loss else ''
            
            # Calculate downtime if this is a RESTORED event
            downtime = ''
            if "RESTORED after" in status:
                downtime = status.split("RESTORED after ")[1].split(",")[0]
                status = "RESTORED"  # Clean up status
            
            # Format details
            if "===" in str(details or ""):
                event_type = "INFO"
                details = status
                status = "SESSION"
            
            row = [
                date,
                time_str,
                event_type,
                ip_address,
                status,
                response_time_str,
                network_type if network_type else '',
                downtime,
                packet_loss,
                details
            ]
            
            self._csv_buffer.append(row)
            
            # Force flush on RESTORED events or if buffer is large enough or enough time has passed
            if status == "RESTORED" or len(self._csv_buffer) >= 10 or time.time() - self._last_flush > 5:
                with open(self.csv_filename, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(self._csv_buffer)
                self._csv_buffer = []
                self._last_flush = time.time()
                
        except Exception as e:
            self.log_event(f"ERROR: Failed to write to log file: {str(e)}")

    def load_settings(self):
        self.saved_settings = {}
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.saved_settings = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def get_network_type(self):
        try:
            # Use CREATE_NO_WINDOW flag to hide PowerShell window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            cmd = ["powershell", "-Command", 
                  "Get-NetConnectionProfile | Select-Object -ExpandProperty NetworkCategory"]
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            profile = result.stdout.strip()
            return profile
        except Exception as e:
            return "Unknown"

    def on_closing(self):
        if self.is_running:
            self.stop_ping()
        self.root.destroy()

    def create_network_frame(self):
        """Create the network profile section
        
        This section will be expanded in the future with:
        - Additional network checks
        - More detailed network information
        - New monitoring features
        """
        self.network_frame = ctk.CTkFrame(self.main_frame)
        self.network_frame.pack(fill="x", padx=5, pady=5)
        
        # Create a frame for the network info and check button
        info_frame = ctk.CTkFrame(self.network_frame)
        info_frame.pack(fill="x", padx=5, pady=5)
        
        self.network_label = ctk.CTkLabel(info_frame, 
                                        text="Network Type: Not Checked",
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.network_label.pack(side="left", pady=5, padx=5)
        
        check_btn = ctk.CTkButton(info_frame, text="Check Network Type", width=150,
                                command=self.check_network_profile)
        check_btn.pack(side="right", padx=5)

    def check_network_profile(self):
        """Check and display the network profile"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            cmd = ["powershell", "-Command", 
                  "Get-NetConnectionProfile | Select-Object -ExpandProperty NetworkCategory"]
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo, timeout=5)
            
            if result.returncode != 0:
                raise Exception(f"PowerShell command failed: {result.stderr}")
                
            profile = result.stdout.strip()
            
            # Get network adapter info with timeout
            cmd_adapter = ["powershell", "-Command", 
                         "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -First 1 | Select-Object -ExpandProperty Name"]
            adapter_result = subprocess.run(cmd_adapter, capture_output=True, text=True, startupinfo=startupinfo, timeout=5)
            
            if adapter_result.returncode != 0:
                raise Exception(f"Failed to get adapter info: {adapter_result.stderr}")
                
            adapter_name = adapter_result.stdout.strip()
            
            if not adapter_name:
                raise Exception("No active network adapter found")
            
            if profile == "DomainAuthenticated":
                color = "#00B050"  # Green
                text = f"Network Profile: Work Network ({adapter_name})"
            else:
                color = "#FF0000"  # Red
                text = f"Warning: {profile} Network ({adapter_name})"
            
            self.network_label.configure(text=text, text_color=color)
        except subprocess.TimeoutExpired:
            self.network_label.configure(
                text="Error: Network check timed out. Please try again.", 
                text_color="#FF0000"
            )
        except Exception as e:
            self.network_label.configure(
                text=f"Error checking network: {str(e)}", 
                text_color="#FF0000"
            )

    def create_ip_frame(self):
        """Create the IP address input section"""
        ip_frame = ctk.CTkFrame(self.main_frame)
        ip_frame.pack(fill="x", padx=5, pady=5)
        
        # Create a frame for labels
        labels_frame = ctk.CTkFrame(ip_frame)
        labels_frame.pack(fill="x", padx=5, pady=5)
        
        # Create frames for each row to ensure alignment
        gateway_frame = ctk.CTkFrame(labels_frame)
        gateway_frame.pack(fill="x", pady=2)
        
        lan_frame = ctk.CTkFrame(labels_frame)
        lan_frame.pack(fill="x", pady=2)
        
        # Gateway IP row
        self.gateway_check = ctk.CTkCheckBox(gateway_frame, text="Gateway IP", 
                                            command=self.update_start_button_state)
        self.gateway_check.pack(side="left", padx=(5, 0))
        
        ctk.CTkLabel(gateway_frame, text="Gateway IP:", 
                    font=ctk.CTkFont(size=12), width=80).pack(side="left", padx=5)
        
        self.gateway_ip_entry = ctk.CTkEntry(gateway_frame, width=200)
        self.gateway_ip_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(gateway_frame, text="Save", 
                     command=lambda: self.save_single_ip("gateway"),
                     width=60).pack(side="left", padx=5)
        
        self.gateway_indicator = ctk.CTkLabel(gateway_frame, text="○", 
                                            text_color="gray",
                                            font=ctk.CTkFont(size=16, weight="bold"))
        self.gateway_indicator.pack(side="right", padx=5)
        
        self.gateway_status = ctk.CTkLabel(gateway_frame, text="Not Running",
                                         font=ctk.CTkFont(size=12), width=150)
        self.gateway_status.pack(side="right", padx=5)
        
        # Google DNS row (formerly LAN IP)
        self.dns_check = ctk.CTkCheckBox(lan_frame, text="Google DNS", 
                                        command=self.update_start_button_state)
        self.dns_check.pack(side="left", padx=(5, 0))
        
        ctk.CTkLabel(lan_frame, text="Google DNS:", 
                    font=ctk.CTkFont(size=12), width=80).pack(side="left", padx=5)
        
        self.lan_ip_entry = ctk.CTkEntry(lan_frame, width=200)
        self.lan_ip_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(lan_frame, text="Save", 
                     command=lambda: self.save_single_ip("lan"),
                     width=60).pack(side="left", padx=5)
        
        self.lan_indicator = ctk.CTkLabel(lan_frame, text="○", 
                                        text_color="gray",
                                        font=ctk.CTkFont(size=16, weight="bold"))
        self.lan_indicator.pack(side="right", padx=5)
        
        self.lan_status = ctk.CTkLabel(lan_frame, text="Not Running",
                                     font=ctk.CTkFont(size=12), width=150)
        self.lan_status.pack(side="right", padx=5)
        
        # Auto-detect and fill IP addresses
        self.detect_ip_addresses()

    def detect_ip_addresses(self):
        """Auto-detect and fill IP addresses"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            # Get default gateway with timeout
            cmd = ["powershell", "-Command", 
                  "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -First 1).NextHop"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, startupinfo=startupinfo)
            
            if result.returncode != 0:
                raise Exception(f"Failed to detect gateway: {result.stderr}")
                
            gateway = result.stdout.strip()
            if gateway:
                self.gateway_ip_entry.delete(0, tk.END)
                self.gateway_ip_entry.insert(0, gateway)
            else:
                raise Exception("No gateway detected")
            
            # Only set LAN IP if not already saved
            if not self.saved_settings.get('lan_ip'):
                try:
                    hostname = socket.gethostname()
                    local_ip = socket.gethostbyname(hostname)
                    if local_ip:
                        self.lan_ip_entry.delete(0, tk.END)
                        self.lan_ip_entry.insert(0, local_ip)
                except socket.gaierror:
                    messagebox.showwarning("Warning", "Could not detect local IP address")
            else:
                self.lan_ip_entry.delete(0, tk.END)
                self.lan_ip_entry.insert(0, self.saved_settings['lan_ip'])
        except subprocess.TimeoutExpired:
            messagebox.showerror("Error", "Gateway detection timed out. Please try again or enter IP manually.")
        except PermissionError:
            messagebox.showerror("Error", "Access denied. Please run as administrator for automatic gateway detection.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to detect IP addresses: {str(e)}")

    def create_control_frame(self):
        """Create the control buttons section"""
        control_frame = ctk.CTkFrame(self.main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        self.start_button = ctk.CTkButton(control_frame, text="Start Tests", 
                                        command=self.start_ping, state="disabled")
        self.start_button.pack(side="left", padx=5, pady=5)

    def create_results_frame(self):
        """Create the results display section"""
        results_frame = ctk.CTkFrame(self.main_frame)
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Title
        ctk.CTkLabel(results_frame, text="Connection Log", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        # Results Text Area
        self.results_text = ctk.CTkTextbox(results_frame, wrap="word",
                                         font=ctk.CTkFont(family="Consolas", size=11))
        self.results_text.pack(fill="both", expand=True, padx=5, pady=5)

    def update_status_indicator(self, status, target):
        """Update status indicators with throttling for better performance"""
        if not hasattr(self, '_last_update'):
            self._last_update = {}
        
        current_time = time.time()
        if target in self._last_update and current_time - self._last_update[target] < 0.35:
            return
            
        self._last_update[target] = current_time
        
        if target == "gateway":
            indicator = self.gateway_status
            status_label = self.gateway_indicator
        else:
            indicator = self.lan_status
            status_label = self.lan_indicator
            
        color = self.status_colors.get(status, "gray")
        icon = self.status_icons.get(status, "○")
        
        # Set the status text
        if status == "up":
            text = "Connected"
        elif status == "down":
            text = "Disconnected"
        elif status == "starting":
            text = "Starting..."
        else:
            text = "Not Running"
        
        # Schedule the update
        self.root.after(10, self._apply_status_update, indicator, status_label, color, text, icon)

    def _apply_status_update(self, indicator, status_label, color, text, icon):
        """Actually apply the status update after delay"""
        indicator.configure(text=icon, text_color=color)
        if status_label:
            status_label.configure(text=text)

    def save_single_ip(self, ip_type):
        """Save IP address to settings file"""
        settings = self.saved_settings.copy()
        if ip_type == "gateway":
            settings['gateway_ip'] = self.gateway_ip_entry.get()
        else:
            settings['lan_ip'] = self.lan_ip_entry.get()
            
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
            self.saved_settings = settings
            messagebox.showinfo("Success", f"{ip_type.title()} IP saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save {ip_type} IP: {e}")

    def start_ping(self):
        """Start the ping tests"""
        if not self.is_running:
            self.is_running = True
            self.start_button.configure(text="Stop Tests")
            self.log_event("=== Network Connection Test Started ===")
            
            # Initialize counters for both IPs
            gateway_ip = self.gateway_ip_entry.get()
            google_dns = self.lan_ip_entry.get()
            
            # Reset counters
            self.total_pings = {
                gateway_ip: 0,
                google_dns: 0
            }
            self.failed_pings = {
                gateway_ip: 0,
                google_dns: 0
            }
            
            # Start gateway thread if enabled
            if self.gateway_check.get():
                self.update_status_indicator("starting", "gateway")
                self.gateway_ping_thread = threading.Thread(
                    target=self.ping,
                    args=(gateway_ip, "gateway")
                )
                self.gateway_ping_thread.daemon = True
                self.gateway_ping_thread.start()
            
            # Start Google DNS thread if enabled
            if self.dns_check.get():
                self.update_status_indicator("starting", "google_dns")
                self.lan_ping_thread = threading.Thread(
                    target=self.ping,
                    args=(google_dns, "google_dns")
                )
                self.lan_ping_thread.daemon = True
                self.lan_ping_thread.start()
        else:
            self.stop_ping()

    def stop_ping(self):
        """Stop the ping tests"""
        if self.is_running:
            self.is_running = False
            self.start_button.configure(text="Start Tests")
            
            # Log final status
            self.log_event("=== Network Connection Test Stopped ===")
            
            # Reset status indicators
            self.update_status_indicator("not_running", "gateway")
            self.update_status_indicator("not_running", "google_dns")
            
            # Clear threads
            if hasattr(self, 'gateway_ping_thread'):
                self.gateway_ping_thread = None
            if hasattr(self, 'lan_ping_thread'):
                self.lan_ping_thread = None

    def log_event(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Identify if this line includes a known label like "GATEWAY:" or "GOOGLE_DNS:"
        label = ""
        rest = message.strip()

        # Check if the message starts with our known prefixes
        # We'll align them in a field wide enough for "GOOGLE_DNS" since it's longer
        if rest.startswith("GATEWAY:"):
            label = "GATEWAY"
            rest = rest.replace("GATEWAY:", "").strip()
        elif rest.startswith("GOOGLE_DNS:"):
            label = "GOOGLE_DNS"
            rest = rest.replace("GOOGLE_DNS:", "").strip()

        # Format the output line:
        # Timestamp (fixed width), two spaces, label (left aligned in 10 chars), two spaces, then rest of the message
        # If there's no label (like start/stop lines), we won't leave that space
        if label:
            formatted_line = f"{timestamp}  {label:<10}  {rest}"
        else:
            formatted_line = f"{timestamp}  {rest}"

        self.results_text.insert("end", formatted_line + "\n")
        self.results_text.see("end")

    def format_duration(self, seconds):
        """Format duration in a human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        
        duration = datetime.timedelta(seconds=seconds)
        days = duration.days
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        seconds = duration.seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
            
        return " ".join(parts)

    def ping(self, ip_address, ping_type):
        """Execute ping tests for a given IP address
        
        This is the main monitoring function that:
        1. Tracks connection status
        2. Handles failure detection
        3. Manages recovery detection
        4. Calculates packet loss
        
        Future enhancements planned for additional monitoring capabilities
        """
        #################################################################
        # CRITICAL SECTION - CORE PING BEHAVIOR AND CONNECTION MONITORING
        # DO NOT MODIFY THIS SECTION WITHOUT CAREFUL REVIEW AND DISCUSSION
        # This section handles:
        # 1. Connection state tracking
        # 2. Failure detection logic (3 consecutive failures)
        # 3. Recovery detection (2 consecutive successes)
        # 4. Packet loss calculation
        # Modifications here could affect reliability of connection monitoring
        #################################################################
        
        # Initialize tracking for this IP if not exists
        if ip_address not in self.total_pings:
            self.total_pings[ip_address] = 0
            self.failed_pings[ip_address] = 0
        
        if ip_address not in self.failure_logged:
            self.failure_logged[ip_address] = False
            self.ip_status[ip_address] = True
            self.down_start_times[ip_address] = None
            
        consecutive_failures = 0
        consecutive_successes = 0
        last_success_log = 0
        ping_interval = 1.0
        first_ping = True
        
        while self.is_running:
            loop_start = time.time()
            
            # Increment total pings counter
            self.total_pings[ip_address] += 1
            
            # Use TCPing handler
            try:
                is_up, ping_time = self.ping_handler.ping_address(ip_address, ping_type)
            except Exception as e:
                self.log_event(f"Error pinging {ip_address}: {str(e)}")
                is_up = False
                ping_time = None
            
            current_time = time.time()
            
            if is_up:
                consecutive_successes += 1
                consecutive_failures = 0
                
                if not self.ip_status[ip_address] and consecutive_successes >= 2:  # Need 2 successful pings to confirm recovery
                    downtime = time.time() - self.down_start_times[ip_address]
                    downtime_str = self.format_duration(downtime)
                    self.log_event(f"{ping_type.upper()}:     Connection restored to {ip_address} - Response: {ping_time:.1f}ms (Down for {downtime_str})")
                    self.log_to_csv(
                        ping_type.upper(),
                        ip_address,
                        f"RESTORED after {downtime_str}",
                        ping_time,
                        self.get_network_type()
                    )
                    self.down_start_times[ip_address] = None
                    self.ip_status[ip_address] = True
                    self.failure_logged[ip_address] = False
                    self.update_status_indicator("up", ping_type)
                
                elif first_ping:  # Only log UP status on first ping
                    self.log_event(f"{ping_type.upper()}:     Response from {ip_address} - Response: {ping_time:.1f}ms")
                    self.log_to_csv(
                        ping_type.upper(),
                        ip_address,
                        "UP",
                        ping_time,
                        self.get_network_type()
                    )
                
                first_ping = False
                self.update_status_indicator("up", ping_type)
            else:
                consecutive_failures += 1
                consecutive_successes = 0
                self.failed_pings[ip_address] += 1
                
                if self.ip_status[ip_address] and consecutive_failures >= 3:  # Need 3 failures to confirm down
                    self.ip_status[ip_address] = False
                    self.down_start_times[ip_address] = current_time
                    if not self.failure_logged[ip_address]:
                        self.log_event(f"{ping_type.upper()}:     Connection LOST to {ip_address} at {datetime.now().strftime('%H:%M:%S')}")
                        self.log_to_csv(
                            ping_type.upper(),
                            ip_address,
                            "Connection LOST",
                            None,
                            self.get_network_type(),
                            skip_packet_loss=True
                        )
                        self.failure_logged[ip_address] = True
                    self.update_status_indicator("down", ping_type)
            
            # Sleep for remaining time
            elapsed = time.time() - loop_start
            if elapsed < ping_interval:
                time.sleep(ping_interval - elapsed)

        #################################################################
        # END OF CRITICAL SECTION - CORE PING BEHAVIOR
        #################################################################

    def update_start_button_state(self):
        """Enable start button only if at least one test is selected"""
        if self.gateway_check.get() or self.dns_check.get():
            self.start_button.configure(state="normal")
        else:
            self.start_button.configure(state="disabled")

    def cleanup_old_logs(self):
        """Remove CSV log files older than 7 days and clean memory"""
        try:
            current_time = datetime.now()
            for filename in os.listdir(self.logs_dir):
                if filename.endswith('.csv'):
                    filepath = os.path.join(self.logs_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    if current_time - file_time > timedelta(days=7):
                        try:
                            os.remove(filepath)
                        except:
                            continue
            
            # Memory cleanup
            import gc
            gc.collect()
        except Exception as e:
            print(f"Error cleaning up logs: {e}")

if __name__ == "__main__":
    # Check and set PowerShell execution policy if needed
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Try to get current execution policy
        check_cmd = ["powershell", "Get-ExecutionPolicy"]
        result = subprocess.run(check_cmd, capture_output=True, text=True, startupinfo=startupinfo)
        current_policy = result.stdout.strip()
        
        if current_policy in ["Restricted", "AllSigned"]:
            # Need admin rights to change policy
            if ctypes.windll.shell32.IsUserAnAdmin():
                set_cmd = ["powershell", "Set-ExecutionPolicy", "RemoteSigned", "-Force"]
                subprocess.run(set_cmd, startupinfo=startupinfo)
            else:
                messagebox.showwarning(
                    "PowerShell Policy", 
                    "Please run GPing as administrator for automatic gateway detection."
                )
    except Exception as e:
        print(f"Error checking PowerShell policy: {e}")
    
    # Set appearance mode and default color theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create and run the main window
    root = tk.Tk()
    app = PingTool(root)
    root.mainloop()
