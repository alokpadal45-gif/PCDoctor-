# Fix functions for problems 1 to 5.
# Blue Screen, Auto Restart, WiFi, Headset, Keystroke Error.

import os
import subprocess
import platform
import ctypes
import psutil


def make_result(success, message, steps):
    return {"success": success, "message": message, "steps": steps}


def is_admin():
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        return os.geteuid() == 0
    except Exception:
        return False


def run_dism(steps):
    # DISM repairs the Windows component store which SFC uses as its source.
    try:
        result = subprocess.run(
            ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"],
            capture_output=True, text=True, timeout=600
        )
        steps.append(result.stdout[:400])
        steps.append("DISM repair finished.")
    except Exception as e:
        steps.append(f"DISM failed: {e}")


# Fix 1 - Blue Screen
# sfc /scannow replaces corrupt system files that cause BSODs.
def fix_bluescreen():
    steps = []

    if platform.system() != "Windows":
        return make_result(False, "BSOD fixes only apply to Windows.", steps)

    if not is_admin():
        steps.append("Administrator rights are required.")
        steps.append("Right-click the app and choose Run as Administrator.")
        return make_result(False, "Admin privileges needed.", steps)

    steps.append("Running System File Checker. This may take 5-10 minutes.")

    try:
        result = subprocess.run(["sfc", "/scannow"], capture_output=True, text=True, timeout=300)
        output = result.stdout + result.stderr
        steps.append(output[:800])

        if "did not find any integrity violations" in output.lower():
            return make_result(True, "No corrupted system files found.", steps)
        if "successfully repaired" in output.lower():
            steps.append("Corrupted files repaired. Restart your PC.")
            return make_result(True, "System files repaired. Restart required.", steps)

        steps.append("SFC found issues but could not fully repair. Running DISM.")
        run_dism(steps)
        return make_result(True, "Repair attempted. Restart your computer.", steps)

    except Exception as e:
        steps.append(f"SFC could not run: {e}")
        return make_result(False, "System File Checker failed.", steps)


# Fix 2 - Auto Restart
# Disable automatic reboot on crash so you can read the BSOD error code.
def fix_auto_restart():
    steps = []

    if platform.system() != "Windows":
        return make_result(False, "This fix only applies to Windows.", steps)

    try:
        cmd = ('powershell -Command "Set-ItemProperty -Path '
               '\'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\CrashControl\' '
               '-Name AutoReboot -Value 0"')
        subprocess.run(cmd, shell=True, check=True, timeout=10)
        steps.append("Auto-restart on crash is now disabled.")
        steps.append("The next BSOD will stay on screen so you can read the error code.")
        return make_result(True, "Auto-restart disabled. Error codes will be visible.", steps)

    except Exception as e:
        steps.append(f"Registry change failed: {e}")
        return make_result(False, "Could not disable auto-restart.", steps)


# Fix 3 - WiFi
# Reset the TCP/IP stack and DNS cache to fix most internet problems.
def fix_wifi():
    steps = []

    if platform.system() != "Windows":
        try:
            subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], timeout=15)
            steps.append("NetworkManager restarted.")
            return make_result(True, "Network service restarted.", steps)
        except Exception as e:
            steps.append(f"Could not restart NetworkManager: {e}")
            return make_result(False, "Network restart failed.", steps)

    commands = [
        ("netsh int ip reset",  "TCP/IP stack reset"),
        ("netsh winsock reset", "Winsock catalog reset"),
        ("ipconfig /flushdns",  "DNS cache cleared"),
        ("ipconfig /release",   "IP address released"),
        ("ipconfig /renew",     "IP address renewed"),
    ]

    for cmd, label in commands:
        try:
            subprocess.run(cmd, shell=True, capture_output=True, timeout=20)
            steps.append(label + " - done")
        except Exception as e:
            steps.append(f"{label} - failed: {e}")

    steps.append("Network reset complete. Restart your PC for full effect.")
    return make_result(True, "Network reset done. Restart recommended.", steps)


# Fix 4 - Headset / AirPods
# Restarting the Bluetooth service clears most pairing and connection issues.
def fix_bluetooth_audio():
    steps = []

    if platform.system() == "Windows":
        try:
            subprocess.run(["net", "stop", "bthserv"], capture_output=True, timeout=15)
            steps.append("Bluetooth service stopped.")
            subprocess.run(["net", "start", "bthserv"], capture_output=True, timeout=15)
            steps.append("Bluetooth service started.")
            steps.append("Remove the headset from paired devices and re-pair it now.")
            return make_result(True, "Bluetooth service restarted.", steps)
        except Exception as e:
            steps.append(f"Service restart failed: {e}")
            return make_result(False, "Could not restart Bluetooth.", steps)

    try:
        subprocess.run(["sudo", "systemctl", "restart", "bluetooth"], timeout=15)
        steps.append("Bluetooth restarted on Linux.")
        return make_result(True, "Bluetooth restarted.", steps)
    except Exception as e:
        steps.append(f"Failed: {e}")
        return make_result(False, "Could not restart Bluetooth.", steps)


# Fix 5 - Keystroke Error
# Filter Keys is an accessibility feature that makes keys feel delayed or stuck.
# Setting Flags to 122 disables all its sub-features.
def fix_keyboard():
    steps = []

    if platform.system() != "Windows":
        return make_result(False, "This fix is Windows-specific.", steps)

    try:
        cmd = ('powershell -Command "Set-ItemProperty -Path '
               '\'HKCU:\\Control Panel\\Accessibility\\Keyboard Response\' '
               '-Name Flags -Value 122"')
        subprocess.run(cmd, shell=True, check=True, timeout=10)
        steps.append("Filter Keys has been disabled.")
        steps.append("Also check Settings > Accessibility > Keyboard for Sticky Keys and Toggle Keys.")
        return make_result(True, "Filter Keys turned off.", steps)

    except Exception as e:
        steps.append(f"Failed: {e}")
        return make_result(False, "Could not change keyboard settings.", steps)