import os
import sys
import glob
import json
import shutil
import subprocess
import re
from typing import List, Dict, Optional, Tuple, Any
from PySide6.QtCore import QObject, Signal, QThread

from system_checker import SystemChecker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_APP_DIR = os.path.join(BASE_DIR, "GK6X-v1.22")
APP_DIR = os.environ.get("GK6X_PATH", DEFAULT_APP_DIR)
if not os.path.exists(APP_DIR):
    user_app_dir = os.path.expanduser("~/.local/share/skyloong_studio/GK6X-v1.22")
    if os.path.exists(user_app_dir):
        APP_DIR = user_app_dir

EXE_PATH = os.path.join(APP_DIR, "GK6X.exe")
LIGHTING_DIR = os.path.join(APP_DIR, "Data", "lighting")
USERDATA_DIR = os.path.join(APP_DIR, "UserData")
CONFIG_SAVE_PATH = os.path.expanduser("~/.config/skyloong_studio/profile.json")

def scan_linux_usb_devices() -> List[Dict[str, Any]]:
    """Scan Linux sysfs, hidraw, input and USB subsystems for connected Skyloong / Semitek devices."""
    devices = []
    seen_keys = set()
    
    # 1. Scan /sys/bus/usb/devices
    for dev_path in glob.glob("/sys/bus/usb/devices/*"):
        id_vendor_f = os.path.join(dev_path, "idVendor")
        id_product_f = os.path.join(dev_path, "idProduct")
        if os.path.exists(id_vendor_f) and os.path.exists(id_product_f):
            try:
                vid = open(id_vendor_f).read().strip().lower()
                pid = open(id_product_f).read().strip().lower()
                
                prod_f = os.path.join(dev_path, "product")
                manuf_f = os.path.join(dev_path, "manufacturer")
                serial_f = os.path.join(dev_path, "serial")
                
                prod = open(prod_f).read().strip() if os.path.exists(prod_f) else ""
                manuf = open(manuf_f).read().strip() if os.path.exists(manuf_f) else ""
                serial = open(serial_f).read().strip() if os.path.exists(serial_f) else ""
                
                # Check for Skyloong / Semitek / GK keyboard signatures
                is_known_vid = vid in ["1ea7", "32e3", "04d9", "0c45"]
                name_match = any(x in (prod + " " + manuf).lower() for x in ["skyloong", "semite", "gk104", "gk6", "gk7", "gk8", "gk9", "gaming keyboa", "nrf52"])
                
                if is_known_vid or name_match:
                    key = f"usb_{vid}_{pid}_{serial}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        devices.append({
                            "type": "usb",
                            "path": dev_path,
                            "vid": vid.zfill(4),
                            "pid": pid.zfill(4),
                            "manufacturer": manuf,
                            "product": prod,
                            "serial": serial
                        })
            except Exception:
                pass
                
    # 2. Scan /sys/class/hidraw
    for hid_path in glob.glob("/sys/class/hidraw/hidraw*"):
        uevent_f = os.path.join(hid_path, "device", "uevent")
        if os.path.exists(uevent_f):
            try:
                uevent_content = open(uevent_f).read()
                hid_id_m = re.search(r"HID_ID=[0-9A-Fa-f]+:([0-9A-Fa-f]+):([0-9A-Fa-f]+)", uevent_content)
                hid_name_m = re.search(r"HID_NAME=(.*)", uevent_content)
                driver_m = re.search(r"DRIVER=(.*)", uevent_content)
                
                if hid_id_m:
                    vid = hid_id_m.group(1).lstrip("0").lower()
                    pid = hid_id_m.group(2).lstrip("0").lower()
                    name = hid_name_m.group(1).strip() if hid_name_m else ""
                    driver = driver_m.group(1).strip() if driver_m else ""
                    
                    is_known_vid = vid in ["1ea7", "32e3", "04d9", "0c45"]
                    name_match = any(x in name.lower() for x in ["skyloong", "semite", "gk104", "gk6", "gaming keyboa", "nrf52"]) or driver == "semitek"
                    
                    if is_known_vid or name_match:
                        dev_node = f"/dev/{os.path.basename(hid_path)}"
                        has_rw = os.access(dev_node, os.R_OK | os.W_OK)
                        key = f"hidraw_{vid}_{pid}_{name}"
                        if key not in seen_keys:
                            seen_keys.add(key)
                            devices.append({
                                "type": "hidraw",
                                "path": hid_path,
                                "dev_node": dev_node,
                                "has_rw_permission": has_rw,
                                "vid": vid.zfill(4),
                                "pid": pid.zfill(4),
                                "name": name,
                                "driver": driver
                            })
            except Exception:
                pass

    # 3. Scan /proc/bus/input/devices for input subsystem device nodes
    if os.path.exists("/proc/bus/input/devices"):
        try:
            content = open("/proc/bus/input/devices", "r").read()
            blocks = content.strip().split("\n\n")
            for block in blocks:
                if any(x in block.lower() for x in ["1ea7", "32e3", "semite", "skyloong", "gk104"]):
                    name_m = re.search(r'N: Name="([^"]+)"', block)
                    vendor_m = re.search(r'Vendor=([0-9a-fA-F]+)', block)
                    product_m = re.search(r'Product=([0-9a-fA-F]+)', block)
                    
                    name = name_m.group(1) if name_m else "Semitek/Skyloong Input"
                    vid = vendor_m.group(1).lower().zfill(4) if vendor_m else "1ea7"
                    pid = product_m.group(1).lower().zfill(4) if product_m else "0907"
                    
                    key = f"input_{vid}_{pid}_{name}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        devices.append({
                            "type": "input",
                            "vid": vid,
                            "pid": pid,
                            "name": name,
                            "product": name
                        })
        except Exception:
            pass
                
    return devices

# Hardware Key Aliases for Split Spacebar and Modular Rotary Knobs (GK104 Pro)
HARDWARE_KEY_ALIASES = {
    # Split Spacebar
    "LeftSpace": "Space_17",
    "StandardSpace": "Space_18",
    "RightSpace": "Space_19",

    # Knob 1 (Esc Position / Main Knob)
    "Knob1_CW": "Space",
    "Knob1_CCW": "Space_2",
    "Knob1_Click": "Space_3",

    # Knob 2 (F11 Position)
    "Knob2_CCW": "Space_4",
    "Knob2_CW": "Space_5",
    "Knob2_Click": "Space_6",

    # Knob 3 (F12 Position)
    "Knob3_CCW": "Space_7",
    "Knob3_CW": "Space_8",
    "Knob3_Click": "Space_9",

    # Knob 4 (PrtSc Position)
    "Knob4_CW": "Space_10",
    "Knob4_CCW": "Space_11",
    "Knob4_Click": "Space_12",

    # Knob 5 (ScrLk Position)
    "Knob5_CW": "Space_13",
    "Knob5_CCW": "Space_14",
    "Knob5_Click": "Space_15",

    # Knob 6 (Pause Position)
    "Knob6_CW": "OpenMediaPlayer",
    "Knob6_CCW": "VolumeDown",
    "Knob6_Click": "Space_16"
}

