# status_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QPushButton, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_LIGHT,
    WHITE, TEXT_DARK, TEXT_MUTED, CARD_RADIUS
)


def _force_bg(widget, hex_color, radius=0):
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    r = f"border-radius: {radius}px;" if radius else ""
    widget.setStyleSheet(f"background: {hex_color}; {r}")


STATUS_COLORS = {
    "Plan to Read": "#29B6F6",
    "Reading":      "#1E90FF",
    "Completed":    "#43A047",
    "Dropped":      "#E53935",
}


class StatusPageLoader(QThread):
    """Load manga filtered by collection status."""
    finished = pyqtSignal(list, str)  # manga list, status name

    def __init__(self, user_id: int, status: str):
        super().__init__()
        self.user_id = user_id
        self.status = status

    def run(self):
        results = []
        status_display = self.status

        try:
            from database import get_session
            from models.manga import Manga
            from models.user_collection import UserCollection

            session = get_session()
            try:
                rows = (
                    session.query(Manga)
                    .join(UserCollection, UserCollection.manga_id == Manga.id)
                    .filter(
                        UserCollection.user_id == self.user_id,
                        UserCollection.status == self.status
                    )
                    .all()
                )

                for manga in rows:
                    results.append({
                        "id": manga.id,
                        "title": manga.title,
                        "cover_url": manga.cover_url or "",
                        "score": manga.score or 0,
                        "status": self.status,
                    })

                results.sort(key=lambda x: x["score"], reverse=True)

            finally:
                session.close()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[StatusPage] Error loading '{self.status}': {e}")

        self.finished.emit(results, status_display)


class MangaCardCompact(QWidget):
    """Compact manga card."""
    clicked = pyqtSignal(int)

    def __init__(self, manga_data: dict, accent_color: str, parent=None):
        super().__init__(parent)
        self.manga_id = manga_data.get("id", 0)
        self.setFixedSize(130, 210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        _force_bg(self, BLUE_CARD, radius=10)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Cover
        self.cover = QLabel()
        self.cover.setFixedSize(114, 150)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setScaledContents(True)
        self.cover.setStyleSheet(
            f"background: rgba(255,255,255,0.15); border-radius: 6px;"
        )
        layout.addWidget(self.cover, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title
        title = manga_data.get("title", "—")
        if len(title) > 18:
            title = title[:16] + "…"
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {WHITE}; font-size: 10px; font-weight: 700; background: transparent;"
        )
        title_lbl.setWordWrap(True)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        # Score
        score = manga_data.get("score", 0)
        if score:
            score_lbl = QLabel(f"★ {score:.1f}")
            score_lbl.setStyleSheet(
                f"color: rgba(255,255,255,0.85); font-size: 9px; font-weight: 600; background: transparent;"
            )
            score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(score_lbl)

        layout.addStretch()

        # Load cover
        cover_url = manga_data.get("cover_url", "")
        if cover_url:
            from .widgets import ImageLoader
            self._img_loader = ImageLoader(str(cover_url))
            self._img_loader.loaded.connect(self._on_cover)
            self._img_loader.start()

    def _on_cover(self, pixmap):
        self.cover.setPixmap(
            pixmap.scaled(114, 150,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.manga_id)
        super().mousePressEvent(event)


class StatusPage(QWidget):
    """Page showing manga filtered by collection status."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._current_status = ""
        self._loader = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──
        topbar = QWidget()
        topbar.setFixedHeight(60)
        _force_bg(topbar, BLUE_PRIMARY)
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 24, 0)
        tb.setSpacing(12)

        self._back_btn = QPushButton("←")
        self._back_btn.setFixedSize(36, 36)
        self._back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.20);
                color: {WHITE}; border: none; border-radius: 18px;
                font-size: 18px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.35); }}
        """)
        self._back_btn.clicked.connect(self._go_back)
        tb.addWidget(self._back_btn)

        # Status badge
        self._badge = QLabel("")
        self._badge.setFixedSize(14, 14)
        self._badge.setStyleSheet("border-radius: 7px;")
        tb.addWidget(self._badge)

        self._title_lbl = QLabel("Status")
        self._title_lbl.setStyleSheet(
            f"color: {WHITE}; font-size: 18px; font-weight: 700; background: transparent;"
        )
        tb.addWidget(self._title_lbl)

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: rgba(255,255,255,0.75); font-size: 12px; background: transparent;"
        )
        tb.addWidget(self._count_lbl)
        tb.addStretch()
        root.addWidget(topbar)

        # ── Grid scroll ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(24, 24, 24, 24)
        self._grid_layout.setSpacing(14)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self._grid_container)
        root.addWidget(scroll, stretch=1)

    def load_status(self, status: str):
        self._current_status = status
        accent = STATUS_COLORS.get(status, BLUE_PRIMARY)
        self._badge.setStyleSheet(f"background: {accent}; border-radius: 7px;")
        self._title_lbl.setText(status)
        self._count_lbl.setText("Loading...")
        self._clear_grid()

        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()

        uid = self.main_window.current_user["id"]
        self._loader = StatusPageLoader(user_id=uid, status=status)
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    @pyqtSlot(list, str)
    def _on_loaded(self, manga_list, status_name):
        self._count_lbl.setText(f"• {len(manga_list)} manga")
        self._clear_grid()

        if not manga_list:
            empty = QLabel(f'No manga with status "{status_name}".')
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; background: transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid_layout.addWidget(empty, 0, 0, 1, 4)
            return

        container_width = self._grid_container.width() - 24
        card_w = 130
        spacing = 14
        cols = max(1, (container_width + spacing) // (card_w + spacing))

        accent = STATUS_COLORS.get(status_name, BLUE_PRIMARY)
        for i, manga in enumerate(manga_list):
            card = MangaCardCompact(manga, accent)
            card.clicked.connect(self.main_window.go_detail)
            row, col = divmod(i, cols)
            self._grid_layout.addWidget(card, row, col, alignment=Qt.AlignmentFlag.AlignCenter)
            
    def _clear_grid(self):
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _go_back(self):
        if hasattr(self.main_window, 'go_dashboard'):
            self.main_window.go_dashboard()