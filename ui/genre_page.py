# genre_page.py
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QPushButton, QSizePolicy, QGridLayout,
    QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QPainterPath, QLinearGradient, QPixmap
)

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_DARK, BLUE_LIGHT,
    WHITE, TEXT_DARK, TEXT_MUTED, CARD_RADIUS
)
from .widgets import _CARD_MIN_W, _CARD_MAX_W, _PAD


def _force_bg(widget, hex_color, radius=0):
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    r = f"border-radius: {radius}px;" if radius else ""
    widget.setStyleSheet(f"background: {hex_color}; {r}")


# ══════════════════════════════════════════════════════════════════════
#  LOADER
# ══════════════════════════════════════════════════════════════════════

class GenrePageLoader(QThread):
    """Load manga list + all genre stats for a user."""
    finished = pyqtSignal(list, dict, str)  # manga_list, genre_counts, selected_genre

    def __init__(self, user_id: int, genre: str):
        super().__init__()
        self.user_id = user_id
        self.genre = genre

    def run(self):
        manga_list = []
        genre_counts = {}
        genre_display = self.genre

        try:
            from database import get_session
            from models.manga import Manga
            from models.user_collection import UserCollection

            session = get_session()
            try:
                # ── 1. Ambil SEMUA manga user untuk hitung statistik genre ──
                all_rows = (
                    session.query(Manga)
                    .join(UserCollection, UserCollection.manga_id == Manga.id)
                    .filter(UserCollection.user_id == self.user_id)
                    .all()
                )

                for manga in all_rows:
                    genres = self._parse_genres(manga.genres or "")
                    for g in genres:
                        genre_counts[g] = genre_counts.get(g, 0) + 1

                # ── 2. Ambil manga dengan genre yang dipilih ──
                rows = (
                    session.query(Manga)
                    .join(UserCollection, UserCollection.manga_id == Manga.id)
                    .filter(
                        UserCollection.user_id == self.user_id,
                        Manga.genres.like(f"%{self.genre}%")
                    )
                    .all()
                )

                for manga in rows:
                    genres = self._parse_genres(manga.genres or "")
                    manga_list.append({
                        "id": manga.id,
                        "title": manga.title,
                        "cover_url": manga.cover_url or "",
                        "genres": genres,
                        "score": manga.score or 0,
                        "status": manga.status or "?",
                    })

                # Sort by score descending
                manga_list.sort(key=lambda x: x["score"], reverse=True)

            finally:
                session.close()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[GenrePage] Error: {e}")

        # Sort genre_counts by count descending
        genre_counts = dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True))

        self.finished.emit(manga_list, genre_counts, genre_display)

    @staticmethod
    def _parse_genres(raw: str) -> list:
        if not raw:
            return []
        if raw.startswith("["):
            try:
                return json.loads(raw)
            except:
                return [g.strip() for g in raw.strip("[]").split(",")]
        return [g.strip() for g in raw.split(",") if g.strip()]


# ══════════════════════════════════════════════════════════════════════
#  GENRE BAR CHART (Kanan)
# ══════════════════════════════════════════════════════════════════════