# Knob structure definitions for UI and presets
KNOBS_METADATA = [
    {
        "id": "Knob1",
        "name": "Pokrętło 1 (Pozycja Esc / Główne)",
        "icon": "🎛️",
        "actions": [
            {"id": "Knob1_CW", "label": "Obrót w prawo (↻)", "default": "VolumeUp"},
            {"id": "Knob1_CCW", "label": "Obrót w lewo (↺)", "default": "VolumeDown"},
            {"id": "Knob1_Click", "label": "Wciśnięcie (Przycisk ⊙)", "default": "VolumeMute"}
        ]
    },
    {
        "id": "Knob2",
        "name": "Pokrętło 2 (Pozycja F11)",
        "icon": "🔊",
        "actions": [
            {"id": "Knob2_CW", "label": "Obrót w prawo (↻)", "default": "MediaNext"},
            {"id": "Knob2_CCW", "label": "Obrót w lewo (↺)", "default": "MediaPrevious"},
            {"id": "Knob2_Click", "label": "Wciśnięcie (Przycisk ⊙)", "default": "MediaPlayPause"}
        ]
    },
    {
        "id": "Knob3",
        "name": "Pokrętło 3 (Pozycja F12)",
        "icon": "🎵",
        "actions": [
            {"id": "Knob3_CW", "label": "Obrót w prawo (↻)", "default": "BrowserForward"},
            {"id": "Knob3_CCW", "label": "Obrót w lewo (↺)", "default": "BrowserBack"},
            {"id": "Knob3_Click", "label": "Wciśnięcie (Przycisk ⊙)", "default": "BrowserRefresh"}
        ]
    },
    {
        "id": "Knob4",
        "name": "Pokrętło 4 (Pozycja PrtSc)",
        "icon": "🌐",
        "actions": [
            {"id": "Knob4_CW", "label": "Obrót w prawo (↻)", "default": "VolumeUp"},
            {"id": "Knob4_CCW", "label": "Obrót w lewo (↺)", "default": "VolumeDown"},
            {"id": "Knob4_Click", "label": "Wciśnięcie (Przycisk ⊙)", "default": "VolumeMute"}
        ]
    },
    {
        "id": "Knob5",
        "name": "Pokrętło 5 (Pozycja ScrLk)",
        "icon": "📜",
        "actions": [
            {"id": "Knob5_CW", "label": "Obrót w prawo (↻)", "default": "VolumeUp"},
            {"id": "Knob5_CCW", "label": "Obrót w lewo (↺)", "default": "VolumeDown"},
            {"id": "Knob5_Click", "label": "Wciśnięcie (Przycisk ⊙)", "default": "VolumeMute"}
        ]
    },
    {
        "id": "Knob6",
        "name": "Pokrętło 6 (Pozycja Pause)",
        "icon": "⚙️",
        "actions": [
            {"id": "Knob6_CW", "label": "Obrót w prawo (↻)", "default": "OpenMediaPlayer"},
            {"id": "Knob6_CCW", "label": "Obrót w lewo (↺)", "default": "VolumeDown"},
            {"id": "Knob6_Click", "label": "Wciśnięcie (Przycisk ⊙)", "default": "VolumeMute"}
        ]
    }
]

# Knob Preset Schemes
KNOB_PRESETS = {
    "Głośność (Audio Volume)": {
        "CW": "VolumeUp",
        "CCW": "VolumeDown",
        "Click": "VolumeMute"
    },
    "Odtwarzacz Muzyki (Media Control)": {
        "CW": "MediaNext",
        "CCW": "MediaPrevious",
        "Click": "MediaPlayPause"
    },
    "Przeglądarka WWW (Browser Nav)": {
        "CW": "BrowserForward",
        "CCW": "BrowserBack",
        "Click": "BrowserRefresh"
    },
    "Przewijanie Strony (Page Scroll)": {
        "CW": "PageDown",
        "CCW": "PageUp",
        "Click": "Enter"
    },
    "Przełączanie Kart (Tab Switch)": {
        "CW": "LCtrl+Tab",
        "CCW": "LCtrl+LShift+Tab",
        "Click": "LCtrl+W"
    },
    "Zoom / Powiększenie": {
        "CW": "LCtrl+Add",
        "CCW": "LCtrl+Subtract",
        "Click": "LCtrl+D0"
    }
}

