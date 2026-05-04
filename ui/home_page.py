from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QPointF
from PyQt6.QtGui import QFont, QPixmap, QColor, QPalette, QIcon, QPainter, QPainterPath, QBrush, QPen
from pathlib import Path
_ICON_DIR = Path(__file__).parent.parent / "assets"

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_FOOTER, WHITE,
    TEXT_DARK, TOPBAR_HEIGHT, CARD_W, CARD_H, CARD_RADIUS
)
from .widgets import MangaCard, ImageLoader


# ── Walking Cat Animation ─────────────────────────────────────────────────────

class WalkingCat(QWidget):
    """Cat that walks back and forth across the footer. Drawn with QPainter."""
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

        # Body
        body = QPainterPath()
        body.addRoundedRect(4, 12, 22, 14, 6, 6)
        p.drawPath(body)

        # Head
        head = QPainterPath()
        head.addEllipse(QPointF(15, 10), 9, 9)
        p.drawPath(head)

        # Ears
        for ex, ey in [(9, 4), (19, 4)]:
            p.drawLine(ex - 2, ey + 3, ex - 3, ey - 1)
            p.drawLine(ex - 2, ey + 3, ex + 1, ey)

        # Eyes
        p.setBrush(QBrush(line_col))
        p.setPen(Qt.PenStyle.NoPen)
        if f == 2:  # blink
            p.setPen(QPen(line_col, 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(11, 10, 13, 10)
            p.drawLine(17, 10, 19, 10)
        else:
            p.drawEllipse(QPointF(12, 10), 1.5, 1.5)
            p.drawEllipse(QPointF(18, 10), 1.5, 1.5)

        # Nose
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(nose_col))
        nose = QPainterPath()
        nose.moveTo(15, 13)
        nose.lineTo(13.5, 14.5)
        nose.lineTo(16.5, 14.5)
        nose.closeSubpath()
        p.drawPath(nose)

        # Whiskers
        p.setPen(QPen(line_col, 1))
        p.drawLine(6, 13, 12, 14)
        p.drawLine(6, 15, 12, 15)
        p.drawLine(18, 14, 24, 13)
        p.drawLine(18, 15, 24, 15)

        # Legs
        p.setPen(QPen(line_col, 2.2))
        p.setBrush(QBrush(body_col))
        leg_x_offsets = [0, 3, 0, -3]
        for i, (lx, ly) in enumerate([(7,26),(12,26),(17,26),(22,26)]):
            ox = leg_x_offsets[i] * (f % 2)
            leg = QPainterPath()
            leg.moveTo(lx, ly)
            leg.quadTo(lx, ly + 3, lx + ox, ly + 8)
            p.drawPath(leg)

        # Tail
        wag = [0, 5, 0, -5][self._frame]
        tail = QPainterPath()
        tail.moveTo(5, 18)
        tail.cubicTo(0, 14, -5 + wag, 8, -3 + wag, 4)
        p.setPen(QPen(line_col, 2.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(tail)
        p.end()



class TopMangaLoader(QThread):
    finished = pyqtSignal(list)

    def run(self):
        try:
            from services.manga_service import MangaService
            self.finished.emit(MangaService().get_top_manga(limit=48))
        except Exception as e:
            print(f"[HomePage] Load error: {e}")
            self.finished.emit([])


# ── History panel (clickable) ─────────────────────────────────────────────────

class HistoryPanel(QWidget):
    # ★ Signal emitted when user clicks the panel
    manga_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HistoryPanel")
        self.setFixedWidth(220)
        self._loader   = None
        self._manga_id = None   # stores current manga id for click navigation

        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(BLUE_CARD))
        self.setPalette(pal)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"border-radius: {CARD_RADIUS}px;")

        # ★ Pointer cursor — signals it's clickable
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

    # ★ Navigate to detail page on click
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._manga_id:
            self.manga_clicked.emit(self._manga_id)
        super().mousePressEvent(event)


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
                background: {WHITE}; border: none;
                border-radius: 20px; padding: 8px 16px;
                font-size: 14px; color: {TEXT_DARK};
            }}
        """)
        self.input.returnPressed.connect(self._on_search)
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
                background: {WHITE}; border: none;
                border-radius: 18px; font-size: 16px; color: {BLUE_PRIMARY};
            }}
            QPushButton:hover {{ background: #E3F2FD; }}
        """)
        filter_btn.clicked.connect(self.filter_triggered)
        layout.addWidget(filter_btn)

    def _on_search(self):
        self.search_triggered.emit(self.input.text().strip())

    def set_text(self, text: str):
        self.input.setText(text)


