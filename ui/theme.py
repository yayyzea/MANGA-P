# MANGA:P — Central theme constants
# All UI files import from here for consistency

BLUE_PRIMARY   = "#1E90FF"
BLUE_DARK      = "#1565C0"
BLUE_SIDEBAR   = "#1976D2"
BLUE_LIGHT     = "#90CAF9"
BLUE_CARD      = "#42A5F5"
BLUE_FOOTER    = "#BBDEFB"
WHITE          = "#FFFFFF"
TEXT_DARK      = "#0D1B2A"
TEXT_MUTED     = "#546E7A"
TEXT_ON_BLUE   = "#FFFFFF"
BG_WHITE       = "#FFFFFF"
BG_PAGE        = "#F5F5F5"

SIDEBAR_WIDTH  = 80       # px  (icon-only sidebar, matches mockup)
TOPBAR_HEIGHT  = 60       # px
CARD_RADIUS    = 12       # px
CARD_W         = 140      # px  manga card width
CARD_H         = 200      # px  manga card height

FONT_FAMILY    = "Segoe UI"

# Full stylesheet applied to QApplication
APP_STYLESHEET = f"""
QWidget {{
    font-family: '{FONT_FAMILY}', Arial, sans-serif;
    color: {TEXT_DARK};
    background: {BG_WHITE};
}}

/* ── Sidebar ── */
#Sidebar {{
    background: {BLUE_PRIMARY};
    min-width: {SIDEBAR_WIDTH}px;
    max-width: {SIDEBAR_WIDTH}px;
}}

#SidebarIcon {{
    background: transparent;
    border: none;
    padding: 10px;
    border-radius: 8px;
}}
#SidebarIcon:hover {{
    background: rgba(255,255,255,0.20);
}}
#SidebarIcon:checked {{
    background: rgba(255,255,255,0.30);
}}

/* ── Top search bar ── */
#SearchBar {{
    background: {BLUE_PRIMARY};
    min-height: {TOPBAR_HEIGHT}px;
    max-height: {TOPBAR_HEIGHT}px;
    padding: 0 16px;
}}
#SearchInput {{
    background: {WHITE};
    border: none;
    border-radius: 24px;
    padding: 8px 16px 8px 40px;
    font-size: 14px;
    color: {TEXT_DARK};
}}
#SearchInput:focus {{
    outline: none;
}}
#FilterBtn {{
    background: {WHITE};
    border: none;
    border-radius: 20px;
    padding: 6px 10px;
    color: {BLUE_PRIMARY};
    font-size: 18px;
}}
#FilterBtn:hover {{
    background: {BLUE_LIGHT};
}}

/* ── Section labels ── */
#SectionLabel {{
    font-size: 16px;
    font-weight: 600;
    color: {BLUE_PRIMARY};
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
    background: {BLUE_DARK};
}}

#CardTitle {{
    color: {WHITE};
    font-size: 11px;
    font-weight: 600;
    background: transparent;
}}
#CardGenre {{
    color: rgba(255,255,255,0.80);
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
    color: {WHITE};
    font-size: 15px;
    font-weight: 700;
    background: transparent;
}}
#HistoryDesc {{
    color: rgba(255,255,255,0.90);
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
    color: {BLUE_PRIMARY};
}}

/* ── Scroll areas ── */
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    width: 6px;
    background: transparent;
}}
QScrollBar::handle:vertical {{
    background: {BLUE_LIGHT};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    height: 6px;
    background: transparent;
}}
QScrollBar::handle:horizontal {{
    background: {BLUE_LIGHT};
    border-radius: 3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""