# 104 Keys definition with display names, positions, groups and modular knob indicators
KEY_DEFINITIONS = [
    # Row 1 (F-Row)
    {"id": "Esc", "label": "ESC", "group": "func", "row": 0, "col": 0, "knob_id": "Knob1", "knob_name": "Knob 1 (Główne / Esc)"},
    {"id": "F1", "label": "F1", "group": "func", "row": 0, "col": 2},
    {"id": "F2", "label": "F2", "group": "func", "row": 0, "col": 3},
    {"id": "F3", "label": "F3", "group": "func", "row": 0, "col": 4},
    {"id": "F4", "label": "F4", "group": "func", "row": 0, "col": 5},
    {"id": "F5", "label": "F5", "group": "func", "row": 0, "col": 6.5},
    {"id": "F6", "label": "F6", "group": "func", "row": 0, "col": 7.5},
    {"id": "F7", "label": "F7", "group": "func", "row": 0, "col": 8.5},
    {"id": "F8", "label": "F8", "group": "func", "row": 0, "col": 9.5},
    {"id": "F9", "label": "F9", "group": "func", "row": 0, "col": 11},
    {"id": "F10", "label": "F10", "group": "func", "row": 0, "col": 12},
    {"id": "F11", "label": "F11", "group": "func", "row": 0, "col": 13, "knob_id": "Knob2", "knob_name": "Knob 2 (F11)"},
    {"id": "F12", "label": "F12", "group": "func", "row": 0, "col": 14, "knob_id": "Knob3", "knob_name": "Knob 3 (F12)"},
    {"id": "Screenshot", "label": "PrtSc", "group": "nav", "row": 0, "col": 15.5, "knob_id": "Knob4", "knob_name": "Knob 4 (PrtSc)"},
    {"id": "ScrollLock", "label": "ScrLk", "group": "nav", "row": 0, "col": 16.5, "knob_id": "Knob5", "knob_name": "Knob 5 (ScrLk)"},
    {"id": "Pause", "label": "Pause", "group": "nav", "row": 0, "col": 17.5, "knob_id": "Knob6", "knob_name": "Knob 6 (Pause)"},

    # Row 2 (Numbers)
    {"id": "BackTick", "label": "`", "group": "alpha", "row": 1, "col": 0},
    {"id": "D1", "label": "1", "group": "alpha", "row": 1, "col": 1},
    {"id": "D2", "label": "2", "group": "alpha", "row": 1, "col": 2},
    {"id": "D3", "label": "3", "group": "alpha", "row": 1, "col": 3},
    {"id": "D4", "label": "4", "group": "alpha", "row": 1, "col": 4},
    {"id": "D5", "label": "5", "group": "alpha", "row": 1, "col": 5},
    {"id": "D6", "label": "6", "group": "alpha", "row": 1, "col": 6},
    {"id": "D7", "label": "7", "group": "alpha", "row": 1, "col": 7},
    {"id": "D8", "label": "8", "group": "alpha", "row": 1, "col": 8},
    {"id": "D9", "label": "9", "group": "alpha", "row": 1, "col": 9},
    {"id": "D0", "label": "0", "group": "alpha", "row": 1, "col": 10},
    {"id": "Subtract", "label": "-", "group": "alpha", "row": 1, "col": 11},
    {"id": "Add", "label": "=", "group": "alpha", "row": 1, "col": 12},
    {"id": "Backspace", "label": "Bksp", "group": "mod", "row": 1, "col": 13, "width": 2.0},
    {"id": "Insert", "label": "Ins", "group": "nav", "row": 1, "col": 15.5},
    {"id": "Home", "label": "Home", "group": "nav", "row": 1, "col": 16.5},
    {"id": "PageUp", "label": "PgUp", "group": "nav", "row": 1, "col": 17.5},
    {"id": "NumLock", "label": "Num", "group": "numpad", "row": 1, "col": 19},
    {"id": "NumPadSlash", "label": "/", "group": "numpad", "row": 1, "col": 20},
    {"id": "NumPadAsterisk", "label": "*", "group": "numpad", "row": 1, "col": 21},
    {"id": "NumPadSubtract", "label": "-", "group": "numpad", "row": 1, "col": 22},

    # Row 3 (QWERTY)
    {"id": "Tab", "label": "Tab", "group": "mod", "row": 2, "col": 0, "width": 1.5},
    {"id": "Q", "label": "Q", "group": "alpha", "row": 2, "col": 1.5},
    {"id": "W", "label": "W", "group": "wasd", "row": 2, "col": 2.5},
    {"id": "E", "label": "E", "group": "alpha", "row": 2, "col": 3.5},
    {"id": "R", "label": "R", "group": "alpha", "row": 2, "col": 4.5},
    {"id": "T", "label": "T", "group": "alpha", "row": 2, "col": 5.5},
    {"id": "Y", "label": "Y", "group": "alpha", "row": 2, "col": 6.5},
    {"id": "U", "label": "U", "group": "alpha", "row": 2, "col": 7.5},
    {"id": "I", "label": "I", "group": "alpha", "row": 2, "col": 8.5},
    {"id": "O", "label": "O", "group": "alpha", "row": 2, "col": 9.5},
    {"id": "P", "label": "P", "group": "alpha", "row": 2, "col": 10.5},
    {"id": "OpenSquareBrace", "label": "[", "group": "alpha", "row": 2, "col": 11.5},
    {"id": "CloseSquareBrace", "label": "]", "group": "alpha", "row": 2, "col": 12.5},
    {"id": "Backslash", "label": "\\", "group": "alpha", "row": 2, "col": 13.5, "width": 1.5},
    {"id": "Delete", "label": "Del", "group": "nav", "row": 2, "col": 15.5},
    {"id": "End", "label": "End", "group": "nav", "row": 2, "col": 16.5},
    {"id": "PageDown", "label": "PgDn", "group": "nav", "row": 2, "col": 17.5},
    {"id": "NumPad7", "label": "7", "group": "numpad", "row": 2, "col": 19},
    {"id": "NumPad8", "label": "8", "group": "numpad", "row": 2, "col": 20},
    {"id": "NumPad9", "label": "9", "group": "numpad", "row": 2, "col": 21},
    {"id": "NumPadAdd", "label": "+", "group": "numpad", "row": 2, "col": 22, "height": 2.0},

    # Row 4 (ASDF)
    {"id": "CapsLock", "label": "Caps", "group": "mod", "row": 3, "col": 0, "width": 1.75},
    {"id": "A", "label": "A", "group": "wasd", "row": 3, "col": 1.75},
    {"id": "S", "label": "S", "group": "wasd", "row": 3, "col": 2.75},
    {"id": "D", "label": "D", "group": "wasd", "row": 3, "col": 3.75},
    {"id": "F", "label": "F", "group": "alpha", "row": 3, "col": 4.75},
    {"id": "G", "label": "G", "group": "alpha", "row": 3, "col": 5.75},
    {"id": "H", "label": "H", "group": "alpha", "row": 3, "col": 6.75},
    {"id": "J", "label": "J", "group": "alpha", "row": 3, "col": 7.75},
    {"id": "K", "label": "K", "group": "alpha", "row": 3, "col": 8.75},
    {"id": "L", "label": "L", "group": "alpha", "row": 3, "col": 9.75},
    {"id": "Semicolon", "label": ";", "group": "alpha", "row": 3, "col": 10.75},
    {"id": "Quotes", "label": "'", "group": "alpha", "row": 3, "col": 11.75},
    {"id": "Enter", "label": "Enter", "group": "mod", "row": 3, "col": 12.75, "width": 2.25},
    {"id": "NumPad4", "label": "4", "group": "numpad", "row": 3, "col": 19},
    {"id": "NumPad5", "label": "5", "group": "numpad", "row": 3, "col": 20},
    {"id": "NumPad6", "label": "6", "group": "numpad", "row": 3, "col": 21},

    # Row 5 (ZXCV)
    {"id": "LShift", "label": "Shift", "group": "mod", "row": 4, "col": 0, "width": 2.25},
    {"id": "Z", "label": "Z", "group": "alpha", "row": 4, "col": 2.25},
    {"id": "X", "label": "X", "group": "alpha", "row": 4, "col": 3.25},
    {"id": "C", "label": "C", "group": "alpha", "row": 4, "col": 4.25},
    {"id": "V", "label": "V", "group": "alpha", "row": 4, "col": 5.25},
    {"id": "B", "label": "B", "group": "alpha", "row": 4, "col": 6.25},
    {"id": "N", "label": "N", "group": "alpha", "row": 4, "col": 7.25},
    {"id": "M", "label": "M", "group": "alpha", "row": 4, "col": 8.25},
    {"id": "Comma", "label": ",", "group": "alpha", "row": 4, "col": 9.25},
    {"id": "Period", "label": ".", "group": "alpha", "row": 4, "col": 10.25},
    {"id": "Slash", "label": "/", "group": "alpha", "row": 4, "col": 11.25},
    {"id": "RShift", "label": "Shift", "group": "mod", "row": 4, "col": 12.25, "width": 2.75},
    {"id": "Up", "label": "▲", "group": "arrows", "row": 4, "col": 16.5},
    {"id": "NumPad1", "label": "1", "group": "numpad", "row": 4, "col": 19},
    {"id": "NumPad2", "label": "2", "group": "numpad", "row": 4, "col": 20},
    {"id": "NumPad3", "label": "3", "group": "numpad", "row": 4, "col": 21},
    {"id": "NumPadEnter", "label": "Ent", "group": "numpad", "row": 4, "col": 22, "height": 2.0},

    # Row 6 (Bottom row)
    {"id": "LCtrl", "label": "Ctrl", "group": "mod", "row": 5, "col": 0, "width": 1.25},
    {"id": "LWin", "label": "Win", "group": "mod", "row": 5, "col": 1.25, "width": 1.25},
    {"id": "LAlt", "label": "Alt", "group": "mod", "row": 5, "col": 2.5, "width": 1.25},
    {"id": "Space_18", "label": "Space", "group": "mod", "row": 5, "col": 3.75, "width": 6.25},
    {"id": "RAlt", "label": "Alt", "group": "mod", "row": 5, "col": 10.0, "width": 1.25},
    {"id": "Menu", "label": "Fn/Menu", "group": "mod", "row": 5, "col": 11.25, "width": 1.25},
    {"id": "RCtrl", "label": "Ctrl", "group": "mod", "row": 5, "col": 12.5, "width": 1.25},
    {"id": "Left", "label": "◄", "group": "arrows", "row": 5, "col": 15.5},
    {"id": "Down", "label": "▼", "group": "arrows", "row": 5, "col": 16.5},
    {"id": "Right", "label": "►", "group": "arrows", "row": 5, "col": 17.5},
    {"id": "NumPad0", "label": "0", "group": "numpad", "row": 5, "col": 19, "width": 2.0},
    {"id": "NumPadPeriod", "label": ".", "group": "numpad", "row": 5, "col": 21}
]

