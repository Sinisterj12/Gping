import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import subprocess
import threading
import time
import json
import os
import psutil
import socket
import re
from datetime import datetime, timedelta
import csv

#################################################################
# CORE FUNCTIONALITY - MODIFY ONLY WHEN CHANGING PING BEHAVIOR
#################################################################

class TCPingHandler:
    """TCPing implementation for network connectivity testing"""
    def __init__(self, tcping_path="tcping.exe"):
        self.tcping_path = tcping_path
        if not os.path.exists(self.tcping_path):
            raise FileNotFoundError(f"Error: {self.tcping_path} not found in the application directory")
        
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
# GUI IMPLEMENTATION - DO NOT MODIFY UNLESS EXPLICITLY REQUESTED
# These sections handle the graphical interface and should remain intact
#################################################################

class PingTool:
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
            
        # Use system appearance mode
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        
        self.settings_file = "gping_settings.json"
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
        
        # Create logs directory
        self.logs_dir = "logs"
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
            
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
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'Timestamp',
                    'Event Type',
                    'IP Address',
                    'Status',
                    'Response Time',
                    'Network Type',
                    'Packet Loss %'
                ])

    def calculate_packet_loss(self, ip_address):
        """Calculate packet loss percentage for an IP"""
        if ip_address not in self.total_pings:
            self.total_pings[ip_address] = 0
            self.failed_pings[ip_address] = 0
        
        if self.total_pings[ip_address] == 0:
            return 0.0
            
        return round((self.failed_pings[ip_address] / self.total_pings[ip_address]) * 100, 1)

    def log_to_csv(self, event_type, ip_address, status, response_time=None, network_type=None, details=None):
        """Log events to CSV file"""
        try:
            response_time_str = f"{response_time:.3f}ms" if response_time is not None else ''
            packet_loss = f"{self.calculate_packet_loss(ip_address)}%"
            
            with open(self.csv_filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Timestamp
                    event_type,                                     # Event Type
                    ip_address,                                     # IP Address
                    status,                                        # Status
                    response_time_str,                             # Response Time
                    network_type if network_type is not None else '',  # Network Type
                    packet_loss                                    # Packet Loss %
                ])
        except Exception as e:
            print(f"Error writing to CSV: {str(e)}")

    def ping(self, ip_address, ping_type):
        """Execute ping tests for a given IP address"""
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
            is_up, ping_time = self.ping_handler.ping_address(ip_address, ping_type)
            current_time = time.time()
            
            if is_up:
                consecutive_successes += 1
                consecutive_failures = 0
                
                if not self.ip_status[ip_address] and consecutive_successes >= 2:  # Need 2 successful pings to confirm recovery
                    self.log_event(f"{ping_type.upper()}: Connection restored to {ip_address} - time={ping_time}ms")
                    self.log_to_csv(
                        ping_type.upper(),
                        ip_address,
                        "RESTORED",
                        ping_time,
                        self.get_network_type()
                    )
                    self.down_start_times[ip_address] = None
                    self.ip_status[ip_address] = True
                    self.failure_logged[ip_address] = False
                
                elif first_ping or current_time - last_success_log >= 300:
                    self.log_event(f"{ping_type.upper()}: Response from {ip_address} - time={ping_time}ms")
                    self.log_to_csv(
                        ping_type.upper(),
                        ip_address,
                        "UP",
                        ping_time,
                        self.get_network_type()
                    )
                    last_success_log = current_time
                
                first_ping = False
                self.root.after(0, lambda: self.update_status_indicator("up", ping_type))
            else:
                consecutive_failures += 1
                consecutive_successes = 0
                self.failed_pings[ip_address] += 1
                
                if self.ip_status[ip_address] and consecutive_failures >= 3:  # Need 3 failures to confirm down
                    self.ip_status[ip_address] = False
                    self.down_start_times[ip_address] = current_time
                    if not self.failure_logged[ip_address]:
                        self.log_event(f"{ping_type.upper()} ALERT: Connection lost to {ip_address}")
                        self.log_to_csv(
                            ping_type.upper(),
                            ip_address,
                            "ALERT",
                            None,
                            self.get_network_type()
                        )
                        self.failure_logged[ip_address] = True
                
                self.root.after(0, lambda: self.update_status_indicator("down", ping_type))
            
            # Sleep for remaining time
            elapsed = time.time() - loop_start
            if elapsed < ping_interval:
                time.sleep(ping_interval - elapsed)

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
        """Create the network profile section"""
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
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            profile = result.stdout.strip()
            
            # Get network adapter info
            cmd_adapter = ["powershell", "-Command", 
                         "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -First 1 | Select-Object -ExpandProperty Name"]
            adapter_result = subprocess.run(cmd_adapter, capture_output=True, text=True, startupinfo=startupinfo)
            adapter_name = adapter_result.stdout.strip()
            
            if profile == "DomainAuthenticated":
                color = "#00B050"  # Green
                text = f"Network Profile: Work Network ({adapter_name})"
            else:
                color = "#FF0000"  # Red
                text = f"Warning: {profile} Network ({adapter_name})"
            
            self.network_label.configure(text=text, text_color=color)
        except Exception as e:
            self.network_label.configure(text=f"Error checking network: {str(e)}", 
                                       text_color="#FF0000")

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
        ctk.CTkLabel(gateway_frame, text="Gateway IP:", 
                    font=ctk.CTkFont(size=12), width=80).pack(side="left", padx=5)
        
        self.gateway_ip_entry = ctk.CTkEntry(gateway_frame, width=200)
        self.gateway_ip_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(gateway_frame, text="Save", 
                     command=lambda: self.save_single_ip("gateway"),
                     width=60).pack(side="left", padx=5)
        
        self.gateway_indicator = ctk.CTkLabel(gateway_frame, text="⬤", 
                                            text_color="gray")
        self.gateway_indicator.pack(side="right", padx=5)
        
        self.gateway_status = ctk.CTkLabel(gateway_frame, text="Not Running",
                                         font=ctk.CTkFont(size=12), width=150)
        self.gateway_status.pack(side="right", padx=5)
        
        # LAN IP row
        ctk.CTkLabel(lan_frame, text="LAN IP:", 
                    font=ctk.CTkFont(size=12), width=80).pack(side="left", padx=5)
        
        self.lan_ip_entry = ctk.CTkEntry(lan_frame, width=200)
        self.lan_ip_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(lan_frame, text="Save", 
                     command=lambda: self.save_single_ip("lan"),
                     width=60).pack(side="left", padx=5)
        
        self.lan_indicator = ctk.CTkLabel(lan_frame, text="⬤", 
                                        text_color="gray")
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

            # Get default gateway
            cmd = ["powershell", "-Command", 
                  "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -First 1).NextHop"]
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            gateway = result.stdout.strip()
            if gateway:
                self.gateway_ip_entry.delete(0, tk.END)
                self.gateway_ip_entry.insert(0, gateway)
            
            # Only set LAN IP if not already saved
            if not self.saved_settings.get('lan_ip'):
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                if local_ip:
                    self.lan_ip_entry.delete(0, tk.END)
                    self.lan_ip_entry.insert(0, local_ip)
            else:
                self.lan_ip_entry.delete(0, tk.END)
                self.lan_ip_entry.insert(0, self.saved_settings['lan_ip'])
        except Exception as e:
            print(f"Error detecting IP addresses: {e}")

    def create_control_frame(self):
        """Create the control buttons section"""
        control_frame = ctk.CTkFrame(self.main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        self.start_button = ctk.CTkButton(control_frame, text="Start Tests", 
                                        command=self.start_ping)
        self.start_button.pack(side="left", padx=5, pady=5)
        
        self.stop_button = ctk.CTkButton(control_frame, text="Stop Tests", 
                                       command=self.stop_ping, state="disabled")
        self.stop_button.pack(side="left", padx=5, pady=5)

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

    def update_status_indicator(self, status, ping_type):
        """Update the status indicators in the GUI"""
        indicator = self.gateway_indicator if ping_type == "gateway" else self.lan_indicator
        status_label = self.gateway_status if ping_type == "gateway" else self.lan_status
        
        if status == "up":
            color = "#00B050"  # Green
            text = "Connected"
        elif status == "down":
            color = "#FF0000"  # Red
            text = "Disconnected"
        elif status == "starting":
            color = "#FFA500"  # Yellow
            text = "Starting..."
        else:
            color = "gray"
            text = "Not Running"
            
        indicator.configure(text_color=color)
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
        gateway_ip_address = self.gateway_ip_entry.get()
        lan_ip_address = self.lan_ip_entry.get()
        
        if not gateway_ip_address:
            messagebox.showwarning("Input Error", "Please enter the Gateway IP address.")
            return
            
        self.is_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        
        # Reset counters for new test
        self.total_pings = {}
        self.failed_pings = {}
        
        # Log test start
        self.log_event("=== Network Connection Test Started ===")
        if gateway_ip_address:
            self.log_event(f"Testing Gateway IP: {gateway_ip_address}")
        if lan_ip_address:
            self.log_event(f"Testing LAN IP: {lan_ip_address}")
        
        # Reset status tracking
        self.last_csv_log_time = 0
        
        # Start gateway thread
        self.update_status_indicator("starting", "gateway")
        self.gateway_ping_thread = threading.Thread(target=self.ping, 
                                                  args=(gateway_ip_address, "gateway"))
        self.gateway_ping_thread.daemon = True
        self.gateway_ping_thread.start()
        
        # Start LAN thread if IP provided
        if lan_ip_address:
            self.update_status_indicator("starting", "lan")
            self.lan_ping_thread = threading.Thread(target=self.ping, 
                                                  args=(lan_ip_address, "lan"))
            self.lan_ping_thread.daemon = True
            self.lan_ping_thread.start()
        else:
            self.update_status_indicator("not_running", "lan")

    def stop_ping(self):
        """Stop the ping tests"""
        if self.is_running:
            self.is_running = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            
            # Log final status
            self.log_event("=== Network Connection Test Stopped ===")
            
            # Reset status indicators
            self.update_status_indicator("not_running", "gateway")
            self.update_status_indicator("not_running", "lan")
            
            # Clear threads
            if hasattr(self, 'gateway_ping_thread'):
                self.gateway_ping_thread = None
            if hasattr(self, 'lan_ping_thread'):
                self.lan_ping_thread = None

    def log_event(self, message):
        """Log events to GUI and file"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format the log entry
            if message.startswith("==="):
                log_entry = f"\n{timestamp} - {message}\n{'=' * 50}"
            elif "Testing" in message:
                log_entry = f"{timestamp} - {message}\n{'-' * 50}"
            else:
                # Pad GATEWAY and LAN with smaller width
                message = message.replace("GATEWAY:", "GATEWAY:".ljust(8))
                message = message.replace("LAN:", "LAN:".ljust(8))
                
                # Align ALERT messages with reduced padding
                message = message.replace("GATEWAY ALERT:", "GATEWAY:".ljust(8) + "ALERT:")
                message = message.replace("LAN ALERT:", "LAN:".ljust(8) + "ALERT:")
                
                # Pad IP addresses with smaller width
                if "192.168.1.254" in message:
                    message = message.replace("192.168.1.254", "192.168.1.254".ljust(13))
                if "8.8.8.8" in message:
                    message = message.replace("8.8.8.8", "8.8.8.8".ljust(13))
                
                log_entry = f"{timestamp} - {message}"
            
            # Update GUI
            self.results_text.insert("end", log_entry + "\n")
            self.results_text.see("end")
            
        except Exception as e:
            print(f"Error writing to log: {e}")

    def format_duration(self, seconds):
        """Format duration in a human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        
        duration = timedelta(seconds=seconds)
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

if __name__ == "__main__":
    root = tk.Tk()
    app = PingTool(root)
    root.mainloop()
