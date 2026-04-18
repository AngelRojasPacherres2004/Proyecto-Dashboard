import streamlit as st

def metric_card(label, value, icon="📊", color="#f6c27d"):
    """
    Componente para tarjetas de métricas
    """
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        padding: 24px;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.08);
        transition: all 0.3s ease;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    " onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 8px 25px rgba(246, 194, 125, 0.15)'"
       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(0,0,0,0.1)'">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="color: {color}; font-size: 12px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px;">
                    {label}
                </div>
                <div style="color: white; font-size: 28px; font-weight: 900; line-height: 1;">
                    {value}
                </div>
            </div>
            <div style="font-size: 32px; opacity: 0.8;">
                {icon}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def section_header(title, subtitle=None, icon="📈"):
    """
    Componente para encabezados de sección
    """
    if subtitle:
        st.markdown(f"""
        <div style="margin: 40px 0 20px 0;">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 24px; margin-right: 12px;">{icon}</span>
                <h2 style="color: #f6c27d; font-size: 24px; font-weight: 800; margin: 0;">
                    {title}
                </h2>
            </div>
            <p style="color: rgba(255,255,255,0.7); font-size: 14px; margin: 0; margin-left: 36px;">
                {subtitle}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="margin: 40px 0 20px 0;">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 24px; margin-right: 12px;">{icon}</span>
                <h2 style="color: #f6c27d; font-size: 24px; font-weight: 800; margin: 0;">
                    {title}
                </h2>
            </div>
        </div>
        """, unsafe_allow_html=True)

def page_header(title, subtitle=None):
    """
    Componente para encabezado principal de página
    """
    if subtitle:
        st.markdown(f"""
        <div style="margin-bottom: 40px; padding: 30px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <h1 style="color: #f6c27d; font-size: 36px; font-weight: 900; margin: 0 0 8px 0; letter-spacing: -1px;">
                {title}
            </h1>
            <p style="color: rgba(255,255,255,0.75); font-size: 16px; margin: 0; font-weight: 400;">
                {subtitle}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="margin-bottom: 40px; padding: 30px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <h1 style="color: #f6c27d; font-size: 36px; font-weight: 900; margin: 0; letter-spacing: -1px;">
                {title}
            </h1>
        </div>
        """, unsafe_allow_html=True)

def action_button(label, icon="➕", key=None, help=None):
    """
    Componente para botones de acción
    """
    return st.button(f"{icon} {label}", key=key, help=help,
                    use_container_width=True)