class GenreBarChart(QWidget):
    """Horizontal bar chart showing genre distribution."""
    clicked_genre = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}         # {genre: count}
        self._selected = ""     # genre yang sedang aktif
        self._bar_rects = []    # simpan posisi bar untuk deteksi klik
        self.setMinimumWidth(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)  # untuk hover effect

    def set_data(self, counts: dict, selected_genre: str = ""):
        self._data = counts if counts else {}
        self._selected = selected_genre
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        total = sum(self._data.values())
        max_count = max(self._data.values()) if self._data else 1

        if not self._data:
            painter.setPen(QColor(TEXT_MUTED))
            font = QFont("Segoe UI", 11)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data")
            return

        # Layout
        padding_t = 20
        padding_b = 20
        bar_h = 28
        gap = 10
        total_items = len(self._data)
        available_h = h - padding_t - padding_b
        # Scrollable area logic — we draw all bars, let parent ScrollArea handle overflow
        start_y = padding_t

        self._bar_rects = []  # reset

        for i, (genre, count) in enumerate(self._data.items()):
            y = start_y + i * (bar_h + gap)

            # Skip if out of visible area (optional optimization)
            if y + bar_h < 0 or y > h:
                continue

            bar_w = max(8, int((w - 130) * count / max_count))  # leave space for label

            # Bar gradient
            bar_rect = QRectF(0, y, bar_w, bar_h)
            grad = QLinearGradient(bar_rect.topLeft(), bar_rect.topRight())
            if genre == self._selected:
                grad.setColorAt(0, QColor(BLUE_PRIMARY))
                grad.setColorAt(1, QColor("#64B5F6"))
            else:
                grad.setColorAt(0, QColor(BLUE_CARD))
                grad.setColorAt(1, QColor(BLUE_LIGHT))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.addRoundedRect(bar_rect, 14, 14)
            painter.drawPath(path)

            # Genre label ON the bar
            painter.setPen(QColor(WHITE) if genre == self._selected else QColor(TEXT_DARK))
            font = QFont("Segoe UI", 10, QFont.Weight.Bold)
            painter.setFont(font)
            label_rect = QRectF(10, y, bar_w - 20, bar_h)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, genre)

            # Count label NEXT to bar
            painter.setPen(QColor(TEXT_DARK))
            font = QFont("Segoe UI", 11, QFont.Weight.Bold)
            painter.setFont(font)
            count_text = f"{count}"
            painter.drawText(
                QRectF(bar_w + 8, y, 50, bar_h),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                count_text
            )

            # Manga count small text
            if total > 0:
                pct = count / total * 100
                painter.setPen(QColor(TEXT_MUTED))
                font = QFont("Segoe UI", 9)
                painter.setFont(font)
                painter.drawText(
                    QRectF(bar_w + 55, y, 70, bar_h),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    f"({pct:.0f}%)"
                )

            # Save rect for click detection
            self._bar_rects.append((QRectF(0, y, w, bar_h), genre))

        # Update widget height hint based on content
        total_height = start_y + total_items * (bar_h + gap) + padding_b
        if total_height != self.minimumHeight():
            self.setMinimumHeight(max(total_height, 200))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            for rect, genre in self._bar_rects:
                if rect.contains(pos):
                    self.clicked_genre.emit(genre)
                    break
        super().mousePressEvent(event)


# ══════════════════════════════════════════════════════════════════════
#  MANGA CARD SMALL (Kiri)
# ══════════════════════════════════════════════════════════════════════

