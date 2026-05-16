from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont, QPainter, QLinearGradient, QColor, QIcon
from pathlib import Path
import json

from services.auth_service import AuthService

_ASSET_DIR   = Path(__file__).parent.parent / "assets"
_REMEMBER_FILE = Path(__file__).parent.parent / "remember_me.json"


# ── Remember Me helpers ──────────────────────────────────────────────────────

def _load_remember() -> dict:
    """
    Kembalikan dict berisi:
      last   : {"email": ..., "password_hash": ...}  ← akun terakhir login
      accounts: [{"username": ..., "email": ...}, ...]  ← semua akun yang pernah remember
    """
    if _REMEMBER_FILE.exists():
        try:
            return json.loads(_REMEMBER_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last": None, "accounts": []}


def _save_remember(email: str, username: str, password_plain: str):
    """Simpan akun terakhir login ke file JSON (password disimpan plaintext lokal)."""
    data = _load_remember()
    entry = {"username": username, "email": email, "password": password_plain}
    # Update last
    data["last"] = entry
    # Tambah/update ke daftar accounts (unik berdasarkan email)
    data["accounts"] = [a for a in data.get("accounts", []) if a["email"] != email]
    data["accounts"].insert(0, entry)
    _REMEMBER_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _clear_remember():
    """Hapus file remember me."""
    if _REMEMBER_FILE.exists():
        _REMEMBER_FILE.unlink()


class LoginPage(QWidget):
    def __init__(self, on_login=None, on_switch_signup=None, parent=None):
        super().__init__(parent)
        self.on_login = on_login
        self.on_switch_signup = on_switch_signup
        self._auth = AuthService()
        self._remember_data = _load_remember()
        self._build()
        self._apply_remember()   # auto-fill setelah UI selesai

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
        
        # Wrapper putih rounded yang berisi input + tombol mata
        pass_container = QWidget()
        pass_container.setFixedHeight(48)
        pass_container.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 24px;
            }
        """)
        pass_row = QHBoxLayout(pass_container)
        pass_row.setContentsMargins(20, 0, 8, 0)
        pass_row.setSpacing(0)

        self.pass_input = QLineEdit()
        self.pass_input.setFixedHeight(48)
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                font-size: 14px;
                color: #1a1a1a;
            }
        """)
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

        # Error/success label
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #FADBD8; background: transparent; font-size: 12px;")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setFixedHeight(20)
        rl.addWidget(self.error_lbl)
        rl.addSpacing(16)

        # ── Remember Me row ───────────────────────────────────────────────
        remember_row = QHBoxLayout()
        remember_row.setSpacing(8)
        remember_row.setContentsMargins(4, 0, 0, 0)

        self._remember_cb = QCheckBox("Remember me")
        self._remember_cb.setStyleSheet("""
            QCheckBox {
                color: rgba(255,255,255,0.92);
                background: transparent;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px; height: 18px;
                border: 2px solid rgba(255,255,255,0.70);
                border-radius: 4px;
                background: rgba(255,255,255,0.15);
            }
            QCheckBox::indicator:checked {
                background: white;
                border-color: white;
                image: url(none);
            }
        """)
        remember_row.addWidget(self._remember_cb)
        remember_row.addStretch()

        # Dropdown pilih akun lain (hanya tampil kalau ada ≥ 2 akun tersimpan)
        self._account_combo = QComboBox()
        self._account_combo.setFixedHeight(32)
        self._account_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255,255,255,0.20);
                color: white;
                border: 1.5px solid rgba(255,255,255,0.50);
                border-radius: 16px;
                padding: 2px 12px;
                font-size: 12px;
            }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background: #1565C0;
                color: white;
                selection-background-color: #1E90FF;
            }
        """)
        self._account_combo.currentIndexChanged.connect(self._on_account_selected)
        remember_row.addWidget(self._account_combo)

        rl.addLayout(remember_row)
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

    # ── Remember Me logic ─────────────────────────────────────────────────────

    def _apply_remember(self):
        """Isi form dari data remember me yang tersimpan."""
        data = self._remember_data
        accounts = data.get("accounts", [])

        # Populate dropdown akun
        self._account_combo.blockSignals(True)
        self._account_combo.clear()
        if len(accounts) >= 1:
            for acc in accounts:
                label = f"{acc['username']} ({acc['email']})"
                self._account_combo.addItem(label, acc)
        self._account_combo.blockSignals(False)

        # Sembunyikan dropdown kalau hanya 0-1 akun
        self._account_combo.setVisible(len(accounts) > 1)

        # Auto-fill dari last
        last = data.get("last")
        if last:
            self._remember_cb.setChecked(True)
            self.email_input.setText(last.get("email", ""))
            self.pass_input.setText(last.get("password", ""))

    def _on_account_selected(self, idx: int):
        """Saat user pilih akun lain dari dropdown."""
        acc = self._account_combo.itemData(idx)
        if acc:
            self.email_input.setText(acc.get("email", ""))
            self.pass_input.setText(acc.get("password", ""))

    def _go_signup(self):
        if self.on_switch_signup:
            self.on_switch_signup()

    def _toggle_password(self):
        if self.pass_input.echoMode() == QLineEdit.EchoMode.Password:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._eye_btn.setIcon(self._eye_icon_show)
        else:
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._eye_btn.setIcon(self._eye_icon_hide)

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

        # ── Simpan atau hapus Remember Me ──────────────────────────────────
        if self._remember_cb.isChecked():
            _save_remember(
                email=self.email_input.text().strip(),
                username=user["username"],
                password_plain=self.pass_input.text(),
            )
            self._remember_data = _load_remember()
        else:
            # Kalau user uncheck, hapus akun ini dari daftar tapi biarkan yang lain
            data = _load_remember()
            email_now = self.email_input.text().strip()
            data["accounts"] = [a for a in data.get("accounts", []) if a["email"] != email_now]
            if data["last"] and data["last"]["email"] == email_now:
                data["last"] = data["accounts"][0] if data["accounts"] else None
            _REMEMBER_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        if self.on_login:
            self.on_login(user)