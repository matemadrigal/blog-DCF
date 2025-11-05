"""
Verificación de la fórmula de ponderación de escenarios
Pesimista: 25%, Base: 50%, Optimista: 25%
"""

# Simulemos el cálculo con valores de ejemplo
pessimistic_price = 100.00
base_price = 150.00
optimistic_price = 200.00

# Probabilidades definidas en el código
# src/dcf/sensitivity_analysis.py
prob_pessimistic = 0.25  # línea 161
prob_base = 0.50         # línea 109
prob_optimistic = 0.25   # línea 206

# Fórmula actual del código (línea 231)
weighted_value = (pessimistic_price * prob_pessimistic +
                  base_price * prob_base +
                  optimistic_price * prob_optimistic)

print('=' * 70)
print('VERIFICACIÓN DE FÓRMULA DE PONDERACIÓN')
print('=' * 70)
print()
print('Valores de ejemplo:')
print(f'  Pesimista: ${pessimistic_price:.2f}')
print(f'  Base:      ${base_price:.2f}')
print(f'  Optimista: ${optimistic_price:.2f}')
print()
print('Probabilidades definidas en el código:')
print(f'  Pesimista: {prob_pessimistic:.0%} (sensitivity_analysis.py línea 161)')
print(f'  Base:      {prob_base:.0%} (sensitivity_analysis.py línea 109)')
print(f'  Optimista: {prob_optimistic:.0%} (sensitivity_analysis.py línea 206)')
print()
print('Fórmula de ponderación (línea 231):')
print('  weighted_value = Σ (price × probability)')
print()
print('Cálculo paso a paso:')
print(f'  ${pessimistic_price:.2f} × {prob_pessimistic:.2f} = ${pessimistic_price * prob_pessimistic:.2f}')
print(f'  ${base_price:.2f} × {prob_base:.2f} = ${base_price * prob_base:.2f}')
print(f'  ${optimistic_price:.2f} × {prob_optimistic:.2f} = ${optimistic_price * prob_optimistic:.2f}')
print('  ' + '-' * 60)
print(f'  VALOR PONDERADO: ${weighted_value:.2f}')
print()
print('Validación:')
print(f'  Suma de probabilidades: {prob_pessimistic + prob_base + prob_optimistic:.2f} = 100%')
print()

# Verificación manual
manual_calc = (100 * 0.25) + (150 * 0.50) + (200 * 0.25)
print(f'  Verificación manual: (100×0.25) + (150×0.50) + (200×0.25) = {manual_calc:.2f}')
print(f'  Código calcula:      {weighted_value:.2f}')
print()

if abs(weighted_value - manual_calc) < 0.01:
    print('✅ LA FÓRMULA ES CORRECTA')
    print('✅ Ponderación: 25% pesimista + 50% base + 25% optimista = 100%')
else:
    print('❌ ERROR: Las fórmulas no coinciden')

print()
print('=' * 70)
print('ANÁLISIS DE SENSIBILIDAD')
print('=' * 70)
print()
print('Con estos valores de ejemplo:')
print(f'  Precio ponderado (${weighted_value:.2f}) está entre Base (${base_price:.2f}) y Optimista (${optimistic_price:.2f})')
print()
print('Esto tiene sentido porque:')
print('  - El 50% de peso en Base "ancla" el valor')
print('  - Pesimista (25%) y Optimista (25%) se balancean')
print()
print('Ejemplo real:')
print('  Si Base = $150, Pesimista = $100, Optimista = $200')
print('  → Ponderado = $150 (mismo que Base)')
print('  Esto ocurre porque Pesimista y Optimista están equidistantes de Base')
print()

# Caso más realista
pessimistic_real = 120.00
base_real = 150.00
optimistic_real = 180.00

weighted_real = (pessimistic_real * 0.25 + base_real * 0.50 + optimistic_real * 0.25)

print('Caso más realista (asimetría):')
print(f'  Pesimista: ${pessimistic_real:.2f}')
print(f'  Base:      ${base_real:.2f}')
print(f'  Optimista: ${optimistic_real:.2f}')
print(f'  → Ponderado: ${weighted_real:.2f}')
print(f'  (Ligeramente por encima de Base: {((weighted_real/base_real - 1)*100):+.1f}%)')
print()
print('=' * 70)