class MangaCardSmall(QWidget):
    """Compact manga card for genre listing."""
    clicked = pyqtSignal(int)

    def __init__(self, manga_data: dict, parent=None):
        super().__init__(parent)
        self.manga_id = manga_data.get("id", 0)
        self.setFixedSize(130, 210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"background: {BLUE_CARD}; border-radius: 10px;")

        # Force black text via QPalette — overrides APP_STYLESHEET inheritance
        from PyQt6.QtGui import QPalette, QColor
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.WindowText, QColor("#111111"))
        pal.setColor(QPalette.ColorRole.Text, QColor("#111111"))
        self.setPalette(pal)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Cover image
        self.cover = QLabel()
        self.cover.setFixedSize(114, 150)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setScaledContents(True)
        self.cover.setStyleSheet(
            "background: rgba(255,255,255,0.15); border-radius: 6px;"
        )
        layout.addWidget(self.cover, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title
        title = manga_data.get("title", "—")
        if len(title) > 18:
            title = title[:16] + "…"
        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_pal = title_lbl.palette()
        title_pal.setColor(QPalette.ColorRole.WindowText, QColor("#111111"))
        title_lbl.setPalette(title_pal)
        title_lbl.setStyleSheet("font-size: 10px; font-weight: 700; background: transparent;")
        layout.addWidget(title_lbl)

        # Score badge
        score = manga_data.get("score", 0)
        if score:
            score_lbl = QLabel(f"★ {score:.1f}")
            score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            score_pal = score_lbl.palette()
            score_pal.setColor(QPalette.ColorRole.WindowText, QColor("#F5C518"))
            score_lbl.setPalette(score_pal)
            score_lbl.setStyleSheet("font-size: 9px; font-weight: 600; background: transparent;")
            layout.addWidget(score_lbl)

        layout.addStretch()

        # Load cover image
        cover_url = manga_data.get("cover_url", "")
        if cover_url:
            from .widgets import ImageLoader
            self._img_loader = ImageLoader(str(cover_url))
            self._img_loader.loaded.connect(self._on_cover)
            self._img_loader.start()

    def _on_cover(self, pixmap):
        self.cover.setPixmap(
            pixmap.scaled(
                114, 150,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.manga_id)
        super().mousePressEvent(event)


# ══════════════════════════════════════════════════════════════════════
#  GENRE PAGE
# ══════════════════════════════════════════════════════════════════════

class GenrePage(QWidget):
    """Page: Grid manga (left) + Genre bar chart (right)."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._current_genre = ""
        self._loader = None
        self._manga_list = []
        self._cards = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──
        topbar = QWidget()
        topbar.setFixedHeight(60)
        topbar.setAttribute(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.WidgetAttribute.WA_StyledBackground, True)
        topbar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7aaee0,stop:0.5 #80d9e8,stop:1 #b5dfa0);")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 24, 0)
        tb.setSpacing(12)

        # Back button
        self._back_btn = QPushButton("←")
        self._back_btn.setFixedSize(36, 36)
        self._back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.20);
                color: {WHITE};
                border: none;
                border-radius: 18px;
                font-size: 18px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.35);
            }}
        """)
        self._back_btn.clicked.connect(self._go_back)
        tb.addWidget(self._back_btn)

        # Title
        self._title_lbl = QLabel("Genre")
        self._title_lbl.setStyleSheet(
            f"color: {WHITE}; font-size: 18px; font-weight: 700; background: transparent;"
        )
        tb.addWidget(self._title_lbl)

        # Count subtitle
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: rgba(255,255,255,0.75); font-size: 12px; background: transparent;"
        )
        tb.addWidget(self._count_lbl)
        tb.addStretch()
        root.addWidget(topbar)

        # ── Info banner ──
        self._info_banner = QLabel("Showing all scraped manga with this genre")
        self._info_banner.setStyleSheet(f"""
            QLabel {{
                background: rgba(196,181,222,0.22);
                color: {TEXT_DARK};
                font-size: 11px;
                padding: 6px 16px;
                border: none;
            }}
        """)
        self._info_banner.setVisible(False)
        root.addWidget(self._info_banner)

        # ── Main content: Splitter (Grid kiri | Chart kanan) ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: #E0E0E0; width: 2px; }")
        splitter.setChildrenCollapsible(False)

        # ── LEFT: Manga grid in scroll area ──
        self._left_scroll = QScrollArea()
        left_scroll = self._left_scroll
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setStyleSheet("background: transparent; border: none;")

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background: transparent;")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(24, 24, 12, 24)
        self._grid_layout.setSpacing(14)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        left_scroll.setWidget(self._grid_container)
        splitter.addWidget(left_scroll)

        # ── RIGHT: Genre bar chart in scroll area ──
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setStyleSheet("background: transparent; border: none;")

        right_container = QWidget()
        right_container.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(16, 24, 24, 24)
        right_layout.setSpacing(8)

        # Chart title
        chart_title = QLabel("Genre Distribution")
        chart_title.setStyleSheet(
            f"color: {BLUE_PRIMARY}; font-size: 14px; font-weight: 700; background: transparent;"
        )
        right_layout.addWidget(chart_title)

        # Bar chart
        self._bar_chart = GenreBarChart()
        self._bar_chart.clicked_genre.connect(self._on_bar_clicked)
        right_layout.addWidget(self._bar_chart, stretch=1)

        right_scroll.setWidget(right_container)
        splitter.addWidget(right_scroll)

        # Set initial sizes: 60% left, 40% right
        splitter.setSizes([600, 400])

        root.addWidget(splitter, stretch=1)

    def load_genre(self, genre: str):
        """Load manga for a specific genre."""
        self._current_genre = genre
        self._title_lbl.setText(genre)
        self._count_lbl.setText("Loading...")
        self._info_banner.setVisible(True)

        # Clear existing cards
        self._clear_grid()

        # Start loader
        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()

        uid = self.main_window.current_user["id"]
        self._loader = GenrePageLoader(user_id=uid, genre=genre)
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    @pyqtSlot(list, dict, str)
    def _on_loaded(self, manga_list, genre_counts, genre_name):
        self._manga_list = manga_list
        self._count_lbl.setText(f"• {len(manga_list)} manga")
        self._clear_grid()

        self._bar_chart.set_data(genre_counts, selected_genre=genre_name)

        if not manga_list:
            empty = QLabel(f'No manga found with genre "{genre_name}".')
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; background: transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid_layout.addWidget(empty, 0, 0, 1, 4)
            return

        self._display_cards()

        from PyQt6.QtCore import QTimer
        QTimer.singleShot(150, self._relayout)

    def _get_cols(self):
        vw = self._left_scroll.viewport().width() - 4
        if vw < 50:
            vw = self.width() - 320
        if vw < 50:
            vw = 700
        spacing = self._grid_layout.spacing()
        for cols in [6, 5, 4, 3, 2, 1]:
            if vw >= cols * 110 + spacing * (cols - 1):
                return cols, vw
        return 1, vw

    def _display_cards(self):
        self._clear_grid()
        self._cards = []

        from .widgets import MangaCard
        from types import SimpleNamespace

        cols, container_width = self._get_cols()
        spacing = self._grid_layout.spacing()
        card_w = min(_CARD_MAX_W, max(_CARD_MIN_W, (container_width - spacing * (cols - 1)) // cols))
        cover_w = card_w - _PAD * 2

        for i, manga_data in enumerate(self._manga_list):
            manga_obj = SimpleNamespace(
                id=manga_data.get("id", 0),
                title=manga_data.get("title", "—"),
                cover_url=manga_data.get("cover_url", ""),
                genres=", ".join(manga_data.get("genres", [])) if isinstance(manga_data.get("genres"), list) else manga_data.get("genres", ""),
                score=manga_data.get("score", 0),
                status=manga_data.get("status", ""),
            )
            card = MangaCard(manga_obj, show_labels=True)
            card.clicked.connect(self.main_window.go_detail)
            card.setFixedWidth(card_w)
            if hasattr(card, "lbl_title"):
                card.lbl_title.setMaximumWidth(cover_w)
                card.lbl_title.setStyleSheet(
                    card.lbl_title.styleSheet() + " color: #111111;"
                )
            if hasattr(card, "lbl_genre"):
                card.lbl_genre.setMaximumWidth(cover_w)
                card.lbl_genre.setStyleSheet(
                    card.lbl_genre.styleSheet() + " color: #555555;"
                )
            if hasattr(card, "lbl_score"):
                card.lbl_score.setStyleSheet(
                    card.lbl_score.styleSheet() + " color: #111111;"
                )
            self._cards.append(card)
            self._grid_layout.addWidget(card, i // cols, i % cols)

    def _relayout(self):
        widgets = []
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                widgets.append(item.widget())
        if not widgets:
            return

        if hasattr(self, '_left_scroll') and self._left_scroll:
            vp_w = self._left_scroll.viewport().width()
            if vp_w > 10:
                self._grid_container.setFixedWidth(vp_w)

        cols, container_width = self._get_cols()
        spacing = self._grid_layout.spacing()
        card_w = min(_CARD_MAX_W, max(_CARD_MIN_W, (container_width - spacing * (cols - 1)) // cols))
        cover_w = card_w - _PAD * 2

        for i, widget in enumerate(widgets):
            widget.setFixedWidth(card_w)
            if hasattr(widget, "lbl_title"):
                widget.lbl_title.setMaximumWidth(cover_w)
            if hasattr(widget, "lbl_genre"):
                widget.lbl_genre.setMaximumWidth(cover_w)
            self._grid_layout.addWidget(widget, i // cols, i % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_left_scroll') and self._left_scroll:
            vp_w = self._left_scroll.viewport().width()
            if vp_w > 10:
                self._grid_container.setFixedWidth(vp_w)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self._relayout)

    def showEvent(self, event):
        super().showEvent(event)
        # Force correct layout every time this page becomes visible
        from PyQt6.QtCore import QTimer
        if hasattr(self, '_left_scroll') and self._left_scroll:
            def _fix():
                vp_w = self._left_scroll.viewport().width()
                if vp_w > 10:
                    self._grid_container.setFixedWidth(vp_w)
                self._relayout()
            QTimer.singleShot(50, _fix)
            QTimer.singleShot(200, _fix)

            
    def _on_bar_clicked(self, genre: str):
        """When user clicks a bar in the chart, switch to that genre."""
        if genre != self._current_genre:
            self.load_genre(genre)

    def _clear_grid(self):
        """Remove all widgets from grid."""
        self._cards = []
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _go_back(self):
        """Navigate back to dashboard."""
        if hasattr(self.main_window, 'go_dashboard'):
            self.main_window.go_dashboard()
