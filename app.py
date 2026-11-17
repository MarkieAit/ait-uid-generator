import streamlit as st
import pandas as pd
import io
# --- BEVEILIGING ---
if "ingelogd" not in st.session_state:
    st.session_state["ingelogd"] = False

if not st.session_state["ingelogd"]:
    wachtwoord = st.text_input("Voer het DM&D wachtwoord in:", type="password")
    if wachtwoord == st.secrets["dmd_wachtwoord"]:
        st.session_state["ingelogd"] = True
        st.rerun() # Dit herlaadt de pagina direct, zonder het wachtwoordveld
    else:
        if wachtwoord != "":
            st.error("Onjuist wachtwoord. Toegang geweigerd.")
        st.stop()
# --- EINDE BEVEILIGING ---

# (Hieronder staat de rest van jouw originele code)
import json
from pylibdmtx.pylibdmtx import encode
from PIL import Image

# 1. Pagina configuratie
st.set_page_config(page_title="MIL-STD-130 UID Generator", layout="wide")

# 2. Achtergrondkleur en styling (CSS Injectie)
st.markdown("""
<style>
    /* Verandert de hoofdachtergrond naar een zacht lichtgrijs */
    .stApp {
        background-color: #f4f5f7; 
    }
    
    /* Maakt de zijbalk iets donkerder voor mooi contrast */
    [data-testid="stSidebar"] {
        background-color: #e2e4e8;
    }
</style>
""", unsafe_allow_html=True)

# 3. Zijbalk (Project info)
with st.sidebar:
    st.header("Project AIT / UID")
    st.write("Deze tool valideert Construct 2 invoer en genereert direct machine-leesbare MIL-STD-130 Data Matrix codes voor Defensie-materieel.")
    st.markdown("---")
    st.caption("Ministerie van Defensie")

# 4. Hoofd applicatie
st.title("MIL-STD-130 UID Generator & Validator")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Data Invoer")
    st.write("Voer de Construct 2 gegevens in:")
    
    # max_chars=5 helpt de gebruiker al in de interface
    ncage = st.text_input("NCAGE-code (exact 5 karakters, bijv. A213N)", max_chars=5)
    mpn = st.text_input("MPN (Manufacturer Part Number, bijv. YS2R8X800)")
    oem = st.text_input("OEM Serienummer (bijv. 05677484)")
    
    generate_btn = st.button("Bereken UII & Genereer Data Matrix", type="primary")

with col2:
    st.header("2. Output & Validatie")
    
    if generate_btn:
        # Check of alle velden zijn ingevuld
        if ncage and mpn and oem:
            
            # Controleer of NCAGE exact 5 tekens is
            if len(ncage) != 5:
                st.error("Fout: Een geldige NCAGE-code moet exact 5 karakters lang zijn (bijv. A213N).")
            else:
                # Forceer alles naar hoofdletters volgens de norm
                ncage_clean = ncage.upper()
                mpn_clean = mpn.upper()
                oem_clean = oem.upper()

                # UII Berekenen met de opgeschoonde data
                uii = f"D{ncage_clean}{mpn_clean}{oem_clean}"
                st.success(f"**Berekende UII:** {uii}")
                
                # Syntax string bouwen
                syntax_string = f"[)>[RS]06[GS]17V{ncage_clean}[GS]1P{mpn_clean}[GS]S{oem_clean}[RS][EOT]"
                
                # JSON Object genereren
                output_data = {
                    "uii": uii,
                    "ncage": ncage_clean,
                    "mpn": mpn_clean,
                    "oem_serial": oem_clean,
                    "iso_15434_syntax": syntax_string
                }
                
                with st.expander("Toon Machine-Readable JSON (Optioneel)"):
    st.json(output_data)
                
                # Data Matrix renderen met pylibdmtx
                st.subheader("Data Matrix (ECC 200)")
                try:
                    # Vervang tekst-tags door werkelijke ASCII stuurcodes
                    barcode_data = syntax_string.replace('[RS]', chr(30)).replace('[GS]', chr(29)).replace('[EOT]', chr(4))
                    
                    # Genereer de barcode
                    encoded = encode(barcode_data.encode('utf-8'))
                    img = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
                    
                    # Toon in de interface
                    st.image(img, caption="Scanbare MIL-STD-130 UID", width=250)
                    
                    # --- NIEUW: DOWNLOAD & PRINT KNOP ---
                    virtueel_bestand = io.BytesIO()
                    img.save(virtueel_bestand, format="PNG")
                    bytes_data = virtueel_bestand.getvalue()
                    
                    st.download_button(
                        label="🖨️ Download & Print Label",
                        data=bytes_data, 
                        file_name=f"UID_{ncage_clean}_{mpn_clean}_{oem_clean}.png",
                        mime="image/png"
                    )
                    
                except Exception as e:
                    st.error(f"Fout bij genereren barcode: {e}")
        else:
            st.warning("Vul alstublieft alle drie de velden in om de UID te genereren.")

# 5. Footer (Naam / Eigenaarschap onderaan de pagina)
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #555; font-size: 14px;'>
        <strong>Ontwikkeld door: Marco van Dijk</strong><br>
        Projectleider AIT / UID | Directie Materieel & Diensten (DM&D) / CLAS
    </div>
    """, 
    unsafe_allow_html=True
)
