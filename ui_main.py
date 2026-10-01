import math
import os
import sys
import time
import shutil
from typing import Dict, List, Optional, Any
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QListWidget, QListWidgetItem,
    QLineEdit, QComboBox, QColorDialog, QFrame, QGridLayout,
    QScrollArea, QMessageBox, QProgressBar, QButtonGroup, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox, QCheckBox,
    QGroupBox, QSplitter, QTextEdit, QPlainTextEdit, QFileDialog,
    QRadioButton, QSlider, QMenu, QSystemTrayIcon, QDialog, QInputDialog
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer, QObject
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap, QAction, QPainter, QLinearGradient, QBrush, QPen

from system_checker import SystemChecker
import i18n
from i18n import (
    tr, get_current_language, set_current_language, get_available_languages,
    get_knobs_metadata, get_knob_presets, get_target_key_categories,
    get_popular_shortcuts, get_available_layers, get_action_short_labels,
    get_friendly_action_label
)
from gk_backend import (
    GKBackend, KEY_DEFINITIONS, COLOR_PRESETS, MacroItem, MacroAction,
    HARDWARE_KEY_ALIASES, get_system_battery_info
)


class KeyVisualButton(QPushButton):
    """Interactive visual representation of a keyboard key for RGB & Remap visualizers."""
    key_clicked = Signal(str)

    def __init__(self, key_id: str, label: str, group: str, width_u: float = 1.0, height_u: float = 1.0,
                 knob_id: Optional[str] = None, knob_name: Optional[str] = None, mode: str = "rgb"):
        super().__init__()
        self.key_id = key_id
        self.label_text = label
        self.group = group
        self.width_u = width_u
        self.height_u = height_u
        self.knob_id = knob_id
        self.knob_name = knob_name
        self.mode = mode  # "rgb" or "remap"
        self.current_color = "#24283b"
        self.remap_action: Optional[str] = None
        self.is_selected = False
        self.row = 0
        self.col = 0.0

        # Square keycap proportions: 1u is ~36x38 px
        base_w = max(int(36 * width_u), 28)
        base_h = max(int(38 * height_u), 36)
        self.setMinimumSize(base_w, base_h)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(lambda: self.key_clicked.emit(self.key_id))
        self.update_content_and_style()

    def set_color(self, hex_color: str):
        self.current_color = hex_color
        self.update_content_and_style()

    def set_remap(self, action: Optional[str]):
        self.remap_action = action
        self.update_content_and_style()

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_content_and_style()

    def update_content_and_style(self):
        c = QColor(self.current_color)
        luminance = (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255
        text_color = "#15161e" if luminance > 0.55 else "#ffffff"

        # Content text
        lines = []
        if self.mode == "remap" and self.knob_id:
            knob_short = self.knob_id.replace("Knob", "K")
            lines.append(f"🎛️{knob_short} {self.label_text}")
        else:
            lines.append(self.label_text)

        if self.remap_action:
            short_labels = get_action_short_labels()
            short_act = short_labels.get(self.remap_action, self.remap_action)
            if short_act.startswith("Macro(") and short_act.endswith(")"):
                short_act = "⚡" + short_act[6:-1]
            if len(short_act) > 9:
                short_act = short_act[:8] + ".."
            lines.append(short_act)

        self.setText("\n".join(lines))

        # Borders & Background
        border = "1px solid #3b4261"
        if self.is_selected:
            border = "2px solid #ff9eaf"
        elif self.mode == "remap" and self.knob_id:
            border = "2px solid #ff9e3b"  # Amber highlight for modular knob sockets
        elif self.remap_action:
            border = "2px solid #7aa2f7"

        bg = self.current_color
        if self.mode == "remap":
            if self.knob_id and self.current_color in ["#24283b", "#000000"]:
                bg = "#2b2216"  # Warm dark amber glow for knob sockets
            elif self.remap_action and self.current_color in ["#24283b", "#000000"]:
                bg = "#1f3554"

        # Tooltip
        tip = f"{tr('remap_col_key', 'Key')}: {self.label_text} ({self.key_id})"
        if self.knob_id:
            k_name = self.knob_name or self.knob_id
            tip += f"\n🎛️ {k_name}\n({tr('remap_btn_assign', 'Click to configure knob')})"
        if self.remap_action:
            tip += f"\n{tr('remap_col_action', 'Assigned Function')}: {get_friendly_action_label(self.remap_action)}"
        self.setToolTip(tip)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {text_color};
                border: {border};
                border-radius: 5px;
                font-size: 9px;
                font-weight: bold;
                padding: 1px 2px;
            }}
            QPushButton:hover {{
                border: 2px solid #7dcfff;
            }}
        """)


class GK104ChassisWidget(QFrame):
    """Authentic chassis frame for GK104 Pro with screen mockup, status LEDs, and brushed casing."""
    def __init__(self, title_text: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setObjectName("gk104Chassis")
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 14)
        main_layout.setSpacing(8)

        # Top Bar of Keyboard Case: Brand Badge, Smart Screen, and Status LEDs
        case_top_bar = QHBoxLayout()
        case_top_bar.setContentsMargins(4, 0, 4, 4)

        # Brand Badge
        brand_box = QHBoxLayout()
        brand_icon = QLabel("⌨️")
        brand_icon.setStyleSheet("font-size: 14px;")
        brand_box.addWidget(brand_icon)

        brand_lbl = QLabel("SKYLOONG • GK104 PRO")
        brand_lbl.setStyleSheet("font-family: monospace; font-size: 12px; font-weight: bold; color: #ff9e3b; letter-spacing: 2px;")
        brand_box.addWidget(brand_lbl)

        badge_sub = QLabel("104RGB / HOT-SWAP / 6-KNOBS")
        badge_sub.setStyleSheet("font-size: 9px; color: #565f89; font-weight: bold; margin-left: 6px; padding: 2px 4px; background-color: #16161e; border-radius: 3px;")
        brand_box.addWidget(badge_sub)
        case_top_bar.addLayout(brand_box)

        case_top_bar.addStretch()

        # Center: Realistic 1.04-inch Smart Screen Mockup
        self.screen_frame = QFrame()
        self.screen_frame.setObjectName("smartScreenMockup")
        self.screen_frame.setFixedSize(190, 42)
        self.screen_frame.setStyleSheet("""
            QFrame#smartScreenMockup {
                background-color: #050608;
                border: 2px solid #ff9e3b;
                border-radius: 6px;
                padding: 2px;
            }
        """)
        screen_layout = QVBoxLayout(self.screen_frame)
        screen_layout.setContentsMargins(6, 2, 6, 2)
        screen_layout.setSpacing(0)

        self.screen_txt_title = QLabel(tr("smart_screen_title", "1.04″ SMART SCREEN"))
        self.screen_txt_title.setStyleSheet("color: #7dcfff; font-family: monospace; font-size: 9px; font-weight: bold;")
        self.screen_txt_title.setAlignment(Qt.AlignCenter)
        screen_layout.addWidget(self.screen_txt_title)

        self.screen_txt_info = QLabel("RAINBOW WAVE • 100%")
        self.screen_txt_info.setStyleSheet("color: #ff9eaf; font-family: monospace; font-size: 10px; font-weight: bold;")
        self.screen_txt_info.setAlignment(Qt.AlignCenter)
        screen_layout.addWidget(self.screen_txt_info)

        case_top_bar.addWidget(self.screen_frame)

        case_top_bar.addStretch()

        # Right: Keyboard Lock Indicators (Num, Caps, Scroll, Win Lock)
        leds_box = QHBoxLayout()
        leds_box.setSpacing(6)
        self.led_num = QLabel("NUM")
        self.led_caps = QLabel("CAPS")
        self.led_scroll = QLabel("SCRL")
        self.led_win = QLabel("WIN")

        for led in [self.led_num, self.led_caps, self.led_scroll, self.led_win]:
            led.setStyleSheet("""
                QLabel {
                    background-color: #1a1b26;
                    color: #7aa2f7;
                    border: 1px solid #3b4261;
                    border-radius: 4px;
                    font-size: 8px;
                    font-weight: bold;
                    padding: 2px 6px;
                }
            """)
            leds_box.addWidget(led)
        case_top_bar.addLayout(leds_box)

        main_layout.addLayout(case_top_bar)

        # Sunken Key Switch Plate Container
        self.switch_plate = QFrame()
        self.switch_plate.setObjectName("switchPlate")
        self.switch_plate.setStyleSheet("""
            QFrame#switchPlate {
                background-color: #13141c;
                border: 2px solid #24283b;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        self.plate_layout = QGridLayout(self.switch_plate)
        self.plate_layout.setSpacing(4)
        self.plate_layout.setContentsMargins(4, 4, 4, 4)

        main_layout.addWidget(self.switch_plate)

        self.setStyleSheet("""
            QFrame#gk104Chassis {
                background-color: #1c1e2d;
                border: 2px solid #32374e;
                border-radius: 12px;
            }
        """)

    def update_screen_info(self, title: str, subtitle: str):
        self.screen_txt_title.setText(title)
        self.screen_txt_info.setText(subtitle)


class LiveRGBAnimationController(QObject):
    """Timer-driven ~30 FPS animation controller for realistic real-time keyboard lighting simulation."""
    def __init__(self, buttons_dict: Dict[str, KeyVisualButton], parent=None):
        super().__init__(parent)
        self.buttons = buttons_dict
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._render_frame)
        self.preset_name = "Spectral Cycle"
        self.brightness = 100
        self.speed = 1.0
        self.frame_count = 0
        self.is_running = False
        self.current_mode = "preset"
        self.static_colors: Dict[str, str] = {}

    def start(self):
        self.is_running = True
        self.timer.start(33)  # ~30 FPS

    def stop(self):
        self.is_running = False
        self.timer.stop()

    def set_preset(self, preset_name: str):
        self.preset_name = preset_name
        self.current_mode = "preset"

    def set_brightness(self, value: int):
        self.brightness = max(0, min(100, value))

    def set_speed(self, speed_factor: float):
        self.speed = max(0.1, min(5.0, speed_factor))

    def set_static_mode(self, colors: Dict[str, str]):
        self.static_colors = dict(colors)
        self.current_mode = "static"

    def _render_frame(self):
        if not self.buttons or self.brightness == 0:
            if self.brightness == 0:
                for btn in self.buttons.values():
                    btn.set_color("#14151f")
            return

        self.frame_count += 1
        t = (self.frame_count * 0.04) * self.speed
        factor = self.brightness / 100.0

        if self.current_mode == "static":
            for kid, btn in self.buttons.items():
                hex_c = self.static_colors.get(kid, "#000000")
                if hex_c in ["#000000", "0x000000"]:
                    btn.set_color("#181924")
                else:
                    c = QColor(hex_c)
                    r = int(c.red() * factor)
                    g = int(c.green() * factor)
                    b = int(c.blue() * factor)
                    btn.set_color(f"#{r:02x}{g:02x}{b:02x}")
            return

        # Preset animations
        p_lower = self.preset_name.lower()

        for kid, btn in self.buttons.items():
            row = getattr(btn, "row", 2)
            col = getattr(btn, "col", 10.0)

            if "streamer" in p_lower or "wave" in p_lower:
                hue = int((t * 120 + col * 14 - row * 18) % 360)
                sat = 240
                val = int(255 * factor)
            elif "breath" in p_lower or "respiration" in p_lower:
                pulse = (math.sin(t * 2.5) + 1.0) / 2.0
                hue = int((t * 40) % 360)
                sat = 240
                val = int(255 * pulse * factor)
            elif "windmill" in p_lower or "radar" in p_lower:
                angle = math.degrees(math.atan2(row - 2.5, col - 11.0))
                hue = int((angle + t * 140) % 360)
                sat = 240
                val = int(255 * factor)
            elif "star" in p_lower or "meteor" in p_lower:
                val_hash = math.sin(kid.__hash__() * 0.1 + t * 4.0)
                if val_hash > 0.6:
                    val = int(255 * ((val_hash - 0.6) / 0.4) * factor)
                    hue = int((kid.__hash__() % 360))
                    sat = 200
                else:
                    val = int(30 * factor)
                    hue = 220
                    sat = 255
            elif "matrix" in p_lower:
                wave_v = math.sin(row * 1.5 - t * 5.0 + col * 0.4)
                if wave_v > 0.4:
                    val = int(255 * factor)
                    hue = 120  # Pure green
                    sat = 255
                else:
                    val = int(30 * factor)
                    hue = 120
                    sat = 255
            elif "cyberpunk" in p_lower:
                step = int((col * 0.5 + t * 2.0) % 2)
                hue = 320 if step == 0 else 180  # Pink / Cyan
                sat = 240
                val = int(255 * factor)
            elif "rhythm" in p_lower or "music" in p_lower:
                audio_h = math.sin(t * 8.0 + col * 0.8) * 0.5 + 0.5
                if (5 - row) / 6.0 <= audio_h:
                    hue = int((row * 40 + t * 30) % 360)
                    sat = 255
                    val = int(255 * factor)
                else:
                    hue = 220
                    sat = 100
                    val = int(20 * factor)
            else:  # Standard Spectrum Cycle
                hue = int((t * 80 + col * 12 + row * 6) % 360)
                sat = 240
                val = int(255 * factor)

            c = QColor.fromHsv(max(0, min(359, hue)), max(0, min(255, sat)), max(0, min(255, val)))
            btn.set_color(c.name())


