"""
InitialScrapeDialog
-------------------
Displayed once on first login (empty DB).
Scrapes top manga from Jikan API, saves to DB, then closes automatically.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QPainter, QLinearGradient, QColor

TARGET = 500
PER_PAGE = 25


class ScrapeWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(int)

    def run(self):
        try:
            from services.jikan_service import JikanService
            from services.manga_service import MangaService
            from database import get_session
            import time as _time

            jikan = JikanService()
            svc   = MangaService()
            session = get_session()
            saved = 0
            page  = 1

            try:
                while saved < TARGET:
                    remaining = TARGET - saved
                    fetch_n   = min(PER_PAGE, remaining)
                    params = {"limit": fetch_n, "type": "manga", "page": page}
                    try:
                        _time.sleep(0.7)
                        resp = jikan._get("top/manga", params=params)
                    except Exception as e:
                        print(f"[ScrapeWorker] Request error page {page}: {e}")
                        break

                    if not resp or "data" not in resp or not resp["data"]:
                        break

                    raw_list = [jikan._clean_manga(item) for item in resp["data"]]
                    svc._bulk_upsert(raw_list, session)

                    saved += len(raw_list)
                    page  += 1
                    self.progress.emit(min(saved, TARGET), TARGET)

                    if len(resp["data"]) < fetch_n:
                        break
            finally:
                session.close()

            self.finished.emit(min(saved, TARGET))

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(0)


class InitialScrapeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MANGA:P — Initial Setup")
        self.setModal(True)
        self.setFixedSize(520, 340)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._worker = None
        self._build()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 22, 22)
        # 水のドレス diagonal gradient
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0.0,  QColor("#006ec4"))   # Sky Blue
        grad.setColorAt(0.4,  QColor("#2cb5d3"))   # Teal
        grad.setColorAt(0.75, QColor("#9abe7c"))   # Dewy Green
        grad.setColorAt(1.0,  QColor("#c4b5de"))   # Lilac Mist
        painter.fillPath(path, grad)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(48, 40, 48, 40)
        root.setSpacing(0)

        emoji = QLabel("📚")
        emoji.setFont(QFont("Segoe UI", 42))
        emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji.setStyleSheet("background: transparent; color: white;")
        root.addWidget(emoji)
        root.addSpacing(12)

        title = QLabel("Setting up MANGA:P…")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("background: transparent; color: white;")
        root.addWidget(title)
        root.addSpacing(8)

        self._sub = QLabel("Fetching the most popular manga from MyAnimeList.\nThis only needs to be done once.")
        self._sub.setFont(QFont("Segoe UI", 11))
        self._sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub.setWordWrap(True)
        self._sub.setStyleSheet("background: transparent; color: rgba(255,255,255,0.88);")
        root.addWidget(self._sub)
        root.addSpacing(28)

        self._bar = QProgressBar()
        self._bar.setRange(0, TARGET)
        self._bar.setValue(0)
        self._bar.setFixedHeight(14)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255,255,255,0.22);
                border: none;
                border-radius: 7px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 white, stop:1 rgba(255,255,255,0.75));
                border-radius: 7px;
            }
        """)
        root.addWidget(self._bar)
        root.addSpacing(10)

        self._count_lbl = QLabel("0 manga fetched")
        self._count_lbl.setFont(QFont("Segoe UI", 10))
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_lbl.setStyleSheet("background: transparent; color: rgba(255,255,255,0.78);")
        root.addWidget(self._count_lbl)
        root.addStretch()

        self._status_lbl = QLabel("⏳  Connecting to Jikan API…")
        self._status_lbl.setFont(QFont("Segoe UI", 10))
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setStyleSheet("background: transparent; color: rgba(255,255,255,0.65);")
        root.addWidget(self._status_lbl)

    def start_scrape(self):
        self._worker = ScrapeWorker()
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    @pyqtSlot(int, int)
    def _on_progress(self, current: int, total: int):
        self._bar.setValue(current)
        self._count_lbl.setText(f"{current} manga fetched")
        pct = int(current / total * 100) if total else 0
        self._status_lbl.setText(f"⏳  Fetching data… {pct}%")

    @pyqtSlot(int)
    def _on_finished(self, count: int):
        self._bar.setValue(TARGET)
        self._count_lbl.setText(f"{count} manga saved successfully ✓")
        self._status_lbl.setText("✅  Done! Opening app…")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1200, self.accept)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            event.ignore()
        else:
            super().closeEvent(event)