# ── Home page ─────────────────────────────────────────────────────────────────

class HomePage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._manga_list = []
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

        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content_widget = QWidget()
        content_scroll.setWidget(content_widget)
        root.addWidget(content_scroll, stretch=1)

        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(24)

        left = QVBoxLayout()
        left.setSpacing(12)

        lbl = QLabel("Top Manga")
        lbl.setStyleSheet(
            f"color: {BLUE_PRIMARY}; font-size: 16px; font-weight: 700; background: transparent;"
        )
        left.addWidget(lbl)

        self.row1 = QHBoxLayout()
        self.row1.setSpacing(16)
        left.addLayout(self.row1)

        self.row2 = QHBoxLayout()
        self.row2.setSpacing(16)
        left.addLayout(self.row2)

        left.addStretch()
        content_layout.addLayout(left, stretch=1)

        # ★ Connect history panel click → go_detail
        self.history = HistoryPanel()
        self.history.manga_clicked.connect(self.main_window.go_detail)
        content_layout.addWidget(self.history, alignment=Qt.AlignmentFlag.AlignTop)

        root.addWidget(self._build_footer())

    def _build_footer(self):
        # Outer container: links row + cat row
        outer = QWidget()
        outer.setAutoFillBackground(True)
        pal = outer.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(BLUE_FOOTER))
        outer.setPalette(pal)

        v = QVBoxLayout(outer)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # ── Links row ─────────────────────────────────────────────────────
        link_bar = QWidget()
        link_bar.setFixedHeight(30)
        link_bar.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(link_bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(4)

        for label, cb in [("Home", self.main_window.go_home),
                          ("About", self.main_window.go_about)]:
            btn = QPushButton(label)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none;
                    color: {BLUE_PRIMARY}; font-size: 12px;
                    text-decoration: underline;
                }}
                QPushButton:hover {{ color: #0D47A1; }}
            """)
            btn.clicked.connect(cb)
            layout.addWidget(btn)
            sep = QLabel("|")
            sep.setStyleSheet(f"color: {BLUE_PRIMARY}; background: transparent; font-size: 12px;")
            layout.addWidget(sep)
        layout.addStretch()
        v.addWidget(link_bar)

        # ── Walking cat strip ──────────────────────────────────────────────
        self.walking_cat = WalkingCat()
        self.walking_cat.setStyleSheet("background: transparent;")
        v.addWidget(self.walking_cat)

        return outer

    def _start_loading(self):
        self._show_placeholders()
        self._loader = TopMangaLoader()
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    def _show_placeholders(self):
        for row_layout in (self.row1, self.row2):
            for _ in range(48):
                ph = QWidget()
                ph.setFixedSize(CARD_W + 16, CARD_H)
                ph.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                ph.setStyleSheet(f"background: {BLUE_CARD}; border-radius: {CARD_RADIUS}px;")
                row_layout.addWidget(ph)
            row_layout.addStretch()

    @pyqtSlot(list)
    def _on_loaded(self, manga_list):
        self._manga_list = manga_list
        self._clear_row(self.row1)
        self._clear_row(self.row2)

        for i, manga in enumerate(manga_list[:8]):
            card = MangaCard(manga, show_labels=True)
            card.clicked.connect(self.main_window.go_detail)
            (self.row1 if i < 4 else self.row2).addWidget(card)

        for row in (self.row1, self.row2):
            row.addStretch()

        if manga_list:
            self.history.load_manga(manga_list[0])

    def _clear_row(self, row_layout):
        while row_layout.count():
            item = row_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_search(self, query):
        if query:
            self.main_window.go_search(query)

    def _on_filter(self):
        self.main_window.go_search("")

    def refresh(self):
        self._start_loading()
