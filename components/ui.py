import streamlit as st


def metric_card(label, value, icon="📊", color_class="accent"):
    st.markdown(f"""
    <div class="metric-card"
         onmouseover="this.style.borderColor='rgba(246,194,125,0.3)'"
         onmouseout="this.style.borderColor='rgba(255,255,255,0.08)'">
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <div>
                <div class="metric-label metric-label--{color_class}">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            <div style="font-size:28px; opacity:0.6;">{icon}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title, subtitle=None, icon="📈"):
    subtitle_html = f'<p class="section-header__subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="section-header">
        <div class="section-header__top">
            <span class="section-header__icon">{icon}</span>
            <h2 class="section-header__title">{title}</h2>
        </div>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def page_header(title, subtitle=None):
    subtitle_html = f'<p class="page-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div style="margin-bottom:25px;">
        <h1 class="page-title">{title}</h1>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def action_button(label, icon="➕", key=None, help=None):
    return st.button(f"{icon} {label}", key=key, help=help, use_container_width=True)