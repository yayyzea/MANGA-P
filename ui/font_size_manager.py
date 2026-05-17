# MANGA:P — Global Font Size Manager
# Mengatur ukuran font di seluruh aplikasi secara rekursif
 
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QFont
 
 
class FontSizeManager(QObject):
    """
    Singleton yang melacak skala font dan menerapkannya ke seluruh aplikasi.
 
    Strategi ganda:
    1. Patch stylesheet QApplication (untuk widget yang pakai font-size CSS)
    2. Rekursif update QFont semua widget yang punya font eksplisit via setFont()
    """
 
    font_changed = pyqtSignal(float)
 
    _instance = None
    LEVELS = [0.85, 1.0, 1.20, 1.45]
 
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = FontSizeManager()
        return cls._instance
 
    def __init__(self):
        super().__init__()
        self._scale = 1.0
        self._base_stylesheet = ""
        self._app_windows = []
        self._base_fonts = {}  # id(widget) -> base point size (at scale 1.0)
 
    # ── public API ─────────────────────────────────────────────────────────
 
    def set_base_stylesheet(self, css: str):
        self._base_stylesheet = css
 
    def register_window(self, window):
        if window not in self._app_windows:
            self._app_windows.append(window)
 
    def scale(self) -> float:
        return self._scale
 
    def apply(self, scale: float):
        """Terapkan skala font ke stylesheet dan semua widget."""
        self._scale = scale
 
        # 1. Patch stylesheet global
        css = self._patched_stylesheet(scale)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(css)
 
        # 2. Update font semua widget di semua window
        for win in list(self._app_windows):
            try:
                if win and not win.isHidden():
                    self._scale_all_fonts(win, scale)
            except Exception:
                pass
 
        self.font_changed.emit(scale)
 
    def increase(self):
        idx = self._nearest_idx()
        if idx < len(self.LEVELS) - 1:
            self.apply(self.LEVELS[idx + 1])
 
    def decrease(self):
        idx = self._nearest_idx()
        if idx > 0:
            self.apply(self.LEVELS[idx - 1])
 
    # ── internals ──────────────────────────────────────────────────────────
 
    def _nearest_idx(self):
        return min(range(len(self.LEVELS)), key=lambda i: abs(self.LEVELS[i] - self._scale))
 
    def _patched_stylesheet(self, scale: float) -> str:
        import re
        def replacer(m):
            original_px = float(m.group(1))
            new_px = max(8, round(original_px * scale))
            return f"font-size: {new_px}px"
        return re.sub(r"font-size:\s*(\d+(?:\.\d+)?)px", replacer, self._base_stylesheet)
 
    def _scale_all_fonts(self, root_widget, scale: float):
        """
        Crawl semua widget secara rekursif.
        Simpan ukuran font dasar (scale=1.0) pertama kali,
        lalu apply ulang dengan scale baru setiap dipanggil.
        """
        all_widgets = [root_widget] + root_widget.findChildren(QWidget)
        for w in all_widgets:
            try:
                wid = id(w)
                font = w.font()
                pt = font.pointSize()
                if pt <= 0:
                    continue  # widget pakai pixel size atau inherit, skip
 
                # Simpan ukuran dasar pertama kali (saat scale masih 1.0)
                if wid not in self._base_fonts:
                    # Jika sudah pernah di-scale, balik ke base dulu
                    prev_scale = self._scale if self._scale != 0 else 1.0
                    self._base_fonts[wid] = round(pt / prev_scale, 2)
 
                base_pt = self._base_fonts[wid]
                new_pt = max(6, round(base_pt * scale))
                if new_pt != pt:
                    new_font = QFont(font)
                    new_font.setPointSize(new_pt)
                    w.setFont(new_font)
            except Exception:
                pass
 