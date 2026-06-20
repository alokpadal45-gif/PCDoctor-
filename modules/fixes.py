# This file receives a problem_id from the web route and calls
# the right repair function. The actual fix logic lives in the
# repairs/ folder, split into four focused files.

from modules.repairs.system_repairs   import fix_bluescreen, fix_auto_restart, fix_wifi, fix_bluetooth_audio, fix_keyboard
from modules.repairs.display_repairs  import fix_screen_flickering, fix_dll_missing, fix_auto_delete, fix_ram
from modules.repairs.software_repairs import fix_slow_performance, fix_file_not_responding, fix_screensaver, fix_update_failure, fix_camera
from modules.repairs.hardware_repairs import fix_fingerprint, fix_auto_screenshot, fix_overheating, fix_battery_drain, fix_freezing, fix_data_recovery


FIXES = {
    "bluescreen":          fix_bluescreen,
    "auto_restart":        fix_auto_restart,
    "wifi_slow":           fix_wifi,
    "headset_airpods":     fix_bluetooth_audio,
    "keystroke_error":     fix_keyboard,
    "screen_flickering":   fix_screen_flickering,
    "dll_missing":         fix_dll_missing,
    "auto_delete":         fix_auto_delete,
    "ram_overuse":         fix_ram,
    "slow_performance":    fix_slow_performance,
    "file_not_responding": fix_file_not_responding,
    "screensaver":         fix_screensaver,
    "update_failure":      fix_update_failure,
    "camera":              fix_camera,
    "fingerprint":         fix_fingerprint,
    "auto_screenshot":     fix_auto_screenshot,
    "overheating":         fix_overheating,
    "battery_drain":       fix_battery_drain,
    "freezing_hanging":    fix_freezing,
    "data_recovery":       fix_data_recovery,
}


def apply_fix(problem_id):
    func = FIXES.get(problem_id)
    if not func:
        return {"success": False, "message": f"Unknown problem: {problem_id}", "steps": []}
    return func()