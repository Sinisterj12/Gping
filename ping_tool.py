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
        self.gateway_down_start = None
        self.lan_down_start = None
        self.last_gateway_status = None
        self.last_lan_status = None
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize logging variables
        self.logs_dir = "logs"
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)

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
            
            with open(self.get_log_filename(), "a") as log_file:
                log_file.write(log_entry + "\n")
            
            # Update results text widget with new log entry
            self.results_text.insert("end", log_entry + "\n")
            self.results_text.see("end")  # Auto-scroll to bottom
            
        except Exception as e:
            print(f"Error writing to log: {e}")

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
        self.last_gateway_status = None
        self.last_lan_status = None
        self.gateway_down_start = None
        self.lan_down_start = None
        
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
            if self.gateway_down_start:
                downtime = self.format_duration(int(current_time - self.gateway_down_start))
                self.log_event(f"GATEWAY STATUS: Down for {downtime} when test stopped")
            if self.lan_down_start:
                downtime = self.format_duration(int(current_time - self.lan_down_start))
                self.log_event(f"LAN STATUS: Down for {downtime} when test stopped")
            
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
        consecutive_failures = 0
        last_success_log = 0
        ping_interval = 1.0  # Base interval between pings
        
        # Create startupinfo once for all ping commands
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        while self.is_running:
            loop_start = time.time()
            try:
                ping_process = subprocess.run(
                    ["ping", "-n", "1", "-w", "500", ip_address],  # Reduced timeout to 500ms
                    capture_output=True,
                    text=True,
                    timeout=1,  # Reduced overall timeout to 1 second
                    startupinfo=startupinfo  # Add startupinfo here
                )
                
                current_time = time.time()
                is_up = "bytes=" in ping_process.stdout
                ping_time = self.extract_ping_time(ping_process.stdout) if is_up else None
                
                if is_up:
                    consecutive_failures = 0
                    # Log successful pings every 5 minutes or after a failure
                    if current_time - last_success_log >= 300 or (
                        (ping_type == "gateway" and self.last_gateway_status == False) or 
                        (ping_type == "lan" and self.last_lan_status == False)
                    ):
                        self.log_event(f"{ping_type.upper()}: Response from {ip_address} - time={ping_time}ms")
                        last_success_log = current_time
                else:
                    consecutive_failures += 1
                
                if ping_type == "gateway":
                    if is_up != self.last_gateway_status:
                        if is_up:
                            if self.gateway_down_start:
                                downtime = max(1, int(current_time - self.gateway_down_start))  # Minimum 1 second
                                self.log_event(f"GATEWAY RESTORED: Connection to {ip_address} after {self.format_duration(downtime)} downtime")
                                self.gateway_down_start = None
                        else:
                            self.gateway_down_start = current_time
                            self.log_event(f"GATEWAY ALERT: Connection lost to {ip_address}")
                        self.last_gateway_status = is_up
                else:  # LAN
                    if is_up != self.last_lan_status:
                        if is_up:
                            if self.lan_down_start:
                                downtime = max(1, int(current_time - self.lan_down_start))  # Minimum 1 second
                                self.log_event(f"LAN RESTORED: Connection to {ip_address} after {self.format_duration(downtime)} downtime")
                                self.lan_down_start = None
                        else:
                            self.lan_down_start = current_time
                            self.log_event(f"LAN ALERT: Connection lost to {ip_address}")
                        self.last_lan_status = is_up
                
                # Log warning if multiple consecutive failures
                if consecutive_failures == 3:
                    self.log_event(f"WARNING: {ping_type.upper()} connection showing intermittent failures")
                
                # Update status indicator
                self.root.after(0, lambda: self.update_status_indicator(
                    "up" if is_up else "down", ping_type))
                
            except subprocess.TimeoutExpired:
                consecutive_failures += 1
                current_time = time.time()
                
                if ping_type == "gateway" and self.last_gateway_status != False:
                    self.gateway_down_start = current_time
                    self.log_event(f"GATEWAY CRITICAL: Connection timeout to {ip_address}")
                    self.last_gateway_status = False
                elif ping_type == "lan" and self.last_lan_status != False:
                    self.lan_down_start = current_time
                    self.log_event(f"LAN CRITICAL: Connection timeout to {ip_address}")
                    self.last_lan_status = False
                
                self.root.after(0, lambda: self.update_status_indicator("down", ping_type))
            
            except Exception as e:
                self.log_event(f"ERROR: {ping_type.upper()} test failed - {str(e)}")
                self.root.after(0, lambda: self.update_status_indicator("down", ping_type))
            
            # Calculate sleep time to maintain consistent intervals
            elapsed = time.time() - loop_start
            sleep_time = max(0, ping_interval - elapsed)
            time.sleep(sleep_time)

    def load_settings(self):
        self.saved_settings = {}
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.saved_settings = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def on_closing(self):
        if self.is_running:
            self.stop_ping()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PingTool(root)
    root.mainloop()
