# Initialiseer sessie-status
if "taal" not in st.session_state:
    st.session_state["taal"] = "NL"
if "ingelogd" not in st.session_state:
    st.session_state["ingelogd"] = False
if "historie" not in st.session_state:
    st.session_state["historie"] = []

# Vooraf ingevulde proefdata bij opstarten
if "ncage_input" not in st.session_state:
    st.session_state["ncage_input"] = "A213N"
if "mpn_input" not in st.session_state:
    st.session_state["mpn_input"] = "YS2R8X800"
if "oem_input" not in st.session_state:
    st.session_state["oem_input"] = "05677484"

"""
UID Studio™ — MIL-STD-130N & STANAG 2290 Generator & Validator
Copyright (c) 2026 Marco van Dijk. All rights reserved.

Independent software built on public standards
(MIL-STD-130N, STANAG 2290, ISO/IEC 15434 Format 06).
Unauthorized copying, distribution, or commercial reuse is prohibited.
"""

import streamlit as st
import pandas as pd
import io
import json
import re
import html
import zipfile
from urllib.parse import quote
from datetime import datetime, date
from pylibdmtx.pylibdmtx import encode, decode
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ==========================================
# LICENTIE- & CONTACTINSTELLINGEN
# ==========================================
VERLOOPDATUM = date(2026, 12, 31)     # ISO: YYYY-MM-DD
MAX_DEMO_BATCH_REGELS = 5             # Max. Excel rows in trial
CONTACT_NAAM = "Marco van Dijk"
CONTACT_EMAIL = "marco@voorbeeld.nl"  # Vul hier je zakelijke e-mailadres in
# ==========================================

# 1. Pagina configuratie (moet altijd als eerste Streamlit-commando staan)
st.set_page_config(page_title="UID Studio™ | MIL-STD-130 & STANAG 2290", layout="wide")

# Initialiseer sessie-status
if "taal" not in st.session_state:
    st.session_state["taal"] = "NL"
if "ingelogd" not in st.session_state:
    st.session_state["ingelogd"] = False
if "historie" not in st.session_state:
    st.session_state["historie"] = []

