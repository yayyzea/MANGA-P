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

# ── Bar Chart ────────────────────────────────────────────────────────────────

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

            painter.setPen(QColor(TEXT_DARK))
            font = QFont("Segoe UI", 10, QFont.Weight.Bold)
            painter.setFont(font)
            display_name = genre[:14] + "…" if len(genre) > 16 else genre
            painter.drawText(
                8, int(y), label_width - 8, bar_h,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                display_name
            )

            bar_rect = QRectF(bar_area_x, y + 2, bar_w, bar_h - 4)
            grad = QLinearGradient(bar_rect.topLeft(), bar_rect.topRight())
            if genre == self._hovered_genre:
                grad.setColorAt(0, QColor("#5BA4E6"))
                grad.setColorAt(1, QColor("#82C4F8"))
            else:
                grad.setColorAt(0, QColor(BLUE_PRIMARY))
                grad.setColorAt(1, QColor(BLUE_LIGHT))
            painter.setBrush(QBrush(grad))
            painter.setPen(QPen(QColor(WHITE), 2) if genre == self._hovered_genre else Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.addRoundedRect(bar_rect, 14, 14)
            painter.drawPath(path)

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

            self._bar_rects.append((QRectF(0, y, w, bar_h), genre))

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

class GenreCountLoader(QThread):
    """
    Query genre distribution + total manga count langsung dari DB.
    Filter hanya manga hasil scrape (is_manual == False).
    TIDAK melakukan request ke API apapun.
    """
    finished = pyqtSignal(dict, int)   # (genre_counts, total_manga)

    def run(self):
        try:
            from database import get_session
            from models.manga import Manga

            session = get_session()
            try:
                scraped_manga = (
                    session.query(Manga)
                    .filter(Manga.is_manual == False)
                    .all()
                )
                total = len(scraped_manga)

                genre_counts = {}
                for manga in scraped_manga:
                    if manga.genres:
                        for g in manga.genres.split(","):
                            g = g.strip()
                            if g:
                                genre_counts[g] = genre_counts.get(g, 0) + 1
            finally:
                session.close()

            genre_counts = dict(
                sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
            )
            self.finished.emit(genre_counts, total)
        except Exception as e:
            print(f"[GenreCountLoader] Error: {e}")
            self.finished.emit({}, 0)

# ── Scrape +100 worker ───────────────────────────────────────────────────────

class AddMangaWorker(QThread):
    """
    Scrape 100 manga berikutnya dari Jikan top/manga.
    Menentukan halaman mulai dari jumlah manga scraped yang sudah ada di DB.
    """
    progress = pyqtSignal(int)   # berapa yang sudah diambil di batch ini
    finished = pyqtSignal(int)   # total yang berhasil ditambahkan

    ADD_COUNT = 100
    PER_PAGE  = 25

    def run(self):
        try:
            from database import get_session
            from models.manga import Manga
            from services.jikan_service import JikanService
            from services.manga_service import MangaService
            import time

            session = get_session()
            jikan   = JikanService()
            svc     = MangaService()

            try:
                existing = (
                    session.query(Manga)
                    .filter(Manga.is_manual == False)
                    .count()
                )
                start_page = (existing // self.PER_PAGE) + 1

                added = 0
                page  = start_page

                while added < self.ADD_COUNT:
                    time.sleep(0.7)
                    resp = jikan._get("top/manga", params={
                        "limit": self.PER_PAGE,
                        "type":  "manga",
                        "page":  page,
                    })
                    if not resp or "data" not in resp or not resp["data"]:
                        break

                    raw_list = [jikan._clean_manga(item) for item in resp["data"]]
                    svc._bulk_upsert(raw_list, session)

                    added += len(raw_list)
                    page  += 1
                    self.progress.emit(min(added, self.ADD_COUNT))

                    if len(resp["data"]) < self.PER_PAGE:
                        break

            finally:
                session.close()

            self.finished.emit(min(added, self.ADD_COUNT))

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[AddMangaWorker] Fatal: {e}")
            self.finished.emit(0)

# ── ScrapedGenreLoader ────────────────────────────────────────────────────────

class ScrapedGenreLoader(QThread):
    finished = pyqtSignal(list, str)

    def __init__(self, genre: str):
        super().__init__()
        self.genre = genre

    def run(self):
        results = []
        try:
            from database import get_session
            from models.manga import Manga

            session = get_session()
            try:
                rows = (
                    session.query(Manga)
                    .filter(Manga.genres.like(f"%{self.genre}%"))
                    .all()
                )
                for manga in rows:
                    results.append({
                        "id":        manga.id,
                        "title":     manga.title,
                        "cover_url": manga.cover_url or "",
                        "score":     manga.score or 0,
                        "genres":    manga.genres or "",
                        "status":    manga.status or "?",
                    })
                results.sort(key=lambda x: x["score"], reverse=True)
            finally:
                session.close()
        except Exception as e:
            print(f"[ScrapedGenre] Error loading genre '{self.genre}': {e}")

        self.finished.emit(results, self.genre)

# ── MangaCardSmall ────────────────────────────────────────────────────────────

class MangaCardSmall(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, manga_data: dict, card_w: int = 140, parent=None):
        super().__init__(parent)
        self.manga_id = manga_data.get("id", 0)
        self._card_w   = card_w
        self._cover_h  = int(card_w * 1.4)
        self._total_h  = self._cover_h + 52
        self._inner_w  = card_w - 16
        self._hovered  = False
        self._pressed  = False

        self.setFixedSize(self._card_w, self._total_h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 6)
        layout.setSpacing(4)

        # Cover
        self.cover = QLabel()
        self.cover.setFixedSize(self._inner_w, self._cover_h)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setScaledContents(False)
        self.cover.setStyleSheet("background: rgba(0,0,0,0.08); border-radius: 6px;")
        layout.addWidget(self.cover)

        # Title
        title = manga_data.get("title", "—")
        self.lbl_title = QLabel()
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setMaximumWidth(self._inner_w)
        self.lbl_title.setMaximumHeight(36)
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet(
            "font-size: 12px; font-weight: 700; color: #111111; background: transparent;"
        )
        layout.addWidget(self.lbl_title)

        max_chars = 20
        display_title = title if len(title) <= max_chars else title[:max_chars] + "..."
        self.lbl_title.setText(display_title)

        # Score
        score = manga_data.get("score", 0)
        score_num = f"{float(score):.1f}" if score else "—"
        score_row = QWidget()
        score_row.setStyleSheet("background: transparent;")
        score_layout = QHBoxLayout(score_row)
        score_layout.setContentsMargins(0, 0, 0, 0)
        score_layout.setSpacing(2)
        score_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_star = QLabel("★")
        lbl_star.setStyleSheet("font-size: 12px; font-weight: 700; color: #F5C518; background: transparent;")
        self.lbl_score = QLabel(score_num)
        self.lbl_score.setStyleSheet("font-size: 12px; font-weight: 600; color: #111111; background: transparent;")
        score_layout.addWidget(lbl_star)
        score_layout.addWidget(self.lbl_score)
        layout.addWidget(score_row)

        # Load cover async
        cover_url = manga_data.get("cover_url", "")
        if cover_url:
            from .widgets import ImageLoader
            self._img_loader = ImageLoader(str(cover_url))
            self._img_loader.loaded.connect(
                lambda px: self._on_cover(px, self._inner_w, self._cover_h)
            )
            self._img_loader.start()

    def _on_cover(self, pixmap, w, h):
        try:
            if not self.cover or not self.isVisible():
                return
            self.cover.setPixmap(
                pixmap.scaled(w, h,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation)
            )
        except RuntimeError:
            pass

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPainterPath, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        if self._pressed:
            color = QColor("#B8DFF0")
        elif self._hovered:
            color = QColor("#B8DFF0")
        else:
            color = QColor(BLUE_CARD)
        painter.fillPath(path, color)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
            self.update()
            if self.rect().contains(event.pos()):
                self.clicked.emit(self.manga_id)
        super().mouseReleaseEvent(event)

# ── ScrapedGenrePage ──────────────────────────────────────────────────────────

class ScrapedGenrePage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._loader = None
        self._manga_list = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QWidget()
        topbar.setFixedHeight(60)
        topbar.setAttribute(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.WidgetAttribute.WA_StyledBackground, True)
        topbar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7aaee0,stop:0.5 #80d9e8,stop:1 #b5dfa0);")
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

        info_banner = QLabel("Showing all scraped manga with this genre")
        info_banner.setStyleSheet(f"""
            QLabel {{
                background: rgba(196,181,222,0.22);
                color: {TEXT_DARK};
                font-size: 11px;
                padding: 6px 16px;
                border: none;
            }}
        """)
        root.addWidget(info_banner)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("background: transparent; border: none;")

        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(16, 16, 16, 16)
        self._grid_layout.setSpacing(12)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self._scroll.setWidget(self._grid_container)
        root.addWidget(self._scroll, stretch=1)

    def load_genre(self, genre: str):
        self._title_lbl.setText(genre)
        self._count_lbl.setText("Loading...")
        self._manga_list = []
        self._clear_grid()

        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()

        self._loader = ScrapedGenreLoader(genre=genre)
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    def _get_cols_and_card_w(self):
        vw = self._scroll.viewport().width()
        if vw < 80:
            vw = self.width()
        if vw < 80:
            vw = 800
        spacing = self._grid_layout.spacing()
        margins = 32
        avail = vw - margins
        for cols in [8, 7, 6, 5, 4, 3, 2, 1]:
            card_w = (avail - spacing * (cols - 1)) // cols
            if card_w >= 110:
                return cols, int(card_w)
        return 1, int(avail)

    def _display_cards(self):
        self._clear_grid()
        if not self._manga_list:
            return

        cols, card_w = self._get_cols_and_card_w()
        for i, manga in enumerate(self._manga_list):
            card = MangaCardSmall(manga, card_w=card_w)
            card.clicked.connect(self.main_window.go_detail)
            self._grid_layout.addWidget(card, i // cols, i % cols)

    def _relayout(self):
        widgets = []
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                widgets.append(item.widget())
        if not widgets:
            return

        cols, card_w = self._get_cols_and_card_w()
        cover_h = int(card_w * 1.4)
        total_h = cover_h + 52
        inner_w = card_w - 16

        for i, widget in enumerate(widgets):
            widget.setFixedSize(card_w, total_h)
            if hasattr(widget, "cover"):
                widget.cover.setFixedSize(inner_w, cover_h)
            if hasattr(widget, "lbl_title"):
                widget.lbl_title.setMaximumWidth(inner_w)
            self._grid_layout.addWidget(widget, i // cols, i % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self._relayout)

    @pyqtSlot(list, str)
    def _on_loaded(self, manga_list, genre_name):
        self._manga_list = manga_list
        self._count_lbl.setText(f"• {len(manga_list)} manga")
        self._clear_grid()

        if not manga_list:
            empty = QLabel(f'No manga found with genre "{genre_name}".')
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; background: transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid_layout.addWidget(empty, 0, 0, 1, 4)
            return

        self._display_cards()

        from PyQt6.QtCore import QTimer
        QTimer.singleShot(150, self._relayout)

    def _clear_grid(self):
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _go_back(self):
        if hasattr(self.main_window, 'go_genre_list'):
            self.main_window.go_genre_list(self.main_window.genre_list_page._genre_counts)

# ── GenreListPage ─────────────────────────────────────────────────────────────

class GenreListPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window   = main_window
        self._genre_counts = {}
        self._total_manga  = 0
        self._loader       = None
        self._add_worker   = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Topbar ────────────────────────────────────────────────────────
        topbar = QWidget()
        topbar.setFixedHeight(60)
        topbar.setAttribute(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.WidgetAttribute.WA_StyledBackground, True)
        topbar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7aaee0,stop:0.5 #80d9e8,stop:1 #b5dfa0);")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 24, 0)
        tb.setSpacing(12)

        back_btn = QPushButton("←")
        back_btn.setFixedSize(36, 36)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.20);
                color: {WHITE}; border: none; border-radius: 18px;
                font-size: 18px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.35); }}
        """)
        back_btn.clicked.connect(self._go_back)
        tb.addWidget(back_btn)

        title_lbl = QLabel("Most Genre")
        title_lbl.setStyleSheet(
            f"color: {WHITE}; font-size: 18px; font-weight: 700; background: transparent;"
        )
        tb.addWidget(title_lbl)
        tb.addStretch()

        self._add_btn = QPushButton("＋ 100 Manga")
        self._add_btn.setFixedHeight(34)
        self._add_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.22);
                color: {WHITE}; border: none; border-radius: 17px;
                font-size: 12px; font-weight: 700;
                padding: 0 18px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.38); }}
            QPushButton:disabled {{
                background: rgba(255,255,255,0.08);
                color: rgba(255,255,255,0.35);
            }}
        """)
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(self._on_add_clicked)
        tb.addWidget(self._add_btn)

        root.addWidget(topbar)

        # ── Info banner + total counter ───────────────────────────────────
        banner_wrap = QWidget()
        banner_wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        banner_wrap.setStyleSheet(f"background: rgba(196,181,222,0.22);")
        brow = QHBoxLayout(banner_wrap)
        brow.setContentsMargins(16, 8, 16, 8)
        brow.setSpacing(0)

        self._banner_lbl = QLabel("Genre distribution from all scraped manga")
        self._banner_lbl.setStyleSheet(
            f"color: {TEXT_DARK}; font-size: 11px; background: transparent;"
        )
        brow.addWidget(self._banner_lbl)
        brow.addStretch()

        self._total_lbl = QLabel("— manga")
        self._total_lbl.setFixedHeight(26)
        self._total_lbl.setStyleSheet(f"""
            color: {BLUE_PRIMARY};
            font-size: 11px;
            font-weight: 700;
            background: white;
            border-radius: 13px;
            padding: 0px 14px;
        """)
        self._total_lbl.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._total_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brow.addWidget(self._total_lbl)

        root.addWidget(banner_wrap)

        # ── Status bar scrape (tersembunyi saat idle) ─────────────────────
        self._scrape_status = QLabel("")
        self._scrape_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scrape_status.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._scrape_status.setStyleSheet(f"""
            background: #E3F2FD;
            color: {BLUE_PRIMARY};
            font-size: 11px;
            font-weight: 600;
            padding: 5px 16px;
        """)
        self._scrape_status.setVisible(False)
        root.addWidget(self._scrape_status)

        # ── Chart ─────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        clayout = QVBoxLayout(container)
        clayout.setContentsMargins(32, 24, 32, 24)
        clayout.setSpacing(8)

        chart_title = QLabel("Genre Distribution")
        chart_title.setStyleSheet(
            f"color: {BLUE_PRIMARY}; font-size: 16px; font-weight: 700; background: transparent;"
        )
        clayout.addWidget(chart_title)

        self._bar_chart = GenreBarChart()
        self._bar_chart.clicked_genre.connect(self._on_genre_clicked)
        clayout.addWidget(self._bar_chart, stretch=1)

        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_data(self, genre_counts: dict = None, top_genre: str = None):
        """
        Dipanggil saat halaman dibuka (dari go_genre_list di main_window).
        Tampilkan data cache dulu jika ada, lalu query DB segar.
        Tidak ada scraping di sini.
        """
        if genre_counts:
            self._genre_counts = genre_counts
            self._bar_chart.set_data(genre_counts)

        self._load_from_db()

    # ── Internal ─────────────────────────────────────────────────────────────

    def _load_from_db(self):
        """Query genre distribution + total dari DB (background thread, tanpa scrape)."""
        if self._loader and self._loader.isRunning():
            return
        self._loader = GenreCountLoader()
        self._loader.finished.connect(self._on_counts_loaded)
        self._loader.start()

    @pyqtSlot(dict, int)
    def _on_counts_loaded(self, genre_counts: dict, total: int):
        self._total_manga = total
        self._total_lbl.setText(f"Total: {total:,} manga")

        if genre_counts:
            self._genre_counts = genre_counts
            self._bar_chart.set_data(genre_counts)

            # Sync ke HomePage agar MostGenreCard ikut terupdate
            if hasattr(self.main_window, 'home_page'):
                hp  = self.main_window.home_page
                hp._genre_counts = genre_counts
                top = list(genre_counts.keys())[0] if genre_counts else None
                if top:
                    hp._top_genre = top
                    hp._most_genre_card.set_genre(top)

    # ── Tombol + 100 Manga ────────────────────────────────────────────────────

    def _on_add_clicked(self):
        if self._add_worker and self._add_worker.isRunning():
            return

        self._add_btn.setEnabled(False)
        self._add_btn.setText("⏳ Scraping…")
        self._scrape_status.setText("⏳ Scraping 100 new manga from Jikan API…")
        self._scrape_status.setVisible(True)

        self._add_worker = AddMangaWorker()
        self._add_worker.progress.connect(self._on_add_progress)
        self._add_worker.finished.connect(self._on_add_finished)
        self._add_worker.start()

    @pyqtSlot(int)
    def _on_add_progress(self, count: int):
        self._scrape_status.setText(f"⏳  Scraping new manga… {count} / 100")

    @pyqtSlot(int)
    def _on_add_finished(self, count: int):
        self._add_btn.setEnabled(True)
        self._add_btn.setText("＋ 100 Manga")

        if count > 0:
            self._scrape_status.setText(
                f"✅  {count} Manga successfully added! Updating distribution…"
            )
            # Reload DB → update total counter + chart sekaligus
            self._load_from_db()
        else:
            self._scrape_status.setText("⚠  No new manga was successfully added.")

        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self._scrape_status.setVisible(False))

    # ── Navigasi ──────────────────────────────────────────────────────────────

    def _on_genre_clicked(self, genre: str):
        if hasattr(self.main_window, 'go_scraped_genre'):
            self.main_window.go_scraped_genre(genre)

    def _go_back(self):
        if hasattr(self.main_window, 'go_home'):
            self.main_window.go_home()