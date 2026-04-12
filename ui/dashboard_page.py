import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QPainterPath, QLinearGradient, QColor, QPalette
)

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_DARK, BLUE_LIGHT,
    WHITE, TEXT_DARK, TEXT_MUTED, CARD_RADIUS
)


# ── Loader ────────────────────────────────────────────────────────────────────

class DashboardLoader(QThread):
    # last_review_data = dict {manga_id, title, cover_url, rating, review_text} | None
    finished = pyqtSignal(dict, object, list)

    def run(self):
        try:
            from database import get_session
            from models.review import Review
            from models.manga import Manga
            from sqlalchemy.orm import joinedload
            from services.collection_service import CollectionService
            from services.review_service import ReviewService

            stats = CollectionService().get_stats()
            avg   = ReviewService().get_average_rating()
            stats["avg_rating"] = avg

            session = get_session()
            try:
                # joinedload manga so we can access title/cover_url safely
                all_reviews = (
                    session.query(Review)
                    .options(joinedload(Review.manga))
                    .order_by(Review.updated_at.desc())
                    .all()
                )

                # Build a plain dict for the last review — avoids DetachedInstanceError
                last_review_data = None
                if all_reviews:
                    r = all_reviews[0]
                    last_review_data = {
                        "manga_id":    r.manga_id,
                        "title":       r.manga.title if r.manga else "—",
                        "cover_url":   r.manga.cover_url if r.manga else "",
                        "rating":      r.rating,
                        "review_text": r.review_text or "",
                    }

                # For bar chart: just ratings list
                ratings = [r.rating for r in all_reviews if r.rating]

            finally:
                session.close()

            self.finished.emit(stats, last_review_data, ratings)
        except Exception as e:
            print(f"[Dashboard] Load error: {e}")
            self.finished.emit({}, None, [])


# ── Helper: force background ──────────────────────────────────────────────────

def _force_bg(widget, hex_color, radius=0):
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    r = f"border-radius: {radius}px;" if radius else ""
    widget.setStyleSheet(f"background: {hex_color}; {r}")


# ── Stat card ─────────────────────────────────────────────────────────────────

class StatCard(QWidget):
    def __init__(self, label, value="—", bg=None, parent=None):
        super().__init__(parent)
        _force_bg(self, bg or BLUE_CARD, radius=CARD_RADIUS)
        self.setMinimumWidth(140)
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        self._val = QLabel(value)
        self._val.setStyleSheet(f"color:{WHITE};font-size:30px;font-weight:800;background:transparent;")
        self._key = QLabel(label)
        self._key.setStyleSheet(f"color:rgba(255,255,255,0.85);font-size:12px;background:transparent;")
        layout.addWidget(self._val)
        layout.addWidget(self._key)

    def set_value(self, v):
        self._val.setText(str(v))


class WideCard(QWidget):
    def __init__(self, label, value="—", parent=None):
        super().__init__(parent)
        _force_bg(self, BLUE_CARD, radius=CARD_RADIUS)
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)
        key_lbl = QLabel(label.upper())
        key_lbl.setStyleSheet(f"color:rgba(255,255,255,0.80);font-size:10px;font-weight:700;letter-spacing:1px;background:transparent;")
        self._val = QLabel(value)
        self._val.setStyleSheet(f"color:{WHITE};font-size:18px;font-weight:700;background:transparent;")
        self._val.setWordWrap(True)
        layout.addWidget(key_lbl)
        layout.addWidget(self._val)
        layout.addStretch()

    def set_value(self, v):
        self._val.setText(str(v))


# ── Pie chart: collection status ──────────────────────────────────────────────

STATUS_COLORS = {
    "Plan to Read": "#29B6F6",
    "Reading":      "#1E90FF",
    "Completed":    "#43A047",
    "Dropped":      "#E53935",
}


