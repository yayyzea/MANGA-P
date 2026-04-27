from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QLineEdit, QCheckBox, QGridLayout,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QPalette, QPixmap, QIcon
from pathlib import Path

_ICON_DIR = Path(__file__).parent.parent / "assets"

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_LIGHT, WHITE,
    TEXT_DARK, TEXT_MUTED,
    TOPBAR_HEIGHT, CARD_W, CARD_H, CARD_RADIUS
)
from .widgets import MangaCard


# ── Konstanta ─────────────────────────────────────────────────────────────────

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

READ_STATUS_OPTIONS = ["Plan to Read", "Reading", "Completed", "Dropped"]


# ── Background worker ─────────────────────────────────────────────────────────

class CollectionLoader(QThread):
    finished = pyqtSignal(list, list)   # last_read entries, my_books entries

    def run(self):
        try:
            from database import get_session
            from models.user_collection import UserCollection
            from sqlalchemy.orm import joinedload

            session = get_session()
            try:
                entries = (
                    session.query(UserCollection)
                    .options(joinedload(UserCollection.manga))
                    .order_by(UserCollection.updated_at.desc())
                    .all()
                )

                last_read = [
                    e for e in entries
                    if e.status in ("Reading", "Completed") and e.manga
                ][:48]

                my_books = [e for e in entries if e.manga]

            finally:
                session.close()

            self.finished.emit(last_read, my_books)

        except Exception as e:
            print(f"[LibraryPage] Load error: {e}")
            self.finished.emit([], [])


# ── Filter helper ─────────────────────────────────────────────────────────────

def _filter_entries(entries, query: str, genres: list, statuses: list, year: str):
    result = []
    q = query.strip().lower()
    for entry in entries:
        manga = entry.manga
        if not manga:
            continue
        if q and q not in (manga.title or "").lower():
            continue
        if genres:
            manga_genres = [g.strip().lower() for g in (manga.genres or "").split(",")]
            if not any(g.lower() in manga_genres for g in genres):
                continue
        if statuses and entry.status not in statuses:
            continue
        if year:
            try:
                if manga.year != int(year):
                    continue
            except ValueError:
                pass
        result.append(entry)
    return result


# ── Search bar khusus Library (dengan tombol filter toggle) ───────────────────

