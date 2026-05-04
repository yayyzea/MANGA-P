from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from .login_page import LoginPage
from .signup_page import SignUpPage


class AuthWindow(QMainWindow):
    LOGIN_INDEX  = 0
    SIGNUP_INDEX = 1

    def __init__(self, on_auth_success=None):
        super().__init__()
        self.on_auth_success = on_auth_success
        self.setWindowTitle("MANGA:P")
        self.setMinimumSize(1000, 560)
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

    def _show_login(self):
        self.stack.setCurrentIndex(self.LOGIN_INDEX)

    def _show_signup(self):
        self.stack.setCurrentIndex(self.SIGNUP_INDEX)

    def _handle_login(self, user):
        if self.on_auth_success:
            self.on_auth_success(user)

    def _handle_signup(self, registered_email):
        # Setelah signup berhasil, balik ke login dan isi email
        self._show_login()
        self.login_page.email_input.setText(registered_email)
        self.login_page.show_success("✓ Akun berhasil dibuat! Silakan login.")