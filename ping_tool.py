import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import time

class PingTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Ping Tool")

        self.ip_label = tk.Label(root, text="IP Address:")
        self.ip_label.pack(pady=5)

        self.ip_entry = tk.Entry(root)
        self.ip_entry.pack(pady=5)

        self.run_button = tk.Button(root, text="Run", command=self.start_ping)
        self.run_button.pack(pady=5)

        self.status_label = tk.Label(root, text="Status: Unknown", bg="grey")
        self.status_label.pack(pady=5, fill=tk.X)

        self.is_running = False
        self.last_status = None
        self.start_time = None

    def start_ping(self):
        ip_address = self.ip_entry.get()
        if not ip_address:
            messagebox.showwarning("Input Error", "Please enter an IP address.")
            return

        self.is_running = True
        self.run_button.config(state=tk.DISABLED)
        self.ping_thread = threading.Thread(target=self.ping, args=(ip_address,))
        self.ping_thread.start()

    def ping(self, ip_address):
        log_file = open("ping_log.txt", "a")
        while self.is_running:
            try:
                response = subprocess.run(["ping", "-n", "1", ip_address], capture_output=True, text=True)
                if "TTL=" in response.stdout:
                    self.update_status("up", log_file)
                else:
                    self.update_status("down", log_file)
            except Exception as e:
                self.update_status("error", log_file)
                print(f"Error: {e}")

            time.sleep(1)

        log_file.close()

    def update_status(self, status, log_file):
        if status == "up":
            if self.last_status != "up":
                self.status_label.config(text="Status: Up", bg="green")
                log_file.write(f"{time.ctime()}: Connection is up\n")
                self.last_status = "up"
                if self.start_time:
                    downtime = time.time() - self.start_time
                    log_file.write(f"{time.ctime()}: Connection restored, downtime was {downtime:.2f} seconds\n")
                    self.start_time = None
        elif status == "down":
            if self.last_status != "down":
                self.status_label.config(text="Status: Down", bg="red")
                log_file.write(f"{time.ctime()}: Connection lost\n")
                self.last_status = "down"
                self.start_time = time.time()
        else:
            self.status_label.config(text="Status: Error", bg="orange")
            log_file.write(f"{time.ctime()}: Error occurred\n")
            self.last_status = "error"

    def stop_ping(self):
        self.is_running = False
        self.run_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = PingTool(root)
    root.protocol("WM_DELETE_WINDOW", app.stop_ping)
    root.mainloop()
