"""
InitialScrapeDialog
-------------------
Ditampilkan sekali saat pertama kali login (DB kosong).
Scrape 500 manga top dari Jikan API, simpan ke DB, lalu tutup otomatis.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QPainter, QLinearGradient, QColor

TARGET = 500          # jumlah manga yang ingin di-scrape
PER_PAGE = 25         # Jikan max per page


# ── Worker thread ──────────────────────────────────────────────────────────────

class ScrapeWorker(QThread):
    """
    Fetch top manga dari Jikan (25 per page) dan upsert ke DB.
    Emit progress(current, total) setiap batch selesai.
    Emit finished() ketika semua selesai.
    """
    progress = pyqtSignal(int, int)   # (jumlah_tersimpan, total_target)
    finished = pyqtSignal(int)        # jumlah total yang berhasil disimpan

    def run(self):
        try:
            from services.jikan_service import JikanService
            from services.manga_service import MangaService
            from database import get_session
            from models.manga import Manga
            import time

            jikan = JikanService()
            svc   = MangaService()
            session = get_session()

            saved = 0
            page  = 1

            try:
                while saved < TARGET:
                    remaining = TARGET - saved
                    fetch_n   = min(PER_PAGE, remaining)

                    import requests
                    import time as _time

                    params = {"limit": fetch_n, "type": "manga", "page": page}
                    try:
                        _time.sleep(0.7)   # hormati rate-limit Jikan
                        resp = jikan._get("top/manga", params=params)
                    except Exception as e:
                        print(f"[ScrapeWorker] Request error page {page}: {e}")
                        break

                    if not resp or "data" not in resp or not resp["data"]:
                        break

                    raw_list = [jikan._clean_manga(item) for item in resp["data"]]

                    # Upsert batch ke DB (reuse MangaService._bulk_upsert logic)
                    svc._bulk_upsert(raw_list, session)

                    saved += len(raw_list)
                    page  += 1

                    self.progress.emit(min(saved, TARGET), TARGET)

                    if len(resp["data"]) < fetch_n:
                        # API sudah tidak punya data lagi
                        break

            finally:
                session.close()

            self.finished.emit(min(saved, TARGET))

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[ScrapeWorker] Fatal error: {e}")
            self.finished.emit(0)


# ── Dialog ─────────────────────────────────────────────────────────────────────

class InitialScrapeDialog(QDialog):
    """
    Modal fullscreen-ish dialog yang ditampilkan saat first login.
    Tidak bisa ditutup user — tutup otomatis setelah scrape selesai.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MANGA:P — Setup Awal")
        self.setModal(True)
        self.setFixedSize(520, 340)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._worker = None
        self._build()

    # ── UI ──────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#1565C0"))
        grad.setColorAt(1.0, QColor("#1E90FF"))
        painter.fillPath(path, grad)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(48, 40, 48, 40)
        root.setSpacing(0)

        # Emoji + judul
        emoji = QLabel("📚")
        emoji.setFont(QFont("Segoe UI", 42))
        emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji.setStyleSheet("background: transparent; color: white;")
        root.addWidget(emoji)
        root.addSpacing(12)

        title = QLabel("Menyiapkan MANGA:P…")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("background: transparent; color: white;")
        root.addWidget(title)
        root.addSpacing(8)

        self._sub = QLabel("Mengambil 500 manga terpopuler dari MyAnimeList.\nIni hanya dilakukan sekali.")
        self._sub.setFont(QFont("Segoe UI", 11))
        self._sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub.setWordWrap(True)
        self._sub.setStyleSheet("background: transparent; color: rgba(255,255,255,0.85);")
        root.addWidget(self._sub)
        root.addSpacing(28)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setRange(0, TARGET)
        self._bar.setValue(0)
        self._bar.setFixedHeight(14)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255,255,255,0.20);
                border: none;
                border-radius: 7px;
            }
            QProgressBar::chunk {
                background: white;
                border-radius: 7px;
            }
        """)
        root.addWidget(self._bar)
        root.addSpacing(10)

        # Counter label
        self._count_lbl = QLabel(f"0 / {TARGET} manga")
        self._count_lbl.setFont(QFont("Segoe UI", 10))
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_lbl.setStyleSheet("background: transparent; color: rgba(255,255,255,0.75);")
        root.addWidget(self._count_lbl)
        root.addStretch()

        # Status bawah
        self._status_lbl = QLabel("⏳  Menghubungi Jikan API…")
        self._status_lbl.setFont(QFont("Segoe UI", 10))
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setStyleSheet("background: transparent; color: rgba(255,255,255,0.65);")
        root.addWidget(self._status_lbl)

    # ── Public ──────────────────────────────────────────────────────────────

    def start_scrape(self):
        """Mulai worker thread. Panggil setelah dialog.show()."""
        self._worker = ScrapeWorker()
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    # ── Slots ────────────────────────────────────────────────────────────────

    @pyqtSlot(int, int)
    def _on_progress(self, current: int, total: int):
        self._bar.setValue(current)
        self._count_lbl.setText(f"{current} / {total} manga")
        pct = int(current / total * 100) if total else 0
        self._status_lbl.setText(f"⏳  Mengambil data… {pct}%")

    @pyqtSlot(int)
    def _on_finished(self, count: int):
        self._bar.setValue(TARGET)
        self._count_lbl.setText(f"{count} manga berhasil disimpan ✓")
        self._status_lbl.setText("✅  Selesai! Membuka aplikasi…")

        # Tunggu sebentar biar user bisa baca, lalu tutup
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1200, self.accept)

    # Cegah user menutup dialog dengan tombol Escape / klik luar
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        # Hanya boleh ditutup oleh accept() (setelah scrape selesai)
        if self._worker and self._worker.isRunning():
            event.ignore()
        else:
            super().closeEvent(event)