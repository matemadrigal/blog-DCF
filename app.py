"""Main dashboard page for blog-DCF platform - Completely redesigned."""

import streamlit as st
import os

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

# Inject custom CSS with font loading
def load_css():
    import os
    import base64
    from pathlib import Path
    
    # Load CSS file
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
    
    # Load fonts and embed as base64
    font_css = ""
    font_dirs = [
        ("tt gertika", "TT_Gertika_Trial"),
        ("roboto", "Roboto")
    ]
    
    for font_dir, font_name in font_dirs:
        font_paths = [
            os.path.join(font_dir, f"{font_name}_Regular.ttf"),
            os.path.join(font_dir, f"{font_name}_Bold.ttf"),
            os.path.join(font_dir, f"{font_name}_Black.ttf"),
            os.path.join("..", font_dir, f"{font_name}_Regular.ttf"),
            os.path.join("..", font_dir, f"{font_name}_Bold.ttf"),
            os.path.join("..", font_dir, f"{font_name}_Black.ttf"),
        ]
        
        # Add specific font files
        if font_name == "TT_Gertika_Trial":
            font_files = [
                ("Regular", 400, "TT_Gertika_Trial_Regular.ttf"),
                ("Bold", 700, "TT_Gertika_Trial_Bold.ttf"),
                ("Black", 900, "TT_Gertika_Trial_Black.ttf"),
            ]
        else:  # Roboto
            font_files = [
                ("Regular", 400, "Roboto-Regular.ttf"),
                ("Bold", 700, "Roboto-Bold.ttf"),
                ("Black", 900, "Roboto-Black.ttf"),
                ("Light", 300, "Roboto-Light.ttf"),
                ("Medium", 500, "Roboto-Medium.ttf"),
            ]
        
        for variant, weight, filename in font_files:
            font_paths_to_try = [
                os.path.join(font_dir, filename),
                os.path.join("..", font_dir, filename),
                os.path.join(os.path.dirname(__file__), font_dir, filename),
            ]
            
            font_data = None
            for font_path in font_paths_to_try:
                try:
                    if os.path.exists(font_path):
                        with open(font_path, "rb") as f:
                            font_data = base64.b64encode(f.read()).decode("utf-8")
                            # Use proper font family names
                            if font_name == "TT_Gertika_Trial":
                                family_name = "TT Gertika"
                            else:
                                family_name = "Roboto"
                            
                            font_css += f"""
@font-face {{
    font-family: '{family_name}';
    src: url(data:font/truetype;charset=utf-8;base64,{font_data}) format('truetype');
    font-weight: {weight};
    font-style: normal;
    font-display: swap;
}}
"""
                            break
                except Exception:
                    continue
    
    # Combine font CSS with main CSS
    if css_content:
        # Replace @font-face declarations in CSS with embedded ones if we have them
        if font_css:
            # Remove existing @font-face from CSS and prepend our embedded fonts
            import re
            css_content = re.sub(r'@font-face\s*\{[^}]*\}', '', css_content, flags=re.MULTILINE)
            css_content = font_css + css_content
        
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        # Fallback CSS if file doesn't exist
        fallback_css = font_css + """
        <style>
        .stApp { background: #0F0F23; color: #F8FAFC; }
        h1 { background: linear-gradient(135deg, #6366F1 0%, #EC4899 100%);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        </style>
        """
        st.markdown(fallback_css, unsafe_allow_html=True)

load_css()

