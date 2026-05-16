from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QTextEdit, QSpinBox,
    QComboBox, QFrame, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_DARK, BLUE_LIGHT,
    WHITE, TEXT_MUTED,
    TOPBAR_HEIGHT, CARD_W, CARD_H, CARD_RADIUS
)
from .widgets import ImageLoader


class DetailLoader(QThread):
    finished = pyqtSignal(object, object, object, list)

    def __init__(self, manga_id: int, user_id: int):
        super().__init__()
        self.manga_id = manga_id
        self.user_id = user_id

    def run(self):
        try:
            from services.manga_service import MangaService
            from services.collection_service import CollectionService
            from services.review_service import ReviewService

            svc = MangaService()
            manga = svc.get_by_id(self.manga_id)
            collection = CollectionService().get_by_manga_id(self.manga_id, user_id=self.user_id)
            review = ReviewService().get_by_manga(self.manga_id, user_id=self.user_id)

            similar = []
            if manga:
                try:
                    similar = svc.get_recommendations(manga, limit=4)
                except Exception:
                    similar = []

            self.finished.emit(manga, collection, review, similar)
        except Exception as e:
            print(f"[DetailPage] Load error: {e}")
            self.finished.emit(None, None, None, [])


class CoverLabel(QLabel):
    def __init__(self, w: int, h: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(w, h)
        self._w, self._h = w, h
        self.setStyleSheet("background: rgba(255,255,255,0.18); border-radius: 10px;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_cover(self, pixmap: QPixmap):
        scaled = pixmap.scaled(self._w, self._h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation)
        x = (scaled.width() - self._w) // 2
        y = (scaled.height() - self._h) // 2
        self.setPixmap(scaled.copy(x, y, self._w, self._h))


class CollectionPanel(QWidget):
    changed = pyqtSignal()
    STATUS_OPTIONS = ["Plan to Read", "Reading", "Completed", "Dropped"]

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._manga_id = self._col_id = None
        self._manga_chapters = 0   # maks chapter manga yang sedang ditampilkan
        self._main_window = main_window
        self._build()

    def _toast(self, msg: str):
        if self._main_window:
            self._main_window.show_toast(msg)

    def _build(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

        self._add_btn = QPushButton("＋  Add to Collection")
        self._add_btn.setFixedHeight(36)
        self._add_btn.setStyleSheet(f"""
            QPushButton {{ background: {WHITE}; color: {BLUE_PRIMARY};
                border: none; border-radius: 8px; font-size: 12px; font-weight: 700; padding: 0 14px; }}
            QPushButton:hover {{ background: {BLUE_LIGHT}; }} """)
        self._add_btn.clicked.connect(self._on_add)
        self._layout.addWidget(self._add_btn)

        self._in_col = QWidget()
        self._in_col.setStyleSheet("background: transparent;")
        ic = QVBoxLayout(self._in_col)
        ic.setContentsMargins(0, 0, 0, 0)
        ic.setSpacing(4)

        r1 = QHBoxLayout()
        lbl1 = QLabel("Status:")
        lbl1.setStyleSheet(f"color: {WHITE}; font-size: 11px; background: transparent;")
        self._status_cb = QComboBox()
        self._status_cb.addItems(self.STATUS_OPTIONS)
        self._status_cb.setFixedWidth(140)
        self._status_cb.setStyleSheet(f"""
            QComboBox {{ background: rgba(255,255,255,0.25); color: {WHITE};
                border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; padding: 2px 8px; font-size: 11px; }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{ background: {BLUE_DARK}; color: {WHITE}; selection-background-color: {BLUE_PRIMARY}; }} """)
        r1.addWidget(lbl1); r1.addWidget(self._status_cb); r1.addStretch()
        self._status_cb.currentIndexChanged.connect(self._on_status_changed)
        ic.addLayout(r1)

        r2 = QHBoxLayout()
        lbl2 = QLabel("Chapter:")
        lbl2.setStyleSheet(f"color: {WHITE}; font-size: 11px; background: transparent;")
        self._ch_spin = QSpinBox()
        self._ch_spin.setRange(0, 9999)
        self._ch_spin.setFixedWidth(80)
        self._ch_spin.setStyleSheet(f"""
            QSpinBox {{ background: rgba(255,255,255,0.25); color: {WHITE};
                border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; padding: 2px 6px; font-size: 11px; }}
            QSpinBox::up-button, QSpinBox::down-button {{ background: rgba(255,255,255,0.15); border: none; width: 16px; }} """)
        r2.addWidget(lbl2); r2.addWidget(self._ch_spin); r2.addStretch()
        self._ch_spin.valueChanged.connect(self._on_chapter_changed)
        ic.addLayout(r2)

        r3 = QHBoxLayout(); r3.setSpacing(8)
        self._save_btn = QPushButton("Save")
        self._save_btn.setFixedHeight(30)
        self._save_btn.setStyleSheet(f"""
            QPushButton {{ background: {WHITE}; color: {BLUE_PRIMARY};
                border: none; border-radius: 7px; font-size: 11px; font-weight: 700; padding: 0 12px; }}
            QPushButton:hover {{ background: {BLUE_LIGHT}; }} """)
        self._save_btn.clicked.connect(self._on_save)

        self._remove_btn = QPushButton("Remove")
        self._remove_btn.setFixedHeight(30)
        self._remove_btn.setStyleSheet(f"""
            QPushButton {{ background: rgba(220,50,50,0.80); color: {WHITE};
                border: none; border-radius: 7px; font-size: 11px; font-weight: 700; padding: 0 12px; }} """)
        self._remove_btn.clicked.connect(self._on_remove)

        r3.addWidget(self._save_btn); r3.addWidget(self._remove_btn); r3.addStretch()
        ic.addLayout(r3)
        self._in_col.hide()
        self._layout.addWidget(self._in_col)

    def load(self, manga_id, entry, manga_chapters: int = 0):
        self._manga_id = manga_id
        self._manga_chapters = manga_chapters or 0
        if entry:
            self._col_id = entry.id
            # Set status dulu (tanpa trigger validasi chapter dua kali)
            self._status_cb.blockSignals(True)
            self._status_cb.setCurrentText(entry.status or "Plan to Read")
            self._status_cb.blockSignals(False)
            # Terapkan aturan chapter sesuai status
            self._apply_chapter_rules(entry.current_chapter or 0)
            self._add_btn.hide(); self._in_col.show()
        else:
            self._col_id = None
            self._add_btn.show(); self._in_col.hide()

    def _on_chapter_changed(self, value: int):
        """Jika chapter mencapai maks, otomatis ubah status ke Completed."""
        if self._manga_chapters and self._manga_chapters > 0 and value == self._manga_chapters:
            if self._status_cb.currentText() != "Completed":
                self._status_cb.setCurrentText("Completed")
                # _apply_chapter_rules sudah dipanggil via currentIndexChanged

    def _on_status_changed(self):
        self._apply_chapter_rules()

    def _on_chapter_changed(self, value: int):
        """Jika chapter mencapai maks, otomatis ubah status menjadi Completed."""
        if not self._manga_chapters or self._manga_chapters <= 0:
            return
        if value >= self._manga_chapters:
            # Blok sinyal status agar tidak memicu _apply_chapter_rules dua kali
            self._status_cb.blockSignals(True)
            self._status_cb.setCurrentText("Completed")
            self._status_cb.blockSignals(False)
            self._apply_chapter_rules()

    def _apply_chapter_rules(self, current_chapter: int = None):
        """
        Atur range dan nilai _ch_spin berdasarkan status aktif dan maks chapter manga.

        - Plan to Read  : chapter dikunci ke 0, spinbox dinonaktifkan
        - Reading       : chapter 1 – maks_chapter (atau 9999 jika maks tidak diketahui)
        - Completed     : chapter otomatis = maks_chapter, spinbox dinonaktifkan
        - Dropped       : chapter 1 – (maks_chapter - 1); jika maks ≤ 1 dikunci ke 0
        """
        status = self._status_cb.currentText()
        mx = self._manga_chapters  # 0 berarti tidak diketahui

        if status == "Plan to Read":
            self._ch_spin.setRange(0, 0)
            self._ch_spin.setValue(0)
            self._ch_spin.setEnabled(False)

        elif status == "Reading":
            hi = mx if mx and mx > 0 else 9999
            self._ch_spin.setRange(1, hi)
            self._ch_spin.setEnabled(True)
            if current_chapter is not None:
                self._ch_spin.setValue(max(1, min(current_chapter, hi)))
            elif self._ch_spin.value() < 1:
                self._ch_spin.setValue(1)

        elif status == "Completed":
            val = mx if mx and mx > 0 else (self._ch_spin.value() or 0)
            self._ch_spin.setRange(val, val)
            self._ch_spin.setValue(val)
            self._ch_spin.setEnabled(False)

        elif status == "Dropped":
            if mx and mx > 1:
                hi = mx - 1
                self._ch_spin.setRange(1, hi)
                self._ch_spin.setEnabled(True)
                if current_chapter is not None:
                    self._ch_spin.setValue(max(1, min(current_chapter, hi)))
                elif self._ch_spin.value() < 1:
                    self._ch_spin.setValue(1)
            else:
                # Maks tidak diketahui atau ≤ 1 — izinkan input bebas mulai 1
                self._ch_spin.setRange(1, 9999)
                self._ch_spin.setEnabled(True)
                if current_chapter is not None:
                    self._ch_spin.setValue(max(1, current_chapter))
                elif self._ch_spin.value() < 1:
                    self._ch_spin.setValue(1)

    def _on_add(self):
        if not self._manga_id: return
        try:
            from services.collection_service import CollectionService
            user_id = self._main_window.current_user["id"] if self._main_window else None
            if not user_id: return
            entry = CollectionService().add(user_id=user_id, manga_id=self._manga_id)
            if entry:
                self._col_id = entry.id
                self._status_cb.blockSignals(True)
                self._status_cb.setCurrentText(entry.status or "Plan to Read")
                self._status_cb.blockSignals(False)
                self._apply_chapter_rules(entry.current_chapter or 0)
                self._add_btn.hide(); self._in_col.show()
                self.changed.emit()
                self._toast("Berhasil ditambahkan ke koleksi")
        except Exception as e:
            print(f"[CollectionPanel] Add error: {e}")

    def _on_save(self):
        if not self._col_id: return
        try:
            from services.collection_service import CollectionService
            CollectionService().update(self._col_id,
                status=self._status_cb.currentText(),
                current_chapter=self._ch_spin.value())
            self.changed.emit()
            self._toast("Koleksi berhasil disimpan")
        except Exception as e:
            print(f"[CollectionPanel] Save error: {e}")

    def _on_remove(self):
        if not self._col_id: return
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Remove")
        msg_box.setText("Remove from collection?\n(Reviews will also be deleted.)")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setStyleSheet("""
            QLabel { color: white; }
            QMessageBox { background-color: #1a1a1a; }
            QPushButton { color: white; background-color: rgba(255,255,255,0.20); 
                        border: 1px solid white; border-radius: 6px; 
                        padding: 4px 12px; }
            QPushButton:hover { background-color: rgba(255,255,255,0.35); }
        """)
        reply = msg_box.exec()
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from services.collection_service import CollectionService
                user_id = self._main_window.current_user["id"] if self._main_window else None
                CollectionService().delete(self._col_id, user_id=user_id)
                self._col_id = None
                self._in_col.hide(); self._add_btn.show()
                self.changed.emit()
                self._toast("Koleksi berhasil dihapus")
            except Exception as e:
                print(f"[CollectionPanel] Remove error: {e}")


class ReviewPanel(QWidget):
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._manga_id = self._col_id = self._review_id = None
        self._main_window = main_window
        self._build()

    def _toast(self, msg: str):
        if self._main_window:
            self._main_window.show_toast(msg)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        r1 = QHBoxLayout()
        lbl = QLabel("Rating:")
        lbl.setStyleSheet(f"color: {WHITE}; font-size: 11px; background: transparent;")
        self._rating = QSpinBox()
        self._rating.setRange(1, 10); self._rating.setValue(7); self._rating.setFixedWidth(60)
        self._rating.setStyleSheet(f"""
            QSpinBox {{ background: rgba(255,255,255,0.25); color: {WHITE};
                border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; padding: 2px 6px; font-size: 12px; }}
            QSpinBox::up-button, QSpinBox::down-button {{ background: rgba(255,255,255,0.15); border: none; width: 16px; }} """)
        r1.addWidget(lbl); r1.addWidget(self._rating); r1.addStretch()
        layout.addLayout(r1)
        self._text = QTextEdit()
        self._text.setPlaceholderText("Write your review here…")
        self._text.setFixedHeight(70)
        self._text.setStyleSheet(f"""
            QTextEdit {{ background: rgba(255,255,255,0.18); color: {WHITE};
                border: 1px solid rgba(255,255,255,0.35); border-radius: 8px; padding: 6px; font-size: 11px; }} """)
        layout.addWidget(self._text)
        r2 = QHBoxLayout(); r2.setSpacing(8)
        self._save_btn = QPushButton("Save Review")
        self._save_btn.setFixedHeight(30)
        self._save_btn.setStyleSheet(f"""
            QPushButton {{ background: {WHITE}; color: {BLUE_PRIMARY};
                border: none; border-radius: 7px; font-size: 11px; font-weight: 700; padding: 0 12px; }}
            QPushButton:hover {{ background: {BLUE_LIGHT}; }} """)
        self._save_btn.clicked.connect(self._on_save)
        self._del_btn = QPushButton("Delete")
        self._del_btn.setFixedHeight(30)
        self._del_btn.setStyleSheet(f"""
            QPushButton {{ background: rgba(220,50,50,0.80); color: {WHITE};
                border: none; border-radius: 7px; font-size: 11px; font-weight: 700; padding: 0 12px; }} """)
        self._del_btn.clicked.connect(self._on_delete)
        self._del_btn.hide()
        r2.addWidget(self._save_btn); r2.addWidget(self._del_btn); r2.addStretch()
        layout.addLayout(r2)

    def load(self, manga_id, col_id, review):
        self._manga_id = manga_id; self._col_id = col_id
        self._review_id = review.id if review else None
        self._rating.setValue(review.rating if review else 7)
        self._text.setPlainText(review.review_text or "" if review else "")
        self._del_btn.setVisible(review is not None)

    def clear(self):
        self._manga_id = self._col_id = self._review_id = None
        self._rating.setValue(7); self._text.clear(); self._del_btn.hide()

    def _on_save(self):
        if not self._manga_id or not self._col_id: return
        try:
            from services.review_service import ReviewService
            svc = ReviewService()
            rating = self._rating.value()
            text = self._text.toPlainText().strip() or None
            user_id = self._main_window.current_user["id"] if self._main_window else None
            if not user_id: return
            if self._review_id:
                svc.update(self._review_id, rating=rating, review_text=text)
            else:
                r = svc.add(manga_id=self._manga_id, collection_id=self._col_id, user_id=user_id, rating=rating, review_text=text)
                if r:
                    self._review_id = r.id; self._del_btn.show()
            self._toast("Review berhasil disimpan")
        except Exception as e:
            print(f"[ReviewPanel] Save error: {e}")

    def _on_delete(self):
        if not self._review_id: return
        reply = QMessageBox.question(self, "Delete Review", "Delete this review?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from services.review_service import ReviewService
                ReviewService().delete(self._review_id)
                self._review_id = None; self._text.clear()
                self._rating.setValue(7); self._del_btn.hide()
                self._toast("Review berhasil dihapus")
            except Exception as e:
                print(f"[ReviewPanel] Delete error: {e}")


class SimilarPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(180)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"background: {BLUE_CARD}; border-radius: {CARD_RADIUS}px;")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        hdr = QLabel("More like this…")
        hdr.setStyleSheet(f"color: {WHITE}; font-size: 13px; font-weight: 700; background: transparent;")
        layout.addWidget(hdr)
        self._cards_layout = QVBoxLayout()
        self._cards_layout.setSpacing(10)
        layout.addLayout(self._cards_layout)
        layout.addStretch()

    def load(self, manga_list, on_click):
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        from .widgets import MangaCard
        for manga in manga_list[:4]:
            card = MangaCard(manga, show_labels=False)
            card.clicked.connect(on_click)
            self._cards_layout.addWidget(card)


class DetailPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._loader = self._cover_ldr = None
        self._manga_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        topbar = QWidget()
        topbar.setFixedHeight(TOPBAR_HEIGHT)
        topbar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        topbar.setStyleSheet(f"background: {BLUE_PRIMARY};")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 16, 0)
        back_btn = QPushButton("  Back")
        back_btn.setFixedSize(80, 34)
        back_btn.setStyleSheet(f"""
            QPushButton {{ background: rgba(255,255,255,0.20); color: {WHITE};
                border: none; border-radius: 8px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: rgba(255,255,255,0.35); }} """)
        back_btn.clicked.connect(self.main_window.go_home)
        tb.addWidget(back_btn); tb.addStretch()
        root.addWidget(topbar)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        body = QWidget()
        body_h = QHBoxLayout(body)
        body_h.setContentsMargins(20, 20, 20, 20)
        body_h.setSpacing(16)
        main_card = QWidget()
        main_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        main_card.setStyleSheet(f"background: {BLUE_CARD}; border-radius: {CARD_RADIUS}px;")
        mc = QVBoxLayout(main_card)
        mc.setContentsMargins(20, 20, 20, 20)
        mc.setSpacing(16)
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        top_row.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_col = QVBoxLayout()
        left_col.setSpacing(6)
        left_col.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._cover = CoverLabel(160, 225)
        left_col.addWidget(self._cover, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._title_lbl = QLabel("Loading…")
        self._title_lbl.setStyleSheet(f"color: {WHITE}; font-size: 14px; font-weight: 700; background: transparent; max-width: 160px;")
        self._title_lbl.setWordWrap(True)
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        left_col.addWidget(self._title_lbl)
        self._meta_layout = QVBoxLayout()
        self._meta_layout.setSpacing(2)
        left_col.addLayout(self._meta_layout)
        left_col.addStretch()
        top_row.addLayout(left_col)
        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        right_col.setAlignment(Qt.AlignmentFlag.AlignTop)
        syn_hdr = QLabel("Synopsis")
        syn_hdr.setStyleSheet(f"color: {WHITE}; font-size: 14px; font-weight: 700; background: transparent;")
        right_col.addWidget(syn_hdr)
        self._synopsis = QLabel("")
        self._synopsis.setStyleSheet(f"color: rgba(255,255,255,0.90); font-size: 12px; background: transparent;")
        self._synopsis.setWordWrap(True)
        self._synopsis.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._synopsis.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        right_col.addWidget(self._synopsis)
        right_col.addStretch()
        top_row.addLayout(right_col, stretch=1)
        mc.addLayout(top_row)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: rgba(255,255,255,0.25); border: none; max-height: 1px;")
        mc.addWidget(sep)
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(32)
        bottom_row.setAlignment(Qt.AlignmentFlag.AlignTop)
        col_sec = QVBoxLayout(); col_sec.setSpacing(6)
        col_lbl = QLabel("Collection")
        col_lbl.setStyleSheet(f"color: {WHITE}; font-size: 13px; font-weight: 700; background: transparent;")
        self._col_panel = CollectionPanel(main_window=self.main_window)
        self._col_panel.changed.connect(self._on_collection_changed)
        col_sec.addWidget(col_lbl); col_sec.addWidget(self._col_panel); col_sec.addStretch()
        bottom_row.addLayout(col_sec)
        rev_sec = QVBoxLayout(); rev_sec.setSpacing(6)
        rev_lbl = QLabel("My Review")
        rev_lbl.setStyleSheet(f"color: {WHITE}; font-size: 13px; font-weight: 700; background: transparent;")
        self._rev_panel = ReviewPanel(main_window=self.main_window)
        rev_sec.addWidget(rev_lbl); rev_sec.addWidget(self._rev_panel); rev_sec.addStretch()
        bottom_row.addLayout(rev_sec, stretch=1)
        mc.addLayout(bottom_row)
        body_h.addWidget(main_card, stretch=1)
        self._similar = SimilarPanel()
        body_h.addWidget(self._similar, alignment=Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

    def _clear_meta(self):
        while self._meta_layout.count():
            item = self._meta_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _add_meta(self, key, value):
        if not value or str(value) in ("", "None"): return
        lbl = QLabel(f"<b>{key}</b>  {value}")
        lbl.setStyleSheet(f"color: rgba(255,255,255,0.90); font-size: 11px; background: transparent;")
        lbl.setWordWrap(True)
        self._meta_layout.addWidget(lbl)

    def load_manga(self, manga_id: int):
        self._manga_id = manga_id
        self._title_lbl.setText("Loading…")
        self._synopsis.setText("")
        self._clear_meta()
        if self._loader and self._loader.isRunning():
            self._loader.quit(); self._loader.wait()
        user_id = self.main_window.current_user["id"] if self.main_window else None
        self._loader = DetailLoader(manga_id, user_id)
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

    @pyqtSlot(object, object, object, list)
    def _on_loaded(self, manga, collection, review, similar):
        if not manga:
            self._title_lbl.setText("Manga not found")
            return
        if manga.cover_url:
            self._cover_ldr = ImageLoader(manga.cover_url)
            self._cover_ldr.loaded.connect(self._cover.set_cover)
            self._cover_ldr.start()
        self._title_lbl.setText(manga.title or "—")
        syn = manga.synopsis or "No synopsis available."
        self._synopsis.setText(syn[:600] + ("…" if len(syn) > 600 else ""))
        self._clear_meta()
        self._add_meta("Genre:", manga.genres)
        self._add_meta("Author:", manga.authors)
        self._add_meta("Year:", manga.year)
        self._add_meta("Status:", manga.status)
        self._add_meta("Score:", manga.score)
        self._add_meta("Chapters:", manga.chapters)
        self._col_panel.load(manga.id, collection, manga_chapters=manga.chapters or 0)
        if collection:
            self._rev_panel.load(manga.id, collection.id, review)
        else:
            self._rev_panel.clear()
        self._similar.load(similar, self.load_manga)

    def _on_collection_changed(self):
        if not self._manga_id: return
        try:
            from services.collection_service import CollectionService
            from services.review_service import ReviewService
            user_id = self.main_window.current_user["id"] if self.main_window else None
            if not user_id: return
            col = CollectionService().get_by_manga_id(self._manga_id, user_id=user_id)
            rev = ReviewService().get_by_manga(self._manga_id, user_id=user_id)
            if col:
                self._rev_panel.load(self._manga_id, col.id, rev)
            else:
                self._rev_panel.clear()
        except Exception as e:
            print(f"[DetailPage] Refresh error: {e}")