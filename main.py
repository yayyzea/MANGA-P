import sys
from PyQt6.QtWidgets import QApplication
from database import init_db
from ui.auth_window import AuthWindow


def _is_db_empty() -> bool:
    """Kembalikan True jika belum ada manga sama sekali di DB."""
    try:
        from database import get_session
        from models.manga import Manga
        session = get_session()
        try:
            return session.query(Manga).count() == 0
        finally:
            session.close()
    except Exception:
        return False


def main():
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("MANGA:P")

    # Set stylesheet di level QApplication lewat FontSizeManager
    # supaya perubahan font size bisa terpropagasi ke semua widget
    from ui.theme import APP_STYLESHEET
    from ui.font_size_manager import FontSizeManager, FONT_BASE_PX
    fsm = FontSizeManager.instance()
    fsm.set_base_stylesheet(APP_STYLESHEET)
    fsm.apply_px(FONT_BASE_PX)   # apply default px sekaligus set stylesheet ke QApplication

    from PyQt6.QtGui import QFont
    font = QFont()
    font.setFamilies(["Helvetica", "Arial", "sans-serif"])
    app.setFont(font)

    main_win_ref = {}   # mutable container to hold reference

    def on_logout():
        if "win" in main_win_ref:
            main_win_ref["win"].close()
            del main_win_ref["win"]
        show_auth()

    def on_auth_success(user):
        """Open MainWindow after login/signup, then close AuthWindow."""
        if "auth" in main_win_ref:
            main_win_ref["auth"].close()
            del main_win_ref["auth"]

        # ── First-time setup: scrape 500 manga jika DB masih kosong ──────────
        if _is_db_empty():
            from ui.initial_scrape_dialog import InitialScrapeDialog
            dlg = InitialScrapeDialog()
            dlg.show()
            dlg.start_scrape()
            dlg.exec()   # modal — blokir sampai scrape selesai
        # ─────────────────────────────────────────────────────────────────────

        from ui.main_window import MainWindow
        main_win = MainWindow(user=user, on_logout=on_logout)
        main_win.showMaximized()
        # Keep reference alive so it doesn't get garbage-collected
        main_win_ref["win"] = main_win

    def show_auth():
        auth_win = AuthWindow(on_auth_success=on_auth_success)
        auth_win.showMaximized()
        main_win_ref["auth"] = auth_win

    show_auth()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
