from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QPushButton, QScrollArea, QWidget,
    QMessageBox, QFrame, QFileDialog, QCheckBox, QGridLayout
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QColor

from .theme import (
    BLUE_PRIMARY, BLUE_DARK, BLUE_LIGHT, BLUE_CARD,
    WHITE, TEXT_DARK, TEXT_MUTED, CARD_RADIUS
)

# ── Genre & status options (same as filter) ───────────────────────────────────

GENRE_OPTIONS = [
    "Action",        "Drama",
    "Adventure",     "Fantasy",
    "Avant Garde",   "Gourmet",
    "Award Winning", "Horror",
    "Comedy",        "Mystery",
    "Romance",       "Sci-Fi",
    "Slice of Life", "Sports",
    "Supernatural",
]

STATUS_OPTIONS = ["Publishing", "Finished", "On Hiatus", "Discontinued", "Not yet published"]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _label(text: str, required: bool = False) -> QLabel:
    lbl = QLabel(f"{text} {'<span style=\"color:#E53935\">*</span>' if required else ''}")
    lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {TEXT_DARK}; background: transparent;")
    return lbl

def _hint(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED}; background: transparent;")
    return lbl

def _input_style() -> str:
    return f"""
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            border: 1.5px solid {BLUE_LIGHT};
            border-radius: 8px;
            padding: 6px 10px;
            font-size: 13px;
            color: {TEXT_DARK};
            background: transparent;
        }}
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
        QDoubleSpinBox:focus, QComboBox:focus {{
            border: 1.5px solid {BLUE_PRIMARY};
        }}
        QComboBox::drop-down {{ border: none; padding-right: 8px; }}
        QComboBox QAbstractItemView {{
            border: 1px solid {BLUE_LIGHT};
            border-radius: 6px;
            selection-background-color: {BLUE_LIGHT};
            background-color: {WHITE};
        }}
        QSpinBox::up-button, QSpinBox::down-button,
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
            width: 18px;
        }}
    """

# ── Main form dialog ──────────────────────────────────────────────────────────

