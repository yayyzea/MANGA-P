from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QScrollArea, QCheckBox,
    QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_LIGHT, BLUE_DARK,
    WHITE, TEXT_DARK, TEXT_MUTED,
    TOPBAR_HEIGHT, CARD_W, CARD_H, CARD_RADIUS
)
from .widgets import MangaCard
from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap, QPalette, QPixmap, QColor
_ICON_DIR = Path(__file__).parent.parent / "assets"


GENRES = [
    "Action",       "Drama",
    "Adventure",    "Fantasy",
    "Avant Garde",  "Gourmet",
    "Award Winning","Horror",
    "Comedy",       "Mystery",
    "Romance",      "Sci-Fi",
    "Slice of Life","Sports",
    "Supernatural",
]
STATUS_OPTIONS = ["Publishing", "Finished", "On Hiatus"]

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QScrollArea, QCheckBox,
    QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QPalette, QIcon, QPixmap
from pathlib import Path

_ICON_DIR = Path(__file__).parent.parent / "assets"

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_LIGHT, BLUE_DARK,
    WHITE, TEXT_DARK, TEXT_MUTED,
    TOPBAR_HEIGHT, CARD_W, CARD_H, CARD_RADIUS
)
from .widgets import MangaCard


GENRES = [
    "Action",        "Drama",
    "Adventure",     "Fantasy",
    "Avant Garde",   "Gourmet",
    "Award Winning", "Horror",
    "Comedy",        "Mystery",
    "Romance",       "Sci-Fi",
    "Slice of Life", "Sports",
    "Supernatural",
]
STATUS_OPTIONS = ["Publishing", "Finished", "On Hiatus"]


# ── Background worker ─────────────────────────────────────────────────────────

class SearchLoader(QThread):
    finished = pyqtSignal(list)

    PAGE_SIZE = 20

    def __init__(self, query="", genres=None, status=None, year=None, page=1):
        super().__init__()
        self.query  = query
        self.genres = genres or []
        self.status = status
        self.year   = year
        self.page   = page

    def run(self):
        try:
            from services.manga_service import MangaService
            svc = MangaService()
            has_filters = bool(self.genres or self.status or self.year)
            if self.query or has_filters:
                results = svc.search(
                    query=self.query or "",
                    genres=self.genres if self.genres else None,
                    status=self.status,
                    year=self.year,
                    page=self.page,
                    limit=self.PAGE_SIZE,
                )
            else:
                all_top = svc.get_top_manga(limit=500)
                offset = (self.page - 1) * self.PAGE_SIZE
                results = all_top[offset: offset + self.PAGE_SIZE]
            self.finished.emit(results)
        except Exception as e:
            print(f"[SearchPage] Load error: {e}")
            self.finished.emit([])


# ── Search bar ────────────────────────────────────────────────────────────────

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
                background: {WHITE}; #tengah search bar
                border: none;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 14px;
                color: {TEXT_DARK};
            }}
        """)
        self.input.returnPressed.connect(
            lambda: self.search_triggered.emit(self.input.text().strip())
        )
        layout.addWidget(self.input)

        filter_btn = QPushButton()
        filter_btn.setObjectName("FilterBtn")
        filter_btn.setFixedSize(36, 36)
        _fx = QPixmap(str(_ICON_DIR / "filter.png"))
        if not _fx.isNull():
            filter_btn.setIcon(QIcon(_fx))
            filter_btn.setIconSize(filter_btn.size() * 0.6)
        else:
            filter_btn.setText("⚙")
        filter_btn.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE};
                border: none;
                border-radius: 18px;
                font-size: 16px;
                color: {BLUE_PRIMARY};
            }}
            QPushButton:hover {{ background: #E3F2FD; }}
        """)
        filter_btn.clicked.connect(self.filter_triggered)
        layout.addWidget(filter_btn)

    def set_text(self, text: str):
        self.input.setText(text)

    def get_text(self) -> str:
        return self.input.text().strip()


# ── Filter panel ──────────────────────────────────────────────────────────────

