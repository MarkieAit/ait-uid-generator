import streamlit as st
import pandas as pd
import io
import json
import re
from pylibdmtx.pylibdmtx import encode
from PIL import Image, ImageDraw, ImageFont, ImageOps

# 1. Pagina configuratie (moet altijd als eerste Streamlit-commando staan)
st.set_page_config(page_title="MIL-STD-130 UID Generator | Defensie", layout="wide")

# --- BEVEILIGING ---
if "ingelogd" not in st.session_state:
    st.session_state["ingelogd"] = False

if not st.session_state["ingelogd"]:
    st.markdown("""
        <div style="background-color: #152232; padding: 1.5rem 2rem; border-bottom: 4px solid #E17000; margin-bottom: 1.5rem;">
            <span style="color: #E17000; font-size: 12px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase;">Ministerie van Defensie | DM&D</span>
            <h1 style="color: #FFFFFF; margin: 0.2rem 0 0 0; font-size: 1.8rem;">MIL-STD-130 UID Generator</h1>
        </div>
    """, unsafe_allow_html=True)
    wachtwoord = st.text_input("Voer het DM&D wachtwoord in:", type="password")
    if wachtwoord == st.secrets["dmd_wachtwoord"]:
        st.session_state["ingelogd"] = True
        st.rerun()
    else:
        if wachtwoord != "":
            st.error("❌ Onjuist wachtwoord. Toegang geweigerd.")
        st.stop()
# --- EINDE BEVEILIGING ---