# Supported hardware layers for remapping
AVAILABLE_LAYERS = [
    ("Base", "Warstwa Podstawowa (Base)"),
    ("Layer1", "Warstwa 1 (Layer 1)"),
    ("Layer2", "Warstwa 2 (Layer 2)"),
    ("Layer3", "Warstwa 3 (Layer 3)"),
    ("FnLayer1", "Warstwa Fn + 1 (FnLayer1)"),
    ("FnLayer2", "Warstwa Fn + 2 (FnLayer2)"),
    ("FnLayer3", "Warstwa Fn + 3 (FnLayer3)")
]

# Categorized target keys for remapping
TARGET_KEY_CATEGORIES = {
    "Podstawowe (Alfanumeryczne)": [
        ("A", "Litera A"), ("B", "Litera B"), ("C", "Litera C"), ("D", "Litera D"),
        ("E", "Litera E"), ("F", "Litera F"), ("G", "Litera G"), ("H", "Litera H"),
        ("I", "Litera I"), ("J", "Litera J"), ("K", "Litera K"), ("L", "Litera L"),
        ("M", "Litera M"), ("N", "Litera N"), ("O", "Litera O"), ("P", "Litera P"),
        ("Q", "Litera Q"), ("R", "Litera R"), ("S", "Litera S"), ("T", "Litera T"),
        ("U", "Litera U"), ("V", "Litera V"), ("W", "Litera W"), ("X", "Litera X"),
        ("Y", "Litera Y"), ("Z", "Litera Z"),
        ("D1", "Cyfra 1"), ("D2", "Cyfra 2"), ("D3", "Cyfra 3"), ("D4", "Cyfra 4"),
        ("D5", "Cyfra 5"), ("D6", "Cyfra 6"), ("D7", "Cyfra 7"), ("D8", "Cyfra 8"),
        ("D9", "Cyfra 9"), ("D0", "Cyfra 0"),
        ("BackTick", "Znak ` (Backtick)"), ("Subtract", "Znak - (Minus)"), ("Add", "Znak = (Równa się)"),
        ("OpenSquareBrace", "Znak ["), ("CloseSquareBrace", "Znak ]"), ("Backslash", "Znak \\"),
        ("Semicolon", "Znak ; (Średnik)"), ("Quotes", "Znak ' (Apostrof)"),
        ("Comma", "Znak , (Przecinek)"), ("Period", "Znak . (Kropka)"), ("Slash", "Znak / (Ukośnik)")
    ],
    "Klawisze Funkcyjne (F1 - F24)": [
        ("F1", "F1"), ("F2", "F2"), ("F3", "F3"), ("F4", "F4"),
        ("F5", "F5"), ("F6", "F6"), ("F7", "F7"), ("F8", "F8"),
        ("F9", "F9"), ("F10", "F10"), ("F11", "F11"), ("F12", "F12"),
        ("F13", "F13"), ("F14", "F14"), ("F15", "F15"), ("F16", "F16"),
        ("F17", "F17"), ("F18", "F18"), ("F19", "F19"), ("F20", "F20"),
        ("F21", "F21"), ("F22", "F22"), ("F23", "F23"), ("F24", "F24")
    ],
    "Nawigacja i Sterowanie": [
        ("Esc", "Escape (Esc)"), ("Tab", "Tabulator (Tab)"), ("CapsLock", "Caps Lock"),
        ("Backspace", "Backspace"), ("Enter", "Enter"), ("Space", "Spacja (Space)"),
        ("LeftSpace", "Lewa Spacja (Left Space)"), ("RightSpace", "Prawa Spacja (Right Space)"),
        ("Insert", "Insert (Ins)"), ("Delete", "Delete (Del)"),
        ("Home", "Home"), ("End", "End"),
        ("PageUp", "Page Up (PgUp)"), ("PageDown", "Page Down (PgDn)"),
        ("Up", "Strzałka w górę (▲)"), ("Down", "Strzałka w dół (▼)"),
        ("Left", "Strzałka w lewo (◄)"), ("Right", "Strzałka w prawo (►)"),
        ("Screenshot", "Print Screen (Zrzut ekranu)"),
        ("ScrollLock", "Scroll Lock"), ("Pause", "Pause / Break")
    ],
    "Modyfikatory": [
        ("LCtrl", "Lewy Control (LCtrl)"), ("RCtrl", "Prawy Control (RCtrl)"),
        ("LShift", "Lewy Shift (LShift)"), ("RShift", "Prawy Shift (RShift)"),
        ("LAlt", "Lewy Alt (LAlt)"), ("RAlt", "Prawy Alt / AltGr (RAlt)"),
        ("LWin", "Lewy Klawisz Windows (LWin)"), ("RWin", "Prawy Klawisz Windows (RWin)"),
        ("Menu", "Menu kontekstowe (App/Menu)")
    ],
    "Klawiatura Numeryczna (NumPad)": [
        ("NumLock", "Num Lock"),
        ("NumPad0", "Num 0"), ("NumPad1", "Num 1"), ("NumPad2", "Num 2"),
        ("NumPad3", "Num 3"), ("NumPad4", "Num 4"), ("NumPad5", "Num 5"),
        ("NumPad6", "Num 6"), ("NumPad7", "Num 7"), ("NumPad8", "Num 8"),
        ("NumPad9", "Num 9"),
        ("NumPadAdd", "Num + (Dodawanie)"), ("NumPadSubtract", "Num - (Odejmowanie)"),
        ("NumPadMultiply", "Num * (Mnożenie)"), ("NumPadSlash", "Num / (Dzielenie)"),
        ("NumPadPeriod", "Num . (Kropka)"), ("NumPadEnter", "Num Enter")
    ],
    "Multimedia i Audio": [
        ("VolumeUp", "🔊 Głośność + (Volume Up)"),
        ("VolumeDown", "🔉 Głośność - (Volume Down)"),
        ("VolumeMute", "🔇 Wycisz dźwięk (Mute)"),
        ("MediaPlayPause", "⏯️ Odtwarzaj / Pauza"),
        ("MediaNext", "⏭️ Następny utwór"),
        ("MediaPrevious", "⏮️ Poprzedni utwór"),
        ("MediaStop", "⏹️ Zatrzymaj odtwarzanie"),
        ("OpenMediaPlayer", "🎵 Otwórz Odtwarzacz Muzyki"),
        ("OpenCalculator", "🧮 Otwórz Kalkulator"),
        ("OpenMyComputer", "💻 Mój Komputer / Eksplorator"),
        ("OpenEmail", "✉️ Program pocztowy (Email)")
    ],
    "Przeglądarka i Internet": [
        ("BrowserHome", "🏠 Strona główna"),
        ("BrowserBack", "⬅️ Wstecz w przeglądarce"),
        ("BrowserForward", "➡️ Dalej w przeglądarce"),
        ("BrowserRefresh", "🔄 Odśwież stronę"),
        ("BrowserStop", "🛑 Zatrzymaj ładowanie"),
        ("BrowserFavorites", "⭐ Ulubione / Zakładki"),
        ("BrowserSearch", "🔍 Szukaj w internecie")
    ]
}

