from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QThread, QRectF
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QPushButton, QSizePolicy, QGridLayout,
    QSplitter
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QPainterPath, QLinearGradient, QPixmap
)

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_LIGHT,
    WHITE, TEXT_DARK, TEXT_MUTED, CARD_RADIUS
)

def _force_bg(widget, hex_color, radius=0):
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    r = f"border-radius: {radius}px;" if radius else ""
    widget.setStyleSheet(f"background: {hex_color}; {r}")

class AuthorPageLoader(QThread):
    finished = pyqtSignal(list, dict, str)

    def __init__(self, user_id: int, author: str):
        super().__init__()
        self.user_id = user_id
        self.author = author

    def run(self):
        manga_list = []
        author_counts = {}
        author_display = self.author

        try:
            from database import get_session
            from models.manga import Manga
            from models.user_collection import UserCollection

            session = get_session()
            try:
                all_rows = (
                    session.query(Manga)
                    .join(UserCollection, UserCollection.manga_id == Manga.id)
                    .filter(
                        UserCollection.user_id == self.user_id,
                        Manga.authors != None,
                        Manga.authors != ""
                    )
                    .all()
                )

                search_term = self.author.strip()

                for manga in all_rows:
                    author_list = manga.authors_list()
                    
                    for a in author_list:
                        author_counts[a] = author_counts.get(a, 0) + 1
                    
                    if search_term in author_list:
                        manga_list.append({
                            "id": manga.id,
                            "title": manga.title,
                            "cover_url": manga.cover_url or "",
                            "score": manga.score or 0,
                            "author": manga.authors or "",
                            "status": manga.status or "?",
                        })

                manga_list.sort(key=lambda x: x["score"], reverse=True)
                author_counts = dict(sorted(author_counts.items(), key=lambda x: x[1], reverse=True))

            finally:
                session.close()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[AuthorPage] Error loading author '{self.author}': {e}")

        self.finished.emit(manga_list, author_counts, author_display)

class AuthorBarChart(QWidget):
    clicked_author = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self._selected = ""
        self._bar_rects = []
        self._hovered_author = None
        self.setMinimumWidth(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    def set_data(self, counts: dict, selected_author: str = ""):
        self._data = counts if counts else {}
        self._selected = selected_author
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        max_count = max(self._data.values()) if self._data else 1

        if not self._data:
            painter.setPen(QColor(TEXT_MUTED))
            font = QFont("Segoe UI", 11)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data")
            return

        padding_t = 20
        padding_b = 20
        bar_h = 28
        gap = 10
        start_y = padding_t
        self._bar_rects = []

        for i, (author, count) in enumerate(self._data.items()):
            y = start_y + i * (bar_h + gap)

            if y + bar_h < 0 or y > h:
                continue

            bar_w = max(8, int((w - 160) * count / max_count))

            bar_rect = QRectF(0, y, bar_w, bar_h)
            grad = QLinearGradient(bar_rect.topLeft(), bar_rect.topRight())
            if author == self._selected:
                grad.setColorAt(0, QColor(BLUE_PRIMARY))
                grad.setColorAt(1, QColor("#64B5F6"))
            elif author == self._hovered_author:
                grad.setColorAt(0, QColor("#5BA4E6"))
                grad.setColorAt(1, QColor("#82C4F8"))
            else:
                grad.setColorAt(0, QColor(BLUE_CARD))
                grad.setColorAt(1, QColor(BLUE_LIGHT))
            painter.setBrush(QBrush(grad))

            if author == self._hovered_author:
                painter.setPen(QPen(QColor(WHITE), 2))
            else:
                painter.setPen(Qt.PenStyle.NoPen)

            path = QPainterPath()
            path.addRoundedRect(bar_rect, 14, 14)
            painter.drawPath(path)

            display_name = author
            if len(display_name) > 18:
                display_name = display_name[:16] + "…"

            painter.setPen(QColor(TEXT_DARK))
            font = QFont("Segoe UI", 9, QFont.Weight.Bold)
            painter.setFont(font)
            label_rect = QRectF(10, y, bar_w - 20, bar_h)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, display_name)

            painter.setPen(QColor(TEXT_DARK))
            font = QFont("Segoe UI", 11, QFont.Weight.Bold)
            painter.setFont(font)
            count_text = f"{count}"
            painter.drawText(
                QRectF(bar_w + 8, y, 50, bar_h),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                count_text
            )

            total = sum(self._data.values())
            if total > 0:
                pct = count / total * 100
                painter.setPen(QColor(TEXT_MUTED))
                font = QFont("Segoe UI", 9)
                painter.setFont(font)
                painter.drawText(
                    QRectF(bar_w + 55, y, 70, bar_h),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    f"({pct:.0f}%)"
                )

            self._bar_rects.append((QRectF(0, y, w, bar_h), author))

        total_height = start_y + len(self._data) * (bar_h + gap) + padding_b
        if total_height != self.minimumHeight():
            self.setMinimumHeight(max(total_height, 200))

    def mouseMoveEvent(self, event):
        pos = event.position()
        new_hover = None
        for rect, author in self._bar_rects:
            if rect.contains(pos):
                new_hover = author
                break

        if new_hover != self._hovered_author:
            self._hovered_author = new_hover
            self.update()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._hovered_author:
            self.clicked_author.emit(self._hovered_author)
        super().mousePressEvent(event)