# 2. Defensie UX Styling (CSS Injectie)
st.markdown("""
<style>
    /* Verberg de standaard Streamlit Share-knop en menubalk rechtsboven */
    [data-testid="stToolbar"] {
        visibility: hidden;
    }

    /* Lichtgrijze ondergrond zodat witte kaarten eruit springen */
    .stApp {
        background-color: #EEF0F3; 
    }
    
    /* Zijbalk in koel antraciet/grijs */
    [data-testid="stSidebar"] {
        background-color: #E2E5E9;
        border-right: 1px solid #CFD4DC;
    }
    
    /* Strakke paginamarges */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 0.8rem;
    }

    /* Hoekige, robuuste vormgeving (2px radius) voor alle interactieve elementen */
    .stButton > button,
    .stDownloadButton > button,
    .stTextInput > div > div > input,
    [data-testid="stFileUploader"] section {
        border-radius: 2px !important;
    }

    /* Witte 'Cards' voor alle containers met border=True */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #D3D8DF !important;
        border-radius: 2px !important;
        padding: 1.25rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }

    /* Primaire knoppen in Defensie-blauw */
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

    /* Grotere klikvlakken voor gebruik op de werkvloer / mobiel */
    .stButton > button, .stDownloadButton > button {
        min-height: 2.8rem;
        font-weight: 600;
        letter-spacing: 0.3px;
    }

    /* Tabbladen robuuster maken */
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

    /* Donkere Defensie Header Banner */
    .defensie-header {
        background-color: #152232;
        padding: 1.2rem 1.8rem;
        border-bottom: 4px solid #E17000;
        margin-bottom: 1.2rem;
        border-radius: 2px;
    }
    .defensie-kicker {
        color: #E17000;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        display: block;
        margin-bottom: 0.25rem;
    }
    .defensie-title {
        color: #FFFFFF;
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
    }

    /* Status-badges (Tags) */
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

    /* Compactere horizontale lijnen */
    hr {
        margin-top: 0.6rem !important;
        margin-bottom: 0.6rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Hulpfunctie om invoervelden te wissen
def wis_velden():
    st.session_state["ncage_input"] = ""
    st.session_state["mpn_input"] = ""
    st.session_state["oem_input"] = ""

# Hulpfunctie voor MIL-STD-130 karakter-check (alleen A-Z, 0-9, streepje en slash)
def bevat_ongeldige_tekens(tekst):
    return bool(re.search(r'[^A-Za-z0-9\-/]', tekst))

# 3. Zijbalk (Project info & Governance)
with st.sidebar:
    st.header("Project AIT / UID")
    st.write("Deze tool valideert Construct 2 invoer en genereert direct machine-leesbare MIL-STD-130 Data Matrix codes voor Defensie-materieel.")
    st.markdown("---")
    st.caption("**Ministerie van Defensie**")
    st.caption("Versie: v1.3 (Defensie UX)")
    st.caption("Beheer: DM&D / CLAS")

# 4. Strakke donkere Header Banner
st.markdown("""
    <div class="defensie-header">
        <span class="defensie-kicker">Ministerie van Defensie &nbsp;|&nbsp; Directie Materieel &amp; Diensten (DM&amp;D)</span>
        <div class="defensie-title">MIL-STD-130 UID Generator &amp; Validator</div>
    </div>
""", unsafe_allow_html=True)

# Scheid de twee werkprocessen met tabbladen
tab1, tab2 = st.tabs(["🏷️ Enkel Label (Werkplaats)", "📊 Batch Verwerking (Excel)"])

# ==========================================
# TAB 1: ENKEL LABEL
# ==========================================
with tab1:
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        with st.container(border=True):
            st.subheader("1. Data Invoer")
            st.caption("Voer de Construct 2 gegevens in (hoofdletters worden automatisch toegepast).")
            
            ncage = st.text_input("NCAGE-code (exact 5 karakters, bijv. A213N)", max_chars=5, key="ncage_input")
            mpn = st.text_input("MPN (Manufacturer Part Number, bijv. YS2R8X800)", key="mpn_input")
            oem = st.text_input("OEM Serienummer (bijv. 05677484)", key="oem_input")

            # Directe foutpreventie bij ongeldige tekens
            invoer_fout = False
            if ncage and bevat_ongeldige_tekens(ncage):
                st.warning("⚠️ NCAGE bevat spaties of ongeldige tekens.")
                invoer_fout = True
            if mpn and bevat_ongeldige_tekens(mpn):
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
                if ncage and mpn and oem:
                    if invoer_fout:
                        st.error("❌ Verwijder eerst de spaties of ongeldige tekens uit de invoervelden.")
                    elif len(ncage) != 5:
                        st.error("❌ Fout: Een geldige NCAGE-code moet exact 5 karakters lang zijn (bijv. A213N).")
                    else:
                        ncage_clean = ncage.upper()
                        mpn_clean = mpn.upper()
                        oem_clean = oem.upper()

                        uii = f"D{ncage_clean}{mpn_clean}{oem_clean}"
                        syntax_string = f"[)>[RS]06[GS]17V{ncage_clean}[GS]1P{mpn_clean}[GS]S{oem_clean}[RS][EOT]"

                        # Status-badges (Defensie tags)
                        st.markdown("""
                            <div class="badge-row">
                                <span class="badge">MIL-STD-130</span>
                                <span class="badge">CONSTRUCT 2</span>
                                <span class="badge">ECC 200</span>
                                <span class="badge badge-ok">✓ GEVALIDEERD</span>
                            </div>
                        """, unsafe_allow_html=True)

                        st.success(f"**Berekende UII:** `{uii}`")
                        
                        output_data = {
                            "uii": uii,
                            "ncage": ncage_clean,
                            "mpn": mpn_clean,
                            "oem_serial": oem_clean,
                            "iso_15434_syntax": syntax_string
                        }
                        
                        with st.expander("Toon Machine-Readable JSON (Optioneel)"):
                            st.json(output_data)
                        
                        try:
                            barcode_data = syntax_string.replace('[RS]', chr(30)).replace('[GS]', chr(29)).replace('[EOT]', chr(4))
                            
                            # 1. Genereer de standaard barcode
                            encoded = encode(barcode_data.encode('utf-8'))
                            img_raw = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
                            
                            # 2. Dynamisch schalen: maximaal 270x270 pixels
                            max_grootte = 270
                            schaalfactor = max(1, min(max_grootte // img_raw.width, max_grootte // img_raw.height))
                            
                            img_barcode = img_raw.resize(
                                (img_raw.width * schaalfactor, img_raw.height * schaalfactor), 
                                Image.Resampling.NEAREST
                            )
                            
                            # 3. Inverteer naar wit-op-zwart
                            img_barcode = ImageOps.invert(img_barcode)
                            
                            # 4. Zwart canvas (breedte 750, hoogte 350)
                            label_img = Image.new('RGB', (750, 350), color='black')
                            
                            # 5. Plak de barcode gecentreerd aan de rechterkant
                            x_pos_barcode = 750 - img_barcode.width - 40
                            y_pos_barcode = (350 - img_barcode.height) // 2
                            label_img.paste(img_barcode, (x_pos_barcode, y_pos_barcode))
                            
                            # 6. Tekst toevoegen
                            draw = ImageDraw.Draw(label_img)
                            try:
                                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 36)
                            except:
                                font = ImageFont.load_default()
                                
                            draw.text((50, 80), f"CAGE:  {ncage_clean}", fill="white", font=font)
                            draw.text((50, 160), f"MPN:   {mpn_clean}", fill="white", font=font)
                            draw.text((50, 240), f"SN:    {oem_clean}", fill="white", font=font)
                            
                            st.image(label_img, caption="Gegenereerd Typeplaatje (Zwart/Wit)", width=460)
                            
                            # Downloadknop
                            virtueel_bestand = io.BytesIO()
                            label_img.save(virtueel_bestand, format="PNG")
                            bytes_data = virtueel_bestand.getvalue()
                            
                            st.download_button(
                                label="🖨️ Download & Print Label (.png)",
                                data=bytes_data, 
                                file_name=f"Label_{ncage_clean}_{mpn_clean}_{oem_clean}.png",
                                mime="image/png",
                                type="primary",
                                use_container_width=True
                            )
                            
                        except Exception as e:
                            st.error(f"❌ Fout bij genereren barcode: {e}")
                else:
                    st.warning("⚠️ Vul alstublieft alle drie de velden in om de UID te genereren.")
            else:
                st.markdown("""
                    <div class="badge-row">
                        <span class="badge">MIL-STD-130</span>
                        <span class="badge">CONSTRUCT 2</span>
                        <span class="badge">ECC 200</span>
                    </div>
                """, unsafe_allow_html=True)
                st.info(
                    "👈 Vul links de **NCAGE**, **MPN** en het **OEM Serienummer** in en klik op "
                    "**Bereken UII & Genereer Label**.\n\n"
                    "Hier verschijnt direct het gevalideerde UII-nummer en het printklare typeplaatje."
                )

# ==========================================
# TAB 2: BATCH INVOER (EXCEL)
# ==========================================
with tab2:
    with st.container(border=True):
        st.subheader("Batch Verwerking via Excel")
        
        # Leeg Excel-sjabloon aanmaken in het geheugen
        sjabloon_df = pd.DataFrame({
            "NCAGE": ["A213N"],
            "MPN": ["YS2R8X800"],
            "OEM": ["05677484"]
        })
        sjabloon_buffer = io.BytesIO()
        with pd.ExcelWriter(sjabloon_buffer, engine='openpyxl') as writer:
            sjabloon_df.to_excel(writer, index=False)
        
        col_info, col_sjabloon = st.columns([3, 1])
        with col_info:
            st.write("Upload een `.xlsx` bestand met de kolommen **NCAGE**, **MPN** en **OEM** om meerdere UII's tegelijk te berekenen.")
        with col_sjabloon:
            st.download_button(
                label="📄 Download Excel-sjabloon",
                data=sjabloon_buffer.getvalue(),
                file_name="DM&D_UID_Sjabloon.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        excel_bestand = st.file_uploader("Sleep je Excel-bestand hierheen of klik op bladeren", type=["xlsx"])

        if excel_bestand is not None:
            df = pd.read_excel(excel_bestand)
            df.columns = df.columns.str.strip().str.upper()
            
            if set(['NCAGE', 'MPN', 'OEM']).issubset(df.columns):
                resultaten = []
                
                for index, row in df.iterrows():
                    ncage_clean = str(row['NCAGE']).strip().upper()
                    mpn_clean = str(row['MPN']).strip().upper()
                    oem_clean = str(row['OEM']).strip().upper()
                    
                    if ncage_clean and ncage_clean != 'NAN':
                        uii = f"D{ncage_clean}{mpn_clean}{oem_clean}"
                        syntax_string = f"[)>[RS]06[GS]17V{ncage_clean}[GS]1P{mpn_clean}[GS]S{oem_clean}[RS][EOT]"
                        
                        resultaten.append({
                            "NCAGE": ncage_clean,
                            "MPN": mpn_clean,
                            "OEM": oem_clean,
                            "UII": uii,
                            "ISO 15434 Syntax": syntax_string
                        })
                
                df_resultaten = pd.DataFrame(resultaten)
                
                if not df_resultaten.empty:
                    st.markdown(f"""
                        <div class="badge-row">
                            <span class="badge">BATCH VERWERKING</span>
                            <span class="badge badge-ok">✓ {len(df_resultaten)} REGELS GEVALIDEERD</span>
                        </div>
                    """, unsafe_allow_html=True)

                    st.dataframe(df_resultaten, use_container_width=True)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_resultaten.to_excel(writer, index=False)
                    excel_data = output.getvalue()
                    
                    st.download_button(
                        label="📥 Download Verwerkte Lijst (.xlsx)",
                        data=excel_data,
                        file_name="DM&D_UID_Batch_Resultaten.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )
            else:
                st.error("❌ Fout: De geüploade Excel mist één of meerdere verplichte kolommen (NCAGE, MPN of OEM). Gebruik het sjabloon rechtsboven.")

# 5. Footer (Naam / Eigenaarschap onderaan de pagina)
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #555; font-size: 13px;'>
        <strong>Ontwikkeld door: Marco van Dijk</strong><br>
        Projectleider AIT / UID | Directie Materieel &amp; Diensten (DM&amp;D) / CLAS
    </div>
    """, 
    unsafe_allow_html=True
)
