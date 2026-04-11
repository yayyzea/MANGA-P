from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QPushButton, QScrollArea, QWidget,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .theme import (
    BLUE_PRIMARY, BLUE_DARK, BLUE_LIGHT, BLUE_CARD,
    WHITE, TEXT_DARK, TEXT_MUTED, CARD_RADIUS
)

# ── Pilihan genre dan status (sama dengan search_page) ────────────────────────

GENRE_OPTIONS = [
    "Action", "Adventure", "Avant Garde", "Award Winning",
    "Comedy", "Drama", "Fantasy", "Gourmet",
    "Horror", "Mystery", "Romance", "Sci-Fi",
    "Slice of Life", "Sports", "Supernatural",
]

STATUS_OPTIONS = ["Publishing", "Finished", "On Hiatus", "Discontinued", "Not yet published"]


# ── Helper: buat label field ──────────────────────────────────────────────────

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
            background: {WHITE};
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
        }}
        QSpinBox::up-button, QSpinBox::down-button,
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
            width: 18px;
        }}
    """


# ── Form dialog utama ─────────────────────────────────────────────────────────

class AddMangaForm(QDialog):
    """
    Dialog untuk menambah manga secara manual ke database lokal.
    Dipanggil dari LibraryPage (tombol "+") oleh A3.

    Signal:
        manga_added(int)  — dikirim setelah berhasil simpan,
                            membawa manga.id agar library bisa refresh.
    """
    manga_added = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Manga Manual")
        self.setMinimumWidth(520)
        self.setMaximumWidth(620)
        self.setModal(True)
        self.setStyleSheet(f"background: {WHITE};")
        self._build()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header biru ──
        header = QWidget()
        header.setFixedHeight(56)
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header.setStyleSheet(f"background: {BLUE_PRIMARY}; border-radius: 0px;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)

        title_lbl = QLabel("Add Manga Manual")
        title_lbl.setStyleSheet(f"color: {WHITE}; font-size: 16px; font-weight: 700; background: transparent;")
        h_lay.addWidget(title_lbl)
        h_lay.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {WHITE}; font-size: 16px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.20); border-radius: 16px; }}
        """)
        close_btn.clicked.connect(self.reject)
        h_lay.addWidget(close_btn)
        root.addWidget(header)

        # ── Scroll area untuk form ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: transparent;")

        body = QWidget()
        body.setStyleSheet(f"background: {WHITE};")
        form = QVBoxLayout(body)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(14)

        # ── Field: Judul ──
        form.addWidget(_label("Judul", required=True))
        self._title = QLineEdit()
        self._title.setPlaceholderText("Contoh: One Piece")
        self._title.setStyleSheet(_input_style())
        form.addWidget(self._title)

        # ── Field: Judul Inggris ──
        form.addWidget(_label("Judul Inggris / Alternatif"))
        self._title_en = QLineEdit()
        self._title_en.setPlaceholderText("Contoh: Naruto: The Movie (opsional)")
        self._title_en.setStyleSheet(_input_style())
        form.addWidget(self._title_en)

        # ── Field: Author ──
        form.addWidget(_label("Author / Penulis"))
        self._authors = QLineEdit()
        self._authors.setPlaceholderText("Contoh: Eiichiro Oda, Akira Toriyama")
        self._authors.setStyleSheet(_input_style())
        form.addWidget(self._authors)
        form.addWidget(_hint("Pisahkan beberapa author dengan koma"))

        # ── Field: Genre ──
        form.addWidget(_label("Genre Utama"))
        self._genre_cb = QComboBox()
        self._genre_cb.addItem("— Pilih genre —", None)
        for g in GENRE_OPTIONS:
            self._genre_cb.addItem(g, g)
        self._genre_cb.setStyleSheet(_input_style())
        form.addWidget(self._genre_cb)

        form.addWidget(_label("Genre Tambahan (opsional)"))
        self._genres_extra = QLineEdit()
        self._genres_extra.setPlaceholderText("Contoh: Romance, Comedy")
        self._genres_extra.setStyleSheet(_input_style())
        form.addWidget(self._genres_extra)
        form.addWidget(_hint("Pisahkan dengan koma, akan digabung dengan genre utama"))

        # ── Row: Status + Tahun + Chapter ──
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        col_status = QVBoxLayout()
        col_status.addWidget(_label("Status"))
        self._status = QComboBox()
        self._status.addItem("— Pilih status —", None)
        for s in STATUS_OPTIONS:
            self._status.addItem(s, s)
        self._status.setStyleSheet(_input_style())
        col_status.addWidget(self._status)
        row1.addLayout(col_status, stretch=2)

        col_year = QVBoxLayout()
        col_year.addWidget(_label("Tahun Terbit"))
        self._year = QSpinBox()
        self._year.setRange(1900, 2099)
        self._year.setValue(2024)
        self._year.setSpecialValueText("—")
        self._year.setStyleSheet(_input_style())
        col_year.addWidget(self._year)
        row1.addLayout(col_year, stretch=1)

        col_ch = QVBoxLayout()
        col_ch.addWidget(_label("Jumlah Chapter"))
        self._chapters = QSpinBox()
        self._chapters.setRange(0, 99999)
        self._chapters.setValue(0)
        self._chapters.setSpecialValueText("?")
        self._chapters.setStyleSheet(_input_style())
        col_ch.addWidget(self._chapters)
        row1.addLayout(col_ch, stretch=1)

        form.addLayout(row1)

        # ── Field: Score ──
        form.addWidget(_label("Score / Rating (1.0 – 10.0)"))
        self._score = QDoubleSpinBox()
        self._score.setRange(0.0, 10.0)
        self._score.setSingleStep(0.1)
        self._score.setDecimals(1)
        self._score.setValue(0.0)
        self._score.setSpecialValueText("Belum ada score")
        self._score.setStyleSheet(_input_style())
        self._score.setFixedWidth(160)
        form.addWidget(self._score)

        # ── Field: Cover URL ──
        form.addWidget(_label("URL Cover / Gambar"))
        self._cover_url = QLineEdit()
        self._cover_url.setPlaceholderText("https://cdn.myanimelist.net/images/manga/... (opsional)")
        self._cover_url.setStyleSheet(_input_style())
        form.addWidget(self._cover_url)

        # ── Field: Sinopsis ──
        form.addWidget(_label("Sinopsis"))
        self._synopsis = QTextEdit()
        self._synopsis.setPlaceholderText("Tulis sinopsis singkat manga ini…")
        self._synopsis.setFixedHeight(100)
        self._synopsis.setStyleSheet(_input_style())
        form.addWidget(self._synopsis)

        # ── Divider ──
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {BLUE_LIGHT};")
        form.addWidget(line)

        # ── Tombol aksi ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._cancel_btn = QPushButton("Batal")
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

        self._save_btn = QPushButton("Simpan Manga")
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

        # ── Label error ──
        self._err_lbl = QLabel("")
        self._err_lbl.setStyleSheet("color: #E53935; font-size: 12px; background: transparent;")
        self._err_lbl.setWordWrap(True)
        self._err_lbl.hide()
        form.addWidget(self._err_lbl)

        scroll.setWidget(body)
        root.addWidget(scroll)

    # ── Ambil nilai dari form ──────────────────────────────────────────────────

    def _get_genres(self) -> str:
        """Gabungkan genre utama + genre tambahan jadi satu string CSV."""
        parts = []
        main = self._genre_cb.currentData()
        if main:
            parts.append(main)
        extra = self._genres_extra.text().strip()
        if extra:
            for g in extra.split(","):
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

    # ── Simpan ────────────────────────────────────────────────────────────────

    def _on_save(self):
        self._clear_error()
        self._save_btn.setEnabled(False)
        self._save_btn.setText("Menyimpan…")

        # Validasi judul wajib diisi
        title = self._title.text().strip()
        if not title:
            self._show_error("Judul manga wajib diisi.")
            self._save_btn.setEnabled(True)
            self._save_btn.setText("Simpan Manga")
            return

        # Ambil semua nilai
        title_en   = self._title_en.text().strip() or None
        authors    = self._authors.text().strip() or None
        genres     = self._get_genres() or None
        status     = self._status.currentData()
        year       = self._year.value() if self._year.value() != 1900 else None
        chapters   = self._chapters.value() if self._chapters.value() > 0 else None
        score      = self._score.value() if self._score.value() > 0.0 else None
        cover_url  = self._cover_url.text().strip() or None
        synopsis   = self._synopsis.toPlainText().strip() or None

        try:
            from services.manga_service import MangaService
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
                score=score,
            )

            # Simpan juga title_en secara langsung (field tidak ada di add_manual,
            # kita update sesudah insert)
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

            self.manga_added.emit(manga.id)
            self.accept()  # tutup dialog dengan status Accepted

        except ValueError as e:
            self._show_error(str(e))
        except Exception as e:
            self._show_error(f"Gagal menyimpan: {e}")
        finally:
            self._save_btn.setEnabled(True)
            self._save_btn.setText("Simpan Manga")