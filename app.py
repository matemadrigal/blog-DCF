"""Main dashboard page for blog-DCF platform."""

import streamlit as st

st.set_page_config(
    page_title="DCF Valuation Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 DCF Valuation Platform")
st.markdown(
    """
Plataforma de valoración que compara **Fair Value (DCF)** vs **Precio de Mercado**.

### 🚀 Funcionalidades:
- **Dashboard**: Resumen ejecutivo de empresas analizadas
- **Análisis Individual**: DCF completo para una empresa específica
- **Comparador**: Compara múltiples empresas lado a lado
- **Histórico**: Evolución temporal Fair Value vs Precio

### 📌 Navegación:
Usa la barra lateral para acceder a cada sección.
"""
)

st.sidebar.success("Selecciona una página arriba ☝️")

st.markdown("---")
st.info("💡 **Tip**: Comienza con 'Análisis Individual' para calcular tu primer DCF.")
