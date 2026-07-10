from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QGraphicsOpacityEffect,
    QFrame
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QPoint
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QIcon, QPainter
from pathlib import Path
 
_ICON_DIR = Path(__file__).parent.parent / "assets"
 
from .theme import BLUE_PRIMARY, WHITE, SIDEBAR_WIDTH, APP_STYLESHEET
from .font_size_manager import FontSizeManager, FONT_MIN_PX, FONT_MAX_PX, FONT_BASE_PX
 
 
class Toast(QLabel):
    def __init__(self, parent, message: str, duration: int = 2000):
        super().__init__(message, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "background: #0d2a40; color: white; border-radius: 10px;"
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FontSizePopup")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(200)
        self.setStyleSheet("""
            #FontSizePopup {
                background: #B8DCF0;
                border-radius: 16px;
                border: none;
            }
        """)



        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        title = QLabel("Text Size")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "color: rgba(0,60,120,0.70); font-size: 11px;"
            "font-weight: 600; letter-spacing: 1px; background: transparent;"
        )
        outer.addWidget(title)

        btn_style = """
            QPushButton {
                background: rgba(0,100,180,0.10);
                border: none; border-radius: 14px;
                color: #003c78; font-size: 20px; font-weight: 700;
            }
            QPushButton:hover   { background: rgba(0,100,180,0.20); }
            QPushButton:pressed { background: rgba(0,100,180,0.35); }
            QPushButton:disabled{
                background: rgba(0,100,180,0.05);
                color: rgba(0,100,180,0.25);
            }
        """
        self._btn_dec = QPushButton("−")
        self._btn_dec.setFixedSize(36, 36)
        self._btn_dec.setStyleSheet(btn_style)
        self._btn_dec.clicked.connect(self._decrease)

        self._px_lbl = QLabel("13 px")
        self._px_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._px_lbl.setStyleSheet(
            "color: rgba(0,60,120,0.85); font-size: 18px; font-weight: 700;"
            "background: transparent; min-width: 64px;"
        )

        self._btn_inc = QPushButton("+")
        self._btn_inc.setFixedSize(36, 36)
        self._btn_inc.setStyleSheet(btn_style)
        self._btn_inc.clicked.connect(self._increase)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        ctrl.addWidget(self._btn_dec)
        ctrl.addStretch()
        ctrl.addWidget(self._px_lbl)
        ctrl.addStretch()
        ctrl.addWidget(self._btn_inc)
        outer.addLayout(ctrl)

        bar_bg = QFrame()
        bar_bg.setFixedHeight(4)
        bar_bg.setStyleSheet(
            "background: rgba(0,100,180,0.18); border-radius: 2px;"
        )
        bar_layout = QHBoxLayout(bar_bg)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)

        self._bar_fill = QFrame()
        self._bar_fill.setFixedHeight(4)
        self._bar_fill.setStyleSheet(
            "background: rgba(0,100,180,0.70); border-radius: 2px;"
        )
        bar_layout.addWidget(self._bar_fill)
        bar_layout.addStretch()
        outer.addWidget(bar_bg)
        self._bar_bg = bar_bg

        hint_row = QHBoxLayout()
        hint_row.setContentsMargins(0, 0, 0, 0)
        lbl_min = QLabel(f"{FONT_MIN_PX}px")
        lbl_max = QLabel(f"{FONT_MAX_PX}px")
        for l in (lbl_min, lbl_max):
            l.setStyleSheet(
                "color: rgba(0,60,120,0.45); font-size: 10px; background: transparent;"
            )
        hint_row.addWidget(lbl_min)
        hint_row.addStretch()
        hint_row.addWidget(lbl_max)
        outer.addLayout(hint_row)

        self.adjustSize()
        self._refresh_ui()

    def _refresh_ui(self):
        mgr = FontSizeManager.instance()
        px  = mgr.px()
        self._px_lbl.setText(f"{px} px")
        self._btn_dec.setEnabled(mgr.can_decrease())
        self._btn_inc.setEnabled(mgr.can_increase())
        steps = FONT_MAX_PX - FONT_MIN_PX
        done  = px - FONT_MIN_PX
        total_w = self._bar_bg.width() or 168
        fill_w  = max(4, round(total_w * done / steps))
        self._bar_fill.setFixedWidth(fill_w)

    def _decrease(self):
        FontSizeManager.instance().decrease()
        self._refresh_ui()

    def _increase(self):
        FontSizeManager.instance().increase()
        self._refresh_ui()

    def show_near(self, sidebar_widget: QWidget, trigger_btn: QWidget):
        self._refresh_ui()
        global_pos = trigger_btn.mapToGlobal(QPoint(0, 0))
        x = global_pos.x() + sidebar_widget.width() + 8
        y = global_pos.y() + (trigger_btn.height() - self.sizeHint().height()) // 2
        self.move(x, y)
        self.show()
        self.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_ui()