# ==========================================
# VERTALINGEN (NL / EN)
# ==========================================
TEXT = {
    "NL": {
        "expired_kicker": "UID Studio™ &nbsp;·&nbsp; Proefperiode Afgelopen",
        "expired_title": "Uw proeflicentie is verlopen",
        "expired_msg": "De proefperiode van UID Studio™ is verlopen op **{datum}**. Upgrade naar een volledige licentie voor onbeperkte batchverwerking, industriële exportformaten (SVG/PDF/ZPL) en maatwerk ERP-koppelingen.",
        "upgrade_cta": "Vraag volledige licentie aan",
        "upgrade_sub": "Onbeperkte Excel-batches · Geen verloopdatum · SVG / PDF / ZPL export",
        "login_kicker": "Enterprise Compliance &nbsp;·&nbsp; MIL-STD-130N &amp; STANAG 2290",
        "login_title": "UID Studio™",
        "login_prompt": "Voer uw toegangscode in:",
        "login_err": "❌ Onjuiste toegangscode. Toegang geweigerd.",
        "secret_err": "❌ Configuratiefout: Stel `app_wachtwoord` in via Streamlit Secrets.",
        "trust_badge": "🔒 100% In-Memory — Geen data opgeslagen",
        "sidebar_desc": "Onafhankelijke B2B-tool voor het valideren en genereren van machine-leesbare MIL-STD-130N / STANAG 2290 Data Matrix codes (ISO/IEC 15434 Format 06).",
        "sidebar_std": "📌 **UID Constructs:**\n- **Construct 2:** `CAGE + MPN + SN` (standaard voor asset management)\n- **Construct 1:** `CAGE + SN` (bij wereldwijd unieke serienummers)",
        "sidebar_demo": "⏳ **Proeflicentie actief**\n- Geldig t/m: **{datum}** ({dagen} dagen)\n- Batch-limiet: max. **{max_regels} regels** per upload",
        "header_title": "UID Studio™ — MIL-STD-130 Generator &amp; Validator",
        "tab_single": "🏷️ Enkel Label",
        "tab_batch": "📊 Batch Verwerking (Excel)",
        "sec_input": "1. Data Invoer",
        "sec_output": "2. Output & Validatie",
        "construct_lbl": "UID Construct",
        "construct_help": "Kies Construct 2 (CAGE + MPN + SN) of Construct 1 (CAGE + SN).",
        "style_lbl": "Label Uitvoering",
        "style_laser": "Laser (Wit op Zwart)",
        "style_thermal": "Thermisch (Zwart op Wit)",
        "c2_info": "ℹ️ **Construct 2:** Unieke identificatie via `CAGE/NCAGE + MPN + Serienummer`.",
        "c1_info": "ℹ️ **Construct 1:** Unieke identificatie via `CAGE/NCAGE + Serienummer` (zonder MPN).",
        "ncage_lbl": "CAGE / NCAGE-code (exact 5 tekens, bijv. A213N)",
        "mpn_lbl": "MPN / Part Number (max. 32 tekens, bijv. YS2R8X800)",
        "sn_lbl": "Serienummer / SN (max. 30 tekens, bijv. 05677484)",
        "len_err": "❌ UII-lengte overschreden: **{lengte} / 50 tekens** (MIL-STD-130 limiet).",
        "len_ok": "📏 Live UII-lengte: **{lengte} / 50 tekens** (MIL-STD-130 norm)",
        "warn_ncage": "⚠️ CAGE/NCAGE bevat spaties of ongeldige tekens.",
        "warn_mpn": "⚠️ MPN bevat spaties of ongeldige tekens.",
        "warn_sn": "⚠️ Serienummer bevat spaties of ongeldige tekens.",
        "btn_gen": "Genereer UII & Label",
        "btn_sample": "⚡ Voorbeeld",
        "btn_clear": "🔄 Wis",
        "err_fix_warns": "❌ Corrigeer eerst de waarschuwingen in de invoervelden.",
        "err_ncage_len": "❌ Fout: Een geldige CAGE/NCAGE-code moet exact 5 tekens lang zijn.",
        "err_uii_len": "❌ Fout: De totale UII mag volgens MIL-STD-130 maximaal 50 tekens lang zijn.",
        "warn_req": "⚠️ Vul alle verplichte velden in om het label te genereren.",
        "badge_decode_ok": "✓ DECODE GEVALIDEERD",
        "badge_decode_fail": "⚠ DECODE CHECK MISLUKT",
        "uii_copy_lbl": "Berekende UII (klik rechts om te kopiëren):",
        "img_caption": "Gegenereerd Label ({stijl})",
        "btn_dl_png": "⬇️ Download Label (.png)",
        "pro_export_lbl": "Industriële exportformaten (Pro):",
        "pro_tooltip": "Beschikbaar in UID Studio™ Pro — neem contact op voor een licentie.",
        "exp_syntax": "🔍 Technische Syntax (ASCII / HEX & DI's)",
        "di_title": "**Data Identifiers (Format 06):**",
        "di_sn": "Serienummer",
        "ascii_title": "**ASCII Structuur:**",
        "hex_title": "**Raw Data (HEX stuurtekens):**",
        "syntax_copy_lbl": "**ISO 15434 Syntax (kopieerbaar):**",
        "exp_json": "Machine-Readable JSON",
        "err_barcode": "❌ Fout bij genereren barcode: {e}",
        "empty_info": "👈 Vul links de gegevens in of klik op **⚡ Voorbeeld** om direct een MIL-STD-130N label te testen.\n\nAlle verwerking gebeurt volledig in het geheugen (Zero Data Retention).",
        "hist_title": "🕒 Recente Labels (Deze Sessie)",
        "btn_dl_again": "⬇️ PNG",
        "batch_title": "Batch Verwerking via Excel",
        "batch_info": "ℹ️ Geaccepteerde kolommen: **CAGE** (of `NCAGE`), **SN** (of `SERIAL`/`OEM`), optioneel **MPN** (Construct 2) en optioneel **ERP_KEY** (of `ERP_SLEUTEL`/`ASSET_ID`). *(Proefversie: max. {max_regels} regels)*",
        "batch_desc": "Regels met **MPN** worden als **Construct 2** verwerkt; zonder MPN als **Construct 1**. Voorloopnullen blijven altijd behouden.",
        "batch_style_lbl": "Stijl voor ZIP-labels",
        "btn_template": "📄 Excel-sjabloon",
        "uploader_lbl": "Sleep uw Excel-bestand (.xlsx) hierheen of klik om te bladeren",
        "err_excel_read": "❌ Kon het Excel-bestand niet lezen. Controleer of het een geldig, onbeveiligd `.xlsx`-bestand is.",
        "demo_limit_title": "Proefversie-limiet bereikt ({totaal} regels gevonden)",
        "demo_limit_msg": "In deze proefversie worden de eerste **{max_regels} regels** verwerkt. Upgrade naar **UID Studio™ Pro** voor onbeperkte batchverwerking en directe ERP-integratie.",
        "status_ok": "OK",
        "status_err_chars": "FOUT (Ongeldige tekens/spaties)",
        "status_err_limits": "FOUT (Veldlimiet: CAGE=5, MPN≤32, SN≤30, UII≤50)",
        "status_warn_dec": "WAARSCHUWING (Decode check)",
        "status_err_bc": "FOUT (Barcode)",
        "dup_warn": "⚠️ **Duplicaat-detectie:** De volgende UII('s) komen vaker voor in dit bestand: `{dups}`",
        "badge_batch": "BATCH VERWERKING",
        "badge_rows": "✓ {n} REGELS VERWERKT",
        "btn_dl_xlsx": "📥 Download Verwerkte Lijst (.xlsx)",
        "btn_dl_zip": "📦 Download Alle Labels (.zip)",
        "no_valid_zip": "ℹ️ Geen geldige labels gegenereerd om als ZIP te downloaden.",
        "err_cols": "❌ Fout: Het bestand mist de verplichte kolommen (minimaal **CAGE/NCAGE** en **SN/SERIAL/OEM**). Gebruik het sjabloon rechtsboven.",
        "footer_rights": "Alle rechten voorbehouden.",
        "footer_sub": "Onafhankelijke software op basis van openbare standaarden (MIL-STD-130N / STANAG 2290 / ISO 15434).",
        "footer_disc": "Disclaimer: Gebruik op eigen risico. De gebruiker blijft zelf verantwoordelijk voor fysieke printkwaliteit en optische verificatie (ISO/IEC 15415)."
    },
    "EN": {
        "expired_kicker": "UID Studio™ &nbsp;·&nbsp; Trial Period Ended",
        "expired_title": "Your trial license has expired",
        "expired_msg": "The trial period for UID Studio™ ended on **{datum}**. Upgrade to a full license for unlimited batch processing, industrial export formats (SVG/PDF/ZPL), and custom ERP integration.",
        "upgrade_cta": "Request Full License",
        "upgrade_sub": "Unlimited Excel batches · No expiry date · SVG / PDF / ZPL export",
        "login_kicker": "Enterprise Compliance &nbsp;·&nbsp; MIL-STD-130N &amp; STANAG 2290",
        "login_title": "UID Studio™",
        "login_prompt": "Enter your access code:",
        "login_err": "❌ Incorrect access code. Access denied.",
        "secret_err": "❌ Configuration error: Set `app_wachtwoord` in Streamlit Secrets.",
        "trust_badge": "🔒 100% In-Memory — Zero Data Stored",
        "sidebar_desc": "Independent B2B tool for validating and generating machine-readable MIL-STD-130N / STANAG 2290 Data Matrix codes (ISO/IEC 15434 Format 06).",
        "sidebar_std": "📌 **UID Constructs:**\n- **Construct 2:** `CAGE + MPN + SN` (standard for asset management)\n- **Construct 1:** `CAGE + SN` (for globally unique serial numbers)",
        "sidebar_demo": "⏳ **Trial License Active**\n- Valid until: **{datum}** ({dagen} days)\n- Batch limit: max. **{max_regels} rows** per upload",
        "header_title": "UID Studio™ — MIL-STD-130 Generator &amp; Validator",
        "tab_single": "🏷️ Single Label",
        "tab_batch": "📊 Batch Processing (Excel)",
        "sec_input": "1. Data Input",
        "sec_output": "2. Output & Validation",
        "construct_lbl": "UID Construct",
        "construct_help": "Select Construct 2 (CAGE + MPN + SN) or Construct 1 (CAGE + SN).",
        "style_lbl": "Label Style",
        "style_laser": "Laser (White on Black)",
        "style_thermal": "Thermal (Black on White)",
        "c2_info": "ℹ️ **Construct 2:** Unique identification via `CAGE/NCAGE + MPN + Serial Number`.",
        "c1_info": "ℹ️ **Construct 1:** Unique identification via `CAGE/NCAGE + Serial Number` (no MPN).",
        "ncage_lbl": "CAGE / NCAGE Code (exact 5 chars, e.g. A213N)",
        "mpn_lbl": "MPN / Part Number (max. 32 chars, e.g. YS2R8X800)",
        "sn_lbl": "Serial Number / SN (max. 30 chars, e.g. 05677484)",
        "len_err": "❌ UII length exceeded: **{lengte} / 50 characters** (MIL-STD-130 limit).",
        "len_ok": "📏 Live UII length: **{lengte} / 50 characters** (MIL-STD-130 standard)",
        "warn_ncage": "⚠️ CAGE/NCAGE contains spaces or invalid characters.",
        "warn_mpn": "⚠️ MPN contains spaces or invalid characters.",
        "warn_sn": "⚠️ Serial number contains spaces or invalid characters.",
        "btn_gen": "Generate UII & Label",
        "btn_sample": "⚡ Sample",
        "btn_clear": "🔄 Clear",
        "err_fix_warns": "❌ Please resolve the warnings in the input fields first.",
        "err_ncage_len": "❌ Error: A valid CAGE/NCAGE code must be exactly 5 characters long.",
        "err_uii_len": "❌ Error: Total UII length cannot exceed 50 characters per MIL-STD-130.",
        "warn_req": "⚠️ Please fill in all required fields to generate the label.",
        "badge_decode_ok": "✓ DECODE VERIFIED",
        "badge_decode_fail": "⚠ DECODE CHECK FAILED",
        "uii_copy_lbl": "Calculated UII (click icon on the right to copy):",
        "img_caption": "Generated Label ({stijl})",
        "btn_dl_png": "⬇️ Download Label (.png)",
        "pro_export_lbl": "Industrial export formats (Pro):",
        "pro_tooltip": "Available in UID Studio™ Pro — contact us for a license.",
        "exp_syntax": "🔍 Technical Syntax (ASCII / HEX & DIs)",
        "di_title": "**Data Identifiers (Format 06):**",
        "di_sn": "Serial Number",
        "ascii_title": "**ASCII Structure:**",
        "hex_title": "**Raw Data (HEX control characters):**",
        "syntax_copy_lbl": "**ISO 15434 Syntax (copyable):**",
        "exp_json": "Machine-Readable JSON",
        "err_barcode": "❌ Error generating barcode: {e}",
        "empty_info": "👈 Enter your asset data on the left or click **⚡ Sample** to test a MIL-STD-130N label right away.\n\nAll processing runs strictly in-memory (Zero Data Retention).",
        "hist_title": "🕒 Recent Labels (This Session)",
        "btn_dl_again": "⬇️ PNG",
        "batch_title": "Batch Processing via Excel",
        "batch_info": "ℹ️ Accepted columns: **CAGE** (or `NCAGE`), **SN** (or `SERIAL`/`OEM`), optional **MPN** (Construct 2), and optional **ERP_KEY** (or `ASSET_ID`/`ERP_SLEUTEL`). *(Trial: max. {max_regels} rows)*",
        "batch_desc": "Rows with **MPN** are processed as **Construct 2**; without MPN as **Construct 1**. Leading zeros are always preserved.",
        "batch_style_lbl": "Style for ZIP labels",
        "btn_template": "📄 Excel Template",
        "uploader_lbl": "Drag and drop your Excel file (.xlsx) here or click to browse",
        "err_excel_read": "❌ Could not read the Excel file. Please verify it is a valid, unprotected `.xlsx` file.",
        "demo_limit_title": "Trial limit reached ({totaal} rows found)",
        "demo_limit_msg": "In this trial version, only the first **{max_regels} rows** are processed. Upgrade to **UID Studio™ Pro** for unlimited batch processing and direct ERP integration.",
        "status_ok": "OK",
        "status_err_chars": "ERROR (Invalid characters/spaces)",
        "status_err_limits": "ERROR (Field limits: CAGE=5, MPN≤32, SN≤30, UII≤50)",
        "status_warn_dec": "WARNING (Decode check)",
        "status_err_bc": "ERROR (Barcode)",
        "dup_warn": "⚠️ **Duplicate detection:** The following UII(s) appear multiple times in this file: `{dups}`",
        "badge_batch": "BATCH PROCESSING",
        "badge_rows": "✓ {n} ROWS PROCESSED",
        "btn_dl_xlsx": "📥 Download Processed List (.xlsx)",
        "btn_dl_zip": "📦 Download All Labels (.zip)",
        "no_valid_zip": "ℹ️ No valid labels were generated for ZIP download.",
        "err_cols": "❌ Error: The uploaded file is missing required columns (at least **CAGE/NCAGE** and **SN/SERIAL/OEM**). Use the template above.",
        "footer_rights": "All rights reserved.",
        "footer_sub": "Independent software built on public standards (MIL-STD-130N / STANAG 2290 / ISO 15434).",
        "footer_disc": "Disclaimer: Use at your own risk. The user remains responsible for physical print quality and optical verification (ISO/IEC 15415)."
    }
}

