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
from datetime import datetime
from pylibdmtx.pylibdmtx import encode, decode
from PIL import Image, ImageDraw, ImageFont, ImageOps

# 1. Pagina configuratie (moet altijd als eerste Streamlit-commando staan)
st.set_page_config(page_title="UID Studio™ | MIL-STD-130 & STANAG 2290 Generator", layout="wide")

# --- BEVEILIGING ---
if "ingelogd" not in st.session_state:
    st.session_state["ingelogd"] = False

if not st.session_state["ingelogd"]:
    st.markdown("""
        <div style="background-color: #152232; padding: 1.5rem 2rem; border-bottom: 4px solid #E17000; margin-bottom: 1.5rem;">
            <span style="color: #E17000; font-size: 12px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase;">Open Standards Tool &nbsp;|&nbsp; MIL-STD-130N &amp; STANAG 2290</span>
            <h1 style="color: #FFFFFF; margin: 0.2rem 0 0 0; font-size: 1.8rem;">UID Studio™ — Generator &amp; Validator</h1>
        </div>
    """, unsafe_allow_html=True)
    wachtwoord = st.text_input("Voer het toegangswachtwoord in:", type="password")
    if wachtwoord == st.secrets["dmd_wachtwoord"]:
        st.session_state["ingelogd"] = True
        st.rerun()
    else:
        if wachtwoord != "":
            st.error("❌ Onjuist wachtwoord. Toegang geweigerd.")
        st.stop()
# --- EINDE BEVEILIGING ---

# Initialiseer sessie-historie
if "historie" not in st.session_state:
    st.session_state["historie"] = []

