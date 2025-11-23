"""Error handling utilities for the DCF platform."""

import streamlit as st
import traceback
from typing import Optional
from .dependency_checker import check_all_dependencies, get_installation_command


def handle_import_error(error: Exception, module_name: str) -> None:
    """
    Handle import errors gracefully in Streamlit.
    
    Args:
        error: The ImportError exception
        module_name: Name of the missing module
    """
    st.error(f"""
    **Dependency Error: Module '{module_name}' not found**
    
    The required module `{module_name}` is not installed in your environment.
    
    **Solution:**
    ```bash
    pip install {module_name}
    ```
    
    Or install all dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    """)
    
    # Show installation help
    with st.expander("🔧 Installation Help", expanded=True):
        st.code(f"pip install {module_name}", language="bash")
        st.markdown(f"Or from the project directory:")
        st.code("pip install -r requirements.txt", language="bash")


def handle_generic_error(error: Exception, context: Optional[str] = None) -> None:
    """
    Handle generic errors gracefully in Streamlit.
    
    Args:
        error: The exception
        context: Optional context about where the error occurred
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    st.error(f"""
    **Error: {error_type}**
    
    {f'**Context:** {context}' if context else ''}
    
    **Message:** {error_message}
    """)
    
    with st.expander("🔍 Technical Details", expanded=False):
        st.code(traceback.format_exc(), language="python")


def check_dependencies_on_startup() -> bool:
    """
    Check dependencies when the app starts and show warnings if needed.
    
    Returns:
        True if all required dependencies are installed
    """
    missing_required, missing_optional = check_all_dependencies()
    
    if missing_required:
        st.error(f"""
        **⚠️ Missing Dependencies Detected**
        
        The following required modules are not installed:
        - {', '.join(missing_required.keys())}
        
        **Installation:**
        ```bash
        {get_installation_command(list(missing_required.keys()))}
        ```
        """)
        return False
    
    if missing_optional:
        st.warning(f"""
        **ℹ️ Missing Optional Dependencies**
        
        The following optional modules are not installed (not critical):
        - {', '.join(missing_optional.keys())}
        """)
    
    return True


def safe_import(module_name: str, import_name: Optional[str] = None, fallback=None):
    """
    Safely import a module with error handling.
    
    Args:
        module_name: Name of the module
        import_name: Optional different import name
        fallback: Optional fallback value if import fails
        
    Returns:
        Imported module or fallback
    """
    import_name = import_name or module_name
    
    try:
        return __import__(import_name)
    except ImportError as e:
        handle_import_error(e, module_name)
        if fallback is not None:
            return fallback
        st.stop()
        return None

