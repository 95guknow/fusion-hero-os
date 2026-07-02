#!/usr/bin/env python3
"""
ALTE_Frau_95g Heroic Core - AMD Radeon GPU Fan Automation (Python)
Global Fan Automation & Thermal Guard - AMD Version

This script controls AMD GPU fans using sysfs (works with amdgpu driver).
It is more universal than rocm-smi and doesn't require ROCm to be fully installed.

Features:
- Automatic detection of AMD GPU hwmon path
- Temperature monitoring
- Manual fan control with configurable curve
- Logging
- Graceful exit (returns control to driver)

Requirements:
- amdgpu kernel driver (standard on modern Linux)
- Write permissions to /sys/class/drm/... (usually needs sudo or udev rule)

Usage:
    sudo python3 gpu_fan_automation_amd.py

Author: ALTE_Frau_95g Core v7.2
"""

import os
import time
import glob
from datetime import datetime

# ==================== CONFIGURATION ====================
CHECK_INTERVAL = 12              # Seconds between checks

TEMP_LOW = 55
TEMP_MEDIUM = 68
TEMP_HIGH = 80
TEMP_CRITICAL = 88

# PWM values (0-255)
FAN_LOW = 60
FAN_MEDIUM = 110
FAN_HIGH = 180
FAN_MAX = 255

LOG_FILE = "/tmp/alte_frau_amd_fan.log"
# =======================================================


def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def find_amd_hwmon_path():
    """
    Find the hwmon path for the first AMD GPU.
    Returns the path to the hwmon directory or None.
    """
    for card in glob.glob("/sys/class/drm/card[0-9]*"):
        hwmon_dir = os.path.join(card, "device", "hwmon")
        if os.path.exists(hwmon_dir):
            hwmon_subdirs = glob.glob(os.path.join(hwmon_dir, "hwmon*"))
            for hwmon in hwmon_subdirs:
                # Check if it looks like an AMD GPU (name file contains "amdgpu" or similar)
                name_file = os.path.join(hwmon, "name")
                if os.path.exists(name_file):
                    try:
                        with open(name_file) as f:
                            name = f.read().strip().lower()
                        if "amdgpu" in name or "radeon" in name:
                            return hwmon
                    except Exception:
                        continue
    return None


def read_temp(hwmon_path: str) -> int:
    """Read temperature from hwmon (in millidegrees, convert to °C)"""
    temp_file = os.path.join(hwmon_path, "temp1_input")
    if not os.path.exists(temp_file):
        return -1
    try:
        with open(temp_file) as f:
            millidegrees = int(f.read().strip())
        return millidegrees // 1000
    except Exception:
        return -1


def set_fan_manual(hwmon_path: str):
    """Enable manual fan control"""
    pwm_enable = os.path.join(hwmon_path, "pwm1_enable")
    if os.path.exists(pwm_enable):
        try:
            with open(pwm_enable, "w") as f:
                f.write("1")  # 1 = manual
            return True
        except PermissionError:
            log("ERROR: No permission to write to pwm1_enable. Run with sudo.")
            return False
    return False


def set_fan_speed(hwmon_path: str, speed: int):
    """Set fan PWM (0-255)"""
    pwm_file = os.path.join(hwmon_path, "pwm1")
    if os.path.exists(pwm_file):
        try:
            with open(pwm_file, "w") as f:
                f.write(str(speed))
            return True
        except PermissionError:
            log("ERROR: No permission to set fan speed. Run with sudo.")
            return False
    return False


def set_fan_auto(hwmon_path: str):
    """Return fan control to the driver"""
    pwm_enable = os.path.join(hwmon_path, "pwm1_enable")
    if os.path.exists(pwm_enable):
        try:
            with open(pwm_enable, "w") as f:
                f.write("2")  # 2 = automatic (driver controlled)
            log("Fan control returned to automatic mode.")
        except Exception:
            pass


def get_fan_speed_for_temp(temp: int) -> int:
    if temp >= TEMP_CRITICAL:
        return FAN_MAX
    elif temp >= TEMP_HIGH:
        return FAN_HIGH
    elif temp >= TEMP_MEDIUM:
        return FAN_MEDIUM
    elif temp >= TEMP_LOW:
        return FAN_LOW
    else:
        return FAN_LOW


def main():
    log("=== ALTE_Frau_95g AMD GPU Fan Automation started ===")

    hwmon_path = find_amd_hwmon_path()
    if not hwmon_path:
        log("ERROR: No AMD GPU hwmon path found. Is amdgpu driver loaded?")
        return

    log(f"Found AMD GPU hwmon path: {hwmon_path}")

    if not set_fan_manual(hwmon_path):
        log("Exiting because manual fan control could not be enabled.")
        return

    try:
        while True:
            temp = read_temp(hwmon_path)
            if temp == -1:
                log("Could not read temperature. Retrying...")
                time.sleep(CHECK_INTERVAL)
                continue

            log(f"Current GPU temperature: {temp}°C")

            target_fan = get_fan_speed_for_temp(temp)
            if set_fan_speed(hwmon_path, target_fan):
                log(f"Fan PWM set to {target_fan}")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        log("Stopping...")
        set_fan_auto(hwmon_path)
        log("Script terminated cleanly.")


if __name__ == "__main__":
    main()
