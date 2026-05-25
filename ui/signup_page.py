from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont, QPainter, QLinearGradient, QColor, QIcon
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
        # 水のドレス diagonal gradient background
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0,  QColor("#006ec4"))   # Sky Blue
        gradient.setColorAt(0.35, QColor("#2cb5d3"))   # Teal
        gradient.setColorAt(0.70, QColor("#9abe7c"))   # Dewy Green
        gradient.setColorAt(1.0,  QColor("#c4b5de"))   # Lilac Mist
        painter.fillRect(self.rect(), gradient)

    def _build(self):
        self.setStyleSheet("QWidget { background: transparent; }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root = QHBoxLayout()
        root.setContentsMargins(40, 0, 40, 0)
        root.setSpacing(40)
        outer.addLayout(root)

        # ── Left: cat image ──
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        left.setFixedHeight(380)
        left.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: transparent;")
        px = QPixmap(str(_ASSET_DIR / "logo_kucing.png"))
        if not px.isNull():
            logo.setPixmap(px.scaled(380, 400,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setText("🐱⭐")
            logo.setFont(QFont("Segoe UI", 72))
        left_layout.addWidget(logo)
        root.addWidget(left, stretch=1, alignment=Qt.AlignmentFlag.AlignRight)

        # ── Right: form ──
        right = QWidget()
        right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        right.setStyleSheet("background: transparent;")
        right.setMinimumWidth(340)
        right.setMaximumWidth(700)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        title = QLabel("Sign Up")
        title.setFont(QFont("Motley", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        rl.addWidget(title)
        rl.addSpacing(6)

        # Colorful accent line under title
        accent = QLabel()
        accent.setFixedHeight(3)
        accent.setMaximumWidth(140)
        accent.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        accent.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255,255,255,0.9), stop:1 rgba(255,255,255,0.2));
            border-radius: 2px;
        """)
        rl.addWidget(accent)
        rl.addSpacing(20)

        rl.addWidget(self._lbl("Enter Username"))
        rl.addSpacing(6)
        self.username_input = self._input()
        rl.addWidget(self.username_input)
        rl.addSpacing(14)

        rl.addWidget(self._lbl("Enter E-mail"))
        rl.addSpacing(6)
        self.email_input = self._input()
        rl.addWidget(self.email_input)
        rl.addSpacing(14)

        rl.addWidget(self._lbl("Enter Password"))
        rl.addSpacing(6)

        pass_container = QWidget()
        pass_container.setFixedHeight(48)
        pass_container.setMinimumWidth(300)
        pass_container.setStyleSheet("QWidget { background: white; border-radius: 24px; }")
        pass_row = QHBoxLayout(pass_container)
        pass_row.setContentsMargins(20, 0, 8, 0)
        pass_row.setSpacing(0)

        self.pass_input = QLineEdit()
        self.pass_input.setFixedHeight(48)
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setStyleSheet("QLineEdit { background: transparent; border: none; font-size: 14px; color: #1a1a1a; }")
        pass_row.addWidget(self.pass_input)

        self._eye_icon_show = QIcon(QPixmap(str(_ASSET_DIR / "view.png")))
        self._eye_icon_hide = QIcon(QPixmap(str(_ASSET_DIR / "hide.png")))

        self._eye_btn = QPushButton()
        self._eye_btn.setFixedSize(32, 32)
        self._eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._eye_btn.setStyleSheet("background: transparent; border: none;")
        self._eye_btn.setIcon(self._eye_icon_hide)
        self._eye_btn.setIconSize(QSize(22, 22))
        self._eye_btn.clicked.connect(self._toggle_password)
        pass_row.addWidget(self._eye_btn)

        rl.addWidget(pass_container)
        rl.addSpacing(8)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #fff3cd; background: transparent; font-size: 12px;")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setFixedHeight(20)
        rl.addWidget(self.error_lbl)
        rl.addSpacing(16)

        self.signup_btn = QPushButton("Sign Up")
        self.signup_btn.setFixedHeight(48)
        self.signup_btn.setFixedWidth(220)
        self.signup_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.signup_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: #006ec4;
                border: none;
                border-radius: 24px;
                font-weight: bold;
            }
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

        rl.addSpacing(12)
        back_row = QHBoxLayout()
        back_row.setSpacing(4)
        back_row.addStretch()
        have = QLabel("Already have an account?")
        have.setStyleSheet("color: rgba(255,255,255,0.85); background: transparent; font-size: 12px;")
        back_btn = QPushButton("Login")
        back_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: white;
                font-size: 12px; font-weight: bold; padding: 0; text-decoration: underline; }
            QPushButton:hover { color: #DCF0F7; }
        """)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self._go_login)
        back_row.addWidget(have)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        rl.addLayout(back_row)

        root.addWidget(right, stretch=1, alignment=Qt.AlignmentFlag.AlignLeft)
        self.pass_input.returnPressed.connect(self._do_register)

    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet("color: white; background: transparent; font-size: 13px; font-weight: 500;")
        return l

    def _input(self, password=False):
        w = QLineEdit()
        w.setFixedHeight(48)
        w.setMinimumWidth(300)
        if password:
            w.setEchoMode(QLineEdit.EchoMode.Password)
        w.setStyleSheet("""
            QLineEdit { background: white; border: none; border-radius: 24px;
                padding: 0 20px; font-size: 14px; color: #1a1a1a; }
            QLineEdit:focus { border: 2px solid rgba(249,106,103,0.5); }
        """)
        return w

    def _go_login(self):
        if self.on_switch_login:
            self.on_switch_login()

    def _toggle_password(self):
        if self.pass_input.echoMode() == QLineEdit.EchoMode.Password:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._eye_btn.setIcon(self._eye_icon_show)
        else:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._eye_btn.setIcon(self._eye_icon_hide)

    def _do_register(self):
        self.error_lbl.setText("")
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.pass_input.text()

        if not username or not email or not password:
            self.error_lbl.setText("⚠  All fields are required")
            return

        if "@" not in email or email.index("@") == 0 or email.index("@") == len(email) - 1:
            self.error_lbl.setText("⚠  Please enter a valid email address")
            return

        if len(password) < 6:
            self.error_lbl.setText("⚠  Password must be at least 6 characters")
            return

        self.signup_btn.setEnabled(False)
        self.signup_btn.setText("Signing up...")

        success, error = self._auth.register(username, email, password)

        self.signup_btn.setEnabled(True)
        self.signup_btn.setText("Sign Up")

        if error:
            self.error_lbl.setText(f"⚠  {error}")
            return

        if success and self.on_signup:
            self.on_signup(email)