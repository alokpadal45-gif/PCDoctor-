# This file receives a problem_id from the web route and calls
# the right check function. The actual check logic lives in the
# checks/ folder, split into four focused files.
# This file itself stays under 50 lines on purpose.

from modules.checks.system_checks  import check_bluescreen, check_auto_restart, check_wifi, check_bluetooth_audio, check_keyboard
from modules.checks.display_checks import check_screen_flickering, check_dll_errors, check_auto_delete, check_ram
from modules.checks.software_checks import check_slow_performance, check_file_not_responding, check_screensaver, check_update_failure, check_camera
from modules.checks.hardware_checks import check_fingerprint, check_auto_screenshot, check_overheating, check_battery_drain, check_freezing, check_data_recovery


CHECKS = {
    "bluescreen":          check_bluescreen,
    "auto_restart":        check_auto_restart,
    "wifi_slow":           check_wifi,
    "headset_airpods":     check_bluetooth_audio,
    "keystroke_error":     check_keyboard,
    "screen_flickering":   check_screen_flickering,
    "dll_missing":         check_dll_errors,
    "auto_delete":         check_auto_delete,
    "ram_overuse":         check_ram,
    "slow_performance":    check_slow_performance,
    "file_not_responding": check_file_not_responding,
    "screensaver":         check_screensaver,
    "update_failure":      check_update_failure,
    "camera":              check_camera,
    "fingerprint":         check_fingerprint,
    "auto_screenshot":     check_auto_screenshot,
    "overheating":         check_overheating,
    "battery_drain":       check_battery_drain,
    "freezing_hanging":    check_freezing,
    "data_recovery":       check_data_recovery,
}


def run_diagnostic(problem_id):
    func = CHECKS.get(problem_id)
    if not func:
        return {"status": "warning", "message": f"Unknown problem: {problem_id}", "details": [], "can_auto_fix": False}
    return func()