from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QPainter, QLinearGradient, QColor
from pathlib import Path

from services.auth_service import AuthService

_ASSET_DIR = Path(__file__).parent.parent / "assets"


class LoginPage(QWidget):
    def __init__(self, on_login=None, on_switch_signup=None, parent=None):
        super().__init__(parent)
        self.on_login = on_login
        self.on_switch_signup = on_switch_signup
        self._auth = AuthService()
        self._build()

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor("#B3D9F5"))
        gradient.setColorAt(0.5, QColor("#3DA8E8"))
        gradient.setColorAt(1.0, QColor("#1E7BC4"))
        painter.fillRect(self.rect(), gradient)

    def show_success(self, message: str):
        self.error_lbl.setStyleSheet("color: #A9DFBF; background: transparent; font-size: 12px;")
        self.error_lbl.setText(message)

    def _build(self):
        self.setStyleSheet("QWidget { background: transparent; }")

        root = QHBoxLayout(self)
        root.setContentsMargins(60, 40, 80, 40)
        root.setSpacing(0)

        # ── KIRI: kucing ──────────────────────────────────────────────────
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: transparent;")
        px = QPixmap(str(_ASSET_DIR / "logo_kucing.png"))
        if not px.isNull():
            logo.setPixmap(px.scaled(300, 320,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setText("🐱⭐")
            logo.setFont(QFont("Segoe UI", 72))
        left_layout.addWidget(logo)
        root.addWidget(left, stretch=1)

        # ── KANAN: form ───────────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        right.setFixedWidth(440)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        rl.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("Welcome Back!")
        title.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        rl.addWidget(title)
        rl.addSpacing(6)

        # Don't have an account?
        row = QHBoxLayout()
        row.setSpacing(4)
        dont = QLabel("Don't have an account?")
        dont.setStyleSheet("color: rgba(255,255,255,0.90); background: transparent; font-size: 13px;")
        su_btn = QPushButton("Sign Up")
        su_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: white;
                font-size: 13px; font-weight: bold; padding: 0; text-decoration: underline; }
            QPushButton:hover { color: #D6EAF8; }
        """)
        su_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        su_btn.clicked.connect(self._go_signup)
        row.addWidget(dont)
        row.addWidget(su_btn)
        row.addStretch()
        rl.addLayout(row)
        rl.addSpacing(24)

        # Email field
        rl.addWidget(self._lbl("Enter E-mail / Username"))
        rl.addSpacing(6)
        self.email_input = self._input()
        rl.addWidget(self.email_input)
        rl.addSpacing(16)

        # Password field
        rl.addWidget(self._lbl("Enter Password"))
        rl.addSpacing(6)
        self.pass_input = self._input(password=True)
        rl.addWidget(self.pass_input)
        rl.addSpacing(8)

        # Error/success label
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #FADBD8; background: transparent; font-size: 12px;")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setFixedHeight(20)
        rl.addWidget(self.error_lbl)
        rl.addSpacing(16)

        # Sign In button
        self.signin_btn = QPushButton("Sign In")
        self.signin_btn.setFixedHeight(48)
        self.signin_btn.setFixedWidth(220)
        self.signin_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.signin_btn.setStyleSheet("""
            QPushButton { background: white; color: #1E90FF; border: none;
                border-radius: 24px; font-weight: bold; }
            QPushButton:hover { background: #EBF5FB; }
            QPushButton:pressed { background: #D6EAF8; }
        """)
        self.signin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.signin_btn.clicked.connect(self._do_login)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self.signin_btn)
        btn_row.addStretch()
        rl.addLayout(btn_row)

        root.addWidget(right)

        self.email_input.returnPressed.connect(self._do_login)
        self.pass_input.returnPressed.connect(self._do_login)

    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet("color: white; background: transparent; font-size: 13px; font-weight: 500;")
        return l

    def _input(self, password=False):
        w = QLineEdit()
        w.setFixedHeight(48)
        if password:
            w.setEchoMode(QLineEdit.EchoMode.Password)
        w.setStyleSheet("""
            QLineEdit { background: white; border: none; border-radius: 24px;
                padding: 0 20px; font-size: 14px; color: #1a1a1a; }
            QLineEdit:focus { border: 2px solid #AED6F1; }
        """)
        return w

    def _go_signup(self):
        if self.on_switch_signup:
            self.on_switch_signup()

    def _do_login(self):
        self.error_lbl.setStyleSheet("color: #FADBD8; background: transparent; font-size: 12px;")
        self.error_lbl.setText("")
        self.signin_btn.setEnabled(False)
        self.signin_btn.setText("Masuk...")

        user = self._auth.login(
            self.email_input.text().strip(),
            self.pass_input.text()
        )

        self.signin_btn.setEnabled(True)
        self.signin_btn.setText("Sign In")

        if not user:
            self.error_lbl.setText("⚠  Username/email atau password salah.")
            self.pass_input.clear()
            return

        if self.on_login:
            self.on_login(user)