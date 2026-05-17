# MANGA:P — Global Font Size Manager (px-based)

import re
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QFont

# ── Font size range ───────────────────────────────────────────────────────────
FONT_MIN_PX  = 11   # smallest allowed size
FONT_MAX_PX  = 20   # largest allowed size
FONT_BASE_PX = 13   # default / reset size

_RX = re.compile(r"font-size:\s*(\d+(?:\.\d+)?)px")


def _patch_css(css: str, scale: float) -> str:
    """Scale every font-size: Npx in a CSS string."""
    def replacer(m: re.Match) -> str:
        new_px = max(FONT_MIN_PX, round(float(m.group(1)) * scale))
        return f"font-size: {new_px}px"
    return _RX.sub(replacer, css)


class FontSizeManager(QObject):
    """
    Singleton managing app-wide font size in discrete +1/-1 px steps.

    Strategy (both applied on every change):
    1. Patch global QApplication stylesheet  (catches #objectName rules)
    2. Walk every widget and patch its inline stylesheet  (catches setStyleSheet calls)
    3. Walk every widget and scale its QFont pointSize  (catches setFont calls)
    """

    font_changed = pyqtSignal(int)   # emits current px size

    _instance = None

    @classmethod
    def instance(cls) -> "FontSizeManager":
        if cls._instance is None:
            cls._instance = FontSizeManager()
        return cls._instance

    def __init__(self):
        super().__init__()
        self._px: int = FONT_BASE_PX
        self._base_stylesheet: str = ""
        self._app_windows: list = []
        # Per-widget baseline storage (at FONT_BASE_PX)
        self._base_inline: dict  = {}   # id(w) -> original inline stylesheet
        self._base_font_pt: dict = {}   # id(w) -> base pointSize

    # ── public API ────────────────────────────────────────────────────────────

    def set_base_stylesheet(self, css: str) -> None:
        self._base_stylesheet = css

    def register_window(self, window) -> None:
        if window not in self._app_windows:
            self._app_windows.append(window)

    def px(self) -> int:
        return self._px

    def scale(self) -> float:
        """Backward-compat for any code still calling scale()."""
        return self._px / FONT_BASE_PX

    def apply_px(self, px: int) -> None:
        self._px = max(FONT_MIN_PX, min(FONT_MAX_PX, px))
        scale = self._px / FONT_BASE_PX

        # 1. Patch global stylesheet
        app = QApplication.instance()
        if app:
            app.setStyleSheet(_patch_css(self._base_stylesheet, scale))

        # 2 & 3. Walk all widgets in all registered windows
        for win in list(self._app_windows):
            try:
                if win and not win.isHidden():
                    self._apply_to_tree(win, scale)
            except Exception:
                pass

        self.font_changed.emit(self._px)

    def increase(self) -> None:
        if self._px < FONT_MAX_PX:
            self.apply_px(self._px + 1)

    def decrease(self) -> None:
        if self._px > FONT_MIN_PX:
            self.apply_px(self._px - 1)

    def reset(self) -> None:
        self._base_inline.clear()
        self._base_font_pt.clear()
        self.apply_px(FONT_BASE_PX)

    def can_increase(self) -> bool:
        return self._px < FONT_MAX_PX

    def can_decrease(self) -> bool:
        return self._px > FONT_MIN_PX

    # ── internals ─────────────────────────────────────────────────────────────

    def _apply_to_tree(self, root: QWidget, scale: float) -> None:
        all_widgets = [root] + root.findChildren(QWidget)
        for w in all_widgets:
            try:
                wid = id(w)

                # ── A. Inline stylesheet ──────────────────────────────────────
                # Store the *original* (base) inline style the first time we
                # see this widget, then always re-scale from that baseline.
                inline = w.styleSheet()
                if inline and _RX.search(inline):
                    if wid not in self._base_inline:
                        # If we're already at non-base scale, back-calculate
                        # the original by reversing the current scale.
                        cur_scale = self._px / FONT_BASE_PX if self._px else 1.0
                        self._base_inline[wid] = _RX.sub(
                            lambda m: f"font-size: {round(float(m.group(1)) / cur_scale)}px",
                            inline,
                        )
                    patched = _patch_css(self._base_inline[wid], scale)
                    if patched != inline:
                        w.setStyleSheet(patched)

                # ── B. QFont pointSize ────────────────────────────────────────
                font = w.font()
                pt   = font.pointSize()
                if pt > 0:
                    if wid not in self._base_font_pt:
                        cur_scale = self._px / FONT_BASE_PX if self._px else 1.0
                        self._base_font_pt[wid] = round(pt / cur_scale, 2)
                    new_pt = max(6, round(self._base_font_pt[wid] * scale))
                    if new_pt != pt:
                        nf = QFont(font)
                        nf.setPointSize(new_pt)
                        w.setFont(nf)

            except Exception:
                pass