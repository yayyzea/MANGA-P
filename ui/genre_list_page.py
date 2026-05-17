from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QPushButton, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QPainterPath, QLinearGradient, QPixmap
)

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_LIGHT,
    WHITE, TEXT_DARK, TEXT_MUTED, CARD_RADIUS
)


def _force_bg(widget, hex_color, radius=0):
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    r = f"border-radius: {radius}px;" if radius else ""
    widget.setStyleSheet(f"background: {hex_color}; {r}")


class GenreBarChart(QWidget):
    clicked_genre = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self._bar_rects = []
        self._hovered_genre = None
        self.setMinimumWidth(350)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    def set_data(self, counts: dict):
        self._data = counts if counts else {}
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        max_count = max(self._data.values()) if self._data else 1

        if not self._data:
            painter.setPen(QColor(TEXT_MUTED))
            font = QFont("Segoe UI", 11)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data")
            return

        padding_t = 24
        padding_b = 24
        bar_h = 30
        gap = 12
        start_y = padding_t
        
        label_width = 140
        count_width = 60
        bar_area_x = label_width + 12
        bar_area_w = w - label_width - count_width - 60
        
        self._bar_rects = []

        for i, (genre, count) in enumerate(self._data.items()):
            y = start_y + i * (bar_h + gap)

            if y + bar_h < 0 or y > h:
                continue

            bar_w = max(4, int(bar_area_w * count / max_count))
            
            # Label genre di kiri (selalu kebaca)
                        # Label genre di kiri (align left, selalu kebaca)
            painter.setPen(QColor(TEXT_DARK))
            font = QFont("Segoe UI", 10, QFont.Weight.Bold)
            painter.setFont(font)
            display_name = genre
            if len(display_name) > 16:
                display_name = display_name[:14] + "…"
            painter.drawText(
                8, int(y), label_width - 8, bar_h,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                display_name
            )
            
            # Bar
            bar_rect = QRectF(bar_area_x, y + 2, bar_w, bar_h - 4)
            grad = QLinearGradient(bar_rect.topLeft(), bar_rect.topRight())
            if genre == self._hovered_genre:
                grad.setColorAt(0, QColor("#5BA4E6"))
                grad.setColorAt(1, QColor("#82C4F8"))
            else:
                grad.setColorAt(0, QColor(BLUE_PRIMARY))
                grad.setColorAt(1, QColor(BLUE_LIGHT))
            painter.setBrush(QBrush(grad))

            if genre == self._hovered_genre:
                painter.setPen(QPen(QColor(WHITE), 2))
            else:
                painter.setPen(Qt.PenStyle.NoPen)

            path = QPainterPath()
            path.addRoundedRect(bar_rect, 6, 6)
            painter.drawPath(path)

            # Count + persentase di kanan bar
            painter.setPen(QColor(TEXT_DARK))
            font = QFont("Segoe UI", 11, QFont.Weight.Bold)
            painter.setFont(font)
            count_x = bar_area_x + bar_w + 10
            painter.drawText(
                int(count_x), int(y), count_width, bar_h,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                str(count)
            )

            total = sum(self._data.values())
            if total > 0:
                pct = count / total * 100
                painter.setPen(QColor(TEXT_MUTED))
                font = QFont("Segoe UI", 9)
                painter.setFont(font)
                painter.drawText(
                    int(count_x + 40), int(y), 60, bar_h,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    f"({pct:.1f}%)"
                )

            # Simpan full row rect untuk deteksi klik
            full_rect = QRectF(0, y, w, bar_h)
            self._bar_rects.append((full_rect, genre))

        total_height = start_y + len(self._data) * (bar_h + gap) + padding_b
        if total_height != self.minimumHeight():
            self.setMinimumHeight(max(total_height, 300))

    def mouseMoveEvent(self, event):
        pos = event.position()
        new_hover = None
        for rect, genre in self._bar_rects:
            if rect.contains(pos):
                new_hover = genre
                break

        if new_hover != self._hovered_genre:
            self._hovered_genre = new_hover
            self.update()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._hovered_genre:
            self.clicked_genre.emit(self._hovered_genre)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if self._data:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._hovered_genre = None
        self.update()
        super().leaveEvent(event)