class AddMangaForm(QDialog):
    manga_added = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Manga Manually")
        self.setMinimumWidth(520)
        self.setMaximumWidth(640)
        self.setModal(True)
        self.setStyleSheet(f"background: {WHITE};")
        self._build()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPainterPath
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        painter.setClipPath(path)
        painter.fillPath(path, QColor(WHITE))
        super().paintEvent(event)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──
        header = QWidget()
        header.setFixedHeight(56)
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header.setStyleSheet("background: transparent;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)

        title_lbl = QLabel("Add Manga Manually")
        title_lbl.setStyleSheet(f"color: {TEXT_DARK}; font-size: 16px; font-weight: 700; background: transparent;")
        h_lay.addWidget(title_lbl)
        h_lay.addStretch()
        root.addWidget(header)

        # ── Scroll area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: transparent;")

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        form = QVBoxLayout(body)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(14)

        # ── Title ──
        form.addWidget(_label("Title", required=True))
        self._title = QLineEdit()
        self._title.setPlaceholderText("e.g. One Piece")
        self._title.setStyleSheet(_input_style())
        form.addWidget(self._title)

        # ── English / Alternative Title ──
        form.addWidget(_label("English / Alternative Title"))
        self._title_en = QLineEdit()
        self._title_en.setPlaceholderText("e.g. Naruto: The Movie (optional)")
        self._title_en.setStyleSheet(_input_style())
        form.addWidget(self._title_en)

        # ── Author ──
        form.addWidget(_label("Author"))
        self._authors = QLineEdit()
        self._authors.setPlaceholderText("e.g. Eiichiro Oda, Akira Toriyama")
        self._authors.setStyleSheet(_input_style())
        form.addWidget(self._authors)
        form.addWidget(_hint("Separate multiple authors with a comma"))

        # ── Genre (multi-select checkboxes) ──
        form.addWidget(_label("Genre", required=True))
        form.addWidget(_hint("Select at least one genre"))

        cb_style = f"""
            QCheckBox {{
                font-size: 13px;
                color: {TEXT_DARK};
                background: transparent;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 16px; height: 16px;
                border: 1.5px solid {BLUE_LIGHT};
                border-radius: 4px;
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background: {BLUE_PRIMARY};
                border-color: {BLUE_PRIMARY};
            }}
            QCheckBox::indicator:hover {{
                border-color: {BLUE_PRIMARY};
            }}
        """

        genre_box = QWidget()
        genre_box.setStyleSheet(f"""
            QWidget#genreBox {{
                border: 1.5px solid {BLUE_LIGHT};
                border-radius: 8px;
                background: transparent;
            }}
        """)
        genre_box.setObjectName("genreBox")
        genre_grid = QGridLayout(genre_box)
        genre_grid.setContentsMargins(12, 10, 12, 10)
        genre_grid.setSpacing(6)

        self._genre_checks = {}
        cols = 2
        for i, genre in enumerate(GENRE_OPTIONS):
            cb = QCheckBox(genre)
            cb.setStyleSheet(cb_style)
            self._genre_checks[genre] = cb
            genre_grid.addWidget(cb, i // cols, i % cols)

        # "Other" row at the end
        other_row_idx = (len(GENRE_OPTIONS) + cols - 1) // cols
        self._other_cb = QCheckBox("Other")
        self._other_cb.setStyleSheet(cb_style)
        self._other_cb.toggled.connect(self._on_other_toggled)
        genre_grid.addWidget(self._other_cb, other_row_idx, 0)

        self._other_input = QLineEdit()
        self._other_input.setPlaceholderText("Specify genre...")
        self._other_input.setFixedHeight(28)
        self._other_input.setEnabled(False)
        self._other_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {BLUE_LIGHT};
                border-radius: 6px;
                padding: 2px 8px;
                font-size: 12px;
                color: {TEXT_DARK};
                background: transparent;
            }}
            QLineEdit:focus {{ border: 1.5px solid {BLUE_PRIMARY}; }}
            QLineEdit:disabled {{ background: rgba(240,244,250,0.5); color: {TEXT_MUTED}; }}
        """)
        genre_grid.addWidget(self._other_input, other_row_idx, 1)

        form.addWidget(genre_box)

        # ── Row: Status + Year + Chapters ──
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        col_status = QVBoxLayout()
        col_status.addWidget(_label("Status"))
        self._status = QComboBox()
        self._status.addItem("— Select status —", None)
        for s in STATUS_OPTIONS:
            self._status.addItem(s, s)
        self._status.setStyleSheet(_input_style())
        self._status.currentIndexChanged.connect(self._on_status_changed)
        col_status.addWidget(self._status)
        row1.addLayout(col_status, stretch=2)

        col_year = QVBoxLayout()
        col_year.addWidget(_label("Year"))
        self._year = QSpinBox()
        self._current_year = QDate.currentDate().year()
        self._year.setRange(1900, self._current_year)
        self._year.setValue(self._current_year)
        self._year.setSpecialValueText("—")
        self._year.setStyleSheet(_input_style())
        col_year.addWidget(self._year)
        row1.addLayout(col_year, stretch=1)

        col_ch = QVBoxLayout()
        col_ch.addWidget(_label("Chapters"))
        self._chapters = QSpinBox()
        self._chapters.setRange(0, 99999)
        self._chapters.setValue(0)
        self._chapters.setSpecialValueText("?")
        self._chapters.setStyleSheet(_input_style())
        col_ch.addWidget(self._chapters)
        row1.addLayout(col_ch, stretch=1)

        form.addLayout(row1)

        # ── Score ──
        form.addWidget(_label("Score / Rating (1.0 – 10.0)"))
        self._score = QDoubleSpinBox()
        self._score.setRange(0.0, 10.0)
        self._score.setSingleStep(0.1)
        self._score.setDecimals(1)
        self._score.setValue(0.0)
        self._score.setSpecialValueText("No score yet")
        self._score.setStyleSheet(_input_style())
        self._score.setFixedWidth(160)
        form.addWidget(self._score)

        # ── Cover image ──
        form.addWidget(_label("Cover Image"))
        self._cover_path = None

        cover_row = QHBoxLayout()
        cover_row.setSpacing(10)

        self._cover_preview = QLabel()
        self._cover_preview.setFixedSize(60, 84)
        self._cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover_preview.setStyleSheet(f"""
            QLabel {{
                border: 1.5px dashed {BLUE_LIGHT};
                border-radius: 6px;
                background: #F5F8FF;
                color: {TEXT_MUTED};
                font-size: 10px;
            }}
        """)
        self._cover_preview.setText("No\nimage")
        cover_row.addWidget(self._cover_preview)

        cover_right = QVBoxLayout()
        cover_right.setSpacing(6)

        self._cover_name_lbl = QLabel("No image selected")
        self._cover_name_lbl.setStyleSheet(
            f"font-size: 12px; color: {TEXT_MUTED}; background: transparent;"
        )
        self._cover_name_lbl.setWordWrap(True)
        cover_right.addWidget(self._cover_name_lbl)

        pick_btn = QPushButton("Choose Image...")
        pick_btn.setFixedHeight(36)
        pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pick_btn.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE};
                border: 1.5px solid {BLUE_LIGHT};
                border-radius: 8px;
                color: {BLUE_PRIMARY};
                font-size: 13px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background: {BLUE_LIGHT};
                color: {WHITE};
            }}
        """)
        pick_btn.clicked.connect(self._pick_cover)
        cover_right.addWidget(pick_btn)

        clear_btn = QPushButton("Remove Image")
        clear_btn.setFixedHeight(28)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {TEXT_MUTED};
                font-size: 11px;
                text-decoration: underline;
            }}
            QPushButton:hover {{ color: #E53935; }}
        """)
        clear_btn.clicked.connect(self._clear_cover)
        cover_right.addWidget(clear_btn)
        cover_right.addStretch()

        cover_row.addLayout(cover_right)
        form.addLayout(cover_row)

        # ── Synopsis ──
        form.addWidget(_label("Synopsis"))
        self._synopsis = QTextEdit()
        self._synopsis.setPlaceholderText("Write a short synopsis of this manga…")
        self._synopsis.setFixedHeight(100)
        self._synopsis.setStyleSheet(_input_style())
        form.addWidget(self._synopsis)

        # ── Divider ──
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {BLUE_LIGHT};")
        form.addWidget(line)

        # ── Action buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setFixedHeight(40)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {WHITE}; border: 1.5px solid {BLUE_LIGHT};
                border-radius: 8px; color: {TEXT_MUTED};
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {BLUE_LIGHT}; color: {WHITE}; }}
        """)
        self._cancel_btn.clicked.connect(self.reject)

        self._save_btn = QPushButton("Save Manga")
        self._save_btn.setFixedHeight(40)
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BLUE_PRIMARY}; border: none;
                border-radius: 8px; color: {WHITE};
                font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {BLUE_DARK}; }}
            QPushButton:disabled {{ background: {BLUE_LIGHT}; color: rgba(255,255,255,0.5); }}
        """)
        self._save_btn.clicked.connect(self._on_save)

        btn_row.addWidget(self._cancel_btn)
        btn_row.addWidget(self._save_btn)
        form.addLayout(btn_row)

        # ── Error label ──
        self._err_lbl = QLabel("")
        self._err_lbl.setStyleSheet("color: #E53935; font-size: 12px; background: transparent;")
        self._err_lbl.setWordWrap(True)
        self._err_lbl.hide()
        form.addWidget(self._err_lbl)

        scroll.setWidget(body)
        root.addWidget(scroll)

    # ── Other genre toggle ────────────────────────────────────────────────────

    def _on_other_toggled(self, checked: bool):
        self._other_input.setEnabled(checked)
        if not checked:
            self._other_input.clear()

    # ── Cover picker ──────────────────────────────────────────────────────────

    def _pick_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Cover Image", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not path:
            return
        px = QPixmap(path)
        if px.isNull():
            self._show_error("The image could not be read.")
            return
        self._cover_path = path
        thumb = px.scaled(
            60, 84,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
)
        x = (thumb.width()  - 60) // 2
        y = (thumb.height() - 84) // 2
        self._cover_preview.setPixmap(thumb.copy(x, y, 60, 84))
        self._cover_preview.setText("")
        self._cover_preview.setStyleSheet(
            "border: 1.5px solid #90CAF9; border-radius: 6px; background: transparent;"
        )
        from pathlib import Path
        self._cover_name_lbl.setText(Path(path).name)
        self._cover_name_lbl.setStyleSheet(
            f"font-size: 12px; color: {TEXT_DARK}; background: transparent;"
        )

    def _clear_cover(self):
        self._cover_path = None
        self._cover_preview.clear()
        self._cover_preview.setText("No\nimage")
        self._cover_preview.setStyleSheet(f"""
            QLabel {{
                border: 1.5px dashed {BLUE_LIGHT};
                border-radius: 6px;
                background: #F5F8FF;
                color: {TEXT_MUTED};
                font-size: 10px;
            }}
        """)
        self._cover_name_lbl.setText("No image selected")
        self._cover_name_lbl.setStyleSheet(
            f"font-size: 12px; color: {TEXT_MUTED}; background: transparent;"
        )

    def _on_status_changed(self):
        status = self._status.currentData()
        if status == "Not yet published":
            self._year.setMaximum(2099)
        else:
            self._year.setMaximum(self._current_year)
            if self._year.value() > self._current_year:
                self._year.setValue(self._current_year)

    def _get_genres(self) -> str:
        """Collect all selected genres (checkboxes + Other input) into a CSV string."""
        parts = []
        for genre, cb in self._genre_checks.items():
            if cb.isChecked():
                parts.append(genre)
        if self._other_cb.isChecked():
            other_text = self._other_input.text().strip()
            if other_text:
                for g in other_text.split(","):
                    g = g.strip()
                    if g and g not in parts:
                        parts.append(g)
        return ", ".join(parts)

    def _show_error(self, msg: str):
        self._err_lbl.setText(msg)
        self._err_lbl.show()

    def _clear_error(self):
        self._err_lbl.hide()
        self._err_lbl.setText("")

    # ── Save ──────────────────────────────────────────────────────────────────

    def _on_save(self):
        self._clear_error()
        self._save_btn.setEnabled(False)
        self._save_btn.setText("Saving…")

        # Validate title
        title = self._title.text().strip()
        if not title:
            self._show_error("Title is required.")
            self._save_btn.setEnabled(True)
            self._save_btn.setText("Save Manga")
            return

        # Validate at least one genre selected
        genres = self._get_genres()
        if not genres:
            self._show_error("Please select at least one genre.")
            self._save_btn.setEnabled(True)
            self._save_btn.setText("Save Manga")
            return

        # Validate Other genre text if Other is checked but empty
        if self._other_cb.isChecked() and not self._other_input.text().strip():
            self._show_error("Please specify the genre in the \"Other\" field.")
            self._save_btn.setEnabled(True)
            self._save_btn.setText("Save Manga")
            return

        # Validate year
        status_val = self._status.currentData()
        year_val = self._year.value()
        current_year = QDate.currentDate().year()
        if year_val != 1900 and status_val != "Not yet published" and year_val > current_year:
            self._show_error(
                f"Year ({year_val}) cannot exceed the current year ({current_year}). "
                f"If the manga hasn't been published yet, select \"Not yet published\"."
            )
            self._save_btn.setEnabled(True)
            self._save_btn.setText("Save Manga")
            return

        # Collect values
        title_en  = self._title_en.text().strip() or None
        authors   = self._authors.text().strip() or None
        status    = self._status.currentData()
        year      = self._year.value() if self._year.value() != 1900 else None
        chapters  = self._chapters.value() if self._chapters.value() > 0 else None
        score     = self._score.value() if self._score.value() > 0.0 else None
        cover_url = self._cover_path or None
        synopsis  = self._synopsis.toPlainText().strip() or None

        try:
            from services.manga_service import MangaService
            from services.collection_service import CollectionService

            svc   = MangaService()
            manga = svc.add_manual(
                title=title,
                synopsis=synopsis,
                authors=authors,
                genres=genres,
                status=status,
                chapters=chapters,
                year=year,
                cover_url=cover_url,
                score=score
)

            # Save title_en if provided
            if title_en and manga:
                from database import get_session
                session = get_session()
                try:
                    from models.manga import Manga
                    obj = session.query(Manga).filter(Manga.id == manga.id).first()
                    if obj:
                        obj.title_en = title_en
                        session.commit()
                finally:
                    session.close()

            # Add to UserCollection so it appears in My Library
            user_id = None
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, "main_window"):
                    mw = parent.main_window
                    if hasattr(mw, "current_user") and mw.current_user:
                        user_id = mw.current_user["id"]
                    break
                if hasattr(parent, "current_user") and parent.current_user:
                    user_id = parent.current_user["id"]
                    break
                parent = parent.parent() if hasattr(parent, "parent") else None

            if user_id is not None:
                col_svc = CollectionService()
                col_svc.add(
                    user_id=user_id,
                    manga_id=manga.id,
                    status="Plan to Read"
)

            self.manga_added.emit(manga.id)
            self.accept()

        except ValueError as e:
            self._show_error(str(e))
        except Exception as e:
            self._show_error(f"Failed to save: {e}")
        finally:
            self._save_btn.setEnabled(True)
            self._save_btn.setText("Save Manga")