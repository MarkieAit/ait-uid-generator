"""
UID Studio™ — MIL-STD-130N & STANAG 2290 Generator & Validator
Copyright (c) 2026 Marco van Dijk. Alle rechten voorbehouden.

Onafhankelijke software ontwikkeld op basis van openbare standaarden
(MIL-STD-130N, STANAG 2290, ISO/IEC 15434 Format 06).
Zonder voorafgaande schriftelijke toestemming van de auteur mag deze
broncode niet worden gekopieerd, verspreid of commercieel hergebruikt.
"""

import streamlit as st
import pandas as pd
import io
import json
import re
import zipfile
from datetime import datetime, date
from pylibdmtx.pylibdmtx import encode, decode
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ==========================================
# LICENTIE- & DEMO-INSTELLINGEN (PAS HIER AAN)
# ==========================================
VERLOOPDATUM = date(2026, 12, 31)   # Jaar, Maand, Dag
MAX_DEMO_BATCH_REGELS = 5           # Maximaal aantal Excel-regels in proefversie
CONTACT_NAAM = "Marco van Dijk"
CONTACT_INFO = "7.spek_amp@icloud.com" # Vul hier je e-mailadres of telefoonnummer in
# ==========================================

# 1. Pagina configuratie (moet altijd als eerste Streamlit-commando staan)
st.set_page_config(page_title="UID Studio™ | MIL-STD-130 & STANAG 2290 Generator", layout="wide")

# Initialiseer taal en sessie-status
if "taal" not in st.session_state:
    st.session_state["taal"] = "🇳🇱 Nederlands"
if "ingelogd" not in st.session_state:
    st.session_state["ingelogd"] = False
if "historie" not in st.session_state:
    st.session_state["historie"] = []

