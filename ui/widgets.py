from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QSizePolicy, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QMutex, QMutexLocker
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor
import urllib.request
from collections import deque

from .theme import CARD_W, CARD_H, CARD_RADIUS, BLUE_CARD

_PAD = 8   # blue padding around the cover image (left/right/top/bottom)

# ── Image loader thread pool ──────────────────────────────────────────────────
# Batasi maksimal thread image loader yang berjalan bersamaan.
# Selebihnya masuk antrian dan dieksekusi saat slot kosong.
_MAX_IMAGE_THREADS = 6
_active_loaders: list = []
_pending_loaders: deque = deque()
_pool_mutex = QMutex()

def _try_start_next():
    """Jalankan loader berikutnya dari antrian jika ada slot kosong."""
    with QMutexLocker(_pool_mutex):
        # Bersihkan loader yang sudah selesai
        global _active_loaders
        _active_loaders = [l for l in _active_loaders if l.isRunning()]
        while _pending_loaders and len(_active_loaders) < _MAX_IMAGE_THREADS:
            loader = _pending_loaders.popleft()
            if not loader._cancelled:
                _active_loaders.append(loader)
                loader.start()

class ImageLoader(QThread):
    loaded = pyqtSignal(QPixmap)

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self._cancelled = False

    def enqueue(self):
        """Masukkan ke antrian pool, jangan langsung .start()."""
        with QMutexLocker(_pool_mutex):
            if len(_active_loaders) < _MAX_IMAGE_THREADS:
                _active_loaders.append(self)
                self.start()
            else:
                _pending_loaders.append(self)

    def cancel(self):
        self._cancelled = True

    def run(self):
        if self._cancelled:
            _try_start_next()
            return
        try:
            req = urllib.request.Request(
                self.url, headers={"User-Agent": "MANGA:P/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
            if not self._cancelled:
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                if not pixmap.isNull():
                    self.loaded.emit(pixmap)
        except Exception:
            pass
        finally:
            _try_start_next()

_CARD_MIN_W = 100   # lebar minimum card
_CARD_MAX_W = 220   # lebar maksimum card
_ASPECT     = CARD_H / CARD_W   # rasio tinggi:lebar cover (200/140 ≈ 1.43)

class MangaCoverLabel(QLabel):
    """Rounded-corner cover image — lebar mengikuti parent, tinggi proporsional."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._raw_pixmap = None
        self._pixmap = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(_CARD_MIN_W - _PAD * 2)
        # Tinggi awal — akan di-update ulang di resizeEvent saat lebar sudah diketahui
        self.setFixedHeight(round(CARD_W * _ASPECT))

    def _sync_height(self):
        # Pakai lebar aktual cover. Kalau belum ada (saat init), fallback ke CARD_W.
        # Tinggi = lebar × rasio aspek, minimum 80px
        w = self.width()
        if w < 10:  # belum di-layout, skip dulu — resizeEvent akan handle
            return
        self.setFixedHeight(max(80, round(w * _ASPECT)))

    def set_cover(self, pixmap: QPixmap):
        self._raw_pixmap = pixmap
        self._rescale()

    def _rescale(self):
        if not self._raw_pixmap:
            return
        w, h = self.width() or CARD_W, self.height() or CARD_H
        self._pixmap = self._raw_pixmap.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
)
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_height()
        self._rescale()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        inner_r = max(CARD_RADIUS - _PAD, 4)
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, inner_r, inner_r)
        painter.setClipPath(path)

        if self._pixmap:
            pw, ph = self._pixmap.width(), self._pixmap.height()
            x = (pw - w) // 2
            y = (ph - h) // 2
            painter.drawPixmap(0, 0, self._pixmap, x, y, w, h)
        else:
            painter.fillPath(path, QColor("#90d5e4"))  # 水のドレス teal placeholder

class MangaCard(QWidget):
    """
    Blue rounded card: _PAD px padding → cover image → title + genre text.
    The _PAD creates visible blue edges around the cover on all sides.
    Hover: card pops forward with slight scale via margin trick.
    """
    clicked = pyqtSignal(int)

    def __init__(self, manga, show_labels: bool = True, parent=None):
        super().__init__(parent)
        self.manga       = manga
        self.show_labels = show_labels
        self._loader     = None
        self._hovered    = False

        self.setObjectName("MangaCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setStyleSheet(
            f"border-radius: {CARD_RADIUS}px;"
        )

        # Animasi posisi (pop-out ke atas)
        self._build()
        self._load_cover()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(_PAD, _PAD, _PAD, _PAD)
        layout.setSpacing(6)

        self.cover = MangaCoverLabel()
        layout.addWidget(self.cover)

        if self.show_labels:
            self.lbl_title = QLabel(self.manga.title or "")
            self.lbl_title.setWordWrap(True)
            self.lbl_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.lbl_title.setStyleSheet(
                "color: #111111; font-size: 13px; font-weight: 600; background: transparent;"
            )
            from PyQt6.QtGui import QPalette, QColor as _QColor
            _pal = self.lbl_title.palette()
            _pal.setColor(QPalette.ColorRole.WindowText, _QColor("#111111"))
            self.lbl_title.setPalette(_pal)

            genres = self.manga.genres or ""
            all_genres = ", ".join(g.strip() for g in genres.split(",")) if genres else ""
            self.lbl_genre = QLabel(all_genres)
            self.lbl_genre.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.lbl_genre.setWordWrap(True)
            self.lbl_genre.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            self.lbl_genre.setStyleSheet(
                "color: rgba(0,0,0,0.60); font-size: 10px; background: transparent;"
            )
            _pal2 = self.lbl_genre.palette()
            _pal2.setColor(QPalette.ColorRole.WindowText, _QColor("#555555"))
            self.lbl_genre.setPalette(_pal2)

            layout.addWidget(self.lbl_title)
            layout.addWidget(self.lbl_genre)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setMinimumWidth(_CARD_MIN_W)
        self.setMaximumWidth(_CARD_MAX_W)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _load_cover(self):
        url = self.manga.cover_url
        if not url:
            return

        import os
        is_local = not url.startswith("http://") and not url.startswith("https://")
        if is_local:
            if os.path.isfile(url):
                px = QPixmap(url)
                if not px.isNull():
                    self.cover.set_cover(px)
            return

        self._loader = ImageLoader(url)
        self._loader.loaded.connect(self._on_image_loaded)
        self._loader.enqueue()

    @pyqtSlot(QPixmap)
    def _on_image_loaded(self, pixmap: QPixmap):
        self.cover.set_cover(pixmap)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), CARD_RADIUS, CARD_RADIUS)
        painter.fillPath(path, QColor("#DCF0F7"))
        super().paintEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.manga.id)

    def stop_loader(self):
        """Batalkan ImageLoader agar tidak membuang bandwidth jika card sudah dihapus."""
        if self._loader:
            self._loader.cancel()
        self._loader = None

    def closeEvent(self, event):
        self.stop_loader()
        super().closeEvent(event)

class MangaCardGrid(QWidget):
    card_clicked = pyqtSignal(int)

    def __init__(self, manga_list, cols: int = 4,
                 show_labels: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("MangaCardGrid")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        for manga in manga_list[:cols]:
            card = MangaCard(manga, show_labels=show_labels)
            card.clicked.connect(self.card_clicked)
            layout.addWidget(card)

        layout.addStretch()