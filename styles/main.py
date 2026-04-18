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

    /* ================= OCULTAR MENU STREAMLIT ================= */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* ================= BACKGROUND APP ================= */
    .stApp {
        background: linear-gradient(135deg, #1c1f2e 0%, #2a2f45 50%, #1f2a3a 100%);
        color: white;
        font-family: 'Inter', sans-serif;
        animation: fadeInApp 0.6s ease-in-out;
    }

    /* ================= SIDEBAR ================= */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2b2f3f 0%, #232838 100%);
        backdrop-filter: blur(18px);
        border-right: 1px solid rgba(255,255,255,0.08);
        animation: slideInLeft 0.5s ease-out;
    }

    /* ================= TEXTO SIDEBAR ================= */
    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* ================= TITULOS ================= */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f6c27d !important;
        font-weight: 800;
        animation: fadeInUp 0.6s ease;
    }

    /* ================= BOTONES ================= */
    .stButton button {
        width: 100%;
        background: rgba(255,255,255,0.06) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        padding: 12px;
        border-radius: 14px;
        transition: all 0.25s ease;
    }

    .stButton button:hover {
        background: rgba(246, 194, 125, 0.15) !important;
        border-color: #f6c27d !important;
        transform: translateX(6px) scale(1.02);
        box-shadow: 0 6px 20px rgba(246, 194, 125, 0.15);
    }

    /* ================= MENU ACTIVO ================= */
    .nav-link-selected {
        background: rgba(246, 194, 125, 0.25) !important;
        color: white !important;
        border-left: 4px solid #f6c27d !important;
        font-weight: 700 !important;
        animation: glow 1.5s infinite alternate;
    }

    /* ================= OCULTAR FOOTER ================= */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ================= ANIMACIONES ================= */

    @keyframes fadeInApp {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes slideInLeft {
        from {
            transform: translateX(-20px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes fadeInUp {
        from {
            transform: translateY(15px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }

    @keyframes glow {
        from {
            box-shadow: 0 0 5px rgba(246, 194, 125, 0.2);
        }
        to {
            box-shadow: 0 0 18px rgba(246, 194, 125, 0.4);
        }
    }

    </style>
    """