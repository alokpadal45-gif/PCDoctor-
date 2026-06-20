# This module collects real-time hardware stats from the computer.
# It uses the psutil library which works on Windows, Linux, and Mac.
# Every other module that needs hardware numbers imports from here.

import psutil
import platform
import datetime


def get_system_info():
    # We build a dictionary and fill it section by section.
    # The frontend reads this dictionary to display the live stats bar.
    info = {}

    # Basic operating system details
    info["os"] = platform.system()
    info["os_version"] = platform.version()
    info["hostname"] = platform.node()

    # CPU usage - interval=1 means psutil waits 1 second for an accurate reading
    info["cpu_percent"] = psutil.cpu_percent(interval=1)
    info["cpu_count"] = psutil.cpu_count(logical=True)
    info["cpu_freq"] = get_cpu_freq()

    # RAM usage
    ram = psutil.virtual_memory()
    info["ram_total_gb"] = round(ram.total / (1024 ** 3), 2)
    info["ram_used_gb"] = round(ram.used / (1024 ** 3), 2)
    info["ram_percent"] = ram.percent

    # Disk usage - Windows uses C:\ and Linux/Mac uses /
    if platform.system() == "Windows":
        disk_path = "C:\\"
    else:
        disk_path = "/"

    disk = psutil.disk_usage(disk_path)
    info["disk_total_gb"] = round(disk.total / (1024 ** 3), 2)
    info["disk_used_gb"] = round(disk.used / (1024 ** 3), 2)
    info["disk_percent"] = disk.percent

    # Battery - desktop computers do not have one so we handle that case
    battery = psutil.sensors_battery()
    if battery:
        info["battery_percent"] = battery.percent
        info["battery_plugged"] = battery.power_plugged
        if battery.secsleft > 0:
            info["battery_minutes"] = round(battery.secsleft / 60, 1)
        else:
            info["battery_minutes"] = "Charging"
    else:
        info["battery_percent"] = None
        info["battery_plugged"] = None
        info["battery_minutes"] = None

    # Temperature - not every system exposes this, so we handle failure quietly
    info["temperature_c"] = get_temperature()

    # Current time so the frontend can show when the stats were last refreshed
    info["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return info


def get_cpu_freq():
    # Some virtual machines and older systems do not expose CPU frequency
    try:
        freq = psutil.cpu_freq()
        if freq:
            return round(freq.current, 1)
        return None
    except Exception:
        return None


def get_temperature():
    # Temperature sensors are not available on all platforms.
    # On Windows you usually need extra drivers.
    # On Linux it works well on most hardware.
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        # Check the most common sensor names used by different hardware vendors
        for sensor_name in ("coretemp", "cpu_thermal", "k10temp", "acpitz"):
            if sensor_name in temps:
                return round(temps[sensor_name][0].current, 1)
        # If none of those matched, just return the first reading we find
        first_group = next(iter(temps.values()))
        return round(first_group[0].current, 1)
    except Exception:
        return None