# Diagnostic checks for problems 15 to 20.
# These are: Fingerprint, Auto Screenshot, Overheating,
# Battery Drain, Freezing, Data Recovery.

import subprocess
import platform
import psutil


def make_result(status, message, details, can_auto_fix):
    return {"status": status, "message": message, "details": details, "can_auto_fix": can_auto_fix}


# Problem 15 - Fingerprint Detection
# We check the Biometric device class in Windows Device Manager.
def check_fingerprint():
    details = []

    if platform.system() == "Windows":
        try:
            cmd = ('powershell -Command "Get-PnpDevice | '
                   'Where-Object { $_.Class -eq \'Biometric\' } | '
                   'Select-Object Status, FriendlyName | ConvertTo-Json"')
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=15)
            output = output.decode(errors="ignore")

            if not output.strip() or output.strip() == "null":
                details.append("No biometric device found.")
                return make_result("critical", "Fingerprint sensor not found.", details, False)

            details.append(output[:400])
            if "Error" in output:
                return make_result("critical", "Fingerprint sensor has an error.", details, True)
            return make_result("ok", "Fingerprint sensor detected.", details, False)

        except Exception as e:
            details.append(f"Could not query biometric devices: {e}")

    details.append("Manual path: Settings > Sign-in options > Windows Hello Fingerprint.")
    return make_result("warning", "Automated fingerprint check not available.", details, False)


# Problem 16 - Auto Screenshot
# We look for scheduled tasks with screenshot-related names.
# Legitimate software rarely silently schedules screen captures.
def check_auto_screenshot():
    details = []

    if platform.system() == "Windows":
        try:
            cmd = ('powershell -Command "Get-ScheduledTask | '
                   'Where-Object { $_.TaskName -like \'*screen*\' -or $_.TaskName -like \'*capture*\' } | '
                   'Select-Object TaskName, State | ConvertTo-Json"')
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=15)
            output = output.decode(errors="ignore")

            if output.strip() and output.strip() != "null":
                details.append("Screenshot-related scheduled tasks found:")
                details.append(output[:400])
                return make_result("warning", "Suspicious screenshot task(s) found. Check for spyware.", details, True)

            details.append("No suspicious screenshot tasks in Task Scheduler.")
            return make_result("ok", "No auto-screenshot tasks detected.", details, False)

        except Exception as e:
            details.append(f"Could not check scheduled tasks: {e}")

    details.append("Also check: Task Scheduler, startup programs, browser extensions.")
    return make_result("warning", "Full check not available on this platform.", details, False)


# Problem 17 - Overheating
# We read CPU temperature from psutil sensor data.
# Above 75C is a warning. Above 90C is dangerous.
def check_overheating():
    details = []

    try:
        temps = psutil.sensors_temperatures()

        if not temps:
            details.append("Temperature sensors not available on this system.")
            details.append("Physically check: is the fan spinning? Are the vents clear?")
            return make_result("warning", "Cannot read temperature on this machine.", details, False)

        for sensor_name, entries in temps.items():
            for entry in entries:
                label = entry.label if entry.label else "CPU"
                details.append(f"{sensor_name} - {label}: {entry.current} C (critical: {entry.critical} C)")

                if entry.current >= 90:
                    return make_result("critical", f"Critical temperature: {entry.current} C. Hardware damage risk.", details, True)
                if entry.current >= 75:
                    return make_result("warning", f"High temperature: {entry.current} C. Clean fan and vents.", details, True)

        return make_result("ok", "Temperature is within safe limits.", details, False)

    except Exception as e:
        details.append(f"Temperature read failed: {e}")
        return make_result("warning", "Could not read temperature data.", details, False)


# Problem 18 - Battery Drain
# We check the battery percentage and whether it is charging or discharging.
def check_battery_drain():
    details = []
    battery = psutil.sensors_battery()

    if not battery:
        details.append("No battery found. This is likely a desktop PC.")
        return make_result("ok", "No battery present.", details, False)

    pct = battery.percent
    status = "Charging" if battery.power_plugged else "Discharging"
    details.append(f"Battery: {pct}% - {status}")

    if pct < 10 and not battery.power_plugged:
        return make_result("critical", f"Battery critically low at {pct}%. Plug in immediately.", details, False)
    if pct < 20 and not battery.power_plugged:
        return make_result("warning", f"Battery low at {pct}%.", details, True)
    if platform.system() == "Windows":
        details.append("Run 'powercfg /batteryreport' in Command Prompt for full battery health.")
    return make_result("ok", f"Battery at {pct}%. No issues.", details, False)


# Problem 19 - Freezing / Hanging Screen
# High CPU + high RAM together is the most common software cause of freezing.
def check_freezing():
    details = []
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk_io = psutil.disk_io_counters()

    details.append(f"CPU: {cpu}%  |  RAM: {ram}%")

    if disk_io:
        read_mb = round(disk_io.read_bytes / 1024**2, 1)
        write_mb = round(disk_io.write_bytes / 1024**2, 1)
        details.append(f"Disk I/O since boot - Read: {read_mb} MB, Write: {write_mb} MB")

    if cpu > 90 and ram > 85:
        return make_result("critical", "CPU and RAM both maxed out. Freezing is expected.", details, True)
    if cpu > 80 or ram > 80:
        return make_result("warning", "High system load. Freezing is possible.", details, True)
    return make_result("ok", "No obvious freeze conditions right now.", details, False)


# Problem 20 - Data Recovery
# We use WMIC on Windows to check disk SMART status.
# A "Pred Fail" result means the drive is about to die.
def check_data_recovery():
    details = []

    if platform.system() == "Windows":
        try:
            cmd = "wmic diskdrive get Status,Model,Size /format:list"
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=15)
            output = output.decode(errors="ignore")
            details.append("Disk status from WMIC:")
            details.append(output[:500])

            if "Pred Fail" in output or "Bad" in output:
                return make_result("critical", "Disk predicting failure. Back up data immediately.", details, False)
            return make_result("ok", "Disk SMART status is OK.", details, False)

        except Exception as e:
            details.append(f"WMIC query failed: {e}")

    try:
        result = subprocess.run(["smartctl", "-H", "/dev/sda"], capture_output=True, text=True, timeout=15)
        output = result.stdout
        details.append(output[:400])
        if "PASSED" in output:
            return make_result("ok", "SMART health test passed.", details, False)
        return make_result("critical", "SMART test failed. Disk may be failing.", details, False)
    except FileNotFoundError:
        details.append("smartmontools not installed. Run: sudo apt install smartmontools")
    except Exception as e:
        details.append(f"smartctl error: {e}")

    return make_result("warning", "Could not read full disk health data.", details, False)