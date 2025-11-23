"""Dependency checker and error handler for the DCF platform."""

import sys
import importlib
from typing import List, Tuple, Optional


# Required dependencies with their import names
REQUIRED_DEPENDENCIES = {
    'pandas': 'pandas',
    'numpy': 'numpy',
    'yfinance': 'yfinance',
    'requests': 'requests',
    'matplotlib': 'matplotlib',
    'plotly': 'plotly',
    'scipy': 'scipy',
    'statsmodels': 'statsmodels',
    'streamlit': 'streamlit',
    'jinja2': 'jinja2',
    'reportlab': 'reportlab',
    'openpyxl': 'openpyxl',
}

# Optional dependencies (nice to have but not critical)
OPTIONAL_DEPENDENCIES = {
    'pytest': 'pytest',
}


def check_dependency(module_name: str, import_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Check if a dependency is installed.
    
    Args:
        module_name: Name of the module to check
        import_name: Optional different import name
        
    Returns:
        Tuple of (is_installed, error_message)
    """
    import_name = import_name or module_name
    
    try:
        importlib.import_module(import_name)
        return True, None
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def check_all_dependencies() -> Tuple[dict, dict]:
    """
    Check all required and optional dependencies.
    
    Returns:
        Tuple of (missing_required, missing_optional)
    """
    missing_required = {}
    missing_optional = {}
    
    # Check required dependencies
    for module_name, import_name in REQUIRED_DEPENDENCIES.items():
        is_installed, error = check_dependency(module_name, import_name)
        if not is_installed:
            missing_required[module_name] = error
    
    # Check optional dependencies
    for module_name, import_name in OPTIONAL_DEPENDENCIES.items():
        is_installed, error = check_dependency(module_name, import_name)
        if not is_installed:
            missing_optional[module_name] = error
    
    return missing_required, missing_optional


def get_installation_command(missing_modules: List[str]) -> str:
    """
    Generate pip install command for missing modules.
    
    Args:
        missing_modules: List of module names
        
    Returns:
        pip install command string
    """
    return f"pip install {' '.join(missing_modules)}"


def predict_missing_dependencies() -> List[str]:
    """
    Predict which dependencies might be missing based on common patterns.
    
    Returns:
        List of potentially missing module names
    """
    missing_required, _ = check_all_dependencies()
    return list(missing_required.keys())


def install_missing_dependencies(missing_modules: List[str], verbose: bool = True) -> bool:
    """
    Attempt to install missing dependencies.
    
    Args:
        missing_modules: List of module names to install
        verbose: Whether to print installation progress
        
    Returns:
        True if installation successful, False otherwise
    """
    import subprocess
    
    if not missing_modules:
        return True
    
    try:
        cmd = [sys.executable, '-m', 'pip', 'install'] + missing_modules
        if verbose:
            print(f"Installing missing dependencies: {', '.join(missing_modules)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            if verbose:
                print("✅ Successfully installed all dependencies")
            return True
        else:
            if verbose:
                print(f"❌ Installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        if verbose:
            print(f"❌ Error during installation: {str(e)}")
        return False


def verify_environment() -> dict:
    """
    Comprehensive environment verification.
    
    Returns:
        Dictionary with verification results
    """
    missing_required, missing_optional = check_all_dependencies()
    
    all_installed = len(missing_required) == 0
    
    result = {
        'all_installed': all_installed,
        'missing_required': missing_required,
        'missing_optional': missing_optional,
        'installation_command': get_installation_command(list(missing_required.keys())) if missing_required else None,
        'predicted_missing': predict_missing_dependencies(),
    }
    
    return result

