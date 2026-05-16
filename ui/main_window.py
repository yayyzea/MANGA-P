from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QIcon
from pathlib import Path

_ICON_DIR = Path(__file__).parent.parent / "assets"

from .theme import BLUE_PRIMARY, WHITE, SIDEBAR_WIDTH, APP_STYLESHEET


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


class Sidebar(QWidget):
    def __init__(self, on_navigate, on_logo_click=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.on_navigate = on_navigate
        self.on_logo_click = on_logo_click
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
        self._set_active(0)

    def _nav(self, page_idx): self._set_active(page_idx); self.on_navigate(page_idx)

    def _set_active(self, page_idx):
        for idx, btn in self._buttons: btn.setChecked(idx == page_idx)

    def set_active(self, page_idx): self._set_active(page_idx)


class MainWindow(QMainWindow):
    def __init__(self, user=None):
        super().__init__()
        self.current_user = user
        self.setWindowTitle("MANGA:P")
        self.resize(1140, 680)
        self.setMinimumSize(900, 580)
        self.setStyleSheet(APP_STYLESHEET)
        self._build()

    def _build(self):
        root = QWidget(); self.setCentralWidget(root)
        h = QHBoxLayout(root); h.setContentsMargins(0,0,0,0); h.setSpacing(0)
        self.sidebar = Sidebar(on_navigate=self._navigate, on_logo_click=self.go_profile)
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
        try:
            from services.user_service import UserService
            data = UserService().get_profile(self.current_user["id"])
            if data:
                self.profile_page.load_profile(name=data.name or "", email=data.email or "", bio=data.bio or "", avatar_path=data.avatar_path)
        except Exception as e: print(f"[go_profile] error: {e}")
        self.stack.setCurrentWidget(self.profile_page)

    def go_search(self, query=""): self.search_page.set_query(query); self._navigate(2)

    def go_detail(self, manga_id: int):
        try:
            from services.manga_service import MangaService
            manga = MangaService().get_by_id(manga_id)
            if manga: self.home_page.history.load_manga(manga)
        except Exception as e: print(f"[MainWindow] History update error: {e}")
        self.detail_page.load_manga(manga_id); self._navigate(3)

    def show_toast(self, message: str, duration: int = 2500): Toast(self, message, duration)
