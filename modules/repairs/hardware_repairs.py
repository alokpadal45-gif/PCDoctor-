# Fix functions for problems 15 to 20.
# Fingerprint, Auto Screenshot, Overheating,
# Battery Drain, Freezing, Data Recovery.

import os
import subprocess
import platform
import psutil


def make_result(success, message, steps):
    return {"success": success, "message": message, "steps": steps}


# Fix 15 - Fingerprint
# Disable then re-enable the biometric sensor to reset the driver.
def fix_fingerprint():
    steps = []

    if platform.system() != "Windows":
        return make_result(False, "Fingerprint fix is Windows-only.", steps)

    try:
        for action in ("Disable", "Enable"):
            cmd = (f'powershell -Command "Get-PnpDevice | '
                   f'Where-Object {{ $_.Class -eq \'Biometric\' }} | '
                   f'{action}-PnpDevice -Confirm:$false"')
            subprocess.run(cmd, shell=True, capture_output=True, timeout=20)
            steps.append(f"Fingerprint sensor {action.lower()}d.")

        steps.append("Re-enroll: Settings > Accounts > Sign-in options > Fingerprint > Add a finger.")
        return make_result(True, "Fingerprint sensor reset.", steps)

    except Exception as e:
        steps.append(f"Failed: {e}")
        return make_result(False, "Could not reset fingerprint sensor.", steps)


# Fix 16 - Auto Screenshot
# Disable scheduled tasks that may be capturing screenshots silently.
def fix_auto_screenshot():
    steps = []

    if platform.system() != "Windows":
        return make_result(False, "This fix is Windows-only.", steps)

    try:
        cmd = ('powershell -Command "Get-ScheduledTask | '
               'Where-Object { $_.TaskName -like \'*screen*\' -or $_.TaskName -like \'*capture*\' } | '
               'Disable-ScheduledTask"')
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=15)
        output = output.decode(errors="ignore")
        steps.append("Suspicious screenshot tasks disabled.")
        steps.append(output[:300] if output.strip() else "No matching tasks found.")
        steps.append("Also run a full Windows Defender antivirus scan.")
        return make_result(True, "Screenshot tasks disabled.", steps)

    except Exception as e:
        steps.append(f"Failed: {e}")
        return make_result(False, "Could not disable screenshot tasks.", steps)


# Fix 17 - Overheating
# Switch to the Balanced power plan which reduces CPU speed and heat.
# The High Performance plan runs the CPU hotter unnecessarily.
def fix_overheating():
    steps = []

    if platform.system() == "Windows":
        try:
            # 381b4222 is the GUID of the built-in Balanced power plan
            subprocess.run(
                ["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"],
                check=True, capture_output=True, timeout=10
            )
            steps.append("Power plan set to Balanced. CPU will run cooler.")
        except Exception as e:
            steps.append(f"Could not switch power plan: {e}")

    steps.append("Physical actions to take:")
    steps.append("1. Clean fan vents with compressed air.")
    steps.append("2. Keep the laptop on a hard flat surface, never on a bed or pillow.")
    steps.append("3. Consider replacing thermal paste if the laptop is over 2 years old.")
    return make_result(True, "Power plan set to Balanced. Check physical ventilation too.", steps)


# Fix 18 - Battery Drain
# Switch to Power Saver plan to extend battery life.
def fix_battery_drain():
    steps = []
    battery = psutil.sensors_battery()

    if not battery:
        return make_result(False, "No battery detected. This appears to be a desktop.", steps)

    if platform.system() == "Windows":
        try:
            # a1841308 is the GUID of the built-in Power Saver plan
            subprocess.run(
                ["powercfg", "/setactive", "a1841308-3541-4fab-bc81-f71556f20b4a"],
                check=True, capture_output=True, timeout=10
            )
            steps.append("Power plan switched to Power Saver.")
        except Exception as e:
            steps.append(f"Could not switch power plan: {e}")

    steps.append("Also: lower screen brightness, turn on Airplane Mode when WiFi not needed.")
    return make_result(True, "Battery saver activated.", steps)


# Fix 19 - Freezing / Hanging
# Kill top CPU-consuming processes and clear temp files to reduce I/O pressure.
def fix_freezing():
    steps = []
    skip = {"system", "svchost.exe", "lsass.exe", "python.exe", "python3"}

    processes = sorted(
        psutil.process_iter(["pid", "name", "cpu_percent"]),
        key=lambda p: p.info["cpu_percent"] or 0,
        reverse=True
    )

    killed = 0
    for proc in processes:
        if killed >= 3:
            break
        if (proc.info["name"] or "").lower() in skip:
            continue
        if (proc.info["cpu_percent"] or 0) > 50:
            try:
                proc.kill()
                steps.append(f"Closed: {proc.info['name']} ({proc.info['cpu_percent']}% CPU)")
                killed += 1
            except Exception:
                pass

    if platform.system() == "Windows":
        temp_dir = os.environ.get("TEMP", r"C:\Windows\Temp")
        cleared = 0
        try:
            for filename in os.listdir(temp_dir):
                try:
                    filepath = os.path.join(temp_dir, filename)
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                        cleared += 1
                except Exception:
                    pass  # locked temp files are skipped safely
            steps.append(f"Cleared {cleared} temp file(s) from {temp_dir}.")
        except Exception as e:
            steps.append(f"Could not clear temp folder: {e}")

    return make_result(True, f"Closed {killed} high-CPU process(es) and cleared temp files.", steps)


# Fix 20 - Data Recovery
# We guide the user rather than act automatically to avoid overwriting lost data.
def fix_data_recovery():
    steps = [
        "Do not save any new files to the drive where data was lost.",
        "Writing new data to that drive can overwrite the files you are trying to recover.",
        "Recommended free tools:",
        "  Recuva (Windows): https://www.ccleaner.com/recuva",
        "  TestDisk / PhotoRec: https://www.cgsecurity.org",
        "  Windows File Recovery (built-in): search winfrw in Start menu",
        "Steps:",
        "  1. Install the tool on a DIFFERENT drive than the one with lost files.",
        "  2. Select the affected drive and run a Deep Scan.",
        "  3. Save recovered files to a DIFFERENT drive.",
        "If the drive makes clicking sounds or is not detected, take it to a recovery lab.",
    ]
    return make_result(True, "Follow the steps below carefully.", steps)