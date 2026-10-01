"""Internationalization (i18n) module for Skyloong GK104 Pro Studio Linux Software.
Supports dynamic switching between English (default) and Polish language packs.
"""

import os
import json
from typing import Dict, List, Tuple, Any, Optional

CONFIG_DIR = os.path.expanduser("~/.config/skyloong_studio")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

# Current language state ("en" by default)
_CURRENT_LANGUAGE = "en"


def get_available_languages() -> List[Tuple[str, str]]:
    """Return available language codes and their display names."""
    return [
        ("en", "🇬🇧 English"),
        ("pl", "🇵🇱 Polski")
    ]


def load_configured_language() -> str:
    """Load user selected language from configuration file, default to 'en'."""
    global _CURRENT_LANGUAGE
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                lang = data.get("language", "en")
                if lang in ["en", "pl"]:
                    _CURRENT_LANGUAGE = lang
                    return _CURRENT_LANGUAGE
    except Exception:
        pass
    _CURRENT_LANGUAGE = "en"
    return _CURRENT_LANGUAGE


def save_configured_language(lang_code: str):
    """Save selected language to persistent configuration."""
    global _CURRENT_LANGUAGE
    if lang_code in ["en", "pl"]:
        _CURRENT_LANGUAGE = lang_code
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        config_data = {}
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                config_data = {}
        config_data["language"] = _CURRENT_LANGUAGE
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[i18n] Error saving language config: {e}")


def get_current_language() -> str:
    return _CURRENT_LANGUAGE


def set_current_language(lang_code: str):
    global _CURRENT_LANGUAGE
    if lang_code in ["en", "pl"]:
        _CURRENT_LANGUAGE = lang_code
        save_configured_language(lang_code)


# Initialize language from stored config
load_configured_language()


# =========================================================================
# TRANSLATIONS DICTIONARY
# =========================================================================

