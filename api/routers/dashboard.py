"""Dashboard summary endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..models import DashboardSummary, DCFResult
from src.cache import DCFCache

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    """
    Get executive dashboard summary with all analyzed companies.

    Returns portfolio overview with key metrics and top opportunities.
    """
    try:
        cache = DCFCache()

        # Get all saved calculations
        calculations = cache.get_all_calculations(limit=100)

        if not calculations:
            return DashboardSummary(
                total_companies=0,
                avg_upside=0.0,
                strong_buys=0,
                buys=0,
                holds=0,
                sells=0,
                last_updated=datetime.now(),
                top_opportunities=[]
            )

        # Calculate metrics
        total = len(calculations)
        upsides = []
        strong_buys = buys = holds = sells = 0

        for calc in calculations:
            upside = calc.get("upside_percentage", 0)
            upsides.append(upside)

            if upside >= 30:
                strong_buys += 1
            elif upside >= 15:
                buys += 1
            elif upside >= -10:
                holds += 1
            else:
                sells += 1

        avg_upside = sum(upsides) / len(upsides) if upsides else 0

        # Get top opportunities (sorted by upside)
        sorted_calcs = sorted(calculations, key=lambda x: x.get("upside_percentage", 0), reverse=True)
        top_5 = sorted_calcs[:5]

        top_opportunities = [
            DCFResult(
                ticker=calc["ticker"],
                company_name=calc.get("company_name", calc["ticker"]),
                calculation_date=datetime.fromisoformat(calc["timestamp"]),
                current_price=calc["market_price"],
                fair_value=calc["fair_value"],
                upside_percentage=calc["upside_percentage"],
                recommendation=get_recommendation_from_upside(calc["upside_percentage"]),
                confidence_score=calc.get("confidence_score", 0.7),
                projection_years=calc.get("parameters", {}).get("projection_years", 5),
                growth_rate=calc.get("parameters", {}).get("growth_rate", 0.05),
                terminal_growth_rate=calc.get("parameters", {}).get("terminal_growth_rate", 0.025),
                discount_rate=calc.get("parameters", {}).get("discount_rate", 0.08)
            )
            for calc in top_5
        ]

        return DashboardSummary(
            total_companies=total,
            avg_upside=avg_upside,
            strong_buys=strong_buys,
            buys=buys,
            holds=holds,
            sells=sells,
            last_updated=datetime.now(),
            top_opportunities=top_opportunities
        )

    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard summary: {str(e)}"
        )


def get_recommendation_from_upside(upside: float) -> str:
    """Helper to get recommendation from upside percentage."""
    if upside >= 30:
        return "Strong Buy"
    elif upside >= 15:
        return "Buy"
    elif upside >= -10:
        return "Hold"
    elif upside >= -25:
        return "Sell"
    else:
        return "Strong Sell"
