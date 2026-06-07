from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QLineEdit, QCheckBox, QGridLayout, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QSize, QTimer, QEvent, QPoint
from PyQt6.QtGui import QColor, QPalette, QPixmap, QIcon
from pathlib import Path

_ICON_DIR = Path(__file__).parent.parent / "assets"

from .theme import (
    BLUE_DARK, BLUE_PRIMARY, BLUE_CARD, BLUE_LIGHT, WHITE,
    TEXT_DARK, TEXT_MUTED,
    TOPBAR_HEIGHT, CARD_W, CARD_H, CARD_RADIUS
)
from .widgets import MangaCard, _CARD_MIN_W, _CARD_MAX_W, _ASPECT, _PAD
from .add_manga_form import AddMangaForm
from .library_delete import (
    CardRow, DeleteConfirmBar, SelectableMangaCard,
    _STATUS_OPTIONS, _STATUS_COLORS,
    _COMBO_STYLE_CHAPTER, _status_combo_style,
)


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


class CollectionLoader(QThread):
    finished = pyqtSignal(list, list)

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    def run(self):
        try:
            from database import get_session
            from models.user_collection import UserCollection
            from sqlalchemy.orm import joinedload

            session = get_session()
            try:
                entries = (
                    session.query(UserCollection)
                    .filter(UserCollection.user_id == self.user_id)
                    .options(joinedload(UserCollection.manga))
                    .order_by(UserCollection.updated_at.desc())
                    .all()
                )

                for entry in entries:
                    if entry.manga:
                        _ = entry.manga.title
                        _ = entry.manga.genres
                        _ = entry.manga.cover_url

            finally:
                session.close()

            last_read = [
                e for e in entries
                if e.status in ("Reading", "Completed") and e.manga
            ][:48]

            my_books = [e for e in entries if e.manga]

            self.finished.emit(last_read, my_books)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[LibraryPage] Load error: {e}")
            self.finished.emit([], [])


