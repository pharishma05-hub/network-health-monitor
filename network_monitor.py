"""
Network Health Monitor
Pings several targets at a fixed interval and logs latency / packet loss to a CSV.
Works on Windows, macOS and Linux. Stop any time with Ctrl+C.
"""

import csv
import platform
import re
import subprocess
import time
from datetime import datetime

# ---- Settings you can change ----
TARGETS = {
    "Router (gateway)": "192.168.1.1",   # change to your router IP
    "Google DNS": "8.8.8.8",
    "Cloudflare DNS": "1.1.1.1",
    "Google": "google.com",
    "YouTube": "youtube.com",
    "GitHub": "github.com",
}
INTERVAL_SECONDS = 5        # time between rounds of pings
DURATION_MINUTES = 30       # how long to run
OUTPUT_FILE = "network_log.csv"
# ---------------------------------

IS_WINDOWS = platform.system().lower() == "windows"


def ping_once(host):
    """Send one ping. Returns latency in ms, or None if it failed."""
    cmd = ["ping", "-n", "1", host] if IS_WINDOWS else ["ping", "-c", "1", host]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    except subprocess.TimeoutExpired:
        return None

    if result.returncode != 0:
        return None

    # Matches "time=23.4 ms", "time=23ms" and "time<1ms"
    match = re.search(r"time[=<]\s*([\d.]+)\s*ms", result.stdout)
    if match:
        return float(match.group(1))
    return None


def main():
    gateway = input(f"Router IP [{TARGETS['Router (gateway)']}]: ").strip()
    if gateway:
        TARGETS["Router (gateway)"] = gateway

    end_time = time.time() + DURATION_MINUTES * 60
    print(f"Monitoring {len(TARGETS)} targets for {DURATION_MINUTES} minutes. Ctrl+C to stop early.\n")

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "target_name", "host", "status", "latency_ms"])

        try:
            while time.time() < end_time:
                stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for name, host in TARGETS.items():
                    latency = ping_once(host)
                    if latency is None:
                        status, shown = "LOST", ""
                        print(f"{stamp} | {name:<18} | LOST")
                    else:
                        status, shown = "OK", latency
                        print(f"{stamp} | {name:<18} | {latency} ms")
                    writer.writerow([stamp, name, host, status, shown])
                f.flush()
                time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nStopped early by user.")

    print(f"\nDone. Data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