class PieChartWidget(QWidget):
    """Pie chart showing collection status breakdown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}   # {label: count}
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, counts: dict):
        self._data = {k: v for k, v in counts.items() if v > 0}
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        total = sum(self._data.values())

        if total == 0:
            painter.setPen(QColor(TEXT_MUTED))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data yet")
            return

        # Pie dimensions
        pie_size = min(w // 2, h - 40)
        pie_x    = (w // 2 - pie_size) // 2
        pie_y    = (h - pie_size) // 2
        pie_rect = QRectF(pie_x, pie_y, pie_size, pie_size)

        start_angle = 90 * 16  # start from top
        items       = list(self._data.items())

        for label, count in items:
            span   = int(round(count / total * 360 * 16))
            color  = QColor(STATUS_COLORS.get(label, BLUE_CARD))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(WHITE), 2))
            painter.drawPie(pie_rect, start_angle, span)
            start_angle += span

        # Legend (right half)
        legend_x = w // 2 + 20
        legend_y = h // 2 - len(items) * 18
        font = QFont("Segoe UI", 10)
        painter.setFont(font)

        for i, (label, count) in enumerate(items):
            y   = legend_y + i * 36
            pct = count / total * 100

            # Color swatch
            painter.setBrush(QBrush(QColor(STATUS_COLORS.get(label, BLUE_CARD))))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(legend_x, y, 14, 14, 3, 3)

            # Label + count
            painter.setPen(QColor(TEXT_DARK))
            painter.drawText(legend_x + 20, y, 200, 14,
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             f"{label}")
            painter.setPen(QColor(TEXT_MUTED))
            painter.drawText(legend_x + 20, y + 16, 200, 14,
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             f"{count} manga  ({pct:.0f}%)")


# ── Bar chart: rating distribution ───────────────────────────────────────────

class RatingBarChart(QWidget):
    """Horizontal bar chart showing how many manga per rating score."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ratings = {}   # {1..10: count}
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, ratings: list):
        """ratings: list of int (1-10)"""
        self._ratings = {i: 0 for i in range(1, 11)}
        for r in ratings:
            if r and 1 <= r <= 10:
                self._ratings[r] += 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h       = self.width(), self.height()
        total      = sum(self._ratings.values())
        max_count  = max(self._ratings.values()) if self._ratings else 1
        if max_count == 0:
            max_count = 1

        if total == 0:
            painter.setPen(QColor(TEXT_MUTED))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No reviews yet")
            return

        padding_l  = 40   # space for score labels
        padding_r  = 60   # space for count labels
        padding_v  = 10
        bar_area_w = w - padding_l - padding_r
        n_bars     = 10
        bar_h      = (h - padding_v * 2) / n_bars - 4

        font = QFont("Segoe UI", 9)
        painter.setFont(font)

        for i, score in enumerate(range(1, 11)):
            count = self._ratings.get(score, 0)
            bar_w = int(bar_area_w * count / max_count) if count > 0 else 2
            y     = padding_v + i * ((h - padding_v * 2) / n_bars)

            # Score label
            painter.setPen(QColor(TEXT_DARK))
            painter.drawText(0, int(y), padding_l - 6, int(bar_h),
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             str(score))

            # Bar fill — gradient blue
            bar_rect = QRectF(padding_l, y + 2, max(bar_w, 2), bar_h - 2)
            grad = QLinearGradient(bar_rect.topLeft(), bar_rect.topRight())
            grad.setColorAt(0, QColor(BLUE_PRIMARY))
            grad.setColorAt(1, QColor(BLUE_LIGHT))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.addRoundedRect(bar_rect, 4, 4)
            painter.drawPath(path)

            # Count label
            if count > 0:
                painter.setPen(QColor(TEXT_MUTED))
                painter.drawText(int(padding_l + bar_w + 6), int(y), padding_r - 8, int(bar_h),
                                 Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                 str(count))


# ── Last review card ──────────────────────────────────────────────────────────