class _AaButton(QWidget):
    from PyQt6.QtCore import pyqtSignal as _sig
    clicked = _sig()
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AaButton")
        self._checked = False
        self._hovered = False
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
        from .theme import BLUE_PRIMARY
        p.setBrush(QBrush(QC(BLUE_PRIMARY)))
        p.setPen(QPen(QC(0, 0, 0, 0)))
        p.drawRect(0, 0, w, h)
        if self._checked:
            p.setBrush(QBrush(QC(255, 255, 255, 76)))
            p.drawRoundedRect(4, 4, w - 8, h - 8, 10, 10)
        elif self._hovered:
            p.setBrush(QBrush(QC(255, 255, 255, 40)))
            p.drawRoundedRect(4, 4, w - 8, h - 8, 10, 10)
        fa = QFont("Segoe UI", 10, QFont.Weight.Bold)
        p.setFont(fa)
        p.setPen(QPen(QC(255, 255, 255, 200)))
        p.drawText(5, 0, w // 2 + 2, h, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, "a")
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
        self.setStyleSheet("border-right: 2px solid rgba(0,60,120,0.20);")
        self._build()
 
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._logo_lbl = QLabel()
        logo = self._logo_lbl
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
        layout.addWidget(self._logo_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
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
            effect = QGraphicsColorizeEffect(); effect.setColor(QColor(0, 60, 120)); btn.setGraphicsEffect(effect)
            btn.clicked.connect(lambda _, idx=page_idx: self._nav(idx))
            self._buttons.append((page_idx, btn))
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
 
        self._font_popup = FontSizePopup()
        self._font_btn = QPushButton()
        self._font_btn.setObjectName("SidebarFont")
        self._font_btn.setToolTip("Ukuran Teks")
        self._font_btn.setCheckable(True)
        self._font_btn.setFixedSize(52, 52)
        px_font = QPixmap(str(_ICON_DIR / "font.png"))
        if not px_font.isNull():
            _px_font_b = QPixmap(px_font.size()); _px_font_b.fill(Qt.GlobalColor.transparent)
            _pp = QPainter(_px_font_b); _pp.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source); _pp.drawPixmap(0,0,px_font); _pp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn); _pp.fillRect(_px_font_b.rect(), QColor(0,60,120)); _pp.end()
            self._font_btn.setIcon(QIcon(_px_font_b))
            self._font_btn.setIconSize(QSize(26, 26))
        else:
            self._font_btn.setText("Aa")
            self._font_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._font_btn.setStyleSheet("QPushButton { background: transparent; border: none; border-radius: 10px; color: #003c78; } QPushButton:hover { background: rgba(255,255,255,0.45); } QPushButton:checked { background: rgba(255,255,255,0.60); }")
        self._font_btn.clicked.connect(self._toggle_font_popup)
        layout.addWidget(self._font_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._exit_btn = QPushButton()
        self._exit_btn.setObjectName("SidebarExit")
        self._exit_btn.setToolTip("Logout / Exit")
        self._exit_btn.setFixedSize(52, 52)
        px_exit = QPixmap(str(_ICON_DIR / "exit.png"))
        if not px_exit.isNull():
            _px_exit_b = QPixmap(px_exit.size()); _px_exit_b.fill(Qt.GlobalColor.transparent)
            _pp2 = QPainter(_px_exit_b); _pp2.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source); _pp2.drawPixmap(0,0,px_exit); _pp2.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn); _pp2.fillRect(_px_exit_b.rect(), QColor(0,60,120)); _pp2.end()
            self._exit_btn.setIcon(QIcon(_px_exit_b))
            self._exit_btn.setIconSize(QSize(26, 26))
        else:
            self._exit_btn.setText("E")
            self._exit_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._exit_btn.setStyleSheet("QPushButton { background: transparent; border: none; border-radius: 10px; color: #003c78; } QPushButton:hover { background: rgba(255,255,255,0.45); }")
        if self.on_logout:
            self._exit_btn.clicked.connect(self.on_logout)
        layout.addWidget(self._exit_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(8)
        self._set_active(0)

    def update_logo(self, avatar_path: str):
        from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
        px = QPixmap(avatar_path)
        if not px.isNull():
            size = 40
            scaled = px.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            x = (scaled.width() - size) // 2
            y = (scaled.height() - size) // 2
            cropped = scaled.copy(x, y, size, size)
            rounded = QPixmap(size, size)
            rounded.fill(Qt.GlobalColor.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, cropped)
            painter.end()
            self._logo_lbl.setPixmap(rounded)
 
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
            from PyQt6.QtWidgets import QApplication
            QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtWidgets import QApplication
        if obj is self._font_popup and event.type() == QEvent.Type.Hide:
            self._font_btn.setChecked(False)
        # Auto-close popup ketika klik di luar
        if self._font_popup.isVisible() and event.type() == QEvent.Type.MouseButtonPress:
            from PyQt6.QtCore import QPoint
            gpos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
            if not self._font_popup.geometry().contains(gpos):
                self._font_popup.hide()
                self._font_btn.setChecked(False)
                QApplication.instance().removeEventFilter(self)
        return super().eventFilter(obj, event)
 
 
def _history_path():
    import os
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "..", "user_history.json")