STRINGS = {
    "en": {
        # App Title & Header
        "app_title": "Skyloong GK104 Pro Studio",
        "app_window_title": "Skyloong GK104 Pro Studio — RGB • Remap • Macros • Knobs",
        "device_detecting": "Detecting GK104 Pro device...",
        "device_connected": "Connected: {name} (USB {vid}:{pid})",
        "device_virtual": "Virtual Mode / No hardware detected",
        "battery_checking": "🔋 Battery: Checking...",
        "battery_ac": "🔋 Power: AC Connected (100%)",
        "battery_val": "🔋 Battery: {val}% ({status})",
        "btn_system_req": "⚙️ System",
        "btn_system_req_tip": "Check and configure system dependencies, Mono runtime and Udev rules",
        "btn_profiles_menu": "📁 Profiles & Files ▾",
        "btn_profiles_menu_tip": "Manage saved profiles, UserData files and backups",
        "menu_profile_manager": "📋 Saved Profiles Manager...",
        "menu_save_json": "💾 Save Profile as JSON...",
        "menu_save_txt": "📄 Save Hardware Code (.txt UserData)...",
        "menu_load_file": "📂 Load Profile / Config file (.json / .txt)...",
        "menu_flash_file": "⚡ Load File & Flash directly to Keyboard...",
        "btn_refresh": "🔄 Refresh",
        "btn_refresh_tip": "Refresh device connection and scan hardware",
        "btn_reset": "⚠️ Reset (Unmap)",
        "btn_reset_tip": "Restore factory key mappings",
        "btn_flash": "💾 FLASH TO KEYBOARD",
        "lbl_status_ready": "Ready.",
        "lbl_status_flashing": "Flashing keyboard memory (Flash)...",
        "lbl_status_resetting": "Resetting keyboard mappings...",
        "lang_selector_label": "🌐 Language:",

        # Tabs
        "tab_lighting": "🌈 RGB Lighting",
        "tab_remap": "⌨️ Remap & Knobs",
        "tab_macro": "⚡ Macro Studio",
        "tab_debug": "📝 Code & Diagnostics",

        # RGB Tab
        "rgb_header_title": "104 Visual Keyboard • Live Animation Preview & Color Painter",
        "rgb_pause_anim": "⏸ Pause Preview",
        "rgb_start_anim": "▶ Start Preview",
        "rgb_speed_label": "Speed:",
        "rgb_space_layout_label": "Spacebar Layout:",
        "rgb_space_split": "Split (2.25+2.75+1.25)",
        "rgb_space_standard": "Standard (6.25u)",
        "rgb_target_layer": "Target LED Layer:",
        "rgb_effects_library": "🌈 Built-In Animation Effects Library",
        "rgb_search_placeholder": "Search effect (e.g. Rainbow, Wave, Breath, Matrix)...",
        "rgb_all_categories": "All Categories",
        "rgb_apply_effect_btn": "⚡ Apply Effect to Keyboard",
        "rgb_tools_title": "🎨 Colors & Painting Tools",
        "rgb_current_brush": "Current brush:",
        "rgb_pick_color_btn": "Pick custom color...",
        "rgb_color_dialog_title": "Choose Brush Color",
        "rgb_zone_painting": "Zone Painting",
        "rgb_zone_wasd": "WASD",
        "rgb_zone_arrows": "Arrows",
        "rgb_zone_numpad": "NumPad",
        "rgb_zone_func": "F1-F12",
        "rgb_zone_alpha": "Letters",
        "rgb_zone_all": "Whole Board",
        "rgb_zone_btn_prefix": "Paint: ",
        "rgb_color_themes": "Preset Color Schemes",
        "rgb_brightness_title": "Keyboard Backlight Brightness",
        "rgb_brightness_label": "Brightness: {val}%",
        "rgb_btn_apply_bright": "⚡ Apply",
        "rgb_btn_led_off": "🌙 Turn off LED",
        "rgb_btn_apply_static": "✅ Apply Static Colors",
        "smart_screen_title": "1.04″ SMART SCREEN",
        "smart_screen_effect": "EFFECT: {name}",

        # Remap Tab
        "remap_active_layer": "Active Layer:",
        "remap_layer_base": "Base Layer (Default)",
        "remap_layer_1": "Layer 1 (Standard)",
        "remap_layer_2": "Layer 2",
        "remap_layer_3": "Layer 3",
        "remap_layer_fn1": "Fn + Layer 1",
        "remap_layer_fn2": "Fn + Layer 2",
        "remap_layer_fn3": "Fn + Layer 3",
        "remap_space_mode": "Spacebar Module:",
        "remap_knobs_title": "🎛️ Modular Rotary Knobs (GK104 Pro Multi-Knob Control)",
        "remap_knob_presets_label": "Knob Presets:",
        "remap_knob_presets_placeholder": "Choose preset configuration...",
        "remap_btn_copy_knobs": "📋 Copy Knobs to All Layers",
        "remap_btn_copy_knobs_tip": "Synchronize knob mappings across Base and Layers 1-3",
        "remap_inspector_title": "🎯 Function & Action Inspector",
        "remap_selected_item": "Selected: {name}",
        "remap_picked_action": "Selected Action: {action}",
        "remap_cat_primary": "⌨️ Primary",
        "remap_cat_numpad": "🔢 Numpad",
        "remap_cat_media": "🎵 Media",
        "remap_cat_backlight": "💡 Backlight",
        "remap_cat_system": "🌐 System/Web",
        "remap_cat_mouse": "🖱️ Mouse",
        "remap_cat_combos": "⚡ Combinations",
        "remap_cat_macros": "📜 Macros",
        "remap_cat_disabled": "🚫 Disable Key",
        "remap_search_placeholder": "Search key or function...",
        "remap_combos_modifiers": "Modifiers:",
        "remap_combos_base_key": "Base Key:",
        "remap_combos_popular": "Popular System Shortcuts:",
        "remap_macro_choose": "Choose Recorded Macro:",
        "remap_btn_assign": "⚡ Assign Function to Key / Knob",
        "remap_btn_reset_key": "↩️ Reset Key to Default",
        "remap_table_title": "📋 Active Layer Remaps Overview ({layer})",
        "remap_col_key": "Key / Knob",
        "remap_col_action": "Assigned Function",
        "remap_col_code": "Hardware Code",
        "remap_col_delete": "Action",
        "remap_btn_clear_layer": "🗑️ Clear All Layer Remaps",

        # Macro Tab
        "macro_library_title": "📜 Macro Library",
        "macro_btn_new": "➕ New Macro",
        "macro_btn_delete": "🗑️ Delete",
        "macro_btn_dup": "📋 Duplicate",
        "macro_btn_rename": "✏️ Rename",
        "macro_editor_title": "⚡ Macro Sequence Editor",
        "macro_name_label": "Macro Name:",
        "macro_repeat_label": "Repeat Mode:",
        "macro_repeat_count": "Repeats:",
        "macro_mode_times": "Repeat X Times",
        "macro_mode_hold": "Hold Key to Repeat",
        "macro_mode_toggle": "Toggle On/Off on Press",
        "macro_table_col_event": "Event",
        "macro_table_col_key": "Target Key",
        "macro_table_col_delay": "Delay (ms)",
        "macro_btn_add_step": "➕ Add Step",
        "macro_btn_move_up": "⬆️ Move Up",
        "macro_btn_move_down": "⬇️ Move Down",
        "macro_btn_del_step": "🗑️ Delete Step",
        "macro_btn_clear_steps": "🧹 Clear All Steps",
        "macro_quick_text_title": "⚡ Quick Text / Command to Macro Generator",
        "macro_quick_text_label": "Enter text or shell command to convert (e.g. sudo pacman -Syu):",
        "macro_quick_text_speed": "Speed (ms/key):",
        "macro_quick_text_btn": "🚀 Generate Key Sequence",
        "macro_status_info": "Sequence: {steps} steps • Buffer safe",

        # Code & Diagnostics Tab
        "debug_code_title": "Generated GK6X UserData Configuration Code",
        "debug_btn_refresh": "🔄 Refresh Code",
        "debug_btn_copy": "📋 Copy to Clipboard",
        "debug_btn_export": "💾 Export to .txt",
        "debug_log_title": "Backend Execution & Communication Log",
        "debug_btn_clear_log": "🧹 Clear Log",
        "debug_bridge_status": "⚙️ Hardware Bridge Status",

        # Profile Manager Dialog
        "pm_title": "📁 Profile & Backup Manager",
        "pm_col_name": "Profile Name",
        "pm_col_type": "Format",
        "pm_col_date": "Last Modified",
        "pm_col_size": "Size",
        "pm_btn_save_current": "💾 Save Current Settings...",
        "pm_btn_import": "📂 Import File...",
        "pm_btn_export": "📤 Export File...",
        "pm_btn_load": "📥 Load to Editor",
        "pm_btn_flash": "⚡ Flash to Keyboard",
        "pm_btn_delete": "🗑️ Delete",
        "pm_btn_close": "Close",
        "pm_no_profiles": "No saved profiles found in ~/.config/skyloong_studio/profiles/. Click 'Save Current Settings...' to create one!",
        "pm_available_count": "Available profiles: {count}. Select a profile to manage.",
        "pm_selected_info": "Selected: {name} ({type}, {size}, modified: {date})",

        # System Diagnostics Dialog
        "diag_title": "⚙️ System Diagnostics & Requirements Wizard",
        "diag_header": "Linux Environment & Hardware Access Verification",
        "diag_mono_title": "Mono Runtime (.NET Execution)",
        "diag_mono_desc": "Required by GK6X low-level communication driver",
        "diag_udev_title": "Udev Rules Configuration",
        "diag_udev_desc": "Grants non-root USB/hidraw read-write access to vendor IDs 1ea7, 32e3, 04d9, 0c45",
        "diag_usb_title": "USB / HIDRAW Nodes Access",
        "diag_usb_desc": "Validates read/write permissions on keyboard communication endpoints",
        "diag_status_ok": "✅ Installed & Verified",
        "diag_status_fail": "❌ Missing / Not Configured",
        "diag_btn_autofix": "⚡ Run Automatic Setup (sudo ./install_rules.sh)",
        "diag_btn_recheck": "🔄 Re-check",
        "diag_btn_close": "Close",

        # Tray Menu
        "tray_title": "Skyloong GK104 Pro Studio",
        "tray_show": "🖥️ Show Window",
        "tray_hide": "⬇️ Minimize to Tray",
        "tray_brightness": "💡 Backlight Brightness",
        "tray_effects": "🌈 Lighting Presets",
        "tray_layers": "🔀 Active Layer",
        "tray_lang": "🌐 Language",
        "tray_apply": "⚡ Flash to Keyboard",
        "tray_quit": "❌ Quit",

        # Messages & Dialogs
        "msg_success": "Success",
        "msg_error": "Error",
        "msg_warning": "Warning",
        "msg_info": "Information",
        "msg_confirm": "Confirm",
        "msg_flashed_success": "Configuration successfully flashed to keyboard hardware memory!",
        "msg_flashed_error": "Failed to flash configuration: {err}",
        "msg_reset_confirm": "Are you sure you want to restore default factory mappings? This will reset all customized keys.",
        "msg_copied_clipboard": "Hardware UserData code copied to clipboard!",
        "msg_copy_knobs_success": "Knob configurations successfully copied to Base, Layer 1, Layer 2, and Layer 3!",
        "msg_profile_saved": "Profile '{name}' successfully saved!",
        "msg_profile_loaded": "Profile '{name}' successfully loaded into editor!",
        "msg_profile_deleted": "Profile '{name}' has been deleted.",
        "msg_delete_confirm": "Are you sure you want to delete profile '{name}'?",
        "msg_assigned_info": "Assigned '{dst}' to '{src}' on {layer}."
    },

    "pl": {
        # App Title & Header
        "app_title": "Skyloong GK104 Pro Studio",
        "app_window_title": "Skyloong GK104 Pro Studio — RGB • Remap • Makra • Knoby",
        "device_detecting": "Wykrywanie urządzenia GK104 Pro...",
        "device_connected": "Połączono: {name} (USB {vid}:{pid})",
        "device_virtual": "Tryb wirtualny / Brak podłączonego sprzętu",
        "battery_checking": "🔋 Bateria: Sprawdzanie...",
        "battery_ac": "🔋 Zasilanie: Sieciowe (100%)",
        "battery_val": "🔋 Bateria: {val}% ({status})",
        "btn_system_req": "⚙️ Wymagania",
        "btn_system_req_tip": "Sprawdź i skonfiguruj wymagania systemowe, Mono oraz reguły Udev",
        "btn_profiles_menu": "📁 Profile & Pliki ▾",
        "btn_profiles_menu_tip": "Zarządzaj zapisami konfiguracji, plikami UserData i profilami",
        "menu_profile_manager": "📋 Menedżer Zapisanych Profili...",
        "menu_save_json": "💾 Zapisz profil jako JSON...",
        "menu_save_txt": "📄 Zapisz kod sprzętowy (.txt UserData)...",
        "menu_load_file": "📂 Wczytaj profil / plik konfiguracji (.json / .txt)...",
        "menu_flash_file": "⚡ Wczytaj plik i wgraj od razu do klawiatury...",
        "btn_refresh": "🔄 Odśwież",
        "btn_refresh_tip": "Odśwież połączenie z klawiaturą",
        "btn_reset": "⚠️ Reset (Unmap)",
        "btn_reset_tip": "Przywróć domyślny układ fabryczny",
        "btn_flash": "💾 WGRAJ DO KLAWIATURY",
        "lbl_status_ready": "Gotowy do pracy.",
        "lbl_status_flashing": "Programowanie pamięci klawiatury (Flash)...",
        "lbl_status_resetting": "Resetowanie mapowań w klawiaturze...",
        "lang_selector_label": "🌐 Język:",

        # Tabs
        "tab_lighting": "🌈 Oświetlenie LED",
        "tab_remap": "⌨️ Remapowanie & Pokrętła (Knobs)",
        "tab_macro": "⚡ Menedżer Makr (Macro Studio)",
        "tab_debug": "📝 Podgląd Kodu & Diagnostyka",

        # RGB Tab
        "rgb_header_title": "Wizualna Klawiatura 104 • Podgląd Animacji na Żywo & Malowanie",
        "rgb_pause_anim": "⏸ Wstrzymaj podgląd",
        "rgb_start_anim": "▶ Uruchom podgląd",
        "rgb_speed_label": "Prędkość:",
        "rgb_space_layout_label": "Układ Spacji:",
        "rgb_space_split": "Podwójna (Split)",
        "rgb_space_standard": "Standard (6.25u)",
        "rgb_target_layer": "Docelowa warstwa LED:",
        "rgb_effects_library": "🌈 Biblioteka Wbudowanych Animacji",
        "rgb_search_placeholder": "Szukaj animacji (np. Rainbow, Wave, Fala, Matrix)...",
        "rgb_all_categories": "Wszystkie kategorie",
        "rgb_apply_effect_btn": "⚡ Zastosuj Animację do Klawiatury",
        "rgb_tools_title": "🎨 Kolory & Narzędzia Malowania",
        "rgb_current_brush": "Aktualny pędzel:",
        "rgb_pick_color_btn": "Wybierz własny kolor...",
        "rgb_color_dialog_title": "Wybierz Kolor Pędzla",
        "rgb_zone_painting": "Malowanie Strefowe",
        "rgb_zone_wasd": "WASD",
        "rgb_zone_arrows": "Strzałki",
        "rgb_zone_numpad": "NumPad",
        "rgb_zone_func": "F1-F12",
        "rgb_zone_alpha": "Litery",
        "rgb_zone_all": "Cała klawiatura",
        "rgb_zone_btn_prefix": "Pomaluj: ",
        "rgb_color_themes": "Gotowe Motywy Kolorystyczne",
        "rgb_brightness_title": "Jasność Podświetlenia Klawiatury",
        "rgb_brightness_label": "Jasność: {val}%",
        "rgb_btn_apply_bright": "⚡ Zastosuj",
        "rgb_btn_led_off": "🌙 Wyłącz LED",
        "rgb_btn_apply_static": "✅ Zastosuj Kolory z Klawiatury",
        "smart_screen_title": "1.04″ SMART SCREEN",
        "smart_screen_effect": "EFFECT: {name}",

        # Remap Tab
        "remap_active_layer": "Aktywna warstwa:",
        "remap_layer_base": "Warstwa Podstawowa (Base)",
        "remap_layer_1": "Warstwa 1 (Layer 1)",
        "remap_layer_2": "Warstwa 2 (Layer 2)",
        "remap_layer_3": "Warstwa 3 (Layer 3)",
        "remap_layer_fn1": "Warstwa Fn + 1 (FnLayer1)",
        "remap_layer_fn2": "Warstwa Fn + 2 (FnLayer2)",
        "remap_layer_fn3": "Warstwa Fn + 3 (FnLayer3)",
        "remap_space_mode": "Układ Spacji:",
        "remap_knobs_title": "🎛️ Modularne Pokrętła (GK104 Pro Multi-Knob Control)",
        "remap_knob_presets_label": "Gotowe profile pokręteł:",
        "remap_knob_presets_placeholder": "Wybierz gotowy profil pokręteł...",
        "remap_btn_copy_knobs": "📋 Kopiuj pokrętła na wszystkie warstwy",
        "remap_btn_copy_knobs_tip": "Synchronizuj mapowania pokręteł pomiędzy warstwą bazową a warstwami 1-3",
        "remap_inspector_title": "🎯 Inspektor Funkcji & Akcji",
        "remap_selected_item": "Wybrano: {name}",
        "remap_picked_action": "Wybrana funkcja: {action}",
        "remap_cat_primary": "⌨️ Główne",
        "remap_cat_numpad": "🔢 Numeryczna",
        "remap_cat_media": "🎵 Media",
        "remap_cat_backlight": "💡 Podświetlenie",
        "remap_cat_system": "🌐 System/WWW",
        "remap_cat_mouse": "🖱️ Mysz",
        "remap_cat_combos": "⚡ Skróty",
        "remap_cat_macros": "📜 Makra",
        "remap_cat_disabled": "🚫 Wyłącz Klawisz",
        "remap_search_placeholder": "Szukaj klawisza lub funkcji...",
        "remap_combos_modifiers": "Modyfikatory:",
        "remap_combos_base_key": "Klawisz bazowy:",
        "remap_combos_popular": "Popularne skróty systemowe:",
        "remap_macro_choose": "Wybierz nagrane makro:",
        "remap_btn_assign": "⚡ Przypisz Funkcję do Klawisza / Pokrętła",
        "remap_btn_reset_key": "↩️ Przywróć Domyślny Klawisz",
        "remap_table_title": "📋 Podsumowanie Mapowań Warstwy ({layer})",
        "remap_col_key": "Klawisz / Pokrętło",
        "remap_col_action": "Przypisana Funkcja",
        "remap_col_code": "Kod Sprzętowy",
        "remap_col_delete": "Akcja",
        "remap_btn_clear_layer": "🗑️ Wyczyść Wszystkie Mapowania Warstwy",

        # Macro Tab
        "macro_library_title": "📜 Biblioteka Makr",
        "macro_btn_new": "➕ Nowe Makro",
        "macro_btn_delete": "🗑️ Usuń",
        "macro_btn_dup": "📋 Duplikuj",
        "macro_btn_rename": "✏️ Zmień nazwę",
        "macro_editor_title": "⚡ Edytor Sekwencji Makra",
        "macro_name_label": "Nazwa Makra:",
        "macro_repeat_label": "Tryb powtarzania:",
        "macro_repeat_count": "Liczba powtórzeń:",
        "macro_mode_times": "Powtórz X razy",
        "macro_mode_hold": "Trzymaj klawisz by powtarzać",
        "macro_mode_toggle": "Włącz/Wyłącz ponownym kliknięciem",
        "macro_table_col_event": "Zdarzenie",
        "macro_table_col_key": "Klawisz docelowy",
        "macro_table_col_delay": "Opóźnienie (ms)",
        "macro_btn_add_step": "➕ Dodaj Krok",
        "macro_btn_move_up": "⬆️ W górę",
        "macro_btn_move_down": "⬇️ W dół",
        "macro_btn_del_step": "🗑️ Usuń Krok",
        "macro_btn_clear_steps": "🧹 Wyczyść Wszystko",
        "macro_quick_text_title": "⚡ Generator Makra z Dowolnego Tekstu / Komendy",
        "macro_quick_text_label": "Wpisz tekst lub komendę do konwersji (np. sudo pacman -Syu):",
        "macro_quick_text_speed": "Opóźnienie (ms/klawisz):",
        "macro_quick_text_btn": "🚀 Generuj Sekwencję Klawiszy",
        "macro_status_info": "Długość: {steps} kroków • Bufor bezpieczny",

        # Code & Diagnostics Tab
        "debug_code_title": "Wygenerowany Kod Sprzętowy GK6X UserData",
        "debug_btn_refresh": "🔄 Odśwież Kod",
        "debug_btn_copy": "📋 Kopiuj do Schowka",
        "debug_btn_export": "💾 Zapisz do pliku .txt",
        "debug_log_title": "Dziennik Wykonania i Komunikacji z Backendem",
        "debug_btn_clear_log": "🧹 Wyczyść Log",
        "debug_bridge_status": "⚙️ Status Mostka Sprzętowego",

        # Profile Manager Dialog
        "pm_title": "📁 Menedżer Profili i Kopii Zapasowych",
        "pm_col_name": "Nazwa Profilu",
        "pm_col_type": "Format",
        "pm_col_date": "Data Modyfikacji",
        "pm_col_size": "Rozmiar",
        "pm_btn_save_current": "💾 Zapisz bieżące ustawienia...",
        "pm_btn_import": "📂 Importuj plik...",
        "pm_btn_export": "📤 Eksportuj plik...",
        "pm_btn_load": "📥 Wczytaj do edytora",
        "pm_btn_flash": "⚡ Wgraj do klawiatury",
        "pm_btn_delete": "🗑️ Usuń",
        "pm_btn_close": "Zamknij",
        "pm_no_profiles": "Brak zapisanych profili w ~/.config/skyloong_studio/profiles/. Kliknij 'Zapisz bieżące ustawienia...' aby utworzyć profil!",
        "pm_available_count": "Dostępnych profili: {count}. Wybierz profil, aby nim zarządzać.",
        "pm_selected_info": "Wybrano: {name} ({type}, {size}, zmodyfikowano: {date})",

        # System Diagnostics Dialog
        "diag_title": "⚙️ Asystent Diagnostyki i Wymagań Systemowych",
        "diag_header": "Weryfikacja Środowiska Linux i Uprawnień Sprzętowych",
        "diag_mono_title": "Środowisko Mono (.NET Runtime)",
        "diag_mono_desc": "Wymagane do uruchomienia mostka komunikacji niskopoziomowej GK6X",
        "diag_udev_title": "Konfiguracja Reguł Udev",
        "diag_udev_desc": "Nadaje uprawnienia zapisu/odczytu USB/hidraw bez roota dla vendor ID 1ea7, 32e3, 04d9, 0c45",
        "diag_usb_title": "Dostęp do Węzłów USB / HIDRAW",
        "diag_usb_desc": "Weryfikuje uprawnienia odczytu i zapisu do kontrolerów klawiatury",
        "diag_status_ok": "✅ Zainstalowano i zweryfikowano",
        "diag_status_fail": "❌ Brak / Wymaga konfiguracji",
        "diag_btn_autofix": "⚡ Uruchom Automatyczną Instalację (sudo ./install_rules.sh)",
        "diag_btn_recheck": "🔄 Sprawdź ponownie",
        "diag_btn_close": "Zamknij",

        # Tray Menu
        "tray_title": "Skyloong GK104 Pro Studio",
        "tray_show": "🖥️ Pokaż Okno Programu",
        "tray_hide": "⬇️ Minimalizuj do Zasobnika",
        "tray_brightness": "💡 Jasność Podświetlenia",
        "tray_effects": "🌈 Motywy Oświetlenia LED",
        "tray_layers": "🔀 Aktywna Warstwa",
        "tray_lang": "🌐 Język",
        "tray_apply": "⚡ Wgraj do Klawiatury",
        "tray_quit": "❌ Wyjście",

        # Messages & Dialogs
        "msg_success": "Sukces",
        "msg_error": "Błąd",
        "msg_warning": "Ostrzeżenie",
        "msg_info": "Informacja",
        "msg_confirm": "Potwierdzenie",
        "msg_flashed_success": "Konfiguracja została pomyślnie wgrana do pamięci klawiatury!",
        "msg_flashed_error": "Nie udało się wgrać konfiguracji: {err}",
        "msg_reset_confirm": "Czy na pewno chcesz przywrócić fabryczny układ klawiszy? Spowoduje to usunięcie wprowadzonych mapowań.",
        "msg_copied_clipboard": "Kod sprzętowy UserData został skopiowany do schowka!",
        "msg_copy_knobs_success": "Konfiguracja pokręteł została pomyślnie skopiowana na warstwy Base, Layer 1, Layer 2 i Layer 3!",
        "msg_profile_saved": "Pomyślnie zapisano profil '{name}'!",
        "msg_profile_loaded": "Profil '{name}' został pomyślnie wczytany do edytora!",
        "msg_profile_deleted": "Profil '{name}' został usunięty.",
        "msg_delete_confirm": "Czy na pewno chcesz usunąć profil '{name}'?",
        "msg_assigned_info": "Przypisano '{dst}' do '{src}' na warstwie {layer}."
    }
}


