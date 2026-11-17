import streamlit as st
import pandas as pd
import io
import json
from pylibdmtx.pylibdmtx import encode
from PIL import Image, ImageDraw, ImageFont, ImageOps

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
    
    /* Verwijder de grote lege ruimte bovenaan het scherm */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
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
                    
                    # 1. Genereer de standaard barcode
                    encoded = encode(barcode_data.encode('utf-8'))
                    img_raw = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
                    
                    # 2. Schaal de barcode groter (NEAREST houdt de blokjes perfect scherp)
                    schaalfactor = 4
                    img_barcode = img_raw.resize(
                        (img_raw.width * schaalfactor, img_raw.height * schaalfactor), 
                        Image.Resampling.NEAREST
                    )
                    
                    # 3. Inverteer naar wit-op-zwart
                    img_barcode = ImageOps.invert(img_barcode)
                    
                    # 4. Maak een zwart canvas voor het complete label (breedte 750, hoogte 350)
                    label_img = Image.new('RGB', (750, 350), color='black')
                    
                    # 5. Plak de barcode aan de rechterkant
                    x_pos_barcode = 750 - img_barcode.width - 40
                    y_pos_barcode = (350 - img_barcode.height) // 2
                    label_img.paste(img_barcode, (x_pos_barcode, y_pos_barcode))
                    
                    # 6. Tekst toevoegen
                    draw = ImageDraw.Draw(label_img)
                    
                    # Probeer het standaard Linux lettertype van de Streamlit Cloud te laden
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
                    except:
                        font = ImageFont.load_default()
                        
                    # Teken de drie regels tekst (witte letters)
                    draw.text((40, 70), f"CAGE:  {ncage_clean}", fill="white", font=font)
                    draw.text((40, 150), f"MPN:   {mpn_clean}", fill="white", font=font)
                    draw.text((40, 230), f"SN:    {oem_clean}", fill="white", font=font)
                    
                    # Toon in de interface
                    st.image(label_img, caption="Gegenereerd Typeplaatje (Zwart/Wit)", width=500)
                    
                    # --- DOWNLOAD & PRINT KNOP ---
                    virtueel_bestand = io.BytesIO()
                    label_img.save(virtueel_bestand, format="PNG")
                    bytes_data = virtueel_bestand.getvalue()
                    
                    st.download_button(
                        label="🖨️ Download & Print Label",
                        data=bytes_data, 
                        file_name=f"Label_{ncage_clean}_{mpn_clean}_{oem_clean}.png",
                        mime="image/png"
                    )
                    
                except Exception as e:
                    st.error(f"Fout bij genereren barcode: {e}")
        else:
            st.warning("Vul alstublieft alle drie de velden in om de UID te genereren.")


# --- NIEUW: 3. BATCH INVOER (EXCEL) ---
st.markdown("---")
st.header("3. Batch Invoer (Excel Upload)")
st.write("Upload een .xlsx bestand met de kolommen: **NCAGE**, **MPN**, en **OEM** om meerdere labels tegelijk te verwerken.")

excel_bestand = st.file_uploader("Kies een Excel-bestand", type=["xlsx"])

if excel_bestand is not None:
    # Lees het bestand in
    df = pd.read_excel(excel_bestand)
    st.write("Controleer de ingeladen data:")
    st.dataframe(df, use_container_width=True)
    
    if st.button("Genereer UII's voor deze lijst", type="primary"):
        resultaten = []
        
        # Loop door elke rij in de geüploade Excel
        for index, row in df.iterrows():
            # Haal de waarden op en converteer naar veilige string
            ncage_clean = str(row.get('NCAGE', '')).strip().upper()
            mpn_clean = str(row.get('MPN', '')).strip().upper()
            oem_clean = str(row.get('OEM', '')).strip().upper()
            
            if ncage_clean and mpn_clean and oem_clean:
                # Bereken UII en Syntax
                uii = f"D{ncage_clean}{mpn_clean}{oem_clean}"
                syntax_string = f"[)>[RS]06[GS]17V{ncage_clean}[GS]1P{mpn_clean}[GS]S{oem_clean}[RS][EOT]"
                
                # Voeg toe aan de resultatenlijst
                resultaten.append({
                    "NCAGE": ncage_clean,
                    "MPN": mpn_clean,
                    "OEM": oem_clean,
                    "Berekende UII": uii,
                    "ISO 15434 Syntax": syntax_string
                })
            
        # Maak een nieuwe tabel van de resultaten
        df_resultaten = pd.DataFrame(resultaten)
        
        # Zet de tabel om naar een downloadbaar Excel-bestand in het geheugen
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_resultaten.to_excel(writer, index=False)
        excel_data = output.getvalue()
        
        st.success(f"✅ {len(df_resultaten)} regels succesvol verwerkt!")
        
        st.download_button(
            label="📥 Download Verwerkte Lijst (.xlsx)",
            data=excel_data,
            file_name="DM&D_UID_Batch_Resultaten.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
# --- EINDE BATCH INVOER ---

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
