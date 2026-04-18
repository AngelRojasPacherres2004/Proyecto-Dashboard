# styles/main.py
import base64
from pathlib import Path

def load_login_bg():
    img_path = Path("assets/login_bg.png")

    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()
def get_global_style():
    return """
    <style>

    /* ===== GENERAL APP ===== */
    .stApp {
        background: radial-gradient(circle at top right, #1a1c25, #08090e);
        color: white;
    }

    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 16, 22, 0.95);
        backdrop-filter: blur(15px);
    }

    /* ===== LOGIN ===== */
    .login-box {
        background: rgba(255,255,255,0.05);
        padding: 20px;
        border-radius: 20px;
    }

    /* ===== BOTONES ===== */
    button {
        border-radius: 12px !important;
    }

    </style>
    """
def get_login_style():
    fondo = load_login_bg()

    return f"""
    <style>

    /* ===== BACKGROUND CON IMAGEN ===== */
    .stApp {{
        background: 
            linear-gradient(rgba(8, 9, 14, 0.55), rgba(8, 9, 14, 0.75)),
            url("data:image/png;base64,{fondo}");

        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* ===== OCULTAR SIDEBAR ===== */
    section[data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
    }}

    /* ===== LAYOUT LOGIN ===== */
    .login-shell {{
        max-width: 1100px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }}

    .login-hero {{
        height: 600px;
        padding: 3rem 2.2rem;
        border-radius: 32px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        backdrop-filter: blur(12px);
        color: white;
    }}

    .login-title {{
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: -0.04em;
    }}

    .login-point {{
        padding: 0.8rem;
        border-radius: 14px;
        background: rgba(255,255,255,0.04);
        margin-bottom: 0.5rem;
        COLOR: #ffff;
    }}

    /* ===== FORM CARD ===== */
    [data-testid="stForm"] {{
        border: none !important;
        background: rgba(255, 255, 255, 0.09) !important;
        border-radius: 32px !important;
        padding: 2rem !important;
        backdrop-filter: blur(18px) !important;
        box-shadow: 0 24px 60px rgba(0,0,0,0.34) !important;
        height: 600px;
    }}

    /* INPUTS */
    .stTextInput input {{
        background: rgba(255,255,255,0.1) !important;
        color: white !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        min-height: 3rem !important;
    }}

    /* BOTÓN */
    .stForm [data-testid="stFormSubmitButton"] button {{
        min-height: 3.2rem !important;
        border-radius: 14px !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #ffd18e 0%, #f0a84f 100%) !important;
        color: #1d1611 !important;
        border: none !important;
    }}

    </style>
    """