def get_app_password():
    """Haalt veilig het wachtwoord op uit Streamlit Secrets (met fallback voor migratie)."""
    try:
        if "app_wachtwoord" in st.secrets:
            return st.secrets["app_wachtwoord"]
        if "dmd_wachtwoord" in st.secrets:
            return st.secrets["dmd_wachtwoord"]
    except Exception:
        pass
    return None

def render_upgrade_card(title, body, cta_label, sub_text):
    """Toont een commerciële B2B upgrade-kaart met directe mailto-knop."""
    subject = quote("UID Studio Pro License Inquiry")
    mailto_link = f"mailto:{CONTACT_EMAIL}?subject={subject}"
    st.markdown(f"""
        <div class="upgrade-card">
            <div class="upgrade-content">
                <div class="upgrade-title">🚀 {html.escape(title)}</div>
                <div class="upgrade-body">{body}</div>
                <div class="upgrade-sub">{html.escape(sub_text)}</div>
            </div>
            <a href="{mailto_link}" class="upgrade-btn">{html.escape(cta_label)} →</a>
        </div>
    """, unsafe_allow_html=True)

# 2. Moderne B2B SaaS Styling (CSS Injectie + Subtiel Watermerk)
st.markdown("""
<style>
    [data-testid="stToolbar"] { visibility: hidden; }
    .stApp {
        background-color: #F8FAFC;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='320' height='220' viewBox='0 0 320 220'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' transform='rotate(-25 160 110)' fill='%230F172A' fill-opacity='0.035' font-family='sans-serif' font-size='22' font-weight='700' letter-spacing='3'%3EUID STUDIO%E2%84%A2%3C/text%3E%3C/svg%3E");
        background-repeat: repeat;
    }
    [data-testid="stSidebar"] {
        background-color: #F1F5F9;
        border-right: 1px solid #E2E8F0;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
    }
    .stButton > button,
    .stDownloadButton > button,
    .stTextInput > div > div > input,
    [data-testid="stFileUploader"] section {
        border-radius: 6px !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        padding: 1.25rem !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
    }
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"] {
        background-color: #2563EB;
        border-color: #2563EB;
        color: #FFFFFF;
    }
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {
        background-color: #1D4ED8;
        border-color: #1D4ED8;
        color: #FFFFFF;
    }
    .stButton > button, .stDownloadButton > button {
        min-height: 2.7rem;
        font-weight: 600;
        letter-spacing: 0.2px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        color: #475569;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-bottom: 3px solid #2563EB !important;
    }
    .app-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 1.3rem 1.8rem;
        border-bottom: 3px solid #2563EB;
        margin-bottom: 1.2rem;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }
    .app-kicker {
        color: #60A5FA;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.4px;
        text-transform: uppercase;
        display: block;
        margin-bottom: 0.25rem;
    }
    .app-title {
        color: #FFFFFF;
        font-size: 1.65rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
    }
    .trust-pill {
        background-color: rgba(16, 185, 129, 0.14);
        color: #6EE7B7;
        border: 1px solid rgba(16, 185, 129, 0.35);
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        white-space: nowrap;
    }
    .badge-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 0.8rem;
    }
    .badge {
        display: inline-block;
        padding: 3px 9px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        border-radius: 4px;
        background-color: #EFF6FF;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
    }
    .badge-ok {
        background-color: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
    }
    .badge-warn {
        background-color: #FFFBEB;
        color: #92400E;
        border: 1px solid #FDE68A;
    }
    .upgrade-card {
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-left: 4px solid #2563EB;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 0.8rem 0 1rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 14px;
    }
    .upgrade-title {
        font-size: 15px;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 4px;
    }
    .upgrade-body {
        font-size: 13.5px;
        color: #334155;
        margin-bottom: 4px;
    }
    .upgrade-sub {
        font-size: 12px;
        color: #64748B;
        font-weight: 500;
    }
    .upgrade-btn {
        background-color: #2563EB;
        color: #FFFFFF !important;
        text-decoration: none !important;
        padding: 9px 16px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        white-space: nowrap;
    }
    .upgrade-btn:hover {
        background-color: #1D4ED8;
    }
    .syntax-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 10px 12px;
        font-family: monospace;
        font-size: 13px;
        line-height: 1.8;
        word-break: break-all;
        margin-bottom: 8px;
    }
    .tok-hdr { background-color: #E2E8F0; color: #0F172A; padding: 2px 5px; border-radius: 3px; font-weight: 700; }
    .tok-ctrl { background-color: #FEE2E2; color: #991B1B; padding: 2px 4px; border-radius: 3px; font-size: 11px; font-weight: 700; }
    .tok-17v { background-color: #DBEAFE; color: #1E40AF; padding: 2px 5px; border-radius: 3px; font-weight: 700; }
    .tok-1p { background-color: #F3E8FF; color: #6B21A8; padding: 2px 5px; border-radius: 3px; font-weight: 700; }
    .tok-s { background-color: #DCFCE7; color: #166534; padding: 2px 5px; border-radius: 3px; font-weight: 700; }
    .di-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
        font-size: 13px;
    }
    hr {
        margin-top: 0.7rem !important;
        margin-bottom: 0.7rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Taalschakelaar op inlog- of verlopen-scherm (neutraal zonder vlaggen)
vandaag = date.today()
iso_verloop = VERLOOPDATUM.strftime("%Y-%m-%d")

if vandaag > VERLOOPDATUM or not st.session_state["ingelogd"]:
    _, lang_col = st.columns([5.5, 1.2])
    with lang_col:
        st.radio(
            "🌐 Language",
            ["NL", "EN"],
            horizontal=True,
            key="taal",
            format_func=lambda x: f"🌐 {x}",
            label_visibility="collapsed"
        )

lang = st.session_state["taal"]
T = TEXT[lang]

# --- CONTROLE VERLOOPDATUM ---
if vandaag > VERLOOPDATUM:
    st.markdown(f"""
        <div class="app-header">
            <div>
                <span class="app-kicker">{T['expired_kicker']}</span>
                <div class="app-title">{T['expired_title']}</div>
            </div>
            <div class="trust-pill">{T['trust_badge']}</div>
        </div>
    """, unsafe_allow_html=True)
    render_upgrade_card(
        title=T["expired_title"],
        body=T["expired_msg"].format(datum=iso_verloop).replace("**", ""),
        cta_label=T["upgrade_cta"],
        sub_text=T["upgrade_sub"]
    )
    st.stop()
# --- EINDE CONTROLE VERLOOPDATUM ---

# --- BEVEILIGING ---
if not st.session_state["ingelogd"]:
    st.markdown(f"""
        <div class="app-header">
            <div>
                <span class="app-kicker">{T['login_kicker']}</span>
                <div class="app-title">{T['login_title']}</div>
            </div>
            <div class="trust-pill">{T['trust_badge']}</div>
        </div>
    """, unsafe_allow_html=True)
    juiste_wachtwoord = get_app_password()
    if juiste_wachtwoord is None:
        st.error(T["secret_err"])
        st.stop()

    wachtwoord = st.text_input(T["login_prompt"], type="password")
    if wachtwoord == juiste_wachtwoord:
        st.session_state["ingelogd"] = True
        st.rerun()
    else:
        if wachtwoord != "":
            st.error(T["login_err"])
        st.stop()
# --- EINDE BEVEILIGING ---

# --- HULPFUNCTIES ---
def wis_velden():
    st.session_state["ncage_input"] = ""
    st.session_state["mpn_input"] = ""
    st.session_state["oem_input"] = ""

def vul_voorbeelddata():
    st.session_state["ncage_input"] = "A213N"
    st.session_state["mpn_input"] = "YS2R8X800"
    st.session_state["oem_input"] = "05677484"

def bevat_ongeldige_tekens(tekst):
    return bool(re.search(r'[^A-Za-z0-9\-/]', tekst))

def vind_kolom(kolommen, aliassen):
    """Zoekt de eerste passende kolomnaam uit een lijst van internationale aliassen."""
    for alias in aliassen:
        if alias in kolommen:
            return alias
    return None

def bouw_kleur_syntax_html(ncage_clean, mpn_clean, oem_clean, sn_label, construct="Construct 2"):
    """Bouwt een kleurgecodeerde ASCII en HEX weergave met HTML-escaping tegen XSS."""
    ncage_esc = html.escape(ncage_clean)
    mpn_esc = html.escape(mpn_clean)
    oem_esc = html.escape(oem_clean)
    sn_lbl_esc = html.escape(sn_label)

    if construct == "Construct 2":
        ascii_html = (
            '<span class="tok-hdr">[)&gt;</span>'
            '<span class="tok-ctrl">RS</span>'
            '<span class="tok-hdr">06</span>'
            '<span class="tok-ctrl">GS</span>'
            f'<span class="tok-17v">17V{ncage_esc}</span>'
            '<span class="tok-ctrl">GS</span>'
            f'<span class="tok-1p">1P{mpn_esc}</span>'
            '<span class="tok-ctrl">GS</span>'
            f'<span class="tok-s">S{oem_esc}</span>'
            '<span class="tok-ctrl">RS</span>'
            '<span class="tok-ctrl">EOT</span>'
        )
        hex_str = f"[)&gt;&lt;0x1E&gt;06&lt;0x1D&gt;17V{ncage_esc}&lt;0x1D&gt;1P{mpn_esc}&lt;0x1D&gt;S{oem_esc}&lt;0x1E&gt;&lt;0x04&gt;"
        di_html = (
            f'<div class="di-row"><span class="tok-17v">17V</span> <strong>CAGE / NCAGE:</strong> {ncage_esc}</div>'
            f'<div class="di-row"><span class="tok-1p">1P</span> <strong>MPN:</strong> {mpn_esc}</div>'
            f'<div class="di-row"><span class="tok-s">S</span> <strong>{sn_lbl_esc}:</strong> {oem_esc}</div>'
        )
    else:
        ascii_html = (
            '<span class="tok-hdr">[)&gt;</span>'
            '<span class="tok-ctrl">RS</span>'
            '<span class="tok-hdr">06</span>'
            '<span class="tok-ctrl">GS</span>'
            f'<span class="tok-17v">17V{ncage_esc}</span>'
            '<span class="tok-ctrl">GS</span>'
            f'<span class="tok-s">S{oem_esc}</span>'
            '<span class="tok-ctrl">RS</span>'
            '<span class="tok-ctrl">EOT</span>'
        )
        hex_str = f"[)&gt;&lt;0x1E&gt;06&lt;0x1D&gt;17V{ncage_esc}&lt;0x1D&gt;S{oem_esc}&lt;0x1E&gt;&lt;0x04&gt;"
        di_html = (
            f'<div class="di-row"><span class="tok-17v">17V</span> <strong>CAGE / NCAGE:</strong> {ncage_esc}</div>'
            f'<div class="di-row"><span class="tok-s">S</span> <strong>{sn_lbl_esc}:</strong> {oem_esc}</div>'
        )
    return ascii_html, hex_str, di_html

def laad_passend_font(draw, regels, max_breedte_px=380, start_grootte=36, min_grootte=16):
    """Schaalt het lettertype automatisch omlaag zodat lange tekst nooit de Data Matrix overlapt."""
    font_pad = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    for grootte in range(start_grootte, min_grootte - 1, -2):
        try:
            font = ImageFont.truetype(font_pad, grootte)
        except Exception:
            return ImageFont.load_default()
        if max(draw.textlength(r, font=font) for r in regels) <= max_breedte_px:
            return font
    try:
        return ImageFont.truetype(font_pad, min_grootte)
    except Exception:
        return ImageFont.load_default()

def genereer_label_afbeelding(ncage_clean, mpn_clean, oem_clean, syntax_string, is_laser=True, construct="Construct 2"):
    """Genereert het label (PNG Image) met gegarandeerde Quiet Zone én decode self-check."""
    barcode_data = syntax_string.replace('[RS]', chr(30)).replace('[GS]', chr(29)).replace('[EOT]', chr(4))
    
    encoded = encode(barcode_data.encode('utf-8'))
    img_raw = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
    
    decode_ok = False
    try:
        check_img = ImageOps.expand(img_raw, border=20, fill='white')
        decoded_objs = decode(check_img)
        if decoded_objs and decoded_objs[0].data.decode('utf-8') == barcode_data:
            decode_ok = True
    except Exception:
        decode_ok = False

    max_grootte = 260
    schaalfactor = max(1, min(max_grootte // img_raw.width, max_grootte // img_raw.height))
    img_barcode = img_raw.resize(
        (img_raw.width * schaalfactor, img_raw.height * schaalfactor),
        Image.Resampling.NEAREST
    )

    achtergrond = 'black' if is_laser else 'white'
    tekstkleur = 'white' if is_laser else 'black'
    if is_laser:
        img_barcode = ImageOps.invert(img_barcode)

    label_img = Image.new('RGB', (750, 350), color=achtergrond)
    x_pos_barcode = 750 - img_barcode.width - 45
    y_pos_barcode = (350 - img_barcode.height) // 2
    label_img.paste(img_barcode, (x_pos_barcode, y_pos_barcode))

    draw = ImageDraw.Draw(label_img)
    if not is_laser:
        draw.rectangle([(0, 0), (749, 349)], outline="#CBD5E1", width=2)

    regels = [f"CAGE:  {ncage_clean}"]
    if construct == "Construct 2" and mpn_clean:
        regels.append(f"MPN:   {mpn_clean}")
    regels.append(f"SN:    {oem_clean}")

    max_tekst_breedte = max(200, x_pos_barcode - 75)
    font = laad_passend_font(draw, regels, max_breedte_px=max_tekst_breedte)

    start_y = 75 if len(regels) == 3 else 110
    stap_y = 80
    for idx, regel in enumerate(regels):
        draw.text((45, start_y + idx * stap_y), regel, fill=tekstkleur, font=font)

    return label_img, decode_ok

# 3. Zijbalk (Neutrale Taalschakelaar, Product info, Trust & Licentiestatus)
dagen_over = (VERLOOPDATUM - vandaag).days
with st.sidebar:
    st.radio(
        "🌐 Language / Taal",
        ["NL", "EN"],
        horizontal=True,
        key="taal",
        format_func=lambda x: f"🌐 {x}",
        label_visibility="collapsed"
    )
    lang = st.session_state["taal"]
    T = TEXT[lang]

    st.markdown("---")
    st.header("UID Studio™")
    st.write(T["sidebar_desc"])
    st.success(T["trust_badge"])
    st.info(T["sidebar_std"])
    st.warning(T["sidebar_demo"].format(datum=iso_verloop, dagen=dagen_over, max_regels=MAX_DEMO_BATCH_REGELS))
    st.markdown("---")
    st.caption("**UID Studio™**")
    st.caption("Version: v3.0 (B2B International)")
    st.caption(f"© 2026 {CONTACT_NAAM}")

# 4. Moderne B2B Header Banner met Zero Data Retention Trust Badge
st.markdown(f"""
    <div class="app-header">
        <div>
            <span class="app-kicker">{T['login_kicker']}</span>
            <div class="app-title">{T['header_title']}</div>
        </div>
        <div class="trust-pill">{T['trust_badge']}</div>
    </div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs([T["tab_single"], T["tab_batch"]])

# ==========================================
# TAB 1: ENKEL LABEL
# ==========================================
with tab1:
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        with st.container(border=True):
            st.subheader(T["sec_input"])
            
            opt_col1, opt_col2 = st.columns(2)
            with opt_col1:
                construct_keuze = st.radio(
                    T["construct_lbl"],
                    ["Construct 2", "Construct 1"],
                    horizontal=True,
                    help=T["construct_help"]
                )
            with opt_col2:
                stijl_opties = [T["style_laser"], T["style_thermal"]]
                label_stijl = st.radio(T["style_lbl"], stijl_opties, horizontal=True)
                is_laser_single = (label_stijl == T["style_laser"])

            st.caption(T["c2_info"] if construct_keuze == "Construct 2" else T["c1_info"])

            ncage = st.text_input(T["ncage_lbl"], max_chars=5, key="ncage_input")
            
            if construct_keuze == "Construct 2":
                mpn = st.text_input(T["mpn_lbl"], max_chars=32, key="mpn_input")
            else:
                mpn = ""
                
            oem = st.text_input(T["sn_lbl"], max_chars=30, key="oem_input")

            huidige_uii_lengte = 1 + len(ncage.strip()) + (len(mpn.strip()) if construct_keuze == "Construct 2" else 0) + len(oem.strip())
            if huidige_uii_lengte > 50:
                st.error(T["len_err"].format(lengte=huidige_uii_lengte))
            else:
                st.caption(T["len_ok"].format(lengte=huidige_uii_lengte))

            invoer_fout = False
            if ncage and bevat_ongeldige_tekens(ncage):
                st.warning(T["warn_ncage"])
                invoer_fout = True
            if construct_keuze == "Construct 2" and mpn and bevat_ongeldige_tekens(mpn):
                st.warning(T["warn_mpn"])
                invoer_fout = True
            if oem and bevat_ongeldige_tekens(oem):
                st.warning(T["warn_sn"])
                invoer_fout = True

            btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 0.9])
            with btn_col1:
                generate_btn = st.button(T["btn_gen"], type="primary", use_container_width=True)
            with btn_col2:
                st.button(T["btn_sample"], on_click=vul_voorbeelddata, use_container_width=True)
            with btn_col3:
                st.button(T["btn_clear"], on_click=wis_velden, use_container_width=True)

    with col2:
        with st.container(border=True):
            st.subheader(T["sec_output"])
            
            if generate_btn:
                verplicht_ok = bool(ncage and oem and (mpn if construct_keuze == "Construct 2" else True))
                if verplicht_ok:
                    if invoer_fout:
                        st.error(T["err_fix_warns"])
                    elif len(ncage) != 5:
                        st.error(T["err_ncage_len"])
                    elif huidige_uii_lengte > 50:
                        st.error(T["err_uii_len"])
                    else:
                        ncage_clean = ncage.upper()
                        mpn_clean = mpn.upper()
                        oem_clean = oem.upper()

                        if construct_keuze == "Construct 2":
                            uii = f"D{ncage_clean}{mpn_clean}{oem_clean}"
                            syntax_string = f"[)>[RS]06[GS]17V{ncage_clean}[GS]1P{mpn_clean}[GS]S{oem_clean}[RS][EOT]"
                        else:
                            uii = f"D{ncage_clean}{oem_clean}"
                            syntax_string = f"[)>[RS]06[GS]17V{ncage_clean}[GS]S{oem_clean}[RS][EOT]"

                        try:
                            label_img, decode_ok = genereer_label_afbeelding(
                                ncage_clean, mpn_clean, oem_clean, syntax_string,
                                is_laser=is_laser_single, construct=construct_keuze
                            )

                            virtueel_bestand = io.BytesIO()
                            label_img.save(virtueel_bestand, format="PNG")
                            bytes_data = virtueel_bestand.getvalue()

                            st.session_state["historie"].insert(0, {
                                "tijd": datetime.now().strftime("%H:%M:%S"),
                                "uii": uii,
                                "construct": construct_keuze,
                                "stijl": label_stijl,
                                "png_bytes": bytes_data
                            })
                            st.session_state["historie"] = st.session_state["historie"][:5]

                            decode_badge = (
                                f'<span class="badge badge-ok">{T["badge_decode_ok"]}</span>'
                                if decode_ok else
                                f'<span class="badge badge-warn">{T["badge_decode_fail"]}</span>'
                            )
                            st.markdown(f"""
                                <div class="badge-row">
                                    <span class="badge">MIL-STD-130N</span>
                                    <span class="badge">FORMAT 06</span>
                                    <span class="badge">{construct_keuze.upper()}</span>
                                    {decode_badge}
                                </div>
                            """, unsafe_allow_html=True)

                            # Eén-klik kopiëren voor de berekende UII
                            st.caption(T["uii_copy_lbl"])
                            st.code(uii, language=None)

                            st.image(label_img, caption=T["img_caption"].format(stijl=label_stijl), width=460)
                            
                            st.download_button(
                                label=T["btn_dl_png"],
                                data=bytes_data,
                                file_name=f"Label_{uii}.png",
                                mime="image/png",
                                type="primary",
                                use_container_width=True
                            )

                            # Industriële Pro-exportformaten (Roadmap / Conversie)
                            st.caption(T["pro_export_lbl"])
                            pro_c1, pro_c2, pro_c3 = st.columns(3)
                            with pro_c1:
                                st.button("SVG (Vector) 🔒", disabled=True, help=T["pro_tooltip"], use_container_width=True)
                            with pro_c2:
                                st.button("PDF (Print) 🔒", disabled=True, help=T["pro_tooltip"], use_container_width=True)
                            with pro_c3:
                                st.button("ZPL (Zebra) 🔒", disabled=True, help=T["pro_tooltip"], use_container_width=True)

                            ascii_html, hex_str, di_html = bouw_kleur_syntax_html(
                                ncage_clean, mpn_clean, oem_clean, sn_label=T["di_sn"], construct=construct_keuze
                            )
                            with st.expander(T["exp_syntax"]):
                                st.markdown(T["di_title"])
                                st.markdown(di_html, unsafe_allow_html=True)
                                st.markdown(T["ascii_title"])
                                st.markdown(f'<div class="syntax-box">{ascii_html}</div>', unsafe_allow_html=True)
                                st.markdown(T["hex_title"])
                                st.markdown(f'<div class="syntax-box">{hex_str}</div>', unsafe_allow_html=True)
                                st.markdown(T["syntax_copy_lbl"])
                                st.code(syntax_string, language=None)

                            output_data = {
                                "uii": uii,
                                "construct": construct_keuze,
                                "cage": ncage_clean,
                                "mpn": mpn_clean if construct_keuze == "Construct 2" else None,
                                "serial_number": oem_clean,
                                "iso_15434_syntax": syntax_string,
                                "decode_verified": decode_ok
                            }
                            with st.expander(T["exp_json"]):
                                st.json(output_data)

                        except Exception as e:
                            st.error(T["err_barcode"].format(e=e))
                else:
                    st.warning(T["warn_req"])
            else:
                st.markdown("""
                    <div class="badge-row">
                        <span class="badge">MIL-STD-130N</span>
                        <span class="badge">FORMAT 06</span>
                        <span class="badge">ECC 200</span>
                    </div>
                """, unsafe_allow_html=True)
                st.info(T["empty_info"])

    # Sessie-historie onderaan Tab 1
    if st.session_state["historie"]:
        with st.container(border=True):
            st.subheader(T["hist_title"])
            for idx, item in enumerate(st.session_state["historie"]):
                h_col1, h_col2, h_col3 = st.columns([3, 2.2, 1.2])
                with h_col1:
                    st.markdown(f"**`{item['uii']}`**")
                with h_col2:
                    st.caption(f"{item['tijd']} · {item['construct']} · {item['stijl']}")
                with h_col3:
                    st.download_button(
                        label=T["btn_dl_again"],
                        data=item["png_bytes"],
                        file_name=f"Label_{item['uii']}.png",
                        mime="image/png",
                        key=f"hist_dl_{idx}",
                        use_container_width=True
                    )

