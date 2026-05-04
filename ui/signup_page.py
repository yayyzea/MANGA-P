from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QPainter, QLinearGradient, QColor
from pathlib import Path

from services.auth_service import AuthService

_ASSET_DIR = Path(__file__).parent.parent / "assets"


class SignUpPage(QWidget):
    def __init__(self, on_signup=None, on_switch_login=None, parent=None):
        super().__init__(parent)
        self.on_signup = on_signup
        self.on_switch_login = on_switch_login
        self._auth = AuthService()
        self._build()

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor("#B3D9F5"))
        gradient.setColorAt(0.5, QColor("#3DA8E8"))
        gradient.setColorAt(1.0, QColor("#1E7BC4"))
        painter.fillRect(self.rect(), gradient)

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

        title = QLabel("Sign Up")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        rl.addWidget(title)
        rl.addSpacing(24)

        # Username
        rl.addWidget(self._lbl("Enter Username"))
        rl.addSpacing(6)
        self.username_input = self._input()
        rl.addWidget(self.username_input)
        rl.addSpacing(16)

        # Email
        rl.addWidget(self._lbl("Enter E-mail"))
        rl.addSpacing(6)
        self.email_input = self._input()
        rl.addWidget(self.email_input)
        rl.addSpacing(16)

        # Password
        rl.addWidget(self._lbl("Enter Password"))
        rl.addSpacing(6)
        self.pass_input = self._input(password=True)
        rl.addWidget(self.pass_input)
        rl.addSpacing(8)

        # Error label
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #FADBD8; background: transparent; font-size: 12px;")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setFixedHeight(20)
        rl.addWidget(self.error_lbl)
        rl.addSpacing(16)

        # Sign Up button
        self.signup_btn = QPushButton("Sign Up")
        self.signup_btn.setFixedHeight(48)
        self.signup_btn.setFixedWidth(220)
        self.signup_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.signup_btn.setStyleSheet("""
            QPushButton { background: white; color: #1E90FF; border: none;
                border-radius: 24px; font-weight: bold; }
            QPushButton:hover { background: #EBF5FB; }
            QPushButton:pressed { background: #D6EAF8; }
        """)
        self.signup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.signup_btn.clicked.connect(self._do_register)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self.signup_btn)
        btn_row.addStretch()
        rl.addLayout(btn_row)

        # Sudah punya akun?
        rl.addSpacing(12)
        back_row = QHBoxLayout()
        back_row.setSpacing(4)
        have = QLabel("Sudah punya akun?")
        have.setStyleSheet("color: rgba(255,255,255,0.85); background: transparent; font-size: 12px;")
        back_btn = QPushButton("Login")
        back_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: white;
                font-size: 12px; font-weight: bold; padding: 0; text-decoration: underline; }
            QPushButton:hover { color: #AED6F1; }
        """)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self._go_login)
        back_row.addWidget(have)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        rl.addLayout(back_row)

        root.addWidget(right)
        self.pass_input.returnPressed.connect(self._do_register)

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

    def _go_login(self):
        if self.on_switch_login:
            self.on_switch_login()

    def _do_register(self):
        self.error_lbl.setStyleSheet("color: #FADBD8; background: transparent; font-size: 12px;")
        self.error_lbl.setText("")
        self.signup_btn.setEnabled(False)
        self.signup_btn.setText("Mendaftar...")

        success, error = self._auth.register(
            self.username_input.text().strip(),
            self.email_input.text().strip(),
            self.pass_input.text()
        )

        self.signup_btn.setEnabled(True)
        self.signup_btn.setText("Sign Up")

        if error:
            self.error_lbl.setText(f"⚠  {error}")
            return

        registered_email = self.email_input.text().strip()
        if self.on_signup:
            self.on_signup(registered_email)