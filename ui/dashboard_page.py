import copy
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QRectF, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QPainterPath, QLinearGradient
)

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_DARK, BLUE_LIGHT,
    WHITE, TEXT_DARK, TEXT_MUTED, CARD_RADIUS
)


def _force_bg(widget, hex_color, radius=0):
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    r = f"border-radius: {radius}px;" if radius else ""
    widget.setStyleSheet(f"background: {hex_color}; {r}")


class DashboardLoader(QThread):
    finished = pyqtSignal(dict, object, list)

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    def run(self):
        stats = {
            "total": 0,
            "counts": {},
            "top_genre": None,
            "top_author": None,
            "genre_counts": {},
            "author_counts": {},
            "avg_rating": None
        }
        last_review_data = None
        ratings = []

        try:
            from services.collection_service import CollectionService
            from services.review_service import ReviewService
            from database import get_session
            from models.review import Review

            stats = CollectionService().get_stats(self.user_id)
            avg = ReviewService().get_average_rating(self.user_id)
            stats["avg_rating"] = avg
            last_review_data = ReviewService().get_last_review_data(self.user_id)

            session = get_session()
            try:
                rows = session.query(Review.rating).filter(
                    Review.user_id == self.user_id,
                    Review.rating != None
                ).all()
                ratings = [int(r[0]) for r in rows if r[0] is not None]
            finally:
                session.close()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[Dashboard] Error: {e}")

        self.finished.emit(stats, last_review_data, ratings)


class StatCard(QWidget):
    clicked = pyqtSignal()

    def __init__(self, label, value="—", bg=None, parent=None):
        super().__init__(parent)
        _force_bg(self, bg or BLUE_CARD, radius=CARD_RADIUS)
        self.setMinimumWidth(140)
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(12)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self._shadow)
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        self._val = QLabel(value)
        self._val.setStyleSheet("color:#111111;font-size:30px;font-weight:800;background:transparent;")
        self._key = QLabel(label)
        self._key.setStyleSheet("color:rgba(0,0,0,0.55);font-size:12px;background:transparent;")
        layout.addWidget(self._val)
        layout.addWidget(self._key)

    def set_value(self, v):
        self._val.setText(str(v))

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


class WideCard(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self, label, value="—", parent=None):
        super().__init__(parent)
        _force_bg(self, BLUE_CARD, radius=CARD_RADIUS)
        self._card_value = "—"
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(12)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self._shadow)
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)
        key_lbl = QLabel(label.upper())
        key_lbl.setStyleSheet("color:rgba(0,0,0,0.50);font-size:10px;font-weight:700;letter-spacing:1px;background:transparent;")
        self._val = QLabel(value)
        self._val.setStyleSheet("color:#111111;font-size:18px;font-weight:700;background:transparent;")
        self._val.setWordWrap(True)
        layout.addWidget(key_lbl)
        layout.addWidget(self._val)
        layout.addStretch()

    def set_value(self, v):
        self._card_value = str(v) if v else "—"
        self._val.setText(self._card_value)

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
        if event.button() == Qt.MouseButton.LeftButton and self._card_value != "—":
            self.clicked.emit(self._card_value)
        super().mousePressEvent(event)


STATUS_COLORS = {
    "Plan to Read": "#2cb5d3",
    "Reading":      "#2cb5d3",
    "Completed":    "#9abe7c",
    "Dropped":      "#f96a67",
}


