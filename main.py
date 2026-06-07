import sys
from PyQt6.QtWidgets import QApplication
from database import init_db


def main():
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("MANGA:P")

    from ui.theme import APP_STYLESHEET
    from ui.font_size_manager import FontSizeManager, FONT_BASE_PX
    fsm = FontSizeManager.instance()
    fsm.set_base_stylesheet(APP_STYLESHEET)
    fsm.apply_px(FONT_BASE_PX)

    from PyQt6.QtGui import QFont
    font = QFont()
    font.setFamilies(["Helvetica", "Arial", "sans-serif"])
    app.setFont(font)

    main_win_ref = {}

    def on_logout():
        if "win" in main_win_ref:
            main_win_ref["win"].close()
            del main_win_ref["win"]
        show_auth()

    def on_auth_success(user):
        if "auth" in main_win_ref:
            main_win_ref["auth"].close()
            del main_win_ref["auth"]

        from ui.main_window import MainWindow
        main_win = MainWindow(user=user, on_logout=on_logout)
        main_win.showMaximized()
        main_win_ref["win"] = main_win

    def show_auth():
        from ui.auth_window import AuthWindow
        auth_win = AuthWindow(on_auth_success=on_auth_success)
        auth_win.showMaximized()
        main_win_ref["auth"] = auth_win

    show_auth()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()