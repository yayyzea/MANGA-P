from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QLineEdit, QCheckBox, QGridLayout, QMessageBox,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QSize, QTimer, QPropertyAnimation, QEasingCurve, QEvent, QPoint
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

        self._input_shadow = QGraphicsDropShadowEffect(input_wrapper)
        self._input_shadow.setBlurRadius(12)
        self._input_shadow.setOffset(0, 4)
        self._input_shadow.setColor(QColor(0, 0, 0, 60))
        input_wrapper.setGraphicsEffect(self._input_shadow)

        self._input_anim = QPropertyAnimation(input_wrapper, b"pos")
        self._input_anim.setDuration(150)
        self._input_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
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

        self._filter_shadow = QGraphicsDropShadowEffect(self.filter_btn)
        self._filter_shadow.setBlurRadius(12)
        self._filter_shadow.setOffset(0, 4)
        self._filter_shadow.setColor(QColor(0, 0, 0, 60))
        self.filter_btn.setGraphicsEffect(self._filter_shadow)

        self._filter_anim = QPropertyAnimation(self.filter_btn, b"pos")
        self._filter_anim.setDuration(150)
        self._filter_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
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

        self._trash_shadow = QGraphicsDropShadowEffect(self.trash_btn)
        self._trash_shadow.setBlurRadius(12)
        self._trash_shadow.setOffset(0, 4)
        self._trash_shadow.setColor(QColor(0, 0, 0, 60))
        self.trash_btn.setGraphicsEffect(self._trash_shadow)

        self._trash_anim = QPropertyAnimation(self.trash_btn, b"pos")
        self._trash_anim.setDuration(150)
        self._trash_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
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
                self._hover_in(self._input_shadow, self._input_anim, self._input_wrapper)
            elif obj == self.filter_btn:
                self._hover_in(self._filter_shadow, self._filter_anim, self.filter_btn)
            elif obj == self.trash_btn:
                self._hover_in(self._trash_shadow, self._trash_anim, self.trash_btn)
        elif event.type() == QEvent.Type.Leave:
            if obj == self._input_wrapper:
                self._hover_out(self._input_shadow, self._input_anim, self._input_wrapper)
            elif obj == self.filter_btn:
                self._hover_out(self._filter_shadow, self._filter_anim, self.filter_btn)
            elif obj == self.trash_btn:
                self._hover_out(self._trash_shadow, self._trash_anim, self.trash_btn)
        return super().eventFilter(obj, event)

    def _hover_in(self, shadow, anim, widget):
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 100))
        anim.stop()
        anim.setStartValue(widget.pos())
        anim.setEndValue(widget.pos() + QPoint(0, -4))
        anim.start()

    def _hover_out(self, shadow, anim, widget):
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        anim.stop()
        anim.setStartValue(widget.pos())
        anim.setEndValue(widget.pos() + QPoint(0, 4))
        anim.start()


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
                background: {WHITE};
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