class ComponentInstallerDialog(QDialog):
    """Interactive assistant for checking and installing Mono, udev rules and USB permissions."""
    def __init__(self, parent=None, auto_prompt_install=False):
        super().__init__(parent)
        self.setWindowTitle(tr("diag_title", "⚙️ System Diagnostics & Requirements Wizard"))
        self.resize(680, 520)
        self.auto_prompt_install = auto_prompt_install
        self.init_ui()
        self.refresh_diagnostics()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # Header title
        title_box = QVBoxLayout()
        header = QLabel(tr("diag_header", "Linux Environment & Hardware Access Verification"))
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #7aa2f7;")
        sub = QLabel(tr("diag_mono_desc", "Required by GK6X low-level communication driver to access hardware without root permissions."))
        sub.setStyleSheet("color: #a9b1d6; font-size: 12px;")
        sub.setWordWrap(True)
        title_box.addWidget(header)
        title_box.addWidget(sub)
        layout.addLayout(title_box)

        # Diagnostic items group
        self.status_group = QGroupBox(tr("diag_title", "Components Status"))
        status_layout = QVBoxLayout(self.status_group)
        status_layout.setSpacing(10)

        # Mono status
        self.lbl_mono_status = QLabel(f"{tr('diag_mono_title')}: Checking...")
        self.lbl_mono_status.setStyleSheet("font-size: 13px;")
        status_layout.addWidget(self.lbl_mono_status)

        # Udev rules status
        self.lbl_udev_status = QLabel(f"{tr('diag_udev_title')}: Checking...")
        self.lbl_udev_status.setStyleSheet("font-size: 13px;")
        status_layout.addWidget(self.lbl_udev_status)

        # Hidraw permission status
        self.lbl_perm_status = QLabel(f"{tr('diag_usb_title')}: Checking...")
        self.lbl_perm_status.setStyleSheet("font-size: 13px;")
        status_layout.addWidget(self.lbl_perm_status)

        layout.addWidget(self.status_group)

        # Auto install / script preview box
        self.script_group = QGroupBox("Automated Setup & Fix")
        script_layout = QVBoxLayout(self.script_group)

        self.lbl_action_hint = QLabel("Click the button below to automatically install missing packages and configure udev rules:")
        self.lbl_action_hint.setStyleSheet("color: #ff9eaf; font-size: 12px; font-weight: bold;")
        script_layout.addWidget(self.lbl_action_hint)

        self.btn_auto_install = QPushButton(tr("diag_btn_autofix", "⚡ Run Automatic Setup (sudo ./install_rules.sh)"))
        self.btn_auto_install.setObjectName("primaryBtn")
        self.btn_auto_install.setStyleSheet("padding: 10px; font-size: 13px; font-weight: bold;")
        self.btn_auto_install.clicked.connect(self.on_run_auto_install)
        script_layout.addWidget(self.btn_auto_install)

        layout.addWidget(self.script_group)

        # Bottom buttons
        bottom_row = QHBoxLayout()
        self.btn_recheck = QPushButton(tr("diag_btn_recheck", "🔄 Re-check"))
        self.btn_recheck.clicked.connect(self.refresh_diagnostics)
        bottom_row.addWidget(self.btn_recheck)

        bottom_row.addStretch()

        self.btn_close = QPushButton(tr("diag_btn_close", "Close"))
        self.btn_close.clicked.connect(self.accept)
        bottom_row.addWidget(self.btn_close)

        layout.addLayout(bottom_row)

    def refresh_diagnostics(self):
        diag = SystemChecker.get_full_diagnostics()

        # Mono
        mono = diag["mono"]
        if mono["installed"]:
            self.lbl_mono_status.setText(f"✅ {tr('diag_mono_title')}: {mono['version']} ({mono['path']})")
            self.lbl_mono_status.setStyleSheet("color: #9ece6a; font-weight: bold; font-size: 13px;")
        else:
            self.lbl_mono_status.setText(f"❌ {tr('diag_mono_title')}: {tr('diag_status_fail')}")
            self.lbl_mono_status.setStyleSheet("color: #f7768e; font-weight: bold; font-size: 13px;")

        # Udev
        udev = diag["udev"]
        if udev["installed"]:
            self.lbl_udev_status.setText(f"✅ {tr('diag_udev_title')}: {tr('diag_status_ok')} ({udev['path']})")
            self.lbl_udev_status.setStyleSheet("color: #9ece6a; font-weight: bold; font-size: 13px;")
        else:
            self.lbl_udev_status.setText(f"❌ {tr('diag_udev_title')}: {tr('diag_status_fail')}")
            self.lbl_udev_status.setStyleSheet("color: #f7768e; font-weight: bold; font-size: 13px;")

        # Permissions
        perms = diag["permissions"]
        if perms["has_access"]:
            nodes_str = ", ".join(perms["accessible_nodes"]) if perms["accessible_nodes"] else "hidraw OK"
            self.lbl_perm_status.setText(f"✅ {tr('diag_usb_title')}: {tr('diag_status_ok')} ({nodes_str})")
            self.lbl_perm_status.setStyleSheet("color: #9ece6a; font-weight: bold; font-size: 13px;")
        else:
            self.lbl_perm_status.setText(f"⚠️ {tr('diag_usb_title')}: {tr('diag_status_fail')}")
            self.lbl_perm_status.setStyleSheet("color: #e0af68; font-weight: bold; font-size: 13px;")

        if diag["all_ok"]:
            self.lbl_action_hint.setText("✅ System environment is fully configured! Hardware bridge is ready.")
            self.lbl_action_hint.setStyleSheet("color: #9ece6a; font-weight: bold;")
            self.btn_auto_install.setEnabled(False)
        else:
            self.lbl_action_hint.setText(f"⚠️ Missing components: {', '.join(diag['missing_items'])}")
            self.lbl_action_hint.setStyleSheet("color: #f7768e; font-weight: bold;")
            self.btn_auto_install.setEnabled(True)

    def on_run_auto_install(self):
        self.btn_auto_install.setEnabled(False)
        self.btn_auto_install.setText("Running setup script...")
        QApplication.processEvents()

        ok, msg = SystemChecker.run_installation()
        self.refresh_diagnostics()
        self.btn_auto_install.setText(tr("diag_btn_autofix", "⚡ Run Automatic Setup (sudo ./install_rules.sh)"))

        if ok:
            QMessageBox.information(self, tr("msg_success", "Success"), msg)
        else:
            QMessageBox.warning(self, tr("msg_error", "Error"), msg)