def tr(key: str, default: Optional[str] = None, **kwargs) -> str:
    """Translate a key into current language."""
    lang = _CURRENT_LANGUAGE
    val = STRINGS.get(lang, {}).get(key)
    if val is None:
        val = STRINGS.get("en", {}).get(key, default if default is not None else key)
    if kwargs and isinstance(val, str):
        try:
            return val.format(**kwargs)
        except Exception:
            return val
    return val


# =========================================================================
# LOCALIZED DICTIONARIES & HELPERS
# =========================================================================

def get_action_short_labels(lang: Optional[str] = None) -> Dict[str, str]:
    l = lang or _CURRENT_LANGUAGE
    if l == "pl":
        return {
            "ToggleLighting": "💡LED OnOff",
            "BrightnessUp": "☀️Jas+",
            "BrightnessDown": "🌙Jas-",
            "LightingSpeedIncrease": "⏩Szyb+",
            "LightingSpeedDecrease": "⏪Szyb-",
            "LightingPauseResume": "⏸️Pauza",
            "NextLightingEffect": "🌈LED Efekt",
            "NextReactiveLightingEffect": "✨LED Reakcja",
            "Disabled": "🚫Wyłączony",
            "0x09060002": "💡LED OnOff",
            "0x09020001": "☀️Jas+",
            "0x09020002": "🌙Jas-",
            "0x09030001": "⏩Szyb+",
            "0x09030002": "⏪Szyb-",
            "0x09060001": "⏸️Pauza",
            "0x09010010": "🌈LED Efekt",
            "0x09010011": "✨LED Reakcja",
            "0x02000000": "🚫Wyłączony",
            "VolumeUp": "🔊Vol+",
            "VolumeDown": "🔉Vol-",
            "VolumeMute": "🔇Mute",
            "MediaPlayPause": "⏯️Play/Pause",
            "MediaNext": "⏭️Next",
            "MediaPrevious": "⏮️Prev",
            "MediaStop": "⏹️Stop",
            "OpenMediaPlayer": "🎵Player",
            "Eject": "⏏️Eject",
            "OpenCalculator": "🧮Kalk",
            "OpenMyComputer": "💻Mój PC",
            "OpenEmail": "✉️Email",
            "BrowserHome": "🏠Home",
            "BrowserBack": "⬅️Wstecz",
            "BrowserForward": "➡️Dalej",
            "BrowserRefresh": "🔄Odśw",
            "BrowserFavorites": "⭐Ulub",
            "BrowserSearch": "🔍Szukaj",
            "Screenshot": "📸PrtSc",
            "MouseLClick": "🖱️L-Klik",
            "MouseRClick": "🖱️P-Klik",
            "MouseMClick": "🖱️Ś-Klik",
            "MouseBack": "◀️M-Wstecz",
            "MouseAdvance": "▶️M-Dalej",
            "LeftClick": "🖱️L-Klik",
            "RightClick": "🖱️P-Klik",
            "MiddleClick": "🖱️Ś-Klik",
            "MouseForward": "▶️M-Dalej"
        }
    else:
        return {
            "ToggleLighting": "💡LED OnOff",
            "BrightnessUp": "☀️Bri+",
            "BrightnessDown": "🌙Bri-",
            "LightingSpeedIncrease": "⏩Spd+",
            "LightingSpeedDecrease": "⏪Spd-",
            "LightingPauseResume": "⏸️Pause",
            "NextLightingEffect": "🌈LED Effect",
            "NextReactiveLightingEffect": "✨LED React",
            "Disabled": "🚫Disabled",
            "0x09060002": "💡LED OnOff",
            "0x09020001": "☀️Bri+",
            "0x09020002": "🌙Bri-",
            "0x09030001": "⏩Spd+",
            "0x09030002": "⏪Spd-",
            "0x09060001": "⏸️Pause",
            "0x09010010": "🌈LED Effect",
            "0x09010011": "✨LED React",
            "0x02000000": "🚫Disabled",
            "VolumeUp": "🔊Vol+",
            "VolumeDown": "🔉Vol-",
            "VolumeMute": "🔇Mute",
            "MediaPlayPause": "⏯️Play/Pause",
            "MediaNext": "⏭️Next",
            "MediaPrevious": "⏮️Prev",
            "MediaStop": "⏹️Stop",
            "OpenMediaPlayer": "🎵Player",
            "Eject": "⏏️Eject",
            "OpenCalculator": "🧮Calc",
            "OpenMyComputer": "💻My PC",
            "OpenEmail": "✉️Email",
            "BrowserHome": "🏠Home",
            "BrowserBack": "⬅️Back",
            "BrowserForward": "➡️Forward",
            "BrowserRefresh": "🔄Refresh",
            "BrowserFavorites": "⭐Fav",
            "BrowserSearch": "🔍Search",
            "Screenshot": "📸PrtSc",
            "MouseLClick": "🖱️L-Click",
            "MouseRClick": "🖱️R-Click",
            "MouseMClick": "🖱️M-Click",
            "MouseBack": "◀️M-Back",
            "MouseAdvance": "▶️M-Fwd",
            "LeftClick": "🖱️L-Click",
            "RightClick": "🖱️R-Click",
            "MiddleClick": "🖱️M-Click",
            "MouseForward": "▶️M-Fwd"
        }