class FilterPanel(QWidget):
    
    apply_clicked = pyqtSignal(list, object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"background: {WHITE};")
        self._genre_cbs  = {}
        self._status_cbs = {}
        self._year_input = None
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Scroll area untuk semua konten filter ──────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        inner_widget = QWidget()
        inner_widget.setStyleSheet(f"background: {WHITE};")
        root = QVBoxLayout(inner_widget)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        root.addWidget(self._heading("Filter"))

        # ── Genre ──────────────────────────────────────────────────────────
        root.addWidget(self._subheading("Genre"))
        g_grid = QGridLayout()
        g_grid.setSpacing(6)
        g_grid.setContentsMargins(0, 0, 0, 0)
        for i, g in enumerate(GENRES):
            cb = QCheckBox(g)
            cb.setStyleSheet(self._cb_style())
            self._genre_cbs[g] = cb
            g_grid.addWidget(cb, i // 2, i % 2)
        root.addLayout(g_grid)

        root.addWidget(self._subheading("Other genre"))
        self._custom_genre_input = QLineEdit()
        self._custom_genre_input.setFixedHeight(32)
        self._custom_genre_input.setMaximumWidth(160)
        self._custom_genre_input.setPlaceholderText("e.g. Isekai")
        self._custom_genre_input.setStyleSheet(f"""
            QLineEdit {{
                background: {WHITE};
                border: 1.5px solid {BLUE_LIGHT};
                border-radius: 6px; padding: 4px 10px;
                font-size: 13px; color: {TEXT_DARK};
            }}
            QLineEdit:focus {{ border-color: {BLUE_PRIMARY}; }}
        """)
        root.addWidget(self._custom_genre_input)

        # ── Status ─────────────────────────────────────────────────────────
        root.addWidget(self._subheading("Status"))
        s_grid = QGridLayout()
        s_grid.setSpacing(6)
        s_grid.setContentsMargins(0, 0, 0, 0)
        for i, s in enumerate(STATUS_OPTIONS):
            cb = QCheckBox(s)
            cb.setStyleSheet(self._cb_style())
            self._status_cbs[s] = cb
            s_grid.addWidget(cb, i // 2, i % 2)
        root.addLayout(s_grid)

        # ── Tahun ──────────────────────────────────────────────────────────
        root.addWidget(self._subheading("Tahun"))
        self._year_input = QLineEdit()
        self._year_input.setPlaceholderText("e.g. 2023")
        self._year_input.setFixedHeight(32)
        self._year_input.setMaximumWidth(110)
        self._year_input.setStyleSheet(f"""
            QLineEdit {{
                background: {WHITE};
                border: 1.5px solid {BLUE_LIGHT};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
                color: {TEXT_DARK};
            }}
            QLineEdit:focus {{
                border-color: {BLUE_PRIMARY};
            }}
        """)
        root.addWidget(self._year_input)
        root.addStretch()

        scroll.setWidget(inner_widget)
        outer.addWidget(scroll, stretch=1)

        # ── Apply — di luar scroll, selalu terlihat ────────────────────────
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedHeight(46)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE};
                border: 2.5px solid {BLUE_PRIMARY};
                border-radius: 23px;
                color: {BLUE_PRIMARY};
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {BLUE_PRIMARY};
                color: {WHITE};
            }}
        """)
        apply_btn.clicked.connect(self._emit_apply)
        outer.addWidget(apply_btn)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _heading(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {TEXT_DARK}; background: transparent;"
        )
        return lbl

    def _subheading(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {TEXT_DARK}; background: transparent;"
        )
        return lbl

    def _cb_style(self):
        return f"""
            QCheckBox {{
                font-size: 11px;
                color: {TEXT_DARK};
                background: transparent;
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 14px; height: 14px;
                border: 2px solid {TEXT_MUTED};
                border-radius: 3px;
                background: {WHITE};
            }}
            QCheckBox::indicator:checked {{
                background: {BLUE_PRIMARY};
                border-color: {BLUE_PRIMARY};
            }}
        """

    def _emit_apply(self):
        genres = [g for g, cb in self._genre_cbs.items() if cb.isChecked()]
        checked_status = [s for s, cb in self._status_cbs.items() if cb.isChecked()]
        status = checked_status[0] if checked_status else None
        year = self.selected_year()
        self.apply_clicked.emit(genres, status, year)

    # ── Getters ───────────────────────────────────────────────────────────

    def selected_genres(self) -> list:
        genres = [g for g, cb in self._genre_cbs.items() if cb.isChecked()]
        custom = self._custom_genre_input.text().strip()
        if custom:
            genres.append(custom)
        return genres

    def selected_status(self):
        checked = [s for s, cb in self._status_cbs.items() if cb.isChecked()]
        return checked[0] if checked else None

    def selected_year(self):
        text = (self._year_input.text() or "").strip()
        if text:
            try:
                return int(text)
            except ValueError:
                pass
        return None


# ── Search page ───────────────────────────────────────────────────────────────

class SearchPage(QWidget):
    COLS = 4

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window    = main_window
        self._loader        = None
        self._current_query = ""
        self._current_page  = 1
        self._is_loading    = False
        self._no_more       = False
        self._card_count    = 0
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.search_bar = SearchBar()
        self.search_bar.search_triggered.connect(self._run_search)
        self.search_bar.filter_triggered.connect(self._toggle_filter)
        root.addWidget(self.search_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # Kiri: grid hasil
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)
        sc = QWidget()
        self._grid_root = QVBoxLayout(sc)
        self._grid_root.setContentsMargins(24, 20, 24, 20)
        self._grid_root.setSpacing(12)

        self.section_lbl = QLabel("Top Manga")
        self.section_lbl.setStyleSheet(
            f"color: {BLUE_PRIMARY}; font-size: 16px; font-weight: 700; background: transparent;"
        )
        self._grid_root.addWidget(self.section_lbl)

        self._grid_container = QWidget()
        self._grid = QGridLayout(self._grid_container)
        self._grid.setSpacing(16)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._grid_root.addWidget(self._grid_container)

        self._loading_lbl = QLabel("Loading…")
        self._loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 13px; background: transparent; padding: 12px;"
        )
        self._loading_lbl.setVisible(False)
        self._grid_root.addWidget(self._loading_lbl)

        self._grid_root.addStretch()

        self._scroll.setWidget(sc)
        body.addWidget(self._scroll, stretch=1)

        self.filter_panel = FilterPanel()
        self.filter_panel.apply_clicked.connect(self._on_filter_apply)
        self.filter_panel.setVisible(False)
        body.addWidget(self.filter_panel)

        root.addLayout(body, stretch=1)
        self._show_placeholders(8)

    def _toggle_filter(self):
        self.filter_panel.setVisible(not self.filter_panel.isVisible())

    def _show_placeholders(self, count=8):
        self._clear_grid()
        for i in range(count):
            ph = QWidget()
            ph.setFixedSize(CARD_W, CARD_H)
            ph.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            ph.setStyleSheet(f"background: {BLUE_CARD}; border-radius: {CARD_RADIUS}px;")
            self._grid.addWidget(ph, i // self.COLS, i % self.COLS)

    def _clear_grid(self):
        self._card_count = 0
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_scroll(self, value):
        sb = self._scroll.verticalScrollBar()
        if sb.maximum() > 0 and value >= sb.maximum() - 200:
            self._load_next_page()

    def _load_next_page(self):
        if self._is_loading or self._no_more:
            return
        self._current_page += 1
        self._start_loader(self._current_page)

    # ── Public ────────────────────────────────────────────────────────────────

    def set_query(self, query: str):
        self._current_query = query
        self.search_bar.set_text(query)
        self._run_search(query)

    def refresh(self):
        self._run_search(self._current_query)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _run_search(self, query=""):
        self._current_query = query
        self._current_page  = 1
        self._no_more       = False
        self.section_lbl.setText(f'Results for "{query}"' if query else "Top Manga")
        self._show_placeholders(8)

        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()

        self._start_loader(1)

    def _start_loader(self, page: int):
        if self._is_loading:
            return
        self._is_loading = True
        self._loading_lbl.setVisible(True)

        loader = SearchLoader(
            query=self._current_query,
            genres=self.filter_panel.selected_genres(),
            status=self.filter_panel.selected_status(),
            year=self.filter_panel.selected_year(),
            page=page,
        )
        loader.finished.connect(lambda results, p=page: self._on_results(results, p))
        loader.start()
        self._loader = loader

    def _on_filter_apply(self, genres, status, year):
        self._run_search(self._current_query)

    @pyqtSlot(list)
    def _on_results(self, manga_list, page=1):
        self._is_loading = False
        self._loading_lbl.setVisible(False)

        if page == 1:
            self._clear_grid()

        if not manga_list:
            self._no_more = True
            if self._card_count == 0:
                empty = QLabel("No results found.")
                empty.setStyleSheet(
                    f"color: {TEXT_MUTED}; font-size: 14px; background: transparent;"
                )
                self._grid.addWidget(empty, 0, 0)
            return

        for manga in manga_list:
            row = self._card_count // self.COLS
            col = self._card_count % self.COLS
            card = MangaCard(manga, show_labels=True)
            card.clicked.connect(self.main_window.go_detail)
            self._grid.addWidget(card, row, col)
            self._card_count += 1

        # Jika hasil kurang dari PAGE_SIZE berarti sudah habis
        if len(manga_list) < SearchLoader.PAGE_SIZE:
            self._no_more = True