class ProfileManagerDialog(QDialog):
    """Dialog for managing user configuration profiles, importing, exporting, and flashing."""
    def __init__(self, backend: GKBackend, main_window=None, parent=None):
        super().__init__(parent or main_window)
        self.backend = backend
        self.main_window = main_window
        self.setWindowTitle(tr("pm_title", "📁 Profile & Backup Manager"))
        self.resize(760, 500)
        self.profiles_data: List[Dict[str, Any]] = []
        self.init_ui()
        self.refresh_profiles_list()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Top title & description
        top_box = QVBoxLayout()
        header = QLabel(tr("pm_title", "📁 Profile & Backup Manager"))
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #7aa2f7;")
        sub = QLabel("Manage your saved configurations, backups, and GK6X UserData files.")
        sub.setStyleSheet("color: #a9b1d6; font-size: 12px;")
        top_box.addWidget(header)
        top_box.addWidget(sub)
        layout.addLayout(top_box)

        # Profiles Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            tr("pm_col_name", "Profile Name"),
            tr("pm_col_type", "Format"),
            tr("pm_col_date", "Last Modified"),
            tr("pm_col_size", "Size")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemDoubleClicked.connect(self.on_table_double_clicked)
        layout.addWidget(self.table)

        # Status / Selected item info
        self.lbl_selected_info = QLabel(tr("pm_no_profiles", "No profiles saved yet."))
        self.lbl_selected_info.setStyleSheet("color: #7dcfff; font-size: 11px;")
        layout.addWidget(self.lbl_selected_info)

        # Action Buttons row
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.btn_save_current = QPushButton(tr("pm_btn_save_current", "💾 Save Current Settings..."))
        self.btn_save_current.setStyleSheet("padding: 6px 12px; font-weight: bold;")
        self.btn_save_current.clicked.connect(self.on_save_current_clicked)
        action_row.addWidget(self.btn_save_current)

        self.btn_import_file = QPushButton(tr("pm_btn_import", "📂 Import File..."))
        self.btn_import_file.clicked.connect(self.on_import_file_clicked)
        action_row.addWidget(self.btn_import_file)

        self.btn_export_file = QPushButton(tr("pm_btn_export", "📤 Export File..."))
        self.btn_export_file.setEnabled(False)
        self.btn_export_file.clicked.connect(self.on_export_file_clicked)
        action_row.addWidget(self.btn_export_file)

        action_row.addStretch()
        layout.addLayout(action_row)

        # Bottom Operation Bar
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.btn_load_to_app = QPushButton(tr("pm_btn_load", "📥 Load to Editor"))
        self.btn_load_to_app.setObjectName("primaryBtn")
        self.btn_load_to_app.setStyleSheet("padding: 8px 16px; font-weight: bold; min-height: 24px;")
        self.btn_load_to_app.setEnabled(False)
        self.btn_load_to_app.clicked.connect(self.on_load_to_app_clicked)
        bottom_row.addWidget(self.btn_load_to_app)

        self.btn_flash_to_kb = QPushButton(tr("pm_btn_flash", "⚡ Flash to Keyboard"))
        self.btn_flash_to_kb.setObjectName("successBtn")
        self.btn_flash_to_kb.setStyleSheet("padding: 8px 16px; font-weight: bold; min-height: 24px;")
        self.btn_flash_to_kb.setEnabled(False)
        self.btn_flash_to_kb.clicked.connect(self.on_flash_to_kb_clicked)
        bottom_row.addWidget(self.btn_flash_to_kb)

        self.btn_delete = QPushButton(tr("pm_btn_delete", "🗑️ Delete"))
        self.btn_delete.setObjectName("dangerBtn")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        bottom_row.addWidget(self.btn_delete)

        bottom_row.addStretch()

        btn_close = QPushButton(tr("pm_btn_close", "Close"))
        btn_close.clicked.connect(self.accept)
        bottom_row.addWidget(btn_close)

        layout.addLayout(bottom_row)

    def refresh_profiles_list(self):
        self.profiles_data = self.backend.get_saved_profiles()
        self.table.setRowCount(len(self.profiles_data))
        for row, p in enumerate(self.profiles_data):
            it_name = QTableWidgetItem(f"📄 {p['name']}")
            it_name.setData(Qt.UserRole, p)
            it_type = QTableWidgetItem(p["type"])
            it_date = QTableWidgetItem(p["date"])
            it_size = QTableWidgetItem(p["size_str"])

            for it in [it_name, it_type, it_date, it_size]:
                it.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            self.table.setItem(row, 0, it_name)
            self.table.setItem(row, 1, it_type)
            self.table.setItem(row, 2, it_date)
            self.table.setItem(row, 3, it_size)

        if not self.profiles_data:
            self.lbl_selected_info.setText(tr("pm_no_profiles"))
        else:
            self.lbl_selected_info.setText(tr("pm_available_count", count=len(self.profiles_data)))

        self.on_selection_changed()

    def _get_selected_profile(self) -> Optional[Dict[str, Any]]:
        row = self.table.currentRow()
        if 0 <= row < len(self.profiles_data):
            return self.profiles_data[row]
        return None

    def on_selection_changed(self):
        p = self._get_selected_profile()
        has_sel = p is not None
        self.btn_load_to_app.setEnabled(has_sel)
        self.btn_flash_to_kb.setEnabled(has_sel)
        self.btn_export_file.setEnabled(has_sel)
        self.btn_delete.setEnabled(has_sel)

        if p:
            self.lbl_selected_info.setText(
                tr("pm_selected_info", name=p["name"], type=p["type"], size=p["size_str"], date=p["date"])
            )

    def on_table_double_clicked(self, item):
        self.on_load_to_app_clicked()

    def on_load_to_app_clicked(self):
        p = self._get_selected_profile()
        if not p:
            return
        ok, msg, _ = self.backend.load_any_config_file(p["path"])
        if ok:
            if self.main_window and hasattr(self.main_window, "apply_loaded_state_to_ui"):
                self.main_window.apply_loaded_state_to_ui()
            QMessageBox.information(self, tr("msg_success", "Success"), tr("msg_profile_loaded", name=p["name"]))
        else:
            QMessageBox.critical(self, tr("msg_error", "Error"), msg)

    def on_flash_to_kb_clicked(self):
        p = self._get_selected_profile()
        if not p:
            return
        reply = QMessageBox.question(
            self,
            tr("pm_btn_flash", "Flash to Keyboard"),
            f"Flash profile '{p['name']}' directly to keyboard memory?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            ok, msg, _ = self.backend.load_any_config_file(p["path"])
            if ok:
                if self.main_window and hasattr(self.main_window, "apply_loaded_state_to_ui"):
                    self.main_window.apply_loaded_state_to_ui()
                if self.main_window and hasattr(self.main_window, "apply_full_configuration"):
                    self.accept()
                    self.main_window.apply_full_configuration()
            else:
                QMessageBox.critical(self, tr("msg_error", "Error"), msg)

    def on_save_current_clicked(self):
        name, ok = QInputDialog.getText(
            self,
            tr("pm_btn_save_current", "Save Profile"),
            "Enter profile name (e.g. Work_Layout, FPS_Gaming, Knob_Controls):"
        )
        if ok and name.strip():
            ptype, ok_type = QInputDialog.getItem(
                self,
                "File Format",
                "Select format:",
                ["JSON Profile (.json - recommended)", "GK6X UserData (.txt)"],
                0,
                False
            )
            if ok_type:
                fmt = "txt" if "UserData" in ptype else "json"
                out_path = self.backend.save_named_profile(name.strip(), profile_type=fmt)
                self.refresh_profiles_list()
                QMessageBox.information(
                    self,
                    tr("msg_success", "Success"),
                    tr("msg_profile_saved", name=name.strip())
                )

    def on_import_file_clicked(self):
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Select file to import",
            "",
            "Config Files (*.json *.txt *.gkprofile);;JSON Profile (*.json *.gkprofile);;UserData TXT (*.txt);;All files (*)"
        )
        if fname and os.path.exists(fname):
            basename = os.path.splitext(os.path.basename(fname))[0]
            fmt = "txt" if fname.endswith(".txt") else "json"
            ok, msg, _ = self.backend.load_any_config_file(fname)
            if ok:
                self.backend.save_named_profile(basename, profile_type=fmt)
                self.refresh_profiles_list()
                if self.main_window and hasattr(self.main_window, "apply_loaded_state_to_ui"):
                    self.main_window.apply_loaded_state_to_ui()
                QMessageBox.information(
                    self,
                    tr("msg_success", "Success"),
                    f"Profile '{basename}' imported and loaded."
                )
            else:
                QMessageBox.critical(self, tr("msg_error", "Error"), msg)

    def on_export_file_clicked(self):
        p = self._get_selected_profile()
        if not p:
            return
        ext_filter = "JSON Profile (*.json)" if p["type"] == "JSON Profile" else "UserData TXT (*.txt)"
        fname, _ = QFileDialog.getSaveFileName(self, "Export Profile", p["filename"], f"{ext_filter};;All files (*)")
        if fname:
            try:
                shutil.copy2(p["path"], fname)
                QMessageBox.information(self, tr("msg_success", "Success"), f"Exported to:\n{fname}")
            except Exception as e:
                QMessageBox.critical(self, tr("msg_error", "Error"), str(e))

    def on_delete_clicked(self):
        p = self._get_selected_profile()
        if not p:
            return
        reply = QMessageBox.question(
            self,
            tr("pm_btn_delete", "Delete"),
            tr("msg_delete_confirm", name=p["name"]),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.backend.delete_named_profile(p["filename"]):
                self.refresh_profiles_list()
                QMessageBox.information(self, tr("msg_success", "Success"), tr("msg_profile_deleted", name=p["name"]))
            else:
                QMessageBox.warning(self, tr("msg_error", "Error"), "Failed to delete file.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_window_title", "Skyloong GK104 Pro Studio — RGB • Remap • Macros • Knobs"))
        self.resize(1200, 880)
        self.setMinimumSize(960, 680)

        self.backend = GKBackend()
        self.space_mode = getattr(self.backend, "space_mode", "split")

        # RGB state
        self.rgb_key_buttons: Dict[str, KeyVisualButton] = {}
        self.selected_brush_color = "#00ffff"
        self.current_key_colors: Dict[str, str] = {k["id"]: "#000000" for k in KEY_DEFINITIONS}
        self.all_effects: List[Dict[str, str]] = []

        # Remap state
        self.remap_key_buttons: Dict[str, KeyVisualButton] = {}
        self.knob_action_buttons: Dict[str, QPushButton] = {}
        self.knob_preset_combos: List[QComboBox] = []
        self.selected_remap_key: Optional[str] = "LeftSpace" if self.space_mode == "split" else "Space_18"
        self.current_remap_layer = "Layer1"

        # Macro state
        self.current_macro_name: Optional[str] = None

        self.init_ui()
        self.init_system_tray()

        # Initialize Live RGB Animation Engine
        self.live_anim = LiveRGBAnimationController(self.rgb_key_buttons, self)
        initial_preset = self.backend.lighting_config.get("preset_name", "Spectral Cycle")
        initial_bright = int(self.backend.lighting_config.get("brightness", 100))
        self.live_anim.set_preset(initial_preset)
        self.live_anim.set_brightness(initial_bright)
        self.live_anim.start()

        self.connect_signals()
        self.refresh_device()
        self.load_effects()
        self.refresh_remap_ui()
        self.refresh_macro_list_ui()

        # Check startup environment and dependencies
        QTimer.singleShot(700, self.check_startup_components)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 1. Top Header Bar
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(10)

        # App Title & Device info
        title_box = QVBoxLayout()
        self.title_lbl = QLabel(tr("app_title", "Skyloong GK104 Pro Studio"))
        self.title_lbl.setObjectName("appTitle")
        self.title_lbl.setStyleSheet("font-size: 17px; font-weight: bold; color: #7aa2f7;")
        title_box.addWidget(self.title_lbl)

        self.device_status_lbl = QLabel(tr("device_detecting", "Detecting GK104 Pro device..."))
        self.device_status_lbl.setObjectName("deviceStatus")
        self.device_status_lbl.setStyleSheet("color: #9ece6a; font-size: 11px;")
        title_box.addWidget(self.device_status_lbl)
        header_layout.addLayout(title_box)

        header_layout.addSpacing(10)

        # Battery Status Widget in Header
        self.lbl_battery_header = QLabel(tr("battery_checking", "🔋 Battery: Checking..."))
        self.lbl_battery_header.setStyleSheet("color: #7aa2f7; font-size: 11px; font-weight: bold; background-color: #13141c; padding: 6px 10px; border-radius: 6px; border: 1px solid #24283b;")
        header_layout.addWidget(self.lbl_battery_header)

        header_layout.addStretch()

        # Language Selector
        lang_box = QHBoxLayout()
        self.lbl_lang_header = QLabel(tr("lang_selector_label", "🌐 Language:"))
        self.lbl_lang_header.setStyleSheet("color: #7aa2f7; font-size: 11px; font-weight: bold;")
        lang_box.addWidget(self.lbl_lang_header)

        self.lang_combo = QComboBox()
        self.lang_combo.setStyleSheet("background-color: #24283b; color: #c0caf5; border: 1px solid #3b4261; border-radius: 6px; padding: 4px 8px; font-weight: bold; min-width: 100px; min-height: 24px;")
        for code, name in get_available_languages():
            self.lang_combo.addItem(name, code)

        cur_lang = get_current_language()
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == cur_lang:
                self.lang_combo.setCurrentIndex(i)
                break

        self.lang_combo.currentIndexChanged.connect(self.on_language_selector_changed)
        lang_box.addWidget(self.lang_combo)
        header_layout.addLayout(lang_box)

        header_layout.addSpacing(6)

        # Global Action Buttons
        self.btn_check_system = QPushButton(tr("btn_system_req", "⚙️ System"))
        self.btn_check_system.setToolTip(tr("btn_system_req_tip", "Check and configure system dependencies, Mono and Udev rules"))
        self.btn_check_system.setStyleSheet("background-color: #24283b; color: #7aa2f7; border: 1px solid #3b4261; border-radius: 6px; padding: 6px 12px; min-height: 24px;")
        self.btn_check_system.clicked.connect(self.open_components_dialog)
        header_layout.addWidget(self.btn_check_system)

        # Profiles & Files Dropdown Menu Button
        self.btn_profiles_menu = QPushButton(tr("btn_profiles_menu", "📁 Profiles & Files ▾"))
        self.btn_profiles_menu.setToolTip(tr("btn_profiles_menu_tip", "Manage saved profiles, UserData files and backups"))
        self.btn_profiles_menu.setStyleSheet("background-color: #24283b; color: #7aa2f7; border: 1px solid #3b4261; border-radius: 6px; padding: 6px 12px; min-height: 24px; font-weight: bold;")

        self.profiles_menu = QMenu(self)
        self.profiles_menu.setStyleSheet("background-color: #1f2335; color: #c0caf5; border: 1px solid #414868; padding: 4px;")
        self._build_profiles_menu()
        self.btn_profiles_menu.setMenu(self.profiles_menu)
        header_layout.addWidget(self.btn_profiles_menu)

        self.btn_refresh_dev = QPushButton(tr("btn_refresh", "🔄 Refresh"))
        self.btn_refresh_dev.setToolTip(tr("btn_refresh_tip", "Refresh device connection and hardware"))
        self.btn_refresh_dev.setStyleSheet("min-height: 24px; padding: 6px 12px;")
        self.btn_refresh_dev.clicked.connect(self.refresh_device)
        header_layout.addWidget(self.btn_refresh_dev)

        self.btn_reset_mappings = QPushButton(tr("btn_reset", "⚠️ Reset (Unmap)"))
        self.btn_reset_mappings.setToolTip(tr("btn_reset_tip", "Restore factory key mappings"))
        self.btn_reset_mappings.setObjectName("dangerBtn")
        self.btn_reset_mappings.setStyleSheet("min-height: 24px; padding: 6px 12px;")
        self.btn_reset_mappings.clicked.connect(self.reset_factory_mappings)
        header_layout.addWidget(self.btn_reset_mappings)

        self.btn_apply_all = QPushButton(tr("btn_flash", "💾 FLASH TO KEYBOARD"))
        self.btn_apply_all.setObjectName("primaryBtn")
        self.btn_apply_all.setStyleSheet("padding: 8px 18px; font-size: 12px; font-weight: bold; min-height: 24px;")
        self.btn_apply_all.clicked.connect(self.apply_full_configuration)
        header_layout.addWidget(self.btn_apply_all)

        main_layout.addWidget(header_frame)

        # 2. Main Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_lighting_tab(), tr("tab_lighting", "🌈 RGB Lighting"))
        self.tab_widget.addTab(self.create_remap_tab(), tr("tab_remap", "⌨️ Remap & Knobs"))
        self.tab_widget.addTab(self.create_macro_tab(), tr("tab_macro", "⚡ Macro Studio"))
        self.tab_widget.addTab(self.create_debug_tab(), tr("tab_debug", "📝 Code & Diagnostics"))
        self.tab_widget.setCurrentIndex(1)  # Default to Remap tab
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tab_widget)

        # 3. Bottom Status / Progress Bar
        bottom_box = QHBoxLayout()
        self.lbl_bottom_info = QLabel(tr("lbl_status_ready", "Ready."))
        self.lbl_bottom_info.setStyleSheet("color: #7982a9; font-size: 11px;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setFixedWidth(160)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3b4261;
                border-radius: 6px;
                background-color: #1a1b26;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #7aa2f7;
                border-radius: 5px;
            }
        """)

        bottom_box.addWidget(self.lbl_bottom_info)
        bottom_box.addStretch()
        bottom_box.addWidget(self.progress_bar)
        main_layout.addLayout(bottom_box)

    def _build_profiles_menu(self):
        self.profiles_menu.clear()
        act_open_mgr = self.profiles_menu.addAction(tr("menu_profile_manager", "📋 Saved Profiles Manager..."))
        act_open_mgr.triggered.connect(self.open_profile_manager)

        self.profiles_menu.addSeparator()

        act_save_json = self.profiles_menu.addAction(tr("menu_save_json", "💾 Save Profile as JSON..."))
        act_save_json.triggered.connect(lambda: self.save_profile_dialog(default_type="json"))

        act_save_txt = self.profiles_menu.addAction(tr("menu_save_txt", "📄 Save Hardware Code (.txt UserData)..."))
        act_save_txt.triggered.connect(self.export_raw_config_dialog)

        self.profiles_menu.addSeparator()

        act_load_file = self.profiles_menu.addAction(tr("menu_load_file", "📂 Load Profile / Config file (.json / .txt)..."))
        act_load_file.triggered.connect(lambda: self.load_profile_dialog(auto_apply=False))

        act_flash_file = self.profiles_menu.addAction(tr("menu_flash_file", "⚡ Load File & Flash directly to Keyboard..."))
        act_flash_file.triggered.connect(lambda: self.load_profile_dialog(auto_apply=True))

    def on_language_selector_changed(self, index: int):
        code = self.lang_combo.itemData(index)
        if code and code != get_current_language():
            set_current_language(code)
            self.retranslate_ui()

    def retranslate_ui(self):
        """Dynamically retranslate all labels, buttons, tabs and inspectors."""
        self.setWindowTitle(tr("app_window_title", "Skyloong GK104 Pro Studio — RGB • Remap • Macros • Knobs"))
        self.title_lbl.setText(tr("app_title", "Skyloong GK104 Pro Studio"))
        self.lbl_lang_header.setText(tr("lang_selector_label", "🌐 Language:"))
        self.btn_check_system.setText(tr("btn_system_req", "⚙️ System"))
        self.btn_check_system.setToolTip(tr("btn_system_req_tip"))
        self.btn_profiles_menu.setText(tr("btn_profiles_menu", "📁 Profiles & Files ▾"))
        self.btn_profiles_menu.setToolTip(tr("btn_profiles_menu_tip"))
        self._build_profiles_menu()
        self.btn_refresh_dev.setText(tr("btn_refresh", "🔄 Refresh"))
        self.btn_refresh_dev.setToolTip(tr("btn_refresh_tip"))
        self.btn_reset_mappings.setText(tr("btn_reset", "⚠️ Reset (Unmap)"))
        self.btn_reset_mappings.setToolTip(tr("btn_reset_tip"))
        self.btn_apply_all.setText(tr("btn_flash", "💾 FLASH TO KEYBOARD"))
        self.lbl_bottom_info.setText(tr("lbl_status_ready", "Ready."))

        # Retranslate Tabs
        self.tab_widget.setTabText(0, tr("tab_lighting", "🌈 RGB Lighting"))
        self.tab_widget.setTabText(1, tr("tab_remap", "⌨️ Remap & Knobs"))
        self.tab_widget.setTabText(2, tr("tab_macro", "⚡ Macro Studio"))
        self.tab_widget.setTabText(3, tr("tab_debug", "📝 Code & Diagnostics"))

        # Retranslate RGB Tab
        if hasattr(self, "lbl_rgb_title"):
            self.lbl_rgb_title.setText(tr("rgb_header_title"))
        if hasattr(self, "btn_toggle_anim"):
            self.btn_toggle_anim.setText(tr("rgb_pause_anim") if self.live_anim.is_running else tr("rgb_start_anim"))
        if hasattr(self, "lbl_rgb_speed"):
            self.lbl_rgb_speed.setText(tr("rgb_speed_label"))
        if hasattr(self, "lbl_rgb_space_mode"):
            self.lbl_rgb_space_mode.setText(tr("rgb_space_layout_label"))
        if hasattr(self, "rgb_radio_split_space"):
            self.rgb_radio_split_space.setText(tr("rgb_space_split"))
        if hasattr(self, "rgb_radio_single_space"):
            self.rgb_radio_single_space.setText(tr("rgb_space_standard"))
        if hasattr(self, "lbl_rgb_target_layer"):
            self.lbl_rgb_target_layer.setText(tr("rgb_target_layer"))
        if hasattr(self, "lbl_effects_lib"):
            self.lbl_effects_lib.setText(tr("rgb_effects_library"))
        if hasattr(self, "effect_search_input"):
            self.effect_search_input.setPlaceholderText(tr("rgb_search_placeholder"))
        if hasattr(self, "btn_apply_effect"):
            self.btn_apply_effect.setText(tr("rgb_apply_effect_btn"))
        if hasattr(self, "lbl_rgb_tools_title"):
            self.lbl_rgb_tools_title.setText(tr("rgb_tools_title"))
        if hasattr(self, "lbl_rgb_current_brush"):
            self.lbl_rgb_current_brush.setText(tr("rgb_current_brush"))
        if hasattr(self, "btn_pick_color"):
            self.btn_pick_color.setText(tr("rgb_pick_color_btn"))
        if hasattr(self, "zone_group"):
            self.zone_group.setTitle(tr("rgb_zone_painting"))
        if hasattr(self, "theme_group"):
            self.theme_group.setTitle(tr("rgb_color_themes"))
        if hasattr(self, "bright_group"):
            self.bright_group.setTitle(tr("rgb_brightness_title"))
        if hasattr(self, "lbl_brightness_val"):
            self.lbl_brightness_val.setText(tr("rgb_brightness_label", val=int(self.brightness_slider.value())))
        if hasattr(self, "btn_apply_bright"):
            self.btn_apply_bright.setText(tr("rgb_btn_apply_bright"))
        if hasattr(self, "btn_led_off"):
            self.btn_led_off.setText(tr("rgb_btn_led_off"))
        if hasattr(self, "btn_apply_static"):
            self.btn_apply_static.setText(tr("rgb_btn_apply_static"))

        # Retranslate Remap Tab
        if hasattr(self, "lbl_remap_layer"):
            self.lbl_remap_layer.setText(tr("remap_active_layer"))
        if hasattr(self, "remap_layer_combo"):
            cur_l = self.remap_layer_combo.currentData()
            self.remap_layer_combo.blockSignals(True)
            self.remap_layer_combo.clear()
            for lid, lname in get_available_layers():
                self.remap_layer_combo.addItem(lname, lid)
            idx = self.remap_layer_combo.findData(cur_l)
            if idx >= 0:
                self.remap_layer_combo.setCurrentIndex(idx)
            self.remap_layer_combo.blockSignals(False)

        if hasattr(self, "lbl_remap_space_mode"):
            self.lbl_remap_space_mode.setText(tr("remap_space_mode"))
        if hasattr(self, "remap_radio_split_space"):
            self.remap_radio_split_space.setText(tr("remap_space_split"))
        if hasattr(self, "remap_radio_single_space"):
            self.remap_radio_single_space.setText(tr("remap_space_standard"))
        if hasattr(self, "btn_clear_layer_top"):
            self.btn_clear_layer_top.setText(tr("remap_btn_clear_layer"))
        if hasattr(self, "remap_title_header"):
            self.remap_title_header.setText(tr("rgb_header_title"))
        if hasattr(self, "legend_knob"):
            self.legend_knob.setText(tr("remap_knobs_title"))
        if hasattr(self, "knobs_title"):
            self.knobs_title.setText(tr("remap_knobs_title"))
        if hasattr(self, "btn_copy_knobs"):
            self.btn_copy_knobs.setText(tr("remap_btn_copy_knobs"))
            self.btn_copy_knobs.setToolTip(tr("remap_btn_copy_knobs_tip"))
        if hasattr(self, "lbl_assign_header_title"):
            self.lbl_assign_header_title.setText(tr("remap_inspector_title"))
        if hasattr(self, "remap_action_search"):
            self.remap_action_search.setPlaceholderText(tr("remap_search_placeholder"))
        if hasattr(self, "btn_assign_action"):
            self.btn_assign_action.setText(tr("remap_btn_assign"))
        if hasattr(self, "btn_reset_single_key"):
            self.btn_reset_single_key.setText(tr("remap_btn_reset_key"))
        if hasattr(self, "lbl_remap_table_title"):
            self.lbl_remap_table_title.setText(tr("remap_table_title", layer=self.current_remap_layer))
        if hasattr(self, "remap_table"):
            self.remap_table.setHorizontalHeaderLabels([
                tr("remap_col_key"),
                tr("remap_col_action"),
                tr("remap_col_code"),
                tr("remap_col_delete")
            ])
        if hasattr(self, "btn_clear_layer_bottom"):
            self.btn_clear_layer_bottom.setText(tr("remap_btn_clear_layer"))

        # Retranslate Macro Tab
        if hasattr(self, "macro_lib_group"):
            self.macro_lib_group.setTitle(tr("macro_library_title"))
        if hasattr(self, "btn_new_macro"):
            self.btn_new_macro.setText(tr("macro_btn_new"))
        if hasattr(self, "btn_del_macro"):
            self.btn_del_macro.setText(tr("macro_btn_delete"))
        if hasattr(self, "btn_dup_macro"):
            self.btn_dup_macro.setText(tr("macro_btn_dup"))
        if hasattr(self, "btn_rename_macro"):
            self.btn_rename_macro.setText(tr("macro_btn_rename"))
        if hasattr(self, "macro_editor_group"):
            self.macro_editor_group.setTitle(tr("macro_editor_title"))
        if hasattr(self, "lbl_macro_name"):
            self.lbl_macro_name.setText(tr("macro_name_label"))
        if hasattr(self, "lbl_macro_repeat"):
            self.lbl_macro_repeat.setText(tr("macro_repeat_label"))
        if hasattr(self, "lbl_macro_repeat_count"):
            self.lbl_macro_repeat_count.setText(tr("macro_repeat_count"))
        if hasattr(self, "macro_actions_table"):
            self.macro_actions_table.setHorizontalHeaderLabels([
                tr("macro_table_col_event"),
                tr("macro_table_col_key"),
                tr("macro_table_col_delay"),
                "Action"
            ])
        if hasattr(self, "btn_add_macro_step"):
            self.btn_add_macro_step.setText(tr("macro_btn_add_step"))
        if hasattr(self, "btn_clear_macro_steps"):
            self.btn_clear_macro_steps.setText(tr("macro_btn_clear_steps"))
        if hasattr(self, "text_macro_group"):
            self.text_macro_group.setTitle(tr("macro_quick_text_title"))
        if hasattr(self, "lbl_quick_text_hint"):
            self.lbl_quick_text_hint.setText(tr("macro_quick_text_label"))
        if hasattr(self, "lbl_quick_text_speed"):
            self.lbl_quick_text_speed.setText(tr("macro_quick_text_speed"))
        if hasattr(self, "btn_generate_text_macro"):
            self.btn_generate_text_macro.setText(tr("macro_quick_text_btn"))

        # Retranslate Debug Tab
        if hasattr(self, "lbl_debug_code_title"):
            self.lbl_debug_code_title.setText(tr("debug_code_title"))
        if hasattr(self, "btn_refresh_code"):
            self.btn_refresh_code.setText(tr("debug_btn_refresh"))
        if hasattr(self, "btn_copy_code"):
            self.btn_copy_code.setText(tr("debug_btn_copy"))
        if hasattr(self, "btn_export_code"):
            self.btn_export_code.setText(tr("debug_btn_export"))
        if hasattr(self, "lbl_debug_log_title"):
            self.lbl_debug_log_title.setText(tr("debug_log_title"))
        if hasattr(self, "btn_clear_log"):
            self.btn_clear_log.setText(tr("debug_btn_clear_log"))
        if hasattr(self, "btn_check_bridge"):
            self.btn_check_bridge.setText(tr("debug_bridge_status"))

        # Refresh components & trays
        self.refresh_device()
        self.load_effects()
        self.refresh_remap_ui()
        self.refresh_macro_list_ui()
        self.init_system_tray()

    def build_keyboard_grid(self, grid_layout: QGridLayout, buttons_dict: Dict[str, KeyVisualButton],
                            click_handler, space_mode: str = "split", mode: str = "rgb"):
        """Populate the grid layout with styled visual keys matching physical 104-key GK104 Pro layout."""
        # Clear existing buttons
        while grid_layout.count():
            item = grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        buttons_dict.clear()

        # Build Rows 0 to 4 (F-Row, Numbers, QWERTY, ASDF, ZXCV)
        for k in KEY_DEFINITIONS:
            if k["row"] < 5:
                w_u = k.get("width", 1.0)
                h_u = k.get("height", 1.0)
                btn = KeyVisualButton(
                    key_id=k["id"],
                    label=k["label"],
                    group=k["group"],
                    width_u=w_u,
                    height_u=h_u,
                    knob_id=k.get("knob_id"),
                    knob_name=k.get("knob_name"),
                    mode=mode
                )
                btn.row = k["row"]
                btn.col = k["col"]
                btn.key_clicked.connect(click_handler)
                row = k["row"]
                col_pos = int(round(k["col"] * 8))
                col_span = int(round(w_u * 8))
                row_span = int(round(h_u))
                grid_layout.addWidget(btn, row, col_pos, row_span, col_span)
                buttons_dict[k["id"]] = btn

        # Build Row 5 (Bottom Row with Spacebar module)
        bottom_keys = [
            {"id": "LCtrl", "label": "Ctrl", "group": "mod", "col": 0.0, "width": 1.25},
            {"id": "LWin", "label": "Win", "group": "mod", "col": 1.25, "width": 1.25},
            {"id": "LAlt", "label": "Alt", "group": "mod", "col": 2.5, "width": 1.25},
        ]

        if space_mode == "split":
            bottom_keys.extend([
                {"id": "LeftSpace", "label": "Space L", "group": "mod", "col": 3.75, "width": 2.25},
                {"id": "StandardSpace", "label": "Space M", "group": "mod", "col": 6.0, "width": 2.75},
                {"id": "RightSpace", "label": "Space R", "group": "mod", "col": 8.75, "width": 1.25}
            ])
        else:
            bottom_keys.append(
                {"id": "Space_18", "label": "Space", "group": "mod", "col": 3.75, "width": 6.25}
            )

        bottom_keys.extend([
            {"id": "RAlt", "label": "Alt", "group": "mod", "col": 10.0, "width": 1.25},
            {"id": "Menu", "label": "Fn/Menu", "group": "mod", "col": 11.25, "width": 1.25},
            {"id": "RCtrl", "label": "Ctrl", "group": "mod", "col": 12.5, "width": 1.25},
            {"id": "Left", "label": "◄", "group": "arrows", "col": 15.5, "width": 1.0},
            {"id": "Down", "label": "▼", "group": "arrows", "col": 16.5, "width": 1.0},
            {"id": "Right", "label": "►", "group": "arrows", "col": 17.5, "width": 1.0},
            {"id": "NumPad0", "label": "0", "group": "numpad", "col": 19.0, "width": 2.0},
            {"id": "NumPadPeriod", "label": ".", "group": "numpad", "col": 21.0, "width": 1.0}
        ])

        for k in bottom_keys:
            w_u = k.get("width", 1.0)
            h_u = k.get("height", 1.0)
            btn = KeyVisualButton(
                key_id=k["id"],
                label=k["label"],
                group=k["group"],
                width_u=w_u,
                height_u=h_u,
                knob_id=k.get("knob_id"),
                knob_name=k.get("knob_name"),
                mode=mode
            )
            btn.row = 5
            btn.col = k["col"]
            btn.key_clicked.connect(click_handler)
            row = 5
            col_pos = int(round(k["col"] * 8))
            col_span = int(round(w_u * 8))
            grid_layout.addWidget(btn, row, col_pos, 1, col_span)
            buttons_dict[k["id"]] = btn

    # =========================================================================
    # TAB 1: RGB LIGHTING
    # =========================================================================
    def create_lighting_tab(self) -> QWidget:
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Top Control Bar for Lighting Tab
        top_ctrl_bar = QHBoxLayout()
        self.lbl_rgb_title = QLabel(tr("rgb_header_title", "104 Visual Keyboard • Live Animation Preview & Color Painter"))
        self.lbl_rgb_title.setStyleSheet("font-weight: bold; color: #7aa2f7; font-size: 13px;")
        top_ctrl_bar.addWidget(self.lbl_rgb_title)
        top_ctrl_bar.addStretch()

        # Live Animation Preview Controls
        self.btn_toggle_anim = QPushButton(tr("rgb_pause_anim", "⏸ Pause Preview"))
        self.btn_toggle_anim.setStyleSheet("background-color: #2b3b55; color: #7dcfff; font-weight: bold; padding: 4px 10px; min-height: 24px;")
        self.btn_toggle_anim.clicked.connect(self.toggle_live_animation)
        top_ctrl_bar.addWidget(self.btn_toggle_anim)

        self.lbl_rgb_speed = QLabel(tr("rgb_speed_label", "Speed:"))
        top_ctrl_bar.addWidget(self.lbl_rgb_speed)
        self.slider_anim_speed = QSlider(Qt.Horizontal)
        self.slider_anim_speed.setRange(2, 30)
        self.slider_anim_speed.setValue(10)
        self.slider_anim_speed.setFixedWidth(80)
        self.slider_anim_speed.valueChanged.connect(self.on_anim_speed_changed)
        top_ctrl_bar.addWidget(self.slider_anim_speed)

        top_ctrl_bar.addSpacing(12)

        # Spacebar mode selector in RGB tab
        self.lbl_rgb_space_mode = QLabel(tr("rgb_space_layout_label", "Spacebar Layout:"))
        top_ctrl_bar.addWidget(self.lbl_rgb_space_mode)
        self.rgb_radio_split_space = QRadioButton(tr("rgb_space_split", "Split (2.25+2.75+1.25)"))
        self.rgb_radio_single_space = QRadioButton(tr("rgb_space_standard", "Standard (6.25u)"))
        if self.space_mode == "split":
            self.rgb_radio_split_space.setChecked(True)
        else:
            self.rgb_radio_single_space.setChecked(True)
        self.rgb_radio_split_space.toggled.connect(self.on_space_mode_toggled)
        self.rgb_radio_single_space.toggled.connect(self.on_space_mode_toggled)
        top_ctrl_bar.addWidget(self.rgb_radio_split_space)
        top_ctrl_bar.addWidget(self.rgb_radio_single_space)
        top_ctrl_bar.addSpacing(12)

        self.rgb_layer_combo = QComboBox()
        self.rgb_layer_combo.addItems(["Base", "Layer1", "Layer2", "Layer3"])
        self.rgb_layer_combo.currentIndexChanged.connect(self.on_rgb_layer_changed)
        self.lbl_rgb_target_layer = QLabel(tr("rgb_target_layer", "Target LED Layer:"))
        top_ctrl_bar.addWidget(self.lbl_rgb_target_layer)
        top_ctrl_bar.addWidget(self.rgb_layer_combo)
        layout.addLayout(top_ctrl_bar)

        # Authentic GK104 Pro Chassis with Smart Screen Mockup & Sunken Switch Plate
        self.rgb_chassis = GK104ChassisWidget()
        self.rgb_grid_layout = self.rgb_chassis.plate_layout

        self.build_keyboard_grid(
            self.rgb_grid_layout,
            self.rgb_key_buttons,
            self.on_rgb_key_clicked,
            self.space_mode,
            mode="rgb"
        )

        layout.addWidget(self.rgb_chassis)

        # Bottom Controls: Left (Effects library) | Right (Palette & Tools)
        splitter = QSplitter(Qt.Horizontal)

        # Left: Animated library
        left_card = QFrame()
        left_card.setObjectName("cardFrame")
        left_card.setMinimumSize(420, 320)
        left_vbox = QVBoxLayout(left_card)
        left_vbox.setContentsMargins(8, 8, 8, 8)

        self.lbl_effects_lib = QLabel(tr("rgb_effects_library", "🌈 Built-In Animation Effects Library"))
        self.lbl_effects_lib.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        left_vbox.addWidget(self.lbl_effects_lib)

        # Search bar & category filter
        filter_bar = QHBoxLayout()
        self.effect_search_input = QLineEdit()
        self.effect_search_input.setPlaceholderText(tr("rgb_search_placeholder", "Search effect (e.g. Rainbow, Wave, Breath, Matrix)..."))
        self.effect_search_input.textChanged.connect(self.filter_effects)
        filter_bar.addWidget(self.effect_search_input)

        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self.filter_effects)
        filter_bar.addWidget(self.category_combo)
        left_vbox.addLayout(filter_bar)

        self.effects_list_widget = QListWidget()
        self.effects_list_widget.currentItemChanged.connect(self.on_effect_list_item_changed)
        self.effects_list_widget.itemDoubleClicked.connect(self.on_effect_double_clicked)
        left_vbox.addWidget(self.effects_list_widget)

        self.btn_apply_effect = QPushButton(tr("rgb_apply_effect_btn", "⚡ Apply Effect to Keyboard"))
        self.btn_apply_effect.setObjectName("primaryBtn")
        self.btn_apply_effect.clicked.connect(self.apply_selected_effect)
        left_vbox.addWidget(self.btn_apply_effect)
        splitter.addWidget(left_card)

        # Right: Palette, Presets & Zones
        right_card = QFrame()
        right_card.setObjectName("cardFrame")
        right_card.setMinimumSize(460, 320)
        right_vbox = QVBoxLayout(right_card)
        right_vbox.setContentsMargins(8, 8, 8, 8)

        self.lbl_rgb_tools_title = QLabel(tr("rgb_tools_title", "🎨 Colors & Painting Tools"))
        self.lbl_rgb_tools_title.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        right_vbox.addWidget(self.lbl_rgb_tools_title)

        # Color picker row
        brush_row = QHBoxLayout()
        self.lbl_rgb_current_brush = QLabel(tr("rgb_current_brush", "Current brush:"))
        brush_row.addWidget(self.lbl_rgb_current_brush)
        self.brush_preview_btn = QPushButton()
        self.brush_preview_btn.setFixedSize(36, 26)
        self.brush_preview_btn.setStyleSheet(f"background-color: {self.selected_brush_color}; border-radius: 4px;")
        self.brush_preview_btn.clicked.connect(self.open_color_dialog)
        brush_row.addWidget(self.brush_preview_btn)

        self.btn_pick_color = QPushButton(tr("rgb_pick_color_btn", "Pick custom color..."))
        self.btn_pick_color.clicked.connect(self.open_color_dialog)
        brush_row.addWidget(self.btn_pick_color)
        brush_row.addStretch()
        right_vbox.addLayout(brush_row)

        # Quick palette
        pal_box = QHBoxLayout()
        quick_colors = [
            "#ff0000", "#00ff00", "#0000ff", "#ffff00",
            "#00ffff", "#ff00ff", "#ff8800", "#ffffff", "#000000"
        ]
        for hex_col in quick_colors:
            q_btn = QPushButton()
            q_btn.setFixedSize(28, 24)
            q_btn.setStyleSheet(f"background-color: {hex_col}; border: 1px solid #3b4261; border-radius: 4px;")
            q_btn.clicked.connect(lambda _, c=hex_col: self.set_brush_color(c))
            pal_box.addWidget(q_btn)
        pal_box.addStretch()
        right_vbox.addLayout(pal_box)

        # Zone painting
        self.zone_group = QGroupBox(tr("rgb_zone_painting", "Zone Painting"))
        zone_layout = QGridLayout(self.zone_group)
        zones = [
            (tr("rgb_zone_wasd", "WASD"), "wasd"),
            (tr("rgb_zone_arrows", "Arrows"), "arrows"),
            (tr("rgb_zone_numpad", "NumPad"), "numpad"),
            (tr("rgb_zone_func", "F1-F12"), "func"),
            (tr("rgb_zone_alpha", "Letters"), "alpha"),
            (tr("rgb_zone_all", "Whole Board"), "all")
        ]
        for idx, (z_name, z_id) in enumerate(zones):
            z_btn = QPushButton(f"{tr('rgb_zone_btn_prefix', 'Paint: ')}{z_name}")
            z_btn.clicked.connect(lambda _, zid=z_id: self.paint_zone(zid))
            zone_layout.addWidget(z_btn, idx // 3, idx % 3)
        right_vbox.addWidget(self.zone_group)

        # Styled Themes
        self.theme_group = QGroupBox(tr("rgb_color_themes", "Preset Color Schemes"))
        theme_layout = QGridLayout(self.theme_group)
        for idx, t_name in enumerate(COLOR_PRESETS.keys()):
            t_btn = QPushButton(t_name)
            t_btn.clicked.connect(lambda _, tn=t_name: self.apply_preset_theme(tn))
            theme_layout.addWidget(t_btn, idx // 2, idx % 2)
        right_vbox.addWidget(self.theme_group)

        # Brightness Control Group
        self.bright_group = QGroupBox(tr("rgb_brightness_title", "Keyboard Backlight Brightness"))
        bright_layout = QHBoxLayout(self.bright_group)
        self.lbl_brightness_val = QLabel(tr("rgb_brightness_label", val=int(self.backend.lighting_config.get('brightness', 100))))
        self.lbl_brightness_val.setFixedWidth(120)
        self.lbl_brightness_val.setStyleSheet("font-weight: bold; color: #ff9eaf;")
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(int(self.backend.lighting_config.get("brightness", 100)))
        self.brightness_slider.valueChanged.connect(self.on_brightness_slider_changed)
        bright_layout.addWidget(self.lbl_brightness_val)
        bright_layout.addWidget(self.brightness_slider)

        for b_val in [25, 50, 75, 100]:
            btn_b = QPushButton(f"{b_val}%")
            btn_b.setFixedWidth(44)
            btn_b.clicked.connect(lambda _, v=b_val: self.set_brightness_level(v))
            bright_layout.addWidget(btn_b)

        self.btn_apply_bright = QPushButton(tr("rgb_btn_apply_bright", "⚡ Apply"))
        self.btn_apply_bright.setObjectName("primaryBtn")
        self.btn_apply_bright.setFixedWidth(80)
        self.btn_apply_bright.clicked.connect(self.apply_brightness_now)
        bright_layout.addWidget(self.btn_apply_bright)

        right_vbox.addWidget(self.bright_group)

        # Tools: LED Off / Apply static
        tools_row = QHBoxLayout()
        self.btn_led_off = QPushButton(tr("rgb_btn_led_off", "🌙 Turn off LED"))
        self.btn_led_off.setObjectName("dangerBtn")
        self.btn_led_off.clicked.connect(self.turn_off_led)
        tools_row.addWidget(self.btn_led_off)

        self.btn_apply_static = QPushButton(tr("rgb_btn_apply_static", "✅ Apply Static Colors"))
        self.btn_apply_static.setObjectName("successBtn")
        self.btn_apply_static.clicked.connect(self.apply_static_keyboard_colors)
        tools_row.addWidget(self.btn_apply_static)
        right_vbox.addLayout(tools_row)

        splitter.addWidget(right_card)
        splitter.setSizes([450, 550])
        layout.addWidget(splitter)

        scroll_area.setWidget(container)
        return scroll_area

    # =========================================================================
    # TAB 2: KEY REMAPPING & ROTARY KNOBS
    # =========================================================================
    def create_remap_tab(self) -> QWidget:
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # Layer Selector & Header
        top_bar = QHBoxLayout()
        self.lbl_remap_layer = QLabel(tr("remap_active_layer", "Active Layer:"))
        self.lbl_remap_layer.setStyleSheet("font-weight: bold; color: #7aa2f7; font-size: 14px;")
        top_bar.addWidget(self.lbl_remap_layer)

        self.remap_layer_combo = QComboBox()
        for layer_id, layer_name in get_available_layers():
            self.remap_layer_combo.addItem(layer_name, layer_id)
        self.remap_layer_combo.setCurrentIndex(1)  # Layer1 default
        self.remap_layer_combo.currentIndexChanged.connect(self.on_remap_layer_changed)
        top_bar.addWidget(self.remap_layer_combo)

        top_bar.addSpacing(20)
        # Spacebar mode selector in Remap tab
        self.lbl_remap_space_mode = QLabel(tr("remap_space_mode", "Spacebar Module:"))
        top_bar.addWidget(self.lbl_remap_space_mode)
        self.remap_radio_split_space = QRadioButton(tr("remap_space_split", "Split (2.25+2.75+1.25)"))
        self.remap_radio_single_space = QRadioButton(tr("remap_space_standard", "Standard (6.25u)"))
        if self.space_mode == "split":
            self.remap_radio_split_space.setChecked(True)
        else:
            self.remap_radio_single_space.setChecked(True)
        self.remap_radio_split_space.toggled.connect(self.on_space_mode_toggled)
        self.remap_radio_single_space.toggled.connect(self.on_space_mode_toggled)
        top_bar.addWidget(self.remap_radio_split_space)
        top_bar.addWidget(self.remap_radio_single_space)

        top_bar.addStretch()

        self.btn_clear_layer_top = QPushButton(tr("remap_btn_clear_layer", "🗑️ Clear All Layer Remaps"))
        self.btn_clear_layer_top.setStyleSheet("min-height: 24px; padding: 6px 12px;")
        self.btn_clear_layer_top.clicked.connect(self.clear_current_layer_remaps)
        top_bar.addWidget(self.btn_clear_layer_top)
        layout.addLayout(top_bar)

        # Interactive visual keyboard for remap with GK104 Pro Chassis
        remap_header = QHBoxLayout()
        self.remap_title_header = QLabel(tr("rgb_header_title", "104 Visual Keyboard • Click key or knob socket (🎛️) to assign function:"))
        self.remap_title_header.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        remap_header.addWidget(self.remap_title_header)
        remap_header.addStretch()

        self.legend_knob = QLabel(tr("remap_knobs_title", "🎛️ Knob Sockets (K1-K6)"))
        self.legend_knob.setStyleSheet("color: #ff9e3b; font-weight: bold; background-color: #2b2216; padding: 3px 8px; border-radius: 4px; border: 1px solid #ff9e3b;")
        remap_header.addWidget(self.legend_knob)
        layout.addLayout(remap_header)

        self.remap_chassis = GK104ChassisWidget()
        self.remap_grid_layout = self.remap_chassis.plate_layout

        self.build_keyboard_grid(
            self.remap_grid_layout,
            self.remap_key_buttons,
            self.on_remap_key_selected,
            self.space_mode,
            mode="remap"
        )

        layout.addWidget(self.remap_chassis)

        # Rotary Knobs Section (GK104 Pro Modular Knobs)
        knobs_card = QFrame()
        knobs_card.setObjectName("cardFrame")
        knobs_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        knobs_vbox = QVBoxLayout(knobs_card)
        knobs_vbox.setContentsMargins(10, 10, 10, 10)
        knobs_vbox.setSpacing(8)

        knobs_header = QHBoxLayout()
        self.knobs_title = QLabel(tr("remap_knobs_title", "🎛️ Modular Rotary Knobs (GK104 Pro Multi-Knob Control)"))
        self.knobs_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #7aa2f7;")
        knobs_header.addWidget(self.knobs_title)
        knobs_header.addStretch()

        self.btn_copy_knobs = QPushButton(tr("remap_btn_copy_knobs", "📋 Copy Knobs to All Layers"))
        self.btn_copy_knobs.setToolTip(tr("remap_btn_copy_knobs_tip", "Synchronize knob mappings across Base and Layers 1-3"))
        self.btn_copy_knobs.setStyleSheet("background-color: #2b3b55; color: #7aa2f7; font-weight: bold; padding: 6px 12px; min-height: 24px;")
        self.btn_copy_knobs.clicked.connect(self.copy_knobs_to_all_layers)
        knobs_header.addWidget(self.btn_copy_knobs)
        knobs_vbox.addLayout(knobs_header)

        knobs_grid = QGridLayout()
        knobs_grid.setSpacing(8)
        self.knob_preset_combos.clear()

        knobs_meta = get_knobs_metadata()
        knob_presets_dict = get_knob_presets()

        for idx, knob_info in enumerate(knobs_meta):
            k_card = QFrame()
            k_card.setObjectName("knobCard")
            k_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            k_card_vbox = QVBoxLayout(k_card)
            k_card_vbox.setContentsMargins(8, 8, 8, 8)
            k_card_vbox.setSpacing(5)

            # Top of card: Title & Preset selector
            k_title_row = QHBoxLayout()
            k_title = QLabel(f"{knob_info['icon']} {knob_info['name']}")
            k_title.setStyleSheet("font-weight: bold; color: #ff9eaf; font-size: 11px;")
            k_title_row.addWidget(k_title)
            k_title_row.addStretch()

            preset_combo = QComboBox()
            preset_combo.addItem(tr("remap_knob_presets_placeholder", "Preset..."), "")
            for p_name in knob_presets_dict.keys():
                preset_combo.addItem(p_name, p_name)
            preset_combo.currentIndexChanged.connect(
                lambda _, kid=knob_info["id"], cb=preset_combo: self.on_knob_preset_applied(kid, cb)
            )
            preset_combo.setMinimumWidth(135)
            preset_combo.setFixedHeight(26)
            k_title_row.addWidget(preset_combo)
            self.knob_preset_combos.append(preset_combo)
            k_card_vbox.addLayout(k_title_row)

            # Action buttons inside card (CW, CCW, Click)
            for act in knob_info["actions"]:
                act_id = act["id"]
                act_label = act["label"]
                btn_act = QPushButton(f"{act_label}: Default")
                btn_act.setProperty("class", "knobActionButton")
                btn_act.setCursor(Qt.PointingHandCursor)
                btn_act.setMinimumHeight(28)
                btn_act.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                btn_act.clicked.connect(lambda _, aid=act_id: self.on_remap_key_selected(aid))
                k_card_vbox.addWidget(btn_act)
                self.knob_action_buttons[act_id] = btn_act

            knobs_grid.addWidget(k_card, idx // 3, idx % 3)

        knobs_vbox.addLayout(knobs_grid)
        layout.addWidget(knobs_card)

        # Bottom section: Left (Action Inspector / Assigner) | Right (Layer Remap Table)
        splitter = QSplitter(Qt.Horizontal)

        # Action Assigner Frame
        assign_card = QFrame()
        assign_card.setObjectName("cardFrame")
        assign_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        assign_vbox = QVBoxLayout(assign_card)
        assign_vbox.setContentsMargins(10, 10, 10, 10)
        assign_vbox.setSpacing(6)

        # Header with selected element indicator & preview
        top_assign_header = QHBoxLayout()
        self.lbl_selected_remap_key = QLabel(tr("remap_selected_item", name="Left Space"))
        self.lbl_selected_remap_key.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff9eaf;")
        top_assign_header.addWidget(self.lbl_selected_remap_key)
        top_assign_header.addStretch()

        self.lbl_picked_action_info = QLabel(tr("remap_picked_action", action="(Select below)"))
        self.lbl_picked_action_info.setStyleSheet("font-size: 11px; font-weight: bold; color: #7dcfff; background-color: #141724; padding: 3px 8px; border-radius: 4px; border: 1px solid #292d3e;")
        top_assign_header.addWidget(self.lbl_picked_action_info)
        assign_vbox.addLayout(top_assign_header)

        # Search bar for instant filtering of all actions
        search_row = QHBoxLayout()
        self.remap_action_search = QLineEdit()
        self.remap_action_search.setPlaceholderText(tr("remap_search_placeholder", "Search key or function (e.g. Volume, Backlight, Calculator, Enter)..."))
        self.remap_action_search.textChanged.connect(self.on_remap_search_changed)
        search_row.addWidget(self.remap_action_search)

        btn_clear_search = QPushButton("✕")
        btn_clear_search.setFixedWidth(28)
        btn_clear_search.clicked.connect(lambda: self.remap_action_search.clear())
        search_row.addWidget(btn_clear_search)
        assign_vbox.addLayout(search_row)

        # Tabbed categories
        self.remap_category_tabs = QTabWidget()
        self.category_action_buttons: Dict[str, List[QPushButton]] = {}
        self.current_picked_action: Optional[str] = None

        target_cats = get_target_key_categories()
        for cat_title, cat_items in target_cats.items():
            tab_page = QWidget()
            tab_layout = QVBoxLayout(tab_page)
            tab_layout.setContentsMargins(4, 6, 4, 4)
            tab_layout.setSpacing(4)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setStyleSheet("background: transparent; border: none;")

            grid_widget = QWidget()
            grid_widget.setStyleSheet("background: transparent;")
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(4)
            grid_layout.setContentsMargins(2, 2, 2, 2)

            self.category_action_buttons[cat_title] = []

            # Number of columns based on category
            cols = 4 if "Primary" in cat_title else 3

            for idx, (action_code, action_label) in enumerate(cat_items):
                btn = QPushButton(action_label)
                btn.setProperty("action_code", action_code)
                btn.setProperty("action_label", action_label)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                btn.setMinimumHeight(28)
                btn.clicked.connect(lambda _, c=action_code, l=action_label, b=btn: self.on_action_picked(c, l, b))
                grid_layout.addWidget(btn, idx // cols, idx % cols)
                self.category_action_buttons[cat_title].append(btn)

            scroll.setWidget(grid_widget)
            tab_layout.addWidget(scroll)
            self.remap_category_tabs.addTab(tab_page, cat_title)

        # Custom Modifier Combination Tab
        tab_combo = QWidget()
        combo_layout = QVBoxLayout(tab_combo)
        combo_layout.setContentsMargins(8, 8, 8, 8)
        combo_layout.setSpacing(8)

        mods_box = QHBoxLayout()
        mods_box.addWidget(QLabel(tr("remap_combos_modifiers", "Modifiers:")))
        self.chk_ctrl = QCheckBox("Ctrl (LCtrl)")
        self.chk_shift = QCheckBox("Shift (LShift)")
        self.chk_alt = QCheckBox("Alt (LAlt)")
        self.chk_win = QCheckBox("Win (Super)")
        for chk in [self.chk_ctrl, self.chk_shift, self.chk_alt, self.chk_win]:
            chk.stateChanged.connect(self.update_combination_preview)
            mods_box.addWidget(chk)
        mods_box.addStretch()
        combo_layout.addLayout(mods_box)

        base_key_row = QHBoxLayout()
        base_key_row.addWidget(QLabel(tr("remap_combos_base_key", "Base Key:")))
        self.combo_base_key = QComboBox()
        for k in KEY_DEFINITIONS:
            self.combo_base_key.addItem(f"{k['label']} [{k['id']}]", k["id"])
        self.combo_base_key.currentIndexChanged.connect(self.update_combination_preview)
        base_key_row.addWidget(self.combo_base_key)

        base_key_row.addSpacing(14)
        base_key_row.addWidget(QLabel(tr("remap_combos_popular", "Popular Shortcuts:")))
        self.popular_shortcuts_combo = QComboBox()
        self.popular_shortcuts_combo.addItem(tr("remap_knob_presets_placeholder", "Choose shortcut..."), "")
        for short_name, short_code, short_desc in get_popular_shortcuts():
            self.popular_shortcuts_combo.addItem(f"{short_desc} ({short_name})", short_code)
        self.popular_shortcuts_combo.currentIndexChanged.connect(self.on_popular_shortcut_selected)
        base_key_row.addWidget(self.popular_shortcuts_combo)
        base_key_row.addStretch()
        combo_layout.addLayout(base_key_row)

        combo_layout.addStretch()
        self.remap_category_tabs.addTab(tab_combo, tr("remap_cat_combos", "⚡ Combinations"))

        # Macro Tab in Remap Inspector
        tab_macro_remap = QWidget()
        mremap_layout = QVBoxLayout(tab_macro_remap)
        mremap_layout.setContentsMargins(8, 8, 8, 8)
        mremap_layout.setSpacing(8)

        mremap_row = QHBoxLayout()
        mremap_row.addWidget(QLabel(tr("remap_macro_choose", "Choose Recorded Macro:")))
        self.remap_macro_combo = QComboBox()
        self.remap_macro_combo.currentIndexChanged.connect(self.on_macro_combo_changed)
        mremap_row.addWidget(self.remap_macro_combo)
        mremap_row.addStretch()
        mremap_layout.addLayout(mremap_row)

        self.lbl_macro_details = QLabel("")
        self.lbl_macro_details.setStyleSheet("color: #7dcfff; font-size: 11px;")
        mremap_layout.addWidget(self.lbl_macro_details)
        mremap_layout.addStretch()
        self.remap_category_tabs.addTab(tab_macro_remap, tr("remap_cat_macros", "📜 Macros"))

        assign_vbox.addWidget(self.remap_category_tabs)

        # Action Execution Buttons
        btn_action_box = QHBoxLayout()
        self.btn_assign_action = QPushButton(tr("remap_btn_assign", "⚡ Assign Function to Key / Knob"))
        self.btn_assign_action.setObjectName("primaryBtn")
        self.btn_assign_action.setStyleSheet("padding: 8px 16px; font-size: 12px; font-weight: bold;")
        self.btn_assign_action.clicked.connect(self.assign_selected_remap_action)
        btn_action_box.addWidget(self.btn_assign_action)

        self.btn_reset_single_key = QPushButton(tr("remap_btn_reset_key", "↩️ Reset Key to Default"))
        self.btn_reset_single_key.setStyleSheet("padding: 8px 14px; font-weight: bold;")
        self.btn_reset_single_key.clicked.connect(self.reset_selected_key_remap)
        btn_action_box.addWidget(self.btn_reset_single_key)
        assign_vbox.addLayout(btn_action_box)

        splitter.addWidget(assign_card)

        # Right Card: Remap Summary Table for Active Layer
        table_card = QFrame()
        table_card.setObjectName("cardFrame")
        table_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        table_vbox = QVBoxLayout(table_card)
        table_vbox.setContentsMargins(10, 10, 10, 10)
        table_vbox.setSpacing(6)

        table_header = QHBoxLayout()
        self.lbl_remap_table_title = QLabel(tr("remap_table_title", layer="Layer1"))
        self.lbl_remap_table_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #7aa2f7;")
        table_header.addWidget(self.lbl_remap_table_title)
        table_header.addStretch()

        self.btn_clear_layer_bottom = QPushButton(tr("remap_btn_clear_layer", "🗑️ Clear Layer"))
        self.btn_clear_layer_bottom.setObjectName("dangerBtn")
        self.btn_clear_layer_bottom.setStyleSheet("min-height: 22px; padding: 4px 8px; font-size: 11px;")
        self.btn_clear_layer_bottom.clicked.connect(self.clear_current_layer_remaps)
        table_header.addWidget(self.btn_clear_layer_bottom)
        table_vbox.addLayout(table_header)

        self.remap_table = QTableWidget()
        self.remap_table.setColumnCount(4)
        self.remap_table.setHorizontalHeaderLabels([
            tr("remap_col_key", "Key / Knob"),
            tr("remap_col_action", "Assigned Function"),
            tr("remap_col_code", "Hardware Code"),
            tr("remap_col_delete", "Action")
        ])
        self.remap_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.remap_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.remap_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.remap_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.remap_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.remap_table.setSelectionMode(QTableWidget.SingleSelection)
        table_vbox.addWidget(self.remap_table)

        splitter.addWidget(table_card)
        splitter.setSizes([620, 380])
        layout.addWidget(splitter)

        scroll_area.setWidget(container)
        return scroll_area

    # =========================================================================
    # TAB 3: MACRO STUDIO
    # =========================================================================
    def create_macro_tab(self) -> QWidget:
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        splitter = QSplitter(Qt.Horizontal)

        # Left Column: Macro list & management
        left_card = QFrame()
        left_card.setObjectName("cardFrame")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(8)

        self.macro_lib_group = QGroupBox(tr("macro_library_title", "📜 Macro Library"))
        lib_box = QVBoxLayout(self.macro_lib_group)
        self.macro_list_widget = QListWidget()
        self.macro_list_widget.currentItemChanged.connect(self.on_macro_selected)
        lib_box.addWidget(self.macro_list_widget)

        btn_row = QHBoxLayout()
        self.btn_new_macro = QPushButton(tr("macro_btn_new", "➕ New Macro"))
        self.btn_new_macro.setObjectName("primaryBtn")
        self.btn_new_macro.clicked.connect(self.create_new_macro)
        btn_row.addWidget(self.btn_new_macro)

        self.btn_del_macro = QPushButton(tr("macro_btn_delete", "🗑️ Delete"))
        self.btn_del_macro.setObjectName("dangerBtn")
        self.btn_del_macro.clicked.connect(self.delete_current_macro)
        btn_row.addWidget(self.btn_del_macro)

        self.btn_dup_macro = QPushButton(tr("macro_btn_dup", "📋 Duplicate"))
        self.btn_dup_macro.clicked.connect(self.duplicate_current_macro)
        btn_row.addWidget(self.btn_dup_macro)

        self.btn_rename_macro = QPushButton(tr("macro_btn_rename", "✏️ Rename"))
        self.btn_rename_macro.clicked.connect(self.rename_current_macro)
        btn_row.addWidget(self.btn_rename_macro)

        lib_box.addLayout(btn_row)
        left_layout.addWidget(self.macro_lib_group)
        splitter.addWidget(left_card)

        # Right Column: Macro Editor
        right_card = QFrame()
        right_card.setObjectName("cardFrame")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(8)

        self.macro_editor_group = QGroupBox(tr("macro_editor_title", "⚡ Macro Sequence Editor"))
        editor_box = QVBoxLayout(self.macro_editor_group)

        # Macro Properties Bar
        prop_row = QHBoxLayout()
        self.lbl_macro_name = QLabel(tr("macro_name_label", "Macro Name:"))
        prop_row.addWidget(self.lbl_macro_name)
        self.macro_name_input = QLineEdit()
        self.macro_name_input.textChanged.connect(self.on_macro_properties_changed)
        prop_row.addWidget(self.macro_name_input)

        self.lbl_macro_repeat = QLabel(tr("macro_repeat_label", "Repeat Mode:"))
        prop_row.addWidget(self.lbl_macro_repeat)
        self.macro_repeat_combo = QComboBox()
        self.macro_repeat_combo.addItem(tr("macro_mode_times", "Repeat X Times"), "RepeatXTimes")
        self.macro_repeat_combo.addItem(tr("macro_mode_hold", "Hold Key to Repeat"), "ReleaseKeyToStop")
        self.macro_repeat_combo.addItem(tr("macro_mode_toggle", "Toggle On/Off on Press"), "PressKeyAgainToStop")
        self.macro_repeat_combo.currentIndexChanged.connect(self.on_macro_properties_changed)
        prop_row.addWidget(self.macro_repeat_combo)

        self.lbl_macro_repeat_count = QLabel(tr("macro_repeat_count", "Repeats:"))
        prop_row.addWidget(self.lbl_macro_repeat_count)
        self.macro_repeat_count_spin = QSpinBox()
        self.macro_repeat_count_spin.setRange(1, 9999)
        self.macro_repeat_count_spin.setValue(1)
        self.macro_repeat_count_spin.valueChanged.connect(self.on_macro_properties_changed)
        prop_row.addWidget(self.macro_repeat_count_spin)

        editor_box.addLayout(prop_row)

        # Macro Steps Table
        self.macro_actions_table = QTableWidget()
        self.macro_actions_table.setColumnCount(4)
        self.macro_actions_table.setHorizontalHeaderLabels([
            tr("macro_table_col_event", "Event"),
            tr("macro_table_col_key", "Target Key"),
            tr("macro_table_col_delay", "Delay (ms)"),
            "Action"
        ])
        self.macro_actions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.macro_actions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.macro_actions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.macro_actions_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        editor_box.addWidget(self.macro_actions_table)

        # Step adder row
        step_add_row = QHBoxLayout()
        self.action_type_combo = QComboBox()
        self.action_type_combo.addItems(["Press (Down + Up)", "Down (Keydown)", "Up (Keyup)"])
        step_add_row.addWidget(self.action_type_combo)

        self.action_key_combo = QComboBox()
        for k in KEY_DEFINITIONS:
            self.action_key_combo.addItem(f"{k['label']} [{k['id']}]", k["id"])
        step_add_row.addWidget(self.action_key_combo)

        step_add_row.addWidget(QLabel("Delay (ms):"))
        self.action_delay_spin = QSpinBox()
        self.action_delay_spin.setRange(1, 10000)
        self.action_delay_spin.setValue(20)
        step_add_row.addWidget(self.action_delay_spin)

        self.btn_add_macro_step = QPushButton(tr("macro_btn_add_step", "➕ Add Step"))
        self.btn_add_macro_step.setObjectName("primaryBtn")
        self.btn_add_macro_step.clicked.connect(self.add_macro_step)
        step_add_row.addWidget(self.btn_add_macro_step)

        self.btn_clear_macro_steps = QPushButton(tr("macro_btn_clear_steps", "🧹 Clear All Steps"))
        self.btn_clear_macro_steps.clicked.connect(self.clear_all_macro_steps)
        step_add_row.addWidget(self.btn_clear_macro_steps)

        editor_box.addLayout(step_add_row)
        right_layout.addWidget(self.macro_editor_group)

        # Quick Text / Command to Macro Generator
        self.text_macro_group = QGroupBox(tr("macro_quick_text_title", "⚡ Quick Text / Command to Macro Generator"))
        text_box = QVBoxLayout(self.text_macro_group)

        self.lbl_quick_text_hint = QLabel(tr("macro_quick_text_label", "Enter text or shell command to convert (e.g. sudo pacman -Syu):"))
        self.lbl_quick_text_hint.setStyleSheet("font-size: 11px; color: #a9b1d6;")
        text_box.addWidget(self.lbl_quick_text_hint)

        text_row = QHBoxLayout()
        self.quick_text_input = QLineEdit()
        self.quick_text_input.setPlaceholderText("sudo pacman -Syu")
        text_row.addWidget(self.quick_text_input)

        self.lbl_quick_text_speed = QLabel(tr("macro_quick_text_speed", "Speed (ms/key):"))
        text_row.addWidget(self.lbl_quick_text_speed)
        self.quick_text_delay_spin = QSpinBox()
        self.quick_text_delay_spin.setRange(5, 500)
        self.quick_text_delay_spin.setValue(25)
        text_row.addWidget(self.quick_text_delay_spin)

        self.btn_generate_text_macro = QPushButton(tr("macro_quick_text_btn", "🚀 Generate Key Sequence"))
        self.btn_generate_text_macro.setObjectName("primaryBtn")
        self.btn_generate_text_macro.clicked.connect(self.generate_macro_from_text)
        text_row.addWidget(self.btn_generate_text_macro)
        text_box.addLayout(text_row)

        right_layout.addWidget(self.text_macro_group)

        splitter.addWidget(right_card)
        splitter.setSizes([350, 650])
        layout.addWidget(splitter)

        scroll_area.setWidget(container)
        return scroll_area

    # =========================================================================
    # TAB 4: CODE PREVIEW & DIAGNOSTICS
    # =========================================================================
    def create_debug_tab(self) -> QWidget:
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Code preview box
        code_card = QFrame()
        code_card.setObjectName("cardFrame")
        code_layout = QVBoxLayout(code_card)

        code_header = QHBoxLayout()
        self.lbl_debug_code_title = QLabel(tr("debug_code_title", "Generated GK6X UserData Configuration Code"))
        self.lbl_debug_code_title.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        code_header.addWidget(self.lbl_debug_code_title)
        code_header.addStretch()

        self.btn_refresh_code = QPushButton(tr("debug_btn_refresh", "🔄 Refresh Code"))
        self.btn_refresh_code.clicked.connect(self.refresh_debug_code_view)
        code_header.addWidget(self.btn_refresh_code)

        self.btn_copy_code = QPushButton(tr("debug_btn_copy", "📋 Copy to Clipboard"))
        self.btn_copy_code.clicked.connect(self.copy_debug_code_to_clipboard)
        code_header.addWidget(self.btn_copy_code)

        self.btn_export_code = QPushButton(tr("debug_btn_export", "💾 Export to .txt"))
        self.btn_export_code.clicked.connect(self.export_raw_config_dialog)
        code_header.addWidget(self.btn_export_code)
        code_layout.addLayout(code_header)

        self.debug_code_edit = QPlainTextEdit()
        self.debug_code_edit.setReadOnly(True)
        self.debug_code_edit.setStyleSheet("font-family: monospace; font-size: 11px; background-color: #13141c; color: #9ece6a; border: 1px solid #24283b; border-radius: 6px;")
        code_layout.addWidget(self.debug_code_edit)
        layout.addWidget(code_card)

        # Execution log box
        log_card = QFrame()
        log_card.setObjectName("cardFrame")
        log_layout = QVBoxLayout(log_card)

        log_header = QHBoxLayout()
        self.lbl_debug_log_title = QLabel(tr("debug_log_title", "Backend Execution & Communication Log"))
        self.lbl_debug_log_title.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        log_header.addWidget(self.lbl_debug_log_title)
        log_header.addStretch()

        self.btn_clear_log = QPushButton(tr("debug_btn_clear_log", "🧹 Clear Log"))
        self.btn_clear_log.clicked.connect(lambda: self.debug_log_edit.clear())
        log_header.addWidget(self.btn_clear_log)

        self.btn_check_bridge = QPushButton(tr("debug_bridge_status", "⚙️ Hardware Bridge Status"))
        self.btn_check_bridge.clicked.connect(self.open_components_dialog)
        log_header.addWidget(self.btn_check_bridge)
        log_layout.addLayout(log_header)

        self.debug_log_edit = QTextEdit()
        self.debug_log_edit.setReadOnly(True)
        self.debug_log_edit.setStyleSheet("font-family: monospace; font-size: 11px; background-color: #13141c; color: #c0caf5; border: 1px solid #24283b; border-radius: 6px;")
        log_layout.addWidget(self.debug_log_edit)
        layout.addWidget(log_card)

        scroll_area.setWidget(container)
        return scroll_area

    # =========================================================================
    # SYSTEM TRAY & POWER MONITOR
    # =========================================================================
    def init_system_tray(self):
        if not hasattr(self, "tray_icon") or self.tray_icon is None:
            self.tray_icon = QSystemTrayIcon(self)
            pix = QPixmap(32, 32)
            pix.fill(Qt.transparent)
            painter = QPainter(pix)
            painter.setBrush(QBrush(QColor("#7aa2f7")))
            painter.setPen(QPen(QColor("#1a1b26"), 2))
            painter.drawRoundedRect(2, 2, 28, 28, 6, 6)
            painter.setPen(QPen(QColor("#15161e"), 2))
            painter.drawText(pix.rect(), Qt.AlignCenter, "GK")
            painter.end()
            self.tray_icon.setIcon(QIcon(pix))
            self.tray_icon.setToolTip(tr("app_window_title", "Skyloong GK104 Pro Studio"))

        tray_menu = QMenu()
        tray_menu.setStyleSheet("background-color: #1f2335; color: #c0caf5; border: 1px solid #414868; padding: 4px;")

        title_act = tray_menu.addAction("⌨️ Skyloong GK104 Pro Studio")
        title_act.setEnabled(False)
        tray_menu.addSeparator()

        show_act = tray_menu.addAction(tr("tray_show", "🖥️ Show Window"))
        show_act.triggered.connect(self.showNormal)

        hide_act = tray_menu.addAction(tr("tray_hide", "⬇️ Minimize to Tray"))
        hide_act.triggered.connect(self.hide)

        tray_menu.addSeparator()

        # Brightness Submenu
        bright_menu = tray_menu.addMenu(tr("tray_brightness", "💡 Backlight Brightness"))
        for b in [100, 75, 50, 25, 0]:
            lbl = f"{b}%" if b > 0 else "Off (0%)"
            act_b = bright_menu.addAction(lbl)
            act_b.triggered.connect(lambda _, val=b: self.set_brightness_level(val))

        # Color Presets Submenu
        preset_menu = tray_menu.addMenu(tr("tray_effects", "🌈 Lighting Presets"))
        for pname in COLOR_PRESETS.keys():
            act_p = preset_menu.addAction(pname)
            act_p.triggered.connect(lambda _, pn=pname: self.apply_preset_theme(pn))

        # Layer Switcher Submenu
        layer_menu = tray_menu.addMenu(tr("tray_layers", "🔀 Active Layer"))
        for lid, lname in get_available_layers():
            act_l = layer_menu.addAction(lname)
            act_l.triggered.connect(lambda _, l=lid: self.switch_remap_layer(l))

        # Language Switcher Submenu
        lang_sub = tray_menu.addMenu(tr("tray_lang", "🌐 Language"))
        for lcode, lname in get_available_languages():
            act_lang = lang_sub.addAction(lname)
            act_lang.triggered.connect(lambda _, c=lcode: self.switch_language_direct(c))

        tray_menu.addSeparator()

        flash_act = tray_menu.addAction(tr("tray_apply", "⚡ Flash to Keyboard"))
        flash_act.triggered.connect(self.apply_full_configuration)

        tray_menu.addSeparator()

        # Battery / Power status in tray
        p_info = get_system_battery_info()
        p_status = p_info.get("status_string", "Power: AC")
        power_act = tray_menu.addAction(f"⚡ {p_status}")
        power_act.setEnabled(False)

        tray_menu.addSeparator()

        quit_act = tray_menu.addAction(tr("tray_quit", "❌ Quit"))
        quit_act.triggered.connect(QApplication.instance().quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def switch_language_direct(self, lang_code: str):
        set_current_language(lang_code)
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == lang_code:
                self.lang_combo.blockSignals(True)
                self.lang_combo.setCurrentIndex(i)
                self.lang_combo.blockSignals(False)
                break
        self.retranslate_ui()

    def connect_signals(self):
        self.backend.apply_finished.connect(self.on_apply_finished)
        self.backend.unmap_finished.connect(self.on_unmap_finished)
        self.backend.log_message.connect(self.on_backend_log)

    def check_startup_components(self):
        diag = SystemChecker.get_full_diagnostics()
        if not diag["all_ok"]:
            dlg = ComponentInstallerDialog(self, auto_prompt_install=True)
            dlg.exec()

    def open_components_dialog(self):
        dlg = ComponentInstallerDialog(self)
        dlg.exec()

    def open_profile_manager(self):
        dlg = ProfileManagerDialog(self.backend, main_window=self, parent=self)
        dlg.exec()

    def on_backend_log(self, msg: str):
        self.debug_log_edit.append(msg)

    def refresh_device(self):
        info = self.backend.get_device_status_info()
        if info["connected"]:
            self.device_status_lbl.setText(
                tr("device_connected", name=info["device_name"], vid=info["vid"], pid=info["pid"])
            )
            self.device_status_lbl.setStyleSheet("color: #9ece6a; font-weight: bold; font-size: 11px;")
        else:
            self.device_status_lbl.setText(tr("device_virtual", "Virtual Mode / No hardware detected"))
            self.device_status_lbl.setStyleSheet("color: #e0af68; font-weight: bold; font-size: 11px;")

        # Update Battery status
        bat_info = get_system_battery_info()
        if bat_info.get("has_battery") and bat_info.get("percentage") is not None:
            pct = bat_info["percentage"]
            st = bat_info.get("state", "Discharging")
            self.lbl_battery_header.setText(tr("battery_val", val=pct, status=st))
            self.lbl_battery_header.setStyleSheet("color: #7dcfff; font-size: 11px; font-weight: bold; background-color: #13141c; padding: 6px 10px; border-radius: 6px; border: 1px solid #24283b;")
        else:
            self.lbl_battery_header.setText(tr("battery_ac", "🔋 Power: AC Connected (100%)"))

    def reset_factory_mappings(self):
        reply = QMessageBox.question(
            self,
            tr("btn_reset", "Reset"),
            tr("msg_reset_confirm", "Are you sure you want to restore default factory mappings?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.progress_bar.setVisible(True)
            self.lbl_bottom_info.setText(tr("lbl_status_resetting", "Resetting keyboard mappings..."))
            self.backend.reset_keyboard_mapping()

    def apply_full_configuration(self):
        self.progress_bar.setVisible(True)
        self.btn_apply_all.setEnabled(False)
        self.lbl_bottom_info.setText(tr("lbl_status_flashing", "Flashing keyboard memory (Flash)..."))
        self.backend.apply_current_configuration()

    def on_apply_finished(self, success: bool, msg: str):
        self.progress_bar.setVisible(False)
        self.btn_apply_all.setEnabled(True)
        self.lbl_bottom_info.setText(msg)
        if success:
            QMessageBox.information(self, tr("msg_success", "Success"), tr("msg_flashed_success"))
        else:
            QMessageBox.warning(self, tr("msg_error", "Error"), tr("msg_flashed_error", err=msg))

    def on_unmap_finished(self, success: bool, msg: str):
        self.progress_bar.setVisible(False)
        self.lbl_bottom_info.setText(msg)
        self.refresh_remap_ui()
        if success:
            QMessageBox.information(self, tr("btn_reset", "Reset"), msg)
        else:
            QMessageBox.warning(self, tr("msg_error", "Error"), msg)

    def on_tab_changed(self, index: int):
        if index == 1:
            self.refresh_remap_ui()
        elif index == 2:
            self.refresh_macro_list_ui()
        elif index == 3:
            self.refresh_debug_code_view()

    # =========================================================================
    # RGB LOGIC
    # =========================================================================
    def load_effects(self):
        self.all_effects = self.backend.get_available_effects()
        categories = sorted(list(set(e["category"] for e in self.all_effects)))
        self.category_combo.clear()
        self.category_combo.addItem(tr("rgb_all_categories", "All Categories"))
        for cat in categories:
            self.category_combo.addItem(cat)
        self.filter_effects()

    def filter_effects(self):
        query = self.effect_search_input.text().lower()
        selected_cat = self.category_combo.currentText()
        all_cat_label = tr("rgb_all_categories", "All Categories")
        self.effects_list_widget.clear()

        for eff in self.all_effects:
            if selected_cat != all_cat_label and eff["category"] != selected_cat:
                continue
            if query and query not in eff["name"].lower():
                continue

            item = QListWidgetItem(f"[{eff['category']}]  {eff['name']}")
            item.setData(Qt.UserRole, eff["name"])
            self.effects_list_widget.addItem(item)

    def on_effect_list_item_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if current:
            effect_name = current.data(Qt.UserRole)
            if effect_name:
                self.live_anim.set_preset(effect_name)
                self.rgb_chassis.update_screen_info(
                    tr("smart_screen_title", "1.04″ SMART SCREEN"),
                    tr("smart_screen_effect", name=effect_name[:12].upper())
                )

    def toggle_live_animation(self):
        if self.live_anim.is_running:
            self.live_anim.stop()
            self.btn_toggle_anim.setText(tr("rgb_start_anim", "▶ Start Preview"))
            self.btn_toggle_anim.setStyleSheet("background-color: #1f3554; color: #7aa2f7; font-weight: bold; padding: 4px 10px;")
        else:
            self.live_anim.start()
            self.btn_toggle_anim.setText(tr("rgb_pause_anim", "⏸ Pause Preview"))
            self.btn_toggle_anim.setStyleSheet("background-color: #2b3b55; color: #7dcfff; font-weight: bold; padding: 4px 10px;")

    def on_anim_speed_changed(self, value: int):
        speed_factor = value / 10.0
        self.live_anim.set_speed(speed_factor)

    def on_effect_double_clicked(self, item: QListWidgetItem):
        self.apply_selected_effect()

    def apply_selected_effect(self):
        item = self.effects_list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, tr("msg_warning", "Warning"), "Please select an effect from the list!")
            return
        effect_name = item.data(Qt.UserRole)
        layer = self.rgb_layer_combo.currentText()
        self.live_anim.set_preset(effect_name)
        self.backend.lighting_config = {
            "mode": "preset",
            "preset_name": effect_name,
            "layer": layer,
            "brightness": int(self.brightness_slider.value()),
            "static_colors": self.current_key_colors
        }
        self.apply_full_configuration()

    def on_rgb_layer_changed(self):
        self.backend.lighting_config["layer"] = self.rgb_layer_combo.currentText()

    def open_color_dialog(self):
        col = QColorDialog.getColor(QColor(self.selected_brush_color), self, tr("rgb_color_dialog_title", "Choose Brush Color"))
        if col.isValid():
            self.set_brush_color(col.name())

    def set_brush_color(self, hex_color: str):
        self.selected_brush_color = hex_color
        self.brush_preview_btn.setStyleSheet(f"background-color: {hex_color}; border-radius: 4px;")

    def on_rgb_key_clicked(self, key_id: str):
        if key_id in self.rgb_key_buttons:
            self.current_key_colors[key_id] = self.selected_brush_color
            self.rgb_key_buttons[key_id].set_color(self.selected_brush_color)
            self.live_anim.set_static_mode(self.current_key_colors)

    def paint_zone(self, zone_id: str):
        keys_to_paint = []
        if zone_id == "wasd":
            keys_to_paint = ["W", "A", "S", "D"]
        elif zone_id == "arrows":
            keys_to_paint = ["Up", "Down", "Left", "Right"]
        elif zone_id == "numpad":
            keys_to_paint = [k["id"] for k in KEY_DEFINITIONS if k.get("group") == "numpad"]
        elif zone_id == "func":
            keys_to_paint = [f"F{i}" for i in range(1, 13)] + ["Esc"]
        elif zone_id == "alpha":
            keys_to_paint = [k["id"] for k in KEY_DEFINITIONS if k.get("group") in ["alpha", "wasd"]]
        elif zone_id == "all":
            keys_to_paint = list(self.rgb_key_buttons.keys())

        for kid in keys_to_paint:
            self.current_key_colors[kid] = self.selected_brush_color
            if kid in self.rgb_key_buttons:
                self.rgb_key_buttons[kid].set_color(self.selected_brush_color)

        self.live_anim.set_static_mode(self.current_key_colors)

    def apply_preset_theme(self, theme_name: str):
        theme = COLOR_PRESETS.get(theme_name)
        if not theme:
            return

        for kid, btn in self.rgb_key_buttons.items():
            grp = getattr(btn, "group", "alpha")
            c = theme.get(grp, theme.get("default", "#7aa2f7"))
            self.current_key_colors[kid] = c
            btn.set_color(c)

        self.live_anim.set_static_mode(self.current_key_colors)
        self.rgb_chassis.update_screen_info(
            tr("smart_screen_title", "1.04″ SMART SCREEN"),
            f"THEME: {theme_name[:12].upper()}"
        )

    def on_brightness_slider_changed(self, value: int):
        self.lbl_brightness_val.setText(tr("rgb_brightness_label", val=value))
        self.live_anim.set_brightness(value)
        self.backend.lighting_config["brightness"] = value

    def set_brightness_level(self, value: int):
        self.brightness_slider.setValue(value)
        self.apply_brightness_now()

    def apply_brightness_now(self):
        b_val = self.brightness_slider.value()
        self.backend.set_lighting_brightness(b_val)
        self.apply_full_configuration()

    def turn_off_led(self):
        self.brightness_slider.setValue(0)
        self.backend.set_lighting_brightness(0)
        self.apply_full_configuration()

    def apply_static_keyboard_colors(self):
        layer = self.rgb_layer_combo.currentText()
        self.backend.lighting_config = {
            "mode": "static",
            "layer": layer,
            "brightness": int(self.brightness_slider.value()),
            "static_colors": dict(self.current_key_colors)
        }
        self.apply_full_configuration()

    # =========================================================================
    # REMAP & KNOB LOGIC
    # =========================================================================
    def on_space_mode_toggled(self):
        if hasattr(self, "remap_radio_split_space") and self.remap_radio_split_space.isChecked():
            new_mode = "split"
        else:
            new_mode = "standard"

        if new_mode != self.space_mode:
            self.space_mode = new_mode
            self.backend.space_mode = new_mode
            self.build_keyboard_grid(
                self.rgb_grid_layout,
                self.rgb_key_buttons,
                self.on_rgb_key_clicked,
                self.space_mode,
                mode="rgb"
            )
            self.build_keyboard_grid(
                self.remap_grid_layout,
                self.remap_key_buttons,
                self.on_remap_key_selected,
                self.space_mode,
                mode="remap"
            )
            self.refresh_remap_ui()

    def on_remap_layer_changed(self):
        self.current_remap_layer = self.remap_layer_combo.currentData() or "Layer1"
        self.refresh_remap_ui()

    def switch_remap_layer(self, layer_id: str):
        idx = self.remap_layer_combo.findData(layer_id)
        if idx >= 0:
            self.remap_layer_combo.setCurrentIndex(idx)

    def on_remap_key_selected(self, key_id: str):
        self.selected_remap_key = key_id

        # Update selection state in UI visual buttons
        for kid, btn in self.remap_key_buttons.items():
            btn.set_selected(kid == key_id)

        # Highlight knob action buttons if a knob action was clicked
        for aid, btn in self.knob_action_buttons.items():
            if aid == key_id:
                btn.setStyleSheet("background-color: #ff9eaf; color: #15161e; font-weight: bold; border-radius: 4px;")
            else:
                btn.setStyleSheet("")

        # Update label
        friendly_name = self._get_friendly_key_name(key_id)
        self.lbl_selected_remap_key.setText(tr("remap_selected_item", name=friendly_name))

    def _get_friendly_key_name(self, key_id: str) -> str:
        for k in KEY_DEFINITIONS:
            if k["id"] == key_id:
                return f"{k['label']} [{k['id']}]"
        if key_id in ["LeftSpace", "StandardSpace", "RightSpace"]:
            return f"Spacebar ({key_id})"
        for kinfo in get_knobs_metadata():
            for act in kinfo["actions"]:
                if act["id"] == key_id:
                    return f"{kinfo['name']} • {act['full_label']}"
        return key_id

    def on_action_picked(self, action_code: str, action_label: str, button_widget: QPushButton):
        self.current_picked_action = action_code
        self.lbl_picked_action_info.setText(tr("remap_picked_action", action=f"{action_label} [{action_code}]"))

        # Highlight active action button
        for cat_title, btn_list in self.category_action_buttons.items():
            for b in btn_list:
                if b == button_widget:
                    b.setStyleSheet("""
                        QPushButton {
                            background-color: #ff9eaf;
                            color: #15161e;
                            font-weight: bold;
                            border: 2px solid #ffffff;
                        }
                    """)
                else:
                    b.setStyleSheet("""
                        QPushButton {
                            background-color: #24283b;
                            color: #c0caf5;
                        }
                        QPushButton:hover {
                            background-color: #2f3652;
                            border: 1px solid #7aa2f7;
                            color: #ffffff;
                        }
                    """)

    def on_remap_search_changed(self, text: str):
        query = text.strip().lower()
        for cat_title, btn_list in self.category_action_buttons.items():
            for b in btn_list:
                code = b.property("action_code") or ""
                lbl = b.property("action_label") or ""
                if not query or query in code.lower() or query in lbl.lower():
                    b.show()
                else:
                    b.hide()

    def update_combination_preview(self):
        mods = []
        if self.chk_ctrl.isChecked():
            mods.append("LCtrl")
        if self.chk_shift.isChecked():
            mods.append("LShift")
        if self.chk_alt.isChecked():
            mods.append("LAlt")
        if self.chk_win.isChecked():
            mods.append("LWin")

        base_k = self.combo_base_key.currentData() or "A"
        if mods:
            combo_str = "+".join(mods) + "+" + base_k
        else:
            combo_str = base_k

        self.current_picked_action = combo_str
        self.lbl_picked_action_info.setText(tr("remap_picked_action", action=f"⚡ Combo: {combo_str}"))

    def on_macro_combo_changed(self):
        macro_act = self.remap_macro_combo.currentData()
        if macro_act:
            self.current_picked_action = macro_act
            self.lbl_picked_action_info.setText(tr("remap_picked_action", action=macro_act))
            m_name = macro_act[6:-1]
            m_obj = self.backend.macros.get(m_name)
            if m_obj:
                self.lbl_macro_details.setText(f"Steps: {len(m_obj.actions)} • Mode: {m_obj.repeat_type}")

    def on_popular_shortcut_selected(self):
        code = self.popular_shortcuts_combo.currentData()
        if not code:
            return
        # Parse modifiers
        self.chk_ctrl.setChecked("LCtrl" in code or "Ctrl" in code)
        self.chk_shift.setChecked("LShift" in code or "Shift" in code)
        self.chk_alt.setChecked("LAlt" in code or "Alt" in code)
        self.chk_win.setChecked("LWin" in code or "Win" in code)

        base_key = code.split("+")[-1]
        idx = self.combo_base_key.findData(base_key)
        if idx >= 0:
            self.combo_base_key.setCurrentIndex(idx)
        self.update_combination_preview()

    def assign_selected_remap_action(self):
        if not self.selected_remap_key:
            QMessageBox.warning(self, tr("msg_warning", "Warning"), "Please select a key on the visual keyboard or knob first!")
            return

        current_tab_text = self.remap_category_tabs.tabText(self.remap_category_tabs.currentIndex())
        target_action = self.current_picked_action

        if "Combination" in current_tab_text or "Skrót" in current_tab_text:
            mods = []
            if self.chk_ctrl.isChecked():
                mods.append("LCtrl")
            if self.chk_shift.isChecked():
                mods.append("LShift")
            if self.chk_alt.isChecked():
                mods.append("LAlt")
            if self.chk_win.isChecked():
                mods.append("LWin")

            base_k = self.combo_base_key.currentData() or "A"
            if mods:
                target_action = "+".join(mods) + "+" + base_k
            else:
                target_action = base_k
        elif "Macro" in current_tab_text or "Makro" in current_tab_text:
            target_action = self.remap_macro_combo.currentData()

        if not target_action:
            QMessageBox.warning(self, tr("msg_warning", "Warning"), "Please select an action in the tabs above before assigning!")
            return

        self.backend.set_key_remap(self.current_remap_layer, self.selected_remap_key, target_action)
        self.refresh_remap_ui()
        friendly_src = self._get_friendly_key_name(self.selected_remap_key)
        friendly_dst = get_friendly_action_label(target_action)
        self.lbl_bottom_info.setText(tr("msg_assigned_info", dst=friendly_dst, src=friendly_src, layer=self.current_remap_layer))

    def reset_selected_key_remap(self):
        if not self.selected_remap_key:
            return
        self.backend.remove_key_remap(self.current_remap_layer, self.selected_remap_key)
        self.refresh_remap_ui()

    def delete_remap_from_table(self, key_id: str):
        self.backend.remove_key_remap(self.current_remap_layer, key_id)
        self.refresh_remap_ui()

    def clear_current_layer_remaps(self):
        reply = QMessageBox.question(
            self,
            tr("remap_btn_clear_layer", "Clear Layer"),
            f"Are you sure you want to clear all remaps on layer {self.current_remap_layer}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.backend.clear_layer_remaps(self.current_remap_layer)
            self.refresh_remap_ui()

    def copy_knobs_to_all_layers(self):
        self.backend.copy_knob_remaps_to_all_layers(self.current_remap_layer)
        self.refresh_remap_ui()
        QMessageBox.information(
            self,
            tr("msg_success", "Success"),
            tr("msg_copy_knobs_success", "Knob configurations copied across all layers.")
        )

    def on_knob_preset_applied(self, knob_id: str, combo_widget: QComboBox):
        preset_name = combo_widget.currentData()
        if not preset_name:
            return
        presets = get_knob_presets()
        preset_dict = presets.get(preset_name)
        if not preset_dict:
            return

        for kinfo in get_knobs_metadata():
            if kinfo["id"] == knob_id:
                for act in kinfo["actions"]:
                    aid = act["id"]
                    if "_CW" in aid:
                        self.backend.set_key_remap(self.current_remap_layer, aid, preset_dict["CW"])
                    elif "_CCW" in aid:
                        self.backend.set_key_remap(self.current_remap_layer, aid, preset_dict["CCW"])
                    elif "_Click" in aid:
                        self.backend.set_key_remap(self.current_remap_layer, aid, preset_dict["Click"])
                break

        self.refresh_remap_ui()
        combo_widget.blockSignals(True)
        combo_widget.setCurrentIndex(0)
        combo_widget.blockSignals(False)

    def refresh_remap_ui(self):
        layer_remaps = self.backend.remaps.get(self.current_remap_layer, {})

        # 1. Update visual keys on the keyboard plate
        for kid, btn in self.remap_key_buttons.items():
            act = layer_remaps.get(kid)
            btn.set_remap(act)
            btn.set_selected(kid == self.selected_remap_key)

        # 2. Update Knob action buttons in the knob cards
        for kinfo in get_knobs_metadata():
            for act in kinfo["actions"]:
                aid = act["id"]
                label_prefix = act["label"]
                if aid in self.knob_action_buttons:
                    btn = self.knob_action_buttons[aid]
                    curr_act = layer_remaps.get(aid, act.get("default", "Default"))
                    friendly = get_friendly_action_label(curr_act)
                    btn.setText(f"{label_prefix}: {friendly}")
                    if aid == self.selected_remap_key:
                        btn.setStyleSheet("background-color: #ff9eaf; color: #15161e; font-weight: bold; border-radius: 4px;")
                    else:
                        btn.setStyleSheet("")

        # 3. Update Macro dropdown in Remap Inspector
        self.remap_macro_combo.blockSignals(True)
        self.remap_macro_combo.clear()
        for m_name in self.backend.macros.keys():
            self.remap_macro_combo.addItem(f"⚡ {m_name}", f"Macro({m_name})")
        self.remap_macro_combo.blockSignals(False)

        # 4. Populate Remap Summary Table
        self.lbl_remap_table_title.setText(tr("remap_table_title", layer=self.current_remap_layer))
        remap_items = list(layer_remaps.items())
        self.remap_table.setRowCount(len(remap_items))

        for row_idx, (src_key, dst_act) in enumerate(remap_items):
            friendly_src = self._get_friendly_key_name(src_key)
            friendly_dst = get_friendly_action_label(dst_act)

            it_key = QTableWidgetItem(friendly_src)
            it_act = QTableWidgetItem(friendly_dst)
            it_code = QTableWidgetItem(dst_act)

            it_key.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            it_act.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            it_code.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)

            self.remap_table.setItem(row_idx, 0, it_key)
            self.remap_table.setItem(row_idx, 1, it_act)
            self.remap_table.setItem(row_idx, 2, it_code)

            del_btn = QPushButton("✕")
            del_btn.setFixedWidth(28)
            del_btn.setStyleSheet("background-color: #3b2732; color: #ff9eaf; font-weight: bold; border-radius: 4px;")
            del_btn.clicked.connect(lambda _, sk=src_key: self.delete_remap_from_table(sk))
            self.remap_table.setCellWidget(row_idx, 3, del_btn)

    # =========================================================================
    # MACRO STUDIO LOGIC
    # =========================================================================
    def refresh_macro_list_ui(self):
        self.macro_list_widget.clear()
        for name, macro in self.backend.macros.items():
            item = QListWidgetItem(f"⚡ {name} ({len(macro.actions)} steps)")
            item.setData(Qt.UserRole, name)
            self.macro_list_widget.addItem(item)

        if self.current_macro_name:
            for idx in range(self.macro_list_widget.count()):
                it = self.macro_list_widget.item(idx)
                if it.data(Qt.UserRole) == self.current_macro_name:
                    self.macro_list_widget.setCurrentItem(it)
                    break
        elif self.macro_list_widget.count() > 0:
            self.macro_list_widget.setCurrentRow(0)

    def on_macro_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if not current:
            return
        m_name = current.data(Qt.UserRole)
        self.current_macro_name = m_name
        macro = self.backend.macros.get(m_name)
        if not macro:
            return

        self.macro_name_input.blockSignals(True)
        self.macro_repeat_combo.blockSignals(True)
        self.macro_repeat_count_spin.blockSignals(True)

        self.macro_name_input.setText(macro.name)
        idx = self.macro_repeat_combo.findData(macro.repeat_type)
        if idx >= 0:
            self.macro_repeat_combo.setCurrentIndex(idx)
        self.macro_repeat_count_spin.setValue(macro.repeat_count)

        self.macro_name_input.blockSignals(False)
        self.macro_repeat_combo.blockSignals(False)
        self.macro_repeat_count_spin.blockSignals(False)

        self.refresh_macro_actions_table()

    def refresh_macro_actions_table(self):
        if not self.current_macro_name or self.current_macro_name not in self.backend.macros:
            self.macro_actions_table.setRowCount(0)
            return

        macro = self.backend.macros[self.current_macro_name]
        self.macro_actions_table.setRowCount(len(macro.actions))

        for row_idx, act in enumerate(macro.actions):
            it_type = QTableWidgetItem(act.action_type)
            it_key = QTableWidgetItem(self._get_friendly_key_name(act.key))

            it_type.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            it_key.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            self.macro_actions_table.setItem(row_idx, 0, it_type)
            self.macro_actions_table.setItem(row_idx, 1, it_key)

            delay_spin = QSpinBox()
            delay_spin.setRange(1, 10000)
            delay_spin.setValue(act.delay)
            delay_spin.valueChanged.connect(lambda val, r=row_idx: self.on_step_delay_changed(r, val))
            self.macro_actions_table.setCellWidget(row_idx, 2, delay_spin)

            opt_widget = QWidget()
            opt_layout = QHBoxLayout(opt_widget)
            opt_layout.setContentsMargins(0, 0, 0, 0)
            opt_layout.setSpacing(2)

            btn_up = QPushButton("▲")
            btn_up.setFixedWidth(24)
            btn_up.clicked.connect(lambda _, r=row_idx: self.move_macro_step(r, -1))
            opt_layout.addWidget(btn_up)

            btn_down = QPushButton("▼")
            btn_down.setFixedWidth(24)
            btn_down.clicked.connect(lambda _, r=row_idx: self.move_macro_step(r, 1))
            opt_layout.addWidget(btn_down)

            btn_del = QPushButton("❌")
            btn_del.setFixedWidth(24)
            btn_del.clicked.connect(lambda _, r=row_idx: self.delete_macro_step(r))
            opt_layout.addWidget(btn_del)

            self.macro_actions_table.setCellWidget(row_idx, 3, opt_widget)

    def on_macro_properties_changed(self):
        if not self.current_macro_name or self.current_macro_name not in self.backend.macros:
            return

        macro = self.backend.macros[self.current_macro_name]
        new_name = self.macro_name_input.text().strip().replace(" ", "_")
        if not new_name:
            return

        macro.repeat_type = self.macro_repeat_combo.currentData()
        macro.repeat_count = self.macro_repeat_count_spin.value()

        if new_name != self.current_macro_name:
            del self.backend.macros[self.current_macro_name]
            macro.name = new_name
            self.backend.macros[new_name] = macro
            self.current_macro_name = new_name
            self.refresh_macro_list_ui()

        self.backend.save_profile()

    def on_step_delay_changed(self, row: int, delay_val: int):
        if self.current_macro_name and self.current_macro_name in self.backend.macros:
            macro = self.backend.macros[self.current_macro_name]
            if 0 <= row < len(macro.actions):
                macro.actions[row].delay = delay_val
                self.backend.save_profile()

    def add_macro_step(self):
        if not self.current_macro_name or self.current_macro_name not in self.backend.macros:
            QMessageBox.warning(self, tr("msg_warning", "Warning"), "Please select or create a macro first!")
            return

        act_text = self.action_type_combo.currentText()
        if "Down" in act_text:
            act_type = "Down"
        elif "Up" in act_text:
            act_type = "Up"
        else:
            act_type = "Press"

        act_key = self.action_key_combo.currentData()
        act_delay = self.action_delay_spin.value()

        macro = self.backend.macros[self.current_macro_name]
        macro.actions.append(MacroAction(action_type=act_type, key=act_key, delay=act_delay))
        self.backend.save_profile()
        self.refresh_macro_actions_table()

    def move_macro_step(self, row: int, direction: int):
        if not self.current_macro_name or self.current_macro_name not in self.backend.macros:
            return
        macro = self.backend.macros[self.current_macro_name]
        new_row = row + direction
        if 0 <= new_row < len(macro.actions):
            macro.actions[row], macro.actions[new_row] = macro.actions[new_row], macro.actions[row]
            self.backend.save_profile()
            self.refresh_macro_actions_table()

    def delete_macro_step(self, row: int):
        if not self.current_macro_name or self.current_macro_name not in self.backend.macros:
            return
        macro = self.backend.macros[self.current_macro_name]
        if 0 <= row < len(macro.actions):
            del macro.actions[row]
            self.backend.save_profile()
            self.refresh_macro_actions_table()

    def clear_all_macro_steps(self):
        if not self.current_macro_name or self.current_macro_name not in self.backend.macros:
            return
        macro = self.backend.macros[self.current_macro_name]
        macro.actions.clear()
        self.backend.save_profile()
        self.refresh_macro_actions_table()

    def create_new_macro(self):
        idx = 1
        new_name = f"Macro_{idx}"
        while new_name in self.backend.macros:
            idx += 1
            new_name = f"Macro_{idx}"

        new_macro = MacroItem(name=new_name, default_delay=20, actions=[MacroAction("Press", "A", 20)])
        self.backend.add_or_update_macro(new_macro)
        self.current_macro_name = new_name
        self.refresh_macro_list_ui()

    def duplicate_current_macro(self):
        if not self.current_macro_name or self.current_macro_name not in self.backend.macros:
            return
        macro = self.backend.macros[self.current_macro_name]
        dup_name = f"{macro.name}_Copy"
        dup_macro = MacroItem(
            name=dup_name,
            default_delay=macro.default_delay,
            repeat_type=macro.repeat_type,
            repeat_count=macro.repeat_count,
            actions=[MacroAction(a.action_type, a.key, a.delay) for a in macro.actions]
        )
        self.backend.add_or_update_macro(dup_macro)
        self.current_macro_name = dup_name
        self.refresh_macro_list_ui()

    def rename_current_macro(self):
        if not self.current_macro_name or self.current_macro_name not in self.backend.macros:
            return
        name, ok = QInputDialog.getText(self, tr("macro_btn_rename", "Rename"), "Enter new macro name:", text=self.current_macro_name)
        if ok and name.strip():
            clean_name = name.strip().replace(" ", "_")
            macro = self.backend.macros[self.current_macro_name]
            del self.backend.macros[self.current_macro_name]
            macro.name = clean_name
            self.backend.macros[clean_name] = macro
            self.current_macro_name = clean_name
            self.backend.save_profile()
            self.refresh_macro_list_ui()

    def delete_current_macro(self):
        if not self.current_macro_name or self.current_macro_name not in self.backend.macros:
            return
        reply = QMessageBox.question(
            self,
            tr("macro_btn_delete", "Delete"),
            f"Are you sure you want to delete macro '{self.current_macro_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.backend.delete_macro(self.current_macro_name)
            self.current_macro_name = None
            self.refresh_macro_list_ui()

    def generate_macro_from_text(self):
        text = self.quick_text_input.text()
        if not text:
            return
        delay = self.quick_text_delay_spin.value()
        m_name = f"Text_{int(time.time()) % 1000}"
        macro = self.backend.create_text_macro(m_name, text, delay=delay)
        self.current_macro_name = macro.name
        self.refresh_macro_list_ui()
        QMessageBox.information(
            self,
            tr("msg_success", "Success"),
            f"Generated macro '{macro.name}' with {len(macro.actions)} steps."
        )

    # =========================================================================
    # CODE PREVIEW & EXPORT DIALOGS
    # =========================================================================
    def refresh_debug_code_view(self):
        raw_code = self.backend.generate_full_config()
        self.debug_code_edit.setPlainText(raw_code)

    def copy_debug_code_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.debug_code_edit.toPlainText())
        QMessageBox.information(self, tr("msg_success", "Success"), tr("msg_copied_clipboard"))

    def export_raw_config_dialog(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Export UserData", "GK104_Config.txt", "GK6X UserData (*.txt);;All files (*)")
        if fname:
            try:
                code = self.backend.generate_full_config()
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(code)
                QMessageBox.information(self, tr("msg_success", "Success"), f"Saved to:\n{fname}")
            except Exception as e:
                QMessageBox.critical(self, tr("msg_error", "Error"), str(e))

    def save_profile_dialog(self, default_type: str = "json"):
        name, ok = QInputDialog.getText(self, tr("pm_btn_save_current", "Save Profile"), "Enter profile name:")
        if ok and name.strip():
            path = self.backend.save_named_profile(name.strip(), profile_type=default_type)
            QMessageBox.information(self, tr("msg_success", "Success"), tr("msg_profile_saved", name=name.strip()))

    def load_profile_dialog(self, auto_apply: bool = False):
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Load Profile",
            "",
            "Config Files (*.json *.txt *.gkprofile);;JSON Profile (*.json *.gkprofile);;UserData TXT (*.txt);;All files (*)"
        )
        if fname and os.path.exists(fname):
            ok, msg, _ = self.backend.load_any_config_file(fname)
            if ok:
                self.apply_loaded_state_to_ui()
                if auto_apply:
                    self.apply_full_configuration()
                else:
                    QMessageBox.information(self, tr("msg_success", "Success"), f"Profile loaded:\n{fname}")
            else:
                QMessageBox.critical(self, tr("msg_error", "Error"), msg)

    def apply_loaded_state_to_ui(self):
        self.space_mode = getattr(self.backend, "space_mode", "split")
        self.build_keyboard_grid(
            self.rgb_grid_layout,
            self.rgb_key_buttons,
            self.on_rgb_key_clicked,
            self.space_mode,
            mode="rgb"
        )
        self.build_keyboard_grid(
            self.remap_grid_layout,
            self.remap_key_buttons,
            self.on_remap_key_selected,
            self.space_mode,
            mode="remap"
        )
        self.refresh_remap_ui()
        self.refresh_macro_list_ui()
        self.refresh_debug_code_view()