def get_friendly_action_label(action: str, lang: Optional[str] = None) -> str:
    """Return a descriptive, readable label for any key or special action code."""
    l = lang or _CURRENT_LANGUAGE
    if not action:
        return "Default Function" if l == "en" else "Domyślna funkcja"
    if action.startswith("Macro(") and action.endswith(")"):
        return f"⚡ Macro: {action[6:-1]}" if l == "en" else f"⚡ Makro: {action[6:-1]}"

    cats = get_target_key_categories(l)
    for cat_name, keys in cats.items():
        for kid, klabel in keys:
            if kid == action:
                return f"{klabel} [{kid}]"

    shorts = get_action_short_labels(l)
    if action in shorts:
        return shorts[action]
    return action


def get_knobs_metadata(lang: Optional[str] = None) -> List[Dict[str, Any]]:
    l = lang or _CURRENT_LANGUAGE
    if l == "pl":
        return [
            {
                "id": "Knob1",
                "name": "Pokrętło 1 (Esc / Główne)",
                "icon": "🎛️",
                "actions": [
                    {"id": "Knob1_CW", "label": "↻ Prawo", "full_label": "Obrót w prawo (CW)", "default": "VolumeUp"},
                    {"id": "Knob1_CCW", "label": "↺ Lewo", "full_label": "Obrót w lewo (CCW)", "default": "VolumeDown"},
                    {"id": "Knob1_Click", "label": "⊙ Klik", "full_label": "Wciśnięcie (Click)", "default": "VolumeMute"}
                ]
            },
            {
                "id": "Knob2",
                "name": "Pokrętło 2 (Pozycja F11)",
                "icon": "🔊",
                "actions": [
                    {"id": "Knob2_CW", "label": "↻ Prawo", "full_label": "Obrót w prawo (CW)", "default": "MediaNext"},
                    {"id": "Knob2_CCW", "label": "↺ Lewo", "full_label": "Obrót w lewo (CCW)", "default": "MediaPrevious"},
                    {"id": "Knob2_Click", "label": "⊙ Klik", "full_label": "Wciśnięcie (Click)", "default": "MediaPlayPause"}
                ]
            },
            {
                "id": "Knob3",
                "name": "Pokrętło 3 (Pozycja F12)",
                "icon": "🎵",
                "actions": [
                    {"id": "Knob3_CW", "label": "↻ Prawo", "full_label": "Obrót w prawo (CW)", "default": "BrowserForward"},
                    {"id": "Knob3_CCW", "label": "↺ Lewo", "full_label": "Obrót w lewo (CCW)", "default": "BrowserBack"},
                    {"id": "Knob3_Click", "label": "⊙ Klik", "full_label": "Wciśnięcie (Click)", "default": "BrowserRefresh"}
                ]
            },
            {
                "id": "Knob4",
                "name": "Pokrętło 4 (Pozycja PrtSc)",
                "icon": "🌐",
                "actions": [
                    {"id": "Knob4_CW", "label": "↻ Prawo", "full_label": "Obrót w prawo (CW)", "default": "VolumeUp"},
                    {"id": "Knob4_CCW", "label": "↺ Lewo", "full_label": "Obrót w lewo (CCW)", "default": "VolumeDown"},
                    {"id": "Knob4_Click", "label": "⊙ Klik", "full_label": "Wciśnięcie (Click)", "default": "VolumeMute"}
                ]
            },
            {
                "id": "Knob5",
                "name": "Pokrętło 5 (Pozycja ScrLk)",
                "icon": "📜",
                "actions": [
                    {"id": "Knob5_CW", "label": "↻ Prawo", "full_label": "Obrót w prawo (CW)", "default": "VolumeUp"},
                    {"id": "Knob5_CCW", "label": "↺ Lewo", "full_label": "Obrót w lewo (CCW)", "default": "VolumeDown"},
                    {"id": "Knob5_Click", "label": "⊙ Klik", "full_label": "Wciśnięcie (Click)", "default": "VolumeMute"}
                ]
            },
            {
                "id": "Knob6",
                "name": "Pokrętło 6 (Pozycja Pause)",
                "icon": "⚙️",
                "actions": [
                    {"id": "Knob6_CW", "label": "↻ Prawo", "full_label": "Obrót w prawo (CW)", "default": "OpenMediaPlayer"},
                    {"id": "Knob6_CCW", "label": "↺ Lewo", "full_label": "Obrót w lewo (CCW)", "default": "VolumeDown"},
                    {"id": "Knob6_Click", "label": "⊙ Klik", "full_label": "Wciśnięcie (Click)", "default": "VolumeMute"}
                ]
            }
        ]
    else:
        return [
            {
                "id": "Knob1",
                "name": "Knob 1 (Esc / Main)",
                "icon": "🎛️",
                "actions": [
                    {"id": "Knob1_CW", "label": "↻ CW (Right)", "full_label": "Turn Clockwise (CW)", "default": "VolumeUp"},
                    {"id": "Knob1_CCW", "label": "↺ CCW (Left)", "full_label": "Turn Counter-Clockwise (CCW)", "default": "VolumeDown"},
                    {"id": "Knob1_Click", "label": "⊙ Click", "full_label": "Press / Click", "default": "VolumeMute"}
                ]
            },
            {
                "id": "Knob2",
                "name": "Knob 2 (F11 Position)",
                "icon": "🔊",
                "actions": [
                    {"id": "Knob2_CW", "label": "↻ CW (Right)", "full_label": "Turn Clockwise (CW)", "default": "MediaNext"},
                    {"id": "Knob2_CCW", "label": "↺ CCW (Left)", "full_label": "Turn Counter-Clockwise (CCW)", "default": "MediaPrevious"},
                    {"id": "Knob2_Click", "label": "⊙ Click", "full_label": "Press / Click", "default": "MediaPlayPause"}
                ]
            },
            {
                "id": "Knob3",
                "name": "Knob 3 (F12 Position)",
                "icon": "🎵",
                "actions": [
                    {"id": "Knob3_CW", "label": "↻ CW (Right)", "full_label": "Turn Clockwise (CW)", "default": "BrowserForward"},
                    {"id": "Knob3_CCW", "label": "↺ CCW (Left)", "full_label": "Turn Counter-Clockwise (CCW)", "default": "BrowserBack"},
                    {"id": "Knob3_Click", "label": "⊙ Click", "full_label": "Press / Click", "default": "BrowserRefresh"}
                ]
            },
            {
                "id": "Knob4",
                "name": "Knob 4 (PrtSc Position)",
                "icon": "🌐",
                "actions": [
                    {"id": "Knob4_CW", "label": "↻ CW (Right)", "full_label": "Turn Clockwise (CW)", "default": "VolumeUp"},
                    {"id": "Knob4_CCW", "label": "↺ CCW (Left)", "full_label": "Turn Counter-Clockwise (CCW)", "default": "VolumeDown"},
                    {"id": "Knob4_Click", "label": "⊙ Click", "full_label": "Press / Click", "default": "VolumeMute"}
                ]
            },
            {
                "id": "Knob5",
                "name": "Knob 5 (ScrLk Position)",
                "icon": "📜",
                "actions": [
                    {"id": "Knob5_CW", "label": "↻ CW (Right)", "full_label": "Turn Clockwise (CW)", "default": "VolumeUp"},
                    {"id": "Knob5_CCW", "label": "↺ CCW (Left)", "full_label": "Turn Counter-Clockwise (CCW)", "default": "VolumeDown"},
                    {"id": "Knob5_Click", "label": "⊙ Click", "full_label": "Press / Click", "default": "VolumeMute"}
                ]
            },
            {
                "id": "Knob6",
                "name": "Knob 6 (Pause Position)",
                "icon": "⚙️",
                "actions": [
                    {"id": "Knob6_CW", "label": "↻ CW (Right)", "full_label": "Turn Clockwise (CW)", "default": "OpenMediaPlayer"},
                    {"id": "Knob6_CCW", "label": "↺ CCW (Left)", "full_label": "Turn Counter-Clockwise (CCW)", "default": "VolumeDown"},
                    {"id": "Knob6_Click", "label": "⊙ Click", "full_label": "Press / Click", "default": "VolumeMute"}
                ]
            }
        ]


