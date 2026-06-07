from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont, QPainter, QLinearGradient, QColor, QIcon
from pathlib import Path
import json, base64
from services.auth_service import AuthService
_ASSET_DIR     = Path(__file__).parent.parent / "assets"
_REMEMBER_FILE = Path(__file__).parent.parent / "remember_me.json"
# ── Simple reversible obfuscation (NOT encryption — just avoids plaintext) ──
# Password is obfuscated with base64 so it isn't stored as raw plaintext.
# This is intentional: the combo-account feature requires auto-filling the
# password field so users can switch accounts in one click.
def _obfuscate(text: str) -> str:
    return base64.b64encode(text.encode()).decode()
def _deobfuscate(text: str) -> str:
    try:
        return base64.b64decode(text.encode()).decode()
    except Exception:
        return text   # fallback for entries saved before this change
def _load_remember() -> dict:
    if _REMEMBER_FILE.exists():
        try:
            return json.loads(_REMEMBER_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last": None, "accounts": []}
def _save_remember(email: str, username: str, password_plain: str):
    """
    Save/update a remembered account.
    - Deduplicates by email (one entry per email).
    - Marks this account as 'last' (will be pre-filled on next open).
    - Password stored obfuscated (base64), not plaintext.
    """
    data  = _load_remember()
    entry = {
        "username": username,
        "email":    email,
        "password": _obfuscate(password_plain),
    }
    # Remove any existing entry for this email, then insert at front
    data["accounts"] = [a for a in data.get("accounts", []) if a.get("email") != email]
    data["accounts"].insert(0, entry)
    data["last"] = entry
    _REMEMBER_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
def _remove_remember(email: str):
    """
    Remove a specific account from remembered list.
    Updates 'last' to the next available account, or None.
    """
    data = _load_remember()
    data["accounts"] = [a for a in data.get("accounts", []) if a.get("email") != email]
    # If we removed the 'last' account, fall back to the next one
    last = data.get("last")
    if last and last.get("email") == email:
        data["last"] = data["accounts"][0] if data["accounts"] else None
    _REMEMBER_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
def _clear_last_remember():
    """Clear the 'last' pointer without removing the account list."""
    data = _load_remember()
    data["last"] = None
    _REMEMBER_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
class LoginPage(QWidget):
    def __init__(self, on_login=None, on_switch_signup=None, parent=None):
        super().__init__(parent)
        self.on_login         = on_login
        self.on_switch_signup = on_switch_signup
        self._auth            = AuthService()
        self._remember_data   = _load_remember()
        self._build()
        self._apply_remember()
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0,  QColor("#006ec4"))   # Sky Blue
        gradient.setColorAt(0.35, QColor("#2cb5d3"))   # Teal
        gradient.setColorAt(0.70, QColor("#9abe7c"))   # Dewy Green
        gradient.setColorAt(1.0,  QColor("#c4b5de"))   # Lilac Mist
        painter.fillRect(self.rect(), gradient)
    def show_success(self, message: str):
        self.error_lbl.setStyleSheet("color: #f0a8c8; background: transparent; font-size: 12px;")
        self.error_lbl.setText(message)
    def _build(self):
        self.setStyleSheet("QWidget { background: transparent; }")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root = QHBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(20)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addLayout(root)
        # ── KIRI: kucing ──────────────────────────────────────────────────
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        left.setFixedWidth(380)
        left.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: transparent;")
        px = QPixmap(str(_ASSET_DIR / "logo_kucing.png"))
        if not px.isNull():
            logo.setPixmap(px.scaled(
                380, 400,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        else:
            logo.setText("🐱⭐")
            logo.setFont(QFont("Segoe UI", 72))
        left_layout.addWidget(logo)
        root.addWidget(left)
        # ── KANAN: form ───────────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        right.setMinimumWidth(380)
        right.setMaximumWidth(520)
        right.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        title = QLabel("Welcome Back!")
        title.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        rl.addWidget(title)
        rl.addSpacing(6)
        row = QHBoxLayout()
        row.setSpacing(4)
        dont = QLabel("Don't have an account?")
        dont.setStyleSheet("color: rgba(255,255,255,0.90); background: transparent; font-size: 13px;")
        su_btn = QPushButton("Sign Up")
        su_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: white;
                font-size: 13px; font-weight: bold; padding: 0; text-decoration: underline; }
            QPushButton:hover { color: #c8b8e8; }
        """)
        su_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        su_btn.clicked.connect(self._go_signup)
        row.addWidget(dont)
        row.addWidget(su_btn)
        row.addStretch()
        rl.addLayout(row)
        rl.addSpacing(24)
        rl.addWidget(self._lbl("Enter E-mail / Username"))
        rl.addSpacing(6)
        self.email_input = self._input()
        rl.addWidget(self.email_input)
        rl.addSpacing(16)
        rl.addWidget(self._lbl("Enter Password"))
        rl.addSpacing(6)
        pass_container = QWidget()
        pass_container.setFixedHeight(48)
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
        self.error_lbl.setStyleSheet("color: #f4918e; background: transparent; font-size: 12px;")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setFixedHeight(20)
        rl.addWidget(self.error_lbl)
        rl.addSpacing(10)
        # ── Remember Me row ───────────────────────────────────────────────
        rem_row = QHBoxLayout()
        rem_row.setSpacing(10)
        rem_row.setContentsMargins(4, 0, 0, 0)
        self._remember_cb = QCheckBox("Remember me")
        asset_url = (_ASSET_DIR / "check.png").as_posix()
        self._remember_cb.setStyleSheet(f"""
            QCheckBox {{
                color: rgba(255,255,255,0.92);
                background: transparent;
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border: 2px solid rgba(255,255,255,0.70);
                border-radius: 4px;
                background: rgba(255,255,255,0.15);
            }}
            QCheckBox::indicator:checked {{
                background: white;
                border-color: white;
                image: url("{asset_url}");
            }}
        """)
        rem_row.addWidget(self._remember_cb)
        rem_row.addStretch()
        self._account_combo = QComboBox()
        self._account_combo.setFixedHeight(32)
        self._account_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._account_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255,255,255,0.20);
                color: white;
                border: 1.5px solid rgba(255,255,255,0.55);
                border-radius: 16px;
                padding: 2px 14px;
                font-size: 12px;
            }
            QComboBox::drop-down { border: none; width: 22px; }
            QComboBox QAbstractItemView {
                background: #6a5acd;
                color: white;
                selection-background-color: #a78fd4;
                border: none;
                border-radius: 8px;
            }
        """)
        self._account_combo.currentIndexChanged.connect(self._on_account_selected)
        rem_row.addWidget(self._account_combo)
        rl.addLayout(rem_row)
        rl.addSpacing(16)
        self.signin_btn = QPushButton("Sign In")
        self.signin_btn.setFixedHeight(48)
        self.signin_btn.setFixedWidth(220)
        self.signin_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.signin_btn.setStyleSheet("""
            QPushButton { background: #f0ecff; color: #5a4abf; border: none;
                border-radius: 24px; font-weight: bold; }
            QPushButton:hover   { background: #ddd5f5; }
            QPushButton:pressed { background: #c8b8e8; }
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
    def _apply_remember(self):
        """
        On startup:
        - Populate the account combo with all remembered accounts.
        - If a 'last' account exists (user had Remember Me checked last time),
          pre-fill the fields and check the checkbox.
        - If no 'last', leave fields empty — user must type credentials.
        """
        data     = self._remember_data
        accounts = data.get("accounts", [])
        self._account_combo.blockSignals(True)
        self._account_combo.clear()
        for acc in accounts:
            label = f"{acc['username']}  ({acc['email']})"
            self._account_combo.addItem(label, acc)
        self._account_combo.blockSignals(False)
        # Show combo only when there are remembered accounts
        self._account_combo.setVisible(len(accounts) > 0)
        last = data.get("last")
        if last:
            # User had Remember Me on — pre-fill and keep checkbox checked
            self._remember_cb.setChecked(True)
            self.email_input.setText(last.get("email", ""))
            self.pass_input.setText(_deobfuscate(last.get("password", "")))
            # Select matching account in combo
            for i in range(self._account_combo.count()):
                acc = self._account_combo.itemData(i)
                if acc and acc.get("email") == last.get("email"):
                    self._account_combo.blockSignals(True)
                    self._account_combo.setCurrentIndex(i)
                    self._account_combo.blockSignals(False)
                    break
        else:
            # No remembered session — start with empty fields
            self._remember_cb.setChecked(False)
            self.email_input.clear()
            self.pass_input.clear()
    def _on_account_selected(self, idx: int):
        acc = self._account_combo.itemData(idx)
        if acc:
            self.email_input.setText(acc.get("email", ""))
            self.pass_input.setText(_deobfuscate(acc.get("password", "")))
            self._remember_cb.setChecked(True)
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
            QLineEdit:focus { border: 2px solid #a78fd4; }
        """)
        return w
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
        self.error_lbl.setStyleSheet("color: #f4918e; background: transparent; font-size: 12px;")
        self.error_lbl.setText("")
        self.signin_btn.setEnabled(False)
        self.signin_btn.setText("Signing in...")
        email_or_user = self.email_input.text().strip()
        password      = self.pass_input.text()
        if not email_or_user or not password:
            self.error_lbl.setText("⚠ Please enter your username/email and password.")
            self.signin_btn.setEnabled(True)
            self.signin_btn.setText("Sign In")
            return
        user = self._auth.login(email_or_user, password
        self.signin_btn.setEnabled(True)
        self.signin_btn.setText("Sign In")
        if not user:
            self.error_lbl.setText("⚠ Invalid username/email or password!")
            self.pass_input.clear()
            return
        if self._remember_cb.isChecked():
            # Save/update this account in remembered list and mark as 'last'
            _save_remember(
                email          = user["email"],
                username       = user["username"],
                password_plain = password,
            )
            # Refresh combo in case a new account was added
            self._remember_data = _load_remember()
            self._apply_remember()
        else:
            # User does NOT want to be remembered:
            # Remove from saved list and clear 'last' pointer
            _remove_remember(user["email"])
            _clear_last_remember()
        if self.on_login:
            self.on_login(user)
