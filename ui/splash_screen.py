"""
SplashScreen — overlay transparan di atas MainWindow.
Muncul saat app pertama kali buka, fade out otomatis setelah
HomePage selesai loading data (dan scraping selesai jika DB kosong).
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSlot, QPoint
)
from PyQt6.QtGui import (
    QPainter, QPainterPath, QColor, QBrush,
    QLinearGradient, QPen, QFont, QPixmap
)

from .theme import BLUE_PRIMARY, BLUE_DARK, WHITE


# ── Dots loading animation ────────────────────────────────────────────────────

class _DotsWidget(QWidget):
    """Tiga titik yang bergantian membesar — indikator loading."""

    DOT_R   = 7
    DOT_GAP = 18
    PERIOD  = 1200

    def __init__(self, parent=None):
        super().__init__(parent)
        n = 3
        total_w = (n - 1) * self.DOT_GAP + self.DOT_R * 2
        self.setFixedSize(total_w + 8, self.DOT_R * 2 + 8)
        self._phase = 0

        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        self._phase = (self._phase + 30) % self.PERIOD
        self.update()

    def stop(self):
        self._timer.stop()

    def paintEvent(self, event):
        import math
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx = w // 2 - self.DOT_GAP
        cy = h // 2

        for i in range(3):
            offset = (self._phase - i * (self.PERIOD / 3)) % self.PERIOD
            t = offset / self.PERIOD
            scale = 0.6 + 0.4 * (0.5 + 0.5 * math.sin(2 * math.pi * t - math.pi / 2))
            r = self.DOT_R * scale

            alpha = int(120 + 135 * scale)
            color = QColor(255, 255, 255, alpha)
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)

            x = cx + i * self.DOT_GAP
            p.drawEllipse(int(x - r), int(cy - r), int(r * 2), int(r * 2))


# ── SplashScreen ─────────────────────────────────────────────────────────────

class SplashScreen(QWidget):
    """
    Overlay penuh di atas MainWindow.
    - Mode normal  : dots animation + "Loading your library…"
    - Mode scraping: progress bar + counter + status text
    Panggil .dismiss() setelah semua proses selesai.
    """

    SCRAPE_TARGET = 500

    def __init__(self, parent=None):
        super().__init__(parent)
        if parent:
            self.resize(parent.size())
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setWindowFlags(Qt.WindowType.Widget)
        self.raise_()

        self._dismissed       = False
        self._scrape_done     = False
        self._home_done       = False
        self._scraping_active = False

        self._build_ui()

        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_anim.setDuration(500)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._opacity_anim.finished.connect(self.hide)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(20)

        # Logo PNG
        import os
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: transparent;")

        base_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(base_dir, "assets", "Manga-P_Logo.png")
        if not os.path.isfile(logo_path):
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Manga-P_Logo.png")

        px = QPixmap(logo_path)
        if not px.isNull():
            px = px.scaledToWidth(380, Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(px)
        else:
            logo.setText("MANGA:P")
            logo.setStyleSheet(
                f"color: {WHITE}; font-size: 40px; font-weight: 800;"
                "letter-spacing: 6px; background: transparent;"
            )
        lay.addWidget(logo)

        # Subtitle — berubah saat scraping
        self._sub = QLabel("Loading your library…")
        self._sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub.setStyleSheet(
            "color: rgba(255,255,255,0.65); font-size: 13px; background: transparent;"
        )
        lay.addWidget(self._sub)

        # ── Progress bar (hidden by default, shown during scraping) ──
        self._progress_wrap = QWidget()
        self._progress_wrap.setStyleSheet("background: transparent;")
        self._progress_wrap.setFixedWidth(420)
        pw_lay = QVBoxLayout(self._progress_wrap)
        pw_lay.setContentsMargins(0, 0, 0, 0)
        pw_lay.setSpacing(8)

        self._bar = QProgressBar()
        self._bar.setRange(0, self.SCRAPE_TARGET)
        self._bar.setValue(0)
        self._bar.setFixedHeight(10)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255,255,255,0.22);
                border: none;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 white, stop:1 rgba(255,255,255,0.70));
                border-radius: 5px;
            }
        """)
        pw_lay.addWidget(self._bar)

        self._count_lbl = QLabel("0 manga fetched")
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.78); font-size: 11px; background: transparent;"
        )
        pw_lay.addWidget(self._count_lbl)

        self._progress_wrap.setVisible(False)
        lay.addWidget(self._progress_wrap, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ── Dots (shown during normal loading) ──
        dots_container = QWidget()
        dots_container.setStyleSheet("background: transparent;")
        dc = QVBoxLayout(dots_container)
        dc.setContentsMargins(0, 0, 0, 0)
        dc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dots = _DotsWidget()
        dc.addWidget(self._dots, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(dots_container)
        self._dots_container = dots_container

    # ── Background paint ──────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0.00, QColor("#006ec4"))
        grad.setColorAt(0.35, QColor("#2cb5d3"))
        grad.setColorAt(0.70, QColor("#9abe7c"))
        grad.setColorAt(1.00, QColor("#c4b5de"))
        p.fillRect(self.rect(), grad)

    # ── Scraping mode ─────────────────────────────────────────────────────────

    def enter_scrape_mode(self):
        """Panggil sebelum scraping dimulai — tampilkan progress bar."""
        self._scraping_active = True
        self._sub.setText("Fetching the most popular manga from MyAnimeList.\nThis only needs to be done once.")
        self._sub.setStyleSheet(
            "color: rgba(255,255,255,0.88); font-size: 12px;"
            "background: transparent;"
        )
        self._dots_container.setVisible(False)
        self._progress_wrap.setVisible(True)

    @pyqtSlot(int, int)
    def update_scrape_progress(self, current: int, total: int):
        self._bar.setValue(current)
        self._count_lbl.setText(f"{current} manga fetched")

    @pyqtSlot(int)
    def scrape_finished(self, count: int):
        """Dipanggil saat ScrapeWorker selesai."""
        self._bar.setValue(self.SCRAPE_TARGET)
        self._count_lbl.setText(f"{count} manga saved ✓")
        self._scrape_done = True
        self._scraping_active = False
        # Kembali ke mode loading biasa sementara HomePage load
        QTimer.singleShot(400, self._switch_to_loading_mode)

    def _switch_to_loading_mode(self):
        self._progress_wrap.setVisible(False)
        self._dots_container.setVisible(True)
        self._sub.setText("Loading your library…")
        self._sub.setStyleSheet(
            "color: rgba(255,255,255,0.65); font-size: 13px; background: transparent;"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    @pyqtSlot()
    def notify_home_ready(self):
        """Dipanggil oleh HomePage setelah data pertama kali selesai dimuat."""
        self._home_done = True
        self._try_dismiss()

    def _try_dismiss(self):
        """Dismiss hanya jika scraping selesai (atau tidak perlu) DAN home sudah siap."""
        if self._dismissed:
            return
        if self._scraping_active:
            return
        if not self._home_done:
            return
        self.dismiss()

    @pyqtSlot()
    def dismiss(self):
        if self._dismissed:
            return
        self._dismissed = True
        self._dots.stop()
        QTimer.singleShot(300, self._start_fade)

    def _start_fade(self):
        self._opacity_anim.setStartValue(1.0)
        self._opacity_anim.setEndValue(0.0)
        self._opacity_anim.start()