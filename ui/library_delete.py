"""
library_delete.py
─────────────────
Semua komponen yang berkaitan dengan fitur hapus (delete) di Library:

  • _CircleCheck         — tombol centang bulat custom di atas kartu
  • SelectableMangaCard  — kartu manga yang bisa dipilih untuk dihapus
  • CardRow              — grid kartu yang mendukung select-mode
  • DeleteConfirmBar     — bar konfirmasi di bagian bawah saat mode hapus aktif

  Helper:
  • _STATUS_OPTIONS, _STATUS_COLORS
  • _COMBO_STYLE_CHAPTER, _status_combo_style()
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QComboBox, QSizePolicy, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QColor, QPixmap, QIcon
from pathlib import Path

_ICON_DIR = Path(__file__).parent.parent / "assets"

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, WHITE,
    TEXT_MUTED, CARD_RADIUS
)
from .widgets import MangaCard, _CARD_MIN_W, _ASPECT, _PAD


# ── Status helpers ─────────────────────────────────────────────────────────────

_STATUS_OPTIONS = ["Plan to Read", "Reading", "Completed", "Dropped"]

_STATUS_COLORS = {
    "Plan to Read": ("#f5a623", "#7a4a00"),   # oranye
    "Reading":      ("#6aabf7", "#0d3a6e"),   # biru
    "Completed":    ("#4caf7d", "#1a4d30"),   # hijau
    "Dropped":      ("#c0392b", "#ffffff"),   # merah
}

_COMBO_STYLE_CHAPTER = """
    QComboBox {
        background: #9abe7c;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 600;
    }
    QComboBox::drop-down { border: none; width: 18px; }
    QComboBox QAbstractItemView {
        background: #ffffff;
        color: #2d5a1b;
        selection-background-color: #c8e6a8;
        border: 1px solid #9abe7c;
        font-size: 11px;
    }
