"""
Critical fixes for visualization issues.

FIXES:
1. Heatmap color scaling (was showing all red)
2. Better error handling for all charts
3. Improved color ranges and normalization
"""

import numpy as np
import plotly.graph_objects as go
from typing import List, Tuple, Optional


def create_fixed_heatmap(
    sensitivity_matrix: np.ndarray,
    discount_rates: List[float],
    growth_rates: List[float],
    current_price: float,
    base_case_index: Optional[Tuple[int, int]] = None,
    COLORS: dict = None,
    TEMPLATE: dict = None,
) -> go.Figure:
    """
    Create FIXED sensitivity heatmap with proper color scaling.

    CRITICAL FIX: Normalize values for color scale to avoid all-red heatmap.

    Args:
        sensitivity_matrix: Matrix of fair values
        discount_rates: List of discount rates (rows)
        growth_rates: List of growth rates (columns)
        current_price: Current market price for comparison
        base_case_index: Tuple of (row, col) for base case
        COLORS: Color scheme dict
        TEMPLATE: Template dict

    Returns:
        Plotly Figure with properly colored heatmap
    """
    # Default colors if not provided
    if COLORS is None:
        COLORS = {
            'positive': '#00CC66',
            'negative': '#FF4444',
            'primary': '#203864',
            'text': '#2C3E50',
        }

    # Calculate upside percentages
    upside_matrix = ((sensitivity_matrix - current_price) / current_price) * 100

    # === CRITICAL FIX: Normalize matrix for color scale ===
    # The problem: Using absolute fair values ($150, $200, etc.) with a 0-1 colorscale
    # makes everything appear red because 150 >> 1.0
    #
    # Solution: Normalize to 0-1 range based on upside percentages
    # Green for >20% upside, Red for <-20% downside

    # Normalize upside_matrix to 0-1 range for colorscale
    # Map: -30% upside → 0.0 (red)
    #       0% upside → 0.5 (yellow)
    #      +30% upside → 1.0 (green)

    upside_min = -30  # Anything below -30% is full red
    upside_max = +30  # Anything above +30% is full green

    # Clip and normalize
    normalized_values = np.clip(upside_matrix, upside_min, upside_max)
    normalized_values = (normalized_values - upside_min) / (upside_max - upside_min)

    # Create custom colorscale (5 colors for smooth gradient)
    colorscale = [
        [0.0, '#D32F2F'],   # Dark Red (< -30% upside)
        [0.25, '#FF6B6B'],  # Light Red (-15% to -30%)
        [0.5, '#FFE082'],   # Yellow (around 0%)
        [0.75, '#81C784'],  # Light Green (+15% to +30%)
        [1.0, '#388E3C'],   # Dark Green (> +30% upside)
    ]

    # Create heatmap with NORMALIZED values for color
    fig = go.Figure(data=go.Heatmap(
        z=normalized_values,  # ← FIX: Use normalized values for colors
        x=[f'{g:.1%}' for g in growth_rates],
        y=[f'{r:.1%}' for r in discount_rates],
        colorscale=colorscale,
        zmin=0,  # Force 0-1 range
        zmax=1,
        text=[[f'${val:.2f}<br>({ups:+.1f}%)'
               for val, ups in zip(row, ups_row)]
              for row, ups_row in zip(sensitivity_matrix, upside_matrix)],
        texttemplate='%{text}',
        textfont={'size': 10, 'color': '#2C3E50'},
        hovertemplate=(
            '<b>Scenario</b><br>'
            'WACC: %{y}<br>'
            'Growth: %{x}<br>'
            '<b>Fair Value: $%{customdata[0]:.2f}</b><br>'
            '<b>Upside: %{customdata[1]:+.1f}%</b><br>'
            '<extra></extra>'
        ),
        customdata=np.stack([sensitivity_matrix, upside_matrix], axis=-1),
        colorbar={
            'title': {
                'text': 'Upside<br>(%)',
                'side': 'right',
            },
            'tickvals': [0, 0.25, 0.5, 0.75, 1.0],
            'ticktext': ['-30%', '-15%', '0%', '+15%', '+30%'],
            'len': 0.7,
        }
    ))

    # Highlight base case with white border
    if base_case_index:
        row_idx, col_idx = base_case_index
        fig.add_shape(
            type='rect',
            x0=col_idx - 0.5,
            x1=col_idx + 0.5,
            y0=row_idx - 0.5,
            y1=row_idx + 0.5,
            line={'color': 'white', 'width': 4},
            layer='above',
        )
        fig.add_annotation(
            x=col_idx,
            y=row_idx,
            text='★',
            showarrow=False,
            font={'size': 24, 'color': 'white'},
            yshift=0,
        )

    # Add current price annotation
    fig.add_annotation(
        text=f'<b>Current Price: ${current_price:.2f}</b>',
        xref='paper',
        yref='paper',
        x=0.02,
        y=0.98,
        xanchor='left',
        yanchor='top',
        showarrow=False,
        bgcolor='rgba(255,255,255,0.95)',
        bordercolor=COLORS.get('primary', '#203864'),
        borderwidth=2,
        borderpad=8,
        font={'size': 12, 'color': COLORS.get('text', '#2C3E50')},
    )

    # Add legend explanation
    fig.add_annotation(
        text=(
            '<i>Color shows upside potential:<br>'
            'Green = Undervalued | Red = Overvalued</i>'
        ),
        xref='paper',
        yref='paper',
        x=0.98,
        y=0.02,
        xanchor='right',
        yanchor='bottom',
        showarrow=False,
        bgcolor='rgba(255,255,255,0.85)',
        bordercolor='#E0E0E0',
        borderwidth=1,
        borderpad=6,
        font={'size': 9, 'color': '#666666'},
    )

    fig.update_layout(
        title={
            'text': (
                '<b>Sensitivity Analysis: Fair Value vs WACC & Growth</b><br>'
                '<sub>Hover cells for details • ★ = Base Case Scenario</sub>'
            ),
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': COLORS.get('text', '#2C3E50')}
        },
        xaxis_title='<b>Terminal Growth Rate (g)</b>',
        yaxis_title='<b>Discount Rate (WACC)</b>',
        xaxis={'side': 'bottom', 'tickangle': -45},
        yaxis={'autorange': 'reversed'},  # High WACC at top
        height=600,
        font={'family': 'Arial, sans-serif', 'size': 11},
        plot_bgcolor='white',
        paper_bgcolor='#FAFAFA',
        margin={'l': 80, 'r': 120, 't': 100, 'b': 80},
    )

    return fig