class ScrapedGenreLoader(QThread):
    finished = pyqtSignal(list, str)

    def __init__(self, genre: str):
        super().__init__()
        self.genre = genre

    def run(self):
        results = []
        genre_display = self.genre

        try:
            from database import get_session
            from models.manga import Manga

            session = get_session()
            try:
                rows = (
                    session.query(Manga)
                    .filter(
                        Manga.genres.like(f"%{self.genre}%")
                    )
                    .all()
                )

                for manga in rows:
                    results.append({
                        "id": manga.id,
                        "title": manga.title,
                        "cover_url": manga.cover_url or "",
                        "score": manga.score or 0,
                        "genres": manga.genres or "",
                        "status": manga.status or "?",
                    })

                results.sort(key=lambda x: x["score"], reverse=True)

            finally:
                session.close()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[ScrapedGenre] Error loading genre '{self.genre}': {e}")

        self.finished.emit(results, genre_display)


class MangaCardCompact(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, manga_data: dict, parent=None):
        super().__init__(parent)
        self.manga_id = manga_data.get("id", 0)
        self.setFixedSize(130, 210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        _force_bg(self, BLUE_CARD, radius=10)

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
            f"color: {WHITE}; font-size: 10px; font-weight: 700; background: transparent;"
        )
        title_lbl.setWordWrap(True)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        score = manga_data.get("score", 0)
        if score:
            score_lbl = QLabel(f"★ {score:.1f}")
            score_lbl.setStyleSheet(
                f"color: rgba(255,255,255,0.85); font-size: 9px; font-weight: 600; background: transparent;"
            )
            score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(score_lbl)

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


class ScrapedGenrePage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._loader = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

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

        self._title_lbl = QLabel("Genre")
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

        info_banner = QLabel("📊  Showing all scraped manga with this genre")
        info_banner.setStyleSheet(f"""
            QLabel {{
                background: {BLUE_LIGHT};
                color: {TEXT_DARK};
                font-size: 11px;
                padding: 6px 16px;
                border: none;
            }}
        """)
        root.addWidget(info_banner)

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

    def load_genre(self, genre: str):
        self._title_lbl.setText(genre)
        self._count_lbl.setText("Loading...")
        self._clear_grid()

        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()

        self._loader = ScrapedGenreLoader(genre=genre)
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    @pyqtSlot(list, str)
    def _on_loaded(self, manga_list, genre_name):
        self._count_lbl.setText(f"• {len(manga_list)} manga")
        self._clear_grid()

        if not manga_list:
            empty = QLabel(f'No manga found with genre "{genre_name}".')
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; background: transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid_layout.addWidget(empty, 0, 0, 1, 4)
            return

        container_width = self.width() - 48
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
        if hasattr(self.main_window, 'go_genre_list'):
            self.main_window.go_genre_list(self.main_window.genre_list_page._genre_counts)


class GenreListPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._genre_counts = {}
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

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

        title = QLabel("Most Genre")
        title.setStyleSheet(
            f"color: {WHITE}; font-size: 18px; font-weight: 700; background: transparent;"
        )
        tb.addWidget(title)
        tb.addStretch()
        root.addWidget(topbar)

        info_banner = QLabel("🔥  Distribution of genres across all scraped manga")
        info_banner.setStyleSheet(f"""
            QLabel {{
                background: {BLUE_LIGHT};
                color: {TEXT_DARK};
                font-size: 11px;
                padding: 8px 16px;
                border: none;
            }}
        """)
        root.addWidget(info_banner)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(8)

        chart_title = QLabel("Genre Distribution")
        chart_title.setStyleSheet(
            f"color: {BLUE_PRIMARY}; font-size: 16px; font-weight: 700; background: transparent;"
        )
        layout.addWidget(chart_title)

        self._bar_chart = GenreBarChart()
        self._bar_chart.clicked_genre.connect(self._on_genre_clicked)
        layout.addWidget(self._bar_chart, stretch=1)

        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

    def load_data(self, genre_counts: dict, top_genre: str = None):
        self._genre_counts = genre_counts
        self._bar_chart.set_data(genre_counts)

    def _on_genre_clicked(self, genre: str):
        if hasattr(self.main_window, 'go_scraped_genre'):
            self.main_window.go_scraped_genre(genre)

    def _go_back(self):
        if hasattr(self.main_window, 'go_home'):
            self.main_window.go_home()