# ==========================================
# VERTALINGEN (NL / EN)
# ==========================================
TEXT = {
    "NL": {
        "expired_kicker": "UID Studio™ &nbsp;|&nbsp; Licentie Verlopen",
        "expired_title": "Proefversie is afgelopen",
        "expired_msg": "🔒 De proefperiode van **UID Studio™** is verlopen op **{datum}**.\n\nNeem contact op met **{naam}** ({contact}) om te kijken naar een passende oplossing of volledige licentie.",
        "login_kicker": "Open Standards Tool &nbsp;|&nbsp; MIL-STD-130N &amp; STANAG 2290",
        "login_title": "UID Studio™ — Generator &amp; Validator",
        "login_prompt": "Voer het toegangswachtwoord in:",
        "login_err": "❌ Onjuist wachtwoord. Toegang geweigerd.",
        "sidebar_desc": "Onafhankelijke tool voor het valideren en genereren van machine-leesbare MIL-STD-130N / STANAG 2290 Data Matrix codes (ISO/IEC 15434 Format 06).",
        "sidebar_std": "📌 **Standaardkeuze:**\n- **Construct 2:** `CAGE + MPN + SN` (meest gebruikt in asset management)\n- **Construct 1:** `CAGE + SN` (bij wereldwijd unieke serienummers)",
        "sidebar_demo": "⏳ **Proefversie actief**\n- Geldig t/m: **{datum}** ({dagen} dagen)\n- Excel-batch: max. **{max_regels} regels** per upload",
        "header_title": "UID Studio™ — Data Matrix Generator &amp; Validator",
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
        "ncage_lbl": "CAGE / NCAGE-code (exact 5 karakters, bijv. A213N)",
        "mpn_lbl": "MPN (max. 32 karakters, bijv. YS2R8X800)",
        "sn_lbl": "Serienummer (max. 30 karakters, bijv. 05677484)",
        "len_err": "❌ UII-lengte overschreden: **{lengte} / 50 tekens** (MIL-STD-130 limiet).",
        "len_ok": "📏 Live UII-lengte: **{lengte} / 50 tekens** (MIL-STD-130 norm)",
        "warn_ncage": "⚠️ CAGE/NCAGE bevat spaties of ongeldige tekens.",
        "warn_mpn": "⚠️ MPN bevat spaties of ongeldige tekens.",
        "warn_sn": "⚠️ Serienummer bevat spaties of ongeldige tekens.",
        "btn_gen": "Bereken UII & Genereer Label",
        "btn_clear": "🔄 Wis velden",
        "err_fix_warns": "❌ Corrigeer eerst de waarschuwingen in de invoervelden.",
        "err_ncage_len": "❌ Fout: Een geldige CAGE/NCAGE-code moet exact 5 karakters lang zijn (bijv. A213N).",
        "err_uii_len": "❌ Fout: De totale UII mag volgens MIL-STD-130 maximaal 50 karakters lang zijn.",
        "warn_req": "⚠️ Vul alstublieft alle verplichte velden in om de UID te genereren.",
        "badge_decode_ok": "✓ DECODE GEVALIDEERD",
        "badge_decode_fail": "⚠ DECODE CHECK MISLUKT",
        "uii_calc": "**Berekende UII:** `{uii}`",
        "img_caption": "Gegenereerd Label ({stijl})",
        "btn_dl_png": "🖨️ Download & Print Label (.png)",
        "exp_syntax": "🔍 Toon Technische Syntax (ASCII / HEX & DI's)",
        "di_title": "**Data Identifiers (Format 06):**",
        "di_sn": "Serienummer",
        "ascii_title": "**ASCII Structuur:**",
        "hex_title": "**Raw Data (HEX stuurtekens):**",
        "exp_json": "Toon Machine-Readable JSON (Optioneel)",
        "err_barcode": "❌ Fout bij genereren barcode: {e}",
        "empty_info": "👈 Vul links de gegevens in en klik op **Bereken UII & Genereer Label**.\n\nUID Studio™ berekent de UII, voert automatisch een **decode self-check** uit en levert direct een printklaar label.",
        "hist_title": "🕒 Recente Labels (Deze Sessie)",
        "btn_dl_again": "⬇️ Opnieuw (.png)",
        "batch_title": "Batch Verwerking via Excel",
        "batch_info": "ℹ️ Upload een Excel-bestand met **NCAGE**, **MPN** (optioneel voor Construct 1) en **OEM**. Voeg optioneel **ERP_SLEUTEL** toe voor ERP-import. *(Proefversie: max. {max_regels} regels per upload)*",
        "batch_desc": "Regels met een ingevulde **MPN** worden als **Construct 2** verwerkt; zonder MPN als **Construct 1**. Voorloopnullen blijven behouden.",
        "batch_style_lbl": "Stijl voor ZIP-labels",
        "btn_template": "📄 Excel-sjabloon",
        "uploader_lbl": "Sleep je Excel-bestand hierheen of klik op bladeren",
        "demo_limit_warn": "⚠️ **Proefversie-limiet bereikt:** Uw bestand bevat {totaal} regels. In deze demo worden de eerste **{max_regels} regels** verwerkt. Neem contact op met **{naam}** ({contact}) voor onbeperkte batchverwerking.",
        "status_ok": "OK",
        "status_err_len": "FOUT (>50 tekens, NCAGE≠5 of OEM leeg)",
        "status_warn_dec": "WAARSCHUWING (Decode check)",
        "status_err_bc": "FOUT (Barcode)",
        "dup_warn": "⚠️ **Duplicaat-detectie:** De volgende UII('s) komen vaker voor in dit bestand: `{dups}`",
        "badge_batch": "BATCH VERWERKING",
        "badge_rows": "✓ {n} REGELS VERWERKT",
        "btn_dl_xlsx": "📥 Download Verwerkte Lijst (.xlsx)",
        "btn_dl_zip": "📦 Download Alle Labels (.zip)",
        "err_cols": "❌ Fout: De geüploade Excel mist de verplichte kolommen (minimaal **NCAGE** en **OEM**). Gebruik het sjabloon rechtsboven.",
        "footer_rights": "Alle rechten voorbehouden.",
        "footer_sub": "Onafhankelijke software op basis van openbare standaarden (MIL-STD-130N / STANAG 2290 / ISO 15434).",
        "footer_disc": "Disclaimer: Gebruik op eigen risico. De gebruiker blijft zelf verantwoordelijk voor de fysieke printkwaliteit en optische verificatie (ISO/IEC 15415)."
    },
    "EN": {
        "expired_kicker": "UID Studio™ &nbsp;|&nbsp; License Expired",
        "expired_title": "Trial Version Has Ended",
        "expired_msg": "🔒 The trial period of **UID Studio™** expired on **{datum}**.\n\nPlease contact **{naam}** ({contact}) to discuss a suitable solution or full license.",
        "login_kicker": "Open Standards Tool &nbsp;|&nbsp; MIL-STD-130N &amp; STANAG 2290",
        "login_title": "UID Studio™ — Generator &amp; Validator",
        "login_prompt": "Enter access password:",
        "login_err": "❌ Incorrect password. Access denied.",
        "sidebar_desc": "Independent tool for validating and generating machine-readable MIL-STD-130N / STANAG 2290 Data Matrix codes (ISO/IEC 15434 Format 06).",
        "sidebar_std": "📌 **Standard Selection:**\n- **Construct 2:** `CAGE + MPN + SN` (standard for asset management)\n- **Construct 1:** `CAGE + SN` (for globally unique serial numbers)",
        "sidebar_demo": "⏳ **Trial Version Active**\n- Valid until: **{datum}** ({dagen} days)\n- Excel batch: max. **{max_regels} rows** per upload",
        "header_title": "UID Studio™ — Data Matrix Generator &amp; Validator",
        "tab_single": "🏷️ Single Label",
        "tab_batch": "📊 Batch Processing (Excel)",
        "sec_input": "1. Data Input",
        "sec_output": "2. Output & Validation",
        "construct_lbl": "UID Construct",
        "construct_help": "Choose Construct 2 (CAGE + MPN + SN) or Construct 1 (CAGE + SN).",
        "style_lbl": "Label Style",
        "style_laser": "Laser (White on Black)",
        "style_thermal": "Thermal (Black on White)",
        "c2_info": "ℹ️ **Construct 2:** Unique identification via `CAGE/NCAGE + MPN + Serial Number`.",
        "c1_info": "ℹ️ **Construct 1:** Unique identification via `CAGE/NCAGE + Serial Number` (without MPN).",
        "ncage_lbl": "CAGE / NCAGE Code (exact 5 characters, e.g. A213N)",
        "mpn_lbl": "MPN (max. 32 characters, e.g. YS2R8X800)",
        "sn_lbl": "Serial Number (max. 30 characters, e.g. 05677484)",
        "len_err": "❌ UII length exceeded: **{lengte} / 50 characters** (MIL-STD-130 limit).",
        "len_ok": "📏 Live UII length: **{lengte} / 50 characters** (MIL-STD-130 standard)",
        "warn_ncage": "⚠️ CAGE/NCAGE contains spaces or invalid characters.",
        "warn_mpn": "⚠️ MPN contains spaces or invalid characters.",
        "warn_sn": "⚠️ Serial number contains spaces or invalid characters.",
        "btn_gen": "Calculate UII & Generate Label",
        "btn_clear": "🔄 Clear fields",
        "err_fix_warns": "❌ Please resolve the warnings in the input fields first.",
        "err_ncage_len": "❌ Error: A valid CAGE/NCAGE code must be exactly 5 characters long (e.g. A213N).",
        "err_uii_len": "❌ Error: Total UII length cannot exceed 50 characters per MIL-STD-130.",
        "warn_req": "⚠️ Please fill in all required fields to generate the UID.",
        "badge_decode_ok": "✓ DECODE VERIFIED",
        "badge_decode_fail": "⚠ DECODE CHECK FAILED",
        "uii_calc": "**Calculated UII:** `{uii}`",
        "img_caption": "Generated Label ({stijl})",
        "btn_dl_png": "🖨️ Download & Print Label (.png)",
        "exp_syntax": "🔍 Show Technical Syntax (ASCII / HEX & DIs)",
        "di_title": "**Data Identifiers (Format 06):**",
        "di_sn": "Serial Number",
        "ascii_title": "**ASCII Structure:**",
        "hex_title": "**Raw Data (HEX control characters):**",
        "exp_json": "Show Machine-Readable JSON (Optional)",
        "err_barcode": "❌ Error generating barcode: {e}",
        "empty_info": "👈 Enter the details on the left and click **Calculate UII & Generate Label**.\n\nUID Studio™ calculates the UII, automatically runs a **decode self-check**, and delivers a print-ready label.",
        "hist_title": "🕒 Recent Labels (This Session)",
        "btn_dl_again": "⬇️ Download (.png)",
        "batch_title": "Batch Processing via Excel",
        "batch_info": "ℹ️ Upload an Excel file with **NCAGE**, **MPN** (optional for Construct 1), and **OEM**. Optionally add **ERP_SLEUTEL** for ERP import. *(Trial version: max. {max_regels} rows per upload)*",
        "batch_desc": "Rows with an **MPN** are processed as **Construct 2**; without MPN as **Construct 1**. Leading zeros are preserved.",
        "batch_style_lbl": "Style for ZIP labels",
        "btn_template": "📄 Excel Template",
        "uploader_lbl": "Drag and drop your Excel file here or click to browse",
        "demo_limit_warn": "⚠️ **Trial limit reached:** Your file contains {totaal} rows. In this demo, only the first **{max_regels} rows** are processed. Contact **{naam}** ({contact}) for unlimited batch processing.",
        "status_ok": "OK",
        "status_err_len": "ERROR (>50 chars, NCAGE≠5 or OEM empty)",
        "status_warn_dec": "WARNING (Decode check)",
        "status_err_bc": "ERROR (Barcode)",
        "dup_warn": "⚠️ **Duplicate detection:** The following UII(s) appear multiple times in this file: `{dups}`",
        "badge_batch": "BATCH PROCESSING",
        "badge_rows": "✓ {n} ROWS PROCESSED",
        "btn_dl_xlsx": "📥 Download Processed List (.xlsx)",
        "btn_dl_zip": "📦 Download All Labels (.zip)",
        "err_cols": "❌ Error: The uploaded Excel file is missing required columns (at least **NCAGE** and **OEM**). Use the template above.",
        "footer_rights": "All rights reserved.",
        "footer_sub": "Independent software based on open standards (MIL-STD-130N / STANAG 2290 / ISO 15434).",
        "footer_disc": "Disclaimer: Use at your own risk. The user remains responsible for physical print quality and optical verification (ISO/IEC 15415)."
    }
}

