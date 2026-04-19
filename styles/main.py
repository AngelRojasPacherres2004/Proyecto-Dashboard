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
def get_admin_style():
    return """
    <style>

    /* ================= OCULTAR ELEMENTOS STREAMLIT ================= */
    [data-testid="stSidebarNav"] { display: none !important; }
    #MainMenu                    { visibility: hidden; }
    footer                       { visibility: hidden; }
    [data-testid="stHeader"]     { background: #1c1f2e !important; }

    /* ================= APP BACKGROUND ================= */
    .stApp {
        background: linear-gradient(135deg, #1c1f2e 0%, #2a2f45 50%, #1f2a3a 100%);
        color: white;
        font-family: 'Inter', sans-serif;
    }

    /* ================= SIDEBAR ================= */
    section[data-testid="stSidebar"] > div:first-child {
        background: #1e2130 !important;
        border-right: 1px solid rgba(255,255,255,0.07);
        padding-top: 0 !important;
    }

    /* ================= SIDEBAR HEADER ================= */
    .sb-header {
        padding: 24px 16px 16px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
        margin-bottom: 12px;
    }

    .sb-logo {
        font-size: 28px;
        margin-bottom: 8px;
    }

    .sb-name {
        color: #f6c27d;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    .sb-role {
        color: rgba(255,255,255,0.45);
        font-size: 12px;
        margin-top: 2px;
    }

    /* ================= SIDEBAR BOTONES ================= */
    section[data-testid="stSidebar"] .stButton button {
        background: transparent !important;
        color: rgba(255,255,255,0.75) !important;
        border: none !important;
        border-radius: 10px !important;
        text-align: left !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        transition: background 0.2s ease, color 0.2s ease;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.06) !important;
        color: white !important;
    }

    /* Botón activo (type="primary") */
    section[data-testid="stSidebar"] .stButton button[kind="primary"] {
        background: rgba(246,194,125,0.15) !important;
        color: #f6c27d !important;
        border-left: 3px solid #f6c27d !important;
        border-radius: 0 10px 10px 0 !important;
        font-weight: 600 !important;
    }

    /* ================= METRIC CARDS ================= */
    .metric-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 10px;
    }

    .metric-label {
        color: rgba(255,255,255,0.45);
        font-size: 11px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .metric-value {
        color: white;
        font-size: 26px;
        font-weight: 800;
        line-height: 1;
    }

    /* ================= PAGE HEADER ================= */
    .page-title {
        color: white;
        font-size: 26px;
        font-weight: 800;
        margin: 0 0 4px 0;
    }

    .page-subtitle {
        color: rgba(255,255,255,0.5);
        font-size: 14px;
        margin: 0;
    }
    /* ================= METRIC LABEL COLORES ================= */
.metric-label--accent { color: #f6c27d; }
.metric-label--green  { color: #5DCAA5; }
.metric-label--red    { color: #F09595; }
.metric-label--blue   { color: #85B7EB; }

/* ================= SECTION HEADER ================= */
.section-header {
    margin: 32px 0 16px;
}

.section-header__top {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}

.section-header__icon { font-size: 20px; }

.section-header__title {
    color: #f6c27d;
    font-size: 20px;
    font-weight: 700;
    margin: 0;
}

.section-header__subtitle {
    color: rgba(255,255,255,0.5);
    font-size: 13px;
    margin: 0 0 0 30px;
}
    </style>
    """