# Popular shortcut presets
POPULAR_SHORTCUTS = [
    ("LCtrl+C", "Kopiuj (Ctrl + C)"),
    ("LCtrl+V", "Wklej (Ctrl + V)"),
    ("LCtrl+X", "Wytnij (Ctrl + X)"),
    ("LCtrl+Z", "Cofnij (Ctrl + Z)"),
    ("LCtrl+Y", "Ponów (Ctrl + Y)"),
    ("LCtrl+A", "Zaznacz wszystko (Ctrl + A)"),
    ("LCtrl+S", "Zapisz (Ctrl + S)"),
    ("LAlt+Tab", "Przełącz okno (Alt + Tab)"),
    ("LAlt+F4", "Zamknij okno (Alt + F4)"),
    ("LWin+D", "Pokaż pulpit (Win + D)"),
    ("LWin+E", "Menedżer plików (Win + E)"),
    ("LCtrl+LShift+Escape", "Menedżer zadań (Ctrl + Shift + Esc)"),
    ("LWin+LShift+S", "Wycinek ekranu (Win + Shift + S)")
]

# Preset RGB themes
COLOR_PRESETS = {
    "Cyberpunk 2077": {
        "all": "#ff0055",
        "wasd": "#00ffff",
        "arrows": "#ffe600",
        "numpad": "#00ffff",
        "func": "#ffe600"
    },
    "Synthwave Neon": {
        "all": "#2b0054",
        "wasd": "#ff007f",
        "arrows": "#00ffff",
        "alpha": "#7928ca",
        "mod": "#ff007f",
        "func": "#00ffff",
        "numpad": "#ff007f"
    },
    "Matrix Green": {
        "all": "#002200",
        "wasd": "#00ff33",
        "alpha": "#00bb22",
        "arrows": "#00ff33",
        "mod": "#005511",
        "func": "#00bb22",
        "numpad": "#00aa22"
    },
    "Sunset Glow": {
        "all": "#ff3b00",
        "wasd": "#ffe600",
        "alpha": "#ff6600",
        "arrows": "#ffe600",
        "mod": "#cc0066",
        "func": "#ff0055",
        "numpad": "#ff3b00"
    },
    "Ice Blizzard": {
        "all": "#003366",
        "wasd": "#00ffff",
        "alpha": "#66ccff",
        "arrows": "#00ffff",
        "mod": "#002244",
        "func": "#e0ffff",
        "numpad": "#66ccff"
    },
    "Blood Red": {
        "all": "#330000",
        "wasd": "#ff0000",
        "alpha": "#880000",
        "arrows": "#ff0000",
        "mod": "#440000",
        "func": "#ff2222",
        "numpad": "#880000"
    }
}


class MacroAction:
    def __init__(self, action_type: str = "Press", key: str = "A", delay: int = 0):
        self.action_type = action_type  # "Press", "Down", "Up"
        self.key = key
        self.delay = delay  # ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.action_type,
            "key": self.key,
            "delay": self.delay
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MacroAction':
        return cls(
            action_type=data.get("type", "Press"),
            key=data.get("key", "A"),
            delay=data.get("delay", 0)
        )

    def to_code_line(self) -> str:
        if self.delay > 0:
            return f"{self.action_type}:{self.key}:{self.delay}"
        return f"{self.action_type}:{self.key}"


class MacroItem:
    def __init__(self, name: str = "NewMacro", default_delay: int = 0,
                 repeat_type: str = "RepeatXTimes", repeat_count: int = 1,
                 actions: Optional[List[MacroAction]] = None):
        self.name = name
        self.default_delay = default_delay
        self.repeat_type = repeat_type  # "RepeatXTimes", "ReleaseKeyToStop", "PressKeyAgainToStop"
        self.repeat_count = repeat_count
        self.actions = actions if actions is not None else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "default_delay": self.default_delay,
            "repeat_type": self.repeat_type,
            "repeat_count": self.repeat_count,
            "actions": [a.to_dict() for a in self.actions]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MacroItem':
        actions = [MacroAction.from_dict(a) for a in data.get("actions", [])]
        return cls(
            name=data.get("name", "NewMacro"),
            default_delay=data.get("default_delay", 0),
            repeat_type=data.get("repeat_type", "RepeatXTimes"),
            repeat_count=data.get("repeat_count", 1),
            actions=actions
        )

    def generate_code_block(self) -> str:
        # Hardware buffer limit for GK6X / Semitek is max 60 actions per macro
        header = f"[Macro({self.name},{self.default_delay},{self.repeat_type},{self.repeat_count})]"
        lines = [header]
        safe_actions = self.actions[:60]
        for a in safe_actions:
            lines.append(a.to_code_line())
        return "\n".join(lines)


def get_system_battery_info() -> Dict[str, Any]:
    """Read system power supply and peripheral battery details."""
    import glob
    res = {
        "has_battery": False,
        "percentage": 100,
        "status": "Unknown",
        "is_charging": False,
        "details_str": "Brak danych o baterii",
        "icon": "🔋",
        "devices": []
    }
    
    # 1. Search sysfs batteries (e.g. BAT0 on laptops like GPD Win Max 2)
    bat_dirs = sorted(glob.glob('/sys/class/power_supply/BAT*'))
    for b_dir in bat_dirs:
        try:
            name = os.path.basename(b_dir)
            cap_file = os.path.join(b_dir, 'capacity')
            status_file = os.path.join(b_dir, 'status')
            
            cap = 100
            if os.path.exists(cap_file):
                cap = int(open(cap_file).read().strip())
            
            st = "Unknown"
            if os.path.exists(status_file):
                st = open(status_file).read().strip()
            
            is_charging = st.lower() in ["charging", "full"]
            
            icon = "🔋"
            if is_charging:
                icon = "⚡"
            elif cap <= 20:
                icon = "🪫"
            
            status_pl = {
                "Full": "Pełna (100%)",
                "Charging": "Ładowanie",
                "Discharging": "Rozładowywanie",
                "Not charging": "Zasilacz podłączony (nie ładuje)",
                "Unknown": "Podłączona"
            }.get(st, st)

            res["has_battery"] = True
            res["percentage"] = cap
            res["status"] = st
            res["is_charging"] = is_charging
            res["icon"] = icon
            res["details_str"] = f"{icon} Bateria laptopa ({name}): {cap}% — {status_pl}"
            res["devices"].append({
                "name": f"Laptop ({name})",
                "percentage": cap,
                "status": status_pl,
                "icon": icon
            })
            break # Primary battery found
        except Exception:
            pass
            
    return res


class ApplyWorker(QThread):
    finished_signal = Signal(bool, str)

    def __init__(self, config_text: str, model_id: str):
        super().__init__()
        self.config_text = config_text
        self.model_id = model_id

    def run(self):
        try:
            os.makedirs(USERDATA_DIR, exist_ok=True)
            cfg_file = os.path.join(USERDATA_DIR, f"{self.model_id}.txt")
            with open(cfg_file, "w", encoding="utf-8") as f:
                f.write(self.config_text)

            if shutil.which("mono") and os.path.exists(EXE_PATH):
                res = subprocess.run(
                    ["mono", EXE_PATH, "/map"],
                    cwd=APP_DIR,
                    capture_output=True,
                    text=True,
                    timeout=15
                )

                if "Connected to device" in res.stdout and "Done" in res.stdout:
                    self.finished_signal.emit(True, "Konfiguracja pomyślnie wgrana do pamięci klawiatury!")
                else:
                    out = res.stdout + "\n" + res.stderr
                    self.finished_signal.emit(False, f"Błąd wgrywania przez GK6X: {out.strip()}")
            else:
                self.finished_signal.emit(
                    True,
                    f"Konfiguracja pomyślnie przygotowana i zapisana w UserData/{self.model_id}.txt oraz profilu!"
                )
        except Exception as e:
            self.finished_signal.emit(False, f"Wyjątek: {str(e)}")


