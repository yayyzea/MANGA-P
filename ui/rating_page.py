# rating_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QPushButton, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap, QColor

from .theme import (
    SKY_BLUE, TEAL, DEWY_GREEN, PETAL_PINK, LILAC_MIST,
    BLUE_PRIMARY, BLUE_CARD, BLUE_LIGHT,
    WHITE, TEXT_DARK, TEXT_MUTED, CARD_RADIUS
)


def _force_bg(widget, hex_color, radius=0):
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    r = f"border-radius: {radius}px;" if radius else ""
    widget.setStyleSheet(f"background: {hex_color}; {r}")


class RatingPageLoader(QThread):
    finished = pyqtSignal(list, int)

    def __init__(self, user_id: int, rating: int):
        super().__init__()
        self.user_id = user_id
        self.rating = rating

    def run(self):
        results = []
        rating_display = self.rating

        try:
            from database import get_session
            from models.manga import Manga
            from models.review import Review
            from models.user_collection import UserCollection

            session = get_session()
            try:
                rows = (
                    session.query(Manga)
                    .join(Review, Review.manga_id == Manga.id)
                    .join(UserCollection, UserCollection.manga_id == Manga.id)
                    .filter(
                        Review.user_id == self.user_id,
                        UserCollection.user_id == self.user_id,
                        Review.rating == self.rating
                    )
                    .all()
                )

                for manga in rows:
                    review = (
                        session.query(Review)
                        .filter(
                            Review.user_id == self.user_id,
                            Review.manga_id == manga.id
                        )
                        .first()
                    )
                    results.append({
                        "id": manga.id,
                        "title": manga.title,
                        "cover_url": manga.cover_url or "",
                        "score": manga.score or 0,
                        "rating": self.rating,
                        "review_text": review.review_text if review else "",
                    })

                results.sort(key=lambda x: x["score"], reverse=True)

            finally:
                session.close()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[RatingPage] Error loading rating {self.rating}: {e}")

        self.finished.emit(results, rating_display)


class RatingBadge(QLabel):
    def __init__(self, rating: int, parent=None):
        super().__init__(parent)
        self.setText(f"★ {rating}/10")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                color: #f5c842;
                font-size: 10px;
                font-weight: 700;
                background: rgba(255,255,255,0.12);
                border-radius: 6px;
                padding: 2px 8px;
            }
        """)


class MangaCardCompact(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, manga_data: dict, parent=None):
        super().__init__(parent)
        self.manga_id = manga_data.get("id", 0)
        self.setFixedSize(130, 210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        _force_bg(self, '#DCF0F7', radius=10)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.cover = QLabel()
        self.cover.setFixedSize(114, 150)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setScaledContents(True)
        self.cover.setStyleSheet("background: rgba(255,255,255,0.15); border-radius: 6px;")
        layout.addWidget(self.cover, alignment=Qt.AlignmentFlag.AlignCenter)

        title = manga_data.get("title", "—")
        if len(title) > 18:
            title = title[:16] + "…"
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "color: #111111; font-size: 10px; font-weight: 700; background: transparent;"
        )
        title_lbl.setWordWrap(True)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        rating = manga_data.get("rating", 0)
        badge = RatingBadge(rating)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

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


class RatingPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._current_rating = 0
        self._loader = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QWidget()
        topbar.setFixedHeight(60)
        topbar.setAttribute(__import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.WidgetAttribute.WA_StyledBackground, True)
        topbar.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #006ec4, stop:0.55 #2cb5d3, stop:1 #f96a67);")
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

        self._stars_header = RatingBadge(0)
        self._stars_header.setStyleSheet("""
            QLabel {
                color: #f5c842;
                font-size: 16px;
                font-weight: 700;
                background: rgba(255,255,255,0.18);
                border-radius: 10px;
                padding: 4px 14px;
            }
        """)
        tb.addWidget(self._stars_header)

        self._title_lbl = QLabel("")
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

    def load_rating(self, rating: int):
        self._current_rating = rating
        self._stars_header.setText(f"★ {rating}/10")
        self._title_lbl.setText("")
        self._count_lbl.setText("Loading...")
        self._clear_grid()

        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()

        uid = self.main_window.current_user["id"]
        self._loader = RatingPageLoader(user_id=uid, rating=rating)
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    @pyqtSlot(list, int)
    def _on_loaded(self, manga_list, rating_val):
        self._count_lbl.setText(f"• {len(manga_list)} manga")
        self._clear_grid()

        if not manga_list:
            empty = QLabel(f'No manga rated {rating_val}/10.')
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; background: transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid_layout.addWidget(empty, 0, 0, 1, 4)
            return

        container_width = self._grid_container.width() - 24
        card_w = 130
        spacing = 14
        cols = max(1, (container_width + spacing) // (card_w + spacing))

        for i, manga in enumerate(manga_list):
            card = MangaCardCompact(manga)
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