def get_lang_code():
    return "EN" if "English" in st.session_state["taal"] else "NL"

# Taalschakelaar tonen op inlog- of verlopen-scherm (als nog niet ingelogd)
vandaag = date.today()
if vandaag > VERLOOPDATUM or not st.session_state["ingelogd"]:
    _, lang_col = st.columns([5, 1.5])
    with lang_col:
        st.radio(
            "Language",
            ["🇳🇱 Nederlands", "🇬🇧 English"],
            horizontal=True,
            key="taal",
            label_visibility="collapsed"
        )

lang = get_lang_code()
T = TEXT[lang]

# --- CONTROLE VERLOOPDATUM ---
if vandaag > VERLOOPDATUM:
    st.markdown(f"""
        <div style="background-color: #152232; padding: 1.5rem 2rem; border-bottom: 4px solid #E17000; margin-bottom: 1.5rem;">
            <span style="color: #E17000; font-size: 12px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase;">{T['expired_kicker']}</span>
            <h1 style="color: #FFFFFF; margin: 0.2rem 0 0 0; font-size: 1.8rem;">{T['expired_title']}</h1>
        </div>
    """, unsafe_allow_html=True)
    st.error(T["expired_msg"].format(datum=VERLOOPDATUM.strftime('%d-%m-%Y'), naam=CONTACT_NAAM, contact=CONTACT_INFO))
    st.stop()
