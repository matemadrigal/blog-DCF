"""Company data endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..models import CompanyInfo, CompanySearchRequest
from src.data_providers.companies_loader import get_company_loader
from src.data_providers.aggregator import get_data_aggregator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search", response_model=list[CompanyInfo])
async def search_companies(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Search for companies by ticker or name.

    Returns matching companies with basic information.
    """
    try:
        loader = get_company_loader()
        results = loader.search_companies(q)

        # Limit results
        results = results[:limit]

        # Convert to CompanyInfo models
        companies = [
            CompanyInfo(
                ticker=company["ticker"],
                name=company["name"],
                sector=company["sector"]
            )
            for company in results
        ]

        return companies

    except Exception as e:
        logger.error(f"Error searching companies: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search companies: {str(e)}"
        )


@router.get("/{ticker}", response_model=CompanyInfo)
async def get_company_info(ticker: str):
    """Get detailed information for a specific company."""
    try:
        # Get basic info from loader
        loader = get_company_loader()
        company = loader.get_company_by_ticker(ticker)

        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company with ticker {ticker} not found"
            )

        # Try to get live market data
        try:
            aggregator = get_data_aggregator()
            market_data = aggregator.get_company_overview(ticker)

            return CompanyInfo(
                ticker=company["ticker"],
                name=company["name"],
                sector=company["sector"],
                market_cap=market_data.get("market_cap"),
                current_price=market_data.get("current_price")
            )
        except Exception:
            # Fallback to basic info
            return CompanyInfo(
                ticker=company["ticker"],
                name=company["name"],
                sector=company["sector"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get company information: {str(e)}"
        )


@router.get("/sector/{sector}", response_model=list[CompanyInfo])
async def get_companies_by_sector(
    sector: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Get all companies in a specific sector."""
    try:
        loader = get_company_loader()
        companies = loader.get_companies_by_sector(sector)

        # Limit results
        companies = companies[:limit]

        return [
            CompanyInfo(
                ticker=company["ticker"],
                name=company["name"],
                sector=company["sector"]
            )
            for company in companies
        ]

    except Exception as e:
        logger.error(f"Error getting companies by sector: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get companies by sector: {str(e)}"
        )


@router.get("/", response_model=list[str])
async def get_all_sectors():
    """Get list of all available sectors."""
    try:
        loader = get_company_loader()
        sectors = loader.get_all_sectors()
        return sectors

    except Exception as e:
        logger.error(f"Error getting sectors: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sectors: {str(e)}"
        )
