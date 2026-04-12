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
from PyQt6.QtGui import QIcon, QPixmap
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
YEAR_OPTIONS   = ["2019", "2020", "2021", "2022", "2023", "2024"]


# ── Background worker ─────────────────────────────────────────────────────────

class SearchLoader(QThread):
    finished = pyqtSignal(list)

    def __init__(self, query="", genres=None, status=None, year=None):
        super().__init__()
        self.query  = query
        self.genres = genres or []
        self.status = status
        self.year   = year

    def run(self):
        try:
            from services.manga_service import MangaService
            svc = MangaService()

            has_filters = bool(self.genres or self.status or self.year)

            if self.query or has_filters:
                # Query OR any active filter → always go through search()
                # manga_service.search() handles: keyword fetch, genre fetch, DB filter
                results = svc.search(
                    query=self.query or "",
                    genres=self.genres if self.genres else None,
                    status=self.status,
                    year=self.year,
                    limit=16,
                )
            else:
                # Absolutely nothing selected → show top manga
                results = svc.get_top_manga(limit=16)

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
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"background: {BLUE_PRIMARY};")
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        icon = QLabel()
        icon.setFixedSize(20, 20)
        _sx2 = QPixmap(str(_ICON_DIR / "search.png"))
        if not _sx2.isNull():
            icon.setPixmap(_sx2.scaled(18, 18,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            icon.setText("🔍")
        icon.setStyleSheet("background: transparent;")
        layout.addWidget(icon)

        self.input = QLineEdit()
        self.input.setObjectName("SearchInput")
        self.input.setPlaceholderText("Search Mangas...")
        self.input.returnPressed.connect(
            lambda: self.search_triggered.emit(self.input.text().strip())
        )
        layout.addWidget(self.input)

        btn = QPushButton()
        btn.setObjectName("FilterBtn")
        btn.setFixedSize(36, 36)
        _fx2 = QPixmap(str(_ICON_DIR / "filter.png"))
        if not _fx2.isNull():
            btn.setIcon(QIcon(_fx2))
            btn.setIconSize(btn.size() * 0.6)
        else:
            btn.setText("⚙")
        btn.clicked.connect(self.filter_triggered)
        layout.addWidget(btn)

    def set_text(self, text: str):
        self.input.setText(text)

    def get_text(self) -> str:
        return self.input.text().strip()


# ── Filter panel ──────────────────────────────────────────────────────────────

class FilterPanel(QWidget):
    apply_clicked = pyqtSignal(list, object, object)  # genres, status|None, year|None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"background: {WHITE};")
        self._genre_cbs  = {}
        self._status_cbs = {}
        self._year_cbs   = {}
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        root.addWidget(self._heading("Filter"))

        # Genre
        root.addWidget(self._subheading("Genre"))
        g_grid = QGridLayout()
        g_grid.setSpacing(6)
        g_grid.setContentsMargins(0, 0, 0, 0)
        for i, g in enumerate(GENRES):
            cb = QCheckBox(g)
            cb.setStyleSheet(self._cb_style())
            self._genre_cbs[g] = cb
            g_grid.addWidget(cb, i // 3, i % 3)
        root.addLayout(g_grid)

        # Status (single select via checkboxes — only first checked is used)
        root.addWidget(self._subheading("Status"))
        s_row = QHBoxLayout()
        s_row.setSpacing(16)
        for s in STATUS_OPTIONS:
            cb = QCheckBox(s)
            cb.setStyleSheet(self._cb_style())
            self._status_cbs[s] = cb
            s_row.addWidget(cb)
        s_row.addStretch()
        root.addLayout(s_row)

        # Year (single select)
        root.addWidget(self._subheading("Year"))
        y_grid = QGridLayout()
        y_grid.setSpacing(6)
        y_grid.setContentsMargins(0, 0, 0, 0)
        for i, y in enumerate(YEAR_OPTIONS):
            cb = QCheckBox(y)
            cb.setStyleSheet(self._cb_style())
            self._year_cbs[y] = cb
            y_grid.addWidget(cb, i // 2, i % 2)
        root.addLayout(y_grid)

        root.addStretch()

        apply_btn = QPushButton("Apply")
        apply_btn.setFixedHeight(46)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE};
                border: 2.5px solid {BLUE_PRIMARY};
                border-radius: 23px;
                color: {BLUE_PRIMARY};
                font-size: 15px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: {BLUE_PRIMARY}; color: {WHITE};
            }}
        """)
        apply_btn.clicked.connect(self._emit_apply)
        root.addWidget(apply_btn)

    def _heading(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT_DARK}; background: transparent;")
        return lbl

    def _subheading(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {TEXT_DARK}; background: transparent;")
        return lbl

    def _cb_style(self):
        return f"""
            QCheckBox {{ font-size: 11px; color: {TEXT_DARK}; background: transparent; spacing: 5px; }}
            QCheckBox::indicator {{
                width: 14px; height: 14px;
                border: 2px solid {TEXT_MUTED}; border-radius: 3px; background: {WHITE};
            }}
            QCheckBox::indicator:checked {{
                background: {BLUE_PRIMARY}; border-color: {BLUE_PRIMARY};
            }}
        """

    def _emit_apply(self):
        genres = [g for g, cb in self._genre_cbs.items()  if cb.isChecked()]
        # status: take first checked only (service expects single str)
        checked_status = [s for s, cb in self._status_cbs.items() if cb.isChecked()]
        status = checked_status[0] if checked_status else None
        # year: take first checked only (service expects single int)
        checked_years = [y for y, cb in self._year_cbs.items() if cb.isChecked()]
        year = int(checked_years[0]) if checked_years else None
        self.apply_clicked.emit(genres, status, year)

    def selected_genres(self): return [g for g, cb in self._genre_cbs.items()  if cb.isChecked()]
    def selected_status(self):
        checked = [s for s, cb in self._status_cbs.items() if cb.isChecked()]
        return checked[0] if checked else None
    def selected_year(self):
        checked = [y for y, cb in self._year_cbs.items() if cb.isChecked()]
        return int(checked[0]) if checked else None


# ── Search page ───────────────────────────────────────────────────────────────

class SearchPage(QWidget):
    COLS = 4

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window    = main_window
        self._loader        = None
        self._current_query = ""
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.search_bar = SearchBar()
        self.search_bar.search_triggered.connect(self._run_search)
        self.search_bar.filter_triggered.connect(
            lambda: self._run_search(self._current_query)
        )
        root.addWidget(self.search_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # Left: grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
        self._grid_root.addStretch()

        scroll.setWidget(sc)
        body.addWidget(scroll, stretch=1)

        # Right: filter
        self.filter_panel = FilterPanel()
        self.filter_panel.apply_clicked.connect(self._on_filter_apply)
        body.addWidget(self.filter_panel)

        root.addLayout(body, stretch=1)
        self._show_placeholders(8)

    def _show_placeholders(self, count=8):
        self._clear_grid()
        for i in range(count):
            ph = QWidget()
            ph.setFixedSize(CARD_W, CARD_H)
            ph.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            ph.setStyleSheet(f"background: {BLUE_CARD}; border-radius: {CARD_RADIUS}px;")
            self._grid.addWidget(ph, i // self.COLS, i % self.COLS)

    def _clear_grid(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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
        self.section_lbl.setText(f'Results for "{query}"' if query else "Top Manga")
        self._show_placeholders(8)

        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()

        self._loader = SearchLoader(
            query=query,
            genres=self.filter_panel.selected_genres(),
            status=self.filter_panel.selected_status(),
            year=self.filter_panel.selected_year(),
        )
        self._loader.finished.connect(self._on_results)
        self._loader.start()

    def _on_filter_apply(self, genres, status, year):
        self._run_search(self._current_query)

    @pyqtSlot(list)
    def _on_results(self, manga_list):
        self._clear_grid()
        if not manga_list:
            empty = QLabel("No results found.")
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; background: transparent;")
            self._grid.addWidget(empty, 0, 0)
            return
        for i, manga in enumerate(manga_list):
            card = MangaCard(manga, show_labels=True)
            card.clicked.connect(self.main_window.go_detail)
            self._grid.addWidget(card, i // self.COLS, i % self.COLS)
