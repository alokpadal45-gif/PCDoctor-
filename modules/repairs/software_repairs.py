# Fix functions for problems 10 to 14.
# Slow Performance, File Not Responding, Screensaver,
# Update Failure, Camera.

import subprocess
import platform
import psutil


def make_result(success, message, steps):
    return {"success": success, "message": message, "steps": steps}


# Fix 10 - Slow Performance
# Set Windows to Best Performance mode which turns off unnecessary animations.
def fix_slow_performance():
    steps = []

    if platform.system() == "Windows":
        try:
            # VisualFXSetting 2 = Adjust for best performance
            cmd = ('powershell -Command "Set-ItemProperty -Path '
                   '\'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects\' '
                   '-Name VisualFXSetting -Value 2"')
            subprocess.run(cmd, shell=True, timeout=10)
            steps.append("Windows set to Best Performance visual mode.")
        except Exception as e:
            steps.append(f"Could not change visual effects: {e}")

        steps.append("Manual steps: Task Manager > Startup tab > disable unused apps.")
        steps.append("Also run Disk Cleanup: search for cleanmgr in the Start menu.")

    return make_result(True, "Performance mode applied.", steps)


# Fix 11 - File Not Responding
# Kill any zombie processes that are stuck and cannot clean themselves up.
def fix_file_not_responding():
    steps = []
    killed = 0

    for proc in psutil.process_iter(["pid", "name", "status"]):
        try:
            if proc.info["status"] == psutil.STATUS_ZOMBIE:
                proc.kill()
                steps.append(f"Terminated zombie process: {proc.info['name']}")
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if killed:
        return make_result(True, f"Terminated {killed} zombie process(es).", steps)

    steps.append("No zombie processes found.")
    steps.append("If a specific app is frozen, use Task Manager > End Task manually.")
    return make_result(True, "No automatic action needed.", steps)


# Fix 12 - Screensaver
# Turn the screensaver off in the registry.
def fix_screensaver():
    steps = []

    if platform.system() != "Windows":
        return make_result(False, "Screensaver fix is Windows-only.", steps)

    try:
        cmd = ('powershell -Command "Set-ItemProperty -Path '
               '\'HKCU:\\Control Panel\\Desktop\' -Name ScreenSaveActive -Value 0"')
        subprocess.run(cmd, shell=True, check=True, timeout=10)
        steps.append("Screensaver has been disabled.")
        return make_result(True, "Screensaver is now off.", steps)

    except Exception as e:
        steps.append(f"Failed: {e}")
        return make_result(False, "Could not disable the screensaver.", steps)


# Fix 13 - Update Failure
# Reset Windows Update by stopping services, clearing the broken cache,
# and restarting services. This fixes most stuck update situations.
def fix_update_failure():
    steps = []

    if platform.system() != "Windows":
        return make_result(False, "Windows Update fix is Windows-only.", steps)

    commands = [
        ("net stop wuauserv",  "Stopped Windows Update service"),
        ("net stop cryptSvc",  "Stopped Cryptographic service"),
        ("net stop bits",      "Stopped BITS service"),
        ("net stop msiserver", "Stopped MSI Installer service"),
        (r'ren C:\Windows\SoftwareDistribution SoftwareDistribution.old', "Renamed update cache"),
        (r'ren C:\Windows\System32\catroot2 catroot2.old', "Renamed catroot2 folder"),
        ("net start wuauserv",  "Started Windows Update service"),
        ("net start cryptSvc",  "Started Cryptographic service"),
        ("net start bits",      "Started BITS service"),
        ("net start msiserver", "Started MSI Installer service"),
    ]

    for cmd, label in commands:
        try:
            subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
            steps.append(label)
        except Exception as e:
            steps.append(f"{label} - error: {e}")

    steps.append("Go to Settings > Windows Update and try updating again.")
    return make_result(True, "Update reset complete.", steps)


# Fix 14 - Camera
# Disable then re-enable the camera device to force the driver to reinitialize.
def fix_camera():
    steps = []

    if platform.system() != "Windows":
        return make_result(False, "Camera fix is Windows-only.", steps)

    try:
        for action in ("Disable", "Enable"):
            cmd = (f'powershell -Command "Get-PnpDevice | '
                   f'Where-Object {{ $_.Class -eq \'Camera\' }} | '
                   f'{action}-PnpDevice -Confirm:$false"')
            subprocess.run(cmd, shell=True, capture_output=True, timeout=20)
            steps.append(f"Camera {action.lower()}d.")

        steps.append("Open the Camera app to test it.")
        return make_result(True, "Camera reset. Test it now.", steps)

    except Exception as e:
        steps.append(f"Device reset failed: {e}")
        steps.append("Manual: Device Manager > Cameras > right-click > Update driver.")
        return make_result(False, "Automatic camera reset failed.", steps)