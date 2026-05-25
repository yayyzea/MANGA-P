from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_LIGHT, WHITE, CARD_RADIUS, TEXT_DARK
)





class AboutPage(QWidget):
    """About page — 水のドレス palette with gradient card."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 32)
        root.setSpacing(28)

        # ── Title ──
        title = QLabel("ABOUT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 38px;
            font-weight: 1200;
            letter-spacing: 1px;
            color: {BLUE_PRIMARY};
            background: transparent;
        """)
        root.addWidget(title)

        # Thin colored divider
        divider = QLabel()
        divider.setFixedHeight(3)
        divider.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        divider.setStyleSheet(f"""
            background: {BLUE_PRIMARY};
            border-radius: 2px;
        """)
        root.addWidget(divider)
        root.addSpacing(8)

        # ── Gradient card ──
        card = QWidget()
        card.setObjectName("aboutCard")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setStyleSheet(f"""
            QWidget#aboutCard {{
                background: {BLUE_CARD};
                border-radius: {CARD_RADIUS}px;
                border: 1.5px solid {BLUE_LIGHT};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 40, 48, 40)

        desc = QLabel(
            "MANGA:P is a personal manga tracking desktop application "
            "designed to help you organize, discover, and review your manga collection. "
            "Search millions of titles from MyAnimeList, keep track of what you're reading, "
            "rate your favorites, and get recommendations based on your taste.\n\n"
            "All your data is stored locally — no account needed, no internet dependency "
            "once manga data is cached. Your library, your way."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("""
            color: rgba(0,0,0,0.75);
            font-size: 14px;
            line-height: 1.8;
            background: transparent;
            font-weight: 500;
        """)
        card_layout.addWidget(desc)


        root.addWidget(card)
        root.addStretch()