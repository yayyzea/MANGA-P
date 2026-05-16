from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QScrollArea,
    QFileDialog, QSizePolicy, QFrame, QMessageBox,
    QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import (
    QPixmap, QPainter, QPainterPath, QColor, QPalette, QFont, QPen
)
from pathlib import Path

_ICON_DIR = Path(__file__).parent.parent / "assets"

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_DARK, BLUE_LIGHT, BLUE_FOOTER,
    WHITE, TEXT_DARK, TEXT_MUTED, FONT_FAMILY,
    TOPBAR_HEIGHT, CARD_RADIUS
)


class AvatarLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, size: int = 140, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._pixmap = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to change profile photo")

    def set_image(self, pixmap: QPixmap):
        if pixmap and not pixmap.isNull():
            self._pixmap = pixmap.scaled(self._size, self._size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(2, 2, self._size - 4, self._size - 4)
        p.setClipPath(path)
        if self._pixmap:
            p.drawPixmap(0, 0, self._pixmap)
        else:
            p.fillPath(path, QColor(BLUE_CARD))
            cat_px = QPixmap(str(_ICON_DIR / "logo_kucing.png"))
            if not cat_px.isNull():
                cat_px = cat_px.scaled(self._size, self._size,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation)
                x = (self._size - cat_px.width()) // 2
                y = (self._size - cat_px.height()) // 2
                p.drawPixmap(x, y, cat_px)
            else:
                p.setPen(QColor(WHITE))
                f = QFont(FONT_FAMILY, int(self._size * 0.4))
                f.setBold(True); p.setFont(f)
                p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "🐱")
        p.setClipping(False)
        pen = QPen(QColor(WHITE), 4)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(2, 2, self._size - 4, self._size - 4)
        p.end()

class ProfileTopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(TOPBAR_HEIGHT)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(BLUE_PRIMARY))
        self.setPalette(pal)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)
        title = QLabel("My Profile")
        title.setStyleSheet(f"color: {WHITE}; font-size: 18px; font-weight: 700; background: transparent; font-family: '{FONT_FAMILY}';")
        layout.addWidget(title); layout.addStretch()


class SwitchAccountDialog(QDialog):
    """Dialog switch account bergaya Instagram."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("Switch Account")
        self.setFixedWidth(380)
        self.setStyleSheet(f"""
            QDialog {{
                background: {BLUE_DARK};
                border-radius: 16px;
            }}
        """)
        self._build()

    def _build(self):
        from .login_page import _load_remember
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Account list ──
        body = QWidget()
        body.setStyleSheet(f"background: {BLUE_DARK};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 16, 16, 8)
        body_layout.setSpacing(8)

        data = _load_remember()
        accounts = data.get("accounts", [])
        current_email = self.main_window.current_user.get("email", "")

        if accounts:
            for acc in accounts:
                is_active = acc["email"] == current_email
                row = self._make_account_row(acc, is_active)
                body_layout.addWidget(row)
        else:
            empty = QLabel("No saved accounts.")
            empty.setStyleSheet(f"color: rgba(255,255,255,0.60); font-size: 13px; background: transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            body_layout.addWidget(empty)

        # ── Add account button ──
        body_layout.addSpacing(8)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: rgba(255,255,255,0.15); border: none; max-height: 1px;")
        body_layout.addWidget(sep)
        body_layout.addSpacing(8)

        add_btn = QPushButton("＋  Add Account")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setFixedHeight(42)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.10);
                color: {WHITE};
                border: 1.5px solid rgba(255,255,255,0.35);
                border-radius: 21px;
                font-size: 13px;
                font-weight: 600;
                font-family: '{FONT_FAMILY}';
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.20); }}
        """)
        add_btn.clicked.connect(self._on_add_account)
        body_layout.addWidget(add_btn)
        body_layout.addSpacing(8)

        layout.addWidget(body)

    def _make_account_row(self, acc: dict, is_active: bool) -> QWidget:
        row = QWidget()
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setFixedHeight(60)
        row.setStyleSheet(f"""
            QWidget {{
                background: {"rgba(255,255,255,0.15)" if is_active else "rgba(255,255,255,0.06)"};
                border-radius: 12px;
            }}
            QWidget:hover {{
                background: rgba(255,255,255,0.22);
            }}
        """)
        rl = QHBoxLayout(row)
        rl.setContentsMargins(12, 0, 12, 0)
        rl.setSpacing(12)

        # Avatar circle
        avatar = QLabel()
        avatar.setFixedSize(38, 38)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: {BLUE_PRIMARY};
            border-radius: 19px;
            color: {WHITE};
            font-size: 15px;
            font-weight: 700;
            font-family: '{FONT_FAMILY}';
        """)
        avatar.setText(acc.get("username", "?")[0].upper())
        rl.addWidget(avatar)

        # Username & email
        info = QVBoxLayout()
        info.setSpacing(2)
        uname = QLabel(acc.get("username", ""))
        uname.setStyleSheet(f"color: {WHITE}; font-size: 13px; font-weight: 700; background: transparent; font-family: '{FONT_FAMILY}';")
        email_lbl = QLabel(acc.get("email", ""))
        email_lbl.setStyleSheet(f"color: rgba(255,255,255,0.65); font-size: 11px; background: transparent; font-family: '{FONT_FAMILY}';")
        info.addWidget(uname)
        info.addWidget(email_lbl)
        rl.addLayout(info)
        rl.addStretch()

        # Active badge or switch button
        if is_active:
            badge = QLabel("Active")
            badge.setStyleSheet(f"""
                background: rgba(255,255,255,0.25);
                color: {WHITE};
                border-radius: 10px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: 600;
                font-family: '{FONT_FAMILY}';
            """)
            rl.addWidget(badge)
        else:
            switch_btn = QPushButton("Switch")
            switch_btn.setFixedHeight(28)
            switch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            switch_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {WHITE};
                    color: {BLUE_DARK};
                    border: none;
                    border-radius: 14px;
                    padding: 0 14px;
                    font-size: 11px;
                    font-weight: 700;
                    font-family: '{FONT_FAMILY}';
                }}
                QPushButton:hover {{ background: {BLUE_LIGHT}; }}
            """)
            switch_btn.clicked.connect(lambda _, a=acc: self._do_switch(a))
            rl.addWidget(switch_btn)

        return row

    def _do_switch(self, acc: dict):
        """Login ke akun lain dan reload MainWindow."""
        from services.auth_service import AuthService
        user = AuthService().login(acc["email"], acc["password"])
        if not user:
            self.main_window.show_toast("⚠ Failed to switch account, please log in again.")
            self.reject()
            return
        self.reject()
        self.main_window._switch_to_user(user)

    def _on_add_account(self):
        """Buka AuthWindow untuk login akun baru."""
        self.reject()
        self.main_window._logout()


