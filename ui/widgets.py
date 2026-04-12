from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QSizePolicy, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor
import urllib.request

from .theme import CARD_W, CARD_H, CARD_RADIUS, BLUE_CARD

_PAD = 8   # blue padding around the cover image (left/right/top/bottom)


class ImageLoader(QThread):
    loaded = pyqtSignal(QPixmap)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            req = urllib.request.Request(
                self.url, headers={"User-Agent": "MANGA:P/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                self.loaded.emit(pixmap)
        except Exception:
            pass


class MangaCoverLabel(QLabel):
    """Rounded-corner cover image, fills with lighter blue when no image."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(CARD_W, CARD_H)
        self._pixmap = None

    def set_cover(self, pixmap: QPixmap):
        self._pixmap = pixmap.scaled(
            CARD_W, CARD_H,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        inner_r = max(CARD_RADIUS - _PAD, 4)
        path = QPainterPath()
        path.addRoundedRect(0, 0, CARD_W, CARD_H, inner_r, inner_r)
        painter.setClipPath(path)

        if self._pixmap:
            pw, ph = self._pixmap.width(), self._pixmap.height()
            x = (pw - CARD_W) // 2
            y = (ph - CARD_H) // 2
            painter.drawPixmap(0, 0, self._pixmap, x, y, CARD_W, CARD_H)
        else:
            painter.fillPath(path, QColor("#64B5F6"))  # lighter blue placeholder


class MangaCard(QWidget):
    """
    Blue rounded card: _PAD px padding → cover image → title + genre text.
    The _PAD creates visible blue edges around the cover on all sides.
    """
    clicked = pyqtSignal(int)

    def __init__(self, manga, show_labels: bool = True, parent=None):
        super().__init__(parent)
        self.manga       = manga
        self.show_labels = show_labels
        self._loader     = None

        self.setObjectName("MangaCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"background: {BLUE_CARD}; border-radius: {CARD_RADIUS}px;"
        )
        self._build()
        self._load_cover()

    def _build(self):
        layout = QVBoxLayout(self)
        # _PAD on all sides → blue visible around cover image
        layout.setContentsMargins(_PAD, _PAD, _PAD, _PAD)
        layout.setSpacing(6)

        self.cover = MangaCoverLabel()
        layout.addWidget(self.cover, alignment=Qt.AlignmentFlag.AlignHCenter)

        if self.show_labels:
            self.lbl_title = QLabel(self.manga.title or "")
            self.lbl_title.setWordWrap(True)
            self.lbl_title.setFixedWidth(CARD_W)
            self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.lbl_title.setStyleSheet(
                "color: white; font-size: 11px; font-weight: 600; background: transparent;"
            )

            genres    = self.manga.genres or ""
            first_gen = genres.split(",")[0].strip() if genres else ""
            self.lbl_genre = QLabel(first_gen)
            self.lbl_genre.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.lbl_genre.setStyleSheet(
                "color: rgba(255,255,255,0.80); font-size: 10px; background: transparent;"
            )

            layout.addWidget(self.lbl_title)
            layout.addWidget(self.lbl_genre)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        # Card is wider than cover by 2×_PAD so blue shows on left and right
        self.setFixedWidth(CARD_W + _PAD * 2)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _load_cover(self):
        if self.manga.cover_url:
            self._loader = ImageLoader(self.manga.cover_url)
            self._loader.loaded.connect(self._on_image_loaded)
            self._loader.start()

    @pyqtSlot(QPixmap)
    def _on_image_loaded(self, pixmap: QPixmap):
        self.cover.set_cover(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.manga.id)

    def enterEvent(self, event):
        self.cover.update()
        super().enterEvent(event)


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