class MangaCardCompact(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, manga_data: dict, parent=None):
        super().__init__(parent)
        self.manga_id = manga_data.get("id", 0)
        self.setFixedSize(130, 210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        _force_bg(self, BLUE_CARD, radius=10)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.cover = QLabel()
        self.cover.setFixedSize(114, 150)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setScaledContents(True)
        self.cover.setStyleSheet("background: rgba(255,255,255,0.15); border-radius: 6px;")
        layout.addWidget(self.cover, alignment=Qt.AlignmentFlag.AlignCenter)

        title = manga_data.get("title", "—")
        if len(title) > 18:
            title = title[:16] + "…"
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: #111111; font-size: 10px; font-weight: 700; background: transparent;"
        )
        title_lbl.setWordWrap(True)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        score = manga_data.get("score", 0)
        if score:
            score_lbl = QLabel(f"★ {score:.1f}")
            score_lbl.setStyleSheet(
                f"color: rgba(0,0,0,0.60); font-size: 9px; font-weight: 600; background: transparent;"
            )
            score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(score_lbl)

        layout.addStretch()

        cover_url = manga_data.get("cover_url", "")
        if cover_url:
            from .widgets import ImageLoader
            self._img_loader = ImageLoader(str(cover_url))
            self._img_loader.loaded.connect(self._on_cover)
            self._img_loader.start()

    def _on_cover(self, pixmap):
        self.cover.setPixmap(
            pixmap.scaled(114, 150,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.manga_id)
        super().mousePressEvent(event)

class AuthorPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._current_author = ""
        self._loader = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QWidget()
        topbar.setFixedHeight(60)
        topbar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        topbar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7aaee0,stop:0.5 #80d9e8,stop:1 #b5dfa0);")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 24, 0)
        tb.setSpacing(12)

        self._back_btn = QPushButton("←")
        self._back_btn.setFixedSize(36, 36)
        self._back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.20);
                color: {WHITE}; border: none; border-radius: 18px;
                font-size: 18px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.35); }}
        """)
        self._back_btn.clicked.connect(self._go_back)
        tb.addWidget(self._back_btn)

        self._title_lbl = QLabel("Author")
        self._title_lbl.setStyleSheet(
            f"color: {WHITE}; font-size: 18px; font-weight: 700; background: transparent;"
        )
        tb.addWidget(self._title_lbl)

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: rgba(0,0,0,0.55); font-size: 12px; background: transparent;"
        )
        tb.addWidget(self._count_lbl)
        tb.addStretch()
        root.addWidget(topbar)

        info_banner = QLabel("One manga may have multiple authors.")
        info_banner.setStyleSheet(f"""
            QLabel {{
                background: rgba(196,181,222,0.22);
                color: {TEXT_DARK};
                font-size: 11px;
                padding: 6px 16px;
                border: none;
            }}
        """)
        root.addWidget(info_banner)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: #E0E0E0; width: 2px; }")
        splitter.setChildrenCollapsible(False)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setStyleSheet("background: transparent; border: none;")

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background: transparent;")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(24, 24, 12, 24)
        self._grid_layout.setSpacing(14)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        left_scroll.setWidget(self._grid_container)
        splitter.addWidget(left_scroll)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setStyleSheet("background: transparent; border: none;")

        right_container = QWidget()
        right_container.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(16, 24, 24, 24)
        right_layout.setSpacing(8)

        chart_title = QLabel("Author Distribution")
        chart_title.setStyleSheet(
            f"color: {BLUE_PRIMARY}; font-size: 14px; font-weight: 700; background: transparent;"
        )
        right_layout.addWidget(chart_title)

        self._bar_chart = AuthorBarChart()
        self._bar_chart.clicked_author.connect(self._on_bar_clicked)
        right_layout.addWidget(self._bar_chart, stretch=1)

        right_scroll.setWidget(right_container)
        splitter.addWidget(right_scroll)

        splitter.setSizes([600, 400])

        root.addWidget(splitter, stretch=1)

    def load_author(self, author: str):
        self._current_author = author
        self._title_lbl.setText(author)
        self._count_lbl.setText("Loading...")
        self._clear_grid()

        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()

        uid = (self.main_window.current_user or {}).get('id', 1)
        self._loader = AuthorPageLoader(user_id=uid, author=author)
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    @pyqtSlot(list, dict, str)
    def _on_loaded(self, manga_list, author_counts, author_name):
        self._count_lbl.setText(f"• {len(manga_list)} manga")
        self._clear_grid()

        self._bar_chart.set_data(author_counts, selected_author=author_name)

        if not manga_list:
            empty = QLabel(f'No manga found by "{author_name}".')
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; background: transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid_layout.addWidget(empty, 0, 0, 1, 4)
            return

        container_width = self._grid_container.width() - 24
        card_w = 130
        spacing = 14
        cols = max(1, (container_width + spacing) // (card_w + spacing))

        for i, manga in enumerate(manga_list):
            card = MangaCardCompact(manga)
            card.clicked.connect(self.main_window.go_detail)
            row, col = divmod(i, cols)
            self._grid_layout.addWidget(card, row, col, alignment=Qt.AlignmentFlag.AlignCenter)
            
    def _on_bar_clicked(self, author: str):
        if author != self._current_author:
            self.load_author(author)

    def _clear_grid(self):
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _go_back(self):
        if hasattr(self.main_window, 'go_dashboard'):
            self.main_window.go_dashboard()