# 2. Styling (CSS Injectie)
st.markdown("""
<style>
    [data-testid="stToolbar"] { visibility: hidden; }
    .stApp { background-color: #EEF0F3; }
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
    /* Kleurgecodeerde Syntax / DI weergave */
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

def bouw_kleur_syntax_html(ncage_clean, mpn_clean, oem_clean, construct="Construct 2"):
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
            f'<div class="di-row"><span class="tok-s">S</span> <strong>Serienummer:</strong> {oem_clean}</div>'
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
            f'<div class="di-row"><span class="tok-s">S</span> <strong>Serienummer:</strong> {oem_clean}</div>'
        )
    return ascii_html, hex_str, di_html

def genereer_label_afbeelding(ncage_clean, mpn_clean, oem_clean, syntax_string, stijl="Laser (Wit op Zwart)", construct="Construct 2"):
    """Genereert het label (PNG Image) én voert direct een decode self-check uit."""
    barcode_data = syntax_string.replace('[RS]', chr(30)).replace('[GS]', chr(29)).replace('[EOT]', chr(4))
    
    # 1. Genereer de ruwe Data Matrix (zwart-op-wit)
    encoded = encode(barcode_data.encode('utf-8'))
    img_raw = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
    
    # 2. Automatische Self-Check (Decode validatie op ruwe matrix met stille rand)
    decode_ok = False
    try:
        check_img = ImageOps.expand(img_raw, border=20, fill='white')
        decoded_objs = decode(check_img)
        if decoded_objs and decoded_objs[0].data.decode('utf-8') == barcode_data:
            decode_ok = True
    except Exception:
        decode_ok = False

    # 3. Dynamisch schalen: maximaal 260x260 pixels (garandeert Quiet Zone)
    max_grootte = 260
    schaalfactor = max(1, min(max_grootte // img_raw.width, max_grootte // img_raw.height))
    img_barcode = img_raw.resize(
        (img_raw.width * schaalfactor, img_raw.height * schaalfactor),
        Image.Resampling.NEAREST
    )

    # 4. Kleuren instellen op basis van Laser of Thermisch
    is_laser = (stijl == "Laser (Wit op Zwart)")
    achtergrond = 'black' if is_laser else 'white'
    tekstkleur = 'white' if is_laser else 'black'
    if is_laser:
        img_barcode = ImageOps.invert(img_barcode)

    # 5. Canvas maken (750 x 350) en barcode rechts plaatsen
    label_img = Image.new('RGB', (750, 350), color=achtergrond)
    x_pos_barcode = 750 - img_barcode.width - 45
    y_pos_barcode = (350 - img_barcode.height) // 2
    label_img.paste(img_barcode, (x_pos_barcode, y_pos_barcode))

    # 6. Tekst (HRI) tekenen
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

# 3. Zijbalk (Product info)
with st.sidebar:
    st.header("UID Studio™")
    st.write("Onafhankelijke tool voor het valideren en genereren van machine-leesbare MIL-STD-130N / STANAG 2290 Data Matrix codes (ISO/IEC 15434 Format 06).")
    st.info("📌 **Standaardkeuze:**\n- **Construct 2:** `CAGE + MPN + SN` (meest gebruikt in asset management)\n- **Construct 1:** `CAGE + SN` (bij wereldwijd unieke serienummers)")
    st.markdown("---")
    st.caption("**UID Studio™**")
    st.caption("Versie: v2.5 (Independent Edition)")
    st.caption("© 2026 Marco van Dijk")

# 4. Strakke donkere Header Banner
st.markdown("""
    <div class="app-header">
        <span class="app-kicker">Open Standards Tool &nbsp;|&nbsp; MIL-STD-130N &amp; STANAG 2290</span>
        <div class="app-title">UID Studio™ — Data Matrix Generator &amp; Validator</div>
    </div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🏷️ Enkel Label", "📊 Batch Verwerking (Excel)"])

# ==========================================
# TAB 1: ENKEL LABEL
# ==========================================
with tab1:
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        with st.container(border=True):
            st.subheader("1. Data Invoer")
            
            opt_col1, opt_col2 = st.columns(2)
            with opt_col1:
                construct_keuze = st.radio(
                    "UID Construct",
                    ["Construct 2", "Construct 1"],
                    horizontal=True,
                    help="Kies Construct 2 (CAGE + MPN + SN) of Construct 1 (CAGE + SN)."
                )
            with opt_col2:
                label_stijl = st.radio("Label Uitvoering", ["Laser (Wit op Zwart)", "Thermisch (Zwart op Wit)"], horizontal=True)

            if construct_keuze == "Construct 2":
                st.caption("ℹ️ **Construct 2:** Unieke identificatie via `CAGE/NCAGE + MPN + Serienummer`.")
            else:
                st.caption("ℹ️ **Construct 1:** Unieke identificatie via `CAGE/NCAGE + Serienummer` (zonder MPN).")

            ncage = st.text_input("CAGE / NCAGE-code (exact 5 karakters, bijv. A213N)", max_chars=5, key="ncage_input")
            
            if construct_keuze == "Construct 2":
                mpn = st.text_input("MPN (max. 32 karakters, bijv. YS2R8X800)", max_chars=32, key="mpn_input")
            else:
                mpn = ""
                
            oem = st.text_input("Serienummer (max. 30 karakters, bijv. 05677484)", max_chars=30, key="oem_input")

            # Live 50-karakter UII teller
            huidige_uii_lengte = 1 + len(ncage.strip()) + (len(mpn.strip()) if construct_keuze == "Construct 2" else 0) + len(oem.strip())
            if huidige_uii_lengte > 50:
                st.error(f"❌ UII-lengte overschreden: **{huidige_uii_lengte} / 50 tekens** (MIL-STD-130 limiet).")
            else:
                st.caption(f"📏 Live UII-lengte: **{huidige_uii_lengte} / 50 tekens** (MIL-STD-130 norm)")

            # Directe foutpreventie
            invoer_fout = False
            if ncage and bevat_ongeldige_tekens(ncage):
                st.warning("⚠️ CAGE/NCAGE bevat spaties of ongeldige tekens.")
                invoer_fout = True
            if construct_keuze == "Construct 2" and mpn and bevat_ongeldige_tekens(mpn):
                st.warning("⚠️ MPN bevat spaties of ongeldige tekens.")
                invoer_fout = True
            if oem and bevat_ongeldige_tekens(oem):
                st.warning("⚠️ Serienummer bevat spaties of ongeldige tekens.")
                invoer_fout = True

            btn_col1, btn_col2 = st.columns([2, 1])
            with btn_col1:
                generate_btn = st.button("Bereken UII & Genereer Label", type="primary", use_container_width=True)
            with btn_col2:
                st.button("🔄 Wis velden", on_click=wis_velden, use_container_width=True)

    with col2:
        with st.container(border=True):
            st.subheader("2. Output & Validatie")
            
            if generate_btn:
                verplicht_ok = bool(ncage and oem and (mpn if construct_keuze == "Construct 2" else True))
                if verplicht_ok:
                    if invoer_fout:
                        st.error("❌ Corrigeer eerst de waarschuwingen in de invoervelden.")
                    elif len(ncage) != 5:
                        st.error("❌ Fout: Een geldige CAGE/NCAGE-code moet exact 5 karakters lang zijn (bijv. A213N).")
                    elif huidige_uii_lengte > 50:
                        st.error("❌ Fout: De totale UII mag volgens MIL-STD-130 maximaal 50 karakters lang zijn.")
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
                                stijl=label_stijl, construct=construct_keuze
                            )

                            virtueel_bestand = io.BytesIO()
                            label_img.save(virtueel_bestand, format="PNG")
                            bytes_data = virtueel_bestand.getvalue()

                            # Sla op in sessie-historie (max. 5 meest recente)
                            st.session_state["historie"].insert(0, {
                                "tijd": datetime.now().strftime("%H:%M:%S"),
                                "uii": uii,
                                "construct": construct_keuze,
                                "stijl": label_stijl,
                                "png_bytes": bytes_data
                            })
                            st.session_state["historie"] = st.session_state["historie"][:5]

                            decode_badge = (
                                '<span class="badge badge-ok">✓ DECODE GEVALIDEERD</span>'
                                if decode_ok else
                                '<span class="badge badge-warn">⚠ DECODE CHECK MISLUKT</span>'
                            )
                            st.markdown(f"""
                                <div class="badge-row">
                                    <span class="badge">MIL-STD-130N</span>
                                    <span class="badge">FORMAT 06</span>
                                    <span class="badge">{construct_keuze.upper()}</span>
                                    {decode_badge}
                                </div>
                            """, unsafe_allow_html=True)

                            st.success(f"**Berekende UII:** `{uii}`")
                            st.image(label_img, caption=f"Gegenereerd Label ({label_stijl})", width=460)
                            
                            st.download_button(
                                label="🖨️ Download & Print Label (.png)",
                                data=bytes_data,
                                file_name=f"Label_{uii}.png",
                                mime="image/png",
                                type="primary",
                                use_container_width=True
                            )

                            # Uitklapbare Technische Syntax (ASCII, HEX & Data Identifiers)
                            ascii_html, hex_str, di_html = bouw_kleur_syntax_html(
                                ncage_clean, mpn_clean, oem_clean, construct=construct_keuze
                            )
                            with st.expander("🔍 Toon Technische Syntax (ASCII / HEX & DI's)"):
                                st.markdown("**Data Identifiers (Format 06):**")
                                st.markdown(di_html, unsafe_allow_html=True)
                                st.markdown("**ASCII Structuur:**")
                                st.markdown(f'<div class="syntax-box">{ascii_html}</div>', unsafe_allow_html=True)
                                st.markdown("**Raw Data (HEX stuurtekens):**")
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
                            with st.expander("Toon Machine-Readable JSON (Optioneel)"):
                                st.json(output_data)

                        except Exception as e:
                            st.error(f"❌ Fout bij genereren barcode: {e}")
                else:
                    st.warning("⚠️ Vul alstublieft alle verplichte velden in om de UID te genereren.")
            else:
                st.markdown("""
                    <div class="badge-row">
                        <span class="badge">MIL-STD-130N</span>
                        <span class="badge">FORMAT 06</span>
                        <span class="badge">ECC 200</span>
                    </div>
                """, unsafe_allow_html=True)
                st.info(
                    "👈 Vul links de gegevens in en klik op **Bereken UII & Genereer Label**.\n\n"
                    "UID Studio™ berekent de UII, voert automatisch een **decode self-check** uit en levert direct een printklaar label."
                )

    # Sessie-historie onderaan Tab 1
    if st.session_state["historie"]:
        with st.container(border=True):
            st.subheader("🕒 Recente Labels (Deze Sessie)")
            for idx, item in enumerate(st.session_state["historie"]):
                h_col1, h_col2, h_col3 = st.columns([3, 2, 1.5])
                with h_col1:
                    st.markdown(f"**`{item['uii']}`**")
                with h_col2:
                    st.caption(f"{item['tijd']} · {item['construct']} · {item['stijl']}")
                with h_col3:
                    st.download_button(
                        label="⬇️ Opnieuw (.png)",
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
        st.subheader("Batch Verwerking via Excel")
        st.info(
            "ℹ️ Upload een Excel-bestand met **NCAGE**, **MPN** (optioneel voor Construct 1) en **OEM**. "
            "Voeg optioneel de kolom **ERP_SLEUTEL** toe (bijv. SAP Equipment-nummer) om de output direct terug te kunnen laden in je ERP-systeem."
        )
        
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
            st.write("Regels met een ingevulde **MPN** worden als **Construct 2** verwerkt; zonder MPN als **Construct 1**. Voorloopnullen blijven behouden.")
        with col_stijl:
            batch_stijl = st.selectbox("Stijl voor ZIP-labels", ["Laser (Wit op Zwart)", "Thermisch (Zwart op Wit)"])
        with col_sjabloon:
            st.download_button(
                label="📄 Excel-sjabloon",
                data=sjabloon_buffer.getvalue(),
                file_name="UID_Studio_Sjabloon.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        excel_bestand = st.file_uploader("Sleep je Excel-bestand hierheen of klik op bladeren", type=["xlsx"])

        if excel_bestand is not None:
            # dtype=str voorkomt dat Excel/pandas voorloopnullen verwijdert
            df = pd.read_excel(excel_bestand, dtype=str)
            df.columns = df.columns.str.strip().str.upper()
            
            if set(['NCAGE', 'OEM']).issubset(df.columns):
                resultaten = []
                zip_buffer = io.BytesIO()
                heeft_mpn = 'MPN' in df.columns
                heeft_sleutel = 'ERP_SLEUTEL' in df.columns

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for index, row in df.iterrows():
                        # ERP_SLEUTEL behoudt exacte opmaak (geen .upper())
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
                        status = "OK" if lengte_ok else "FOUT (>50 tekens, NCAGE≠5 of OEM leeg)"

                        if lengte_ok:
                            try:
                                img, decode_ok = genereer_label_afbeelding(
                                    ncage_clean, mpn_clean, oem_clean, syntax_string,
                                    stijl=batch_stijl, construct=construct_type
                                )
                                img_bytes = io.BytesIO()
                                img.save(img_bytes, format="PNG")
                                zf.writestr(f"Label_{index+1}_{uii}.png", img_bytes.getvalue())
                                if not decode_ok:
                                    status = "WAARSCHUWING (Decode check)"
                            except Exception:
                                status = "FOUT (Barcode)"

                        rij_resultaat = {}
                        if heeft_sleutel:
                            rij_resultaat["ERP_SLEUTEL"] = sleutel_clean

                        rij_resultaat.update({
                            "NCAGE": ncage_clean,
                            "MPN": mpn_clean,
                            "OEM": oem_clean,
                            "Construct": construct_type,
                            "UII": uii,
                            "Lengte": len(uii),
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
                        st.warning(f"⚠️ **Duplicaat-detectie:** De volgende UII('s) komen vaker voor in dit bestand: `{unieke_dups}`")

                    st.markdown(f"""
                        <div class="badge-row">
                            <span class="badge">BATCH VERWERKING</span>
                            <span class="badge badge-ok">✓ {len(df_resultaten)} REGELS VERWERKT</span>
                        </div>
                    """, unsafe_allow_html=True)

                    st.dataframe(df_resultaten, use_container_width=True)

                    excel_output = io.BytesIO()
                    with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
                        df_resultaten.to_excel(writer, index=False)
                    
                    dl_col1, dl_col2 = st.columns(2)
                    with dl_col1:
                        st.download_button(
                            label="📥 Download Verwerkte Lijst (.xlsx)",
                            data=excel_output.getvalue(),
                            file_name="UID_Studio_Batch_Resultaten.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary",
                            use_container_width=True
                        )
                    with dl_col2:
                        st.download_button(
                            label="📦 Download Alle Labels (.zip)",
                            data=zip_buffer.getvalue(),
                            file_name="UID_Studio_Batch_Labels.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
            else:
                st.error("❌ Fout: De geüploade Excel mist de verplichte kolommen (minimaal **NCAGE** en **OEM**). Gebruik het sjabloon rechtsboven.")

# 5. Footer (Eigenaarschap, Copyright & Disclaimer)
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #555; font-size: 13px;'>
        <strong>UID Studio™</strong> &nbsp;|&nbsp; &copy; 2026 <strong>Marco van Dijk</strong> — Alle rechten voorbehouden.<br>
        Onafhankelijke software op basis van openbare standaarden (MIL-STD-130N / STANAG 2290 / ISO 15434).<br>
        <span style='font-size: 11px; color: #777;'>Disclaimer: Gebruik op eigen risico. De gebruiker blijft zelf verantwoordelijk voor de fysieke printkwaliteit en optische verificatie (ISO/IEC 15415).</span>
    </div>
    """, 
    unsafe_allow_html=True
)