class UnmapWorker(QThread):
    finished_signal = Signal(bool, str)

    def run(self):
        try:
            if shutil.which("mono") and os.path.exists(EXE_PATH):
                res = subprocess.run(
                    ["mono", EXE_PATH, "/unmap"],
                    cwd=APP_DIR,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if "Connected to device" in res.stdout and "Done" in res.stdout:
                    self.finished_signal.emit(True, "Zresetowano mapowanie klawiszy do ustawień fabrycznych!")
                else:
                    out = res.stdout + "\n" + res.stderr
                    self.finished_signal.emit(False, f"Błąd resetowania: {out.strip()}")
            else:
                self.finished_signal.emit(True, "Zresetowano mapowanie klawiszy do ustawień fabrycznych w profilu!")
        except Exception as e:
            self.finished_signal.emit(False, f"Wyjątek: {str(e)}")


class GKBackend(QObject):
    device_status_signal = Signal(bool, str, str)  # is_connected, model_id, model_name
    apply_finished = Signal(bool, str)
    unmap_finished = Signal(bool, str)

    def __init__(self):
        super().__init__()
        self.current_model_id = "656802056"
        self.current_device_name = "Skyloong GK104 Pro (104RGB)"
        self.worker: Optional[ApplyWorker] = None
        self.unmap_worker: Optional[UnmapWorker] = None

        # State storage
        self.remaps: Dict[str, Dict[str, str]] = {layer_id: {} for layer_id, _ in AVAILABLE_LAYERS}
        self.macros: Dict[str, MacroItem] = {}
        self.lighting_config: Dict[str, Any] = {
            "mode": "preset",  # "preset", "static", "off"
            "preset_name": "Spectral Cycle",
            "layer": "Base",
            "static_colors": {k["id"]: "#00ffff" for k in KEY_DEFINITIONS}
        }

        self.load_profile()

    def detect_device(self) -> Tuple[bool, str, str]:
        """Detect connected device using native Linux USB/sysfs inspection and GK6X."""
        self.last_device_info = {}
        self.has_permission_issue = False
        
        # 1. Try Mono GK6X dumpkeys if mono is installed and executable exists
        if shutil.which("mono") and os.path.exists(EXE_PATH):
            try:
                res = subprocess.run(
                    ["mono", EXE_PATH, "/dumpkeys"],
                    cwd=APP_DIR,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                stdout = res.stdout
                if "Connected to device" in stdout:
                    m = re.search(r"Connected to device '([^']+)' model:(\d+)", stdout)
                    if m:
                        dev_name = f"Skyloong {m.group(1)}"
                        model_id = m.group(2)
                        self.current_model_id = model_id
                        self.current_device_name = dev_name
                        self.last_device_info = {"name": dev_name, "model_id": model_id, "mode": "GK6X Native"}
                        self.device_status_signal.emit(True, model_id, dev_name)
                        return True, model_id, dev_name
            except Exception as e:
                print(f"Mono detection note: {e}")

        # 2. Native Linux Hardware Detection via sysfs / USB / hidraw / input
        usb_devs = scan_linux_usb_devices()
        
        kb_dev = None
        dongle_dev = None
        for dev in usb_devs:
            vid = dev.get("vid", "").lower()
            pid = dev.get("pid", "").lower()
            if (vid == "1ea7" and pid == "0907") or (vid == "32e3" and pid in ["00f7", "f7"]):
                kb_dev = dev
                break
            elif vid == "1ea7" and pid == "0067":
                dongle_dev = dev
            elif any(x in dev.get("product", "").lower() or x in dev.get("name", "").lower() for x in ["gaming keyboar", "semite", "skyloong", "gk104"]):
                kb_dev = dev
            elif dev.get("driver") == "semitek":
                kb_dev = dev

        # Check hidraw permissions
        diag = SystemChecker.check_hidraw_permissions()
        if not diag["has_access"] and not SystemChecker.check_udev_rules()["installed"]:
            self.has_permission_issue = True

        if kb_dev:
            model_id = "656802056"  # GK104 Pro 104RGB default model
            dev_name = "Skyloong GK104 Pro (104RGB USB)"
            self.current_model_id = model_id
            self.current_device_name = dev_name
            self.last_device_info = kb_dev
            self.device_status_signal.emit(True, model_id, dev_name)
            return True, model_id, dev_name
        elif dongle_dev:
            model_id = "656802056"
            dev_name = "Skyloong GK104 Pro (Odbiornik 2.4GHz / nRF52)"
            self.current_model_id = model_id
            self.current_device_name = dev_name
            self.last_device_info = dongle_dev
            self.device_status_signal.emit(True, model_id, dev_name)
            return True, model_id, dev_name
        elif usb_devs:
            first = usb_devs[0]
            model_id = "656802056"
            prod_name = first.get("product") or first.get("name") or "GK104 Pro"
            dev_name = f"Skyloong {prod_name} [{first.get('vid')}:{first.get('pid')}]"
            self.current_model_id = model_id
            self.current_device_name = dev_name
            self.last_device_info = first
            self.device_status_signal.emit(True, model_id, dev_name)
            return True, model_id, dev_name

        self.device_status_signal.emit(False, self.current_model_id, "Nie wykryto urządzenia")
        return False, self.current_model_id, "Nie wykryto urządzenia"

    def get_available_effects(self) -> List[Dict[str, str]]:
        """List all available .le files categorized."""
        effects = []
        if not os.path.exists(LIGHTING_DIR):
            return effects

        for fname in sorted(os.listdir(LIGHTING_DIR)):
            if fname.endswith(".le"):
                name = fname[:-3]
                category = self._categorize_effect(name)
                effects.append({
                    "name": name,
                    "filename": fname,
                    "category": category
                })
        return effects

    def _categorize_effect(self, name: str) -> str:
        lower = name.lower()
        if "rainbow" in lower or "spectral" in lower or "rgb" in lower:
            return "Tęcza / Rainbow"
        elif "breath" in lower or "respiration" in lower:
            return "Oddychanie / Breathing"
        elif "wave" in lower or "streamer" in lower or "flow" in lower:
            return "Fala / Wave"
        elif "meteor" in lower or "star" in lower or "shuttle" in lower:
            return "Gwiazdy / Meteor"
        elif "windmill" in lower:
            return "Wiatrak / Windmill"
        elif "static" in lower:
            return "Statyczne / Static"
        else:
            return "Dynamiczne / Dynamic"

    # ==========================
    # REMAP & MACRO MANAGEMENT
    # ==========================
    def set_key_remap(self, layer: str, source_key: str, target_action: str):
        if layer not in self.remaps:
            self.remaps[layer] = {}
        if not target_action or target_action == "Default":
            if source_key in self.remaps[layer]:
                del self.remaps[layer][source_key]
        else:
            self.remaps[layer][source_key] = target_action
        self.save_profile()

    def remove_key_remap(self, layer: str, source_key: str):
        if layer in self.remaps and source_key in self.remaps[layer]:
            del self.remaps[layer][source_key]
            self.save_profile()

    def clear_layer_remaps(self, layer: str):
        if layer in self.remaps:
            self.remaps[layer] = {}
            self.save_profile()

    def get_remaps_for_layer(self, layer: str) -> Dict[str, str]:
        return self.remaps.get(layer, {})

    def add_or_update_macro(self, macro: MacroItem):
        self.macros[macro.name] = macro
        self.save_profile()

    def delete_macro(self, macro_name: str):
        if macro_name in self.macros:
            del self.macros[macro_name]
            # Remove any remaps referencing this macro
            macro_ref = f"Macro({macro_name})"
            for layer, mappings in self.remaps.items():
                keys_to_remove = [k for k, v in mappings.items() if v == macro_ref]
                for k in keys_to_remove:
                    del mappings[k]
            self.save_profile()

    @staticmethod
    def text_to_macro_actions(text: str, char_delay: int = 20) -> List[MacroAction]:
        """Convert a text string into a series of MacroAction presses."""
        actions: List[MacroAction] = []
        for ch in text:
            if ch.isalpha():
                if ch.isupper():
                    actions.append(MacroAction(action_type="Press", key=f"LShift+{ch.upper()}", delay=char_delay))
                else:
                    actions.append(MacroAction(action_type="Press", key=ch.upper(), delay=char_delay))
            elif ch.isdigit():
                actions.append(MacroAction(action_type="Press", key=f"D{ch}", delay=char_delay))
            elif ch == " ":
                actions.append(MacroAction(action_type="Press", key="Space", delay=char_delay))
            elif ch == "\n":
                actions.append(MacroAction(action_type="Press", key="Enter", delay=char_delay))
            elif ch == "\t":
                actions.append(MacroAction(action_type="Press", key="Tab", delay=char_delay))
            elif ch == "-":
                actions.append(MacroAction(action_type="Press", key="Subtract", delay=char_delay))
            elif ch == "=":
                actions.append(MacroAction(action_type="Press", key="Add", delay=char_delay))
            elif ch == "_":
                actions.append(MacroAction(action_type="Press", key="LShift+Subtract", delay=char_delay))
            elif ch == "+":
                actions.append(MacroAction(action_type="Press", key="LShift+Add", delay=char_delay))
            elif ch == "!":
                actions.append(MacroAction(action_type="Press", key="LShift+D1", delay=char_delay))
            elif ch == "@":
                actions.append(MacroAction(action_type="Press", key="LShift+D2", delay=char_delay))
            elif ch == "#":
                actions.append(MacroAction(action_type="Press", key="LShift+D3", delay=char_delay))
            elif ch == "$":
                actions.append(MacroAction(action_type="Press", key="LShift+D4", delay=char_delay))
            elif ch == "%":
                actions.append(MacroAction(action_type="Press", key="LShift+D5", delay=char_delay))
            elif ch == "^":
                actions.append(MacroAction(action_type="Press", key="LShift+D6", delay=char_delay))
            elif ch == "&":
                actions.append(MacroAction(action_type="Press", key="LShift+D7", delay=char_delay))
            elif ch == "*":
                actions.append(MacroAction(action_type="Press", key="LShift+D8", delay=char_delay))
            elif ch == "(":
                actions.append(MacroAction(action_type="Press", key="LShift+D9", delay=char_delay))
            elif ch == ")":
                actions.append(MacroAction(action_type="Press", key="LShift+D0", delay=char_delay))
            elif ch == "[":
                actions.append(MacroAction(action_type="Press", key="OpenSquareBrace", delay=char_delay))
            elif ch == "]":
                actions.append(MacroAction(action_type="Press", key="CloseSquareBrace", delay=char_delay))
            elif ch == ";":
                actions.append(MacroAction(action_type="Press", key="Semicolon", delay=char_delay))
            elif ch == ":":
                actions.append(MacroAction(action_type="Press", key="LShift+Semicolon", delay=char_delay))
            elif ch == "'":
                actions.append(MacroAction(action_type="Press", key="Quotes", delay=char_delay))
            elif ch == '"':
                actions.append(MacroAction(action_type="Press", key="LShift+Quotes", delay=char_delay))
            elif ch == ",":
                actions.append(MacroAction(action_type="Press", key="Comma", delay=char_delay))
            elif ch == "<":
                actions.append(MacroAction(action_type="Press", key="LShift+Comma", delay=char_delay))
            elif ch == ".":
                actions.append(MacroAction(action_type="Press", key="Period", delay=char_delay))
            elif ch == ">":
                actions.append(MacroAction(action_type="Press", key="LShift+Period", delay=char_delay))
            elif ch == "/":
                actions.append(MacroAction(action_type="Press", key="Slash", delay=char_delay))
            elif ch == "?":
                actions.append(MacroAction(action_type="Press", key="LShift+Slash", delay=char_delay))
            elif ch == "\\":
                actions.append(MacroAction(action_type="Press", key="Backslash", delay=char_delay))
            elif ch == "|":
                actions.append(MacroAction(action_type="Press", key="LShift+Backslash", delay=char_delay))
            elif ch == "`":
                actions.append(MacroAction(action_type="Press", key="BackTick", delay=char_delay))
            elif ch == "~":
                actions.append(MacroAction(action_type="Press", key="LShift+BackTick", delay=char_delay))
        return actions

    # ==========================
    # CONFIG FILE GENERATION
    # ==========================
    def generate_full_config(self) -> str:
        """Generate full UserData txt file content containing aliases, macros, remaps, and lighting."""
        blocks: List[str] = []

        # 1. Hardware Key Aliases (Split Space & Knobs)
        blocks.append("# ==========================\n# KEY ALIASES (GK104 Pro Knobs & Split Space)\n# ==========================")
        alias_lines = ["[KeyAlias]"]
        for alias_name, real_key in HARDWARE_KEY_ALIASES.items():
            alias_lines.append(f"{alias_name}:{real_key}")
        blocks.append("\n".join(alias_lines) + "\n")

        # 2. Macros
        if self.macros:
            blocks.append("# ==========================\n# MACROS DEFINITIONS\n# ==========================")
            for m in self.macros.values():
                blocks.append(m.generate_code_block() + "\n")

        # 3. Key Remapping Layers
        has_remaps = any(len(mappings) > 0 for mappings in self.remaps.values())
        if has_remaps:
            blocks.append("# ==========================\n# KEY REMAPPINGS\n# ==========================")
            for layer_id, _ in AVAILABLE_LAYERS:
                layer_map = self.remaps.get(layer_id, {})
                if layer_map:
                    layer_block = [f"[{layer_id}]"]
                    for src, dst in layer_map.items():
                        # Map legacy names if present
                        mapped_src = src
                        if src == "Space_18" or src == "Space":
                            mapped_src = "StandardSpace"
                        elif src == "Space_17":
                            mapped_src = "LeftSpace"
                        elif src == "Space_19":
                            mapped_src = "RightSpace"
                        layer_block.append(f"{mapped_src}:{dst}")
                    blocks.append("\n".join(layer_block) + "\n")

        # 4. Lighting Configuration
        blocks.append("# ==========================\n# LIGHTING CONFIGURATION\n# ==========================")
        mode = self.lighting_config.get("mode", "preset")
        layer = self.lighting_config.get("layer", "Base")
        brightness = int(self.lighting_config.get("brightness", 100))

        if mode == "off" or brightness <= 0:
            blocks.append("[NoLighting]\n")
        elif mode == "static":
            preset_name = "CustomGUIStatic"
            static_colors = self.lighting_config.get("static_colors", {})
            self._save_static_le_file(preset_name, static_colors, brightness=brightness)
            # Apply to all main layers so the keyboard never goes dark when switching layers or connection modes
            blocks.append(f"[Lighting({preset_name},Base)]")
            blocks.append(f"[Lighting({preset_name},Layer1)]")
            blocks.append(f"[Lighting({preset_name},Layer2)]")
            blocks.append(f"[Lighting({preset_name},Layer3)]\n")
        else:
            preset_name = self.lighting_config.get("preset_name", "Spectral Cycle")
            actual_preset = self._prepare_preset_lighting(preset_name, brightness=brightness)
            # Apply to all main layers so the keyboard stays lit on Windows (Layer 1), Mac (Layer 2) and Base
            blocks.append(f"[Lighting({actual_preset},Base)]")
            blocks.append(f"[Lighting({actual_preset},Layer1)]")
            blocks.append(f"[Lighting({actual_preset},Layer2)]")
            blocks.append(f"[Lighting({actual_preset},Layer3)]\n")

        return "\n".join(blocks)

    def _prepare_preset_lighting(self, preset_name: str, brightness: int = 100) -> str:
        """Create a brightness-scaled version of the .le lighting effect if needed."""
        if brightness >= 100:
            return preset_name

        orig_path = os.path.join(LIGHTING_DIR, f"{preset_name}.le")
        if not os.path.exists(orig_path):
            return preset_name

        try:
            with open(orig_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            factor = max(0.0, min(1.0, brightness / 100.0))

            def scale_val(val_str: str) -> str:
                if not isinstance(val_str, str):
                    return val_str
                clean = val_str.replace("0x", "").replace("#", "")
                if len(clean) == 6:
                    try:
                        r = int(int(clean[0:2], 16) * factor)
                        g = int(int(clean[2:4], 16) * factor)
                        b = int(int(clean[4:6], 16) * factor)
                        return f"0x{r:02x}{g:02x}{b:02x}"
                    except ValueError:
                        return val_str
                return val_str

            if "Frames" in data and isinstance(data["Frames"], list):
                for frame in data["Frames"]:
                    if "Data" in frame and isinstance(frame["Data"], dict):
                        for k, v in frame["Data"].items():
                            frame["Data"][k] = scale_val(v)
            elif "Data" in data and isinstance(data["Data"], dict):
                for k, v in data["Data"].items():
                    data["Data"][k] = scale_val(v)

            scaled_name = f"{preset_name}_scaled_{brightness}"
            scaled_path = os.path.join(LIGHTING_DIR, f"{scaled_name}.le")
            with open(scaled_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return scaled_name
        except Exception as e:
            print(f"Error scaling preset lighting: {e}")
            return preset_name

    def _save_static_le_file(self, preset_name: str, key_colors: Dict[str, str], brightness: int = 100):
        factor = max(0.0, min(1.0, brightness / 100.0))
        data = {}
        for k, hex_col in key_colors.items():
            clean_hex = hex_col.replace("#", "").replace("0x", "")
            if len(clean_hex) == 6:
                try:
                    r = int(int(clean_hex[0:2], 16) * factor)
                    g = int(int(clean_hex[2:4], 16) * factor)
                    b = int(int(clean_hex[4:6], 16) * factor)
                    data[k] = f"0x{r:02x}{g:02x}{b:02x}"
                except ValueError:
                    data[k] = f"0x{clean_hex.lower()}"
            else:
                data[k] = f"0x{clean_hex.lower()}"

        static_json = {
            "Type": "Static",
            "Data": data
        }
        os.makedirs(LIGHTING_DIR, exist_ok=True)
        le_path = os.path.join(LIGHTING_DIR, f"{preset_name}.le")
        with open(le_path, "w", encoding="utf-8") as f:
            json.dump(static_json, f, indent=2)

    def set_brightness(self, brightness: int, auto_apply: bool = False):
        """Set brightness (0-100) and optionally apply immediately to hardware."""
        brightness = max(0, min(100, int(brightness)))
        self.lighting_config["brightness"] = brightness
        self.save_profile()
        if auto_apply:
            self.apply_current_configuration()

    def set_lighting_preset(self, preset_name: str, layer: str = "Base", auto_apply: bool = False):
        """Set active lighting preset and optionally apply immediately."""
        self.lighting_config["mode"] = "preset"
        self.lighting_config["preset_name"] = preset_name
        self.lighting_config["layer"] = layer
        self.save_profile()
        if auto_apply:
            self.apply_current_configuration()

    def set_lighting_off(self, auto_apply: bool = False):
        """Turn off RGB lighting."""
        self.lighting_config["mode"] = "off"
        self.save_profile()
        if auto_apply:
            self.apply_current_configuration()

    # ==========================
    # APPLY / UNMAP OPERATIONS
    # ==========================
    def apply_current_configuration(self):
        """Apply all macros, remaps, and lighting to the keyboard hardware."""
        config_text = self.generate_full_config()
        if self.worker is not None and self.worker.isRunning():
            self.worker.wait()

        self.worker = ApplyWorker(config_text, self.current_model_id)
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.worker.start()

    def reset_keyboard_mapping(self):
        """Factory reset keyboard mappings."""
        if self.unmap_worker is not None and self.unmap_worker.isRunning():
            self.unmap_worker.wait()

        self.unmap_worker = UnmapWorker()
        self.unmap_worker.finished_signal.connect(self._on_unmap_finished)
        self.unmap_worker.start()

    def _on_worker_finished(self, success: bool, msg: str):
        self.apply_finished.emit(success, msg)

    def _on_unmap_finished(self, success: bool, msg: str):
        if success:
            self.remaps = {layer_id: {} for layer_id, _ in AVAILABLE_LAYERS}
            self.save_profile()
        self.unmap_finished.emit(success, msg)

    # ==========================
    # PROFILE PERSISTENCE
    # ==========================
    def save_profile(self, path: Optional[str] = None):
        target_path = path or CONFIG_SAVE_PATH
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            data = {
                "model_id": self.current_model_id,
                "space_mode": getattr(self, "space_mode", "split"),
                "remaps": self.remaps,
                "macros": {name: m.to_dict() for name, m in self.macros.items()},
                "lighting": self.lighting_config
            }
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving profile: {e}")

    def load_profile(self, path: Optional[str] = None):
        target_path = path or CONFIG_SAVE_PATH
        if not os.path.exists(target_path):
            self.space_mode = "split"
            self._init_default_macros()
            return

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.space_mode = data.get("space_mode", "split")
            self.remaps = data.get("remaps", {layer_id: {} for layer_id, _ in AVAILABLE_LAYERS})
            macros_data = data.get("macros", {})
            self.macros = {name: MacroItem.from_dict(m) for name, m in macros_data.items()}
            self.lighting_config = data.get("lighting", self.lighting_config)
            if "brightness" not in self.lighting_config:
                self.lighting_config["brightness"] = 100
        except Exception as e:
            print(f"Error loading profile: {e}")
            self.space_mode = "split"
            self._init_default_macros()

    def _init_default_macros(self):
        """Create some handy initial macro samples."""
        self.macros = {
            "QuickCopyPaste": MacroItem(
                name="QuickCopyPaste",
                default_delay=20,
                repeat_type="RepeatXTimes",
                repeat_count=1,
                actions=[
                    MacroAction("Press", "LCtrl+C", delay=50),
                    MacroAction("Press", "Right", delay=20),
                    MacroAction("Press", "Enter", delay=20),
                    MacroAction("Press", "LCtrl+V", delay=20)
                ]
            ),
            "TaskManager": MacroItem(
                name="TaskManager",
                default_delay=0,
                repeat_type="RepeatXTimes",
                repeat_count=1,
                actions=[
                    MacroAction("Press", "LCtrl+LShift+Escape", delay=0)
                ]
            )
        }