def get_knob_presets(lang: Optional[str] = None) -> Dict[str, Dict[str, str]]:
    l = lang or _CURRENT_LANGUAGE
    if l == "pl":
        return {
            "Głośność (Audio Volume)": {
                "CW": "VolumeUp", "CCW": "VolumeDown", "Click": "VolumeMute"
            },
            "Odtwarzacz Muzyki (Media Player)": {
                "CW": "MediaNext", "CCW": "MediaPrevious", "Click": "MediaPlayPause"
            },
            "💡 Jasność Podświetlenia (Backlight)": {
                "CW": "BrightnessUp", "CCW": "BrightnessDown", "Click": "ToggleLighting"
            },
            "✨ Szybkość Animacji LED (Speed)": {
                "CW": "LightingSpeedIncrease", "CCW": "LightingSpeedDecrease", "Click": "LightingPauseResume"
            },
            "🌈 Przełączanie Profili LED (Effects)": {
                "CW": "NextLightingEffect", "CCW": "NextReactiveLightingEffect", "Click": "ToggleLighting"
            },
            "Przeglądarka WWW (Browser Nav)": {
                "CW": "BrowserForward", "CCW": "BrowserBack", "Click": "BrowserRefresh"
            },
            "Przewijanie Strony (Page Scroll)": {
                "CW": "PageDown", "CCW": "PageUp", "Click": "Enter"
            },
            "Przełączanie Kart (Tab Switch)": {
                "CW": "LCtrl+Tab", "CCW": "LCtrl+LShift+Tab", "Click": "LCtrl+W"
            },
            "Zoom / Powiększenie": {
                "CW": "LCtrl+Add", "CCW": "LCtrl+Subtract", "Click": "LCtrl+D0"
            }
        }
    else:
        return {
            "Audio Volume Control": {
                "CW": "VolumeUp", "CCW": "VolumeDown", "Click": "VolumeMute"
            },
            "Media Player Control": {
                "CW": "MediaNext", "CCW": "MediaPrevious", "Click": "MediaPlayPause"
            },
            "💡 Backlight Brightness": {
                "CW": "BrightnessUp", "CCW": "BrightnessDown", "Click": "ToggleLighting"
            },
            "✨ LED Animation Speed": {
                "CW": "LightingSpeedIncrease", "CCW": "LightingSpeedDecrease", "Click": "LightingPauseResume"
            },
            "🌈 LED Effects Switcher": {
                "CW": "NextLightingEffect", "CCW": "NextReactiveLightingEffect", "Click": "ToggleLighting"
            },
            "Web Browser Navigation": {
                "CW": "BrowserForward", "CCW": "BrowserBack", "Click": "BrowserRefresh"
            },
            "Page Scroll (PgDn / PgUp)": {
                "CW": "PageDown", "CCW": "PageUp", "Click": "Enter"
            },
            "Browser Tab Switcher": {
                "CW": "LCtrl+Tab", "CCW": "LCtrl+LShift+Tab", "Click": "LCtrl+W"
            },
            "Document & Screen Zoom": {
                "CW": "LCtrl+Add", "CCW": "LCtrl+Subtract", "Click": "LCtrl+D0"
            }
        }


