from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QPointF
from PyQt6.QtGui import QFont, QPixmap, QColor, QPalette, QIcon, QPainter, QPainterPath, QBrush, QPen
from pathlib import Path
_ICON_DIR = Path(__file__).parent.parent / "assets"

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_FOOTER, WHITE, BLUE_LIGHT,
    TEXT_DARK, TOPBAR_HEIGHT, CARD_W, CARD_H, CARD_RADIUS
)
from .widgets import MangaCard, ImageLoader, _CARD_MIN_W, _CARD_MAX_W, _ASPECT, _PAD
from .search_page import FilterPanel, SearchLoader


def _force_bg(widget, hex_color, radius=0):
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    r = f"border-radius: {radius}px;" if radius else ""
    widget.setStyleSheet(f"background: {hex_color}; {r}")


class WalkingCat(QWidget):
    SIZE  = 36
    SPEED = 2
    FRAMES = [0, 1, 2, 1]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(self.SIZE + 8)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")
        self._x     = 10.0
        self._dir   = 1
        self._frame = 0
        self._tick  = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(16)

    def _step(self):
        self._x += self.SPEED * self._dir
        self._tick += 1
        if self._tick % 8 == 0:
            self._frame = (self._frame + 1) % len(self.FRAMES)
        margin = self.SIZE + 10
        if self._x + self.SIZE > self.width() - margin:
            self._dir = -1
        elif self._x < margin:
            self._dir = 1
        self.update()

    def resizeEvent(self, event):
        self._x = max(0, min(self._x, max(0, self.width() - self.SIZE)))
        super().resizeEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        x, y, s = int(self._x), 4, self.SIZE
        f = self.FRAMES[self._frame]
        flip = (self._dir == -1)

        if flip:
            p.translate(x + s, y)
            p.scale(-1, 1)
        else:
            p.translate(x, y)

        body_col = QColor("#FFFFFF")
        line_col = QColor("#1A237E")
        nose_col = QColor("#FF8A65")

        pen = QPen(line_col, 2.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(QBrush(body_col))

        body = QPainterPath()
        body.addRoundedRect(4, 12, 22, 14, 6, 6)
        p.drawPath(body)

        head = QPainterPath()
        head.addEllipse(QPointF(15, 10), 9, 9)
        p.drawPath(head)

        for ex, ey in [(9, 4), (19, 4)]:
            p.drawLine(ex - 2, ey + 3, ex - 3, ey - 1)
            p.drawLine(ex - 2, ey + 3, ex + 1, ey)

        p.setBrush(QBrush(line_col))
        p.setPen(Qt.PenStyle.NoPen)
        if f == 2:
            p.setPen(QPen(line_col, 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(11, 10, 13, 10)
            p.drawLine(17, 10, 19, 10)
        else:
            p.drawEllipse(QPointF(12, 10), 1.5, 1.5)
            p.drawEllipse(QPointF(18, 10), 1.5, 1.5)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(nose_col))
        nose = QPainterPath()
        nose.moveTo(15, 13)
        nose.lineTo(13.5, 14.5)
        nose.lineTo(16.5, 14.5)
        nose.closeSubpath()
        p.drawPath(nose)

        p.setPen(QPen(line_col, 1))
        p.drawLine(6, 13, 12, 14)
        p.drawLine(6, 15, 12, 15)
        p.drawLine(18, 14, 24, 13)
        p.drawLine(18, 15, 24, 15)

        p.setPen(QPen(line_col, 2.2))
        p.setBrush(QBrush(body_col))
        leg_x_offsets = [0, 3, 0, -3]
        for i, (lx, ly) in enumerate([(7,26),(12,26),(17,26),(22,26)]):
            ox = leg_x_offsets[i] * (f % 2)
            leg = QPainterPath()
            leg.moveTo(lx, ly)
            leg.quadTo(lx, ly + 3, lx + ox, ly + 8)
            p.drawPath(leg)

        wag = [0, 5, 0, -5][self._frame]
        tail = QPainterPath()
        tail.moveTo(5, 18)
        tail.cubicTo(0, 14, -5 + wag, 8, -3 + wag, 4)
        p.setPen(QPen(line_col, 2.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(tail)
        p.end()


class TopMangaLoader(QThread):
    finished = pyqtSignal(list, dict)

    def run(self):
        try:
            from services.manga_service import MangaService
            from database import get_session
            from models.manga import Manga

            manga_list = MangaService().get_top_manga(limit=105)

            # Hitung genre_counts dari SEMUA manga di database tanpa filter apapun
            genre_counts = {}
            session = get_session()
            try:
                all_manga = session.query(Manga).all()
                for manga in all_manga:
                    if manga.genres:
                        for g in manga.genres.split(","):
                            g = g.strip()
                            if g:
                                genre_counts[g] = genre_counts.get(g, 0) + 1
            finally:
                session.close()

            genre_counts = dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True))
            top_genre = list(genre_counts.keys())[0] if genre_counts else None

            self.finished.emit(manga_list, {"top_genre": top_genre, "genre_counts": genre_counts})
        except Exception as e:
            print(f"[HomePage] Load error: {e}")
            self.finished.emit([], {})


class HistoryPanel(QWidget):
    manga_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HistoryPanel")
        self.setFixedWidth(220)
        self._loader   = None
        self._manga_id = None

        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(BLUE_CARD))
        self.setPalette(pal)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"border-radius: {CARD_RADIUS}px;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        hdr = QLabel("History")
        hdr.setStyleSheet(
            f"color: {WHITE}; font-size: 16px; font-weight: 700; background: transparent;"
        )
        layout.addWidget(hdr)

        self.cover_lbl = QLabel()
        self.cover_lbl.setFixedSize(190, 260)
        self.cover_lbl.setStyleSheet(
            "background: rgba(255,255,255,0.15); border-radius: 8px;"
        )
        self.cover_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.cover_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.title_lbl = QLabel("")
        self.title_lbl.setStyleSheet(
            f"color: {WHITE}; font-size: 14px; font-weight: 700; background: transparent;"
        )
        self.title_lbl.setWordWrap(True)
        layout.addWidget(self.title_lbl)

        self.desc_lbl = QLabel("")
        self.desc_lbl.setStyleSheet(
            f"color: rgba(255,255,255,0.88); font-size: 11px; background: transparent;"
        )
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setMaximumHeight(120)
        layout.addWidget(self.desc_lbl)

        layout.addStretch()

    def load_manga(self, manga):
        if not manga:
            return
        self._manga_id = manga.id
        self.title_lbl.setText(manga.title or "")
        synopsis = manga.synopsis or ""
        self.desc_lbl.setText(synopsis[:280] + ("…" if len(synopsis) > 280 else ""))
        if manga.cover_url:
            self._loader = ImageLoader(manga.cover_url)
            self._loader.loaded.connect(self._on_cover)
            self._loader.start()

    @pyqtSlot(QPixmap)
    def _on_cover(self, pixmap: QPixmap):
        scaled = pixmap.scaled(
            190, 260,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        self.cover_lbl.setPixmap(scaled)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._manga_id:
            self.manga_clicked.emit(self._manga_id)
        super().mousePressEvent(event)


class SearchBar(QWidget):
    search_triggered = pyqtSignal(str)
    filter_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SearchBar")
        self.setFixedHeight(TOPBAR_HEIGHT)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(BLUE_PRIMARY))
        self.setPalette(pal)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        icon = QLabel()
        icon.setFixedSize(20, 20)
        _sx = QPixmap(str(_ICON_DIR / "search.png"))
        if not _sx.isNull():
            icon.setPixmap(_sx.scaled(18, 18,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            icon.setText("🔍")
        icon.setStyleSheet("background: transparent;")
        layout.addWidget(icon)

        self.input = QLineEdit()
        self.input.setObjectName("SearchInput")
        self.input.setPlaceholderText("Search Mangas...")
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background: {WHITE}; border: none;
                border-radius: 20px; padding: 8px 16px;
                font-size: 14px; color: {TEXT_DARK};
            }}
        """)
        self.input.returnPressed.connect(self._on_search)
        layout.addWidget(self.input)

        self.filter_btn = QPushButton()
        self.filter_btn.setObjectName("FilterBtn")
        self.filter_btn.setFixedSize(36, 36)
        _fx = QPixmap(str(_ICON_DIR / "filter.png"))
        if not _fx.isNull():
            self.filter_btn.setIcon(QIcon(_fx))
            self.filter_btn.setIconSize(self.filter_btn.size() * 0.6)
        else:
            self.filter_btn.setText("⚙")
        self.filter_btn.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE}; border: none;
                border-radius: 18px; font-size: 16px; color: {BLUE_PRIMARY};
            }}
            QPushButton:hover {{ background: #E3F2FD; }}
        """)
        self.filter_btn.clicked.connect(self.filter_triggered)
        layout.addWidget(self.filter_btn)

    def _on_search(self):
        self.search_triggered.emit(self.input.text().strip())

    def set_text(self, text: str):
        self.input.setText(text)


