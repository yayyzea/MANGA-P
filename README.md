# MANGA:P

Aplikasi desktop untuk menjelajahi, mengoleksi, dan mengulas manga, dibangun dengan **PyQt6** dan didukung data dari **Jikan API** (MyAnimeList). Semua data disimpan lokal menggunakan **SQLite** melalui **SQLAlchemy**.

## ✨ Fitur

- **Autentikasi pengguna** — sign up, login, dan profil (avatar, bio) untuk tiap pengguna.
- **Auto-scrape data manga** dari Jikan API:
  - Saat pertama kali dijalankan (database masih kosong), aplikasi otomatis melakukan scraping awal.
  - Tombol tambah manga baru di halaman *Most Genre* untuk mengambil data manga tambahan kapan saja.
- **Pencarian manga** berdasarkan judul, genre, status, dan tahun rilis.
- **Koleksi pribadi (Library)** — simpan manga favorit, filter berdasarkan genre/status/tahun, dan kelola (hapus) koleksi.
- **Rating & Review** — beri rating dan ulasan pada manga, lengkap dengan tag.
- **Dashboard statistik** — ringkasan koleksi pengguna dalam bentuk kartu statistik, pie chart, dan bar chart.
- **Distribusi genre (Most Genre)** — visualisasi genre dari seluruh manga yang sudah tersimpan di database.
- **Halaman detail manga** — sinopsis, penulis, skor, jumlah chapter, dan genre.
- **Halaman penulis (Author)** — lihat manga lain dari penulis yang sama.
- **Tambah manga manual** — input data manga secara manual tanpa scraping.
- **Pengaturan tampilan** — pengaturan ukuran font aplikasi.

## 🛠️ Teknologi

| Komponen        | Teknologi                     |
|------------------|-------------------------------|
| UI               | PyQt6                         |
| Database ORM     | SQLAlchemy                    |
| Database         | SQLite (`manga_p.db`)         |
| Sumber data      | Jikan API v4 (docs.api.jikan.moe) |
| HTTP client      | `requests`                    |

## 📁 Struktur Proyek

```
MANGA-P-main/
├── main.py                  # Entry point aplikasi
├── database.py               # Koneksi & inisialisasi database (SQLite)
├── signals.py                 # Custom Qt signals lintas halaman
├── migrate_and_tags.py        # Skrip migrasi tambahan
├── models/                    # Model SQLAlchemy (User, Manga, Review, UserCollection)
├── services/                  # Logic layer (auth, manga, review, collection, Jikan API)
├── ui/                        # Semua halaman & widget PyQt6
│   ├── auth_window.py / login_page.py / signup_page.py
│   ├── main_window.py / home_page.py / dashboard_page.py
│   ├── library_page.py / library_delete.py
│   ├── search_page.py / detail_page.py / author_page.py
│   ├── genre_page.py / genre_list_page.py
│   ├── rating_page.py / status_page.py
│   ├── profile_page.py / about_page.py
│   ├── add_manga_form.py / initial_scrape_dialog.py
│   └── theme.py / widgets.py / font_size_manager.py / splash_screen.py
└── assets/                    # Ikon, logo, dan aset media
```

## 🚀 Instalasi & Menjalankan

### 1. Prasyarat
- Python 3.10 atau lebih baru
- Koneksi internet (dibutuhkan untuk scraping data dari Jikan API)

### 2. Clone / salin proyek
```bash
cd MANGA-P-main
```

### 3. (Opsional) Buat virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

Dependencies utama:
```
PyQt6>=6.6.0
SQLAlchemy>=2.0.0
requests>=2.31.0
```

### 5. Jalankan aplikasi
```bash
python main.py
```

## 🗄️ Database

Database SQLite (`manga_p.db`) akan otomatis dibuat di root folder proyek saat aplikasi pertama kali dijalankan. Migrasi kolom baru dijalankan otomatis dan aman diulang (idempotent) lewat fungsi `init_db()` di `database.py`.

**Catatan:** Saat login/signup pertama kali dan database masih kosong, aplikasi akan otomatis melakukan scraping awal (sekitar 500 manga) dari Jikan API sebelum masuk ke halaman utama. Proses ini butuh koneksi internet dan bisa memakan waktu beberapa menit karena mengikuti rate limit Jikan API.

## 🌐 Tentang Jikan API

Aplikasi ini menggunakan Jikan API — API tidak resmi untuk MyAnimeList — sebagai sumber data manga (judul, sinopsis, cover, genre, skor, dll). Karena Jikan memiliki rate limit (±3 request/detik), proses scraping diberi jeda antar request untuk menghindari pemblokiran.

## 📄 Lisensi

Proyek ini dibuat untuk keperluan pembelajaran/tugas. Data manga bersumber dari MyAnimeList melalui Jikan API dan tunduk pada ketentuan penggunaan masing-masing.
