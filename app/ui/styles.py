"""
Centralized UI styles for SnapSight.
Provides a cohesive, modern dark theme.
"""

MODERN_DARK_THEME = """
/* Global */
QWidget {
    background-color: #1E1E1E;
    color: #E0E0E0;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

/* Headers */
h2 {
    color: #FFFFFF;
    font-size: 20px;
    font-weight: 600;
}
h3 {
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 600;
}

/* Cards (QFrame) */
QFrame.Card {
    background-color: #252526;
    border: 1px solid #333333;
    border-radius: 8px;
}

/* Buttons */
QPushButton {
    background-color: #333333;
    color: #FFFFFF;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #444444;
    border: 1px solid #555555;
}
QPushButton:pressed {
    background-color: #222222;
}
QPushButton:focus {
    border: 1px solid #00A6FF;
    outline: none;
}
QPushButton:disabled {
    background-color: #2A2A2A;
    color: #777777;
    border: 1px solid #333333;
}
QPushButton.Primary {
    background-color: #007ACC;
    color: #FFFFFF;
    border: 1px solid #005A9E;
}
QPushButton.Primary:hover {
    background-color: #0098FF;
    border: 1px solid #007ACC;
}
QPushButton.Primary:pressed {
    background-color: #005A9E;
}
QPushButton.Primary:focus {
    border: 1px solid #66C2FF;
    outline: none;
}
QPushButton.Primary:disabled {
    background-color: #2A2A2A;
    color: #777777;
    border: 1px solid #333333;
}

/* Text Inputs */
QTextEdit {
    background-color: #2D2D30;
    color: #E0E0E0;
    border: 1px solid #3E3E42;
    border-radius: 4px;
    padding: 8px;
    selection-background-color: #264F78;
}
QTextEdit:focus {
    border: 1px solid #007ACC;
}

/* Labels */
QLabel {
    background-color: transparent;
}
QLabel.Title {
    font-size: 22px;
    font-weight: bold;
    color: #FFFFFF;
}
QLabel.Subtitle {
    font-size: 13px;
    color: #AAAAAA;
}
QLabel.Metadata {
    font-size: 11px;
    color: #888888;
}
QLabel.StatusGreen {
    color: #4CAF50;
    font-weight: bold;
}
QLabel.StatusOrange {
    color: #FF9800;
    font-weight: bold;
}
QLabel.PreviewEmpty {
    background-color: #2D2D30;
    border: 1px dashed #444444;
    border-radius: 6px;
    color: #888888;
    font-size: 14px;
}
QLabel.PreviewImage {
    background-color: transparent;
    border: none;
}

/* Splitters */
QSplitter::handle {
    background-color: transparent;
}
QSplitter::handle:horizontal {
    width: 12px;
}
QSplitter::handle:vertical {
    height: 12px;
}
"""