class ProfilePage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._avatar_path = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(ProfileTopBar())
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setStyleSheet(f"background: {WHITE};")
        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)
        outer = QHBoxLayout(content)
        outer.setContentsMargins(40, 30, 40, 30)
        outer.addStretch()
        card = QFrame()
        card.setObjectName("ProfileCard")
        card.setFixedWidth(560)
        card.setStyleSheet(f"QFrame#ProfileCard {{ background: {BLUE_CARD}; border-radius: {CARD_RADIUS + 4}px; }}")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 32, 36, 32)
        card_layout.setSpacing(18)

        avatar_row = QHBoxLayout(); avatar_row.addStretch()
        self.avatar = AvatarLabel(140)
        self.avatar.clicked.connect(self._on_change_avatar)
        avatar_row.addWidget(self.avatar); avatar_row.addStretch()
        card_layout.addLayout(avatar_row)

        change_btn = QPushButton("Change Photo")
        change_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_btn.setStyleSheet(f"QPushButton {{ background: rgba(255,255,255,0.20); color: {WHITE}; border: 1px solid rgba(255,255,255,0.55); border-radius: 14px; padding: 6px 16px; font-size: 12px; font-weight: 600; font-family: '{FONT_FAMILY}'; }} QPushButton:hover {{ background: rgba(255,255,255,0.32); }}")
        change_btn.clicked.connect(self._on_change_avatar)
        change_row = QHBoxLayout(); change_row.addStretch(); change_row.addWidget(change_btn); change_row.addStretch()
        card_layout.addLayout(change_row)
        card_layout.addSpacing(8)

        self.name_input = self._make_field(card_layout, "Username", "Insert username here...")
        self.email_input = self._make_field(card_layout, "Email", "Insert email here...")
        self.pass_input = self._make_field(card_layout, "Password", "••••••••", is_password=True)

        bio_label = QLabel("Short Bio")
        bio_label.setStyleSheet(f"color: {WHITE}; font-size: 12px; font-weight: 700; background: transparent; font-family: '{FONT_FAMILY}';")
        card_layout.addWidget(bio_label)
        self.bio_input = QTextEdit()
        self.bio_input.setPlaceholderText("Tell us a little about yourself...")
        self.bio_input.setFixedHeight(90)
        self.bio_input.setStyleSheet(f"QTextEdit {{ background: {WHITE}; border: none; border-radius: 10px; padding: 10px 12px; font-size: 13px; color: {TEXT_DARK}; font-family: '{FONT_FAMILY}'; }}")
        card_layout.addWidget(self.bio_input)
        card_layout.addSpacing(10)

        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        cancel_btn = QPushButton("Back")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor); cancel_btn.setFixedHeight(38)
        cancel_btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {WHITE}; border: 1.5px solid {WHITE}; border-radius: 19px; padding: 0 22px; font-size: 13px; font-weight: 600; font-family: '{FONT_FAMILY}'; }} QPushButton:hover {{ background: rgba(255,255,255,0.15); }}")
        cancel_btn.clicked.connect(self.main_window.go_home)
        save_btn = QPushButton("Save Profile")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor); save_btn.setFixedHeight(38)
        save_btn.setStyleSheet(f"QPushButton {{ background: {WHITE}; color: {BLUE_DARK}; border: none; border-radius: 19px; padding: 0 22px; font-size: 13px; font-weight: 700; font-family: '{FONT_FAMILY}'; }} QPushButton:hover {{ background: {BLUE_FOOTER}; }}")
        save_btn.clicked.connect(self._on_save)
        btn_row.addStretch(); btn_row.addWidget(cancel_btn); btn_row.addWidget(save_btn)
        card_layout.addLayout(btn_row)

        # Switch Account button
        card_layout.addSpacing(8)
        switch_btn = QPushButton("🔄  Switch Account")
        switch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        switch_btn.setFixedHeight(40)
        switch_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.18);
                color: {WHITE};
                border: 1.5px solid rgba(255,255,255,0.55);
                border-radius: 20px;
                padding: 0 22px;
                font-size: 13px;
                font-weight: 700;
                font-family: '{FONT_FAMILY}';
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.30); }}
        """)
        switch_btn.clicked.connect(self._on_switch_account)
        switch_row = QHBoxLayout()
        switch_row.addStretch()
        switch_row.addWidget(switch_btn)
        switch_row.addStretch()
        card_layout.addLayout(switch_row)

        outer.addWidget(card); outer.addStretch()
        root.addWidget(self._build_footer())

    def _make_field(self, parent_layout, label_text, placeholder, is_password=False):
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {WHITE}; font-size: 12px; font-weight: 700; background: transparent; font-family: '{FONT_FAMILY}';")
        parent_layout.addWidget(label)
        field = QLineEdit()
        field.setPlaceholderText(placeholder); field.setFixedHeight(36)
        if is_password: field.setEchoMode(QLineEdit.EchoMode.Password)
        field.setStyleSheet(f"QLineEdit {{ background: {WHITE}; border: none; border-radius: 18px; padding: 0 14px; font-size: 13px; color: {TEXT_DARK}; font-family: '{FONT_FAMILY}'; }} QLineEdit:focus {{ border: 1.5px solid {BLUE_DARK}; }}")
        parent_layout.addWidget(field)
        return field

    def _build_footer(self):
        outer = QWidget()
        outer.setAutoFillBackground(True)
        pal = outer.palette(); pal.setColor(QPalette.ColorRole.Window, QColor(BLUE_FOOTER)); outer.setPalette(pal)
        v = QHBoxLayout(outer); v.setContentsMargins(16, 6, 16, 6); v.setSpacing(4)
        for label, cb in [("Home", self.main_window.go_home), ("About", self.main_window.go_about)]:
            btn = QPushButton(label)
            btn.setStyleSheet(f"QPushButton {{ background: transparent; border: none; color: {BLUE_PRIMARY}; font-size: 12px; text-decoration: underline; font-family: '{FONT_FAMILY}'; }} QPushButton:hover {{ color: #0D47A1; }}")
            btn.clicked.connect(cb); v.addWidget(btn)
            sep = QLabel("|"); sep.setStyleSheet(f"color: {BLUE_PRIMARY}; background: transparent; font-size: 12px;"); v.addWidget(sep)
        v.addStretch()
        return outer

    def _on_change_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Profile Photo", "", "Image (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            pix = QPixmap(path)
            if not pix.isNull(): self.avatar.set_image(pix); self._avatar_path = path

    def _on_save(self):
        name = self.name_input.text().strip(); email = self.email_input.text().strip()
        pwd = self.pass_input.text(); bio = self.bio_input.toPlainText().strip()
        if not name: self._toast("Username cannot be empty"); return
        if "@" not in email or "." not in email: self._toast("Invalid email"); return
        if pwd and len(pwd) < 6: self._toast("Password must be at least 6 characters"); return
        from services.user_service import UserService
        UserService().update_profile(user_id=self.main_window.current_user["id"], name=name, email=email, password=pwd if pwd else None, bio=bio, avatar_path=self._avatar_path)
        self._toast("Profile saved successfully ✓")

    def _on_switch_account(self):
        dialog = SwitchAccountDialog(self.main_window, parent=self)
        dialog.exec()

    def _toast(self, msg: str):
        if hasattr(self.main_window, "show_toast"): self.main_window.show_toast(msg)

    def load_profile(self, name="", email="", bio="", avatar_path=None):
        self.name_input.setText(name); self.email_input.setText(email)
        self.bio_input.setPlainText(bio)
        if avatar_path:
            pix = QPixmap(avatar_path)
            if not pix.isNull(): self.avatar.set_image(pix); self._avatar_path = avatar_path

    def refresh(self):
        try:
            from services.user_service import UserService
            data = UserService().get_profile(self.main_window.current_user["id"])
            if data:
                self.load_profile(
                    name=data.name or "",
                    email=data.email or "",
                    bio=data.bio or "",
                    avatar_path=data.avatar_path
                )
        except Exception as e:
            print(f"[ProfilePage] refresh error: {e}")