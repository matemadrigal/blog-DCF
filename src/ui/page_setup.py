"""Shared page setup utilities to eliminate duplication across pages."""

import os
import logging
from pathlib import Path
import streamlit as st

logger = logging.getLogger(__name__)


def load_custom_css() -> None:
    """Load custom CSS from assets folder with multiple path fallbacks."""
    css_paths = [
        Path("assets/custom.css"),
        Path("./assets/custom.css"),
        Path(__file__).parent.parent.parent / "assets" / "custom.css"
    ]

    css_content = None
    for path in css_paths:
        try:
            css_content = path.read_text(encoding="utf-8")
            logger.debug(f"Loaded CSS from {path}")
            break
        except FileNotFoundError:
            continue
        except Exception as e:
            logger.warning(f"Error loading CSS from {path}: {e}")
            continue

    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        logger.warning("Custom CSS file not found, using fallback styles")
        # Fallback CSS if file doesn't exist
        st.markdown("""
        <style>
        .stApp { background: #0A0E27; color: #FFFFFF; }
        h1 { background: linear-gradient(135deg, #0066FF 0%, #00D4AA 100%);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        </style>
        """, unsafe_allow_html=True)


def hide_streamlit_toolbar() -> None:
    """Hide Streamlit's default toolbar for cleaner UI."""
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


def setup_page(
    title: str,
    icon: str = "💼",
    layout: str = "wide",
    initial_sidebar_state: str = "expanded",
    load_css: bool = True,
    hide_toolbar: bool = True
) -> None:
    """
    Unified page setup for all Streamlit pages.

    Args:
        title: Page title
        icon: Page icon emoji
        layout: Layout mode ("wide" or "centered")
        initial_sidebar_state: Sidebar state ("expanded" or "collapsed")
        load_css: Whether to load custom CSS
        hide_toolbar: Whether to hide Streamlit toolbar
    """
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state=initial_sidebar_state,
    )

    if load_css:
        load_custom_css()

    if hide_toolbar:
        hide_streamlit_toolbar()

    logger.info(f"Page setup complete: {title}")


def render_hero(title: str, subtitle: str) -> None:
    """
    Render a modern hero section with gradient title.

    Args:
        title: Main title text
        subtitle: Subtitle text
    """
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <h1 style="background: linear-gradient(135deg, #0066FF 0%, #00D4AA 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem;">
            {title}
        </h1>
        <p style="color: #B4B9D1; font-size: 1.1rem;">
            {subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)