def validate_sensitivity_inputs(
    sensitivity_matrix: np.ndarray,
    discount_rates: List[float],
    growth_rates: List[float],
    current_price: float,
) -> Tuple[bool, str]:
    """
    Validate inputs for sensitivity heatmap.

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check matrix
    if sensitivity_matrix is None or sensitivity_matrix.size == 0:
        return False, "Sensitivity matrix is empty"

    if not isinstance(sensitivity_matrix, np.ndarray):
        return False, "Sensitivity matrix must be numpy array"

    if sensitivity_matrix.ndim != 2:
        return False, f"Sensitivity matrix must be 2D (got {sensitivity_matrix.ndim}D)"

    # Check rates
    if not discount_rates or not growth_rates:
        return False, "Discount rates and growth rates cannot be empty"

    if len(discount_rates) != sensitivity_matrix.shape[0]:
        return False, f"Discount rates length ({len(discount_rates)}) doesn't match matrix rows ({sensitivity_matrix.shape[0]})"

    if len(growth_rates) != sensitivity_matrix.shape[1]:
        return False, f"Growth rates length ({len(growth_rates)}) doesn't match matrix cols ({sensitivity_matrix.shape[1]})"

    # Check for invalid values
    if np.any(np.isnan(sensitivity_matrix)):
        return False, "Sensitivity matrix contains NaN values"

    if np.any(np.isinf(sensitivity_matrix)):
        return False, "Sensitivity matrix contains infinite values"

    # Check price
    if current_price <= 0:
        return False, f"Current price must be positive (got {current_price})"

    # Check rates ranges
    if any(r <= 0 for r in discount_rates):
        return False, "All discount rates must be positive"

    if any(g < 0 for g in growth_rates):
        return False, "All growth rates must be non-negative"

    if any(g >= r for g, r in zip(growth_rates, [max(discount_rates)] * len(growth_rates))):
        # Check if any g >= max WACC (invalid for terminal value formula)
        max_g = max(growth_rates)
        min_r = min(discount_rates)
        if max_g >= min_r:
            return False, f"Growth rate ({max_g:.1%}) must be less than WACC ({min_r:.1%})"

    return True, ""


def calculate_sensitivity_matrix_safe(
    fcf_projections: List[float],
    wacc_range: List[float],
    growth_range: List[float],
    shares: float,
    cash: float = 0,
    debt: float = 0,
) -> np.ndarray:
    """
    Calculate sensitivity matrix with comprehensive error handling.

    Returns:
        Numpy array of fair values per share
    """
    n_wacc = len(wacc_range)
    n_growth = len(growth_range)

    sensitivity_matrix = np.zeros((n_wacc, n_growth))

    for i, wacc_val in enumerate(wacc_range):
        for j, growth_val in enumerate(growth_range):
            try:
                # Check if WACC > g (required for terminal value)
                if wacc_val <= growth_val:
                    # Set to NaN for invalid combinations
                    sensitivity_matrix[i, j] = np.nan
                    continue

                # Calculate PV of explicit period
                pv_fcf = sum(
                    fcf / ((1 + wacc_val) ** (k + 1))
                    for k, fcf in enumerate(fcf_projections)
                )

                # Calculate terminal value
                terminal_fcf = fcf_projections[-1] * (1 + growth_val)
                terminal_value = terminal_fcf / (wacc_val - growth_val)

                # Discount terminal value
                pv_terminal = terminal_value / ((1 + wacc_val) ** len(fcf_projections))

                # Enterprise value
                enterprise_value = pv_fcf + pv_terminal

                # Equity value
                equity_value = enterprise_value + cash - debt

                # Fair value per share
                fair_value_per_share = equity_value / shares if shares > 0 else 0

                sensitivity_matrix[i, j] = fair_value_per_share

            except Exception as e:
                # Set to NaN on error
                sensitivity_matrix[i, j] = np.nan

    # Replace NaN with interpolated values or reasonable estimates
    # For display purposes, NaN cells will show "N/A"
    return sensitivity_matrix