# ==========================================
# TAB 2: BATCH INVOER (EXCEL)
# ==========================================
with tab2:
    with st.container(border=True):
        st.subheader(T["batch_title"])
        st.info(T["batch_info"].format(max_regels=MAX_DEMO_BATCH_REGELS))
        
        # Internationaal sjabloon (met ondersteuning voor NL aliassen bij upload)
        sjabloon_df = pd.DataFrame({
            "ERP_KEY": ["10004582"],
            "CAGE": ["A213N"],
            "MPN": ["YS2R8X800"],
            "SN": ["05677484"]
        })
        sjabloon_buffer = io.BytesIO()
        with pd.ExcelWriter(sjabloon_buffer, engine='openpyxl') as writer:
            sjabloon_df.to_excel(writer, index=False)
        
        col_info, col_stijl, col_sjabloon = st.columns([2.5, 1.5, 1.2])
        with col_info:
            st.write(T["batch_desc"])
        with col_stijl:
            batch_stijl = st.selectbox(T["batch_style_lbl"], [T["style_laser"], T["style_thermal"]])
            is_laser_batch = (batch_stijl == T["style_laser"])
        with col_sjabloon:
            st.download_button(
                label=T["btn_template"],
                data=sjabloon_buffer.getvalue(),
                file_name="UID_Studio_Template.xlsx" if lang == "EN" else "UID_Studio_Sjabloon.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        excel_bestand = st.file_uploader(T["uploader_lbl"], type=["xlsx"])

        if excel_bestand is not None:
            try:
                df = pd.read_excel(excel_bestand, dtype=str)
            except Exception:
                st.error(T["err_excel_read"])
                st.stop()

            df.columns = df.columns.str.strip().str.upper()

            # Internationale & Nederlandse kolom-aliassen automatisch herkennen
            col_cage = vind_kolom(df.columns, ["CAGE", "NCAGE", "CAGE_CODE", "NCAGE_CODE"])
            col_sn = vind_kolom(df.columns, ["SN", "SERIAL", "SERIAL_NUMBER", "SERIENUMMER", "OEM"])
            col_mpn = vind_kolom(df.columns, ["MPN", "PART_NUMBER", "PART_NO", "PN", "P/N"])
            col_key = vind_kolom(df.columns, ["ERP_KEY", "ERP_SLEUTEL", "ASSET_ID", "EQUIPMENT_ID", "KEY"])
            
            if col_cage and col_sn:
                # Verwijder volledig lege rijen vóór de demo-limiet
                df = df.replace(r'^\s*$', pd.NA, regex=True).dropna(how="all")

                totaal_regels = len(df)
                if totaal_regels > MAX_DEMO_BATCH_REGELS:
                    render_upgrade_card(
                        title=T["demo_limit_title"].format(totaal=totaal_regels),
                        body=T["demo_limit_msg"].format(max_regels=MAX_DEMO_BATCH_REGELS).replace("**", ""),
                        cta_label=T["upgrade_cta"],
                        sub_text=T["upgrade_sub"]
                    )
                    df = df.head(MAX_DEMO_BATCH_REGELS)

                resultaten = []
                zip_buffer = io.BytesIO()
                geldige_labels_count = 0

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for index, row in df.iterrows():
                        sleutel_raw = str(row[col_key]).strip() if (col_key and pd.notna(row[col_key])) else ""
                        sleutel_clean = "" if sleutel_raw.upper() in ("NAN", "NONE") else sleutel_raw

                        ncage_raw = str(row[col_cage]).strip().upper() if pd.notna(row[col_cage]) else ""
                        oem_raw = str(row[col_sn]).strip().upper() if pd.notna(row[col_sn]) else ""
                        mpn_raw = str(row[col_mpn]).strip().upper() if (col_mpn and pd.notna(row[col_mpn])) else ""

                        ncage_clean = "" if ncage_raw in ("NAN", "NONE") else ncage_raw
                        mpn_clean = "" if mpn_raw in ("NAN", "NONE") else mpn_raw
                        oem_clean = "" if oem_raw in ("NAN", "NONE") else oem_raw

                        if not (ncage_clean or mpn_clean or oem_clean):
                            continue

                        if mpn_clean:
                            construct_type = "Construct 2"
                            uii = f"D{ncage_clean}{mpn_clean}{oem_clean}"
                            syntax_string = f"[)>[RS]06[GS]17V{ncage_clean}[GS]1P{mpn_clean}[GS]S{oem_clean}[RS][EOT]"
                        else:
                            construct_type = "Construct 1"
                            uii = f"D{ncage_clean}{oem_clean}"
                            syntax_string = f"[)>[RS]06[GS]17V{ncage_clean}[GS]S{oem_clean}[RS][EOT]"

                        tekens_ok = not (
                            bevat_ongeldige_tekens(ncage_clean)
                            or (mpn_clean and bevat_ongeldige_tekens(mpn_clean))
                            or bevat_ongeldige_tekens(oem_clean)
                        )
                        limieten_ok = (
                            len(ncage_clean) == 5
                            and len(mpn_clean) <= 32
                            and 1 <= len(oem_clean) <= 30
                            and len(uii) <= 50
                        )

                        if not tekens_ok:
                            status = T["status_err_chars"]
                        elif not limieten_ok:
                            status = T["status_err_limits"]
                        else:
                            status = T["status_ok"]
                            try:
                                img, decode_ok = genereer_label_afbeelding(
                                    ncage_clean, mpn_clean, oem_clean, syntax_string,
                                    is_laser=is_laser_batch, construct=construct_type
                                )
                                img_bytes = io.BytesIO()
                                img.save(img_bytes, format="PNG")
                                zf.writestr(f"Label_{index+1}_{uii}.png", img_bytes.getvalue())
                                geldige_labels_count += 1
                                if not decode_ok:
                                    status = T["status_warn_dec"]
                            except Exception:
                                status = T["status_err_bc"]

                        rij_resultaat = {}
                        if col_key:
                            rij_resultaat[col_key] = sleutel_clean

                        rij_resultaat.update({
                            "CAGE": ncage_clean,
                            "MPN": mpn_clean,
                            "SN": oem_clean,
                            "Construct": construct_type,
                            "UII": uii if (tekens_ok and limieten_ok) else "",
                            "Length" if lang == "EN" else "Lengte": len(uii) if (tekens_ok and limieten_ok) else 0,
                            "Status": status,
                            "ISO 15434 Syntax": syntax_string if (tekens_ok and limieten_ok) else ""
                        })
                        resultaten.append(rij_resultaat)
                
                df_resultaten = pd.DataFrame(resultaten)
                
                if not df_resultaten.empty:
                    geldige_uiis = df_resultaten[df_resultaten['UII'] != ""]
                    duplicaten = geldige_uiis[geldige_uiis['UII'].duplicated(keep=False)]
                    if not duplicaten.empty:
                        unieke_dups = ", ".join(duplicaten['UII'].unique())
                        st.warning(T["dup_warn"].format(dups=unieke_dups))

                    st.markdown(f"""
                        <div class="badge-row">
                            <span class="badge">{T['badge_batch']}</span>
                            <span class="badge badge-ok">{T['badge_rows'].format(n=len(df_resultaten))}</span>
                        </div>
                    """, unsafe_allow_html=True)

                    st.dataframe(df_resultaten, use_container_width=True)

                    excel_output = io.BytesIO()
                    with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
                        df_resultaten.to_excel(writer, index=False)
                    
                    dl_col1, dl_col2 = st.columns(2)
                    with dl_col1:
                        st.download_button(
                            label=T["btn_dl_xlsx"],
                            data=excel_output.getvalue(),
                            file_name="UID_Studio_Batch_Results.xlsx" if lang == "EN" else "UID_Studio_Batch_Resultaten.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary",
                            use_container_width=True
                        )
                    with dl_col2:
                        if geldige_labels_count > 0:
                            st.download_button(
                                label=T["btn_dl_zip"],
                                data=zip_buffer.getvalue(),
                                file_name="UID_Studio_Batch_Labels.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                        else:
                            st.info(T["no_valid_zip"])
            else:
                st.error(T["err_cols"])

# 5. Footer (Eigenaarschap, Copyright & Disclaimer)
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #64748B; font-size: 13px;'>
        <strong style='color: #0F172A;'>UID Studio™</strong> &nbsp;|&nbsp; &copy; 2026 <strong style='color: #0F172A;'>{CONTACT_NAAM}</strong> — {T['footer_rights']}<br>
        {T['footer_sub']}<br>
        <span style='font-size: 11px; color: #94A3B8;'>{T['footer_disc']}</span>
    </div>
    """, 
    unsafe_allow_html=True
)
