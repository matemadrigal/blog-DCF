#!/usr/bin/env python3
"""
Script to check and predict missing dependencies for the DCF platform.
Run this script to verify all dependencies are installed.
"""

import sys
from src.utils.dependency_checker import (
    check_all_dependencies,
    verify_environment,
    install_missing_dependencies,
    predict_missing_dependencies
)


def main():
    print("=" * 60)
    print("🔍 DCF Platform - Dependency Checker")
    print("=" * 60)
    print()
    
    # Verify environment
    result = verify_environment()
    
    # Check current status
    missing_required, missing_optional = check_all_dependencies()
    
    if result['all_installed']:
        print("✅ Todas las dependencias requeridas están instaladas")
        print()
        
        if missing_optional:
            print("ℹ️  Dependencias opcionales faltantes:")
            for module, error in missing_optional.items():
                print(f"   - {module}: {error}")
            print()
    else:
        print("❌ Dependencias faltantes detectadas:")
        print()
        
        for module, error in missing_required.items():
            print(f"   - {module}")
            print(f"     Error: {error}")
        print()
        
        print("📋 Comando de instalación:")
        print(f"   {result['installation_command']}")
        print()
        
        # Ask if user wants to install
        response = input("¿Deseas instalar las dependencias faltantes? (s/n): ").lower()
        if response in ['s', 'si', 'y', 'yes']:
            print()
            print("📦 Instalando dependencias...")
            success = install_missing_dependencies(list(missing_required.keys()))
            
            if success:
                print()
                print("✅ Instalación completada. Verificando nuevamente...")
                print()
                
                # Re-check
                missing_required, _ = check_all_dependencies()
                if not missing_required:
                    print("✅ Todas las dependencias están ahora instaladas")
                else:
                    print("⚠️  Algunas dependencias aún faltan:")
                    for module, error in missing_required.items():
                        print(f"   - {module}: {error}")
            else:
                print()
                print("❌ Error durante la instalación. Intenta instalarlas manualmente.")
        else:
            print()
            print("ℹ️  Instala las dependencias manualmente cuando estés listo.")
    
    print()
    print("=" * 60)
    
    # Predict future missing dependencies
    predicted = predict_missing_dependencies()
    if predicted:
        print()
        print("🔮 Predicción: Los siguientes módulos podrían faltar en el futuro:")
        for module in predicted:
            print(f"   - {module}")
        print()
        print("💡 Tip: Ejecuta 'pip install -r requirements.txt' para instalar todo")
    
    print()
    return 0 if result['all_installed'] else 1


if __name__ == "__main__":
    sys.exit(main())