def load_history(user_id: int) -> int | None:
    import json, os
    path = _history_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(str(user_id))
    except Exception as e:
        print(f"[History] load error: {e}")
        return None


def save_history(user_id: int, manga_id: int):
    import json, os
    path = _history_path()
    data = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[str(user_id)] = manga_id
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[History] save error: {e}")


class MainWindow(QMainWindow):
    def __init__(self, user=None, on_logout=None):
        super().__init__()
        self.current_user = user
        self.on_logout = on_logout
        self.setWindowTitle("MANGA:P")
        self.resize(1140, 680)
        self.setMinimumSize(900, 580)
        self.setStyleSheet(APP_STYLESHEET)
        mgr = FontSizeManager.instance()
        mgr.set_base_stylesheet(APP_STYLESHEET)
        mgr.register_window(self)
        self._build()

        try:
            from services.user_service import UserService
            profile = UserService().get_profile(self.current_user["id"])
            if profile and profile.avatar_path:
                self.update_sidebar_avatar(profile.avatar_path)
        except Exception as e:
            print("Avatar load error:", e)
 
    def _build(self):
        root = QWidget()
        root.setObjectName("CentralWidget")
        root.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCentralWidget(root)
        h = QHBoxLayout(root); h.setContentsMargins(0,0,0,0); h.setSpacing(0)
        self.sidebar = Sidebar(on_navigate=self._navigate, on_logo_click=self.go_profile, on_logout=self.on_logout)
        h.addWidget(self.sidebar)
        self.stack = QStackedWidget(); h.addWidget(self.stack)

        # ── Lazy page cache — page hanya dibuat saat pertama kali dibuka ──
        self._page_cache = {}

        # Hanya HomePage yang langsung dibuat (halaman pertama yang terlihat)
        from .home_page import HomePage
        self.home_page = HomePage(self)
        self._page_cache[0] = self.home_page
        self.stack.addWidget(self.home_page)  # index 0

        # Sisanya pakai placeholder kosong dulu — diganti saat navigate
        self._placeholder_indices = {
            1: "library_page",
            2: "search_page",
            3: "detail_page",
            4: "about_page",
            5: "dashboard_page",
            6: "profile_page",
            7: "genre_page",
            8: "status_page",
            9: "rating_page",
            10: "author_page",
            11: "genre_list_page",
            12: "scraped_genre_page",
        }
        for idx in range(1, 13):
            self.stack.addWidget(QWidget())

        self.stack.setCurrentIndex(0)

        # ── Splash screen overlay ──
        from .splash_screen import SplashScreen
        self._splash = SplashScreen(root)
        self._splash.resize(root.size())
        self._splash.show()
        self._splash.raise_()

        # Restore history di background setelah UI tampil
        if self.current_user:
            last_id = load_history(self.current_user["id"])
            if last_id:
                QTimer.singleShot(800, lambda: self._restore_history(last_id))

    def _restore_history(self, last_id: int):
        """Load history manga di background thread agar tidak freeze UI."""
        from PyQt6.QtCore import QThread
        from PyQt6.QtCore import pyqtSignal as _sig

        class _HistoryLoader(QThread):
            done = _sig(object)
            def __init__(self, mid): super().__init__(); self._mid = mid
            def run(self):
                try:
                    from services.manga_service import MangaService
                    manga = MangaService().get_by_id(self._mid)
                    self.done.emit(manga)
                except Exception as e:
                    print(f"[MainWindow] Restore history error: {e}")
                    self.done.emit(None)

        self._hist_loader = _HistoryLoader(last_id)
        self._hist_loader.done.connect(
            lambda m: self.home_page.history.load_manga(m) if m else None
        )
        self._hist_loader.start()

    def _get_or_create_page(self, idx: int):
        """Buat page jika belum ada, kembalikan widget-nya."""
        if idx in self._page_cache:
            return self._page_cache[idx]

        name = self._placeholder_indices.get(idx)
        if not name:
            return None

        page = None
        if name == "library_page":
            from .library_page import LibraryPage; page = LibraryPage(self)
        elif name == "search_page":
            from .search_page import SearchPage; page = SearchPage(self)
        elif name == "detail_page":
            from .detail_page import DetailPage; page = DetailPage(self)
        elif name == "about_page":
            from .about_page import AboutPage; page = AboutPage(self)
        elif name == "dashboard_page":
            from .dashboard_page import DashboardPage; page = DashboardPage(self)
        elif name == "profile_page":
            from .profile_page import ProfilePage; page = ProfilePage(self)
        elif name == "genre_page":
            from .genre_page import GenrePage; page = GenrePage(self)
        elif name == "status_page":
            from .status_page import StatusPage; page = StatusPage(self)
        elif name == "rating_page":
            from .rating_page import RatingPage; page = RatingPage(self)
        elif name == "author_page":
            from .author_page import AuthorPage; page = AuthorPage(self)
        elif name == "genre_list_page":
            from .genre_list_page import GenreListPage; page = GenreListPage(self)
        elif name == "scraped_genre_page":
            from .genre_list_page import ScrapedGenrePage; page = ScrapedGenrePage(self)

        if page:
            old = self.stack.widget(idx)
            self.stack.removeWidget(old)
            old.deleteLater()
            self.stack.insertWidget(idx, page)
            self._page_cache[idx] = page
            setattr(self, name, page)

        return page
 
    def showEvent(self, event):
        super().showEvent(event)

        from PyQt6.QtCore import QTimer

        QTimer.singleShot(300, self.home_page._relayout)

    def _navigate(self, idx):
        # Inisialisasi page secara lazy saat pertama kali dibuka
        page = self._get_or_create_page(idx)
        if idx == 1 and page and hasattr(page, 'refresh'): page.refresh()
        if idx == 5 and page and hasattr(page, 'refresh'): page.refresh()
        if idx == 6 and page and hasattr(page, 'refresh'): page.refresh()
        self.stack.setCurrentIndex(idx)
        if idx in (0, 1, 5): self.sidebar.set_active(idx)

    def dismiss_splash(self):
        """Dipanggil oleh HomePage setelah data pertama kali selesai dimuat."""
        if hasattr(self, '_splash') and self._splash:
            self._splash.dismiss()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_splash') and self._splash and self._splash.isVisible():
            cw = self.centralWidget()
            if cw:
                self._splash.resize(cw.size())

    def go_home(self): self._navigate(0)
    def go_library(self): self._navigate(1)
    def go_about(self): self._navigate(4)
    def go_dashboard(self): self._navigate(5)
    def go_profile(self): self._navigate(6)

    def go_search(self, query=""):
        page = self._get_or_create_page(2)
        if page: page.set_query(query)
        self._navigate(2)

    def go_detail(self, manga_id: int):
        # Simpan index halaman sebelumnya untuk tombol Back
        self._prev_index = self.stack.currentIndex()
        # Simpan history dulu (hanya baca DB, cepat)
        if self.current_user:
            save_history(self.current_user["id"], manga_id)
        page = self._get_or_create_page(3)
        if page: page.load_manga(manga_id)
        self._navigate(3)

    def go_back(self):
        """Kembali ke halaman sebelumnya sebelum go_detail dipanggil."""
        prev = getattr(self, "_prev_index", 0)
        self._navigate(prev)

    def go_genre(self, genre: str):
        page = self._get_or_create_page(7)
        if page: page.load_genre(genre)
        self.stack.setCurrentIndex(7)

    def go_status(self, status: str):
        page = self._get_or_create_page(8)
        if page: page.load_status(status)
        self.stack.setCurrentIndex(8)

    def go_rating(self, rating: int):
        page = self._get_or_create_page(9)
        if page: page.load_rating(rating)
        self.stack.setCurrentIndex(9)

    def go_author(self, author: str):
        page = self._get_or_create_page(10)
        if page: page.load_author(author)
        self.stack.setCurrentIndex(10)

    def go_genre_list(self, genre_counts: dict, top_genre: str = None):
        page = self._get_or_create_page(11)
        if page: page.load_data(genre_counts, top_genre)
        self.stack.setCurrentIndex(11)

    def go_scraped_genre(self, genre: str):
        page = self._get_or_create_page(12)
        if page: page.load_genre(genre)
        self.stack.setCurrentIndex(12)

    def show_toast(self, message: str, duration: int = 2500): Toast(self, message, duration)

    def update_sidebar_avatar(self, avatar_path: str):
        self.sidebar.update_logo(avatar_path)

    def _switch_to_user(self, user: dict):
        """Reload seluruh halaman untuk user baru setelah switch account."""
        self.current_user = user

        # Hanya refresh page yang sudah pernah dibuat (lazy)
        for idx, page in self._page_cache.items():
            if hasattr(page, 'refresh'):
                page.refresh()

        # Load avatar sidebar user baru kalau ada
        try:
            from services.user_service import UserService
            profile = UserService().get_profile(user["id"])
            if profile and profile.avatar_path:
                self.update_sidebar_avatar(profile.avatar_path)
            else:
                # Reset ke logo default
                from PyQt6.QtGui import QPixmap
                _logo_px = QPixmap(str(_ICON_DIR / "logo_kucing.png"))
                if not _logo_px.isNull():
                    self.sidebar._logo_lbl.setPixmap(
                        _logo_px.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
                    )
        except Exception as e:
            print(f"[Switch] avatar load error: {e}")

        self.go_home()
        self.show_toast(f"✓ Switched to {user.get('username', 'account')}")