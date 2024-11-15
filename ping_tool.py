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

class PingTool:
    def __init__(self, root):
        self.root = root
        self.root.title("GPing by James")
        
        # Use system appearance mode
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        
        self.settings_file = "gping_settings.json"
        self.load_settings()
        
        self.root.geometry("650x550")
        self.root.minsize(650, 550)
        
        # Main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create network profile section
        self.create_network_frame()
        
        # Create IP input section
        self.create_ip_frame()
        
        # Create control buttons
        self.create_control_frame()
        
        # Create results section
        self.create_results_frame()
        
        self.is_running = False
        self.last_csv_log_time = 0
        self.csv_log_interval = 300  # Log successful pings every 5 minutes
        self.failure_logged = {}  # Track failures per IP address
        self.ip_status = {}  # Track status per IP address
        self.down_start_times = {}  # Track down start times per IP
        self.total_downtime = {}  # Track total downtime per IP
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize logging variables
        self.current_date = datetime.now().strftime('%m%d%Y')
        self.csv_filename = f"GPing{self.current_date}.csv"
        self.logs_dir = "logs"  # Add this back
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        self.init_csv_log()
        
    def create_network_frame(self):
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
        try:
            # Use CREATE_NO_WINDOW flag to hide PowerShell window
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
        try:
            # Use CREATE_NO_WINDOW flag to hide PowerShell window
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
        control_frame = ctk.CTkFrame(self.main_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        self.start_button = ctk.CTkButton(control_frame, text="Start Tests", 
                                        command=self.start_ping)
        self.start_button.pack(side="left", padx=5, pady=5)
        
        self.stop_button = ctk.CTkButton(control_frame, text="Stop Tests", 
                                       command=self.stop_ping, state="disabled")
        self.stop_button.pack(side="left", padx=5, pady=5)

    def create_results_frame(self):
        # Results Frame
        results_frame = ctk.CTkFrame(self.main_frame)
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Title
        ctk.CTkLabel(results_frame, text="Connection Log", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        # Results Text Area
        self.results_text = ctk.CTkTextbox(results_frame, wrap="word",
                                         font=ctk.CTkFont(family="Consolas", size=11))
        self.results_text.pack(fill="both", expand=True, padx=5, pady=5)

    def get_log_filename(self):
        """Generate log filename based on current date"""
        return os.path.join(self.logs_dir, f"GPing{datetime.now().strftime('%m%d%Y')}.log")

    def log_event(self, message, ping_type=None, status_change=False):
        """Log events with timestamp, avoiding redundant entries"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format the log entry based on type
            if message.startswith("==="):
                # Section headers
                log_entry = f"\n{timestamp} - {message}\n{'=' * 50}"
            elif "Testing" in message:
                # IP test announcements
                log_entry = f"{timestamp} - {message}\n{'-' * 50}"
            else:
                # Regular entries
                log_entry = f"{timestamp} - {message}"
            
            # Write to the current day's log file
            log_path = os.path.join(self.logs_dir, f"GPing{self.current_date}.log")
            with open(log_path, "a") as log_file:
                log_file.write(log_entry + "\n")
            
            # Update results text widget with new log entry
            self.results_text.insert("end", log_entry + "\n")
            self.results_text.see("end")  # Auto-scroll to bottom
            
        except Exception as e:
            print(f"Error writing to log: {e}")

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
                    'Response Time (ms)',
                    'Network Type',
                    'Details'
                ])

    def log_to_csv(self, event_type, ip_address, status, response_time=None, network_type=None, details=None):
        """Log events to CSV file"""
        try:
            with open(self.csv_filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    event_type,
                    ip_address,
                    status,
                    response_time if response_time is not None else '',
                    network_type if network_type is not None else '',
                    details if details is not None else ''
                ])
        except Exception as e:
            print(f"Error writing to CSV: {str(e)}")

    def extract_ping_time(self, ping_output):
        """Extract ping time from ping command output"""
        try:
            time_match = re.search(r"time[=<](\d+)ms", ping_output)
            if time_match:
                return int(time_match.group(1))
            return None
        except:
            return None

    def format_duration(self, seconds):
        """Format duration in a human-readable format"""
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

    def update_status_indicator(self, status, ping_type):
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
        gateway_ip_address = self.gateway_ip_entry.get()
        lan_ip_address = self.lan_ip_entry.get()
        
        if not gateway_ip_address:
            messagebox.showwarning("Input Error", "Please enter the Gateway IP address.")
            return
            
        self.is_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        
        # Log test start with clear formatting
        self.log_event("=== Network Connection Test Started ===")
        if gateway_ip_address:
            self.log_event(f"Testing Gateway IP: {gateway_ip_address}")
        if lan_ip_address:
            self.log_event(f"Testing LAN IP: {lan_ip_address}")
        
        # Reset status tracking
        self.last_csv_log_time = 0
        
        # Update status to starting (yellow)
        self.update_status_indicator("starting", "gateway")
        self.gateway_ping_thread = threading.Thread(target=self.ping, 
                                                  args=(gateway_ip_address, "gateway"))
        self.gateway_ping_thread.daemon = True
        self.gateway_ping_thread.start()
        
        if lan_ip_address:
            self.update_status_indicator("starting", "lan")
            self.lan_ping_thread = threading.Thread(target=self.ping, 
                                                  args=(lan_ip_address, "lan"))
            self.lan_ping_thread.daemon = True
            self.lan_ping_thread.start()
        else:
            self.update_status_indicator("not_running", "lan")

    def stop_ping(self):
        if self.is_running:
            self.is_running = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            
            # Log final status if there were ongoing issues
            current_time = time.time()
            for ip_address in self.down_start_times:
                if self.down_start_times[ip_address]:
                    downtime = self.format_duration(int(current_time - self.down_start_times[ip_address]))
                    self.log_event(f"{ip_address.upper()} STATUS: Down for {downtime} when test stopped")
            
            self.log_event("=== Network Connection Test Stopped ===")
            
            # Reset status indicators
            self.update_status_indicator("not_running", "gateway")
            self.update_status_indicator("not_running", "lan")
            
            # Clear any existing threads
            if hasattr(self, 'gateway_ping_thread'):
                self.gateway_ping_thread = None
            if hasattr(self, 'lan_ping_thread'):
                self.lan_ping_thread = None

    def ping(self, ip_address, ping_type):
        # Initialize status tracking for this IP if not exists
        if ip_address not in self.failure_logged:
            self.failure_logged[ip_address] = False
            self.ip_status[ip_address] = True  # Assume up initially
            self.down_start_times[ip_address] = None
            self.total_downtime[ip_address] = 0
            
        consecutive_failures = 0
        last_success_log = 0
        ping_interval = 1.0
        first_ping = True  # Track if this is the first ping
        
        # Create startupinfo once for all ping commands
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        while self.is_running:
            # Check if date has changed and update log file if needed
            current_date = datetime.now().strftime('%m%d%Y')
            if current_date != self.current_date:
                self.current_date = current_date
                self.csv_filename = f"GPing{self.current_date}.csv"
                self.init_csv_log()
            
            loop_start = time.time()
            try:
                ping_process = subprocess.run(
                    ["ping", "-n", "1", "-w", "500", ip_address],
                    capture_output=True,
                    text=True,
                    timeout=1,
                    startupinfo=startupinfo
                )
                
                current_time = time.time()
                is_up = "bytes=" in ping_process.stdout
                ping_time = self.extract_ping_time(ping_process.stdout) if is_up else None
                
                if is_up:
                    consecutive_failures = 0
                    self.failure_logged[ip_address] = False  # Reset failure logging flag for this IP
                    
                    # Check if we're recovering from a down state
                    if not self.ip_status[ip_address]:
                        if self.down_start_times[ip_address]:
                            downtime = max(1, int(current_time - self.down_start_times[ip_address]))
                            self.total_downtime[ip_address] += downtime
                            self.log_event(f"{ping_type.upper()}: Connection restored to {ip_address} after {self.format_duration(downtime)} downtime (Total downtime: {self.format_duration(self.total_downtime[ip_address])}) - time={ping_time}ms")
                            self.log_to_csv(
                                ping_type.upper(),
                                ip_address,
                                "RESTORED",
                                ping_time,
                                self.get_network_type(),
                                f"Downtime: {self.format_duration(downtime)} (Total: {self.format_duration(self.total_downtime[ip_address])})"
                            )
                            self.down_start_times[ip_address] = None
                    # Always log the first successful ping
                    elif first_ping or current_time - last_success_log >= 300:
                        self.log_event(f"{ping_type.upper()}: Response from {ip_address} - time={ping_time}ms")
                    
                    first_ping = False
                        
                    # Only log to CSV on status change or interval
                    if current_time - self.last_csv_log_time >= self.csv_log_interval or not self.ip_status[ip_address]:
                        if not self.ip_status[ip_address]:  # If recovering from down state
                            if self.down_start_times[ip_address]:
                                downtime = max(1, int(current_time - self.down_start_times[ip_address]))
                                self.log_to_csv(
                                    ping_type.upper(),
                                    ip_address,
                                    "RESTORED",
                                    ping_time,
                                    self.get_network_type(),
                                    f"Downtime: {self.format_duration(downtime)}"
                                )
                                self.down_start_times[ip_address] = None
                        else:  # Regular interval update
                            self.log_to_csv(
                                ping_type.upper(),
                                ip_address,
                                "UP",
                                ping_time,
                                self.get_network_type(),
                                f"Response time: {ping_time}ms"
                            )
                        self.last_csv_log_time = current_time
                    last_success_log = current_time
                    self.ip_status[ip_address] = True
                else:
                    consecutive_failures += 1
                    if first_ping:
                        self.log_event(f"{ping_type.upper()}: No response from {ip_address}")
                        first_ping = False
                        
                    if self.ip_status[ip_address] and consecutive_failures >= 3:  # Just went down
                        self.ip_status[ip_address] = False
                        self.down_start_times[ip_address] = current_time
                        self.log_event(f"{ping_type.upper()} ALERT: Connection lost to {ip_address}")
                        self.log_to_csv(
                            ping_type.upper(),
                            ip_address,
                            "ALERT",
                            None,
                            self.get_network_type(),
                            "Connection lost"
                        )
                    # Only log the initial failure after 3 attempts
                    elif consecutive_failures >= 3 and not self.failure_logged[ip_address]:
                        self.log_to_csv(
                            ping_type.upper(),
                            ip_address,
                            "DOWN",
                            None,
                            self.get_network_type(),
                            f"No response after {consecutive_failures} attempts"
                        )
                        self.failure_logged[ip_address] = True  # Set flag for this IP
                
                # Update UI status
                if ping_type == "gateway":
                    self.last_gateway_status = is_up
                else:  # LAN
                    self.last_lan_status = is_up
                
                # Update status indicator
                self.root.after(0, lambda: self.update_status_indicator(
                    "up" if is_up else "down", ping_type))

                # Sleep for remaining time to maintain 1 second interval
                elapsed = time.time() - loop_start
                if elapsed < ping_interval:
                    time.sleep(ping_interval - elapsed)
                    
            except subprocess.TimeoutExpired:
                if first_ping:
                    self.log_event(f"{ping_type.upper()}: Connection timeout to {ip_address}")
                    first_ping = False
                
                if not self.failure_logged[ip_address]:
                    self.log_to_csv(
                        ping_type.upper(),
                        ip_address,
                        "DOWN",
                        None,
                        self.get_network_type(),
                        "Ping timeout"
                    )
                    self.failure_logged[ip_address] = True
                
                # Update UI status
                if ping_type == "gateway":
                    self.last_gateway_status = False
                else:  # LAN
                    self.last_lan_status = False
                
                # Update status indicator
                self.root.after(0, lambda: self.update_status_indicator("down", ping_type))

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

if __name__ == "__main__":
    root = tk.Tk()
    app = PingTool(root)
    root.mainloop()
