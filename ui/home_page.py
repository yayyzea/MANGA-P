from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QPointF, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont, QPixmap, QColor, QPalette, QIcon, QPainter, QPainterPath, QBrush, QPen
from pathlib import Path
_ICON_DIR = Path(__file__).parent.parent / "assets"

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_FOOTER, WHITE, BLUE_LIGHT,
    TEXT_DARK, TOPBAR_HEIGHT, CARD_W, CARD_H, CARD_RADIUS
)
from .widgets import MangaCard, ImageLoader, _CARD_MIN_W, _CARD_MAX_W, _ASPECT, _PAD
from .search_page import FilterPanel, SearchLoader


def _force_bg(widget, hex_color, radius=0):
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    r = f"border-radius: {radius}px;" if radius else ""
    widget.setStyleSheet(f"background: {hex_color}; {r}")


class WalkingCat(QWidget):
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
        line_col = QColor("#006ec4")
        nose_col = QColor("#FF8A65")

        pen = QPen(line_col, 2.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(QBrush(body_col))

        body = QPainterPath()
        body.addRoundedRect(4, 12, 22, 14, 6, 6)
        p.drawPath(body)

        head = QPainterPath()
        head.addEllipse(QPointF(15, 10), 9, 9)
        p.drawPath(head)

        for ex, ey in [(9, 4), (19, 4)]:
            p.drawLine(ex - 2, ey + 3, ex - 3, ey - 1)
            p.drawLine(ex - 2, ey + 3, ex + 1, ey)

        p.setBrush(QBrush(line_col))
        p.setPen(Qt.PenStyle.NoPen)
        if f == 2:
            p.setPen(QPen(line_col, 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(11, 10, 13, 10)
            p.drawLine(17, 10, 19, 10)
        else:
            p.drawEllipse(QPointF(12, 10), 1.5, 1.5)
            p.drawEllipse(QPointF(18, 10), 1.5, 1.5)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(nose_col))
        nose = QPainterPath()
        nose.moveTo(15, 13)
        nose.lineTo(13.5, 14.5)
        nose.lineTo(16.5, 14.5)
        nose.closeSubpath()
        p.drawPath(nose)

        p.setPen(QPen(line_col, 1))
        p.drawLine(6, 13, 12, 14)
        p.drawLine(6, 15, 12, 15)
        p.drawLine(18, 14, 24, 13)
        p.drawLine(18, 15, 24, 15)

        p.setPen(QPen(line_col, 2.2))
        p.setBrush(QBrush(body_col))
        leg_x_offsets = [0, 3, 0, -3]
        for i, (lx, ly) in enumerate([(7,26),(12,26),(17,26),(22,26)]):
            ox = leg_x_offsets[i] * (f % 2)
            leg = QPainterPath()
            leg.moveTo(lx, ly)
            leg.quadTo(lx, ly + 3, lx + ox, ly + 8)
            p.drawPath(leg)

        wag = [0, 5, 0, -5][self._frame]
        tail = QPainterPath()
        tail.moveTo(5, 18)
        tail.cubicTo(0, 14, -5 + wag, 8, -3 + wag, 4)
        p.setPen(QPen(line_col, 2.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(tail)
        p.end()


class TopMangaLoader(QThread):
    finished = pyqtSignal(list, dict)

    def run(self):
        try:
            from services.manga_service import MangaService
            from database import get_session
            from models.manga import Manga

            # get_top_manga sekarang HANYA baca DB — tidak pernah hit API
            manga_list = MangaService().get_top_manga(limit=105)

            # Hitung genre_counts dari SEMUA manga di database tanpa filter apapun
            genre_counts = {}
            session = get_session()
            try:
                all_manga = session.query(Manga).all()
                for manga in all_manga:
                    if manga.genres:
                        for g in manga.genres.split(","):
                            g = g.strip()
                            if g:
                                genre_counts[g] = genre_counts.get(g, 0) + 1
            finally:
                session.close()

            genre_counts = dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True))
            top_genre = list(genre_counts.keys())[0] if genre_counts else None

            self.finished.emit(manga_list, {"top_genre": top_genre, "genre_counts": genre_counts})
        except Exception as e:
            print(f"[HomePage] Load error: {e}")
            self.finished.emit([], {})


class ApiRefreshLoader(QThread):
    """
    Background thread yang fetch top manga dari Jikan API lalu emit sinyal
    supaya HomePage bisa reload kartu tanpa freeze UI.
    Hanya dijalankan SETELAH UI sudah tampil.
    """
    refresh_done = pyqtSignal()

    def run(self):
        try:
            from services.manga_service import MangaService
            MangaService().refresh_top_manga_from_api(limit=105)
            self.refresh_done.emit()
        except Exception as e:
            print(f"[ApiRefreshLoader] Error: {e}")


class HistoryPanel(QWidget):
    manga_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HistoryPanel")
        self.setFixedWidth(220)
        self._loader   = None
        self._manga_id = None
        self._synopsis_text = ""

        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(BLUE_CARD))
        self.setPalette(pal)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"border-radius: {CARD_RADIUS}px;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Shadow
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(12)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self._shadow)

        # Animasi pop-out
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        hdr = QLabel("History")
        hdr.setStyleSheet(
            f"color: #000000; font-size: 16px; font-weight: 700; background: transparent;"
        )
        layout.addWidget(hdr)

        # Synopsis overlay di atas cover
        self._cover_wrapper = QWidget()
        self._cover_wrapper.setFixedSize(190, 260)
        self._cover_wrapper.setStyleSheet("background: transparent;")
        cover_stack = QVBoxLayout(self._cover_wrapper)
        cover_stack.setContentsMargins(0, 0, 0, 0)
        cover_stack.setSpacing(0)

        self.cover_lbl = QLabel()
        self.cover_lbl.setFixedSize(190, 260)
        self.cover_lbl.setStyleSheet(
            "background: rgba(255,255,255,0.15); border-radius: 8px;"
        )
        self.cover_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_lbl.setParent(self._cover_wrapper)
        self.cover_lbl.move(0, 0)

        self._synopsis_overlay = QLabel("")
        self._synopsis_overlay.setParent(self)
        self._synopsis_overlay.setWordWrap(True)
        self._synopsis_overlay.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self._synopsis_overlay.setStyleSheet("""
            background: rgba(0, 0, 0, 0.82);
            color: rgba(255,255,255,0.95);
            font-size: 13px;
            border-radius: 12px;
            padding: 16px;
        """)
        self._synopsis_overlay.setVisible(False)

        layout.addWidget(self._cover_wrapper, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Placeholder kosong — tampil kalau user belum pernah klik manga
        self.empty_lbl = QLabel("Click a manga\nto see its\ndetails here")
        self.empty_lbl.setFixedSize(190, 260)
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setWordWrap(True)
        self.empty_lbl.setStyleSheet(
            "color: rgba(0,0,0,0.40); font-size: 12px; background: transparent;"
        )
        layout.addStretch()
        layout.addWidget(self.empty_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

        self.title_lbl = QLabel("")
        self.title_lbl.setStyleSheet(
            f"color: #000000; font-size: 14px; font-weight: 700; background: transparent;"
        )
        self.title_lbl.setWordWrap(True)
        layout.addWidget(self.title_lbl)

        self.desc_lbl = QLabel("")
        self.desc_lbl.setStyleSheet(
            f"color: rgba(0,0,0,0.70); font-size: 11px; background: transparent;"
        )
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setMaximumHeight(120)
        layout.addWidget(self.desc_lbl)

        layout.addStretch()

        # Awal: tampilkan state kosong
        self.cover_lbl.setVisible(False)
        self.empty_lbl.setVisible(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._synopsis_overlay.setGeometry(0, 0, self.width(), self.height())

    def load_manga(self, manga):
        """Update panel saat user klik kartu manga (in-memory, tidak simpan ke DB)."""
        if not manga:
            self._manga_id = None
            self.empty_lbl.setVisible(True)
            self.cover_lbl.setVisible(False)
            self.title_lbl.setText("")
            self.desc_lbl.setText("")
            self._synopsis_text = ""
            self._synopsis_overlay.setText("")
            return
        self._manga_id = manga.id
        self.empty_lbl.setVisible(False)
        self.cover_lbl.setVisible(True)
        self.title_lbl.setText(manga.title or "")
        synopsis = manga.synopsis or ""
        self._synopsis_text = synopsis
        self.desc_lbl.setText(synopsis[:280] + ("…" if len(synopsis) > 280 else ""))
        self._synopsis_overlay.setText(synopsis)
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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._manga_id:
            self.manga_clicked.emit(self._manga_id)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self._shadow.setBlurRadius(28)
        self._shadow.setOffset(0, 8)
        self._shadow.setColor(QColor(0, 0, 0, 100))
        self._anim.stop()
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(self.pos() + QPoint(0, -6))
        self._anim.start()
        if self._manga_id:
            self._synopsis_overlay.setGeometry(0, 0, self.width(), self.height())
            self._synopsis_overlay.raise_()
            self._synopsis_overlay.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._shadow.setBlurRadius(12)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 60))
        self._anim.stop()
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(self.pos() + QPoint(0, 6))
        self._anim.start()
        self._synopsis_overlay.setVisible(False)
        super().leaveEvent(event)


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

        # Shadow + animasi seperti MangaCard
        self._search_shadow = QGraphicsDropShadowEffect(input_wrapper)
        self._search_shadow.setBlurRadius(12)
        self._search_shadow.setOffset(0, 4)
        self._search_shadow.setColor(QColor(0, 0, 0, 60))
        input_wrapper.setGraphicsEffect(self._search_shadow)

        self._search_anim = QPropertyAnimation(input_wrapper, b"pos")
        self._search_anim.setDuration(150)
        self._search_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._input_wrapper = input_wrapper
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
        self.input.returnPressed.connect(self._on_search)
        wrapper_layout.addWidget(self.input)
        layout.addWidget(input_wrapper)

        self.filter_btn = QPushButton()
        self.filter_btn.setObjectName("FilterBtn")
        self.filter_btn.setFixedSize(44, 44)
        _fx = QPixmap(str(_ICON_DIR / "filter.png"))
        if not _fx.isNull():
            self.filter_btn.setIcon(QIcon(_fx))
            self.filter_btn.setIconSize(self.filter_btn.size() * 0.55)
        else:
            self.filter_btn.setText("⚙")
        self.filter_btn.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE}; border: none;
                border-radius: 22px; font-size: 16px; color: {BLUE_PRIMARY};
            }}
        """)

        self._filter_shadow = QGraphicsDropShadowEffect(self.filter_btn)
        self._filter_shadow.setBlurRadius(12)
        self._filter_shadow.setOffset(0, 4)
        self._filter_shadow.setColor(QColor(0, 0, 0, 60))
        self.filter_btn.setGraphicsEffect(self._filter_shadow)

        self._filter_anim = QPropertyAnimation(self.filter_btn, b"pos")
        self._filter_anim.setDuration(150)
        self._filter_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.filter_btn.clicked.connect(self.filter_triggered)
        self.filter_btn.installEventFilter(self)
        layout.addWidget(self.filter_btn)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj == self.filter_btn:
            if event.type() == QEvent.Type.Enter:
                self._on_filter_btn_enter()
            elif event.type() == QEvent.Type.Leave:
                self._on_filter_btn_leave()
        return super().eventFilter(obj, event)

    def _on_search(self):
        self.search_triggered.emit(self.input.text().strip())

    def set_text(self, text: str):
        self.input.setText(text)

    def enterEvent(self, event):
        self._search_shadow.setBlurRadius(28)
        self._search_shadow.setOffset(0, 8)
        self._search_shadow.setColor(QColor(0, 0, 0, 100))
        self._search_anim.stop()
        self._search_anim.setStartValue(self._input_wrapper.pos())
        self._search_anim.setEndValue(self._input_wrapper.pos() + QPoint(0, -4))
        self._search_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._search_shadow.setBlurRadius(12)
        self._search_shadow.setOffset(0, 4)
        self._search_shadow.setColor(QColor(0, 0, 0, 60))
        self._search_anim.stop()
        self._search_anim.setStartValue(self._input_wrapper.pos())
        self._search_anim.setEndValue(self._input_wrapper.pos() + QPoint(0, 4))
        self._search_anim.start()
        super().leaveEvent(event)

    def _on_filter_btn_enter(self):
        self._filter_shadow.setBlurRadius(28)
        self._filter_shadow.setOffset(0, 8)
        self._filter_shadow.setColor(QColor(0, 0, 0, 100))
        self._filter_anim.stop()
        self._filter_anim.setStartValue(self.filter_btn.pos())
        self._filter_anim.setEndValue(self.filter_btn.pos() + QPoint(0, -4))
        self._filter_anim.start()

    def _on_filter_btn_leave(self):
        self._filter_shadow.setBlurRadius(12)
        self._filter_shadow.setOffset(0, 4)
        self._filter_shadow.setColor(QColor(0, 0, 0, 60))
        self._filter_anim.stop()
        self._filter_anim.setStartValue(self.filter_btn.pos())
        self._filter_anim.setEndValue(self.filter_btn.pos() + QPoint(0, 4))
        self._filter_anim.start()


class MostGenreCard(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        _force_bg(self, BLUE_CARD, radius=CARD_RADIUS)
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Drop shadow
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(12)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self._shadow)

        # Animasi pop-out
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(16)
        
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(80, 80)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _cat_px = QPixmap(str(_ICON_DIR / "kucing_duduk.png"))
        if not _cat_px.isNull():
            icon_lbl.setPixmap(
                _cat_px.scaled(80, 80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
            )
        else:
            icon_lbl.setText("🐱")
            icon_lbl.setStyleSheet("font-size: 48px; background: transparent;")
        icon_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.setContentsMargins(0, 0, 0, 0)
        
        self._label = QLabel("MOST GENRE")
        self._label.setFixedHeight(18)
        self._label.setStyleSheet(
            "color: rgba(0,0,0,0.50); font-size: 13px; font-weight: 700; letter-spacing: 1px; background: transparent;"
        )
        text_col.addWidget(self._label)
        
        self._value = QLabel("—")
        self._value.setFixedHeight(32)
        self._value.setStyleSheet(
            "color: #111111; font-size: 26px; font-weight: 700; background: transparent;"
        )
        text_col.addWidget(self._value)
        
        layout.addLayout(text_col)
        layout.addStretch()
        
        arrow = QLabel("→")
        arrow.setStyleSheet(
            "color: rgba(0,0,0,0.40); font-size: 18px; font-weight: 700; background: transparent;"
        )
        layout.addWidget(arrow)

    def set_genre(self, genre: str):
        self._value.setText(genre if genre else "—")

    def enterEvent(self, event):
        self._shadow.setBlurRadius(28)
        self._shadow.setOffset(0, 8)
        self._shadow.setColor(QColor(0, 0, 0, 100))
        self._anim.stop()
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(self.pos() + QPoint(0, -6))
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._shadow.setBlurRadius(12)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 60))
        self._anim.stop()
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(self.pos() + QPoint(0, 6))
        self._anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class _GenreOnlyLoader(QThread):
    """Lightweight loader: hanya hitung genre_counts dari seluruh DB, tanpa fetch top manga."""
    finished = pyqtSignal(dict)

    def run(self):
        try:
            from database import get_session
            from models.manga import Manga

            genre_counts = {}
            session = get_session()
            try:
                for manga in session.query(Manga).all():
                    if manga.genres:
                        for g in manga.genres.split(","):
                            g = g.strip()
                            if g:
                                genre_counts[g] = genre_counts.get(g, 0) + 1
            finally:
                session.close()

            genre_counts = dict(
                sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
            )
            self.finished.emit(genre_counts)
        except Exception as e:
            print(f"[_GenreOnlyLoader] Error: {e}")
            self.finished.emit({})


class HomePage(QWidget):
    GENRE_POLL_MS = 30_000  # refresh genre counts tiap 30 detik

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._manga_list = []
        self._genre_counts = {}
        self._top_genre = None
        self._current_limit = 50
        self._filter_mode   = False
        self._filter_page   = 1
        self._filter_genres = []
        self._filter_status = None
        self._filter_year   = None
        self._is_loading    = False
        self._no_more       = False
        self._card_count    = 0
        self._genre_refresh_loader = None
        self._build()
        self._start_loading()

        # Polling otomatis: refresh distribusi genre dari DB setiap 30 detik
        self._genre_poll_timer = QTimer(self)
        self._genre_poll_timer.timeout.connect(self.refresh_genre_counts)
        self._genre_poll_timer.start(self.GENRE_POLL_MS)

        # Update instan setiap kali MangaService commit data baru ke DB
        from signals import app_signals
        app_signals.db_updated.connect(self.refresh_genre_counts)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.search_bar = SearchBar()
        self.search_bar.search_triggered.connect(self._on_search)
        self.search_bar.filter_triggered.connect(self._on_filter)
        root.addWidget(self.search_bar)

        outer_row = QWidget()
        outer_row_layout = QHBoxLayout(outer_row)
        outer_row_layout.setContentsMargins(24, 16, 24, 20)
        outer_row_layout.setSpacing(24)
        root.addWidget(outer_row, stretch=1)

        left_wrapper = QWidget()
        left_wrapper.setStyleSheet("background: transparent;")
        left_wrapper_layout = QVBoxLayout(left_wrapper)
        left_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        left_wrapper_layout.setSpacing(12)
        outer_row_layout.addWidget(left_wrapper, stretch=1)

        self._most_genre_card = MostGenreCard()
        self._most_genre_card.clicked.connect(self._on_most_genre_clicked)
        left_wrapper_layout.addWidget(self._most_genre_card)

        lbl = QLabel("Top Manga")
        lbl.setStyleSheet(
            f"color: {BLUE_PRIMARY}; font-size: 16px; font-weight: 700; background: transparent;"
        )
        left_wrapper_layout.addWidget(lbl)

        btn_container = QWidget()
        btn_container.setStyleSheet("background: transparent;")
        self._top_btn_row = QHBoxLayout(btn_container)
        self._top_btn_row.setSpacing(10)
        self._top_btn_row.setContentsMargins(0, 0, 0, 4)
        self._top_buttons = {}
        for n in [10, 20, 50, 100]:
            btn = QPushButton(f"Top {n}")
            btn.setFixedHeight(32)
            btn.setFixedWidth(75)
            btn.setCheckable(True)
            btn.setChecked(n == 50)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {BLUE_PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{ background: #1565C0; }}
                QPushButton:checked {{
                    background: white;
                    color: {BLUE_PRIMARY};
                    border: 2px solid {BLUE_PRIMARY};
                }}
            """)
            btn.clicked.connect(lambda _, lim=n: self._set_limit(lim))
            self._top_buttons[n] = btn
            self._top_btn_row.addWidget(btn)
        self._top_btn_row.addStretch()
        left_wrapper_layout.addWidget(btn_container)

        self.content_scroll = QScrollArea()
        content_scroll = self.content_scroll
        content_scroll.setWidgetResizable(True)
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_scroll.setWidget(content_widget)
        left_wrapper_layout.addWidget(content_scroll, stretch=1)

        left = QVBoxLayout(content_widget)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(12)

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")

        self.manga_grid = QGridLayout(self.grid_container)
        self.manga_grid.setSpacing(6)
        self.manga_grid.setContentsMargins(0, 0, 0, 0)

        left.addWidget(self.grid_container)

        self._home_loading_lbl = QLabel("Loading…")
        self._home_loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._home_loading_lbl.setStyleSheet(
            f"color: #111111; font-size: 13px; background: transparent; padding: 12px;"
        )
        self._home_loading_lbl.setVisible(False)
        left.addWidget(self._home_loading_lbl)

        left.addStretch()

        self.content_scroll.verticalScrollBar().valueChanged.connect(self._on_home_scroll)

        self.filter_panel = FilterPanel()
        self.filter_panel.apply_clicked.connect(self._on_filter_apply)
        self.filter_panel.setVisible(False)
        outer_row_layout.addWidget(self.filter_panel)

        self.history = HistoryPanel()
        self.history.manga_clicked.connect(self.main_window.go_detail)
        outer_row_layout.addWidget(self.history, alignment=Qt.AlignmentFlag.AlignTop)

    def _start_loading(self):
        self._show_placeholders()
        self._loader = TopMangaLoader()
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    def _start_api_refresh(self):
        """Fetch data terbaru dari Jikan API di background setelah UI sudah tampil."""
        self._api_refresh_loader = ApiRefreshLoader()
        self._api_refresh_loader.refresh_done.connect(self._on_api_refresh_done)
        self._api_refresh_loader.start()

    @pyqtSlot()
    def _on_api_refresh_done(self):
        """Setelah API refresh selesai, reload kartu dari DB yang sudah terupdate."""
        self._start_loading()

    def _show_placeholders(self):
        self._clear_grid()
        # Taruh di posisi sementara, relayout akan fix setelah ukuran diketahui
        for i in range(min(self._current_limit, 6)):
            ph = QWidget()
            ph.setFixedSize(CARD_W + 16, CARD_H)
            ph.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            ph.setStyleSheet(f"background: {BLUE_CARD}; border-radius: {CARD_RADIUS}px;")
            self.manga_grid.addWidget(ph, 0, i)

    @pyqtSlot(list, dict)
    def _on_loaded(self, manga_list, stats):
        self._manga_list = manga_list
        self._genre_counts = stats.get("genre_counts", {})
        self._top_genre = stats.get("top_genre")

        if self._top_genre:
            self._most_genre_card.set_genre(self._top_genre)

        self._display_cards()

        # Kalau DB kosong / sedikit, kick off API refresh di background
        # setelah UI sudah tampil — tidak memblokir apapun
        if len(manga_list) < 10 and not getattr(self, '_api_refreshed', False):
            self._api_refreshed = True
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, self._start_api_refresh)

    def _on_most_genre_clicked(self):
        if hasattr(self.main_window, 'go_genre_list'):
            self.main_window.go_genre_list(self._genre_counts, self._top_genre)

    def _set_limit(self, limit: int):
        self._current_limit = limit
        self._filter_mode = False
        for btn in self._top_buttons.values():
            btn.setVisible(True)
        for n, btn in self._top_buttons.items():
            btn.setChecked(n == limit)
        self._display_cards()

    def _get_cols(self):
        vw = self.content_scroll.viewport().width() - 4
        if vw < 50:
            vw = self.width() - 320  # sidebar 80 + history 220 + margins
        if vw < 50:
            vw = 700
        spacing = self.manga_grid.spacing()
        for cols in [6, 5, 4, 3, 2, 1]:
            if vw >= cols * 110 + spacing * (cols - 1):
                return cols, vw
        return 1, vw

    def _display_cards(self):
        self._clear_grid()
        self._cards = []
        to_show = self._manga_list[:self._current_limit]
        cols, container_width = self._get_cols()
        spacing = self.manga_grid.spacing()
        card_w = min(_CARD_MAX_W, max(_CARD_MIN_W, (container_width - spacing * (cols - 1)) // cols))
        cover_w = card_w - _PAD * 2

        for i, manga in enumerate(to_show):
            card = MangaCard(manga, show_labels=True)
            card.clicked.connect(self.main_window.go_detail)
            card.clicked.connect(lambda mid, m=manga: self.history.load_manga(m))
            card.setFixedWidth(card_w)
            if hasattr(card, "lbl_title"):
                card.lbl_title.setMaximumWidth(cover_w)
            if hasattr(card, "lbl_genre"):
                card.lbl_genre.setMaximumWidth(cover_w)
            self._cards.append(card)
            self.manga_grid.addWidget(card, i // cols, i % cols)

        # Relayout ulang setelah render untuk koreksi ukuran
        QTimer.singleShot(150, self._relayout)

    def _relayout(self):
        widgets = []
        while self.manga_grid.count():
            item = self.manga_grid.takeAt(0)
            if item.widget():
                widgets.append(item.widget())
        if not widgets:
            return

        cols, container_width = self._get_cols()
        spacing = self.manga_grid.spacing()
        card_w = min(_CARD_MAX_W, max(_CARD_MIN_W, (container_width - spacing * (cols - 1)) // cols))
        cover_w = card_w - _PAD * 2

        for i, widget in enumerate(widgets):
            widget.setFixedWidth(card_w)
            if hasattr(widget, "lbl_title"):
                widget.lbl_title.setMaximumWidth(cover_w)
            if hasattr(widget, "lbl_genre"):
                widget.lbl_genre.setMaximumWidth(cover_w)
            self.manga_grid.addWidget(widget, i // cols, i % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(50, self._relayout)

    def _clear_grid(self):
        self._cards = []
        while self.manga_grid.count():
            item = self.manga_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_filter_apply(self, genres, status, year):
        # Kalau tidak ada filter yang dipilih, balik ke tampilan normal
        if not genres and not status and not year:
            self._filter_mode = False
            for btn in self._top_buttons.values():
                btn.setVisible(True)
            self._display_cards()
            return

        self._filter_mode   = True
        self._filter_page   = 1
        self._filter_genres = genres
        self._filter_status = status
        self._filter_year   = year
        self._no_more       = False
        self._card_count    = 0
        self._clear_grid()
        for btn in self._top_buttons.values():
            btn.setVisible(False)
        self._start_filter_loader(page=1)

    def _on_home_scroll(self, value):
        if not self._filter_mode:
            return
        sb = self.content_scroll.verticalScrollBar()
        if sb.maximum() > 0 and value >= sb.maximum() - 200:
            if not self._is_loading and not self._no_more:
                self._filter_page += 1
                self._start_filter_loader(self._filter_page)

    def _start_filter_loader(self, page: int):
        if self._is_loading:
            return
        self._is_loading = True
        self._home_loading_lbl.setVisible(True)
        loader = SearchLoader(
            query="",
            genres=self._filter_genres,
            status=self._filter_status,
            year=self._filter_year,
            page=page,
        )
        loader.finished.connect(lambda results, p=page: self._on_filter_results(results, p))
        loader.start()
        self._loader = loader

    def _on_filter_results(self, manga_list, page):
        self._is_loading = False
        self._home_loading_lbl.setVisible(False)

        if page == 1 and not manga_list:
            return

        container_width = self.content_scroll.viewport().width() - 4
        if container_width < 50:
            container_width = self.width() - 80 - 220 - 72
        spacing = self.manga_grid.spacing()
        for cols in [5, 4, 3, 2, 1]:
            if container_width >= cols * 130 + spacing * (cols - 1):
                break

        for manga in manga_list:
            row = self._card_count // cols
            col = self._card_count % cols
            card = MangaCard(manga, show_labels=True)
            card.clicked.connect(self.main_window.go_detail)
            card.clicked.connect(lambda mid, m=manga: self.history.load_manga(m))
            self.manga_grid.addWidget(card, row, col)
            self._card_count += 1

        if len(manga_list) < SearchLoader.PAGE_SIZE:
            self._no_more = True

        # Scraping mungkin menambah manga baru ke DB → refresh distribusi genre
        self.refresh_genre_counts()

    def _on_search(self, query):
        if query:
            self.main_window.go_search(query)

    def _on_filter(self):
        is_open = self.filter_panel.isVisible()
        self.filter_panel.setVisible(not is_open)
        self.history.setVisible(is_open)

    def refresh(self):
        self._start_loading()

    def refresh_genre_counts(self):
        """Refresh genre distribution dari DB tanpa reload seluruh manga list.
        Dipanggil setelah scraping selesai agar chart distribusi selalu terupdate."""
        loader = _GenreOnlyLoader()
        loader.finished.connect(self._on_genre_counts_refreshed)
        loader.start()
        self._genre_refresh_loader = loader  # simpan referensi agar tidak di-GC

    @pyqtSlot(dict)
    def _on_genre_counts_refreshed(self, genre_counts: dict):
        if not genre_counts:
            return
        self._genre_counts = genre_counts
        top = list(genre_counts.keys())[0] if genre_counts else None
        if top:
            self._top_genre = top
            self._most_genre_card.set_genre(top)
