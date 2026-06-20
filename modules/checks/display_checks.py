# Diagnostic checks for problems 6 to 9.
# These are: Screen Flickering, DLL Missing, Auto Delete, RAM Overuse.

import os
import subprocess
import platform
import psutil


def make_result(status, message, details, can_auto_fix):
    return {"status": status, "message": message, "details": details, "can_auto_fix": can_auto_fix}


# Problem 6 - Screen Flickering
# Outdated display drivers are the most common cause of flickering.
# We check the display adapter status in Device Manager.
def check_screen_flickering():
    details = []

    if platform.system() == "Windows":
        try:
            cmd = ('powershell -Command "Get-PnpDevice | '
                   'Where-Object { $_.Class -eq \'Display\' } | '
                   'Select-Object Status, FriendlyName | ConvertTo-Json"')
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=15)
            output = output.decode(errors="ignore")
            details.append("Display adapters:")
            details.append(output[:400])

            if "Error" in output or "Unknown" in output:
                return make_result("critical", "Display driver issue found in Device Manager.", details, True)
            return make_result("ok", "Display driver appears healthy.", details, False)

        except Exception as e:
            details.append(f"Could not check display devices: {e}")

    details.append("Manual fix: Device Manager > Display Adapters > Update driver.")
    return make_result("warning", "Automated display check not available.", details, False)


# Problem 7 - DLL Missing
# sfc /verifyonly scans system files and reports any missing DLLs.
# This flag is read-only and makes no changes to the system.
def check_dll_errors():
    details = []

    if platform.system() != "Windows":
        return make_result("ok", "DLL checks only apply to Windows.", ["Non-Windows system."], False)

    details.append("Running SFC verify scan. No changes will be made.")

    try:
        result = subprocess.run(["sfc", "/verifyonly"], capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
        details.append(output[:600])

        if "did not find any integrity violations" in output.lower():
            return make_result("ok", "No missing DLLs found. System files are intact.", details, False)
        return make_result("critical", "System file issues detected. DLL files may be missing.", details, True)

    except PermissionError:
        details.append("SFC needs Administrator rights. Re-run the app as Administrator.")
        return make_result("warning", "Admin privileges required.", details, False)

    except Exception as e:
        details.append(f"SFC failed: {e}")
        return make_result("warning", "SFC scan could not run.", details, False)


# Problem 8 - Auto Deleting Files
# Windows Storage Sense can delete files automatically.
# We check the registry to see if it is turned on.
def check_auto_delete():
    details = []

    if platform.system() == "Windows":
        try:
            cmd = ('powershell -Command "(Get-ItemProperty '
                   'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion'
                   '\\StorageSense\\Parameters\\StoragePolicy '
                   '-Name 01 -ErrorAction SilentlyContinue).01"')
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=10)
            out = out.decode(errors="ignore").strip()

            if out == "1":
                details.append("Storage Sense is enabled and can delete files automatically.")
                return make_result("warning", "Storage Sense is on. It may be deleting your files.", details, True)

            details.append("Storage Sense is disabled.")

        except Exception as e:
            details.append(f"Could not check Storage Sense: {e}")

    details.append("Also check: antivirus quarantine and OneDrive/Dropbox sync settings.")
    return make_result("ok", "No auto-delete settings found.", details, False)


# Problem 9 - RAM Overuse
# We read RAM usage and if it is high we show the top 5 memory consumers.
def check_ram():
    details = []
    ram = psutil.virtual_memory()
    details.append(f"RAM used: {ram.percent}%  ({round(ram.used/1024**3, 1)} GB of {round(ram.total/1024**3, 1)} GB)")

    if ram.percent > 85:
        processes = sorted(
            psutil.process_iter(["name", "memory_percent"]),
            key=lambda p: p.info["memory_percent"] or 0,
            reverse=True
        )
        details.append("Top 5 processes using the most RAM:")
        for p in processes[:5]:
            details.append(f"{p.info['name']}: {round(p.info['memory_percent'], 1)}%")
        return make_result("critical", f"RAM critically high at {ram.percent}%.", details, True)

    if ram.percent > 70:
        return make_result("warning", f"RAM is elevated at {ram.percent}%.", details, False)

    return make_result("ok", f"RAM is normal at {ram.percent}%.", details, False)