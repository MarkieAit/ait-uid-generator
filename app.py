import streamlit as st
import pandas as pd
import io
import json
import re
from pylibdmtx.pylibdmtx import encode
from PIL import Image, ImageDraw, ImageFont, ImageOps

# 1. Pagina configuratie (moet altijd als eerste Streamlit-commando staan)
st.set_page_config(page_title="MIL-STD-130 UID Generator", layout="wide")

# --- BEVEILIGING ---
if "ingelogd" not in st.session_state:
    st.session_state["ingelogd"] = False

if not st.session_state["ingelogd"]:
    st.title("MIL-STD-130 UID Generator")
    wachtwoord = st.text_input("Voer het DM&D wachtwoord in:", type="password")
    if wachtwoord == st.secrets["dmd_wachtwoord"]:
        st.session_state["ingelogd"] = True
        st.rerun()
    else:
        if wachtwoord != "":
            st.error("❌ Onjuist wachtwoord. Toegang geweigerd.")
        st.stop()
# --- EINDE BEVEILIGING ---

# 2. Achtergrondkleur en Defensie-styling (CSS Injectie)
st.markdown("""
<style>
    /* Verberg de standaard Streamlit Share-knop en menubalk rechtsboven */
    [data-testid="stToolbar"] {
        visibility: hidden;
    }

    /* Hoofdachtergrond lichtgrijs */
    .stApp {
        background-color: #f4f5f7; 
    }
    
    /* Zijbalk iets donkerder voor contrast */
    [data-testid="stSidebar"] {
        background-color: #e2e4e8;
    }
    
    /* Optimale marges zodat titel én footer goed in beeld blijven */
    .block-container {
        padding-top: 2.8rem;
        padding-bottom: 0.5rem;
    }

    /* Compactere horizontale lijnen en koppen */
    hr {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    h1, h2 {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
    }

    /* Primaire knoppen in Defensie-blauw i.p.v. Streamlit-rood */
    .stButton > button[kind="primary"] {
        background-color: #154273;
        border-color: #154273;
        color: white;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #0e2e52;
        border-color: #0e2e52;
        color: white;
    }

    /* Grotere klikvlakken voor gebruik op de werkvloer / mobiel */
    .stButton > button, .stDownloadButton > button {
        min-height: 2.8rem;
        font-weight: 600;
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
    st.caption("Versie: v1.2 (Pilot)")
    st.caption("Beheer: DM&D / CLAS")

# 4. Hoofd applicatie
st.title("MIL-STD-130 UID Generator & Validator")

# Scheid de twee werkprocessen met tabbladen
tab1, tab2 = st.tabs(["🏷️ Enkel Label (Werkplaats)", "📊 Batch Verwerking (Excel)"])

# ==========================================
# TAB 1: ENKEL LABEL
# ==========================================
with tab1:
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("1. Data Invoer")
        st.write("Voer de Construct 2 gegevens in:")
        
        ncage = st.text_input("NCAGE-code (exact 5 karakters, bijv. A213N)", max_chars=5, key="ncage_input")
        mpn = st.text_input("MPN (Manufacturer Part Number, bijv. YS2R8X800)", key="mpn_input")
        oem = st.text_input("OEM Serienummer (bijv. 05677484)", key="oem_input")

        # Directe foutpreventie bij ongeldige tekens (zoals spaties)
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
                    st.success(f"✅ **Berekende UII:** {uii}")
                    
                    syntax_string = f"[)>[RS]06[GS]17V{ncage_clean}[GS]1P{mpn_clean}[GS]S{oem_clean}[RS][EOT]"
                    
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
                        
                        st.image(label_img, caption="Gegenereerd Typeplaatje (MIL-STD-130)", width=480)
                        
                        # Downloadknop
                        virtueel_bestand = io.BytesIO()
                        label_img.save(virtueel_bestand, format="PNG")
                        bytes_data = virtueel_bestand.getvalue()
                        
                        st.download_button(
                            label="🖨️ Download & Print Label (.png)",
                            data=bytes_data, 
                            file_name=f"Label_{ncage_clean}_{mpn_clean}_{oem_clean}.png",
                            mime="image/png",
                            type="primary"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Fout bij genereren barcode: {e}")