# --- EINDE CONTROLE VERLOOPDATUM ---

# --- BEVEILIGING ---
if not st.session_state["ingelogd"]:
    st.markdown(f"""
        <div style="background-color: #152232; padding: 1.5rem 2rem; border-bottom: 4px solid #E17000; margin-bottom: 1.5rem;">
            <span style="color: #E17000; font-size: 12px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase;">{T['login_kicker']}</span>
            <h1 style="color: #FFFFFF; margin: 0.2rem 0 0 0; font-size: 1.8rem;">{T['login_title']}</h1>
        </div>
    """, unsafe_allow_html=True)
    wachtwoord = st.text_input(T["login_prompt"], type="password")
    if wachtwoord == st.secrets["dmd_wachtwoord"]:
        st.session_state["ingelogd"] = True
        st.rerun()
    else:
        if wachtwoord != "":
            st.error(T["login_err"])
        st.stop()
# --- EINDE BEVEILIGING ---

# 2. Styling (CSS Injectie)
st.markdown("""
<style>
    [data-testid="stToolbar"] { visibility: hidden; }
    .stApp {
        background-color: #EEF0F3;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='320' height='220' viewBox='0 0 320 220'%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' transform='rotate(-25 160 110)' fill='%23152232' fill-opacity='0.07' font-family='sans-serif' font-size='22' font-weight='700' letter-spacing='3'%3EUID STUDIO%E2%84%A2%3C/text%3E%3C/svg%3E");
        background-repeat: repeat;
    }
    [data-testid="stSidebar"] {
        background-color: #E2E5E9;
        border-right: 1px solid #CFD4DC;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 0.8rem;
    }
    .stButton > button,
    .stDownloadButton > button,
    .stTextInput > div > div > input,
    [data-testid="stFileUploader"] section {
        border-radius: 2px !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #D3D8DF !important;
        border-radius: 2px !important;
        padding: 1.25rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"] {
        background-color: #154273;
        border-color: #154273;
        color: #FFFFFF;
    }
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {
        background-color: #0E2E52;
        border-color: #0E2E52;
        color: #FFFFFF;
    }
    .stButton > button, .stDownloadButton > button {
        min-height: 2.8rem;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 2px solid #D3D8DF;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 2px 2px 0 0;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        color: #333F4D;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #154273 !important;
        border-bottom: 3px solid #E17000 !important;
    }
    .app-header {
        background-color: #152232;
        padding: 1.2rem 1.8rem;
        border-bottom: 4px solid #E17000;
        margin-bottom: 1.2rem;
        border-radius: 2px;
    }
    .app-kicker {
        color: #E17000;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        display: block;
        margin-bottom: 0.25rem;
    }
    .app-title {
        color: #FFFFFF;
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
    }
    .badge-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 0.8rem;
    }
    .badge {
        display: inline-block;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        border-radius: 2px;
        background-color: #E8EEF5;
        color: #154273;
        border: 1px solid #C5D4E6;
    }
    .badge-ok {
        background-color: #E4F3EA;
        color: #1B5E20;
        border: 1px solid #B7DFC5;
    }
    .badge-warn {
        background-color: #FFF4E5;
        color: #B25E00;
        border: 1px solid #FFD8A8;
    }
    .syntax-box {
        background-color: #F4F6F8;
        border: 1px solid #D3D8DF;
        border-radius: 2px;
        padding: 10px 12px;
        font-family: monospace;
        font-size: 13px;
        line-height: 1.8;
        word-break: break-all;
        margin-bottom: 8px;
    }
    .tok-hdr { background-color: #E2E8F0; color: #1E293B; padding: 2px 5px; border-radius: 2px; font-weight: 700; }
    .tok-ctrl { background-color: #FEE2E2; color: #991B1B; padding: 2px 4px; border-radius: 2px; font-size: 11px; font-weight: 700; }
    .tok-17v { background-color: #DBEAFE; color: #1E40AF; padding: 2px 5px; border-radius: 2px; font-weight: 700; }
    .tok-1p { background-color: #F3E8FF; color: #6B21A8; padding: 2px 5px; border-radius: 2px; font-weight: 700; }
    .tok-s { background-color: #DCFCE7; color: #166534; padding: 2px 5px; border-radius: 2px; font-weight: 700; }
    .di-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
        font-size: 13px;
    }
    hr {
        margin-top: 0.6rem !important;
        margin-bottom: 0.6rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HULPFUNCTIES ---
def wis_velden():
    st.session_state["ncage_input"] = ""
    st.session_state["mpn_input"] = ""
    st.session_state["oem_input"] = ""

def bevat_ongeldige_tekens(tekst):
    return bool(re.search(r'[^A-Za-z0-9\-/]', tekst))

def bouw_kleur_syntax_html(ncage_clean, mpn_clean, oem_clean, sn_label, construct="Construct 2"):
    """Bouwt een kleurgecodeerde ASCII en HEX weergave van de ISO 15434 Format 06 syntax."""
    if construct == "Construct 2":
        ascii_html = (
            '<span class="tok-hdr">[)&gt;</span>'
            '<span class="tok-ctrl">RS</span>'
            '<span class="tok-hdr">06</span>'
            '<span class="tok-ctrl">GS</span>'
            f'<span class="tok-17v">17V{ncage_clean}</span>'
            '<span class="tok-ctrl">GS</span>'
            f'<span class="tok-1p">1P{mpn_clean}</span>'
            '<span class="tok-ctrl">GS</span>'
            f'<span class="tok-s">S{oem_clean}</span>'
            '<span class="tok-ctrl">RS</span>'
            '<span class="tok-ctrl">EOT</span>'
        )
        hex_str = f"[)>&lt;0x1E&gt;06&lt;0x1D&gt;17V{ncage_clean}&lt;0x1D&gt;1P{mpn_clean}&lt;0x1D&gt;S{oem_clean}&lt;0x1E&gt;&lt;0x04&gt;"
        di_html = (
            f'<div class="di-row"><span class="tok-17v">17V</span> <strong>CAGE / NCAGE:</strong> {ncage_clean}</div>'
            f'<div class="di-row"><span class="tok-1p">1P</span> <strong>MPN:</strong> {mpn_clean}</div>'
            f'<div class="di-row"><span class="tok-s">S</span> <strong>{sn_label}:</strong> {oem_clean}</div>'
        )
    else:
        ascii_html = (
            '<span class="tok-hdr">[)&gt;</span>'
            '<span class="tok-ctrl">RS</span>'
            '<span class="tok-hdr">06</span>'
            '<span class="tok-ctrl">GS</span>'
            f'<span class="tok-17v">17V{ncage_clean}</span>'
            '<span class="tok-ctrl">GS</span>'
            f'<span class="tok-s">S{oem_clean}</span>'
            '<span class="tok-ctrl">RS</span>'
            '<span class="tok-ctrl">EOT</span>'
        )
        hex_str = f"[)>&lt;0x1E&gt;06&lt;0x1D&gt;17V{ncage_clean}&lt;0x1D&gt;S{oem_clean}&lt;0x1E&gt;&lt;0x04&gt;"
        di_html = (
            f'<div class="di-row"><span class="tok-17v">17V</span> <strong>CAGE / NCAGE:</strong> {ncage_clean}</div>'
            f'<div class="di-row"><span class="tok-s">S</span> <strong>{sn_label}:</strong> {oem_clean}</div>'
        )
    return ascii_html, hex_str, di_html

def genereer_label_afbeelding(ncage_clean, mpn_clean, oem_clean, syntax_string, is_laser=True, construct="Construct 2"):
    """Genereert het label (PNG Image) én voert direct een decode self-check uit."""
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
        draw.rectangle([(0, 0), (749, 349)], outline="#CCCCCC", width=2)

    regels = [f"CAGE:  {ncage_clean}"]
    if construct == "Construct 2" and mpn_clean:
        regels.append(f"MPN:   {mpn_clean}")
    regels.append(f"SN:    {oem_clean}")

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 36)
    except Exception:
        font = ImageFont.load_default()

    start_y = 75 if len(regels) == 3 else 110
    stap_y = 80
    for idx, regel in enumerate(regels):
        draw.text((45, start_y + idx * stap_y), regel, fill=tekstkleur, font=font)

    return label_img, decode_ok

# 3. Zijbalk (Taalschakelaar, Product info & Licentiestatus)
dagen_over = (VERLOOPDATUM - vandaag).days
with st.sidebar:
    st.radio(
        "Taal / Language",
        ["🇳🇱 Nederlands", "🇬🇧 English"],
        horizontal=True,
        key="taal",
        label_visibility="collapsed"
    )
    # Herlaad actieve vertaling na mogelijke wissel in zijbalk
    lang = get_lang_code()
    T = TEXT[lang]

    st.markdown("---")
    st.header("UID Studio™")
    st.write(T["sidebar_desc"])
    st.info(T["sidebar_std"])
    st.warning(T["sidebar_demo"].format(datum=VERLOOPDATUM.strftime('%d-%m-%Y'), dagen=dagen_over, max_regels=MAX_DEMO_BATCH_REGELS))
    st.markdown("---")
    st.caption("**UID Studio™**")
    st.caption("Version: v2.7 (Bilingual Demo)")
    st.caption(f"© 2026 {CONTACT_NAAM}")

# 4. Strakke donkere Header Banner
st.markdown(f"""
    <div class="app-header">
        <span class="app-kicker">{T['login_kicker']}</span>
        <div class="app-title">{T['header_title']}</div>
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

            if construct_keuze == "Construct 2":
                st.caption(T["c2_info"])
            else:
                st.caption(T["c1_info"])

            ncage = st.text_input(T["ncage_lbl"], max_chars=5, key="ncage_input")
            
            if construct_keuze == "Construct 2":
                mpn = st.text_input(T["mpn_lbl"], max_chars=32, key="mpn_input")
            else:
                mpn = ""
                
            oem = st.text_input(T["sn_lbl"], max_chars=30, key="oem_input")

            # Live 50-karakter UII teller
            huidige_uii_lengte = 1 + len(ncage.strip()) + (len(mpn.strip()) if construct_keuze == "Construct 2" else 0) + len(oem.strip())
            if huidige_uii_lengte > 50:
                st.error(T["len_err"].format(lengte=huidige_uii_lengte))
            else:
                st.caption(T["len_ok"].format(lengte=huidige_uii_lengte))

            # Directe foutpreventie
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

            btn_col1, btn_col2 = st.columns([2, 1])
            with btn_col1:
                generate_btn = st.button(T["btn_gen"], type="primary", use_container_width=True)
            with btn_col2:
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

                            st.success(T["uii_calc"].format(uii=uii))
                            st.image(label_img, caption=T["img_caption"].format(stijl=label_stijl), width=460)
                            
                            st.download_button(
                                label=T["btn_dl_png"],
                                data=bytes_data,
                                file_name=f"Label_{uii}.png",
                                mime="image/png",
                                type="primary",
                                use_container_width=True
                            )

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

                            output_data = {
                                "uii": uii,
                                "construct": construct_keuze,
                                "ncage": ncage_clean,
                                "mpn": mpn_clean if construct_keuze == "Construct 2" else None,
                                "oem_serial": oem_clean,
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
                h_col1, h_col2, h_col3 = st.columns([3, 2, 1.5])
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
        
        sjabloon_df = pd.DataFrame({
            "ERP_SLEUTEL": ["10004582"],
            "NCAGE": ["A213N"],
            "MPN": ["YS2R8X800"],
            "OEM": ["05677484"]
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
            df = pd.read_excel(excel_bestand, dtype=str)
            df.columns = df.columns.str.strip().str.upper()
            
            if set(['NCAGE', 'OEM']).issubset(df.columns):
                totaal_regels = len(df)
                if totaal_regels > MAX_DEMO_BATCH_REGELS:
                    st.warning(T["demo_limit_warn"].format(
                        totaal=totaal_regels,
                        max_regels=MAX_DEMO_BATCH_REGELS,
                        naam=CONTACT_NAAM,
                        contact=CONTACT_INFO
                    ))
                    df = df.head(MAX_DEMO_BATCH_REGELS)

                resultaten = []
                zip_buffer = io.BytesIO()
                heeft_mpn = 'MPN' in df.columns
                heeft_sleutel = 'ERP_SLEUTEL' in df.columns

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for index, row in df.iterrows():
                        sleutel_raw = str(row['ERP_SLEUTEL']).strip() if (heeft_sleutel and pd.notna(row['ERP_SLEUTEL'])) else ""
                        sleutel_clean = "" if sleutel_raw.upper() in ("NAN", "NONE") else sleutel_raw

                        ncage_raw = str(row['NCAGE']).strip().upper() if pd.notna(row['NCAGE']) else ""
                        oem_raw = str(row['OEM']).strip().upper() if pd.notna(row['OEM']) else ""
                        mpn_raw = str(row['MPN']).strip().upper() if (heeft_mpn and pd.notna(row['MPN'])) else ""

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

                        lengte_ok = len(uii) <= 50 and len(ncage_clean) == 5 and bool(oem_clean)
                        status = T["status_ok"] if lengte_ok else T["status_err_len"]

                        if lengte_ok:
                            try:
                                img, decode_ok = genereer_label_afbeelding(
                                    ncage_clean, mpn_clean, oem_clean, syntax_string,
                                    is_laser=is_laser_batch, construct=construct_type
                                )
                                img_bytes = io.BytesIO()
                                img.save(img_bytes, format="PNG")
                                zf.writestr(f"Label_{index+1}_{uii}.png", img_bytes.getvalue())
                                if not decode_ok:
                                    status = T["status_warn_dec"]
                            except Exception:
                                status = T["status_err_bc"]

                        rij_resultaat = {}
                        if heeft_sleutel:
                            rij_resultaat["ERP_SLEUTEL"] = sleutel_clean

                        rij_resultaat.update({
                            "NCAGE": ncage_clean,
                            "MPN": mpn_clean,
                            "OEM": oem_clean,
                            "Construct": construct_type,
                            "UII": uii,
                            "Length" if lang == "EN" else "Lengte": len(uii),
                            "Status": status,
                            "ISO 15434 Syntax": syntax_string
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
                        st.download_button(
                            label=T["btn_dl_zip"],
                            data=zip_buffer.getvalue(),
                            file_name="UID_Studio_Batch_Labels.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
            else:
                st.error(T["err_cols"])

# 5. Footer (Eigenaarschap, Copyright & Disclaimer)
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #555; font-size: 13px;'>
        <strong>UID Studio™</strong> &nbsp;|&nbsp; &copy; 2026 <strong>{CONTACT_NAAM}</strong> — {T['footer_rights']}<br>
        {T['footer_sub']}<br>
        <span style='font-size: 11px; color: #777;'>{T['footer_disc']}</span>
    </div>
    """, 
    unsafe_allow_html=True
)
