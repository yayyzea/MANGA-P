import sys
from PyQt6.QtWidgets import QApplication
from database import init_db
from ui.auth_window import AuthWindow


def main():
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("MANGA:P")

    main_win_ref = {}   # mutable container to hold reference

    def on_auth_success(user):
        """Open MainWindow after login/signup, then close AuthWindow."""
        auth_win.close()

        from ui.main_window import MainWindow
        main_win = MainWindow()
        main_win.show()
        # Keep reference alive so it doesn't get garbage-collected
        main_win_ref["win"] = main_win

    auth_win = AuthWindow(on_auth_success=on_auth_success)
    auth_win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()