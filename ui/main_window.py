from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QGraphicsOpacityEffect,
    QFrame
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QPoint
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QIcon
from pathlib import Path
 
_ICON_DIR = Path(__file__).parent.parent / "assets"
 
from .theme import BLUE_PRIMARY, WHITE, SIDEBAR_WIDTH, APP_STYLESHEET
from .font_size_manager import FontSizeManager
 
 
class Toast(QLabel):
    def __init__(self, parent, message: str, duration: int = 2000):
        super().__init__(message, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "background: #1E1E2E; color: white; border-radius: 10px;"
            "padding: 10px 20px; font-size: 13px; font-weight: 600;"
        )
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.adjustSize()
        self._reposition()
        self.raise_()
        self.show()
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(1.0)
        self._anim = QPropertyAnimation(self._effect, b"opacity")
        self._anim.setDuration(500)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self._anim.finished.connect(self.deleteLater)
        QTimer.singleShot(duration, self._anim.start)
 
    def _reposition(self):
        p = self.parent()
        if p:
            pw, ph = p.width(), p.height()
            self.move((pw - self.width()) // 2, ph - self.height() - 50)
 
 
class FontSizePopup(QFrame):
    """
    Flyout panel muncul di kanan sidebar saat tombol 'Aa' diklik.
    Menampilkan tombol '-' dan '+' untuk memperkecil/memperbesar font,
    beserta indikator level font saat ini.
    """
 
    # Label level font yang ditampilkan ke user
    _LEVEL_LABELS = ["Kecil", "Normal", "Besar", "X-Besar"]
    _LEVELS       = [0.85, 1.0, 1.20, 1.45]
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FontSizePopup")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            #FontSizePopup {
                background: #1565C0;
                border-radius: 14px;
                border: 1.5px solid rgba(255,255,255,0.30);
            }
        """)
 
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)
 
        # ── Judul popup ────────────────────────────────────────────────
        title_lbl = QLabel("Ukuran Teks")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setFont(QFont("Segoe UI", 9))
        title_lbl.setStyleSheet("color: rgba(255,255,255,0.70); background: transparent;")
        outer.addWidget(title_lbl)
 
        # ── Baris kontrol: [−] [label level] [+] ──────────────────────
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)
        ctrl_row.setContentsMargins(0, 0, 0, 0)
 
        # Tombol minus
        self._btn_dec = QPushButton("−")
        self._btn_dec.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._btn_dec.setFixedSize(40, 40)
        self._btn_dec.setToolTip("Perkecil teks")
        self._btn_dec.setStyleSheet(self._action_btn_style())
        self._btn_dec.clicked.connect(self._decrease)
 
        # Label level saat ini
        self._level_lbl = QLabel("Normal")
        self._level_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._level_lbl.setFixedWidth(62)
        self._level_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._level_lbl.setStyleSheet("color: white; background: transparent;")
 
        # Tombol plus
        self._btn_inc = QPushButton("+")
        self._btn_inc.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._btn_inc.setFixedSize(40, 40)
        self._btn_inc.setToolTip("Perbesar teks")
        self._btn_inc.setStyleSheet(self._action_btn_style())
        self._btn_inc.clicked.connect(self._increase)
 
        ctrl_row.addWidget(self._btn_dec)
        ctrl_row.addWidget(self._level_lbl)
        ctrl_row.addWidget(self._btn_inc)
        outer.addLayout(ctrl_row)
 
        # ── Indikator titik level ──────────────────────────────────────
        dot_row = QHBoxLayout()
        dot_row.setSpacing(6)
        dot_row.setContentsMargins(0, 0, 0, 0)
        dot_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dots = []
        for _ in self._LEVELS:
            dot = QLabel("●")
            dot.setFont(QFont("Segoe UI", 8))
            dot.setStyleSheet("color: rgba(255,255,255,0.35); background: transparent;")
            self._dots.append(dot)
            dot_row.addWidget(dot)
        outer.addLayout(dot_row)
 
        self.adjustSize()
        self._refresh_ui()
 
    # ── Gaya tombol aksi ──────────────────────────────────────────────
    @staticmethod
    def _action_btn_style():
        return """
            QPushButton {
                background: rgba(255,255,255,0.18);
                border: none;
                border-radius: 10px;
                color: white;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.35);
            }
            QPushButton:pressed {
                background: rgba(255,255,255,0.55);
            }
            QPushButton:disabled {
                background: rgba(255,255,255,0.07);
                color: rgba(255,255,255,0.30);
            }
        """
 
    # ── Perbarui label & indikator sesuai skala saat ini ─────────────
    def _refresh_ui(self):
        mgr = FontSizeManager.instance()
        idx = min(range(len(self._LEVELS)),
                  key=lambda i: abs(self._LEVELS[i] - mgr.scale()))
        self._level_lbl.setText(self._LEVEL_LABELS[idx])
        self._btn_dec.setEnabled(idx > 0)
        self._btn_inc.setEnabled(idx < len(self._LEVELS) - 1)
        for i, dot in enumerate(self._dots):
            dot.setStyleSheet(
                "color: white; background: transparent;"
                if i == idx else
                "color: rgba(255,255,255,0.30); background: transparent;"
            )
 
    def _decrease(self):
        FontSizeManager.instance().decrease()
        self._refresh_ui()
 
    def _increase(self):
        FontSizeManager.instance().increase()
        self._refresh_ui()
 
    def show_near(self, sidebar_widget: QWidget, trigger_btn: QWidget):
        """Tampilkan popup di kanan sidebar, sejajar dengan tombol pemicu."""
        self._refresh_ui()
        global_pos = trigger_btn.mapToGlobal(QPoint(0, 0))
        x = global_pos.x() + sidebar_widget.width() + 6
        y = global_pos.y() + (trigger_btn.height() - self.height()) // 2
        self.move(x, y)
        self.show()
        self.raise_()
 
 
 
class _AaButton(QWidget):
    """
    Tombol sidebar berbentuk 'Aa' — huruf kecil dan besar berdampingan.
    Memancarkan sinyal clicked() saat diklik / ditekan Enter.
    Mendukung state aktif (checked) dengan highlight background.
    """
 
    from PyQt6.QtCore import pyqtSignal as _sig
    clicked = _sig()
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AaButton")
        self._checked = False
        self._hovered = False
        # PENTING: jangan pakai WA_StyledBackground — biarkan paintEvent yang handle background
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAutoFillBackground(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
 
    def setChecked(self, state: bool):
        self._checked = state
        self.update()
 
    def isChecked(self) -> bool:
        return self._checked
 
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QBrush, QPen, QColor as QC
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
 
        # Gambar background sidebar dulu (BIRU) agar tidak putih
        from .theme import BLUE_PRIMARY
        p.setBrush(QBrush(QC(BLUE_PRIMARY)))
        p.setPen(QPen(QC(0, 0, 0, 0)))
        p.drawRect(0, 0, w, h)
 
        # Overlay highlight saat checked atau hover
        if self._checked:
            p.setBrush(QBrush(QC(255, 255, 255, 76)))
            p.drawRoundedRect(4, 4, w - 8, h - 8, 10, 10)
        elif self._hovered:
            p.setBrush(QBrush(QC(255, 255, 255, 40)))
            p.drawRoundedRect(4, 4, w - 8, h - 8, 10, 10)
 
        # "a" kecil — kiri bawah
        fa = QFont("Segoe UI", 10, QFont.Weight.Bold)
        p.setFont(fa)
        p.setPen(QPen(QC(255, 255, 255, 200)))
        p.drawText(5, 0, w // 2 + 2, h, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, "a")
 
        # "A" besar — kanan tengah
        fA = QFont("Segoe UI", 17, QFont.Weight.Bold)
        p.setFont(fA)
        p.setPen(QPen(QC(255, 255, 255, 255)))
        p.drawText(w // 2 - 4, 0, w // 2 + 4, h, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "A")
 
        p.end()
 
    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)
 
    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)
 
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self.update()
            self.clicked.emit()
        super().mousePressEvent(event)
 
    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt as Qt_
        if event.key() in (Qt_.Key.Key_Return, Qt_.Key.Key_Space):
            self._checked = not self._checked
            self.update()
            self.clicked.emit()
        super().keyPressEvent(event)
 
 
class Sidebar(QWidget):
    def __init__(self, on_navigate, on_logo_click=None, on_logout=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.on_navigate = on_navigate
        self.on_logo_click = on_logo_click
        self.on_logout = on_logout
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(BLUE_PRIMARY))
        self.setPalette(pal)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("border-right: 2px solid rgba(255,255,255,0.18);")
        self._build()
 
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        logo = QLabel()
        logo.setFixedSize(48, 48)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: transparent; border-radius: 24px;")
        _logo_px = QPixmap(str(_ICON_DIR / "logo_kucing.png"))
        if not _logo_px.isNull():
            logo.setPixmap(_logo_px.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setText("🐱"); logo.setFont(QFont("Segoe UI", 22))
        if self.on_logo_click:
            logo.mousePressEvent = lambda e: self.on_logo_click() if e.button() == Qt.MouseButton.LeftButton else None
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(16)
        self._buttons = []
        nav_items = [("home.png","Home",0),("library.png","Library",1),("dashboard.png","Dashboard",5),("about.png","About",4)]
        for icon_file, tip, page_idx in nav_items:
            btn = QPushButton()
            btn.setObjectName("SidebarIcon"); btn.setToolTip(tip); btn.setCheckable(True); btn.setFixedSize(52, 52)
            px = QPixmap(str(_ICON_DIR / icon_file))
            if not px.isNull(): btn.setIcon(QIcon(px)); btn.setIconSize(QSize(26, 26))
            else: btn.setText(tip[:1])
            btn.setStyleSheet("""QPushButton { background: transparent; border: none; border-radius: 10px; } QPushButton:hover { background: rgba(255,255,255,0.20); } QPushButton:checked { background: rgba(255,255,255,0.30); }""")
            from PyQt6.QtWidgets import QGraphicsColorizeEffect
            effect = QGraphicsColorizeEffect(); effect.setColor(QColor(255, 255, 255)); btn.setGraphicsEffect(effect)
            btn.clicked.connect(lambda _, idx=page_idx: self._nav(idx))
            self._buttons.append((page_idx, btn))
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
 
        # ── Font Size Button ("Aa") ───────────────────────────────────────────
        self._font_popup = FontSizePopup()
        self._font_btn = QPushButton()
        self._font_btn.setObjectName("SidebarFont")
        self._font_btn.setToolTip("Ukuran Teks")
        self._font_btn.setCheckable(True)
        self._font_btn.setFixedSize(52, 52)
        px_font = QPixmap(str(_ICON_DIR / "font.png"))
        if not px_font.isNull():
            self._font_btn.setIcon(QIcon(px_font))
            self._font_btn.setIconSize(QSize(26, 26))
        else:
            self._font_btn.setText("Aa")
            self._font_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._font_btn.setStyleSheet("QPushButton { background: transparent; border: none; border-radius: 10px; color: white; } QPushButton:hover { background: rgba(255,255,255,0.20); } QPushButton:checked { background: rgba(255,255,255,0.30); }")
        self._font_btn.clicked.connect(self._toggle_font_popup)
        layout.addWidget(self._font_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ── Exit Button ───────────────────────────────────────────
        self._exit_btn = QPushButton()
        self._exit_btn.setObjectName("SidebarExit")
        self._exit_btn.setToolTip("Logout / Exit")
        self._exit_btn.setFixedSize(52, 52)
        px_exit = QPixmap(str(_ICON_DIR / "exit.png"))
        if not px_exit.isNull():
            self._exit_btn.setIcon(QIcon(px_exit))
            self._exit_btn.setIconSize(QSize(26, 26))
        else:
            self._exit_btn.setText("E")
            self._exit_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._exit_btn.setStyleSheet("QPushButton { background: transparent; border: none; border-radius: 10px; color: white; } QPushButton:hover { background: rgba(255,255,255,0.20); }")
        if self.on_logout:
            self._exit_btn.clicked.connect(self.on_logout)
        layout.addWidget(self._exit_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(8)
        self._set_active(0)
 
    def _nav(self, page_idx): self._set_active(page_idx); self.on_navigate(page_idx)
 
    def _set_active(self, page_idx):
        for idx, btn in self._buttons: btn.setChecked(idx == page_idx)
 
    def set_active(self, page_idx): self._set_active(page_idx)
 
    def _toggle_font_popup(self):
        if self._font_popup.isVisible():
            self._font_popup.hide()
            self._font_btn.setChecked(False)
        else:
            self._font_popup.show_near(self, self._font_btn)
            # Uncheck when popup closes
            self._font_popup.installEventFilter(self)
 
    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj is self._font_popup and event.type() == QEvent.Type.Hide:
            self._font_btn.setChecked(False)
        return super().eventFilter(obj, event)
 
 
class MainWindow(QMainWindow):
    def __init__(self, user=None, on_logout=None):
        super().__init__()
        self.current_user = user
        self.on_logout = on_logout
        self.setWindowTitle("MANGA:P")
        self.resize(1140, 680)
        self.setMinimumSize(900, 580)
        self.setStyleSheet(APP_STYLESHEET)
        # Initialize font size manager
        mgr = FontSizeManager.instance()
        mgr.set_base_stylesheet(APP_STYLESHEET)
        mgr.register_window(self)
        self._build()
 
    def _build(self):
        root = QWidget(); self.setCentralWidget(root)
        h = QHBoxLayout(root); h.setContentsMargins(0,0,0,0); h.setSpacing(0)
        self.sidebar = Sidebar(on_navigate=self._navigate, on_logo_click=self.go_profile, on_logout=self.on_logout)
        h.addWidget(self.sidebar)
        self.stack = QStackedWidget(); h.addWidget(self.stack)
        from .home_page import HomePage; from .library_page import LibraryPage
        from .search_page import SearchPage; from .detail_page import DetailPage
        from .about_page import AboutPage; from .dashboard_page import DashboardPage
        from .profile_page import ProfilePage
        self.home_page = HomePage(self); self.library_page = LibraryPage(self)
        self.search_page = SearchPage(self); self.detail_page = DetailPage(self)
        self.about_page = AboutPage(self); self.dashboard_page = DashboardPage(self)
        self.profile_page = ProfilePage(self)
        self.stack.addWidget(self.home_page); self.stack.addWidget(self.library_page)
        self.stack.addWidget(self.search_page); self.stack.addWidget(self.detail_page)
        self.stack.addWidget(self.about_page); self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.profile_page)
        self.stack.setCurrentIndex(0)
 
    def _navigate(self, idx):
        if idx == 1: self.library_page.refresh()
        if idx == 5: self.dashboard_page.refresh()
        if idx == 6: self.profile_page.refresh()
        self.stack.setCurrentIndex(idx)
        if idx in (0,1,5): self.sidebar.set_active(idx)
 
    def go_home(self): self._navigate(0)
    def go_library(self): self._navigate(1)
    def go_about(self): self._navigate(4)
    def go_dashboard(self): self._navigate(5)
 
    def go_profile(self):
        self._navigate(6)
 
    def go_search(self, query=""): self.search_page.set_query(query); self._navigate(2)
 
    def go_detail(self, manga_id: int):
        try:
            from services.manga_service import MangaService
            manga = MangaService().get_by_id(manga_id)
            if manga: self.home_page.history.load_manga(manga)
        except Exception as e: print(f"[MainWindow] History update error: {e}")
        self.detail_page.load_manga(manga_id); self._navigate(3)
 
    def show_toast(self, message: str, duration: int = 2500): Toast(self, message, duration)
