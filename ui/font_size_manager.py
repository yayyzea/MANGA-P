# MANGA:P — Global Font Size Manager
# Manages font size scaling across the entire app without breaking spacing/padding

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

# Font size presets (base multiplier)
FONT_SIZES = {
    "small":  0.85,
    "normal": 1.0,
    "large":  1.20,
    "xlarge": 1.45,
}

# Base font sizes from the stylesheet (in px)
BASE_FONT_SIZES = {
    "#SearchInput":  14,
    "#SectionLabel": 16,
    "#CardTitle":    11,
    "#CardGenre":    10,
    "#HistoryTitle": 15,
    "#HistoryDesc":  11,
    "#FooterLink":   12,
    "#FilterBtn":    18,
    "QWidget":       13,   # default fallback
}


class FontSizeManager(QObject):
    """Singleton that tracks font scale and rebuilds the QApplication stylesheet."""

    font_changed = pyqtSignal(float)   # emits new scale factor

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = FontSizeManager()
        return cls._instance

    def __init__(self):
        super().__init__()
        self._scale = 1.0       # current scale factor
        self._base_stylesheet = ""  # filled in by MainWindow

    # ── public API ────────────────────────────────────────────────────────────

    def set_base_stylesheet(self, css: str):
        """Store the original stylesheet so we can patch it on every change."""
        self._base_stylesheet = css

    def scale(self) -> float:
        return self._scale

    def apply(self, scale: float):
        """Scale all font-size values in the stylesheet and push to QApplication."""
        self._scale = scale
        css = self._patched_stylesheet(scale)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(css)
        self.font_changed.emit(scale)

    def increase(self):
        levels = [0.85, 1.0, 1.20, 1.45]
        idx = self._nearest_idx(levels)
        if idx < len(levels) - 1:
            self.apply(levels[idx + 1])

    def decrease(self):
        levels = [0.85, 1.0, 1.20, 1.45]
        idx = self._nearest_idx(levels)
        if idx > 0:
            self.apply(levels[idx - 1])

    # ── internals ─────────────────────────────────────────────────────────────

    def _nearest_idx(self, levels):
        return min(range(len(levels)), key=lambda i: abs(levels[i] - self._scale))

    def _patched_stylesheet(self, scale: float) -> str:
        """
        Walk the stylesheet and multiply every `font-size: Npx` value by scale.
        padding/margin/border-radius values are intentionally left untouched so
        spacing is preserved perfectly.
        """
        import re

        def replacer(m):
            original_px = float(m.group(1))
            new_px = max(8, round(original_px * scale))
            return f"font-size: {new_px}px"

        return re.sub(r"font-size:\s*(\d+(?:\.\d+)?)px", replacer, self._base_stylesheet)
