"""DCF calculation endpoints."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..models import DCFCalculationRequest, DCFResult, SensitivityAnalysis
from src.dcf.enhanced_model import EnhancedDCFModel
from src.dcf.wacc_calculator import WACCCalculator
from src.dcf.sensitivity_analysis import SensitivityAnalyzer
from src.data_providers.aggregator import get_data_aggregator
from src.core.intelligent_selector import IntelligentDataSelector
from src.cache import DCFCache
from src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


def get_recommendation(upside_percentage: float) -> str:
    """Determine investment recommendation based on upside."""
    if upside_percentage >= 30:
        return "Strong Buy"
    elif upside_percentage >= 15:
        return "Buy"
    elif upside_percentage >= -10:
        return "Hold"
    elif upside_percentage >= -25:
        return "Sell"
    else:
        return "Strong Sell"


@router.post("/calculate", response_model=DCFResult)
async def calculate_dcf(request: DCFCalculationRequest):
    """
    Calculate DCF valuation for a company.

    Returns fair value, current price, and investment recommendation.
    """
    try:
        logger.info(f"Calculating DCF for {request.ticker}")

        # Initialize services
        aggregator = get_data_aggregator()
        cache = DCFCache()
        selector = IntelligentDataSelector(aggregator, cache)

        # Get company data
        try:
            company_data = await selector.get_company_data(request.ticker)
        except Exception as e:
            logger.error(f"Failed to fetch company data: {e}")
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch data for ticker {request.ticker}"
            )

        # Use intelligent values if requested
        if request.use_intelligent_values:
            params = selector.get_intelligent_parameters(request.ticker, company_data)
            growth_rate = params.get("growth_rate", settings.dcf.default_growth_rate)
            terminal_growth = params.get("terminal_growth_rate", settings.dcf.default_terminal_growth)
            discount_rate = params.get("wacc", settings.dcf.default_risk_free_rate + settings.dcf.default_market_risk_premium)
        else:
            growth_rate = request.growth_rate or settings.dcf.default_growth_rate
            terminal_growth = request.terminal_growth_rate or settings.dcf.default_terminal_growth
            discount_rate = request.discount_rate or 0.08

        # Calculate DCF
        dcf_model = EnhancedDCFModel()
        result = dcf_model.calculate_dcf(
            ticker=request.ticker,
            company_data=company_data,
            projection_years=request.projection_years,
            growth_rate=growth_rate,
            terminal_growth_rate=terminal_growth,
            discount_rate=discount_rate
        )

        # Get current price
        current_price = company_data.get("current_price", 0)
        fair_value = result.get("fair_value_per_share", 0)

        # Calculate upside
        upside = ((fair_value - current_price) / current_price * 100) if current_price > 0 else 0

        # Determine recommendation
        recommendation = get_recommendation(upside)

        # Calculate confidence score based on data quality
        confidence = result.get("confidence_score", 0.7)

        # Cache result
        cache.save_dcf_calculation(
            ticker=request.ticker,
            fair_value=fair_value,
            market_price=current_price,
            parameters={
                "growth_rate": growth_rate,
                "terminal_growth_rate": terminal_growth,
                "discount_rate": discount_rate,
                "projection_years": request.projection_years
            }
        )

        return DCFResult(
            ticker=request.ticker.upper(),
            company_name=company_data.get("name", request.ticker),
            calculation_date=datetime.now(),
            current_price=current_price,
            fair_value=fair_value,
            upside_percentage=upside,
            recommendation=recommendation,
            confidence_score=confidence,
            projection_years=request.projection_years,
            growth_rate=growth_rate,
            terminal_growth_rate=terminal_growth,
            discount_rate=discount_rate,
            fcf_current=result.get("fcf_current"),
            revenue_current=result.get("revenue_current"),
            shares_outstanding=result.get("shares_outstanding")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating DCF: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate DCF: {str(e)}"
        )


@router.get("/sensitivity/{ticker}", response_model=SensitivityAnalysis)
async def get_sensitivity_analysis(
    ticker: str,
    base_growth: float = Query(0.05, ge=-0.5, le=1.0),
    base_discount: float = Query(0.08, ge=0, le=0.5)
):
    """
    Perform sensitivity analysis on DCF valuation.

    Tests different growth rate and discount rate scenarios.
    """
    try:
        logger.info(f"Performing sensitivity analysis for {ticker}")

        # Initialize analyzer
        analyzer = SensitivityAnalyzer()
        aggregator = get_data_aggregator()
        cache = DCFCache()
        selector = IntelligentDataSelector(aggregator, cache)

        # Get company data
        company_data = await selector.get_company_data(ticker)

        # Run sensitivity analysis
        scenarios = analyzer.analyze_scenarios(
            ticker=ticker,
            company_data=company_data,
            base_growth_rate=base_growth,
            base_discount_rate=base_discount
        )

        return SensitivityAnalysis(
            ticker=ticker.upper(),
            base_fair_value=scenarios["base"]["fair_value"],
            optimistic_fair_value=scenarios["optimistic"]["fair_value"],
            pessimistic_fair_value=scenarios["pessimistic"]["fair_value"],
            scenarios=scenarios
        )

    except Exception as e:
        logger.error(f"Error in sensitivity analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform sensitivity analysis: {str(e)}"
        )


@router.get("/history/{ticker}", response_model=list[dict])
async def get_valuation_history(
    ticker: str,
    days: int = Query(90, ge=1, le=365, description="Number of days of history")
):
    """Get historical DCF valuations for a ticker."""
    try:
        cache = DCFCache()
        history = cache.get_price_history(ticker, days=days)

        return history

    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch valuation history: {str(e)}"
        )