# Complete Streamlit UI hiding and fix ForwardRef elements
st.markdown("""
<style>
    /* Hide ALL Streamlit UI elements */
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stHeader"],
    .stAppToolbar,
    .stAppHeader,
    [class*="stToolbar"],
    [class*="stHeader"],
    [class*="stDecoration"],
    [class*="st-emotion-cache-14vh5up"],
    [class*="st-emotion-cache-13892zc"],
    button[title*="Settings"],
    button[title*="Menu"],
    button[aria-label*="Settings"],
    button[aria-label*="Menu"],
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        opacity: 0 !important;
        position: absolute !important;
        z-index: -9999 !important;
    }
    
    /* Remove default margins */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Hide Streamlit branding */
    footer {
        display: none !important;
    }
    
    /* Fix ForwardRef elements - make them display contents */
    ForwardRef,
    [class*="ForwardRef"] {
        display: contents !important;
    }
    
    /* Fix expander summary elements */
    summary.st-emotion-cache-pxambx,
    summary.e1326t814,
    [class*="st-emotion-cache-pxambx"],
    [class*="e1326t814"] {
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        background: var(--bg-secondary) !important;
        color: var(--lime-bright) !important;
        padding: 1rem 1.5rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        border: none !important;
        list-style: none !important;
    }
    
    /* Fix metric value displays */
    [class*="st-emotion-cache-1q82h82"],
    [class*="e1wr3kle3"] {
        display: block !important;
        color: var(--lime-bright) !important;
        font-family: 'Roboto', sans-serif !important;
        font-weight: 900 !important;
        font-size: 2rem !important;
    }
</style>

<script>
    // Navigation menu functionality
    document.addEventListener('DOMContentLoaded', function() {
        // Get current page
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.navbar-menu a');
        
        // Mark active link
        navLinks.forEach(link => {
            const onclick = link.getAttribute('onclick');
            if (onclick) {
                const match = onclick.match(/href='([^']+)'/);
                if (match) {
                    const href = match[1];
                    if (currentPath === href || (href === '/' && currentPath === '/')) {
                        link.classList.add('active');
                    }
                }
            }
        });
        
        // Fix ForwardRef elements by unwrapping them
        const fixForwardRefs = () => {
            const forwardRefs = document.querySelectorAll('[class*="ForwardRef"], ForwardRef');
            forwardRefs.forEach(ref => {
                if (ref.children && ref.children.length > 0 && ref.parentNode) {
                    Array.from(ref.children).forEach(child => {
                        ref.parentNode.insertBefore(child.cloneNode(true), ref);
                    });
                    // Don't remove, just make it invisible
                    ref.style.display = 'none';
                } else if (ref.parentNode) {
                    // If no children, just hide it
                    ref.style.display = 'none';
                }
            });
        };
        
        fixForwardRefs();
        
        // Fix expander and metric display issues
        const observer = new MutationObserver(function(mutations) {
        // Fix any new ForwardRef elements that appear
        const fixNewForwardRefs = () => {
            document.querySelectorAll('[class*="ForwardRef"], ForwardRef').forEach(ref => {
                if (ref.children && ref.children.length > 0 && ref.parentNode) {
                    Array.from(ref.children).forEach(child => {
                        if (!ref.parentNode.contains(child) || child.parentNode === ref) {
                            ref.parentNode.insertBefore(child.cloneNode(true), ref);
                        }
                    });
                    ref.style.display = 'none';
                } else if (ref.parentNode) {
                    ref.style.display = 'none';
                }
            });
        };
        
        fixNewForwardRefs();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Also fix expander summaries to ensure text is visible
        const fixExpanderSummaries = () => {
            document.querySelectorAll('summary, [class*="summary"]').forEach(summary => {
                summary.style.color = '#1A1A1A';
                summary.style.visibility = 'visible';
                Array.from(summary.querySelectorAll('*')).forEach(child => {
                    child.style.color = '#1A1A1A';
                    child.style.visibility = 'visible';
                });
            });
        };
        
        fixExpanderSummaries();
        
        // Run fixes periodically to catch dynamically added elements
        setInterval(() => {
            fixForwardRefs();
            fixNewForwardRefs();
            fixExpanderSummaries();
        }, 1000);
    });
</script>
""", unsafe_allow_html=True)

# Static Navigation Menu with Streamlit navigation
st.markdown("""
<div class="static-navbar">
    <a href="#" onclick="window.location.href='/' + window.location.search; return false;" class="navbar-brand">DCF Platform</a>
    <nav>
        <ul class="navbar-menu">
            <li><a href="#" onclick="window.location.href='/' + window.location.search; return false;">Home</a></li>
            <li><a href="#" onclick="window.location.href='/2_📊_Dashboard' + window.location.search; return false;">Dashboard</a></li>
            <li><a href="#" onclick="window.location.href='/1_📈_Análisis_Individual' + window.location.search; return false;">Analysis</a></li>
            <li><a href="#" onclick="window.location.href='/3_⚖️_Comparador' + window.location.search; return false;">Compare</a></li>
            <li><a href="#" onclick="window.location.href='/4_📅_Histórico' + window.location.search; return false;">Historical</a></li>
            <li><a href="#" onclick="window.location.href='/5_🔔_Alertas' + window.location.search; return false;">Alerts</a></li>
        </ul>
    </nav>
</div>
""", unsafe_allow_html=True)

# Hero Section - New Design with Image Aesthetic
st.markdown("""
<div class="hero-section fade-in">
    <h1 class="hero-title">DCF Valuation Platform</h1>
    <p class="hero-subtitle">
        Professional valuation platform that compares <strong style="color: var(--lime-bright);">Fair Value (DCF)</strong> vs <strong style="color: var(--lime-bright);">Market Price</strong>.
        Advanced tool for financial analysis and investment decision-making with cutting-edge design.
    </p>
</div>
""", unsafe_allow_html=True)

