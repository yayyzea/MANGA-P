# MANGA:P — Central theme constants
# Color palette: 水のドレス (Mizu no Dress / Water Dress)
# Palette: Sky Blue #006ec4, Teal #2cb5d3, Dewy Green #9abe7c, Petal Pink #f96a67, Lilac Mist #c4b5de

# ── Core palette from 水のドレス ────────────────────────────────────────────
SKY_BLUE     = "#006ec4"   # deep sky blue — primary brand
TEAL         = "#2cb5d3"   # bright teal — accent / highlight
DEWY_GREEN   = "#9abe7c"   # soft sage green — secondary accent
PETAL_PINK   = "#f96a67"   # coral pink — call-to-action / alerts
LILAC_MIST   = "#c4b5de"   # soft lavender — light accent / borders

# ── Semantic aliases (keep old names so other files don't break) ──────────
BLUE_PRIMARY   = SKY_BLUE
BLUE_DARK      = "#004f9a"   # darker sky blue
BLUE_SIDEBAR   = "#005aab"   # sidebar — slightly lighter dark blue
BLUE_LIGHT     = LILAC_MIST  # soft lavender — light accent
BLUE_CARD      = "#DCF0F7"   # very light sky tint — card background
BLUE_FOOTER    = "#FCE8E8"   # blush pink — footer (petal pink tint)

WHITE          = "#FFFFFF"
BLACK          = "#000000"
TEXT_DARK      = "#111111"
TEXT_MUTED     = "#5a6e7a"
TEXT_ON_BLUE   = "#0d2a40"   # dark navy on light blue cards
BG_WHITE       = "#F4FBFF"   # lightest sky wash
BG_PAGE        = "#EBF7FF"   # gradient start — pale sky
BG_PAGE_2      = "#F0FAFD"   # gradient end — pale teal

SIDEBAR_WIDTH  = 80
TOPBAR_HEIGHT  = 60
CARD_RADIUS    = 14
CARD_W         = 140
CARD_H         = 200

FONT_FAMILY    = "Helvetica"

# Gradient helper strings (used in QSS qlineargradient)
_SIDEBAR_GRAD  = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7aaee0, stop:0.40 #82c8ef, stop:0.68 #80d9e8, stop:0.88 #b5dfa0, stop:1 #f0a8c8)"
_PAGE_GRAD     = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {BG_PAGE}, stop:0.40 #E4F5FC, stop:0.72 #FFF0F0, stop:1 #FAE8F5)"

APP_STYLESHEET = f"""
QWidget {{
    font-family: '{FONT_FAMILY}', Arial, sans-serif;
    color: {TEXT_DARK};
    background: transparent;
}}

/* ── Page background gradient ── */
#CentralWidget {{
    background: {_PAGE_GRAD};
}}

/* ── Sidebar — rich sky-to-teal gradient ── */
#Sidebar {{
    background: {_SIDEBAR_GRAD};
    min-width: {SIDEBAR_WIDTH}px;
    max-width: {SIDEBAR_WIDTH}px;
    border-right: 2px solid rgba(0,80,160,0.18);
}}

#SidebarIcon {{
    background: transparent;
    border: none;
    padding: 10px;
    border-radius: 10px;
}}
#SidebarIcon:hover {{
    background: rgba(255,255,255,0.45);
}}
#SidebarIcon:checked {{
    background: rgba(255,255,255,0.55);
    border-left: 3px solid #004f9a;
}}

/* ── Top search bar ── */
#SearchBar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {SKY_BLUE}, stop:0.55 {TEAL}, stop:1 {PETAL_PINK});
    min-height: {TOPBAR_HEIGHT}px;
    max-height: {TOPBAR_HEIGHT}px;
    padding: 0 20px;
}}
#SearchInput {{
    background: rgba(255,255,255,0.92);
    border: none;
    border-radius: 24px;
    padding: 8px 20px 8px 44px;
    font-size: 14px;
    color: {TEXT_DARK};
}}
#SearchInput:focus {{
    background: {WHITE};
    outline: none;
}}
#FilterBtn {{
    background: rgba(255,255,255,0.22);
    border: 1px solid rgba(255,255,255,0.35);
    border-radius: 20px;
    padding: 6px 10px;
    color: {WHITE};
    font-size: 18px;
}}
#FilterBtn:hover {{
    background: rgba(255,255,255,0.38);
}}

/* ── Section labels ── */
#SectionLabel {{
    font-size: 16px;
    font-weight: 700;
    color: {PETAL_PINK};
    padding: 0;
    margin: 0;
    background: transparent;
}}

/* ── Manga card ── */
#MangaCard {{
    background: {BLUE_CARD};
    border-radius: {CARD_RADIUS}px;
    border: none;
}}
#MangaCard:hover {{
    background: #FAD6E0;
}}

#MangaCard QLabel {{
    color: {TEXT_ON_BLUE};
    background: transparent;
}}

#CardTitle {{
    color: {TEXT_ON_BLUE};
    font-size: 13px;
    font-weight: 700;
    background: transparent;
}}
#CardGenre {{
    color: rgba(0,0,0,0.55);
    font-size: 10px;
    background: transparent;
}}

/* ── History panel ── */
#HistoryPanel {{
    background: {BLUE_CARD};
    border-radius: {CARD_RADIUS}px;
    padding: 12px;
}}
#HistoryTitle {{
    color: {TEXT_ON_BLUE};
    font-size: 15px;
    font-weight: 700;
    background: transparent;
}}
#HistoryDesc {{
    color: rgba(0,0,0,0.75);
    font-size: 11px;
    background: transparent;
}}

/* ── Footer ── */
#Footer {{
    background: {BLUE_FOOTER};
    min-height: 40px;
    max-height: 40px;
    padding: 0 16px;
}}
#FooterLink {{
    background: transparent;
    border: none;
    color: {BLUE_DARK};
    font-size: 12px;
    padding: 0 4px;
    text-decoration: underline;
}}
#FooterLink:hover {{
    color: {SKY_BLUE};
}}

/* ── Scroll areas ── */
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    width: 5px;
    background: transparent;
    margin: 4px 0;
}}
QScrollBar::handle:vertical {{
    background: {LILAC_MIST};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {PETAL_PINK};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    height: 5px;
    background: transparent;
}}
QScrollBar::handle:horizontal {{
    background: {LILAC_MIST};
    border-radius: 3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── Tooltips ── */
QToolTip {{
    background: {BLUE_DARK};
    color: {WHITE};
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}}
"""