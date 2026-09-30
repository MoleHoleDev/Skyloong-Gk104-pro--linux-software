DARK_THEME = """
QWidget {
    background-color: #1a1b26;
    color: #c0caf5;
    font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', sans-serif;
    font-size: 13px;
}

/* Main Window */
QMainWindow {
    background-color: #16161e;
}

/* Header & Card Containers */
QFrame#headerFrame {
    background-color: #1f2335;
    border-radius: 12px;
    border: 1px solid #292e42;
    padding: 12px;
}

QFrame#cardFrame {
    background-color: #1f2335;
    border-radius: 10px;
    border: 1px solid #292e42;
    padding: 10px;
}

QFrame#keyMapContainer {
    background-color: #13141c;
    border-radius: 12px;
    border: 1px solid #24283b;
    padding: 14px;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #292e42;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: bold;
    color: #7aa2f7;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #292e42;
    background-color: #1a1b26;
    border-radius: 10px;
    top: -1px;
}

QTabBar::tab {
    background-color: #1f2335;
    color: #a9b1d6;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
    border: 1px solid #292e42;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #7aa2f7;
    color: #15161e;
}

QTabBar::tab:hover:!selected {
    background-color: #292e42;
    color: #c0caf5;
}

/* Buttons */
QPushButton {
    background-color: #24283b;
    color: #c0caf5;
    border: 1px solid #414868;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2f354f;
    border-color: #7aa2f7;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #7aa2f7;
    color: #15161e;
}

QPushButton:disabled {
    background-color: #1a1b26;
    color: #565f89;
    border-color: #24283b;
}

QPushButton#primaryBtn {
    background-color: #7aa2f7;
    color: #15161e;
    border: 1px solid #7aa2f7;
    font-size: 13px;
    padding: 9px 18px;
    border-radius: 8px;
}

QPushButton#primaryBtn:hover {
    background-color: #89b4fa;
    border-color: #89b4fa;
}

QPushButton#primaryBtn:pressed {
    background-color: #3d59a1;
    color: #c0caf5;
}

QPushButton#dangerBtn {
    background-color: #f7768e;
    color: #15161e;
    border: 1px solid #f7768e;
    font-weight: bold;
}

QPushButton#dangerBtn:hover {
    background-color: #ff9eaf;
}

QPushButton#successBtn {
    background-color: #9ece6a;
    color: #15161e;
    border: 1px solid #9ece6a;
    font-weight: bold;
}

QPushButton#successBtn:hover {
    background-color: #b9f27c;
}

/* Key Button in Visualizer */
QPushButton.keyboardKey {
    background-color: #24283b;
    color: #c0caf5;
    border: 1px solid #3b4261;
    border-radius: 5px;
    font-size: 10px;
    font-weight: bold;
    padding: 0px;
    margin: 1px;
}

QPushButton.keyboardKey:hover {
    border: 2px solid #7aa2f7;
}

/* Preset Buttons */
QPushButton.presetChip {
    background-color: #1f2335;
    border: 1px solid #3b4261;
    border-radius: 14px;
    padding: 5px 12px;
    font-size: 12px;
}

QPushButton.presetChip:checked {
    background-color: #7aa2f7;
    color: #15161e;
    border-color: #7aa2f7;
}

/* Labels */
QLabel {
    color: #c0caf5;
}

QLabel#titleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #7aa2f7;
}

QLabel#subtitleLabel {
    font-size: 12px;
    color: #7982a9;
}

QLabel#statusBadgeConnected {
    background-color: #1e3a29;
    color: #9ece6a;
    border: 1px solid #9ece6a;
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: bold;
}

QLabel#statusBadgeDisconnected {
    background-color: #3b2229;
    color: #f7768e;
    border: 1px solid #f7768e;
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: bold;
}

/* Input & Search */
QLineEdit, QSpinBox, QTextEdit, QPlainTextEdit {
    background-color: #16161e;
    border: 1px solid #3b4261;
    border-radius: 8px;
    padding: 7px 10px;
    color: #c0caf5;
}

QLineEdit:focus, QSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #7aa2f7;
}

/* Checkbox & Radio */
QCheckBox, QRadioButton {
    color: #c0caf5;
    spacing: 8px;
    font-weight: 500;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #3b4261;
    border-radius: 4px;
    background-color: #16161e;
}

QRadioButton::indicator {
    border-radius: 9px;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #7aa2f7;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #7aa2f7;
    border-color: #7aa2f7;
}

/* List Widget & Table Widget */
QListWidget, QTableWidget {
    background-color: #16161e;
    border: 1px solid #292e42;
    border-radius: 8px;
    padding: 4px;
    color: #c0caf5;
    gridline-color: #292e42;
}

QHeaderView::section {
    background-color: #1f2335;
    color: #7aa2f7;
    padding: 6px;
    border: 1px solid #292e42;
    font-weight: bold;
}

QListWidget::item, QTableWidget::item {
    padding: 6px 10px;
    border-radius: 5px;
    margin-bottom: 2px;
}

QListWidget::item:hover, QTableWidget::item:hover {
    background-color: #24283b;
    color: #7aa2f7;
}

QListWidget::item:selected, QTableWidget::item:selected {
    background-color: #3d59a1;
    color: #ffffff;
    font-weight: bold;
}

/* Combo Box */
QComboBox {
    background-color: #1f2335;
    border: 1px solid #3b4261;
    border-radius: 8px;
    padding: 6px 12px;
    color: #c0caf5;
}

QComboBox:hover {
    border-color: #7aa2f7;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid #3b4261;
}

QComboBox QAbstractItemView {
    background-color: #1f2335;
    border: 1px solid #3b4261;
    selection-background-color: #3d59a1;
    color: #c0caf5;
}

/* ScrollBar */
QScrollBar:vertical {
    border: none;
    background: #16161e;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #3b4261;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #7aa2f7;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #16161e;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #3b4261;
    border-radius: 4px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #7aa2f7;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Knob Cards & Controls */
QFrame#knobCard {
    background-color: #1a1e2e;
    border-radius: 10px;
    border: 1px solid #2d354b;
    padding: 8px;
}

QFrame#knobCard:hover {
    border: 1px solid #7aa2f7;
}

QPushButton.knobActionButton {
    background-color: #24293e;
    border: 1px solid #3b4261;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 11px;
    text-align: left;
    color: #c0caf5;
}

QPushButton.knobActionButton:hover {
    background-color: #2f3652;
    border: 1px solid #7aa2f7;
    color: #ffffff;
}

QPushButton.knobActionButtonSelected {
    background-color: #3d59a1;
    border: 2px solid #ff9eaf;
    color: #ffffff;
    font-weight: bold;
}
"""
