from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QTextEdit, QSpinBox,
    QComboBox, QFrame, QSizePolicy, QMessageBox,
    QGraphicsOpacityEffect, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap

from .theme import (
    BLUE_PRIMARY, BLUE_CARD, BLUE_DARK, BLUE_LIGHT,
    BLACK, WHITE, TEXT_MUTED,
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
    status_changed = pyqtSignal(str)
    STATUS_OPTIONS = ["Plan to Read", "Reading", "Completed", "Dropped"]

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._manga_id = self._col_id = None
        self._manga_chapters = 0   
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
            QPushButton {{ background: {BLACK}; color: {WHITE};
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
        lbl1.setStyleSheet(f"color: {BLACK}; font-size: 11px; background: transparent;")
        self._status_cb = QComboBox()
        self._status_cb.addItems(self.STATUS_OPTIONS)
        self._status_cb.setFixedWidth(140)
        self._status_cb.setStyleSheet(f"""
            QComboBox {{ background: {WHITE}; color: {BLACK};
                border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; padding: 2px 8px; font-size: 11px; }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{ background: {WHITE}; color: {BLACK}; selection-background-color: {BLUE_LIGHT}; }} """)
        r1.addWidget(lbl1); r1.addWidget(self._status_cb); r1.addStretch()
        self._status_cb.currentIndexChanged.connect(self._on_status_changed)
        ic.addLayout(r1)

        r2 = QHBoxLayout()
        lbl2 = QLabel("Chapter:")
        lbl2.setStyleSheet(f"color: {BLACK}; font-size: 11px; background: transparent;")
        self._ch_spin = QSpinBox()
        self._ch_spin.setRange(0, 9999)
        self._ch_spin.setFixedWidth(80)
        self._ch_spin.setStyleSheet(f"""
            QSpinBox {{ background: rgba(255,255,255,0.25); color: {BLACK};
                border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; padding: 2px 6px; font-size: 11px; }}
            QSpinBox::up-button, QSpinBox::down-button {{ background: rgba(255,255,255,0.15); border: none; width: 16px; }} """)
        r2.addWidget(lbl2); r2.addWidget(self._ch_spin); r2.addStretch()
        self._ch_spin.valueChanged.connect(self._on_chapter_changed)
        ic.addLayout(r2)

        r3 = QHBoxLayout(); r3.setSpacing(8)
        self._save_btn = QPushButton("Save")
        self._save_btn.setFixedHeight(30)
        self._save_btn.setStyleSheet(f"""
            QPushButton {{ background: {BLACK}; color: {WHITE};
                border: none; border-radius: 7px; font-size: 11px; font-weight: 700; padding: 0 12px; }}
            QPushButton:hover {{ background: {BLUE_LIGHT}; }} """)
        self._save_btn.clicked.connect(self._on_save)

        self._remove_btn = QPushButton("Remove")
        self._remove_btn.setFixedHeight(30)
        self._remove_btn.setStyleSheet(f"""
            QPushButton {{ background: rgba(220,50,50,0.80); color: {BLACK};
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
            self._status_cb.blockSignals(True)
            self._status_cb.setCurrentText(entry.status or "Plan to Read")
            self._status_cb.blockSignals(False)
            self._apply_chapter_rules(entry.current_chapter or 0)
            self._add_btn.hide(); self._in_col.show()
        else:
            self._col_id = None
            self._add_btn.show(); self._in_col.hide()

    def _on_status_changed(self):
        self._apply_chapter_rules()
        self.status_changed.emit(self._status_cb.currentText())

    def _on_chapter_changed(self, value: int):
        if not self._manga_chapters or self._manga_chapters <= 0:
            return
        if value >= self._manga_chapters:
            self._status_cb.blockSignals(True)
            self._status_cb.setCurrentText("Completed")
            self._status_cb.blockSignals(False)
            self._apply_chapter_rules()

    def _apply_chapter_rules(self, current_chapter: int = None):
        status = self._status_cb.currentText()
        mx = self._manga_chapters  

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
                self._toast("Successfully added to collection")
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
            self._toast("Collection successfully saved")
        except Exception as e:
            print(f"[CollectionPanel] Save error: {e}")

    def _on_remove(self):
        if not self._col_id: return
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Remove")
        msg_box.setText("Remove from collection?\n(Reviews will also be deleted.)")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background: {BLUE_DARK};
                font-family: Arial;
            }}
            QLabel {{
                color: {WHITE};
                background: transparent;
                font-size: 13px;
            }}
            QPushButton {{
                background: rgba(255,255,255,0.15);
                color: {WHITE};
                border: 1px solid rgba(255,255,255,0.40);
                border-radius: 12px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.28);
            }}
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
                self._toast("Collection successfully removed")
            except Exception as e:
                print(f"[CollectionPanel] Remove error: {e}")


_TAG_COLORS = {
    "still reading": ("#1565C0", "#E3F2FD"),
    "completed":     ("#1B5E20", "#E8F5E9"),
    "dropped":       ("#B71C1C", "#FFEBEE"),
}


class TagBar(QWidget):
    tags_changed = pyqtSignal(list)

    STATUS_TAG_MAP = {
        "Reading":   "still reading",
        "Completed": "completed",
        "Dropped":   "dropped",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._tags: list = []
        self._auto_tag: str = ""
        self._locked = False
        self._build()

    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._row = QHBoxLayout(self._container)
        self._row.setContentsMargins(0, 0, 0, 0)
        self._row.setSpacing(6)
        self._row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        outer.addWidget(self._container, stretch=1)

        self._add_btn = QPushButton("＋")
        self._add_btn.setFixedSize(26, 26)
        self._add_btn.setToolTip("Add tag")
        self._add_btn.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,0.20);color:white;"
            "border:1px solid rgba(255,255,255,0.40);border-radius:13px;"
            "font-size:13px;font-weight:700;}"
            "QPushButton:hover{background:rgba(255,255,255,0.35);}"
            "QPushButton:disabled{opacity:0.35;}"
        )
        self._add_btn.clicked.connect(self._on_add)
        outer.addWidget(self._add_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

    def set_status(self, status: str):
        new_auto = self.STATUS_TAG_MAP.get(status, "")
        if new_auto == self._auto_tag:
            return
        if self._auto_tag and self._auto_tag in self._tags:
            self._tags.remove(self._auto_tag)
        self._auto_tag = new_auto
        if new_auto and new_auto not in self._tags:
            self._tags.insert(0, new_auto)
        self._refresh()

    def load_tags(self, tags: list, status: str = ""):
        self._auto_tag = self.STATUS_TAG_MAP.get(status, "")
        others = [t for t in tags if t != self._auto_tag]
        self._tags = ([self._auto_tag] if self._auto_tag else []) + others
        self._refresh()

    def get_tags(self) -> list:
        return list(self._tags)

    def set_locked(self, locked: bool):
        self._locked = locked
        self._add_btn.setEnabled(not locked)
        self._refresh()

    def _refresh(self):
        while self._row.count():
            item = self._row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for tag in self._tags:
            self._row.addWidget(self._make_pill(tag))

    def _make_pill(self, tag: str) -> QWidget:
        colors = _TAG_COLORS.get(tag.lower())
        if colors:
            bg, fg = colors
        else:
            bg, fg = "#E0E0E0", "#1A1A2E"

        pill = QWidget()
        pill.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        pill.setFixedHeight(24)
        pill.setSizePolicy(
            pill.sizePolicy().horizontalPolicy(),
            pill.sizePolicy().verticalPolicy()
        )
        pill.setStyleSheet(
            f"QWidget{{background:{bg};border-radius:12px;}}"
        )

        row = QHBoxLayout(pill)
        row.setContentsMargins(10, 0, 8, 0)
        row.setSpacing(4)

        lbl = QLabel(tag)
        lbl.setStyleSheet(
            f"color:{fg};font-size:10px;font-weight:600;background:transparent;"
        )
        row.addWidget(lbl)

        is_auto = (tag == self._auto_tag)
        if not is_auto and not self._locked:
            x_style = (
                f"QPushButton{{background:transparent;color:{fg};border:none;"
                f"font-size:9px;font-weight:700;padding:0;}}"
                f"QPushButton:hover{{color:#000000;}}"
            )
            x = QPushButton("✕")
            x.setFixedSize(13, 13)
            x.setStyleSheet(x_style)
            x.clicked.connect(lambda _, t=tag: self._remove(t))
            row.addWidget(x)
        return pill

    def _remove(self, tag: str):
        if tag in self._tags:
            self._tags.remove(tag)
        self._refresh()
        self.tags_changed.emit(self._tags)

    def _on_add(self):
        if self._locked:
            return
        dialog = QInputDialog(self)
        dialog.setWindowTitle("New Tag")
        dialog.setLabelText("Tag name:")
        dialog.setStyleSheet("""
            QInputDialog { background-color: #FFFFFF; }
            QLabel { color: #1A1A2E; font-size: 12px; }
            QLineEdit { background-color: #F5F5F5; color: #1A1A2E; border: 1px solid #CCCCCC;
                        border-radius: 6px; padding: 4px 8px; font-size: 12px; }
            QPushButton { background-color: #1565C0; color: white; border: none;
                          border-radius: 6px; padding: 4px 14px; font-size: 11px; font-weight: 700; }
            QPushButton:hover { background-color: #1976D2; }
        """)
        ok = dialog.exec()
        text = dialog.textValue()
        tag = text.strip().lower()
        if ok and tag and tag not in self._tags:
            self._tags.append(tag)
            self._refresh()
            self.tags_changed.emit(self._tags)


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
        lbl.setStyleSheet(f"color: {BLACK}; font-size: 11px; background: transparent;")
        self._rating = QSpinBox()
        self._rating.setRange(1, 10); self._rating.setValue(7); self._rating.setFixedWidth(60)
        self._rating.setStyleSheet(f"""
            QSpinBox {{ background: rgba(255,255,255,0.25); color: {BLACK};
                border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; padding: 2px 6px; font-size: 12px; }}
            QSpinBox::up-button, QSpinBox::down-button {{ background: rgba(255,255,255,0.15); border: none; width: 16px; }} """)
        r1.addWidget(lbl); r1.addWidget(self._rating); r1.addStretch()
        layout.addLayout(r1)
        self._text = QTextEdit()
        self._text.setPlaceholderText("Write your review here…")
        self._text.setFixedHeight(70)
        self._text.setStyleSheet(f"""
            QTextEdit {{ background: rgba(255,255,255,0.18); color: {BLACK};
                border: 1px solid rgba(255,255,255,0.35); border-radius: 8px; padding: 6px; font-size: 11px; }} """)
        layout.addWidget(self._text)
        r2 = QHBoxLayout(); r2.setSpacing(8)
        self._save_btn = QPushButton("Save Review")
        self._save_btn.setFixedHeight(30)
        self._save_btn.setStyleSheet(f"""
            QPushButton {{ background: {BLACK}; color: {WHITE};
                border: none; border-radius: 7px; font-size: 11px; font-weight: 700; padding: 0 12px; }}
            QPushButton:hover {{ background: {BLUE_LIGHT}; }} """)
        self._save_btn.clicked.connect(self._on_save)
        self._del_btn = QPushButton("Delete")
        self._del_btn.setFixedHeight(30)
        self._del_btn.setStyleSheet(f"""
            QPushButton {{ background: rgba(220,50,50,0.80); color: {BLACK};
                border: none; border-radius: 7px; font-size: 11px; font-weight: 700; padding: 0 12px; }} """)
        self._del_btn.clicked.connect(self._on_delete)
        self._del_btn.hide()
        r2.addWidget(self._save_btn); r2.addWidget(self._del_btn); r2.addStretch()
        layout.addLayout(r2)

        tag_hdr = QLabel("Tags")
        tag_hdr.setStyleSheet("color:rgba(0,0,0,0.55);font-size:10px;font-weight:600;background:transparent;")
        layout.addWidget(tag_hdr)
        self._tag_bar = TagBar()
        layout.addWidget(self._tag_bar)

    def load(self, manga_id, col_id, review, status: str = ""):
        self._manga_id = manga_id; self._col_id = col_id
        self._review_id = review.id if review else None
        self._rating.setValue(review.rating if review else 7)
        self._text.setPlainText(review.review_text or "" if review else "")
        self._del_btn.setVisible(review is not None)
        try:
            import json
            raw = getattr(review, "tags", "[]") if review else "[]"
            saved_tags = json.loads(raw or "[]")
        except Exception:
            saved_tags = []
        self._tag_bar.load_tags(saved_tags, status=status)

    def clear(self):
        self._manga_id = self._col_id = self._review_id = None
        self._rating.setValue(7); self._text.clear(); self._del_btn.hide()
        self._tag_bar.load_tags([], status="")

    def set_locked(self, locked: bool):
        self._rating.setEnabled(not locked)
        self._text.setEnabled(not locked)
        self._save_btn.setEnabled(not locked)
        self._tag_bar.set_locked(locked)
        effect = self.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)
        effect.setOpacity(0.35 if locked else 1.0)
        self._text.setPlaceholderText(
            'Set status selain "Plan to Read" untuk menulis review…'
            if locked else "Write your review here…"
        )

    def _on_save(self):
        if not self._manga_id or not self._col_id: return
        try:
            from services.review_service import ReviewService
            svc = ReviewService()
            rating = self._rating.value()
            text = self._text.toPlainText().strip() or None
            tags = self._tag_bar.get_tags()
            user_id = self._main_window.current_user["id"] if self._main_window else None
            if not user_id: return
            if self._review_id:
                svc.update(self._review_id, rating=rating, review_text=text, tags=tags)
            else:
                r = svc.add(manga_id=self._manga_id, collection_id=self._col_id, user_id=user_id, rating=rating, review_text=text, tags=tags)
                if r:
                    self._review_id = r.id; self._del_btn.show()
            self._toast("Review successfully saved")
        except Exception as e:
            print(f"[ReviewPanel] Save error: {e}")

    def _on_delete(self):
        if not self._review_id: return
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Delete Review")
        msg_box.setText("Delete this review?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background: {BLUE_DARK};
                font-family: Arial;
            }}
            QLabel {{
                color: {WHITE};
                background: transparent;
                font-size: 13px;
            }}
            QPushButton {{
                background: rgba(255,255,255,0.15);
                color: {WHITE};
                border: 1px solid rgba(255,255,255,0.40);
                border-radius: 12px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.28);
            }}
        """)
        reply = msg_box.exec()
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from services.review_service import ReviewService
                ReviewService().delete(self._review_id)
                self._review_id = None; self._text.clear()
                self._rating.setValue(7); self._del_btn.hide()
                self._toast("Review successfully deleted")
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
        hdr.setStyleSheet(f"color: {BLACK}; font-size: 13px; font-weight: 700; background: transparent;")
        layout.addWidget(hdr)
        self._cards_layout = QVBoxLayout()
        self._cards_layout.setSpacing(10)
        layout.addLayout(self._cards_layout)
        layout.addStretch()

    def load(self, manga_list, on_click):
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            w = item.widget()
            if w:
                if hasattr(w, 'stop_loader'):
                    w.stop_loader()
                else:
                    ldr = getattr(w, '_loader', None)
                    if ldr and ldr.isRunning():
                        ldr.quit()
                        ldr.wait()
                w.deleteLater()
        from .widgets import MangaCard
        for manga in manga_list[:4]:
            card = MangaCard(manga, show_labels=False)
            card.clicked.connect(on_click)
            self._cards_layout.addWidget(card)


class DetailPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._loader = None
        self._cover_ldr = None
        self._active_threads = []   
        self._manga_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        topbar = QWidget()
        topbar.setFixedHeight(TOPBAR_HEIGHT)
        topbar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        topbar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7aaee0,stop:0.5 #82c8ef,stop:1 #80d9e8);")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 16, 0)
        back_btn = QPushButton("  Back")
        back_btn.setFixedSize(80, 34)
        back_btn.setStyleSheet(f"""
            QPushButton {{ background: rgba(0,60,120,0.15); color: #003c78;
                border: none; border-radius: 8px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: rgba(0,60,120,0.25); }} """)
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
        self._title_lbl.setStyleSheet(f"color: {BLACK}; font-size: 14px; font-weight: 700; background: transparent; max-width: 160px;")
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
        syn_hdr.setStyleSheet(f"color: {BLACK}; font-size: 14px; font-weight: 700; background: transparent;")
        right_col.addWidget(syn_hdr)
        self._synopsis = QLabel("")
        # Perbaikan: Menambahkan f-string dan mengubah warna ke {BLACK}
        self._synopsis.setStyleSheet(f"color: {BLACK}; font-size: 12px; background: transparent;")
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
        col_lbl.setStyleSheet(f"color: {BLACK}; font-size: 13px; font-weight: 700; background: transparent;")
        self._col_panel = CollectionPanel(main_window=self.main_window)
        self._col_panel.changed.connect(self._on_collection_changed)
        self._col_panel.status_changed.connect(self._on_status_dropdown_changed)
        col_sec.addWidget(col_lbl); col_sec.addWidget(self._col_panel); col_sec.addStretch()
        bottom_row.addLayout(col_sec)
        rev_sec = QVBoxLayout(); rev_sec.setSpacing(6)
        rev_lbl = QLabel("My Review")
        rev_lbl.setStyleSheet(f"color: {BLACK}; font-size: 13px; font-weight: 700; background: transparent;")
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
        # Perbaikan: Menambahkan f-string dan mengubah warna ke {BLACK}
        lbl.setStyleSheet(f"color: {BLACK}; font-size: 11px; background: transparent;")
        lbl.setWordWrap(True)
        self._meta_layout.addWidget(lbl)

    def load_manga(self, manga_id: int):
        self._manga_id = manga_id
        self._title_lbl.setText("Loading…")
        self._synopsis.setText("")
        self._clear_meta()

        if self._loader is not None:
            try:
                self._loader.finished.disconnect()
            except Exception:
                pass
            if self._loader.isRunning():
                self._loader.quit()
                self._loader.wait()
            self._loader = None

        if self._cover_ldr is not None:
            if self._cover_ldr.isRunning():
                self._cover_ldr.quit()
                self._cover_ldr.wait()
            self._cover_ldr = None

        user_id = self.main_window.current_user["id"] if self.main_window else None
        self._loader = DetailLoader(manga_id, user_id)
        self._loader.finished.connect(self._on_loaded)
        
        # Perbaikan: Simpan referensi ke active_threads (Keep-alive)
        self._active_threads.append(self._loader)
        self._loader.finished.connect(lambda: self._cleanup_thread(self._loader))
        
        self._loader.start()

    @pyqtSlot(object, object, object, list)
    def _on_loaded(self, manga, collection, review, similar):
        if not manga:
            self._title_lbl.setText("Manga not found")
            return
        if manga.cover_url:
            if self._cover_ldr is not None and self._cover_ldr.isRunning():
                self._cover_ldr.quit()
                self._cover_ldr.wait()
            self._cover_ldr = ImageLoader(manga.cover_url)
            self._cover_ldr.loaded.connect(self._cover.set_cover)
            self._cover_ldr.finished.connect(lambda: self._cleanup_thread(self._cover_ldr))
            
            # Perbaikan: Simpan referensi cover_ldr ke active_threads
            self._active_threads.append(self._cover_ldr)
            
            self._cover_ldr.start()
        self._title_lbl.setText(manga.title or "—")
        syn = manga.synopsis or "No synopsis available."
        self._synopsis.setText(syn)
        self._clear_meta()
        self._add_meta("Genre:", manga.genres)
        self._add_meta("Author:", manga.authors)
        self._add_meta("Year:", manga.year)
        self._add_meta("Status:", manga.status)
        self._add_meta("Score:", manga.score)
        self._add_meta("Chapters:", manga.chapters)
        self._col_panel.load(manga.id, collection, manga_chapters=manga.chapters or 0)
        if collection:
            _status = (collection.status or "Plan to Read").strip()
            self._rev_panel.load(manga.id, collection.id, review, status=_status)
            self._rev_panel.set_locked(_status == "Plan to Read")
        else:
            self._rev_panel.clear()
            self._rev_panel.set_locked(True)
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
                _status = (col.status or "Plan to Read").strip()
                self._rev_panel.load(self._manga_id, col.id, rev, status=_status)
                self._rev_panel.set_locked(_status == "Plan to Read")
            else:
                self._rev_panel.clear()
                self._rev_panel.set_locked(True)
        except Exception as e:
            print(f"[DetailPage] Refresh error: {e}")

    def _cleanup_thread(self, thread):
        try:
            if thread in self._active_threads:
                self._active_threads.remove(thread)
        except Exception:
            pass

    def _on_status_dropdown_changed(self, status: str):
        locked = status.strip() == "Plan to Read"
        self._rev_panel.set_locked(locked)
        if not locked:
            self._rev_panel._tag_bar.set_status(status.strip())