class LibrarySearchBar(QWidget):
    search_triggered  = pyqtSignal(str)
    filter_toggled    = pyqtSignal()
    delete_toggled    = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SearchBar")
        self.setFixedHeight(TOPBAR_HEIGHT)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(BLUE_PRIMARY))
        self.setPalette(pal)
        # Hover/pressed state untuk filter dan trash btn
        self._filter_hovered = False
        self._filter_pressed = False
        self._trash_hovered  = False
        self._trash_pressed  = False
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        # ── Search input wrapper (icon inside pill) ──
        input_wrapper = QWidget()
        input_wrapper.setStyleSheet(f"""
            QWidget {{
                background: {WHITE};
                border-radius: 22px;
            }}
        """)
        input_wrapper.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        input_wrapper.setFixedHeight(44)
        wrapper_layout = QHBoxLayout(input_wrapper)
        wrapper_layout.setContentsMargins(14, 0, 14, 0)
        wrapper_layout.setSpacing(8)

        icon = QLabel()
        icon.setFixedSize(18, 18)
        _sx = QPixmap(str(_ICON_DIR / "search.png"))
        if not _sx.isNull():
            icon.setPixmap(_sx.scaled(18, 18,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            icon.setText("🔍")
        icon.setStyleSheet("background: transparent;")
        wrapper_layout.addWidget(icon)

        self.input = QLineEdit()
        self.input.setObjectName("SearchInput")
        self.input.setPlaceholderText("Search Mangas...")
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; border: none;
                padding: 0; font-size: 14px; color: {TEXT_DARK};
            }}
        """)
        self.input.textChanged.connect(lambda t: self.search_triggered.emit(t.strip()))
        self.input.returnPressed.connect(
            lambda: self.search_triggered.emit(self.input.text().strip())
        )
        wrapper_layout.addWidget(self.input)

        self._input_wrapper = input_wrapper
        input_wrapper.installEventFilter(self)

        layout.addWidget(input_wrapper)

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
            QPushButton:checked {{ background: #ddd5f5; }}
        """)

        self.filter_btn.installEventFilter(self)

        self.filter_btn.clicked.connect(self.filter_toggled)
        layout.addWidget(self.filter_btn)

        self.trash_btn = QPushButton()
        _tx = QPixmap(str(_ICON_DIR / "trash.png"))
        if not _tx.isNull():
            self.trash_btn.setIcon(QIcon(_tx))
            self.trash_btn.setIconSize(QSize(20, 20))
        else:
            self.trash_btn.setText("🗑")
        self.trash_btn.setObjectName("TrashBtn")
        self.trash_btn.setFixedSize(36, 36)
        self.trash_btn.setCheckable(True)
        self.trash_btn.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE}; border: none;
                border-radius: 18px; font-size: 16px; color: #c85a58;
            }}
            QPushButton:checked {{
                background: #e87e7c; color: #fff5f5;
            }}
        """)

        self.trash_btn.installEventFilter(self)

        self.trash_btn.toggled.connect(self.delete_toggled)
        layout.addWidget(self.trash_btn)

    def reset_trash(self):
        self.trash_btn.blockSignals(True)
        self.trash_btn.setChecked(False)
        self.trash_btn.blockSignals(False)

    def get_text(self) -> str:
        return self.input.text().strip()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            if obj == self._input_wrapper:
                self._set_input_hover(True)
            elif obj == self.filter_btn:
                self._set_btn_hover(self.filter_btn, "filter", True)
            elif obj == self.trash_btn:
                self._set_btn_hover(self.trash_btn, "trash", True)
        elif event.type() == QEvent.Type.Leave:
            if obj == self._input_wrapper:
                self._set_input_hover(False)
            elif obj == self.filter_btn:
                self._set_btn_hover(self.filter_btn, "filter", False)
            elif obj == self.trash_btn:
                self._set_btn_hover(self.trash_btn, "trash", False)
        elif event.type() == QEvent.Type.MouseButtonPress:
            if obj == self.filter_btn:
                self._set_btn_pressed(self.filter_btn, "filter", True)
            elif obj == self.trash_btn:
                self._set_btn_pressed(self.trash_btn, "trash", True)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if obj == self.filter_btn:
                self._set_btn_pressed(self.filter_btn, "filter", False)
            elif obj == self.trash_btn:
                self._set_btn_pressed(self.trash_btn, "trash", False)
        return super().eventFilter(obj, event)

    def _set_input_hover(self, hovered: bool):
        bg = "#E8F4FB" if hovered else WHITE
        self._input_wrapper.setStyleSheet(f"""
            QWidget {{
                background: {bg};
                border-radius: 22px;
            }}
        """)

    def _set_btn_hover(self, btn: QPushButton, kind: str, hovered: bool):
        setattr(self, f"_{kind}_hovered", hovered)
        self._apply_btn_style(btn, kind)

    def _set_btn_pressed(self, btn: QPushButton, kind: str, pressed: bool):
        setattr(self, f"_{kind}_pressed", pressed)
        self._apply_btn_style(btn, kind)

    def _apply_btn_style(self, btn: QPushButton, kind: str):
        hovered = getattr(self, f"_{kind}_hovered", False)
        pressed = getattr(self, f"_{kind}_pressed", False)

        if kind == "trash":
            if pressed:
                bg = "#9DCCE8"
            elif hovered:
                bg = "#B8DFF0"
            else:
                bg = WHITE
            checked_bg = "#e87e7c"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg}; border: none;
                    border-radius: 18px; font-size: 16px; color: #c85a58;
                }}
                QPushButton:checked {{
                    background: {checked_bg}; color: #fff5f5;
                }}
            """)
        else:  # filter
            if pressed:
                bg = "#9DCCE8"
            elif hovered:
                bg = "#B8DFF0"
            else:
                bg = WHITE
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg}; border: none;
                    border-radius: 18px; font-size: 16px; color: {BLUE_PRIMARY};
                }}
                QPushButton:checked {{ background: #ddd5f5; }}
            """)


class LibraryFilterPanel(QWidget):
    apply_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        self._genre_cbs  = {}
        self._status_cbs = {}
        self._year_input = None
        self._custom_genre_input = None
        self._build()
        self.setVisible(False)

    def _build(self):
        from PyQt6.QtWidgets import QScrollArea
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 0, 12, 12)
        outer.setSpacing(0)

        # Scroll area untuk semua konten filter
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        inner_widget = QWidget()
        inner_widget.setStyleSheet("background: transparent;")
        root = QVBoxLayout(inner_widget)
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
            g_grid.addWidget(cb, i // 2, i % 2)
        root.addLayout(g_grid)

        root.addWidget(self._subheading("Other genre"))
        self._custom_genre_input = QLineEdit()
        self._custom_genre_input.setFixedHeight(32)
        self._custom_genre_input.setMaximumWidth(160)
        self._custom_genre_input.setPlaceholderText("e.g. Isekai")
        self._custom_genre_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: 1.5px solid {BLUE_LIGHT};
                border-radius: 6px; padding: 4px 10px;
                font-size: 13px; color: {TEXT_DARK};
            }}
            QLineEdit:focus {{ border-color: {BLUE_PRIMARY}; }}
        """)
        root.addWidget(self._custom_genre_input)

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

        root.addWidget(self._subheading("Year"))
        self._year_input = QLineEdit()
        self._year_input.setFixedHeight(32)
        self._year_input.setMaximumWidth(110)
        self._year_input.setPlaceholderText("e.g. 2023")
        self._year_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: 1.5px solid {BLUE_LIGHT};
                border-radius: 6px; padding: 4px 10px;
                font-size: 13px; color: {TEXT_DARK};
            }}
            QLineEdit:focus {{ border-color: {BLUE_PRIMARY}; }}
        """)
        root.addWidget(self._year_input)
        root.addStretch()

        scroll.setWidget(inner_widget)
        outer.addWidget(scroll, stretch=1)

        # Apply button di luar scroll, selalu nempel di bawah
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedHeight(46)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
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
        outer.addWidget(apply_btn)

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
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background: {BLUE_PRIMARY}; border-color: {BLUE_PRIMARY};
            }}
        """

    def selected_genres(self) -> list:
        genres = [g for g, cb in self._genre_cbs.items() if cb.isChecked()]
        if self._custom_genre_input:
            custom = self._custom_genre_input.text().strip()
            if custom:
                genres.append(custom)
        return genres

    def selected_statuses(self) -> list: return [s for s, cb in self._status_cbs.items() if cb.isChecked()]
    def selected_year(self)     -> str:  return (self._year_input.text() or "").strip()

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())


class LibraryPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._loader = None
        self._all_last_read: list = []
        self._all_my_books:  list = []
        self._build()
        self._start_loading()

    def adjust_content_width(self):
        if hasattr(self, 'scroll') and self.scroll and self.scroll.widget():
            vp_w = self.scroll.viewport().width()
            if vp_w > 10:
                self.scroll.widget().setFixedWidth(vp_w)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_content_width()

    def showEvent(self, event):
        super().showEvent(event)
        # Force correct layout every time this page becomes visible
        QTimer.singleShot(50, self.adjust_content_width)
        QTimer.singleShot(100, self.last_read_row._relayout)
        QTimer.singleShot(100, self.my_books_row._relayout)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.search_bar = LibrarySearchBar()
        self.search_bar.search_triggered.connect(self._apply_filters)
        self.search_bar.filter_toggled.connect(self._toggle_filter)
        self.search_bar.delete_toggled.connect(self._set_delete_mode)
        root.addWidget(self.search_bar)

        self.body = QHBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(20)

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
        self.last_read_row.set_scroll_area(self.scroll)
        self.last_read_row.show_placeholders(6)
        cl.addWidget(self.last_read_row)

        cl.addWidget(self._sec("My Books"))
        self.my_books_row = CardRow()
        self.my_books_row.set_scroll_area(self.scroll)
        self.my_books_row.show_placeholders(6)
        cl.addWidget(self.my_books_row)

        cl.addStretch()
        self.scroll.setWidget(content)
        self.body.addWidget(self.scroll, stretch=1)

        self.filter_panel = LibraryFilterPanel()
        self.filter_panel.apply_clicked.connect(self._apply_filters)
        self.body.addWidget(self.filter_panel)

        root.addLayout(self.body, stretch=1)

        self.confirm_bar = DeleteConfirmBar()
        self.confirm_bar.cancelled.connect(self._cancel_delete_mode)
        self.confirm_bar.confirmed.connect(self._confirm_delete)
        root.addWidget(self.confirm_bar)

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

    def _toggle_filter(self):
        self.filter_panel.toggle_visibility()
        self._add_btn.setVisible(not self.filter_panel.isVisible())
        
        # Schedul relayout setelah layout engine selesai menyesuaikan lebar
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self.adjust_content_width)
        QTimer.singleShot(100, self.last_read_row._relayout)
        QTimer.singleShot(100, self.my_books_row._relayout)


    def _open_add_form(self):
        try:
            dialog = AddMangaForm(parent=self)
            dialog.manga_added.connect(self._on_manga_added)
            dialog.exec()
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _on_manga_added(self, manga_id: int):
        self._start_loading()
        if hasattr(self.main_window, 'show_toast'):
            self.main_window.show_toast("Manga successfully added!")

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
        self.search_bar.reset_trash()
        self._set_delete_mode(False)

    def _update_selection_count(self):
        ids = list(dict.fromkeys(
            self.last_read_row.get_selected_entry_ids()
            + self.my_books_row.get_selected_entry_ids()
        ))
        self.confirm_bar.update_count(len(ids))

    def _style_msgbox(self, msg):
        """Force QMessageBox pakai warna terang agar tidak kena dark theme sistem."""
        from PyQt6.QtGui import QPalette, QColor as _QC
        pal = msg.palette()
        pal.setColor(QPalette.ColorRole.Window,     _QC(BLUE_DARK))
        pal.setColor(QPalette.ColorRole.WindowText, _QC(WHITE))
        pal.setColor(QPalette.ColorRole.ButtonText, _QC(WHITE))
        pal.setColor(QPalette.ColorRole.Text,       _QC(WHITE))
        msg.setPalette(pal)
        msg.setStyleSheet(f"""
            QMessageBox {{ background: {BLUE_DARK}; font-family: Arial; }}
            QLabel {{ color: {WHITE}; background: transparent; font-size: 13px; }}
            QPushButton {{
                background: rgba(255,255,255,0.15); color: {WHITE};
                border: 1px solid rgba(255,255,255,0.40); border-radius: 12px;
                padding: 6px 18px; font-size: 12px; font-weight: 600; min-width: 80px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.28); }}
        """)

    def _confirm_delete(self):
        ids = list(dict.fromkeys(
            self.last_read_row.get_selected_entry_ids()
            + self.my_books_row.get_selected_entry_ids()
        ))
        if not ids:
            return

        count = len(ids)
        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Confirmation")
        msg.setText(
            f"Delete {count} manga from My Library?\n\n"
            "This action cannot be undone."
        )
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        msg.button(QMessageBox.StandardButton.Yes).setText("Yes, Delete")
        msg.button(QMessageBox.StandardButton.Cancel).setText("Cancel")
        self._style_msgbox(msg)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self._do_delete(ids)

    def _do_delete(self, entry_ids: list):
        try:
            from services.collection_service import CollectionService
            svc = CollectionService()
            uid = self.main_window.current_user["id"]

            deleted = sum(1 for eid in entry_ids if svc.delete(eid, user_id=uid))
            self._cancel_delete_mode()
            self._start_loading()
            if deleted:
                ok = QMessageBox(self)
                ok.setWindowTitle("Success")
                ok.setText(f"{deleted} manga successfully deleted from My Library.")
                ok.setStandardButtons(QMessageBox.StandardButton.Ok)
                self._style_msgbox(ok)
                ok.exec()
        except Exception as e:
            print(f"[LibraryPage] Delete error: {e}")

    def _start_loading(self):
        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()
        self.last_read_row.show_placeholders(6)
        self.my_books_row.show_placeholders(6)
        user_id = self.main_window.current_user["id"]
        self._loader = CollectionLoader(user_id=user_id)
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    @pyqtSlot(list, list)
    def _on_loaded(self, lr_entries, mb_entries):
        self._all_last_read = lr_entries
        self._all_my_books  = mb_entries
        self._apply_filters()

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

        self.last_read_row.load_cards(filtered_lr[:12], self.main_window.go_detail,
                                      mode="chapter", on_update=self._update_entry)
        self.my_books_row.load_cards(filtered_mb,       self.main_window.go_detail,
                                     mode="status",  on_update=self._update_entry)

        # Force correct layout on initial load — cascade relayouts so cards
        # never appear stacked/overlapping before the user interacts
        QTimer.singleShot(50, self.adjust_content_width)
        QTimer.singleShot(100, self.last_read_row._relayout)
        QTimer.singleShot(100, self.my_books_row._relayout)
        QTimer.singleShot(300, self.adjust_content_width)
        QTimer.singleShot(350, self.last_read_row._relayout)
        QTimer.singleShot(350, self.my_books_row._relayout)

    def _update_entry(self, entry_id: int, **kwargs):
        """Update current_chapter atau status langsung dari dropdown di card."""
        try:
            from services.collection_service import CollectionService
            CollectionService().update(collection_id=entry_id, **kwargs)
        except Exception as e:
            print(f"[LibraryPage] update_entry error: {e}")

    def refresh(self):
        self._start_loading()