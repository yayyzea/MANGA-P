from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from .theme import BLUE_PRIMARY, BLUE_CARD, WHITE, CARD_RADIUS


class AboutPage(QWidget):
    """About page — matches the mockup (title + blue description card)."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 32)
        root.setSpacing(24)

        # Back button
        back = QPushButton("‹‹")
        back.setFixedSize(40, 32)
        back.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {BLUE_PRIMARY};
                font-size: 18px;
                font-weight: 700;
            }}
            QPushButton:hover {{ color: #0D47A1; }}
        """)
        back.clicked.connect(self.main_window.go_home)
        root.addWidget(back, alignment=Qt.AlignmentFlag.AlignLeft)

        # Title
        title = QLabel("ABOUT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 36px;
            font-weight: 800;
            color: #0D1B2A;
            background: transparent;
        """)
        root.addWidget(title)

        # Description card
        card = QWidget()
        card.setStyleSheet(f"""
            background: {BLUE_CARD};
            border-radius: {CARD_RADIUS}px;
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)

        desc = QLabel(
            "MANGA:P is a personal manga tracking desktop application "
            "designed to help you organize, discover, and review your manga collection. "
            "Search millions of titles from MyAnimeList, keep track of what you're reading, "
            "rate your favorites, and get recommendations based on your taste. "
            "All your data is stored locally — no account needed, no internet dependency "
            "once manga data is cached. Your library, your way."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(f"""
            color: {WHITE};
            font-size: 14px;
            line-height: 1.7;
            background: transparent;
        """)
        card_layout.addWidget(desc)
        root.addWidget(card)

        root.addStretch()