class PieChartWidget(QWidget):
    clicked_status = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self._slices = []
        self._hovered_label = None
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

    def set_data(self, counts: dict):
        self._data = {}
        if counts:
            for k, v in counts.items():
                if v > 0:
                    self._data[str(k)] = int(v)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        total = sum(self._data.values())
        self._slices = []

        if total == 0:
            painter.setPen(QColor(TEXT_MUTED))
            font = QFont("Segoe UI", 11)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data yet")
            return

        pie_size = min(w // 2, h - 40)
        pie_x = (w // 2 - pie_size) // 2
        pie_y = (h - pie_size) // 2
        pie_rect = QRectF(pie_x, pie_y, pie_size, pie_size)

        start_angle = 90 * 16
        items = list(self._data.items())

        for label, count in items:
            span = int(round(count / total * 360 * 16))
            color = QColor(STATUS_COLORS.get(label, BLUE_CARD))
            painter.setBrush(QBrush(color))

            if label == self._hovered_label:
                painter.setPen(QPen(QColor(WHITE), 3))
            else:
                painter.setPen(QPen(QColor(WHITE), 2))

            painter.drawPie(pie_rect, start_angle, span)
            self._slices.append((pie_rect, start_angle, span, label))
            start_angle += span

        legend_x = w // 2 + 20
        legend_y = h // 2 - len(items) * 18
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        for i, (label, count) in enumerate(items):
            y = legend_y + i * 36
            pct = count / total * 100
            painter.setBrush(QBrush(QColor(STATUS_COLORS.get(label, BLUE_CARD))))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(legend_x, y, 14, 14, 3, 3)
            painter.setPen(QColor(TEXT_DARK))
            painter.drawText(legend_x + 20, y, 200, 14,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{label}")
            painter.setPen(QColor(TEXT_MUTED))
            painter.drawText(legend_x + 20, y + 16, 200, 14,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{count} manga  ({pct:.0f}%)")

    def mouseMoveEvent(self, event):
        pos = event.position()
        new_hover = None
        for pie_rect, start_angle, span, label in self._slices:
            center = pie_rect.center()
            dx = pos.x() - center.x()
            dy = pos.y() - center.y()
            dist = (dx * dx + dy * dy) ** 0.5
            radius = pie_rect.width() / 2

            if dist <= radius:
                import math
                angle = math.degrees(math.atan2(-dy, dx))
                if angle < 0:
                    angle += 360
                angle_16 = angle * 16
                sa = start_angle % (360 * 16)
                ea = sa + span

                if ea <= 360 * 16:
                    if sa <= angle_16 < ea:
                        new_hover = label
                        break
                else:
                    if angle_16 >= sa or angle_16 < (ea % (360 * 16)):
                        new_hover = label
                        break

        if new_hover != self._hovered_label:
            self._hovered_label = new_hover
            self.update()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._hovered_label:
            self.clicked_status.emit(self._hovered_label)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if self._data:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._hovered_label = None
        self.update()
        super().leaveEvent(event)


class RatingBarChart(QWidget):
    clicked_rating = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ratings = {}
        self._bar_rects = []
        self._hovered_score = None
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

    def set_data(self, ratings):
        new_ratings = {i: 0 for i in range(1, 11)}
        if ratings:
            for r in ratings:
                try:
                    val = int(r) if isinstance(r, (int, float)) else int(r[0]) if isinstance(r, (list, tuple)) else int(r.rating) if hasattr(r, 'rating') else int(r)
                    if 1 <= val <= 10:
                        new_ratings[val] += 1
                except:
                    pass
        self._ratings = new_ratings
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        total = sum(self._ratings.values())
        max_count = max(self._ratings.values()) if self._ratings else 1
        if max_count == 0:
            max_count = 1

        if total == 0:
            painter.setPen(QColor(TEXT_MUTED))
            font = QFont("Segoe UI", 11)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No reviews yet")
            self._bar_rects = []
            return

        padding_l, padding_r, padding_v = 40, 60, 10
        bar_area_w = w - padding_l - padding_r
        bar_h = (h - padding_v * 2) / 10 - 4
        font = QFont("Segoe UI", 9)
        painter.setFont(font)

        self._bar_rects = []

        for i, score in enumerate(range(1, 11)):
            count = self._ratings.get(score, 0)
            bar_w = int(bar_area_w * count / max_count) if count > 0 else 2
            y = padding_v + i * ((h - padding_v * 2) / 10)

            painter.setPen(QColor(TEXT_DARK))
            painter.drawText(
                0, int(y),
                padding_l - 6, int(bar_h),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(score)
            )

            bar_rect = QRectF(padding_l, y + 2, max(bar_w, 2), bar_h - 2)
            grad = QLinearGradient(bar_rect.topLeft(), bar_rect.topRight())
            grad.setColorAt(0, QColor(BLUE_PRIMARY))
            grad.setColorAt(1, QColor(BLUE_LIGHT))
            painter.setBrush(QBrush(grad))

            if score == self._hovered_score:
                painter.setPen(QPen(QColor(WHITE), 2))
            else:
                painter.setPen(Qt.PenStyle.NoPen)

            path = QPainterPath()
            path.addRoundedRect(bar_rect, 4, 4)
            painter.drawPath(path)

            if count > 0:
                painter.setPen(QColor(TEXT_MUTED))
                painter.drawText(
                    int(padding_l + bar_w + 6), int(y),
                    padding_r - 8, int(bar_h),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    str(count)
                )

            full_rect = QRectF(0, y, w, bar_h)
            self._bar_rects.append((full_rect, score))

    def mouseMoveEvent(self, event):
        pos = event.position()
        new_hover = None
        for rect, score in self._bar_rects:
            if rect.contains(pos) and self._ratings.get(score, 0) > 0:
                new_hover = score
                break

        if new_hover != self._hovered_score:
            self._hovered_score = new_hover
            self.update()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._hovered_score:
            self.clicked_rating.emit(self._hovered_score)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if any(v > 0 for v in self._ratings.values()):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._hovered_score = None
        self.update()
        super().leaveEvent(event)


class LastReviewCard(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("lastReviewCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#lastReviewCard {{
                background: #F8FBFF;
                border-radius: {CARD_RADIUS}px;
                border: 1.5px solid {BLUE_LIGHT};
            }}
        """)
        self._manga_id = None
        self._img_loader = None

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(12)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self._shadow)
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 14, 18, 14)
        outer.setSpacing(14)
        self._cover = QLabel()
        self._cover.setFixedSize(60, 85)
        self._cover.setStyleSheet("background: rgba(0,0,0,0.08); border-radius: 6px;")
        self._cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover.setScaledContents(True)
        outer.addWidget(self._cover)
        right = QVBoxLayout()
        right.setSpacing(5)
        top_row = QHBoxLayout()
        self._title_lbl = QLabel("No reviews yet.")
        self._title_lbl.setStyleSheet(f"color:{BLUE_PRIMARY};font-size:14px;font-weight:700;background:transparent;")
        self._title_lbl.setWordWrap(True)
        self._hint = QLabel("→ Lihat detail")
        self._hint.setStyleSheet("color:rgba(0,0,0,0.45);font-size:11px;background:transparent;")
        self._hint.setVisible(False)
        top_row.addWidget(self._title_lbl)
        top_row.addStretch()
        top_row.addWidget(self._hint)
        right.addLayout(top_row)
        self._rating = QLabel("")
        self._rating.setStyleSheet("color:rgba(0,0,0,0.65);font-size:13px;background:transparent;")
        right.addWidget(self._rating)
        self._text = QLabel("")
        self._text.setStyleSheet("color:rgba(0,0,0,0.70);font-size:12px;background:transparent;")
        self._text.setWordWrap(True)
        right.addWidget(self._text)
        self._tags_row = QHBoxLayout()
        self._tags_row.setSpacing(5)
        self._tags_row.setContentsMargins(0, 2, 0, 0)
        self._tags_placeholder = QWidget()
        self._tags_placeholder.setLayout(self._tags_row)
        self._tags_placeholder.setStyleSheet("background: transparent;")
        right.addWidget(self._tags_placeholder)
        right.addStretch()
        outer.addLayout(right, stretch=1)

    def load(self, review_data: dict):
        if not review_data:
            self._title_lbl.setText("No reviews yet.")
            self._rating.setText("")
            self._text.setText("")
            self._manga_id = None
            self._cover.clear()
            self._hint.setVisible(False)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self._clear_tags()
            return
        self._manga_id = int(review_data.get("manga_id", 0))
        self._title_lbl.setText(str(review_data.get("title", "—")))
        self._rating.setText(f"★  {review_data.get('rating', '?')} / 10")
        self._text.setText(str(review_data.get("review_text", "(no review text)")))
        self._hint.setVisible(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_tags()
        tags = review_data.get("tags", [])
        if isinstance(tags, list):
            for tag in tags:
                tag = str(tag).strip()
                if not tag:
                    continue
                chip = QLabel(tag)
                chip.setStyleSheet("""
                    QLabel {
                        background: rgba(0,0,0,0.08);
                        color: #333333;
                        border-radius: 8px;
                        padding: 1px 8px;
                        font-size: 11px;
                        font-weight: 600;
                    }
                """)
                chip.setFixedHeight(18)
                self._tags_row.addWidget(chip)
        self._tags_row.addStretch()
        cover_url = review_data.get("cover_url", "")
        if cover_url:
            from .widgets import ImageLoader
            self._img_loader = ImageLoader(str(cover_url))
            self._img_loader.loaded.connect(self._on_cover)
            self._img_loader.start()

    def _clear_tags(self):
        while self._tags_row.count():
            item = self._tags_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_cover(self, pixmap):
        self._cover.setPixmap(pixmap.scaled(60, 85, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))

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
        if event.button() == Qt.MouseButton.LeftButton and self._manga_id:
            self.clicked.emit(self._manga_id)
        super().mousePressEvent(event)


def _chart_card(title: str, chart_widget: QWidget) -> QWidget:
    card = QWidget()
    card.setObjectName("chartCard")
    card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    card.setStyleSheet(f"""
        QWidget#chartCard {{
            background: #F8FBFF;
            border-radius: {CARD_RADIUS}px;
            border: 1.5px solid {BLUE_LIGHT};
        }}
    """)

    shadow = QGraphicsDropShadowEffect(card)
    shadow.setBlurRadius(12)
    shadow.setOffset(0, 4)
    shadow.setColor(QColor(0, 0, 0, 60))
    card.setGraphicsEffect(shadow)
    card._shadow = shadow

    anim = QPropertyAnimation(card, b"pos")
    anim.setDuration(150)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    card._anim = anim

    def enter(event):
        card._shadow.setBlurRadius(28)
        card._shadow.setOffset(0, 8)
        card._shadow.setColor(QColor(0, 0, 0, 100))
        card._anim.stop()
        card._anim.setStartValue(card.pos())
        card._anim.setEndValue(card.pos() + QPoint(0, -6))
        card._anim.start()

    def leave(event):
        card._shadow.setBlurRadius(12)
        card._shadow.setOffset(0, 4)
        card._shadow.setColor(QColor(0, 0, 0, 60))
        card._anim.stop()
        card._anim.setStartValue(card.pos())
        card._anim.setEndValue(card.pos() + QPoint(0, 6))
        card._anim.start()

    card.enterEvent = enter
    card.leaveEvent = leave

    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)
    hdr = QLabel(title)
    hdr.setFixedHeight(22)
    hdr.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    hdr.setStyleSheet(f"color: {BLUE_PRIMARY}; font-size: 13px; font-weight: 700; background: transparent; border: none; padding: 0; margin: 0;")
    layout.addWidget(hdr)
    layout.addWidget(chart_widget)
    return card


class DashboardPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._loader = None
        self._genre_counts = {}
        self._author_counts = {}
        self._build()
        self._start_loading()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QWidget()
        topbar.setFixedHeight(60)
        _force_bg(topbar, BLUE_DARK)
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(24, 0, 24, 0)
        title = QLabel("Dashboard")
        title.setStyleSheet(f"color:{WHITE};font-size:18px;font-weight:700;background:transparent;")
        tb.addWidget(title)
        tb.addStretch()
        root.addWidget(topbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 24, 24, 24)
        bl.setSpacing(16)

        row1 = QHBoxLayout()
        row1.setSpacing(16)

        self._total = StatCard("Total Manga", "—", bg=BLUE_CARD)
        self._rating = StatCard("Avg Rating", "—", bg=BLUE_CARD)
        self._genre = WideCard("Top Genre", "—")
        self._author = WideCard("Top Author", "—")

        row1.addWidget(self._total, 0, Qt.AlignmentFlag.AlignVCenter)
        row1.addWidget(self._rating, 0, Qt.AlignmentFlag.AlignVCenter)
        row1.addWidget(self._genre, 2, Qt.AlignmentFlag.AlignVCenter)
        row1.addWidget(self._author, 2, Qt.AlignmentFlag.AlignVCenter)
        bl.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(16)

        self._pie = PieChartWidget()
        pie_card = _chart_card("Collection Status", self._pie)
        row2.addWidget(pie_card, stretch=1)

        self._bar = RatingBarChart()
        bar_card = _chart_card("Rating Distribution (1–10)", self._bar)
        row2.addWidget(bar_card, stretch=1)

        bl.addLayout(row2)

        self._total.clicked.connect(self.main_window.go_library)
        self._pie.clicked_status.connect(self.main_window.go_status)
        self._bar.clicked_rating.connect(self.main_window.go_rating)
        self._genre.clicked.connect(self.main_window.go_genre)
        self._author.clicked.connect(self.main_window.go_author)

        bl.addWidget(self._sec("Last Review"))
        self._last_review = LastReviewCard()
        self._last_review.clicked.connect(self.main_window.go_detail)
        bl.addWidget(self._last_review)

        bl.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

    def _sec(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{BLUE_PRIMARY};font-size:15px;font-weight:700;background:transparent;")
        return lbl

    def _start_loading(self):
        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()
        uid = self.main_window.current_user["id"]
        self._loader = DashboardLoader(user_id=uid)
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    @pyqtSlot(dict, object, list)
    def _on_loaded(self, stats, last_review, all_reviews):
        total = int(stats.get("total", 0))
        avg = stats.get("avg_rating")
        top_genre = stats.get("top_genre")
        top_author = stats.get("top_author")
        self._genre_counts = stats.get("genre_counts", {})
        self._author_counts = stats.get("author_counts", {})
        counts = {}
        for k, v in stats.get("counts", {}).items():
            counts[str(k)] = int(v)
        ratings_copy = []
        if all_reviews:
            for r in all_reviews:
                try:
                    ratings_copy.append(int(r))
                except:
                    pass
        last_review_copy = None
        if last_review:
            last_review_copy = {
                "manga_id": int(last_review.get("manga_id", 0)),
                "title": str(last_review.get("title", "—")),
                "cover_url": str(last_review.get("cover_url", "")),
                "rating": last_review.get("rating"),
                "review_text": str(last_review.get("review_text", "")),
                "tags": last_review.get("tags", []),
            }
        self._total.set_value(total)
        self._rating.set_value(f"{avg:.1f}" if avg else "—")
        self._genre.set_value(str(top_genre) if top_genre else "—")
        self._author.set_value(str(top_author) if top_author else "—")
        self._pie.set_data(counts)
        self._bar.set_data(ratings_copy)
        self._last_review.load(last_review_copy)

    def refresh(self):
        self._start_loading()