class _CircleCheck(QWidget):
    """Tombol centang bulat custom — transparan saat unchecked, hijau + ceklis saat checked."""

    SIZE = 26

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def set_checked(self, val: bool):
        self._checked = val
        self.update()

    def is_checked(self) -> bool:
        return self._checked

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self.update()
        event.accept()  # jangan propagasi ke MangaCard parent

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPen, QBrush, QPainterPath, QColor as _QC
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self.SIZE
        r = s / 2

        if self._checked:
            # Lingkaran hijau solid
            p.setBrush(QBrush(_QC("#7ec8a0")))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(0, 0, s, s)
            # Ceklis putih
            pen = QPen(_QC(WHITE), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.drawLine(int(s*0.22), int(s*0.50), int(s*0.44), int(s*0.72))
            p.drawLine(int(s*0.44), int(s*0.72), int(s*0.78), int(s*0.30))
        else:
            # Lingkaran transparan dengan border putih
            p.setBrush(QBrush(_QC(255, 255, 255, 180)))
            p.setPen(QPen(_QC(WHITE), 2.2))
            p.drawEllipse(1, 1, s-2, s-2)


class SelectableMangaCard(QWidget):
    clicked = pyqtSignal(int)

    # Margin ekstra di sekeliling card agar QGraphicsDropShadowEffect
    # punya ruang render dan tidak terpotong oleh batas widget.
    _SHADOW_MARGIN = 10

    def __init__(self, manga, entry_id: int, show_labels: bool = True, parent=None):
        super().__init__(parent)
        self.manga    = manga
        self.entry_id = entry_id
        self._checkbox = None

        # Jangan pakai WA_StyledBackground — biarkan transparan secara default
        # agar shadow dari MangaCard child tidak ter-clip.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setStyleSheet("background: transparent;")

        m = self._SHADOW_MARGIN
        layout = QVBoxLayout(self)
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(0)

        self._card = MangaCard(manga, show_labels=show_labels)
        self._card.clicked.connect(self.clicked)
        layout.addWidget(self._card)

        self.setSizePolicy(self._card.sizePolicy())

    def set_select_mode(self, active: bool):
        if active:
            if self._checkbox is None:
                self._checkbox = _CircleCheck(self._card)  # parent = _card
                self._checkbox.move(10, 10)
                self._checkbox.raise_()
            self._checkbox.set_checked(False)
            self._checkbox.setVisible(True)
        else:
            if self._checkbox:
                self._checkbox.setVisible(False)

    def is_selected(self) -> bool:
        return self._checkbox is not None and self._checkbox.is_checked()


class CardRow(QWidget):
    """Menampilkan kartu manga dalam grid yang wrap otomatis — tidak ada scroll horizontal sendiri."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selectable_cards: list[SelectableMangaCard] = []
        self._scroll_area = None  # referensi ke QScrollArea induk
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._build()

    def _build(self):
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 8, 0, 8)
        self._grid.setSpacing(16)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    def set_scroll_area(self, scroll_area):
        """Simpan referensi scroll area agar bisa ambil lebar viewport yang akurat."""
        self._scroll_area = scroll_area

    def _available_width(self):
        """Ambil lebar yang tersedia — dari viewport scroll area jika ada, fallback ke self.width()."""
        if self._scroll_area is not None:
            vp_w = self._scroll_area.viewport().width()
            if vp_w > 10:
                # kurangi margin konten (24 kiri + 24 kanan)
                return vp_w - 48
        w = self.width()
        return w if w > 10 else 800

    def _get_cols_and_card_w(self):
        """Hitung jumlah kolom dan lebar kartu secara dinamis — sama persis dengan homepage."""
        avail = self._available_width()
        spacing = self._grid.spacing()
        for cols in [6, 5, 4, 3, 2, 1]:
            if avail >= cols * 110 + spacing * (cols - 1):
                break
        card_w = min(_CARD_MAX_W, max(_CARD_MIN_W, (avail - spacing * (cols - 1)) // cols))
        return cols, card_w

    def _relayout(self):
        """Susun ulang semua widget ke grid sesuai lebar saat ini, termasuk resize kartu."""
        widgets = []
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                widgets.append(item.widget())
        if not widgets:
            return
        cols, card_w = self._get_cols_and_card_w()
        cover_w = card_w - _PAD * 2
        for i, w in enumerate(widgets):
            # SelectableMangaCard punya shadow margin di setiap sisi
            sm = getattr(w, '_SHADOW_MARGIN', 0)
            w.setFixedWidth(card_w + sm * 2)
            # update lebar label jika ada (SelectableMangaCard wraps MangaCard)
            inner = getattr(w, '_card', w)
            if hasattr(inner, 'lbl_title'):
                inner.lbl_title.setMaximumWidth(cover_w)
            if hasattr(inner, 'lbl_genre'):
                inner.lbl_genre.setMaximumWidth(cover_w)
            self._grid.addWidget(w, i // cols, i % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(50, self._relayout)

    def show_placeholders(self, count=6):
        self._clear()
        cols, card_w = self._get_cols_and_card_w()
        card_h = int(card_w * _ASPECT) + 48  # cover + label area
        for i in range(count):
            ph = QWidget()
            ph.setFixedSize(card_w, card_h)
            ph.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            ph.setStyleSheet(f"background: {BLUE_CARD}; border-radius: {CARD_RADIUS}px;")
            self._grid.addWidget(ph, i // cols, i % cols)

    def load_cards(self, entries, on_click):
        self._clear()
        self._selectable_cards = []
        if not entries:
            lbl = QLabel("No manga found.")
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
            self._grid.addWidget(lbl, 0, 0)
            return
        cols, card_w = self._get_cols_and_card_w()
        cover_w = card_w - _PAD * 2
        idx = 0
        for entry in entries:
            manga = entry.manga
            if not manga:
                continue
            card = SelectableMangaCard(manga, entry_id=entry.id, show_labels=True)
            card.clicked.connect(on_click)
            sm = card._SHADOW_MARGIN
            card.setFixedWidth(card_w + sm * 2)
            inner = card._card
            if hasattr(inner, 'lbl_title'):
                inner.lbl_title.setMaximumWidth(cover_w)
            if hasattr(inner, 'lbl_genre'):
                inner.lbl_genre.setMaximumWidth(cover_w)
            self._selectable_cards.append(card)
            self._grid.addWidget(card, idx // cols, idx % cols)
            idx += 1

        # Relayout ulang setelah render untuk koreksi ukuran (sama seperti homepage)
        QTimer.singleShot(150, self._relayout)

    def set_select_mode(self, active: bool):
        for card in self._selectable_cards:
            card.set_select_mode(active)

    def get_selected_entry_ids(self) -> list:
        return [c.entry_id for c in self._selectable_cards if c.is_selected()]

    def _clear(self):
        self._selectable_cards = []
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class DeleteConfirmBar(QWidget):
    cancelled = pyqtSignal()
    confirmed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"background: {WHITE};")
        self.setFixedHeight(0)
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

        cancel_btn = QPushButton("Cancel")
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
            QPushButton:hover {{ background: #ede8f8; }}
        """)
        cancel_btn.clicked.connect(self.cancelled)
        layout.addWidget(cancel_btn)

        self.delete_btn = QPushButton()
        icon_px = QPixmap(str(_ICON_DIR / "trash.png"))
        if not icon_px.isNull():
            self.delete_btn.setIcon(QIcon(icon_px))
            self.delete_btn.setIconSize(QSize(18, 18))
            self.delete_btn.setText("  Delete")
        else:
            self.delete_btn.setText("🗑  Delete")

        self.delete_btn.setFixedHeight(38)
        self.delete_btn.setMinimumWidth(100)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: #e87e7c; border: none;
                border-radius: 19px;
                color: {WHITE};
                font-size: 14px; font-weight: 700;
                padding: 0 16px;
            }}
            QPushButton:hover   {{ background: #c85a58; }}
            QPushButton:disabled {{ background: #ffd6d6; color: #e8a8a8; }}
        """)
        self.delete_btn.clicked.connect(self.confirmed)
        layout.addWidget(self.delete_btn)

    def setVisible(self, visible: bool):
        self.setFixedHeight(64 if visible else 0)
        super().setVisible(visible)

    def update_count(self, count: int):
        if count == 0:
            self.info_lbl.setText("Select the manga you want to delete")
            self.delete_btn.setEnabled(False)
        else:
            self.info_lbl.setText(f"{count} manga selected")
            self.delete_btn.setEnabled(True)


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

        self.search_bar = LibrarySearchBar()
        self.search_bar.search_triggered.connect(self._apply_filters)
        self.search_bar.filter_toggled.connect(self._toggle_filter)
        self.search_bar.delete_toggled.connect(self._set_delete_mode)
        root.addWidget(self.search_bar)

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
        self.last_read_row.set_scroll_area(scroll)
        self.last_read_row.show_placeholders(6)
        cl.addWidget(self.last_read_row)

        cl.addWidget(self._sec("My Books"))
        self.my_books_row = CardRow()
        self.my_books_row.set_scroll_area(scroll)
        self.my_books_row.show_placeholders(6)
        cl.addWidget(self.my_books_row)

        cl.addStretch()
        scroll.setWidget(content)
        self.body.addWidget(scroll, stretch=1)

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

        self.last_read_row.load_cards(filtered_lr[:12], self.main_window.go_detail)
        self.my_books_row.load_cards(filtered_mb,       self.main_window.go_detail)

    def refresh(self):
        self._start_loading()