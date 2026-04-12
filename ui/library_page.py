from .add_manga_form import AddMangaForm

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, TEXT_MUTED,
    CARD_W, CARD_H, CARD_RADIUS
)
from .widgets import MangaCard
from .home_page import SearchBar


# ── Background worker ─────────────────────────────────────────────────────────

class CollectionLoader(QThread):
    finished = pyqtSignal(list, list)   # last_read manga, my_books manga

    def run(self):
        try:
            from database import get_session
            from models.user_collection import UserCollection
            from sqlalchemy.orm import joinedload

            session = get_session()
            try:
                # ★ joinedload: fetch manga relationship WITHIN the session
                #   so accessing item.manga after session.close() won't crash
                entries = (
                    session.query(UserCollection)
                    .options(joinedload(UserCollection.manga))
                    .order_by(UserCollection.updated_at.desc())
                    .all()
                )

                # Last Read = entries with Reading or Completed status
                last_read_manga = [
                    e.manga for e in entries
                    if e.status in ("Reading", "Completed") and e.manga
                ][:12]

                # My Books = all entries
                my_books_manga = [e.manga for e in entries if e.manga]

            finally:
                session.close()

            self.finished.emit(last_read_manga, my_books_manga)

        except Exception as e:
            print(f"[LibraryPage] Load error: {e}")
            self.finished.emit([], [])


# ── Horizontal card row ───────────────────────────────────────────────────────

class CardRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFixedHeight(CARD_H + 40)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        self._row = QHBoxLayout(self._inner)
        self._row.setContentsMargins(0, 8, 0, 8)
        self._row.setSpacing(16)
        self._row.addStretch()

        self.scroll.setWidget(self._inner)
        root.addWidget(self.scroll)

    def show_placeholders(self, count=6):
        self._clear()
        for _ in range(count):
            ph = QWidget()
            ph.setFixedSize(CARD_W + 16, CARD_H)
            ph.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            ph.setStyleSheet(f"background: {BLUE_CARD}; border-radius: {CARD_RADIUS}px;")
            self._row.insertWidget(self._row.count() - 1, ph)

    def load_cards(self, manga_list, on_click):
        self._clear()
        if not manga_list:
            lbl = QLabel("No manga yet.")
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
            self._row.insertWidget(0, lbl)
            return
        for manga in manga_list:
            card = MangaCard(manga, show_labels=True)
            card.clicked.connect(on_click)
            self._row.insertWidget(self._row.count() - 1, card)

    def _clear(self):
        while self._row.count() > 1:
            item = self._row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ── Library page ──────────────────────────────────────────────────────────────

class LibraryPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._loader = None
        self._build()
        self._start_loading()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        top_row = QHBoxLayout()

        self.search_bar = SearchBar()
        self.search_bar.search_triggered.connect(
            lambda q: self.main_window.go_search(q) if q else None
        )
        self.search_bar.filter_triggered.connect(lambda: self.main_window.go_search(""))
        
        top_row.addWidget(self.search_bar)
        
        # tombol +
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(40, 40)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BLUE_PRIMARY};
                color: white;
                border-radius: 20px;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #1565C0;
            }}
        """)
        
        self.add_btn.clicked.connect(self._open_add_form)
        
        top_row.addWidget(self.add_btn)
        
        root.addLayout(top_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 20, 24, 20)
        bl.setSpacing(20)

        bl.addWidget(self._sec("Last Read"))
        self.last_read_row = CardRow()
        self.last_read_row.show_placeholders(6)
        bl.addWidget(self.last_read_row)

        bl.addWidget(self._sec("My Books"))
        self.my_books_row = CardRow()
        self.my_books_row.show_placeholders(6)
        bl.addWidget(self.my_books_row)

        bl.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

    def _sec(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {BLUE_PRIMARY}; font-size: 16px; "
            f"font-weight: 700; background: transparent;"
        )
        return lbl

    def _start_loading(self):
        if self._loader and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()
        self.last_read_row.show_placeholders(6)
        self.my_books_row.show_placeholders(6)
        self._loader = CollectionLoader()
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    @pyqtSlot(list, list)
    def _on_loaded(self, lr, mb):
        self.last_read_row.load_cards(lr, self.main_window.go_detail)
        self.my_books_row.load_cards(mb, self.main_window.go_detail)

    def refresh(self):
        self._start_loading()
        
    def _open_add_form(self):
        dialog = AddMangaForm(self)
    
        dialog.manga_added.connect(lambda _: self.refresh())
    
        dialog.exec()