def get_target_key_categories(lang: Optional[str] = None) -> Dict[str, List[Tuple[str, str]]]:
    l = lang or _CURRENT_LANGUAGE
    if l == "pl":
        return {
            "⌨️ Primary (Klawisze Główne)": [
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
                ("Comma", "Znak , (Przecinek)"), ("Period", "Znak . (Kropka)"), ("Slash", "Znak / (Ukośnik)"),
                ("Esc", "Escape (Esc)"), ("Tab", "Tabulator (Tab)"), ("CapsLock", "Caps Lock"),
                ("Backspace", "Backspace"), ("Enter", "Enter"), ("Space", "Spacja (Space)"),
                ("LeftSpace", "Lewa Spacja (Left Space)"), ("RightSpace", "Prawa Spacja (Right Space)"),
                ("Insert", "Insert (Ins)"), ("Delete", "Delete (Del)"),
                ("Home", "Home"), ("End", "End"),
                ("PageUp", "Page Up (PgUp)"), ("PageDown", "Page Down (PgDn)"),
                ("Up", "Strzałka w górę (▲)"), ("Down", "Strzałka w dół (▼)"),
                ("Left", "Strzałka w lewo (◄)"), ("Right", "Strzałka w prawo (►)"),
                ("F1", "F1"), ("F2", "F2"), ("F3", "F3"), ("F4", "F4"),
                ("F5", "F5"), ("F6", "F6"), ("F7", "F7"), ("F8", "F8"),
                ("F9", "F9"), ("F10", "F10"), ("F11", "F11"), ("F12", "F12"),
                ("LCtrl", "Lewy Control (LCtrl)"), ("RCtrl", "Prawy Control (RCtrl)"),
                ("LShift", "Lewy Shift (LShift)"), ("RShift", "Prawy Shift (RShift)"),
                ("LAlt", "Lewy Alt (LAlt)"), ("RAlt", "Prawy Alt / AltGr (RAlt)"),
                ("LWin", "Lewy Win (LWin)"), ("RWin", "Prawy Win (RWin)"),
                ("Menu", "Menu kontekstowe (App/Menu)")
            ],
            "🔢 Number Pad (Klawiatura Numeryczna)": [
                ("NumLock", "Num Lock"),
                ("NumPad0", "Num 0"), ("NumPad1", "Num 1"), ("NumPad2", "Num 2"),
                ("NumPad3", "Num 3"), ("NumPad4", "Num 4"), ("NumPad5", "Num 5"),
                ("NumPad6", "Num 6"), ("NumPad7", "Num 7"), ("NumPad8", "Num 8"),
                ("NumPad9", "Num 9"),
                ("NumPadAdd", "Num + (Dodawanie)"), ("NumPadSubtract", "Num - (Odejmowanie)"),
                ("NumPadMultiply", "Num * (Mnożenie)"), ("NumPadSlash", "Num / (Dzielenie)"),
                ("NumPadPeriod", "Num . (Kropka)"), ("NumPadEnter", "Num Enter")
            ],
            "🎵 Media (Multimedia i Dźwięk)": [
                ("VolumeUp", "🔊 Głośność + (Volume Up)"),
                ("VolumeDown", "🔉 Głośność - (Volume Down)"),
                ("VolumeMute", "🔇 Wycisz dźwięk (Mute)"),
                ("MediaPlayPause", "⏯️ Odtwarzaj / Pauza"),
                ("MediaNext", "⏭️ Następny utwór"),
                ("MediaPrevious", "⏮️ Poprzedni utwór"),
                ("MediaStop", "⏹️ Zatrzymaj odtwarzanie"),
                ("OpenMediaPlayer", "🎵 Otwórz Odtwarzacz Muzyki"),
                ("Eject", "⏏️ Wysuń nośnik (Eject)")
            ],
            "💡 Backlight (Podświetlenie LED)": [
                ("ToggleLighting", "💡 Włącz / Wyłącz Podświetlenie"),
                ("BrightnessUp", "☀️ Zwiększ Jasność (Brightness +)"),
                ("BrightnessDown", "🌙 Zmniejsz Jasność (Brightness -)"),
                ("LightingSpeedIncrease", "⏩ Przyspiesz Animację LED"),
                ("LightingSpeedDecrease", "⏪ Zwolnij Animację LED"),
                ("LightingPauseResume", "⏸️ Wstrzymaj / Wznów Efekt LED"),
                ("NextLightingEffect", "🌈 Następny Profil / Efekt RGB"),
                ("NextReactiveLightingEffect", "✨ Następny Efekt Reaktywny")
            ],
            "🌐 System & Browser (System i Przeglądarka)": [
                ("OpenCalculator", "🧮 Kalkulator"),
                ("OpenMyComputer", "💻 Mój Komputer / Pliki"),
                ("OpenEmail", "✉️ Klient Poczty Email"),
                ("BrowserHome", "🏠 Strona Główna Przeglądarki"),
                ("BrowserBack", "⬅️ Wstecz w Przeglądarce"),
                ("BrowserForward", "➡️ Dalej w Przeglądarce"),
                ("BrowserRefresh", "🔄 Odśwież Stronę"),
                ("BrowserFavorites", "⭐ Ulubione / Zakładki"),
                ("BrowserSearch", "🔍 Szukaj w Sieci"),
                ("Screenshot", "📸 Zrzut Ekranu (PrintScreen)")
            ],
            "🖱️ Mouse (Symulacja Myszy)": [
                ("MouseLClick", "🖱️ Lewy Przycisk Myszy (L-Click)"),
                ("MouseRClick", "🖱️ Prawy Przycisk Myszy (R-Click)"),
                ("MouseMClick", "🖱️ Środkowy Przycisk Myszy (M-Click)"),
                ("MouseBack", "◀️ Przycisk Myszy Wstecz"),
                ("MouseAdvance", "▶️ Przycisk Myszy Dalej")
            ]
        }
    else:
        return {
            "⌨️ Primary Keys": [
                ("A", "Key A"), ("B", "Key B"), ("C", "Key C"), ("D", "Key D"),
                ("E", "Key E"), ("F", "Key F"), ("G", "Key G"), ("H", "Key H"),
                ("I", "Key I"), ("J", "Key J"), ("K", "Key K"), ("L", "Key L"),
                ("M", "Key M"), ("N", "Key N"), ("O", "Key O"), ("P", "Key P"),
                ("Q", "Key Q"), ("R", "Key R"), ("S", "Key S"), ("T", "Key T"),
                ("U", "Key U"), ("V", "Key V"), ("W", "Key W"), ("X", "Key X"),
                ("Y", "Key Y"), ("Z", "Key Z"),
                ("D1", "Digit 1"), ("D2", "Digit 2"), ("D3", "Digit 3"), ("D4", "Digit 4"),
                ("D5", "Digit 5"), ("D6", "Digit 6"), ("D7", "Digit 7"), ("D8", "Digit 8"),
                ("D9", "Digit 9"), ("D0", "Digit 0"),
                ("BackTick", "Symbol ` (Backtick)"), ("Subtract", "Symbol - (Minus)"), ("Add", "Symbol = (Equals)"),
                ("OpenSquareBrace", "Symbol ["), ("CloseSquareBrace", "Symbol ]"), ("Backslash", "Symbol \\"),
                ("Semicolon", "Symbol ; (Semicolon)"), ("Quotes", "Symbol ' (Apostrophe)"),
                ("Comma", "Symbol , (Comma)"), ("Period", "Symbol . (Period)"), ("Slash", "Symbol / (Slash)"),
                ("Esc", "Escape (Esc)"), ("Tab", "Tabulator (Tab)"), ("CapsLock", "Caps Lock"),
                ("Backspace", "Backspace"), ("Enter", "Enter"), ("Space", "Spacebar (Space)"),
                ("LeftSpace", "Left Spacebar"), ("RightSpace", "Right Spacebar"),
                ("Insert", "Insert (Ins)"), ("Delete", "Delete (Del)"),
                ("Home", "Home"), ("End", "End"),
                ("PageUp", "Page Up (PgUp)"), ("PageDown", "Page Down (PgDn)"),
                ("Up", "Up Arrow (▲)"), ("Down", "Down Arrow (▼)"),
                ("Left", "Left Arrow (◄)"), ("Right", "Right Arrow (►)"),
                ("F1", "F1"), ("F2", "F2"), ("F3", "F3"), ("F4", "F4"),
                ("F5", "F5"), ("F6", "F6"), ("F7", "F7"), ("F8", "F8"),
                ("F9", "F9"), ("F10", "F10"), ("F11", "F11"), ("F12", "F12"),
                ("LCtrl", "Left Control (LCtrl)"), ("RCtrl", "Right Control (RCtrl)"),
                ("LShift", "Left Shift (LShift)"), ("RShift", "Right Shift (RShift)"),
                ("LAlt", "Left Alt (LAlt)"), ("RAlt", "Right Alt / AltGr (RAlt)"),
                ("LWin", "Left Win (LWin)"), ("RWin", "Right Win (RWin)"),
                ("Menu", "Context Menu (App/Menu)")
            ],
            "🔢 Number Pad": [
                ("NumLock", "Num Lock"),
                ("NumPad0", "Num 0"), ("NumPad1", "Num 1"), ("NumPad2", "Num 2"),
                ("NumPad3", "Num 3"), ("NumPad4", "Num 4"), ("NumPad5", "Num 5"),
                ("NumPad6", "Num 6"), ("NumPad7", "Num 7"), ("NumPad8", "Num 8"),
                ("NumPad9", "Num 9"),
                ("NumPadAdd", "Num + (Add)"), ("NumPadSubtract", "Num - (Subtract)"),
                ("NumPadMultiply", "Num * (Multiply)"), ("NumPadSlash", "Num / (Divide)"),
                ("NumPadPeriod", "Num . (Period)"), ("NumPadEnter", "Num Enter")
            ],
            "🎵 Media & Sound": [
                ("VolumeUp", "🔊 Volume Up"),
                ("VolumeDown", "🔉 Volume Down"),
                ("VolumeMute", "🔇 Audio Mute"),
                ("MediaPlayPause", "⏯️ Play / Pause"),
                ("MediaNext", "⏭️ Next Track"),
                ("MediaPrevious", "⏮️ Previous Track"),
                ("MediaStop", "⏹️ Stop Playback"),
                ("OpenMediaPlayer", "🎵 Launch Media Player"),
                ("Eject", "⏏️ Eject Media")
            ],
            "💡 Backlight & Lighting": [
                ("ToggleLighting", "💡 Toggle LED Backlight On/Off"),
                ("BrightnessUp", "☀️ Increase Brightness"),
                ("BrightnessDown", "🌙 Decrease Brightness"),
                ("LightingSpeedIncrease", "⏩ Increase Animation Speed"),
                ("LightingSpeedDecrease", "⏪ Decrease Animation Speed"),
                ("LightingPauseResume", "⏸️ Pause / Resume LED Effect"),
                ("NextLightingEffect", "🌈 Next RGB Profile / Effect"),
                ("NextReactiveLightingEffect", "✨ Next Reactive Effect")
            ],
            "🌐 System & Web Navigation": [
                ("OpenCalculator", "🧮 Calculator"),
                ("OpenMyComputer", "💻 File Explorer / My PC"),
                ("OpenEmail", "✉️ Email Client"),
                ("BrowserHome", "🏠 Browser Home"),
                ("BrowserBack", "⬅️ Browser Back"),
                ("BrowserForward", "➡️ Browser Forward"),
                ("BrowserRefresh", "🔄 Browser Refresh"),
                ("BrowserFavorites", "⭐ Bookmarks / Favorites"),
                ("BrowserSearch", "🔍 Web Search"),
                ("Screenshot", "📸 Screenshot (PrintScreen)")
            ],
            "🖱️ Mouse Emulation": [
                ("MouseLClick", "🖱️ Mouse Left Click"),
                ("MouseRClick", "🖱️ Mouse Right Click"),
                ("MouseMClick", "🖱️ Mouse Middle Click"),
                ("MouseBack", "◀️ Mouse Back Button"),
                ("MouseAdvance", "▶️ Mouse Forward Button")
            ]
        }