"""

def _status_combo_style(status: str) -> str:
    bg, fg = _STATUS_COLORS.get(status, ("#f5a623", "#7a4a00"))
    return f"""
        QComboBox {{
            background: {bg};
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
        }}
        QComboBox::drop-down {{ border: none; width: 18px; }}
        QComboBox QAbstractItemView {{
            background: #ffffff;
            color: {fg};
            selection-background-color: {bg}44;
            border: 1px solid {bg};
            font-size: 11px;
        }}
    """


# ── _CircleCheck ───────────────────────────────────────────────────────────────

class _CircleCheck(QWidget):
    """Tombol centang bulat custom — transparan saat unchecked, hijau + ceklis saat checked."""

    SIZE = 26
    toggled = pyqtSignal(bool)

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
            self.toggled.emit(self._checked)
        event.accept()  # jangan propagasi ke MangaCard parent

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPen, QBrush, QColor as _QC
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self.SIZE

        if self._checked:
            # Lingkaran hijau solid
            p.setBrush(QBrush(_QC("#7ec8a0")))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(0, 0, s, s)
            # Ceklis putih
            pen = QPen(_QC(WHITE), 2.5, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.drawLine(int(s*0.22), int(s*0.50), int(s*0.44), int(s*0.72))
            p.drawLine(int(s*0.44), int(s*0.72), int(s*0.78), int(s*0.30))
        else:
            # Lingkaran transparan dengan border putih
            p.setBrush(QBrush(_QC(255, 255, 255, 180)))
            p.setPen(QPen(_QC(WHITE), 2.2))
            p.drawEllipse(1, 1, s-2, s-2)


# ── SelectableMangaCard ────────────────────────────────────────────────────────

class SelectableMangaCard(QWidget):
    clicked = pyqtSignal(int)

    _SHADOW_MARGIN = 6

    def __init__(self, manga, entry_id: int, show_labels: bool = True,
                 mode: str = None, entry=None, on_update=None, parent=None):
        super().__init__(parent)
        self.manga      = manga
        self.entry_id   = entry_id
        self._checkbox  = None
        self._mode      = mode
        self._entry     = entry
        self._on_update = on_update
        self._combo     = None
        self._select_mode = False

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setStyleSheet("background: transparent;")

        m = self._SHADOW_MARGIN
        outer = QVBoxLayout(self)
        outer.setContentsMargins(m, m, m, m)
        outer.setSpacing(0)

        self._card = MangaCard(manga, show_labels=True)
        if hasattr(self._card, 'lbl_genre'):
            self._card.lbl_genre.setVisible(False)
        self._card.clicked.connect(self._on_card_clicked)
        # Intercept press di card agar select mode bisa toggle checkbox sebelum release
        self._card.mousePressEvent = self._intercept_card_press
        self._card.mouseReleaseEvent = self._intercept_card_release
        outer.addWidget(self._card)

        if mode in ("chapter", "status"):
            combo = QComboBox()
            combo.setStyleSheet(_COMBO_STYLE_CHAPTER if mode == "chapter" else _status_combo_style(
                (entry.status if entry and entry.status else "Plan to Read")
            ))

            if mode == "chapter":
                chapters = manga.chapters or 0
                current  = (entry.current_chapter or 0) if entry else 0
                max_ch   = chapters if chapters > 0 else max(current + 10, 10)
                for ch in range(1, max_ch + 1):
                    combo.addItem(f"Chapter {ch}", ch)
                if current > 0:
                    idx = combo.findData(current)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
                combo.currentIndexChanged.connect(self._on_chapter_changed)

            elif mode == "status":
                combo.addItems(_STATUS_OPTIONS)
                if entry and entry.status:
                    idx = combo.findText(entry.status)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
                combo.currentIndexChanged.connect(self._on_status_changed)

            self._card.layout().setContentsMargins(_PAD, _PAD, _PAD, _PAD)
            self._card.layout().addWidget(combo)
            self._combo = combo

        self.setSizePolicy(self._card.sizePolicy())

    def _intercept_card_press(self, event):
        from PyQt6.QtWidgets import QWidget
        if self._select_mode and event.button() == Qt.MouseButton.LeftButton:
            if self._checkbox:
                self._checkbox.set_checked(not self._checkbox.is_checked())
            event.accept()
        else:
            # Normal press — set _pressed state di MangaCard
            if event.button() == Qt.MouseButton.LeftButton:
                self._card._pressed = True
                self._card.update()
            event.accept()

    def _intercept_card_release(self, event):
        if self._select_mode:
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._card._pressed = False
            self._card.update()
            if self._card.rect().contains(event.pos()):
                self.clicked.emit(self.manga.id)
        event.accept()

    def _on_card_clicked(self, manga_id: int):
        # Hanya dipanggil saat tidak di select mode (fallback)
        if not self._select_mode:
            self.clicked.emit(manga_id)

    def _on_chapter_changed(self, idx):
        if self._on_update and self._entry and self._combo:
            ch = self._combo.itemData(idx) or 0
            self._on_update(self._entry.id, current_chapter=ch)

    def _on_status_changed(self, idx):
        if self._on_update and self._entry and self._combo:
            status = self._combo.currentText()
            self._combo.setStyleSheet(_status_combo_style(status))
            self._on_update(self._entry.id, status=status)

    def _place_combo(self):
        pass  # tidak dipakai lagi, combo sudah di layout

    def set_select_mode(self, active: bool):
        self._select_mode = active
        if active:
            if self._checkbox is None:
                self._checkbox = _CircleCheck(self._card)
                self._checkbox.move(10, 10)
                self._checkbox.raise_()
            self._checkbox.set_checked(False)
            self._checkbox.setVisible(True)
        else:
            if self._checkbox:
                self._checkbox.setVisible(False)

    def is_selected(self) -> bool:
        return self._checkbox is not None and self._checkbox.is_checked()


# ── CardRow ────────────────────────────────────────────────────────────────────

class CardRow(QWidget):
    """Menampilkan kartu manga dalam grid yang wrap otomatis — tidak ada scroll horizontal sendiri."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selectable_cards: list[SelectableMangaCard] = []
        self._scroll_area = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._build()

    def _build(self):
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 8, 0, 8)
        self._grid.setSpacing(10)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    def set_scroll_area(self, scroll_area):
        """Simpan referensi scroll area agar bisa ambil lebar viewport yang akurat."""
        self._scroll_area = scroll_area

    def _available_width(self):
        if self._scroll_area is not None:
            vp_w = self._scroll_area.viewport().width()
            if vp_w > 10:
                return vp_w - 48
        w = self.width()
        return w if w > 10 else 800

    def _get_cols_and_card_w(self):
        avail   = self._available_width()
        spacing = self._grid.spacing()
        for cols in [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]:
            if avail >= cols * 120 + spacing * (cols - 1):
                break
        card_w = min(120, max(_CARD_MIN_W, (avail - spacing * (cols - 1)) // cols))
        return cols, card_w

    def _relayout(self):
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
            sm = getattr(w, '_SHADOW_MARGIN', 0)
            w.setFixedWidth(card_w + sm * 2)
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
        card_h = int(card_w * _ASPECT) + 48
        for i in range(count):
            ph = QWidget()
            ph.setFixedSize(card_w, card_h)
            ph.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            ph.setStyleSheet(f"background: {BLUE_CARD}; border-radius: {CARD_RADIUS}px;")
            self._grid.addWidget(ph, i // cols, i % cols)

    def load_cards(self, entries, on_click, mode: str = None, on_update=None):
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
            card = SelectableMangaCard(
                manga, entry_id=entry.id,
                mode=mode, entry=entry, on_update=on_update
            )
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


# ── DeleteConfirmBar ───────────────────────────────────────────────────────────

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
            f"color: #1a1a2e; font-size: 14px; background: transparent;"
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
            QPushButton:hover    {{ background: #c85a58; }}
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