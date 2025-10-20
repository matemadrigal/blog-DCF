"""Enhanced interactive charts for DCF analysis.

This module provides professional, publication-ready charts with:
- Waterfall charts for DCF breakdown
- Enhanced heatmaps with annotations
- Animated temporal charts
- Export capabilities (PNG, SVG, HTML)
"""

from typing import List, Dict, Optional, Any, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import io


class EnhancedChartGenerator:
    """Generate enhanced interactive charts for DCF analysis."""

    # Professional color schemes
    COLORS = {
        'positive': '#00CC66',  # Green
        'negative': '#FF4444',  # Red
        'neutral': '#FFB366',   # Orange
        'primary': '#203864',   # Dark blue
        'secondary': '#4A90E2', # Light blue
        'accent': '#F5A623',    # Gold
        'background': '#F8F9FA',
        'text': '#2C3E50',
        'grid': '#E8E8E8',
    }

    # Chart templates
    TEMPLATE = {
        'layout': {
            'font': {'family': 'Arial, sans-serif', 'size': 12, 'color': '#2C3E50'},
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white',
            'hovermode': 'closest',
            'margin': {'l': 60, 'r': 60, 't': 80, 'b': 60},
        }
    }

    def __init__(self):
        """Initialize the chart generator."""
        pass

    def create_waterfall_chart(
        self,
        ticker: str,
        base_fcf: float,
        projected_fcf: List[float],
        pv_fcf: List[float],
        terminal_value: float,
        pv_terminal: float,
        enterprise_value: float,
        cash: float,
        debt: float,
        equity_value: float,
        shares: float,
        fair_value_per_share: float,
    ) -> go.Figure:
        """
        Create a waterfall chart showing DCF value breakdown.

        This chart visually shows how we get from base FCF to fair value per share.

        Args:
            ticker: Stock ticker
            base_fcf: Base year FCF
            projected_fcf: List of projected FCF
            pv_fcf: List of present values of FCF
            terminal_value: Terminal value
            pv_terminal: Present value of terminal value
            enterprise_value: Enterprise value
            cash: Cash and equivalents
            debt: Total debt
            equity_value: Equity value
            shares: Shares outstanding
            fair_value_per_share: Fair value per share

        Returns:
            Plotly Figure with waterfall chart
        """
        # Calculate components
        total_pv_fcf = sum(pv_fcf)

        # Build waterfall data
        labels = [
            'PV FCF (5Y)',
            'PV Terminal',
            'Enterprise Value',
            '+ Cash',
            '- Debt',
            'Equity Value',
            '÷ Shares',
            'Fair Value/Share'
        ]

        values = [
            total_pv_fcf,
            pv_terminal,
            0,  # Subtotal (EV = PV FCF + PV Terminal)
            cash,
            -debt,
            0,  # Subtotal (Equity = EV + Cash - Debt)
            0,  # Division operation (visual only)
            fair_value_per_share / 1e9 if fair_value_per_share > 1e6 else fair_value_per_share,
        ]

        # Normalize to billions for readability
        if enterprise_value > 1e9:
            values = [v / 1e9 if abs(v) > 1e6 else v for v in values]
            units = 'B'
        elif enterprise_value > 1e6:
            values = [v / 1e6 if abs(v) > 1e3 else v for v in values]
            units = 'M'
        else:
            units = ''

        # Measure types for waterfall
        measures = ['relative', 'relative', 'total', 'relative', 'relative', 'total', 'relative', 'total']

        # Colors
        colors = [
            self.COLORS['primary'],
            self.COLORS['primary'],
            self.COLORS['secondary'],
            self.COLORS['positive'],
            self.COLORS['negative'],
            self.COLORS['secondary'],
            self.COLORS['neutral'],
            self.COLORS['accent'],
        ]

        # Create waterfall
        fig = go.Figure(go.Waterfall(
            name=ticker,
            orientation='v',
            measure=measures,
            x=labels,
            y=values,
            text=[f'${v:.2f}{units}' if i < 6 else (f'{shares/1e9:.2f}B shares' if i == 6 else f'${v:.2f}')
                  for i, v in enumerate(values)],
            textposition='outside',
            connector={'line': {'color': self.COLORS['grid'], 'width': 2, 'dash': 'dot'}},
            decreasing={'marker': {'color': self.COLORS['negative']}},
            increasing={'marker': {'color': self.COLORS['positive']}},
            totals={'marker': {'color': self.COLORS['accent']}},
        ))

        fig.update_layout(
            title={
                'text': f'DCF Waterfall - {ticker}<br><sub>From Cash Flows to Fair Value</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': self.COLORS['text'], 'family': 'Arial, sans-serif'}
            },
            yaxis_title=f'Value (${units})' if units else 'Value ($)',
            xaxis_title='',
            showlegend=False,
            height=500,
            font=self.TEMPLATE['layout']['font'],
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='x unified',
            xaxis={'tickangle': -45},
        )

        return fig

    def create_enhanced_heatmap(
        self,
        sensitivity_matrix: np.ndarray,
        discount_rates: List[float],
        growth_rates: List[float],
        current_price: float,
        base_case_index: Tuple[int, int] = None,
    ) -> go.Figure:
        """
        Create enhanced sensitivity heatmap with annotations and highlights.

        Args:
            sensitivity_matrix: Matrix of fair values
            discount_rates: List of discount rates (rows)
            growth_rates: List of growth rates (columns)
            current_price: Current market price for comparison
            base_case_index: Tuple of (row, col) for base case

        Returns:
            Plotly Figure with enhanced heatmap
        """
        # Calculate upside percentages
        upside_matrix = ((sensitivity_matrix - current_price) / current_price) * 100

        # === CRITICAL FIX: Normalize for proper color scaling ===
        # Problem: Using absolute values ($150, $200) with 0-1 colorscale makes everything red
        # Solution: Normalize based on upside percentages
        upside_min = -30  # Below -30% upside = full red
        upside_max = +30  # Above +30% upside = full green

        # Clip and normalize to 0-1 range
        normalized_values = np.clip(upside_matrix, upside_min, upside_max)
        normalized_values = (normalized_values - upside_min) / (upside_max - upside_min)

        # Create custom colorscale (smooth gradient)
        colorscale = [
            [0.0, '#D32F2F'],   # Dark Red (< -30% upside)
            [0.25, '#FF6B6B'],  # Light Red (-15% to -30%)
            [0.5, '#FFE082'],   # Yellow (around 0%)
            [0.75, '#81C784'],  # Light Green (+15% to +30%)
            [1.0, '#388E3C'],   # Dark Green (> +30% upside)
        ]

        # Create heatmap with NORMALIZED values for proper coloring
        fig = go.Figure(data=go.Heatmap(
            z=normalized_values,  # ← FIX: Use normalized values instead of absolute
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

        # Highlight base case
        if base_case_index:
            row_idx, col_idx = base_case_index
            fig.add_shape(
                type='rect',
                x0=col_idx - 0.5,
                x1=col_idx + 0.5,
                y0=row_idx - 0.5,
                y1=row_idx + 0.5,
                line={'color': 'white', 'width': 4},
            )
            fig.add_annotation(
                x=col_idx,
                y=row_idx,
                text='★',
                showarrow=False,
                font={'size': 20, 'color': 'white'},
            )

        # Add current price line annotation
        fig.add_annotation(
            text=f'Current Price: ${current_price:.2f}',
            xref='paper',
            yref='paper',
            x=0.02,
            y=0.98,
            showarrow=False,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor=self.COLORS['primary'],
            borderwidth=2,
            borderpad=5,
            font={'size': 11, 'color': self.COLORS['text']},
        )

        fig.update_layout(
            title={
                'text': 'Sensitivity Analysis: Fair Value vs WACC & Growth<br><sub>Hover for details • ★ = Base Case</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16, 'color': self.COLORS['text']}
            },
            xaxis_title='Terminal Growth Rate (g)',
            yaxis_title='Discount Rate (WACC)',
            height=550,
            font=self.TEMPLATE['layout']['font'],
            plot_bgcolor='white',
            paper_bgcolor='white',
        )

        return fig

    def create_animated_temporal_chart(
        self,
        dates: List[datetime],
        fair_values: List[float],
        market_prices: List[float],
        ticker: str,
        animate: bool = True,
    ) -> go.Figure:
        """
        Create animated temporal evolution chart.

        Args:
            dates: List of dates
            fair_values: List of fair value per share
            market_prices: List of market prices
            ticker: Stock ticker
            animate: Whether to add animation (default True)

        Returns:
            Plotly Figure with temporal chart (optionally animated)
        """
        # Create figure with secondary y-axis
        fig = make_subplots(
            rows=2,
            cols=1,
            row_heights=[0.7, 0.3],
            subplot_titles=(
                f'{ticker} - Fair Value vs Market Price',
                'Upside/Downside (%)'
            ),
            vertical_spacing=0.12,
        )

        # Main chart - Fair Value and Price
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=market_prices,
                mode='lines',
                name='Market Price',
                line={'color': self.COLORS['primary'], 'width': 2.5},
                hovertemplate='%{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>',
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=fair_values,
                mode='lines+markers',
                name='Fair Value (DCF)',
                line={'color': self.COLORS['accent'], 'width': 2.5, 'dash': 'dash'},
                marker={'size': 6, 'symbol': 'diamond'},
                hovertemplate='%{x|%Y-%m-%d}<br>Fair Value: $%{y:.2f}<extra></extra>',
            ),
            row=1,
            col=1,
        )

        # Calculate upside
        upside = [((fv - mp) / mp) * 100 if mp > 0 else 0
                  for fv, mp in zip(fair_values, market_prices)]

        # Upside chart with color coding
        colors = [self.COLORS['positive'] if u > 10 else
                  (self.COLORS['negative'] if u < -10 else self.COLORS['neutral'])
                  for u in upside]

        fig.add_trace(
            go.Bar(
                x=dates,
                y=upside,
                name='Upside',
                marker={'color': colors},
                hovertemplate='%{x|%Y-%m-%d}<br>Upside: %{y:+.1f}%<extra></extra>',
            ),
            row=2,
            col=1,
        )

        # Add zero line in upside chart
        fig.add_hline(
            y=0,
            line_dash='dot',
            line_color=self.COLORS['text'],
            row=2,
            col=1,
        )

        # Update axes
        fig.update_xaxes(title_text='', row=1, col=1)
        fig.update_xaxes(title_text='Date', row=2, col=1)
        fig.update_yaxes(title_text='Price ($)', row=1, col=1)
        fig.update_yaxes(title_text='Upside (%)', row=2, col=1)

        # Layout
        fig.update_layout(
            height=700,
            hovermode='x unified',
            font=self.TEMPLATE['layout']['font'],
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=True,
            legend={'x': 0.02, 'y': 0.98, 'bgcolor': 'rgba(255,255,255,0.8)'},
        )

        # Add animation if requested
        if animate and len(dates) > 5:
            # Create frames for animation
            frames = []
            for i in range(5, len(dates) + 1, max(1, len(dates) // 20)):  # 20 frames max
                frame_data = [
                    go.Scatter(x=dates[:i], y=market_prices[:i]),
                    go.Scatter(x=dates[:i], y=fair_values[:i]),
                    go.Bar(x=dates[:i], y=upside[:i], marker={'color': colors[:i]}),
                ]
                frames.append(go.Frame(data=frame_data, name=str(i)))

            fig.frames = frames

            # Add play/pause buttons
            fig.update_layout(
                updatemenus=[{
                    'type': 'buttons',
                    'showactive': False,
                    'buttons': [
                        {
                            'label': '▶ Play',
                            'method': 'animate',
                            'args': [None, {
                                'frame': {'duration': 100, 'redraw': True},
                                'fromcurrent': True,
                                'mode': 'immediate',
                            }]
                        },
                        {
                            'label': '⏸ Pause',
                            'method': 'animate',
                            'args': [[None], {
                                'frame': {'duration': 0, 'redraw': False},
                                'mode': 'immediate',
                            }]
                        }
                    ],
                    'x': 0.1,
                    'y': 1.15,
                }]
            )

        return fig

    def export_chart_to_image(
        self,
        fig: go.Figure,
        format: str = 'png',
        width: int = 1200,
        height: int = 800,
        scale: int = 2,
    ) -> bytes:
        """
        Export Plotly figure to image bytes.

        Args:
            fig: Plotly figure
            format: Image format ('png', 'svg', 'pdf', 'jpeg')
            width: Width in pixels
            height: Height in pixels
            scale: Scale factor for resolution (default 2 for retina)

        Returns:
            Image bytes

        Raises:
            ImportError: If kaleido is not installed
        """
        try:
            import kaleido
        except ImportError:
            raise ImportError(
                "kaleido is required for image export. "
                "Install with: pip install kaleido"
            )

        img_bytes = fig.to_image(
            format=format,
            width=width,
            height=height,
            scale=scale,
        )

        return img_bytes

    def export_chart_to_html(
        self,
        fig: go.Figure,
        include_plotlyjs: str = 'cdn',
        config: Optional[Dict] = None,
    ) -> str:
        """
        Export Plotly figure to standalone HTML.

        Args:
            fig: Plotly figure
            include_plotlyjs: How to include plotly.js ('cdn', True, False)
            config: Plotly config dict (optional)

        Returns:
            HTML string
        """
        if config is None:
            config = {
                'displayModeBar': True,
                'displaylogo': False,
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'dcf_chart',
                    'height': 800,
                    'width': 1200,
                    'scale': 2,
                },
                'modeBarButtonsToAdd': ['hoverclosest', 'hovercompare'],
            }

        html_str = fig.to_html(
            include_plotlyjs=include_plotlyjs,
            config=config,
            full_html=True,
        )

        return html_str

    def create_fcf_breakdown_chart(
        self,
        years: List[int],
        fcf_values: List[float],
        growth_rates: List[float],
        discount_rate: float,
        pv_values: List[float],
    ) -> go.Figure:
        """
        Create dual-axis chart showing FCF projections and present values.

        Args:
            years: List of years (0, 1, 2, ...)
            fcf_values: Projected FCF values
            growth_rates: Growth rate for each year
            discount_rate: Discount rate (WACC)
            pv_values: Present value of each FCF

        Returns:
            Plotly Figure
        """
        fig = make_subplots(
            specs=[[{'secondary_y': True}]],
        )

        # FCF bars
        fig.add_trace(
            go.Bar(
                x=years,
                y=fcf_values,
                name='Projected FCF',
                marker={'color': self.COLORS['primary']},
                text=[f'${v/1e9:.2f}B<br>+{g:.1%}' for v, g in zip(fcf_values, growth_rates)],
                textposition='outside',
                hovertemplate='Year %{x}<br>FCF: $%{y:.2e}<br>Growth: %{customdata:.1%}<extra></extra>',
                customdata=growth_rates,
            ),
            secondary_y=False,
        )

        # PV line
        fig.add_trace(
            go.Scatter(
                x=years,
                y=pv_values,
                name='Present Value',
                mode='lines+markers',
                line={'color': self.COLORS['accent'], 'width': 3},
                marker={'size': 10, 'symbol': 'diamond'},
                text=[f'${v/1e9:.2f}B' for v in pv_values],
                textposition='top center',
                hovertemplate='Year %{x}<br>PV: $%{y:.2e}<extra></extra>',
            ),
            secondary_y=True,
        )

        # Layout
        fig.update_xaxes(title_text='Year', dtick=1)
        fig.update_yaxes(title_text='Projected FCF ($)', secondary_y=False, tickformat='$,.0s')
        fig.update_yaxes(title_text='Present Value ($)', secondary_y=True, tickformat='$,.0s')

        fig.update_layout(
            title={
                'text': f'FCF Projections & Present Values<br><sub>WACC: {discount_rate:.2%}</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16, 'color': self.COLORS['text']}
            },
            height=500,
            hovermode='x unified',
            font=self.TEMPLATE['layout']['font'],
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend={'x': 0.02, 'y': 0.98, 'bgcolor': 'rgba(255,255,255,0.9)'},
        )

        return fig