class MostGenreCard(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        _force_bg(self, BLUE_CARD, radius=CARD_RADIUS)
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(12)
        
        icon_lbl = QLabel("🔥")
        icon_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        layout.addWidget(icon_lbl)
        
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        
        self._label = QLabel("MOST GENRE")
        self._label.setStyleSheet(
            f"color: rgba(255,255,255,0.80); font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent;"
        )
        text_col.addWidget(self._label)
        
        self._value = QLabel("—")
        self._value.setStyleSheet(
            f"color: {WHITE}; font-size: 20px; font-weight: 700; background: transparent;"
        )
        text_col.addWidget(self._value)
        
        layout.addLayout(text_col)
        layout.addStretch()
        
        arrow = QLabel("→")
        arrow.setStyleSheet(
            f"color: rgba(255,255,255,0.60); font-size: 18px; font-weight: 700; background: transparent;"
        )
        layout.addWidget(arrow)

    def set_genre(self, genre: str):
        self._value.setText(genre if genre else "—")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class HomePage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._manga_list = []
        self._genre_counts = {}
        self._top_genre = None
        self._current_limit = 50
        self._filter_mode   = False
        self._filter_page   = 1
        self._filter_genres = []
        self._filter_status = None
        self._filter_year   = None
        self._is_loading    = False
        self._no_more       = False
        self._card_count    = 0
        self._build()
        self._start_loading()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.search_bar = SearchBar()
        self.search_bar.search_triggered.connect(self._on_search)
        self.search_bar.filter_triggered.connect(self._on_filter)
        root.addWidget(self.search_bar)

        outer_row = QWidget()
        outer_row_layout = QHBoxLayout(outer_row)
        outer_row_layout.setContentsMargins(24, 16, 24, 20)
        outer_row_layout.setSpacing(24)
        root.addWidget(outer_row, stretch=1)

        left_wrapper = QWidget()
        left_wrapper.setStyleSheet("background: transparent;")
        left_wrapper_layout = QVBoxLayout(left_wrapper)
        left_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        left_wrapper_layout.setSpacing(12)
        outer_row_layout.addWidget(left_wrapper, stretch=1)

        self._most_genre_card = MostGenreCard()
        self._most_genre_card.clicked.connect(self._on_most_genre_clicked)
        left_wrapper_layout.addWidget(self._most_genre_card)

        lbl = QLabel("Top Manga")
        lbl.setStyleSheet(
            f"color: {BLUE_PRIMARY}; font-size: 16px; font-weight: 700; background: transparent;"
        )
        left_wrapper_layout.addWidget(lbl)

        btn_container = QWidget()
        btn_container.setStyleSheet("background: transparent;")
        self._top_btn_row = QHBoxLayout(btn_container)
        self._top_btn_row.setSpacing(10)
        self._top_btn_row.setContentsMargins(0, 0, 0, 4)
        self._top_buttons = {}
        for n in [10, 20, 50, 100]:
            btn = QPushButton(f"Top {n}")
            btn.setFixedHeight(32)
            btn.setFixedWidth(75)
            btn.setCheckable(True)
            btn.setChecked(n == 50)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {BLUE_PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{ background: #1565C0; }}
                QPushButton:checked {{
                    background: white;
                    color: {BLUE_PRIMARY};
                    border: 2px solid {BLUE_PRIMARY};
                }}
            """)
            btn.clicked.connect(lambda _, lim=n: self._set_limit(lim))
            self._top_buttons[n] = btn
            self._top_btn_row.addWidget(btn)
        self._top_btn_row.addStretch()
        left_wrapper_layout.addWidget(btn_container)

        self.content_scroll = QScrollArea()
        content_scroll = self.content_scroll
        content_scroll.setWidgetResizable(True)
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_scroll.setWidget(content_widget)
        left_wrapper_layout.addWidget(content_scroll, stretch=1)

        left = QVBoxLayout(content_widget)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(12)

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")

        self.manga_grid = QGridLayout(self.grid_container)
        self.manga_grid.setSpacing(6)
        self.manga_grid.setContentsMargins(0, 0, 0, 0)

        left.addWidget(self.grid_container)

        self._home_loading_lbl = QLabel("Loading…")
        self._home_loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._home_loading_lbl.setStyleSheet(
            f"color: {WHITE}; font-size: 13px; background: transparent; padding: 12px;"
        )
        self._home_loading_lbl.setVisible(False)
        left.addWidget(self._home_loading_lbl)

        left.addStretch()

        self.content_scroll.verticalScrollBar().valueChanged.connect(self._on_home_scroll)

        self.filter_panel = FilterPanel()
        self.filter_panel.apply_clicked.connect(self._on_filter_apply)
        self.filter_panel.setVisible(False)
        outer_row_layout.addWidget(self.filter_panel)

        self.history = HistoryPanel()
        self.history.manga_clicked.connect(self.main_window.go_detail)
        outer_row_layout.addWidget(self.history, alignment=Qt.AlignmentFlag.AlignTop)

    def _start_loading(self):
        self._show_placeholders()
        self._loader = TopMangaLoader()
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    def _show_placeholders(self):
        self._clear_grid()
        for _ in range(self._current_limit):
            ph = QWidget()
            ph.setFixedSize(CARD_W + 16, CARD_H)
            ph.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            ph.setStyleSheet(f"background: {BLUE_CARD}; border-radius: {CARD_RADIUS}px;")
            self.manga_grid.addWidget(ph, 0, 0)
        self._relayout()

    @pyqtSlot(list, dict)
    def _on_loaded(self, manga_list, stats):
        self._manga_list = manga_list
        self._genre_counts = stats.get("genre_counts", {})
        self._top_genre = stats.get("top_genre")
        
        if self._top_genre:
            self._most_genre_card.set_genre(self._top_genre)
        
        self._display_cards()

        if manga_list and self.history._manga_id is None:
            self.history.load_manga(manga_list[0])

    def _on_most_genre_clicked(self):
        if hasattr(self.main_window, 'go_genre_list'):
            self.main_window.go_genre_list(self._genre_counts, self._top_genre)

    def _set_limit(self, limit: int):
        self._current_limit = limit
        self._filter_mode = False
        for btn in self._top_buttons.values():
            btn.setVisible(True)
        for n, btn in self._top_buttons.items():
            btn.setChecked(n == limit)
        self._display_cards()

    def _display_cards(self):
        self._clear_grid()
        self._cards = []
        to_show = self._manga_list[:self._current_limit]

        for manga in to_show:
            card = MangaCard(manga, show_labels=True)
            card.clicked.connect(self.main_window.go_detail)
            self._cards.append(card)
            self.manga_grid.addWidget(card, 0, 0)
        self._relayout()

    def _relayout(self):
        widgets = []
        while self.manga_grid.count():
            item = self.manga_grid.takeAt(0)
            if item.widget():
                widgets.append(item.widget())
        if not widgets:
            return

        container_width = self.content_scroll.viewport().width() - 4
        if container_width < 50:
            container_width = self.width() - 80 - 220 - 72

        spacing = self.manga_grid.spacing()
        for cols in [6, 5, 4, 3, 2, 1]:
            if container_width >= cols * 110 + spacing * (cols - 1):
                break

        card_w = min(_CARD_MAX_W, max(_CARD_MIN_W, (container_width - spacing * (cols - 1)) // cols))
        cover_w = card_w - _PAD * 2

        for i, widget in enumerate(widgets):
            widget.setMinimumWidth(_CARD_MIN_W)
            widget.setMaximumWidth(_CARD_MAX_W)
            if hasattr(widget, "lbl_title"):
                widget.lbl_title.setMaximumWidth(cover_w)
            if hasattr(widget, "lbl_genre"):
                widget.lbl_genre.setMaximumWidth(cover_w)
            self.manga_grid.addWidget(widget, i // cols, i % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(50, self._relayout)

    def _clear_grid(self):
        self._cards = []
        while self.manga_grid.count():
            item = self.manga_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_filter_apply(self, genres, status, year):
        # Kalau tidak ada filter yang dipilih, balik ke tampilan normal
        if not genres and not status and not year:
            self._filter_mode = False
            for btn in self._top_buttons.values():
                btn.setVisible(True)
            self._display_cards()
            return

        self._filter_mode   = True
        self._filter_page   = 1
        self._filter_genres = genres
        self._filter_status = status
        self._filter_year   = year
        self._no_more       = False
        self._card_count    = 0
        self._clear_grid()
        for btn in self._top_buttons.values():
            btn.setVisible(False)
        self._start_filter_loader(page=1)

    def _on_home_scroll(self, value):
        if not self._filter_mode:
            return
        sb = self.content_scroll.verticalScrollBar()
        if sb.maximum() > 0 and value >= sb.maximum() - 200:
            if not self._is_loading and not self._no_more:
                self._filter_page += 1
                self._start_filter_loader(self._filter_page)

    def _start_filter_loader(self, page: int):
        if self._is_loading:
            return
        self._is_loading = True
        self._home_loading_lbl.setVisible(True)
        loader = SearchLoader(
            query="",
            genres=self._filter_genres,
            status=self._filter_status,
            year=self._filter_year,
            page=page,
        )
        loader.finished.connect(lambda results, p=page: self._on_filter_results(results, p))
        loader.start()
        self._loader = loader

    def _on_filter_results(self, manga_list, page):
        self._is_loading = False
        self._home_loading_lbl.setVisible(False)

        if page == 1 and not manga_list:
            return

        container_width = self.content_scroll.viewport().width() - 4
        if container_width < 50:
            container_width = self.width() - 80 - 220 - 72
        spacing = self.manga_grid.spacing()
        for cols in [5, 4, 3, 2, 1]:
            if container_width >= cols * 130 + spacing * (cols - 1):
                break

        for manga in manga_list:
            row = self._card_count // cols
            col = self._card_count % cols
            card = MangaCard(manga, show_labels=True)
            card.clicked.connect(self.main_window.go_detail)
            self.manga_grid.addWidget(card, row, col)
            self._card_count += 1

        if len(manga_list) < SearchLoader.PAGE_SIZE:
            self._no_more = True

    def _on_search(self, query):
        if query:
            self.main_window.go_search(query)

    def _on_filter(self):
        is_open = self.filter_panel.isVisible()
        self.filter_panel.setVisible(not is_open)
        self.history.setVisible(is_open)

    def refresh(self):
        self._start_loading()