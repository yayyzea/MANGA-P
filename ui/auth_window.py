from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from PyQt6.QtCore import Qt
from .login_page import LoginPage
from .signup_page import SignUpPage


class AuthWindow(QMainWindow):
    """
    Window that hosts LoginPage and SignUpPage in a QStackedWidget.
    Switches between the two screens via 'Sign Up' / 'Sign In' links.

    After successful authentication, `on_auth_success(user)` is called
    so the caller can open MainWindow and close this window.
    """

    LOGIN_INDEX  = 0
    SIGNUP_INDEX = 1

    def __init__(self, on_auth_success=None):
        super().__init__()
        self.on_auth_success = on_auth_success
        self.setWindowTitle("MANGA:P")
        self.setMinimumSize(1100, 700)
        self._init_ui()

    def _init_ui(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_page = LoginPage(
            on_login=self._handle_login,
            on_switch_signup=self._show_signup,
        )
        self.signup_page = SignUpPage(
            on_signup=self._handle_signup,
            on_switch_login=self._show_login,
        )

        self.stack.addWidget(self.login_page)   # index 0
        self.stack.addWidget(self.signup_page)  # index 1
        self.stack.setCurrentIndex(self.LOGIN_INDEX)

    # ── navigation ──────────────────────────────────────────────────────────
    def _show_login(self):
        self.stack.setCurrentIndex(self.LOGIN_INDEX)

    def _show_signup(self):
        self.stack.setCurrentIndex(self.SIGNUP_INDEX)

    # ── auth handlers ────────────────────────────────────────────────────────
    def _handle_login(self, email_or_username: str, password: str):
        if not email_or_username or not password:
            self._show_error("Please fill in all fields.")
            return

        try:
            from services.auth_service import AuthService
            user = AuthService().login(email_or_username, password)
            if user:
                if self.on_auth_success:
                    self.on_auth_success(user)
            else:
                self._show_error("Invalid username/email or password.")
        except ImportError:
            # auth_service belum ada — fallback: langsung masuk
            if self.on_auth_success:
                self.on_auth_success({"username": email_or_username})
        except Exception as e:
            self._show_error(f"Login error: {e}")

    def _handle_signup(self, username: str, email: str, password: str):
        if not username or not email or not password:
            self._show_error("Please fill in all fields.")
            return

        if "@" not in email:
            self._show_error("Please enter a valid email address.")
            return

        if len(password) < 6:
            self._show_error("Password must be at least 6 characters.")
            return

        try:
            from services.auth_service import AuthService
            success, msg = AuthService().register(username, email, password)
            if success:
                self._show_info("Account created! Please sign in.")
                self._show_login()
            else:
                self._show_error(msg or "Registration failed.")
        except ImportError:
            # auth_service belum ada — fallback: langsung sukses
            self._show_info("Account created! Please sign in.")
            self._show_login()
        except Exception as e:
            self._show_error(f"Registration error: {e}")

    # ── helpers ──────────────────────────────────────────────────────────────
    def _show_error(self, message: str):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Error")
        msg.setText(message)
        msg.exec()

    def _show_info(self, message: str):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Info")
        msg.setText(message)
        msg.exec()