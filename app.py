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
        border-bottom: 3
