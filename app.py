"""Main dashboard page for blog-DCF platform."""

import streamlit as st

st.set_page_config(
    page_title="DCF Valuation Platform",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Check dependencies on startup
try:
    from src.utils.error_handler import check_dependencies_on_startup
    check_dependencies_on_startup()
except Exception:
    # If dependency checker itself fails, continue anyway
    pass

# Inject custom CSS
def load_css():
    import os
    css_paths = [
        "assets/custom.css",
        "./assets/custom.css",
        os.path.join(os.path.dirname(__file__), "assets", "custom.css")
    ]
    
    css_content = None
    for path in css_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                css_content = f.read()
                break
        except FileNotFoundError:
            continue
    
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        # Fallback CSS if file doesn't exist
        st.markdown("""
        <style>
        .stApp { background: #0A0E27; color: #FFFFFF; }
        h1 { background: linear-gradient(135deg, #0066FF 0%, #00D4AA 100%);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        </style>
        """, unsafe_allow_html=True)

load_css()

# Hide Streamlit toolbar
st.markdown("""
<style>
[data-testid="stToolbar"],
.stAppToolbar,
[class*="stAppToolbar"],
[class*="st-emotion-cache-14vh5up"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    overflow: hidden !important;
    opacity: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero-section">
    <h1 class="hero-title">DCF Valuation Platform</h1>
    <p class="hero-subtitle">
        Professional valuation platform that compares <strong>Fair Value (DCF)</strong> vs <strong>Market Price</strong>.
        Advanced tool for financial analysis and investment decision-making.
    </p>
</div>
""", unsafe_allow_html=True)

# Features Grid
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <div class="feature-title">Executive Dashboard</div>
        <div class="feature-description">
            Consolidated overview of all analyzed companies with key metrics and investment recommendations.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📈</div>
        <div class="feature-title">Individual Analysis</div>
        <div class="feature-description">
            Complete DCF calculation for a specific company with detailed analysis and advanced visualizations.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">⚖️</div>
        <div class="feature-title">Comparator</div>
        <div class="feature-description">
            Compare multiple companies side by side to identify the best investment opportunities.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📅</div>
        <div class="feature-title">Historical Analysis</div>
        <div class="feature-description">
            Temporal evolution of Fair Value vs Market Price for trend tracking.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Quick Start Section
st.markdown("### 🚀 Quick Start")
st.markdown("""
<div style="background: #1E2338; padding: 2rem; border-radius: 16px; border: 1px solid #2A2F4A;">
    <p style="color: #B4B9D1; font-size: 1.1rem; line-height: 1.8;">
        <strong style="color: #0066FF;">Step 1:</strong> Navigate to <strong>Individual Analysis</strong> from the side menu<br>
        <strong style="color: #0066FF;">Step 2:</strong> Enter the company ticker you want to analyze<br>
        <strong style="color: #0066FF;">Step 3:</strong> Configure DCF parameters (or use intelligent values)<br>
        <strong style="color: #0066FF;">Step 4:</strong> Review the calculated Fair Value and compare with market price
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Navigation Info
st.sidebar.markdown("""
<div style="background: #1E2338; border: 1px solid #0066FF; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 4px 16px rgba(0, 102, 255, 0.2);">
    <h3 style="color: #0066FF; margin: 0 0 0.75rem 0; font-size: 1.2rem; font-weight: 700;">🧭 Navigation</h3>
    <p style="color: #B4B9D1; margin: 0; font-size: 0.95rem; line-height: 1.6;">
        Use the top menu to access each section of the platform.
    </p>
</div>
""", unsafe_allow_html=True)

# Add some spacing and styling to sidebar content
st.sidebar.markdown("""
<style>
[data-testid="stSidebar"] [class*="css"] {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] a {
    color: #B4B9D1 !important;
    font-weight: 500;
    padding: 0.5rem 0;
    display: block;
    transition: all 0.2s ease;
}
[data-testid="stSidebar"] a:hover {
    color: #0066FF !important;
    padding-left: 0.5rem;
}
</style>
""", unsafe_allow_html=True)