class LibrarySearchBar(QWidget):
    search_triggered  = pyqtSignal(str)
    filter_toggled    = pyqtSignal()        # sinyal toggle sidebar filter

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

        # Ikon search
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

        # Input pencarian lokal
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
        self.input.textChanged.connect(lambda t: self.search_triggered.emit(t.strip()))
        self.input.returnPressed.connect(
            lambda: self.search_triggered.emit(self.input.text().strip())
        )
        layout.addWidget(self.input)

        # Tombol filter (toggle)
        self.filter_btn = QPushButton()
        self.filter_btn.setObjectName("FilterBtn")
        self.filter_btn.setFixedSize(36, 36)
        self.filter_btn.setCheckable(True)
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
            QPushButton:hover   {{ background: #E3F2FD; }}
            QPushButton:checked {{ background: #BBDEFB; }}
        """)
        self.filter_btn.clicked.connect(self.filter_toggled)
        layout.addWidget(self.filter_btn)

    def get_text(self) -> str:
        return self.input.text().strip()


# ── Filter panel khusus Library ───────────────────────────────────────────────

class LibraryFilterPanel(QWidget):
    """
    Sidebar filter yang muncul/hilang saat tombol filter diklik.
    Konten: Genre, Read Status, Tahun, dan tombol Apply.
    """
    apply_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"background: {WHITE};")
        self._genre_cbs  = {}
        self._status_cbs = {}
        self._year_input = None
        self._build()
        # Tersembunyi secara default
        self.setVisible(False)

    def _build(self):
        root = QVBoxLayout(self)
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
            g_grid.addWidget(cb, i // 3, i % 3)
        root.addLayout(g_grid)

        # ── Read Status ────────────────────────────────────────────────────
        root.addWidget(self._subheading("Read Status"))
        s_grid = QGridLayout()
        s_grid.setSpacing(6)
        s_grid.setContentsMargins(0, 0, 0, 0)
        pairs = [("Plan to Read", "Completed"), ("Reading", "Dropped")]
        for row_idx, (s1, s2) in enumerate(pairs):
            for col_idx, s in enumerate([s1, s2]):
                cb = QCheckBox(s)
                cb.setStyleSheet(self._cb_style())
                self._status_cbs[s] = cb
                s_grid.addWidget(cb, row_idx, col_idx)
        root.addLayout(s_grid)

        # ── Tahun ──────────────────────────────────────────────────────────
        root.addWidget(self._subheading("Tahun"))
        self._year_input = QLineEdit()
        self._year_input.setFixedHeight(32)
        self._year_input.setMaximumWidth(110)
        self._year_input.setStyleSheet(f"""
            QLineEdit {{
                background: {WHITE};
                border: 1.5px solid {BLUE_LIGHT};
                border-radius: 6px; padding: 4px 10px;
                font-size: 13px; color: {TEXT_DARK};
            }}
            QLineEdit:focus {{ border-color: {BLUE_PRIMARY}; }}
        """)
        root.addWidget(self._year_input)

        root.addStretch()

        # ── Apply ──────────────────────────────────────────────────────────
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
                background: {BLUE_PRIMARY};
                color: {WHITE};
            }}
        """)
        apply_btn.clicked.connect(self.apply_clicked)
        root.addWidget(apply_btn)

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
            QCheckBox {{ font-size: 11px; color: {TEXT_DARK}; background: transparent; spacing: 5px; }}
            QCheckBox::indicator {{
                width: 14px; height: 14px;
                border: 2px solid {TEXT_MUTED}; border-radius: 3px;
                background: {WHITE};
            }}
            QCheckBox::indicator:checked {{
                background: {BLUE_PRIMARY}; border-color: {BLUE_PRIMARY};
            }}
        """

    # ── Getters ───────────────────────────────────────────────────────────

    def selected_genres(self)   -> list: return [g for g, cb in self._genre_cbs.items()  if cb.isChecked()]
    def selected_statuses(self) -> list: return [s for s, cb in self._status_cbs.items() if cb.isChecked()]
    def selected_year(self)     -> str:  return (self._year_input.text() or "").strip()

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())


# ── Horizontal card row ───────────────────────────────────────────────────────

class CardRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFixedHeight(CARD_H + 40)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        self._row = QHBoxLayout(self._inner)
        self._row.setContentsMargins(0, 8, 0, 8)
        self._row.setSpacing(16)
        self._row.addStretch()

        self.scroll.setWidget(self._inner)
        root.addWidget(self.scroll)

    def show_placeholders(self, count=6):
        self._clear()
        for _ in range(count):
            ph = QWidget()
            ph.setFixedSize(CARD_W + 16, CARD_H)
            ph.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            ph.setStyleSheet(f"background: {BLUE_CARD}; border-radius: {CARD_RADIUS}px;")
            self._row.insertWidget(self._row.count() - 1, ph)

    def load_cards(self, manga_list, on_click):
        self._clear()
        if not manga_list:
            lbl = QLabel("No manga found.")
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
            self._row.insertWidget(0, lbl)
            return
        for manga in manga_list:
            card = MangaCard(manga, show_labels=True)
            card.clicked.connect(on_click)
            self._row.insertWidget(self._row.count() - 1, card)

    def _clear(self):
        while self._row.count() > 1:
            item = self._row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ── Library page ──────────────────────────────────────────────────────────────

class LibraryPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._loader = None
        self._all_last_read: list = []
        self._all_my_books:  list = []
        self._build()
        self._start_loading()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Search bar ─────────────────────────────────────────────────────
        self.search_bar = LibrarySearchBar()
        self.search_bar.search_triggered.connect(self._apply_filters)
        # Tombol filter → toggle sidebar
        self.search_bar.filter_toggled.connect(self._toggle_filter)
        root.addWidget(self.search_bar)

        # ── Body: konten kiri + filter kanan (filter awalnya hidden) ───────
        self.body = QHBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(0)

        # Kiri: scroll area berisi Last Read + My Books
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(20)

        cl.addWidget(self._sec("Last Read"))
        self.last_read_row = CardRow()
        self.last_read_row.show_placeholders(6)
        cl.addWidget(self.last_read_row)

        cl.addWidget(self._sec("My Books"))
        self.my_books_row = CardRow()
        self.my_books_row.show_placeholders(6)
        cl.addWidget(self.my_books_row)

        cl.addStretch()
        scroll.setWidget(content)
        self.body.addWidget(scroll, stretch=1)

        # Kanan: filter panel (hidden by default)
        self.filter_panel = LibraryFilterPanel()
        self.filter_panel.apply_clicked.connect(self._apply_filters)
        self.body.addWidget(self.filter_panel)

        root.addLayout(self.body, stretch=1)

    def _sec(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {BLUE_PRIMARY}; font-size: 16px; "
            f"font-weight: 700; background: transparent;"
        )
        return lbl

    # ── Toggle filter sidebar ─────────────────────────────────────────────────

    def _toggle_filter(self):
        self.filter_panel.toggle_visibility()

    # ── Loading ───────────────────────────────────────────────────────────────

    def _start_loading(self):
        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()
        self.last_read_row.show_placeholders(6)
        self.my_books_row.show_placeholders(6)
        self._loader = CollectionLoader()
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    @pyqtSlot(list, list)
    def _on_loaded(self, lr_entries, mb_entries):
        self._all_last_read = lr_entries
        self._all_my_books  = mb_entries
        self._apply_filters()

    # ── Filter & render ───────────────────────────────────────────────────────

    def _apply_filters(self, query: str = ""):
        if not isinstance(query, str):
            query = ""
        # Selalu ambil teks terkini dari search bar
        current_text = self.search_bar.get_text()
        if current_text:
            query = current_text

        genres   = self.filter_panel.selected_genres()
        statuses = self.filter_panel.selected_statuses()
        year     = self.filter_panel.selected_year()

        filtered_lr = _filter_entries(self._all_last_read, query, genres, statuses, year)
        lr_manga = [e.manga for e in filtered_lr][:12]

        filtered_mb = _filter_entries(self._all_my_books, query, genres, statuses, year)
        mb_manga = [e.manga for e in filtered_mb]

        self.last_read_row.load_cards(lr_manga, self.main_window.go_detail)
        self.my_books_row.load_cards(mb_manga, self.main_window.go_detail)

    # ── Public ────────────────────────────────────────────────────────────────

    def refresh(self):
        self._start_loading()
