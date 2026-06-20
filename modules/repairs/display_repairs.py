# Fix functions for problems 6 to 9.
# Screen Flickering, DLL Missing, Auto Delete, RAM Overuse.

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
    try:
        result = subprocess.run(
            ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"],
            capture_output=True, text=True, timeout=600
        )
        steps.append(result.stdout[:400])
        steps.append("DISM finished.")
    except Exception as e:
        steps.append(f"DISM failed: {e}")


# Fix 6 - Screen Flickering
# The proper fix is a GPU driver update done manually.
# We apply a software fallback that helps in some cases.
def fix_screen_flickering():
    steps = []

    if platform.system() == "Windows":
        try:
            cmd = ('powershell -Command "Set-ItemProperty -Path '
                   '\'HKCU:\\SOFTWARE\\Microsoft\\Avalon.Graphics\' '
                   '-Name DisableHWAcceleration -Value 1 -Force"')
            subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            steps.append("Software rendering fallback enabled for some apps.")
        except Exception:
            steps.append("Could not apply software rendering fallback.")

    steps.append("Manual steps needed for a full fix:")
    steps.append("1. Device Manager > Display Adapters > right-click GPU > Update driver.")
    steps.append("2. Right-click Desktop > Display settings > Advanced display > set correct refresh rate.")
    return make_result(True, "Partial fix applied. Manual GPU driver update still needed.", steps)


# Fix 7 - DLL Missing
# Run DISM first to fix the repair source, then SFC to restore missing DLLs.
def fix_dll_missing():
    steps = []

    if platform.system() != "Windows":
        return make_result(False, "DLL fixes only apply to Windows.", steps)

    if not is_admin():
        steps.append("Administrator rights required.")
        steps.append("Right-click the app and choose Run as Administrator.")
        return make_result(False, "Admin privileges needed.", steps)

    steps.append("Step 1: Running DISM to repair the Windows image.")
    run_dism(steps)

    steps.append("Step 2: Running SFC to restore missing DLL files.")
    try:
        result = subprocess.run(["sfc", "/scannow"], capture_output=True, text=True, timeout=300)
        steps.append(result.stdout[:600])
        steps.append("Repair complete. Restart your computer.")
        return make_result(True, "DLL repair finished. Restart required.", steps)
    except Exception as e:
        steps.append(f"SFC step failed: {e}")
        return make_result(False, "Repair partially failed.", steps)


# Fix 8 - Auto Delete
# Turn off Storage Sense so Windows stops deleting files automatically.
def fix_auto_delete():
    steps = []

    if platform.system() != "Windows":
        return make_result(False, "Storage Sense only exists on Windows.", steps)

    try:
        cmd = ('powershell -Command "Set-ItemProperty -Path '
               '\'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters\\StoragePolicy\' '
               '-Name 01 -Value 0"')
        subprocess.run(cmd, shell=True, check=True, timeout=10)
        steps.append("Storage Sense disabled.")
        steps.append("Your files will no longer be deleted automatically.")
        steps.append("Verify at: Settings > System > Storage > Storage Sense.")
        return make_result(True, "Storage Sense turned off.", steps)

    except Exception as e:
        steps.append(f"Failed: {e}")
        return make_result(False, "Could not disable Storage Sense.", steps)


# Fix 9 - RAM Overuse
# Kill the top 3 memory-heavy non-system processes to free RAM.
def fix_ram():
    steps = []

    system_processes = {
        "system", "svchost.exe", "lsass.exe", "csrss.exe",
        "winlogon.exe", "services.exe", "python.exe", "python3",
        "cmd.exe", "powershell.exe"
    }

    processes = sorted(
        psutil.process_iter(["pid", "name", "memory_percent"]),
        key=lambda p: p.info["memory_percent"] or 0,
        reverse=True
    )

    killed = 0
    for proc in processes:
        if killed >= 3:
            break
        name = (proc.info["name"] or "").lower()
        if name in system_processes:
            continue
        try:
            mem = round(proc.info["memory_percent"], 1)
            proc.kill()
            steps.append(f"Closed: {proc.info['name']} (was using {mem}% RAM)")
            killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            steps.append(f"Skipped {proc.info['name']}: {e}")

    if killed > 0:
        return make_result(True, f"Freed RAM by closing {killed} process(es).", steps)

    steps.append("No non-system processes could be safely closed.")
    return make_result(False, "No processes were safe to close.", steps)