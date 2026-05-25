"""
signals.py — Singleton event bus.
Dipakai untuk broadcast event antar layer tanpa circular import.

Usage:
    from signals import app_signals
    app_signals.db_updated.connect(my_slot)   # di UI
    app_signals.db_updated.emit()             # di service/thread
"""
from PyQt6.QtCore import QObject, pyqtSignal


class _AppSignals(QObject):
    # Dipancarkan setiap kali MangaService._bulk_upsert berhasil commit data baru
    db_updated = pyqtSignal()


# Satu instance global — import dari mana saja dapat objek yang sama
app_signals = _AppSignals()