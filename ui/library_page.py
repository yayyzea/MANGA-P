from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QLineEdit, QCheckBox, QGridLayout, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QPalette, QPixmap, QIcon
from pathlib import Path

_ICON_DIR = Path(__file__).parent.parent / "assets"

from .theme import (
    BLUE_DARK, BLUE_PRIMARY, BLUE_CARD, BLUE_LIGHT, WHITE,
    TEXT_DARK, TEXT_MUTED,
    TOPBAR_HEIGHT, CARD_W, CARD_H, CARD_RADIUS
)
from .widgets import MangaCard
from .add_manga_form import AddMangaForm


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


# ── Search bar khusus Library ─────────────────────────────────────────────────

class LibrarySearchBar(QWidget):
    search_triggered  = pyqtSignal(str)
    filter_toggled    = pyqtSignal()
    delete_toggled    = pyqtSignal(bool)   # True = masuk mode delete

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

        # Tombol trash bin
        self.trash_btn = QPushButton("🗑")
        self.trash_btn.setObjectName("TrashBtn")
        self.trash_btn.setFixedSize(36, 36)
        self.trash_btn.setCheckable(True)
        self.trash_btn.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE}; border: none;
                border-radius: 18px; font-size: 16px; color: #E53935;
            }}
            QPushButton:hover   {{ background: #FFEBEE; }}
            QPushButton:checked {{
                background: #E53935; color: {WHITE};
            }}
        """)
        self.trash_btn.toggled.connect(self.delete_toggled)
        layout.addWidget(self.trash_btn)

    def reset_trash(self):
        """Reset tombol trash ke state normal (tidak aktif)."""
        self.trash_btn.blockSignals(True)
        self.trash_btn.setChecked(False)
        self.trash_btn.blockSignals(False)

    def get_text(self) -> str:
        return self.input.text().strip()


# ── Filter panel khusus Library ───────────────────────────────────────────────

class LibraryFilterPanel(QWidget):
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
        self.setVisible(False)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        root.addWidget(self._heading("Filter"))

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

    def selected_genres(self)   -> list: return [g for g, cb in self._genre_cbs.items()  if cb.isChecked()]
    def selected_statuses(self) -> list: return [s for s, cb in self._status_cbs.items() if cb.isChecked()]
    def selected_year(self)     -> str:  return (self._year_input.text() or "").strip()

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())


# ── Manga Card dengan Checkbox overlay (mode delete) ─────────────────────────

class SelectableMangaCard(QWidget):
    """
    Wrapper MangaCard yang menampilkan checkbox di pojok kiri atas
    saat mode delete aktif.
    """
    clicked = pyqtSignal(int)

    def __init__(self, manga, entry_id: int, show_labels: bool = True, parent=None):
        super().__init__(parent)
        self.manga    = manga
        self.entry_id = entry_id     # UserCollection.id untuk delete

        self._checkbox = None

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._card = MangaCard(manga, show_labels=show_labels)
        self._card.clicked.connect(self.clicked)
        layout.addWidget(self._card)

        self.setSizePolicy(self._card.sizePolicy())
        self.setFixedWidth(self._card.width())

    def set_select_mode(self, active: bool):
        if active:
            if self._checkbox is None:
                self._checkbox = QCheckBox(self)
                self._checkbox.setStyleSheet(f"""
                    QCheckBox {{ background: transparent; spacing: 0px; }}
                    QCheckBox::indicator {{
                        width: 22px; height: 22px;
                        border: 2.5px solid {WHITE};
                        border-radius: 5px;
                        background: rgba(255,255,255,0.85);
                    }}
                    QCheckBox::indicator:checked {{
                        background: #E53935;
                        border-color: #E53935;
                    }}
                """)
                self._checkbox.move(8, 8)
                self._checkbox.raise_()
            self._checkbox.setChecked(False)
            self._checkbox.setVisible(True)
        else:
            if self._checkbox:
                self._checkbox.setVisible(False)

    def is_selected(self) -> bool:
        return self._checkbox is not None and self._checkbox.isChecked()


# ── Horizontal card row ───────────────────────────────────────────────────────

class CardRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selectable_cards: list[SelectableMangaCard] = []
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

    def load_cards(self, entries, on_click):
        """
        entries: list of UserCollection entries.
        on_click: callable(manga_id).
        """
        self._clear()
        self._selectable_cards = []
        if not entries:
            lbl = QLabel("No manga found.")
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
            self._row.insertWidget(0, lbl)
            return
        for entry in entries:
            manga = entry.manga
            if not manga:
                continue
            card = SelectableMangaCard(manga, entry_id=entry.id, show_labels=True)
            card.clicked.connect(on_click)
            self._selectable_cards.append(card)
            self._row.insertWidget(self._row.count() - 1, card)

    def set_select_mode(self, active: bool):
        for card in self._selectable_cards:
            card.set_select_mode(active)

    def get_selected_entry_ids(self) -> list:
        return [c.entry_id for c in self._selectable_cards if c.is_selected()]

    def _clear(self):
        self._selectable_cards = []
        while self._row.count() > 1:
            item = self._row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ── Banner konfirmasi delete ───────────────────────────────────────────────────

class DeleteConfirmBar(QWidget):
    cancelled = pyqtSignal()
    confirmed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"background: {WHITE}; border-top: 1.5px solid #FFCDD2;")
        self.setFixedHeight(64)
        self._build()
        self.setVisible(False)

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(12)

        self.info_lbl = QLabel("Pilih manga yang ingin dihapus")
        self.info_lbl.setStyleSheet(
            f"color: {TEXT_DARK}; font-size: 14px; background: transparent;"
        )
        layout.addWidget(self.info_lbl, stretch=1)

        cancel_btn = QPushButton("Batal")
        cancel_btn.setFixedHeight(38)
        cancel_btn.setMinimumWidth(90)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE};
                border: 2px solid {BLUE_PRIMARY};
                border-radius: 19px;
                color: {BLUE_PRIMARY};
                font-size: 14px; font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background: #E3F2FD; }}
        """)
        cancel_btn.clicked.connect(self.cancelled)
        layout.addWidget(cancel_btn)

        self.delete_btn = QPushButton("🗑  Hapus")
        self.delete_btn.setFixedHeight(38)
        self.delete_btn.setMinimumWidth(100)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: #E53935; border: none;
                border-radius: 19px;
                color: {WHITE};
                font-size: 14px; font-weight: 700;
                padding: 0 16px;
            }}
            QPushButton:hover   {{ background: #B71C1C; }}
            QPushButton:disabled {{ background: #FFCDD2; color: #EF9A9A; }}
        """)
        self.delete_btn.clicked.connect(self.confirmed)
        layout.addWidget(self.delete_btn)

    def update_count(self, count: int):
        if count == 0:
            self.info_lbl.setText("Pilih manga yang ingin dihapus")
            self.delete_btn.setEnabled(False)
        else:
            self.info_lbl.setText(f"{count} manga dipilih")
            self.delete_btn.setEnabled(True)


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
        self.search_bar.filter_toggled.connect(self._toggle_filter)
        self.search_bar.delete_toggled.connect(self._set_delete_mode)
        root.addWidget(self.search_bar)

        # ── Body: konten + filter sidebar ──────────────────────────────────
        self.body = QHBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(20)

        # ── Last Read header + tombol + ──────────────────────────────────
        lr_header = QHBoxLayout()
        lr_header.setContentsMargins(0, 0, 0, 0)
        lr_header.addWidget(self._sec("Last Read"))
        lr_header.addStretch()
        self._add_btn = QPushButton("+")
        self._add_btn.setFixedSize(32, 32)
        self._add_btn.setToolTip("Tambah Manga Manual")
        self._add_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {BLUE_PRIMARY};
                border: none;
                font-size: 26px;
                font-weight: 300;
                line-height: 1;
            }}
            QPushButton:hover {{ color: {BLUE_DARK}; }}
        """)
        self._add_btn.clicked.connect(self._open_add_form)
        lr_header.addWidget(self._add_btn)
        cl.addLayout(lr_header)
 
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

        self.filter_panel = LibraryFilterPanel()
        self.filter_panel.apply_clicked.connect(self._apply_filters)
        self.body.addWidget(self.filter_panel)

        root.addLayout(self.body, stretch=1)

        # ── Banner konfirmasi delete ────────────────────────────────────────
        self.confirm_bar = DeleteConfirmBar()
        self.confirm_bar.cancelled.connect(self._cancel_delete_mode)
        self.confirm_bar.confirmed.connect(self._confirm_delete)
        root.addWidget(self.confirm_bar)

        # Timer polling untuk update jumlah checkbox yang dicentang
        self._check_timer = QTimer(self)
        self._check_timer.setInterval(150)
        self._check_timer.timeout.connect(self._update_selection_count)

    def _sec(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {BLUE_PRIMARY}; font-size: 16px; "
            f"font-weight: 700; background: transparent;"
        )
        return lbl

    # ── Filter sidebar ────────────────────────────────────────────────────────

    def _toggle_filter(self):
        self.filter_panel.toggle_visibility()

    def _open_add_form(self):
        """Buka dialog AddMangaForm untuk menambah manga manual."""
        dialog = AddMangaForm(parent=self)
        dialog.manga_added.connect(self._on_manga_added)
        dialog.exec()
 
    def _on_manga_added(self, manga_id: int):
        """Dipanggil setelah manga berhasil disimpan — refresh library."""
        self._start_loading()
        if hasattr(self.main_window, 'show_toast'):
            self.main_window.show_toast("Manga berhasil ditambahkan!")

    # ── Delete mode ───────────────────────────────────────────────────────────

    def _set_delete_mode(self, active: bool):
        self.last_read_row.set_select_mode(active)
        self.my_books_row.set_select_mode(active)
        if active:
            self.confirm_bar.setVisible(True)
            self._check_timer.start()
        else:
            self.confirm_bar.setVisible(False)
            self._check_timer.stop()

    def _cancel_delete_mode(self):
        self.search_bar.reset_trash()     # unchecks trash_btn tanpa memicu sinyal
        self._set_delete_mode(False)

    def _update_selection_count(self):
        ids = list(dict.fromkeys(
            self.last_read_row.get_selected_entry_ids()
            + self.my_books_row.get_selected_entry_ids()
        ))
        self.confirm_bar.update_count(len(ids))

    def _confirm_delete(self):
        ids = list(dict.fromkeys(
            self.last_read_row.get_selected_entry_ids()
            + self.my_books_row.get_selected_entry_ids()
        ))
        if not ids:
            return

        count = len(ids)
        msg = QMessageBox(self)
        msg.setWindowTitle("Konfirmasi Hapus")
        msg.setText(
            f"Hapus {count} manga dari My Library?\n\n"
            "Tindakan ini tidak dapat dibatalkan."
        )
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        msg.button(QMessageBox.StandardButton.Yes).setText("Ya, Hapus")
        msg.button(QMessageBox.StandardButton.Cancel).setText("Batal")
        msg.setStyleSheet(f"""
            QMessageBox {{ background: {WHITE}; }}
            QLabel {{ color: {TEXT_DARK}; font-size: 14px; }}
            QPushButton {{
                min-width: 90px; min-height: 34px;
                border-radius: 17px;
                font-size: 13px; font-weight: 600;
                padding: 0 12px;
            }}
        """)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self._do_delete(ids)

    def _do_delete(self, entry_ids: list):
        from services.collection_service import CollectionService
        svc = CollectionService()
        deleted = sum(1 for eid in entry_ids if svc.delete(eid))

        self._cancel_delete_mode()
        self._start_loading()

        if deleted:
            ok = QMessageBox(self)
            ok.setWindowTitle("Berhasil")
            ok.setText(f"{deleted} manga berhasil dihapus dari My Library.")
            ok.setStandardButtons(QMessageBox.StandardButton.Ok)
            ok.setStyleSheet(f"""
                QMessageBox {{ background: {WHITE}; }}
                QLabel {{ color: {TEXT_DARK}; font-size: 14px; }}
                QPushButton {{
                    min-width: 80px; min-height: 32px;
                    border-radius: 16px; font-size: 13px;
                    background: {BLUE_PRIMARY}; color: {WHITE}; border: none;
                }}
            """)
            ok.exec()

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
        current_text = self.search_bar.get_text()
        if current_text:
            query = current_text

        genres   = self.filter_panel.selected_genres()
        statuses = self.filter_panel.selected_statuses()
        year     = self.filter_panel.selected_year()

        filtered_lr = _filter_entries(self._all_last_read, query, genres, statuses, year)
        filtered_mb = _filter_entries(self._all_my_books,  query, genres, statuses, year)

        # Kirim list entries (bukan manga) agar entry.id tersedia untuk delete
        self.last_read_row.load_cards(filtered_lr[:12], self.main_window.go_detail)
        self.my_books_row.load_cards(filtered_mb,       self.main_window.go_detail)

    # ── Public ────────────────────────────────────────────────────────────────

    def refresh(self):
        self._start_loading()
