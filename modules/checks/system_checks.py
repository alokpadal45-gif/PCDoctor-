# Diagnostic checks for problems 1 to 5 from the whiteboard.
# These are: Blue Screen, Auto Restart, WiFi, Headset, Keystroke Error.
# All functions are read-only - they inspect but never change anything.

import os
import subprocess
import platform
import psutil


def make_result(status, message, details, can_auto_fix):
    return {"status": status, "message": message, "details": details, "can_auto_fix": can_auto_fix}


# Problem 1 - Blue Screen
# Windows saves a small dump file every time a BSOD crash happens.
# We just check if any of those files exist in the standard folder.
def check_bluescreen():
    details = []
    dump_folder = r"C:\Windows\Minidump"

    if platform.system() != "Windows":
        return make_result("ok", "BSOD checks only apply to Windows.", ["Non-Windows OS."], False)

    if not os.path.exists(dump_folder):
        details.append("No MiniDump folder found. No recent crashes recorded.")
        return make_result("ok", "No crash history found.", details, False)

    dumps = [f for f in os.listdir(dump_folder) if f.endswith(".dmp")]

    if dumps:
        details.append(f"Found {len(dumps)} crash dump file(s) in {dump_folder}.")
        for f in dumps[-5:]:
            details.append(f)
        return make_result("critical", f"{len(dumps)} BSOD dump(s) found.", details, True)

    details.append("No crash dump files found. System has been stable.")
    return make_result("ok", "No BSOD history.", details, False)


# Problem 2 - Auto Restart
# Windows logs Event ID 41 every time the system restarts without a clean shutdown.
# We query the System event log for those entries and display them cleanly.
def check_auto_restart():
    import json
    details = []

    if platform.system() != "Windows":
        return make_result("ok", "Restart checks are Windows-only.", ["Non-Windows OS."], False)

    try:
        cmd = ('powershell -Command "Get-WinEvent -FilterHashtable '
               '@{LogName=\'System\'; Id=41} -MaxEvents 5 2>$null | '
               'Select-Object TimeCreated, Message | ConvertTo-Json"')
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=15)
        output = output.decode(errors="ignore").strip()

        if not output or output == "null":
            details.append("No unexpected restart events found.")
            return make_result("ok", "No unexpected restarts logged.", details, False)

        # Parse the JSON and show each event in plain readable text
        events = json.loads(output)

        # PowerShell returns a single object instead of a list when only one result exists
        if isinstance(events, dict):
            events = [events]

        details.append(f"Found {len(events)} unexpected restart event(s):")
        for i, event in enumerate(events, 1):
            # The message is long - we only show the first sentence
            message = event.get("Message", "No details available.")
            first_sentence = message.split(".")[0].strip()
            details.append(f"Event {i}: {first_sentence}.")

        return make_result("critical", f"{len(events)} unexpected restart(s) found in event log.", details, True)

    except Exception as e:
        details.append(f"Could not read event log: {e}")
        return make_result("warning", "Event log check failed.", details, False)


# Problem 3 - WiFi / No Internet
# We ping Google DNS (8.8.8.8) to test whether internet is reachable.
def check_wifi():
    details = []

    active = [name for name, stat in psutil.net_if_stats().items() if stat.isup]
    details.append("Active interfaces: " + (", ".join(active) if active else "None"))

    ping_cmd = ["ping", "-n", "3", "8.8.8.8"] if platform.system() == "Windows" else ["ping", "-c", "3", "8.8.8.8"]

    try:
        result = subprocess.run(ping_cmd, capture_output=True, timeout=10, text=True)
        if result.returncode == 0:
            details.append("Ping to 8.8.8.8 succeeded.")
            details.append(result.stdout.splitlines()[-1])
            return make_result("ok", "Internet connection is working.", details, False)
        else:
            details.append("Ping failed - no response from 8.8.8.8.")
            return make_result("critical", "No internet connection detected.", details, True)

    except subprocess.TimeoutExpired:
        details.append("Ping timed out after 10 seconds.")
        return make_result("critical", "Connection timeout. Very slow or no internet.", details, True)

    except Exception as e:
        details.append(f"Ping error: {e}")
        return make_result("warning", "Could not test connectivity.", details, False)


# Problem 4 - Headset / AirPods
# We look for Bluetooth and audio devices in Device Manager and check their status.
def check_bluetooth_audio():
    details = []

    if platform.system() == "Windows":
        try:
            cmd = ('powershell -Command "Get-PnpDevice | '
                   'Where-Object { $_.Class -eq \'Bluetooth\' -or $_.Class -eq \'AudioEndpoint\' } | '
                   'Select-Object Status, FriendlyName | ConvertTo-Json"')
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=15)
            output = output.decode(errors="ignore")
            details.append("Bluetooth/audio devices:")
            details.append(output[:400])

            if "Error" in output or "Unknown" in output:
                return make_result("warning", "Bluetooth or audio device has an error.", details, True)
            return make_result("ok", "Bluetooth and audio devices look fine.", details, False)

        except Exception as e:
            details.append(f"Device Manager query failed: {e}")
            return make_result("warning", "Could not check Bluetooth devices.", details, False)

    try:
        result = subprocess.run(["systemctl", "is-active", "bluetooth"], capture_output=True, text=True)
        status = result.stdout.strip()
        details.append(f"Bluetooth service: {status}")
        if status == "active":
            return make_result("ok", "Bluetooth service is running.", details, False)
        return make_result("critical", "Bluetooth service is not running.", details, True)
    except Exception:
        details.append("Cannot check Bluetooth service on this platform.")
        return make_result("warning", "Manual check required.", details, False)


# Problem 5 - Keystroke Error
# We check Device Manager for keyboard device errors.
def check_keyboard():
    details = []

    if platform.system() == "Windows":
        try:
            cmd = ('powershell -Command "Get-PnpDevice | '
                   'Where-Object { $_.Class -eq \'Keyboard\' } | '
                   'Select-Object Status, FriendlyName | ConvertTo-Json"')
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=15)
            output = output.decode(errors="ignore")
            details.append("Keyboard devices:")
            details.append(output[:400])

            if "Error" in output or "Unknown" in output:
                return make_result("warning", "Keyboard device error found.", details, True)
            return make_result("ok", "Keyboard device recognized.", details, False)

        except Exception as e:
            details.append(f"Query failed: {e}")

    details.append("Open Notepad and type every key to verify manually.")
    return make_result("warning", "Manual keyboard test needed.", details, False)