def get_popular_shortcuts(lang: Optional[str] = None) -> List[Tuple[str, str]]:
    l = lang or _CURRENT_LANGUAGE
    if l == "pl":
        return [
            ("Ctrl+Alt+T", "LCtrl+LAlt+T", "🖥️ Terminal"),
            ("Super+L", "LWin+L", "🔒 Blokada ekranu"),
            ("Alt+F4", "LAlt+F4", "❌ Zamknij okno"),
            ("Ctrl+Shift+Esc", "LCtrl+LShift+Esc", "📈 Menedżer zadań"),
            ("Super+D", "LWin+D", "🖼️ Pokaż pulpit"),
            ("Ctrl+C", "LCtrl+C", "📋 Kopiuj"),
            ("Ctrl+V", "LCtrl+V", "📥 Wklej"),
            ("Ctrl+X", "LCtrl+X", "✂️ Wytnij"),
            ("Ctrl+Z", "LCtrl+Z", "↩️ Cofnij"),
            ("Ctrl+Y", "LCtrl+Y", "🔁 Ponów"),
            ("Ctrl+S", "LCtrl+S", "💾 Zapisz"),
            ("Ctrl+A", "LCtrl+A", "🔲 Zaznacz wszystko"),
            ("PrtSc", "Screenshot", "📸 Zrzut ekranu")
        ]
    else:
        return [
            ("Ctrl+Alt+T", "LCtrl+LAlt+T", "🖥️ Terminal"),
            ("Super+L", "LWin+L", "🔒 Lock Screen"),
            ("Alt+F4", "LAlt+F4", "❌ Close Window"),
            ("Ctrl+Shift+Esc", "LCtrl+LShift+Esc", "📈 Task Manager / System Monitor"),
            ("Super+D", "LWin+D", "🖼️ Show Desktop"),
            ("Ctrl+C", "LCtrl+C", "📋 Copy"),
            ("Ctrl+V", "LCtrl+V", "📥 Paste"),
            ("Ctrl+X", "LCtrl+X", "✂️ Cut"),
            ("Ctrl+Z", "LCtrl+Z", "↩️ Undo"),
            ("Ctrl+Y", "LCtrl+Y", "🔁 Redo"),
            ("Ctrl+S", "LCtrl+S", "💾 Save"),
            ("Ctrl+A", "LCtrl+A", "🔲 Select All"),
            ("PrtSc", "Screenshot", "📸 Screenshot")
        ]


def get_available_layers(lang: Optional[str] = None) -> List[Tuple[str, str]]:
    l = lang or _CURRENT_LANGUAGE
    if l == "pl":
        return [
            ("Base", "Warstwa Podstawowa (Base)"),
            ("Layer1", "Warstwa 1 (Layer 1)"),
            ("Layer2", "Warstwa 2 (Layer 2)"),
            ("Layer3", "Warstwa 3 (Layer 3)"),
            ("FnLayer1", "Warstwa Fn + 1 (FnLayer1)"),
            ("FnLayer2", "Warstwa Fn + 2 (FnLayer2)"),
            ("FnLayer3", "Warstwa Fn + 3 (FnLayer3)")
        ]
    else:
        return [
            ("Base", "Base Layer (Default)"),
            ("Layer1", "Layer 1 (Standard)"),
            ("Layer2", "Layer 2"),
            ("Layer3", "Layer 3"),
            ("FnLayer1", "Fn + Layer 1"),
            ("FnLayer2", "Fn + Layer 2"),
            ("FnLayer3", "Fn + Layer 3")
        ]
