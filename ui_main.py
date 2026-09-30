import os
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QListWidget, QListWidgetItem,
    QLineEdit, QComboBox, QColorDialog, QFrame, QGridLayout,
    QScrollArea, QMessageBox, QProgressBar, QButtonGroup, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox, QCheckBox,
    QGroupBox, QSplitter, QTextEdit, QPlainTextEdit, QFileDialog,
    QRadioButton, QSlider, QMenu, QSystemTrayIcon
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap, QAction

from gk_backend import (
    GKBackend, KEY_DEFINITIONS, COLOR_PRESETS, AVAILABLE_LAYERS,
    TARGET_KEY_CATEGORIES, POPULAR_SHORTCUTS, MacroItem, MacroAction,
    KNOBS_METADATA, KNOB_PRESETS, HARDWARE_KEY_ALIASES,
    get_system_battery_info
)


class KeyVisualButton(QPushButton):
    """Interactive visual representation of a keyboard key for RGB & Remap visualizers."""
    key_clicked = Signal(str)

    def __init__(self, key_id: str, label: str, group: str):
        super().__init__(label)
        self.key_id = key_id
        self.label_text = label
        self.group = group
        self.current_color = "#24283b"
        self.remap_action: Optional[str] = None
        self.is_selected = False

        self.setProperty("class", "keyboardKey")
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(lambda: self.key_clicked.emit(self.key_id))
        self.update_style()

    def set_color(self, hex_color: str):
        self.current_color = hex_color
        self.update_style()

    def set_remap(self, action: Optional[str]):
        self.remap_action = action
        if action:
            short_act = action
            if len(short_act) > 7:
                short_act = short_act[:6] + ".."
            self.setText(f"{self.label_text}\n{short_act}")
        else:
            self.setText(self.label_text)
        self.update_style()

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        c = QColor(self.current_color)
        luminance = (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255
        text_color = "#15161e" if luminance > 0.5 else "#ffffff"

        border = "1px solid #3b4261"
        if self.is_selected:
            border = "2px solid #ff9eaf"
        elif self.remap_action:
            border = "2px solid #7aa2f7"

        bg = self.current_color
        if self.remap_action and self.current_color == "#24283b":
            bg = "#1f3554"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {text_color};
                border: {border};
                border-radius: 4px;
                font-size: 9px;
                font-weight: bold;
                padding: 1px;
            }}
            QPushButton:hover {{
                border: 2px solid #7aa2f7;
            }}
        """)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Skyloong GK104 Pro Studio — RGB • Remap • Makra • Knoby")
        self.resize(1200, 880)
        self.setMinimumSize(1040, 740)

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
        self.selected_remap_key: Optional[str] = "LeftSpace" if self.space_mode == "split" else "Space_18"
        self.current_remap_layer = "Layer1"

        # Macro state
        self.current_macro_name: Optional[str] = None

        self.init_ui()
        self.init_system_tray()
        self.connect_signals()
        self.refresh_device()
        self.load_effects()
        self.refresh_remap_ui()
        self.refresh_macro_list_ui()

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
        header_layout.setContentsMargins(10, 8, 10, 8)

        # App Title & Device info
        title_box = QVBoxLayout()
        title_lbl = QLabel("Skyloong GK104 Pro Studio")
        title_lbl.setObjectName("appTitle")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #7aa2f7;")
        title_box.addWidget(title_lbl)

        self.device_status_lbl = QLabel("Wykrywanie urządzenia GK104 Pro...")
        self.device_status_lbl.setObjectName("deviceStatus")
        self.device_status_lbl.setStyleSheet("color: #9ece6a; font-size: 12px;")
        title_box.addWidget(self.device_status_lbl)
        header_layout.addLayout(title_box)

        header_layout.addSpacing(15)

        # Battery Status Widget in Header
        self.lbl_battery_header = QLabel("🔋 Bateria: Sprawdzanie...")
        self.lbl_battery_header.setStyleSheet("color: #7aa2f7; font-size: 12px; font-weight: bold; background-color: #13141c; padding: 6px 12px; border-radius: 6px; border: 1px solid #24283b;")
        header_layout.addWidget(self.lbl_battery_header)

        header_layout.addStretch()

        # Global Action Buttons
        self.btn_refresh_dev = QPushButton("🔄 Odśwież połączenie")
        self.btn_refresh_dev.clicked.connect(self.refresh_device)
        header_layout.addWidget(self.btn_refresh_dev)

        self.btn_reset_mappings = QPushButton("⚠️ Reset Fabryczny (Unmap)")
        self.btn_reset_mappings.setObjectName("dangerBtn")
        self.btn_reset_mappings.clicked.connect(self.reset_factory_mappings)
        header_layout.addWidget(self.btn_reset_mappings)

        self.btn_apply_all = QPushButton("💾 WGRAJ DO KLAWIATURY")
        self.btn_apply_all.setObjectName("primaryBtn")
        self.btn_apply_all.setStyleSheet("padding: 10px 20px; font-size: 13px; font-weight: bold;")
        self.btn_apply_all.clicked.connect(self.apply_full_configuration)
        header_layout.addWidget(self.btn_apply_all)

        main_layout.addWidget(header_frame)

        # 2. Main Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_lighting_tab(), "🌈 Oświetlenie LED")
        self.tab_widget.addTab(self.create_remap_tab(), "⌨️ Remapowanie & Pokrętła (Knobs)")
        self.tab_widget.addTab(self.create_macro_tab(), "⚡ Menedżer Makr (Macro Studio)")
        self.tab_widget.addTab(self.create_debug_tab(), "📝 Podgląd Kodu & Diagnostyka")
        self.tab_widget.setCurrentIndex(1)  # Default to Remap tab
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tab_widget)

        # 3. Bottom Status / Progress Bar
        bottom_box = QHBoxLayout()
        self.lbl_bottom_info = QLabel("Gotowy do pracy.")
        self.lbl_bottom_info.setStyleSheet("color: #7982a9; font-size: 11px;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(160)

        bottom_box.addWidget(self.lbl_bottom_info)
        bottom_box.addStretch()
        bottom_box.addWidget(self.progress_bar)
        main_layout.addLayout(bottom_box)

    # =========================================================================
    # VIRTUAL KEYBOARD BUILDER (Handles Split Spacebar & Standard Spacebar)
    # =========================================================================
    def build_keyboard_grid(self, grid_layout: QGridLayout, buttons_dict: Dict[str, KeyVisualButton],
                            click_handler, space_mode: str):
        # Clear existing widgets from layout
        while grid_layout.count():
            item = grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        buttons_dict.clear()

        # Rows 0 to 4
        for key_info in KEY_DEFINITIONS:
            if key_info["row"] < 5:
                btn = KeyVisualButton(key_info["id"], key_info["label"], key_info["group"])
                btn.key_clicked.connect(click_handler)
                row = key_info["row"]
                col_pos = int(key_info["col"] * 2)
                col_span = int(key_info.get("width", 1.0) * 2)
                row_span = int(key_info.get("height", 1.0))
                grid_layout.addWidget(btn, row, col_pos, row_span, col_span)
                buttons_dict[key_info["id"]] = btn

        # Row 5 (Bottom Row with Spacebar Options)
        bottom_keys = [
            {"id": "LCtrl", "label": "Ctrl", "group": "mod", "col": 0, "width": 1.25},
            {"id": "LWin", "label": "Win", "group": "mod", "col": 1.25, "width": 1.25},
            {"id": "LAlt", "label": "Alt", "group": "mod", "col": 2.5, "width": 1.25},
        ]

        if space_mode == "split":
            bottom_keys.extend([
                {"id": "LeftSpace", "label": "⎵ Lewa Spacja", "group": "mod", "col": 3.75, "width": 3.125},
                {"id": "RightSpace", "label": "⎵ Prawa Spacja", "group": "mod", "col": 6.875, "width": 3.125},
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
            btn = KeyVisualButton(k["id"], k["label"], k["group"])
            btn.key_clicked.connect(click_handler)
            row = 5
            col_pos = int(k["col"] * 2)
            col_span = int(k.get("width", 1.0) * 2)
            grid_layout.addWidget(btn, row, col_pos, 1, col_span)
            buttons_dict[k["id"]] = btn

    # =========================================================================
    # TAB 1: RGB LIGHTING
    # =========================================================================
    def create_lighting_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Top interactive keyboard container
        kb_card = QFrame()
        kb_card.setObjectName("keyMapContainer")
        kb_layout = QVBoxLayout(kb_card)
        kb_layout.setContentsMargins(8, 8, 8, 8)

        kb_header = QHBoxLayout()
        kb_title = QLabel("Wizualna Klawiatura 104 (Kliknij klawisz, aby pomalować aktualnym kolorem)")
        kb_title.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        kb_header.addWidget(kb_title)
        kb_header.addStretch()

        # Spacebar mode selector in RGB tab
        kb_header.addWidget(QLabel("Układ Spacji:"))
        self.rgb_radio_split_space = QRadioButton("Podwójna spacja (Split)")
        self.rgb_radio_single_space = QRadioButton("Standardowa")
        if self.space_mode == "split":
            self.rgb_radio_split_space.setChecked(True)
        else:
            self.rgb_radio_single_space.setChecked(True)
        self.rgb_radio_split_space.toggled.connect(self.on_space_mode_toggled)
        self.rgb_radio_single_space.toggled.connect(self.on_space_mode_toggled)
        kb_header.addWidget(self.rgb_radio_split_space)
        kb_header.addWidget(self.rgb_radio_single_space)
        kb_header.addSpacing(15)

        self.rgb_layer_combo = QComboBox()
        self.rgb_layer_combo.addItems(["Base", "Layer1", "Layer2", "Layer3"])
        self.rgb_layer_combo.currentIndexChanged.connect(self.on_rgb_layer_changed)
        kb_header.addWidget(QLabel("Docelowa warstwa LED:"))
        kb_header.addWidget(self.rgb_layer_combo)
        kb_layout.addLayout(kb_header)

        # Grid of keys
        self.rgb_grid_widget = QWidget()
        self.rgb_grid_layout = QGridLayout(self.rgb_grid_widget)
        self.rgb_grid_layout.setSpacing(2)
        self.rgb_grid_layout.setContentsMargins(0, 4, 0, 4)

        self.build_keyboard_grid(
            self.rgb_grid_layout,
            self.rgb_key_buttons,
            self.on_rgb_key_clicked,
            self.space_mode
        )

        kb_layout.addWidget(self.rgb_grid_widget)
        layout.addWidget(kb_card)

        # Bottom Controls: Left (Effects library) | Right (Palette & Tools)
        splitter = QSplitter(Qt.Horizontal)

        # Left: Animated library
        left_card = QFrame()
        left_card.setObjectName("cardFrame")
        left_vbox = QVBoxLayout(left_card)
        left_vbox.setContentsMargins(8, 8, 8, 8)

        left_lbl = QLabel("🌊 Biblioteka Animacji (330+ efektów)")
        left_lbl.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        left_vbox.addWidget(left_lbl)

        search_box = QHBoxLayout()
        self.effect_search_input = QLineEdit()
        self.effect_search_input.setPlaceholderText("Szukaj animacji (np. Rainbow, Wave, Breath, Meteor)...")
        self.effect_search_input.textChanged.connect(self.filter_effects)
        search_box.addWidget(self.effect_search_input)

        self.category_combo = QComboBox()
        self.category_combo.addItem("Wszystkie kategorie")
        self.category_combo.currentIndexChanged.connect(self.filter_effects)
        search_box.addWidget(self.category_combo)
        left_vbox.addLayout(search_box)

        self.effects_list_widget = QListWidget()
        self.effects_list_widget.itemDoubleClicked.connect(self.on_effect_double_clicked)
        left_vbox.addWidget(self.effects_list_widget)

        btn_apply_effect = QPushButton("✨ Zastosuj wybraną animację")
        btn_apply_effect.clicked.connect(self.apply_selected_effect)
        left_vbox.addWidget(btn_apply_effect)

        splitter.addWidget(left_card)

        # Right: Palette, Presets & Zones
        right_card = QFrame()
        right_card.setObjectName("cardFrame")
        right_vbox = QVBoxLayout(right_card)
        right_vbox.setContentsMargins(8, 8, 8, 8)

        right_lbl = QLabel("🎨 Kolory & Narzędzia Malowania")
        right_lbl.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        right_vbox.addWidget(right_lbl)

        # Color picker row
        brush_row = QHBoxLayout()
        brush_row.addWidget(QLabel("Aktualny pędzel:"))
        self.brush_preview_btn = QPushButton()
        self.brush_preview_btn.setFixedSize(36, 26)
        self.brush_preview_btn.setStyleSheet(f"background-color: {self.selected_brush_color}; border-radius: 4px;")
        self.brush_preview_btn.clicked.connect(self.open_color_dialog)
        brush_row.addWidget(self.brush_preview_btn)

        btn_pick_color = QPushButton("Wybierz własny kolor...")
        btn_pick_color.clicked.connect(self.open_color_dialog)
        brush_row.addWidget(btn_pick_color)
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
        zone_group = QGroupBox("Malowanie Strefowe")
        zone_layout = QGridLayout(zone_group)
        zones = [
            ("WASD", "wasd"), ("Strzałki", "arrows"), ("NumPad", "numpad"),
            ("F1-F12", "func"), ("Litery", "alpha"), ("Cała klawiatura", "all")
        ]
        for idx, (z_name, z_id) in enumerate(zones):
            z_btn = QPushButton(f"Pomaluj: {z_name}")
            z_btn.clicked.connect(lambda _, zid=z_id: self.paint_zone(zid))
            zone_layout.addWidget(z_btn, idx // 3, idx % 3)
        right_vbox.addWidget(zone_group)

        # Styled Themes
        theme_group = QGroupBox("Gotowe Motywy Kolorystyczne")
        theme_layout = QGridLayout(theme_group)
        for idx, t_name in enumerate(COLOR_PRESETS.keys()):
            t_btn = QPushButton(t_name)
            t_btn.clicked.connect(lambda _, tn=t_name: self.apply_preset_theme(tn))
            theme_layout.addWidget(t_btn, idx // 2, idx % 2)
        right_vbox.addWidget(theme_group)

        # Brightness Control Group
        bright_group = QGroupBox("Jasność Podświetlenia Klawiatury")
        bright_layout = QHBoxLayout(bright_group)
        self.lbl_brightness_val = QLabel(f"Jasność: {self.backend.lighting_config.get('brightness', 100)}%")
        self.lbl_brightness_val.setFixedWidth(100)
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

        btn_apply_bright = QPushButton("⚡ Zastosuj")
        btn_apply_bright.setObjectName("primaryBtn")
        btn_apply_bright.setFixedWidth(80)
        btn_apply_bright.clicked.connect(self.apply_brightness_now)
        bright_layout.addWidget(btn_apply_bright)

        right_vbox.addWidget(bright_group)

        # Tools: LED Off / Apply static
        tools_row = QHBoxLayout()
        btn_led_off = QPushButton("🌙 Wyłącz LED")
        btn_led_off.setObjectName("dangerBtn")
        btn_led_off.clicked.connect(self.turn_off_led)
        tools_row.addWidget(btn_led_off)

        btn_apply_static = QPushButton("✅ Zastosuj Kolory z Klawiatury")
        btn_apply_static.setObjectName("successBtn")
        btn_apply_static.clicked.connect(self.apply_static_keyboard_colors)
        tools_row.addWidget(btn_apply_static)
        right_vbox.addLayout(tools_row)

        splitter.addWidget(right_card)
        splitter.setSizes([450, 550])
        layout.addWidget(splitter)

        return widget

    # =========================================================================
    # TAB 2: KEY REMAPPING & ROTARY KNOBS
    # =========================================================================
    def create_remap_tab(self) -> QWidget:
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Layer Selector & Header
        top_bar = QHBoxLayout()
        layer_lbl = QLabel("Wybierz warstwę do edycji:")
        layer_lbl.setStyleSheet("font-weight: bold; color: #7aa2f7; font-size: 14px;")
        top_bar.addWidget(layer_lbl)

        self.remap_layer_combo = QComboBox()
        for layer_id, layer_name in AVAILABLE_LAYERS:
            self.remap_layer_combo.addItem(layer_name, layer_id)
        self.remap_layer_combo.setCurrentIndex(1)  # Layer1 default
        self.remap_layer_combo.currentIndexChanged.connect(self.on_remap_layer_changed)
        top_bar.addWidget(self.remap_layer_combo)

        top_bar.addSpacing(20)
        # Spacebar mode selector in Remap tab
        top_bar.addWidget(QLabel("Układ Spacji:"))
        self.remap_radio_split_space = QRadioButton("Podwójna spacja (Split)")
        self.remap_radio_single_space = QRadioButton("Standardowa")
        if self.space_mode == "split":
            self.remap_radio_split_space.setChecked(True)
        else:
            self.remap_radio_single_space.setChecked(True)
        self.remap_radio_split_space.toggled.connect(self.on_space_mode_toggled)
        self.remap_radio_single_space.toggled.connect(self.on_space_mode_toggled)
        top_bar.addWidget(self.remap_radio_split_space)
        top_bar.addWidget(self.remap_radio_single_space)

        top_bar.addStretch()

        btn_clear_layer = QPushButton("🗑️ Wyczyść mapowania tej warstwy")
        btn_clear_layer.clicked.connect(self.clear_current_layer_remaps)
        top_bar.addWidget(btn_clear_layer)
        layout.addLayout(top_bar)

        # Interactive visual keyboard for remap
        kb_card = QFrame()
        kb_card.setObjectName("keyMapContainer")
        kb_vbox = QVBoxLayout(kb_card)
        kb_vbox.setContentsMargins(8, 8, 8, 8)

        kb_vbox.addWidget(QLabel("Wybierz klawisz myszką, aby przypisać nową funkcję, skrót lub makro:"))

        self.remap_grid_widget = QWidget()
        self.remap_grid_layout = QGridLayout(self.remap_grid_widget)
        self.remap_grid_layout.setSpacing(2)
        self.remap_grid_layout.setContentsMargins(0, 4, 0, 4)

        self.build_keyboard_grid(
            self.remap_grid_layout,
            self.remap_key_buttons,
            self.on_remap_key_selected,
            self.space_mode
        )

        kb_vbox.addWidget(self.remap_grid_widget)
        layout.addWidget(kb_card)

        # Rotary Knobs Section (GK104 Pro Modular Knobs)
        knobs_card = QFrame()
        knobs_card.setObjectName("cardFrame")
        knobs_vbox = QVBoxLayout(knobs_card)
        knobs_vbox.setContentsMargins(10, 10, 10, 10)
        knobs_vbox.setSpacing(8)

        knobs_header = QHBoxLayout()
        knobs_title = QLabel("🎛️ Konfiguracja Pokręteł (Rotary Knobs — GK104 Pro)")
        knobs_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #7aa2f7;")
        knobs_header.addWidget(knobs_title)
        knobs_header.addStretch()

        btn_copy_knobs = QPushButton("📋 Skopiuj te pokrętła na wszystkie warstwy (Base, Layer 1-3)")
        btn_copy_knobs.setStyleSheet("background-color: #2b3b55; color: #7aa2f7; font-weight: bold; padding: 4px 10px;")
        btn_copy_knobs.clicked.connect(self.copy_knobs_to_all_layers)
        knobs_header.addWidget(btn_copy_knobs)
        knobs_vbox.addLayout(knobs_header)

        knobs_grid = QGridLayout()
        knobs_grid.setSpacing(8)

        for idx, knob_info in enumerate(KNOBS_METADATA):
            k_card = QFrame()
            k_card.setObjectName("knobCard")
            k_card_vbox = QVBoxLayout(k_card)
            k_card_vbox.setContentsMargins(8, 8, 8, 8)
            k_card_vbox.setSpacing(4)

            # Top of card: Title & Preset selector
            k_title_row = QHBoxLayout()
            k_title = QLabel(f"{knob_info['icon']} {knob_info['name']}")
            k_title.setStyleSheet("font-weight: bold; color: #ff9eaf; font-size: 11px;")
            k_title_row.addWidget(k_title)
            k_title_row.addStretch()

            preset_combo = QComboBox()
            preset_combo.addItem("⚡ Szybki schemat...", "")
            for p_name in KNOB_PRESETS.keys():
                preset_combo.addItem(p_name, p_name)
            preset_combo.currentIndexChanged.connect(
                lambda _, kid=knob_info["id"], cb=preset_combo: self.on_knob_preset_applied(kid, cb)
            )
            preset_combo.setFixedWidth(145)
            k_title_row.addWidget(preset_combo)
            k_card_vbox.addLayout(k_title_row)

            # Action buttons inside card (CW, CCW, Click)
            for act in knob_info["actions"]:
                act_id = act["id"]
                act_label = act["label"]
                btn_act = QPushButton(f"{act_label}: Domyślny")
                btn_act.setProperty("class", "knobActionButton")
                btn_act.setCursor(Qt.PointingHandCursor)
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
        assign_vbox = QVBoxLayout(assign_card)
        assign_vbox.setContentsMargins(10, 10, 10, 10)
        assign_vbox.setSpacing(8)

        self.lbl_selected_remap_key = QLabel("Edytowany element: [ Lewa Spacja ]")
        self.lbl_selected_remap_key.setStyleSheet("font-size: 15px; font-weight: bold; color: #ff9eaf;")
        assign_vbox.addWidget(self.lbl_selected_remap_key)

        # Mode Selection
        self.remap_mode_tabs = QTabWidget()

        # Mode A: Standard Key
        tab_std = QWidget()
        v_std = QVBoxLayout(tab_std)
        v_std.addWidget(QLabel("Wybierz klawisz docelowy z listy:"))
        self.std_key_combo = QComboBox()
        for cat_name, keys in TARGET_KEY_CATEGORIES.items():
            for kid, klabel in keys:
                self.std_key_combo.addItem(f"[{cat_name}] {klabel}", kid)
        v_std.addWidget(self.std_key_combo)
        v_std.addStretch()
        self.remap_mode_tabs.addTab(tab_std, "Pojedynczy klawisz")

        # Mode B: Modifier Combination (Shortcut)
        tab_combo = QWidget()
        v_combo = QVBoxLayout(tab_combo)
        v_combo.addWidget(QLabel("Zaznacz modyfikatory i wybierz klawisz bazowy:"))

        mod_box = QHBoxLayout()
        self.chk_ctrl = QCheckBox("Ctrl")
        self.chk_shift = QCheckBox("Shift")
        self.chk_alt = QCheckBox("Alt")
        self.chk_win = QCheckBox("Win")
        mod_box.addWidget(self.chk_ctrl)
        mod_box.addWidget(self.chk_shift)
        mod_box.addWidget(self.chk_alt)
        mod_box.addWidget(self.chk_win)
        v_combo.addLayout(mod_box)

        combo_base_row = QHBoxLayout()
        combo_base_row.addWidget(QLabel("Klawisz bazowy:"))
        self.combo_base_key = QComboBox()
        for cat_name, keys in TARGET_KEY_CATEGORIES.items():
            if "Podstawowe" in cat_name or "Funkcyjne" in cat_name or "Nawigacja" in cat_name or "Multimedia" in cat_name:
                for kid, klabel in keys:
                    self.combo_base_key.addItem(f"{kid} ({klabel})", kid)
        combo_base_row.addWidget(self.combo_base_key)
        v_combo.addLayout(combo_base_row)

        v_combo.addWidget(QLabel("Lub wybierz popularny skrót:"))
        self.popular_shortcuts_combo = QComboBox()
        self.popular_shortcuts_combo.addItem("-- Wybierz gotowy skrót --", "")
        for s_code, s_desc in POPULAR_SHORTCUTS:
            self.popular_shortcuts_combo.addItem(s_desc, s_code)
        self.popular_shortcuts_combo.currentIndexChanged.connect(self.on_popular_shortcut_selected)
        v_combo.addWidget(self.popular_shortcuts_combo)
        v_combo.addStretch()
        self.remap_mode_tabs.addTab(tab_combo, "Kombinacja (Skrót)")

        # Mode C: Macro Assignment
        tab_macro = QWidget()
        v_macro = QVBoxLayout(tab_macro)
        v_macro.addWidget(QLabel("Przypisz zdefiniowane makro:"))
        self.remap_macro_combo = QComboBox()
        v_macro.addWidget(self.remap_macro_combo)
        v_macro.addStretch()
        self.remap_mode_tabs.addTab(tab_macro, "Makro")

        assign_vbox.addWidget(self.remap_mode_tabs)

        # Action buttons
        btn_box = QHBoxLayout()
        btn_assign = QPushButton("✅ Przypisz do wybranego elementu")
        btn_assign.setObjectName("primaryBtn")
        btn_assign.clicked.connect(self.assign_selected_remap_action)
        btn_box.addWidget(btn_assign)

        btn_reset_key = QPushButton("🗑️ Przywróć domyślny")
        btn_reset_key.clicked.connect(self.reset_selected_key_remap)
        btn_box.addWidget(btn_reset_key)
        assign_vbox.addLayout(btn_box)

        splitter.addWidget(assign_card)

        # Right: Remap Table
        table_card = QFrame()
        table_card.setObjectName("cardFrame")
        table_vbox = QVBoxLayout(table_card)
        table_vbox.setContentsMargins(8, 8, 8, 8)

        table_vbox.addWidget(QLabel("Zmodyfikowane klawisze i pokrętła na aktywnej warstwie:"))
        self.remap_table = QTableWidget()
        self.remap_table.setColumnCount(3)
        self.remap_table.setHorizontalHeaderLabels(["Źródło / Klawisz / Knob", "Przypisana Akcja / Makro", "Akcja"])
        self.remap_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.remap_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.remap_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table_vbox.addWidget(self.remap_table)

        splitter.addWidget(table_card)
        splitter.setSizes([500, 500])
        layout.addWidget(splitter)

        scroll_area.setWidget(container)
        return scroll_area

    # =========================================================================
    # TAB 3: MACRO STUDIO
    # =========================================================================
    def create_macro_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        splitter = QSplitter(Qt.Horizontal)

        # Left: Macro List
        left_card = QFrame()
        left_card.setObjectName("cardFrame")
        left_vbox = QVBoxLayout(left_card)
        left_vbox.setContentsMargins(8, 8, 8, 8)

        left_vbox.addWidget(QLabel("⚡ Twoje Makra"))
        self.macro_list_widget = QListWidget()
        self.macro_list_widget.currentItemChanged.connect(self.on_macro_selected)
        left_vbox.addWidget(self.macro_list_widget)

        macro_btn_row = QHBoxLayout()
        btn_new_macro = QPushButton("➕ Nowe makro")
        btn_new_macro.clicked.connect(self.create_new_macro)
        macro_btn_row.addWidget(btn_new_macro)

        btn_dup_macro = QPushButton("📋 Duplikuj")
        btn_dup_macro.clicked.connect(self.duplicate_current_macro)
        macro_btn_row.addWidget(btn_dup_macro)

        btn_del_macro = QPushButton("🗑️ Usuń")
        btn_del_macro.setObjectName("dangerBtn")
        btn_del_macro.clicked.connect(self.delete_current_macro)
        macro_btn_row.addWidget(btn_del_macro)
        left_vbox.addLayout(macro_btn_row)

        splitter.addWidget(left_card)

        # Right: Macro Editor
        right_card = QFrame()
        right_card.setObjectName("cardFrame")
        right_vbox = QVBoxLayout(right_card)
        right_vbox.setContentsMargins(10, 10, 10, 10)
        right_vbox.setSpacing(8)

        right_vbox.addWidget(QLabel("Edycja Makra:"))

        # Macro Properties Form
        props_grid = QGridLayout()

        props_grid.addWidget(QLabel("Nazwa makra:"), 0, 0)
        self.macro_name_input = QLineEdit()
        self.macro_name_input.textChanged.connect(self.on_macro_properties_changed)
        props_grid.addWidget(self.macro_name_input, 0, 1)

        props_grid.addWidget(QLabel("Domyślne opóźnienie (ms):"), 0, 2)
        self.macro_delay_spin = QSpinBox()
        self.macro_delay_spin.setRange(0, 10000)
        self.macro_delay_spin.setValue(0)
        self.macro_delay_spin.valueChanged.connect(self.on_macro_properties_changed)
        props_grid.addWidget(self.macro_delay_spin, 0, 3)

        props_grid.addWidget(QLabel("Tryb powtarzania:"), 1, 0)
        self.macro_repeat_combo = QComboBox()
        self.macro_repeat_combo.addItem("Wykonaj określoną liczbę razy", "RepeatXTimes")
        self.macro_repeat_combo.addItem("Powtarzaj przy trzymaniu klawisza", "ReleaseKeyToStop")
        self.macro_repeat_combo.addItem("Włącz / Wyłącz ponownym kliknięciem (Toggle)", "PressKeyAgainToStop")
        self.macro_repeat_combo.currentIndexChanged.connect(self.on_macro_properties_changed)
        props_grid.addWidget(self.macro_repeat_combo, 1, 1)

        props_grid.addWidget(QLabel("Liczba powtórzeń:"), 1, 2)
        self.macro_repeat_count_spin = QSpinBox()
        self.macro_repeat_count_spin.setRange(1, 255)
        self.macro_repeat_count_spin.setValue(1)
        self.macro_repeat_count_spin.valueChanged.connect(self.on_macro_properties_changed)
        props_grid.addWidget(self.macro_repeat_count_spin, 1, 3)

        right_vbox.addLayout(props_grid)

        # Macro Actions Table
        right_vbox.addWidget(QLabel("Sekwencja akcji makra (Kroki):"))
        self.macro_actions_table = QTableWidget()
        self.macro_actions_table.setColumnCount(4)
        self.macro_actions_table.setHorizontalHeaderLabels(["Typ Akcji", "Klawisz / Znak", "Opóźnienie (ms)", "Opcje"])
        self.macro_actions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.macro_actions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.macro_actions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.macro_actions_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        right_vbox.addWidget(self.macro_actions_table)

        # Step adder toolbar
        add_step_box = QHBoxLayout()
        self.action_type_combo = QComboBox()
        self.action_type_combo.addItems(["Press (Naciśnij i puść)", "Down (Wciśnij)", "Up (Puść)"])
        add_step_box.addWidget(self.action_type_combo)

        self.action_key_combo = QComboBox()
        for cat_name, keys in TARGET_KEY_CATEGORIES.items():
            for kid, klabel in keys:
                self.action_key_combo.addItem(f"{kid} ({klabel})", kid)
        add_step_box.addWidget(self.action_key_combo)

        add_step_box.addWidget(QLabel("Opóźnienie (ms):"))
        self.action_delay_spin = QSpinBox()
        self.action_delay_spin.setRange(0, 5000)
        self.action_delay_spin.setValue(20)
        add_step_box.addWidget(self.action_delay_spin)

        btn_add_step = QPushButton("➕ Dodaj krok")
        btn_add_step.clicked.connect(self.add_macro_step)
        add_step_box.addWidget(btn_add_step)
        right_vbox.addLayout(add_step_box)

        # Quick Text to Macro Generator
        quick_text_group = QGroupBox("🚀 Szybki generator tekstu do makra")
        quick_text_vbox = QVBoxLayout(quick_text_group)
        quick_text_row = QHBoxLayout()
        self.quick_text_input = QLineEdit()
        self.quick_text_input.setPlaceholderText("Wpisz tekst (np. login, komendę, ciąg znaków)...")
        quick_text_row.addWidget(self.quick_text_input)

        btn_gen_text = QPushButton("Konwertuj na sekwencję")
        btn_gen_text.clicked.connect(self.generate_macro_from_text)
        quick_text_row.addWidget(btn_gen_text)
        quick_text_vbox.addLayout(quick_text_row)
        right_vbox.addWidget(quick_text_group)

        splitter.addWidget(right_card)
        splitter.setSizes([350, 650])
        layout.addWidget(splitter)

        return widget

    # =========================================================================
    # TAB 4: DEBUG & DIAGNOSTICS
    # =========================================================================
    def create_debug_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        card = QFrame()
        card.setObjectName("cardFrame")
        card_vbox = QVBoxLayout(card)
        card_vbox.setContentsMargins(10, 10, 10, 10)
        card_vbox.setSpacing(8)

        card_vbox.addWidget(QLabel("Podgląd wygenerowanej konfiguracji sprzętowej GK6X UserData:"))

        self.debug_code_text = QPlainTextEdit()
        self.debug_code_text.setReadOnly(True)
        self.debug_code_text.setStyleSheet("font-family: monospace; font-size: 11px; background-color: #13141c; color: #a9b1d6;")
        card_vbox.addWidget(self.debug_code_text)

        btn_row = QHBoxLayout()
        btn_refresh_code = QPushButton("🔄 Odśwież kod")
        btn_refresh_code.clicked.connect(self.refresh_debug_code_view)
        btn_row.addWidget(btn_refresh_code)

        btn_export = QPushButton("💾 Eksportuj profil do pliku JSON...")
        btn_export.clicked.connect(self.export_profile_json)
        btn_row.addWidget(btn_export)

        btn_import = QPushButton("📂 Importuj profil z pliku JSON...")
        btn_import.clicked.connect(self.import_profile_json)
        btn_row.addWidget(btn_import)
        btn_row.addStretch()
        card_vbox.addLayout(btn_row)

        layout.addWidget(card)
        return widget

    # =========================================================================
    # SIGNALS & CONNECTORS
    # =========================================================================
    def connect_signals(self):
        self.backend.device_status_signal.connect(self.on_device_status)
        self.backend.apply_finished.connect(self.on_apply_finished)
        self.backend.unmap_finished.connect(self.on_unmap_finished)

    def refresh_device(self):
        self.device_status_lbl.setText("Sprawdzanie połączenia USB...")
        self.backend.detect_device()

    def on_device_status(self, is_connected: bool, model_id: str, model_name: str):
        if is_connected:
            self.device_status_lbl.setText(f"🟢 Połączono: {model_name} (ID: {model_id})")
            self.device_status_lbl.setStyleSheet("color: #9ece6a; font-weight: bold;")
        else:
            self.device_status_lbl.setText(f"🔴 Rozłączono / Brak urządzenia (ID: {model_id})")
            self.device_status_lbl.setStyleSheet("color: #f7768e; font-weight: bold;")

    def on_space_mode_toggled(self):
        sender = self.sender()
        if sender in [self.rgb_radio_single_space, self.remap_radio_single_space]:
            if not sender.isChecked():
                return
            new_mode = "standard"
        elif sender in [self.rgb_radio_split_space, self.remap_radio_split_space]:
            if not sender.isChecked():
                return
            new_mode = "split"
        else:
            return

        if new_mode != self.space_mode:
            self.space_mode = new_mode
            self.backend.space_mode = new_mode

            # Synchronize radio buttons without recursion
            self.rgb_radio_split_space.blockSignals(True)
            self.rgb_radio_single_space.blockSignals(True)
            self.remap_radio_split_space.blockSignals(True)
            self.remap_radio_single_space.blockSignals(True)

            self.rgb_radio_split_space.setChecked(new_mode == "split")
            self.rgb_radio_single_space.setChecked(new_mode == "standard")
            self.remap_radio_split_space.setChecked(new_mode == "split")
            self.remap_radio_single_space.setChecked(new_mode == "standard")

            self.rgb_radio_split_space.blockSignals(False)
            self.rgb_radio_single_space.blockSignals(False)
            self.remap_radio_split_space.blockSignals(False)
            self.remap_radio_single_space.blockSignals(False)

            # Rebuild keyboard grids
            self.build_keyboard_grid(
                self.rgb_grid_layout,
                self.rgb_key_buttons,
                self.on_rgb_key_clicked,
                self.space_mode
            )
            self.build_keyboard_grid(
                self.remap_grid_layout,
                self.remap_key_buttons,
                self.on_remap_key_selected,
                self.space_mode
            )

            # Update selected key if necessary
            if self.space_mode == "split" and self.selected_remap_key == "Space_18":
                self.selected_remap_key = "LeftSpace"
            elif self.space_mode == "standard" and self.selected_remap_key in ["LeftSpace", "RightSpace"]:
                self.selected_remap_key = "Space_18"

            self.refresh_remap_ui()
            self.backend.save_profile()

    def reset_factory_mappings(self):
        reply = QMessageBox.question(
            self,
            "Potwierdzenie resetu",
            "Czy na pewno chcesz przywrócić fabryczne mapowanie klawiszy (Unmap)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.progress_bar.setVisible(True)
            self.lbl_bottom_info.setText("Resetowanie mapowań w klawiaturze...")
            self.backend.reset_keyboard_mapping()

    def apply_full_configuration(self):
        self.progress_bar.setVisible(True)
        self.btn_apply_all.setEnabled(False)
        self.lbl_bottom_info.setText("Programowanie pamięci klawiatury (Flash)...")
        self.backend.apply_current_configuration()

    def on_apply_finished(self, success: bool, msg: str):
        self.progress_bar.setVisible(False)
        self.btn_apply_all.setEnabled(True)
        self.lbl_bottom_info.setText(msg)
        if success:
            QMessageBox.information(self, "Sukces", msg)
        else:
            QMessageBox.warning(self, "Błąd wgrywania", msg)

    def on_unmap_finished(self, success: bool, msg: str):
        self.progress_bar.setVisible(False)
        self.lbl_bottom_info.setText(msg)
        self.refresh_remap_ui()
        if success:
            QMessageBox.information(self, "Reset Mapowania", msg)
        else:
            QMessageBox.warning(self, "Błąd", msg)

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
        self.category_combo.addItem("Wszystkie kategorie")
        for cat in categories:
            self.category_combo.addItem(cat)
        self.filter_effects()

    def filter_effects(self):
        query = self.effect_search_input.text().lower()
        selected_cat = self.category_combo.currentText()
        self.effects_list_widget.clear()

        for eff in self.all_effects:
            if selected_cat != "Wszystkie kategorie" and eff["category"] != selected_cat:
                continue
            if query and query not in eff["name"].lower():
                continue

            item = QListWidgetItem(f"[{eff['category']}]  {eff['name']}")
            item.setData(Qt.UserRole, eff["name"])
            self.effects_list_widget.addItem(item)

    def on_effect_double_clicked(self, item: QListWidgetItem):
        self.apply_selected_effect()

    def apply_selected_effect(self):
        item = self.effects_list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "Wybór", "Wybierz animację z listy!")
            return
        effect_name = item.data(Qt.UserRole)
        layer = self.rgb_layer_combo.currentText()
        self.backend.lighting_config = {
            "mode": "preset",
            "preset_name": effect_name,
            "layer": layer,
            "static_colors": self.current_key_colors
        }
        self.apply_full_configuration()

    def on_rgb_layer_changed(self):
        self.backend.lighting_config["layer"] = self.rgb_layer_combo.currentText()

    def open_color_dialog(self):
        col = QColorDialog.getColor(QColor(self.selected_brush_color), self, "Wybierz Kolor Pędzla")
        if col.isValid():
            self.set_brush_color(col.name())

    def set_brush_color(self, hex_color: str):
        self.selected_brush_color = hex_color
        self.brush_preview_btn.setStyleSheet(f"background-color: {hex_color}; border-radius: 4px;")

    def on_rgb_key_clicked(self, key_id: str):
        if key_id in self.rgb_key_buttons:
            self.rgb_key_buttons[key_id].set_color(self.selected_brush_color)
            self.current_key_colors[key_id] = self.selected_brush_color

    def paint_zone(self, zone_id: str):
        for kid, btn in self.rgb_key_buttons.items():
            match = False
            if zone_id == "all":
                match = True
            elif zone_id == btn.group:
                match = True
            elif zone_id == "alpha" and btn.group in ["alpha", "wasd"]:
                match = True

            if match:
                btn.set_color(self.selected_brush_color)
                self.current_key_colors[kid] = self.selected_brush_color

    def apply_preset_theme(self, theme_name: str):
        theme = COLOR_PRESETS.get(theme_name)
        if not theme:
            return

        for kid, btn in self.rgb_key_buttons.items():
            color = theme.get(btn.group, theme.get("all", "#000000"))
            btn.set_color(color)
            self.current_key_colors[kid] = color

    def apply_static_keyboard_colors(self):
        layer = self.rgb_layer_combo.currentText()
        self.backend.lighting_config = {
            "mode": "static",
            "layer": layer,
            "static_colors": self.current_key_colors
        }
        self.apply_full_configuration()

    def turn_off_led(self):
        self.backend.lighting_config = {
            "mode": "off",
            "layer": self.rgb_layer_combo.currentText(),
            "static_colors": self.current_key_colors
        }
        self.apply_full_configuration()

    # =========================================================================
    # REMAP & KNOB LOGIC
    # =========================================================================
    def on_remap_layer_changed(self):
        self.current_remap_layer = self.remap_layer_combo.currentData()
        self.refresh_remap_ui()

    def refresh_remap_ui(self):
        # Update macro dropdown in remap inspector
        self.remap_macro_combo.clear()
        for m_name in self.backend.macros.keys():
            self.remap_macro_combo.addItem(f"Makro: {m_name}", f"Macro({m_name})")

        # Update visual keyboard buttons on current layer
        layer_remaps = self.backend.get_remaps_for_layer(self.current_remap_layer)
        for kid, btn in self.remap_key_buttons.items():
            action = layer_remaps.get(kid)
            btn.set_remap(action)
            btn.set_selected(kid == self.selected_remap_key)

        # Update knob action buttons on current layer
        for knob_info in KNOBS_METADATA:
            for act in knob_info["actions"]:
                aid = act["id"]
                btn = self.knob_action_buttons.get(aid)
                if btn:
                    assigned = layer_remaps.get(aid)
                    is_sel = (aid == self.selected_remap_key)
                    if assigned:
                        btn.setText(f"{act['label']}: {assigned} ⚡")
                        btn.setStyleSheet("""
                            background-color: #1f3554;
                            border: 2px solid #7aa2f7;
                            color: #ffffff;
                            font-weight: bold;
                        """ if not is_sel else """
                            background-color: #3d59a1;
                            border: 2px solid #ff9eaf;
                            color: #ffffff;
                            font-weight: bold;
                        """)
                    else:
                        btn.setText(f"{act['label']}: [Domyślnie]")
                        btn.setStyleSheet("""
                            background-color: #24293e;
                            border: 1px solid #3b4261;
                            color: #c0caf5;
                        """ if not is_sel else """
                            background-color: #3d59a1;
                            border: 2px solid #ff9eaf;
                            color: #ffffff;
                            font-weight: bold;
                        """)

        # Update remapped table
        self.remap_table.setRowCount(0)
        for row_idx, (src, dst) in enumerate(layer_remaps.items()):
            self.remap_table.insertRow(row_idx)

            # Friendly readable source name
            src_desc = self._get_friendly_key_name(src)
            self.remap_table.setItem(row_idx, 0, QTableWidgetItem(src_desc))
            self.remap_table.setItem(row_idx, 1, QTableWidgetItem(dst))

            btn_del = QPushButton("Usuń")
            btn_del.clicked.connect(lambda _, k=src: self.delete_remap_from_table(k))
            self.remap_table.setCellWidget(row_idx, 2, btn_del)

    def _get_friendly_key_name(self, key_id: str) -> str:
        if key_id == "LeftSpace":
            return "Lewa Spacja (Left Space)"
        elif key_id == "RightSpace":
            return "Prawa Spacja (Right Space)"
        elif key_id in ["Space_18", "StandardSpace", "Space"]:
            return "Standardowa Spacja (Space)"

        for k_info in KNOBS_METADATA:
            for act in k_info["actions"]:
                if act["id"] == key_id:
                    return f"{k_info['name']} — {act['label']}"

        for kdef in KEY_DEFINITIONS:
            if kdef["id"] == key_id:
                return f"{kdef['label']} ({kdef['id']})"

        return key_id

    def on_remap_key_selected(self, key_id: str):
        self.selected_remap_key = key_id

        # Update keyboard buttons selection
        for kid, btn in self.remap_key_buttons.items():
            btn.set_selected(kid == key_id)

        # Update knob buttons selection
        for aid, btn in self.knob_action_buttons.items():
            btn_sel = (aid == key_id)
            layer_remaps = self.backend.get_remaps_for_layer(self.current_remap_layer)
            assigned = layer_remaps.get(aid)
            if btn_sel:
                btn.setStyleSheet("background-color: #3d59a1; border: 2px solid #ff9eaf; color: #ffffff; font-weight: bold;")
            elif assigned:
                btn.setStyleSheet("background-color: #1f3554; border: 2px solid #7aa2f7; color: #ffffff; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: #24293e; border: 1px solid #3b4261; color: #c0caf5;")

        friendly_name = self._get_friendly_key_name(key_id)
        self.lbl_selected_remap_key.setText(f"Edytowany element: [ {friendly_name} ]")

    def on_knob_preset_applied(self, knob_id: str, combo: QComboBox):
        preset_name = combo.currentData()
        if not preset_name:
            return

        scheme = KNOB_PRESETS.get(preset_name)
        if not scheme:
            return

        # Map the 3 actions for this knob on the current layer
        if knob_id == "Knob1":
            self.backend.set_key_remap(self.current_remap_layer, "Knob1_CW", scheme["CW"])
            self.backend.set_key_remap(self.current_remap_layer, "Knob1_CCW", scheme["CCW"])
            self.backend.set_key_remap(self.current_remap_layer, "Knob1_Click", scheme["Click"])
        elif knob_id == "Knob2":
            self.backend.set_key_remap(self.current_remap_layer, "Knob2_CW", scheme["CW"])
            self.backend.set_key_remap(self.current_remap_layer, "Knob2_CCW", scheme["CCW"])
            self.backend.set_key_remap(self.current_remap_layer, "Knob2_Click", scheme["Click"])
        elif knob_id == "Knob3":
            self.backend.set_key_remap(self.current_remap_layer, "Knob3_CW", scheme["CW"])
            self.backend.set_key_remap(self.current_remap_layer, "Knob3_CCW", scheme["CCW"])
            self.backend.set_key_remap(self.current_remap_layer, "Knob3_Click", scheme["Click"])
        elif knob_id == "Knob4":
            self.backend.set_key_remap(self.current_remap_layer, "Knob4_CW", scheme["CW"])
            self.backend.set_key_remap(self.current_remap_layer, "Knob4_CCW", scheme["CCW"])
            self.backend.set_key_remap(self.current_remap_layer, "Knob4_Click", scheme["Click"])
        elif knob_id == "Knob5":
            self.backend.set_key_remap(self.current_remap_layer, "Knob5_CW", scheme["CW"])
            self.backend.set_key_remap(self.current_remap_layer, "Knob5_CCW", scheme["CCW"])
            self.backend.set_key_remap(self.current_remap_layer, "Knob5_Click", scheme["Click"])
        elif knob_id == "Knob6":
            self.backend.set_key_remap(self.current_remap_layer, "Knob6_Click", scheme["Click"])

        combo.setCurrentIndex(0)
        self.refresh_remap_ui()
        self.lbl_bottom_info.setText(f"Zastosowano schemat '{preset_name}' dla {knob_id} na warstwie {self.current_remap_layer}.")

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

    def assign_selected_remap_action(self):
        if not self.selected_remap_key:
            QMessageBox.warning(self, "Brak elementu", "Kliknij najpierw klawisz lub akcję pokrętła!")
            return

        mode_idx = self.remap_mode_tabs.currentIndex()
        target_action = ""

        if mode_idx == 0:
            # Single key
            target_action = self.std_key_combo.currentData()
        elif mode_idx == 1:
            # Combination
            mods = []
            if self.chk_ctrl.isChecked():
                mods.append("LCtrl")
            if self.chk_shift.isChecked():
                mods.append("LShift")
            if self.chk_alt.isChecked():
                mods.append("LAlt")
            if self.chk_win.isChecked():
                mods.append("LWin")

            base_k = self.combo_base_key.currentData()
            if mods:
                target_action = "+".join(mods) + "+" + base_k
            else:
                target_action = base_k
        elif mode_idx == 2:
            # Macro
            target_action = self.remap_macro_combo.currentData()

        if target_action:
            self.backend.set_key_remap(self.current_remap_layer, self.selected_remap_key, target_action)
            self.refresh_remap_ui()
            friendly_src = self._get_friendly_key_name(self.selected_remap_key)
            self.lbl_bottom_info.setText(f"Przypisano {target_action} do {friendly_src} na {self.current_remap_layer}.")

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
            "Czyszczenie warstwy",
            f"Czy na pewno chcesz usunąć wszystkie mapowania na warstwie {self.current_remap_layer}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.backend.clear_layer_remaps(self.current_remap_layer)
            self.refresh_remap_ui()

    # =========================================================================
    # MACRO STUDIO LOGIC
    # =========================================================================
    def refresh_macro_list_ui(self):
        self.macro_list_widget.blockSignals(True)
        self.macro_list_widget.clear()

        for m_name in self.backend.macros.keys():
            item = QListWidgetItem(f"⚡ {m_name}")
            item.setData(Qt.UserRole, m_name)
            self.macro_list_widget.addItem(item)

        self.macro_list_widget.blockSignals(False)

        if not self.current_macro_name and self.backend.macros:
            self.current_macro_name = list(self.backend.macros.keys())[0]

        if self.current_macro_name:
            for idx in range(self.macro_list_widget.count()):
                item = self.macro_list_widget.item(idx)
                if item.data(Qt.UserRole) == self.current_macro_name:
                    self.macro_list_widget.setCurrentItem(item)
                    break
            self.load_macro_to_editor(self.current_macro_name)

    def on_macro_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if current:
            macro_name = current.data(Qt.UserRole)
            self.current_macro_name = macro_name
            self.load_macro_to_editor(macro_name)

    def load_macro_to_editor(self, macro_name: str):
        macro = self.backend.macros.get(macro_name)
        if not macro:
            return

        self.macro_name_input.blockSignals(True)
        self.macro_delay_spin.blockSignals(True)
        self.macro_repeat_combo.blockSignals(True)
        self.macro_repeat_count_spin.blockSignals(True)

        self.macro_name_input.setText(macro.name)
        self.macro_delay_spin.setValue(macro.default_delay)

        idx = self.macro_repeat_combo.findData(macro.repeat_type)
        if idx >= 0:
            self.macro_repeat_combo.setCurrentIndex(idx)
        self.macro_repeat_count_spin.setValue(macro.repeat_count)

        self.macro_name_input.blockSignals(False)
        self.macro_delay_spin.blockSignals(False)
        self.macro_repeat_combo.blockSignals(False)
        self.macro_repeat_count_spin.blockSignals(False)

        self.refresh_macro_actions_table()

    def refresh_macro_actions_table(self):
        if not self.current_macro_name or self.current_macro_name not in self.backend.macros:
            self.macro_actions_table.setRowCount(0)
            return

        macro = self.backend.macros[self.current_macro_name]
        self.macro_actions_table.setRowCount(0)

        for row_idx, act in enumerate(macro.actions):
            self.macro_actions_table.insertRow(row_idx)

            type_item = QTableWidgetItem(act.action_type)
            type_item.setTextAlignment(Qt.AlignCenter)
            self.macro_actions_table.setItem(row_idx, 0, type_item)

            key_item = QTableWidgetItem(act.key)
            self.macro_actions_table.setItem(row_idx, 1, key_item)

            delay_spin = QSpinBox()
            delay_spin.setRange(0, 5000)
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

        macro.default_delay = self.macro_delay_spin.value()
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
            QMessageBox.warning(self, "Brak makra", "Wybierz lub utwórz najpierw makro!")
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

    def delete_current_macro(self):
        if not self.current_macro_name or self.current_macro_name not in self.backend.macros:
            return

        reply = QMessageBox.question(
            self,
            "Usunięcie makra",
            f"Czy na pewno chcesz bezpowrotnie usunąć makro '{self.current_macro_name}'?",
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
            QMessageBox.warning(self, "Brak tekstu", "Wpisz tekst do wygenerowania makra!")
            return

        if not self.current_macro_name or self.current_macro_name not in self.backend.macros:
            self.create_new_macro()

        actions = self.backend.text_to_macro_actions(text, char_delay=20)
        macro = self.backend.macros[self.current_macro_name]
        macro.actions.extend(actions)
        self.backend.save_profile()
        self.quick_text_input.clear()
        self.refresh_macro_actions_table()
        QMessageBox.information(self, "Wygenerowano", f"Dodano {len(actions)} naciśnięć klawiszy do makra {self.current_macro_name}!")

    # =========================================================================
    # DEBUG & PROFILE PERSISTENCE
    # =========================================================================
    def refresh_debug_code_view(self):
        code = self.backend.generate_full_config()
        self.debug_code_text.setPlainText(code)

    def export_profile_json(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Zapisz profil", "gk104_profile.json", "JSON (*.json)")
        if fname:
            self.backend.save_profile(fname)
            QMessageBox.information(self, "Eksport", f"Zapisano profil do: {fname}")

    def import_profile_json(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Wczytaj profil", "", "JSON (*.json)")
        if fname and os.path.exists(fname):
            self.backend.load_profile(fname)
            self.space_mode = getattr(self.backend, "space_mode", "split")
            self.build_keyboard_grid(
                self.rgb_grid_layout,
                self.rgb_key_buttons,
                self.on_rgb_key_clicked,
                self.space_mode
            )
            self.build_keyboard_grid(
                self.remap_grid_layout,
                self.remap_key_buttons,
                self.on_remap_key_selected,
                self.space_mode
            )
            self.refresh_remap_ui()
            self.refresh_macro_list_ui()
            QMessageBox.information(self, "Import", f"Wczytano profil z: {fname}")

    # =========================================================================
    # BRIGHTNESS & KNOB HELPERS
    # =========================================================================
    def on_brightness_slider_changed(self, value: int):
        self.lbl_brightness_val.setText(f"Jasność: {value}%")
        self.backend.lighting_config["brightness"] = value

    def set_brightness_level(self, value: int):
        self.brightness_slider.setValue(value)
        self.lbl_brightness_val.setText(f"Jasność: {value}%")
        self.backend.set_brightness(value, auto_apply=True)
        self.lbl_bottom_info.setText(f"Ustawiono jasność: {value}% i wgrano do klawiatury.")

    def apply_brightness_now(self):
        val = self.brightness_slider.value()
        self.backend.set_brightness(val, auto_apply=True)
        self.lbl_bottom_info.setText(f"Wgrywanie jasności {val}% do klawiatury...")

    def copy_knobs_to_all_layers(self):
        """Copy rotary knob configurations from active layer to all standard layers."""
        src_layer_remaps = self.backend.get_remaps_for_layer(self.current_remap_layer)
        knob_action_ids = [act["id"] for k_info in KNOBS_METADATA for act in k_info["actions"]]

        copied_count = 0
        for lid, _ in AVAILABLE_LAYERS:
            if lid in ["Base", "Layer1", "Layer2", "Layer3"]:
                if lid not in self.backend.remaps:
                    self.backend.remaps[lid] = {}
                for aid in knob_action_ids:
                    if aid in src_layer_remaps:
                        self.backend.remaps[lid][aid] = src_layer_remaps[aid]
                        copied_count += 1
                    elif aid in self.backend.remaps[lid]:
                        del self.backend.remaps[lid][aid]

        self.backend.save_profile()
        self.refresh_remap_ui()
        QMessageBox.information(
            self,
            "Pokrętła Skopiowane",
            f"Pomyślnie zsynchronizowano ustawienia pokręteł z warstwy '{self.current_remap_layer}' "
            f"na wszystkie warstwy (Base, Layer 1, Layer 2, Layer 3).\n\n"
            f"Teraz pokrętła będą działać tak samo na każdym profilu klawiatury!"
        )

    # =========================================================================
    # SYSTEM TRAY CONTROLLER & BATTERY MONITORING
    # =========================================================================
    def init_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        app_icon = QIcon.fromTheme("input-keyboard")
        if app_icon.isNull():
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("#7aa2f7"))
            app_icon = QIcon(pixmap)
        self.tray_icon.setIcon(app_icon)
        self.tray_icon.setToolTip("Skyloong GK104 Pro Studio")

        # Tray Context Menu
        self.tray_menu = QMenu()

        self.tray_title_action = QAction("⌨️ Skyloong GK104 Pro Studio", self)
        self.tray_title_action.setEnabled(False)
        self.tray_menu.addAction(self.tray_title_action)

        self.tray_battery_action = QAction("🔋 Bateria: Sprawdzanie...", self)
        self.tray_battery_action.setEnabled(False)
        self.tray_menu.addAction(self.tray_battery_action)

        self.tray_menu.addSeparator()

        # Brightness Submenu
        bright_menu = self.tray_menu.addMenu("💡 Jasność Podświetlenia")
        for b_val, b_label in [
            (100, "🌕 100% (Maksymalna)"),
            (75, "🌖 75%"),
            (50, "🌗 50%"),
            (25, "🌘 25%"),
            (0, "🌑 Wyłącz LED (0%)")
        ]:
            act = QAction(b_label, self)
            act.triggered.connect(lambda _, v=b_val: self.on_tray_brightness_selected(v))
            bright_menu.addAction(act)

        # Quick Presets Submenu
        preset_menu = self.tray_menu.addMenu("🌈 Szybki Profil RGB")
        for p_name in ["Spectral Cycle", "Rainbow Streamer", "Breathing", "Cyberpunk 2077", "Matrix Green", "Ice Blizzard"]:
            act = QAction(p_name, self)
            act.triggered.connect(lambda _, pn=p_name: self.on_tray_preset_selected(pn))
            preset_menu.addAction(act)

        act_off = QAction("🌙 Wyłącz podświetlenie", self)
        act_off.triggered.connect(self.turn_off_led)
        preset_menu.addAction(act_off)

        # Profile / Layer Submenu
        layer_menu = self.tray_menu.addMenu("🔀 Warstwa Klawiatury")
        for lid, lname in AVAILABLE_LAYERS[:4]:
            act = QAction(lname, self)
            act.triggered.connect(lambda _, l=lid: self.on_tray_layer_selected(l))
            layer_menu.addAction(act)

        self.tray_menu.addSeparator()

        self.tray_show_action = QAction("🖥️ Pokaż / Ukryj okno", self)
        self.tray_show_action.triggered.connect(self.toggle_window_visibility)
        self.tray_menu.addAction(self.tray_show_action)

        act_apply = QAction("💾 Wgraj bieżącą konfigurację", self)
        act_apply.triggered.connect(self.apply_full_configuration)
        self.tray_menu.addAction(act_apply)

        self.tray_menu.addSeparator()

        act_exit = QAction("🚪 Zakończ program", self)
        act_exit.triggered.connect(QApplication.instance().quit)
        self.tray_menu.addAction(act_exit)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

        # Background status timer (updates every 4 seconds)
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh_system_status)
        self.status_timer.start(4000)
        self.refresh_system_status()

    def refresh_system_status(self):
        """Update battery and connection status on both main window and tray."""
        try:
            bat_info = get_system_battery_info()
            if bat_info["has_battery"]:
                bat_text = f"{bat_info['icon']} Bateria: {bat_info['percentage']}% ({bat_info['status']})"
                self.lbl_battery_header.setText(bat_text)
                self.tray_battery_action.setText(bat_text)
                tooltip = f"Skyloong GK104 Pro Studio\n{bat_text}"
            else:
                self.lbl_battery_header.setText("🔌 Zasilanie sieciowe")
                self.tray_battery_action.setText("🔌 Zasilanie sieciowe (Brak baterii)")
                tooltip = "Skyloong GK104 Pro Studio\nZasilanie sieciowe"

            current_bright = self.backend.lighting_config.get("brightness", 100)
            tooltip += f"\n💡 Jasność RGB: {current_bright}%"
            self.tray_icon.setToolTip(tooltip)
        except Exception as e:
            print(f"Error in refresh_system_status: {e}")

    def on_tray_brightness_selected(self, value: int):
        self.set_brightness_level(value)
        self.tray_icon.showMessage(
            "Jasność Klawiatury",
            f"Ustawiono jasność podświetlenia na {value}%",
            QSystemTrayIcon.Information,
            1500
        )

    def on_tray_preset_selected(self, preset_name: str):
        if preset_name in COLOR_PRESETS:
            self.apply_preset_theme(preset_name)
            self.apply_static_keyboard_colors()
        else:
            self.backend.set_lighting_preset(preset_name, layer="Base", auto_apply=True)
        self.tray_icon.showMessage(
            "Profil RGB",
            f"Zastosowano profil '{preset_name}'",
            QSystemTrayIcon.Information,
            1500
        )

    def on_tray_layer_selected(self, layer_id: str):
        idx = self.remap_layer_combo.findData(layer_id)
        if idx >= 0:
            self.remap_layer_combo.setCurrentIndex(idx)
        self.tray_icon.showMessage(
            "Warstwa Klawiatury",
            f"Wybrano warstwę: {layer_id}",
            QSystemTrayIcon.Information,
            1500
        )

    def toggle_window_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()

    def on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.toggle_window_visibility()

    def closeEvent(self, event):
        """Minimize to tray instead of quitting on window close."""
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "Skyloong Studio działa w tle",
                "Aplikacja została zminimalizowana do zasobnika systemowego KDE. Kliknij ikonę, aby ją otworzyć.",
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()
        else:
            event.accept()