# Features Grid - Modern Card Design
st.markdown("""
<div class="feature-grid fade-in-up">
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <div class="feature-title">Executive Dashboard</div>
        <div class="feature-description">
            Consolidated overview of all analyzed companies with key metrics and investment recommendations.
            Track performance across your portfolio with real-time updates.
        </div>
    </div>
    
    <div class="feature-card">
        <div class="feature-icon">📈</div>
        <div class="feature-title">Individual Analysis</div>
        <div class="feature-description">
            Complete DCF calculation for a specific company with detailed analysis and advanced visualizations. 
            Get comprehensive insights into company valuation, cash flow projections, and fair value estimates. 
            Analyze growth rates, terminal values, and sensitivity scenarios to make informed investment decisions.
        </div>
    </div>
    
    <div class="feature-card">
        <div class="feature-icon">⚖️</div>
        <div class="feature-title">Comparator</div>
        <div class="feature-description">
            Compare multiple companies side by side to identify the best investment opportunities.
            Make informed decisions with comparative analysis.
        </div>
    </div>
    
    <div class="feature-card">
        <div class="feature-icon">📅</div>
        <div class="feature-title">Historical Analysis</div>
        <div class="feature-description">
            Temporal evolution of Fair Value vs Market Price for trend tracking.
            Understand valuation trends over time.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Quick Start Section - Redesigned
st.markdown("""
<div style="max-width: 1200px; margin: 4rem auto; padding: 0 2rem;">
    <h2 style="text-align: center; margin-bottom: 2rem; font-family: 'Roboto', sans-serif;">
        <span class="text-gradient">Quick Start Guide</span>
    </h2>
    <div class="data-card" style="padding: 3rem;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem;">
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">1️⃣</div>
                <h3 style="font-family: 'Roboto', sans-serif; margin-bottom: 0.5rem; color: var(--lime-bright);">Navigate</h3>
                <p style="font-family: 'TT Gertika', sans-serif; color: var(--text-on-dark);">
                    Go to <strong style="color: var(--lime-medium);">Individual Analysis</strong> from the top menu
                </p>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">2️⃣</div>
                <h3 style="font-family: 'Roboto', sans-serif; margin-bottom: 0.5rem; color: var(--lime-bright);">Enter Ticker</h3>
                <p style="font-family: 'TT Gertika', sans-serif; color: var(--text-on-dark);">
                    Enter the company ticker you want to analyze
                </p>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">3️⃣</div>
                <h3 style="font-family: 'Roboto', sans-serif; margin-bottom: 0.5rem; color: var(--lime-bright);">Configure</h3>
                <p style="font-family: 'TT Gertika', sans-serif; color: var(--text-on-dark);">
                    Configure DCF parameters or use intelligent defaults
                </p>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">4️⃣</div>
                <h3 style="font-family: 'Roboto', sans-serif; margin-bottom: 0.5rem; color: var(--lime-bright);">Review</h3>
                <p style="font-family: 'TT Gertika', sans-serif; color: var(--text-on-dark);">
                    Review Fair Value and compare with market price
                </p>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar - Redesigned with New Aesthetic
st.sidebar.markdown("""
<div style="background: var(--bg-card); border: 2px solid var(--lime-medium); padding: 2rem; border-radius: var(--radius-lg); margin-bottom: 2rem; box-shadow: var(--shadow-md), var(--shadow-lime);">
    <h3 style="font-family: 'Roboto', sans-serif; color: var(--lime-bright); margin: 0 0 1rem 0; font-size: 1.3rem; font-weight: 700;">🧭 Navigation</h3>
    <p style="font-family: 'TT Gertika', sans-serif; color: var(--text-on-dark); margin: 0; font-size: 0.95rem; line-height: 1.8;">
        Use the top navigation menu to access each section of the platform. All features are designed for professional financial analysis with a modern, sleek interface.
    </p>
</div>
""", unsafe_allow_html=True)

# Additional styling for sidebar and hide ForwardRef
st.sidebar.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 2px solid var(--lime-medium) !important;
    }
    
    [data-testid="stSidebar"] * {
        font-family: 'TT Gertika', sans-serif !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-family: 'Roboto', sans-serif !important;
        color: var(--lime-bright) !important;
    }
    
    /* Hide ForwardRef elements */
    ForwardRef,
    [class*="ForwardRef"] {
        display: contents !important;
        visibility: visible !important;
    }
    
    /* Fix expander styling */
    .stExpander summary {
        background: var(--bg-secondary) !important;
        color: var(--lime-bright) !important;
    }
    
    /* Fix metric values */
    [class*="st-emotion-cache-1q82h82"],
    [class*="e1wr3kle3"] {
        color: var(--lime-bright) !important;
        font-family: 'Roboto', sans-serif !important;
        font-weight: 900 !important;
    }
</style>
""", unsafe_allow_html=True)