class LastReviewCard(QWidget):
    # Emits manga_id when clicked
    clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        _force_bg(self, BLUE_CARD, radius=CARD_RADIUS)
        self._manga_id = None
        self._img_loader = None

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 14, 18, 14)
        outer.setSpacing(14)

        # Cover image (left)
        self._cover = QLabel()
        self._cover.setFixedSize(60, 85)
        self._cover.setStyleSheet("background: rgba(255,255,255,0.18); border-radius: 6px;")
        self._cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover.setScaledContents(True)
        outer.addWidget(self._cover)

        # Right column
        right = QVBoxLayout()
        right.setSpacing(5)

        # Title + hint
        top_row = QHBoxLayout()
        self._title_lbl = QLabel("No reviews yet.")
        self._title_lbl.setStyleSheet(
            f"color:{WHITE};font-size:14px;font-weight:700;background:transparent;"
        )
        self._title_lbl.setWordWrap(True)
        self._hint = QLabel("→ Lihat detail")
        self._hint.setStyleSheet(
            f"color:rgba(255,255,255,0.55);font-size:11px;background:transparent;"
        )
        self._hint.setVisible(False)
        top_row.addWidget(self._title_lbl)
        top_row.addStretch()
        top_row.addWidget(self._hint)
        right.addLayout(top_row)

        self._rating = QLabel("")
        self._rating.setStyleSheet(
            f"color:rgba(255,255,255,0.80);font-size:13px;background:transparent;"
        )
        right.addWidget(self._rating)

        self._text = QLabel("")
        self._text.setStyleSheet(
            f"color:rgba(255,255,255,0.85);font-size:12px;background:transparent;"
        )
        self._text.setWordWrap(True)
        right.addWidget(self._text)
        right.addStretch()

        outer.addLayout(right, stretch=1)

    def load(self, review_data: dict):
        """review_data: plain dict {manga_id, title, cover_url, rating, review_text}"""
        if not review_data:
            self._title_lbl.setText("No reviews yet.")
            self._rating.setText("")
            self._text.setText("")
            self._manga_id = None
            self._cover.clear()
            self._hint.setVisible(False)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        self._manga_id = review_data.get("manga_id")
        self._title_lbl.setText(review_data.get("title") or "—")
        self._rating.setText(f"★  {review_data.get('rating', '?')} / 10")
        self._text.setText(review_data.get("review_text") or "(no review text)")
        self._hint.setVisible(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Load cover image
        cover_url = review_data.get("cover_url", "")
        if cover_url:
            from .widgets import ImageLoader
            self._img_loader = ImageLoader(cover_url)
            self._img_loader.loaded.connect(self._on_cover)
            self._img_loader.start()

    def _on_cover(self, pixmap):
        self._cover.setPixmap(
            pixmap.scaled(60, 85,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._manga_id:
            self.clicked.emit(self._manga_id)
        super().mousePressEvent(event)


# ── Chart card wrapper ────────────────────────────────────────────────────────

def _chart_card(title: str, chart_widget: QWidget) -> QWidget:
    card = QWidget()
    card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    # Single setStyleSheet — no _force_bg conflict — guarantees uniform radius all corners
    card.setStyleSheet(
        f"background: #F8FBFF; border-radius: {CARD_RADIUS}px; "
        f"border: 1.5px solid {BLUE_LIGHT};"
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)

    hdr = QLabel(title)
    hdr.setStyleSheet(
        f"color: {BLUE_PRIMARY}; font-size: 13px; font-weight: 700; background: transparent;"
    )
    layout.addWidget(hdr)
    layout.addWidget(chart_widget)
    return card


# ── Dashboard page ────────────────────────────────────────────────────────────

class DashboardPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._loader = None
        self._build()
        self._start_loading()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Topbar
        topbar = QWidget()
        topbar.setFixedHeight(60)
        _force_bg(topbar, BLUE_PRIMARY)
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(24, 0, 24, 0)
        title = QLabel("Dashboard")
        title.setStyleSheet(f"color:{WHITE};font-size:18px;font-weight:700;background:transparent;")
        tb.addWidget(title)
        tb.addStretch()
        root.addWidget(topbar)

        # Scroll body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 24, 24, 24)
        bl.setSpacing(16)

        # ── Row 1: stat cards ─────────────────────────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        self._total  = StatCard("Total Manga", "—", bg=BLUE_CARD)
        self._rating = StatCard("Avg Rating",  "—", bg=BLUE_CARD)
        self._genre  = WideCard("Top Genre",   "—")
        row1.addWidget(self._total)
        row1.addWidget(self._rating)
        row1.addWidget(self._genre, stretch=2)
        bl.addLayout(row1)

        # ── Row 2: charts side by side ────────────────────────────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        self._pie = PieChartWidget()
        pie_card  = _chart_card("Collection Status", self._pie)
        row2.addWidget(pie_card, stretch=1)

        self._bar = RatingBarChart()
        bar_card  = _chart_card("Rating Distribution (1–10)", self._bar)
        row2.addWidget(bar_card, stretch=1)

        bl.addLayout(row2)

        # ── Row 3: last review ────────────────────────────────────────────────
        bl.addWidget(self._sec("Last Review"))
        self._last_review = LastReviewCard()
        self._last_review.clicked.connect(self.main_window.go_detail)
        bl.addWidget(self._last_review)

        bl.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

    def _sec(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{BLUE_PRIMARY};font-size:15px;font-weight:700;background:transparent;"
        )
        return lbl

    def _start_loading(self):
        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()
        self._loader = DashboardLoader()
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    @pyqtSlot(dict, object, list)
    def _on_loaded(self, stats, last_review, all_reviews):
        self._total.set_value(stats.get("total", 0))
        avg = stats.get("avg_rating")
        self._rating.set_value(f"{avg:.1f}" if avg else "—")
        self._genre.set_value(stats.get("top_genre") or "—")

        # Charts
        self._pie.set_data(stats.get("counts", {}))
        self._bar.set_data(all_reviews)   # all_reviews is now list of int ratings

        self._last_review.load(last_review)

    def refresh(self):
        self._start_loading()
