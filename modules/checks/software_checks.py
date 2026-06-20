# Diagnostic checks for problems 10 to 14.
# These are: Slow Performance, File Not Responding, Screensaver,
# Update Failure, Camera.

import subprocess
import platform
import psutil


def make_result(status, message, details, can_auto_fix):
    return {"status": status, "message": message, "details": details, "can_auto_fix": can_auto_fix}


# Problem 10 - Slow Performance
# High CPU or high RAM both cause the system to feel slow.
# We also count running processes as a useful indicator.
def check_slow_performance():
    details = []
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    process_count = len(psutil.pids())

    details.append(f"CPU usage: {cpu}%")
    details.append(f"RAM usage: {ram}%")
    details.append(f"Running processes: {process_count}")

    if cpu > 90 or ram > 90:
        return make_result("critical", "System is severely overloaded. Slowness expected.", details, True)
    if cpu > 70 or ram > 75:
        return make_result("warning", "System load is high. Performance may be affected.", details, True)
    return make_result("ok", "CPU and RAM are within normal ranges.", details, False)


# Problem 11 - File Not Responding
# A zombie process has finished but is stuck waiting to be cleaned up.
# These show up as Not Responding in Task Manager.
def check_file_not_responding():
    details = []
    zombies = []

    for proc in psutil.process_iter(["name", "status"]):
        try:
            if proc.info["status"] == psutil.STATUS_ZOMBIE:
                zombies.append(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if zombies:
        details.append("Zombie (not responding) processes found:")
        for name in zombies:
            details.append(name)
        return make_result("warning", f"{len(zombies)} unresponsive process(es) found.", details, True)

    details.append("No zombie processes found.")
    return make_result("ok", "No unresponsive processes detected.", details, False)


# Problem 12 - Screensaver Starting
# We read the Windows registry to check if a screensaver is configured
# and how many seconds of inactivity it takes to activate.
def check_screensaver():
    details = []

    if platform.system() != "Windows":
        return make_result("ok", "Screensaver check is Windows-only.", ["Non-Windows OS."], False)

    try:
        cmd = ('powershell -Command "(Get-ItemProperty '
               '\'HKCU:\\Control Panel\\Desktop\' -Name ScreenSaveActive).ScreenSaveActive"')
        val = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=10)
        val = val.decode(errors="ignore").strip()

        if val == "1":
            cmd2 = ('powershell -Command "(Get-ItemProperty '
                    '\'HKCU:\\Control Panel\\Desktop\' -Name ScreenSaveTimeOut).ScreenSaveTimeOut"')
            timeout = subprocess.check_output(cmd2, shell=True, stderr=subprocess.DEVNULL, timeout=10)
            timeout = timeout.decode(errors="ignore").strip()
            details.append(f"Screensaver is enabled. Activates after {timeout} seconds.")
            return make_result("warning", "Screensaver is active and may launch unexpectedly.", details, True)

        details.append("Screensaver is disabled.")
        return make_result("ok", "Screensaver is off.", details, False)

    except Exception as e:
        details.append(f"Could not read screensaver settings: {e}")
        return make_result("warning", "Screensaver status check failed.", details, False)


# Problem 13 - System Update Failure
# Windows Update failure events are recorded with IDs 20 and 24 in the System log.
def check_update_failure():
    details = []

    if platform.system() != "Windows":
        return make_result("ok", "Update check is Windows-only.", ["Non-Windows OS."], False)

    try:
        cmd = ('powershell -Command "Get-WinEvent -LogName System -MaxEvents 100 2>$null | '
               'Where-Object { $_.Id -eq 20 -or $_.Id -eq 24 } | '
               'Select-Object -First 5 TimeCreated, Message | ConvertTo-Json"')
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=20)
        output = output.decode(errors="ignore")

        if output.strip() and output.strip() != "null":
            details.append("Windows Update failure events found:")
            details.append(output[:400])
            return make_result("critical", "Windows Update failures detected.", details, True)

        details.append("No update failure events in the log.")
        return make_result("ok", "No update failures detected.", details, False)

    except Exception as e:
        details.append(f"Could not read event log: {e}")
        return make_result("warning", "Could not check Windows Update status.", details, False)


# Problem 14 - Camera Undetectable
# We look for Camera or Image class devices in Device Manager.
def check_camera():
    details = []

    if platform.system() == "Windows":
        try:
            cmd = ('powershell -Command "Get-PnpDevice | '
                   'Where-Object { $_.Class -eq \'Camera\' -or $_.Class -eq \'Image\' } | '
                   'Select-Object Status, FriendlyName | ConvertTo-Json"')
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=15)
            output = output.decode(errors="ignore")

            if not output.strip() or output.strip() == "null":
                details.append("No camera device found in Device Manager.")
                return make_result("critical", "Camera not detected by Windows.", details, True)

            details.append(output[:400])

            if "Error" in output:
                return make_result("critical", "Camera device has an error.", details, True)
            return make_result("ok", "Camera device recognized.", details, False)

        except Exception as e:
            details.append(f"Device Manager query failed: {e}")

    details.append("On Linux/Mac: run 'ls /dev/video*' in the terminal to check.")
    return make_result("warning", "Automated camera check not available here.", details, False)