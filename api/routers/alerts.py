"""Alert management endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.alerts import AlertSystem, AlertStatus

logger = logging.getLogger(__name__)
router = APIRouter()


class AlertCreate(BaseModel):
    """Model for creating a new alert."""

    ticker: str
    alert_type: str  # "price_above", "price_below", "upside_above", "upside_below"
    threshold: float
    name: Optional[str] = None


class AlertResponse(BaseModel):
    """Alert response model."""

    id: int
    ticker: str
    alert_type: str
    threshold: float
    status: str
    created_at: str
    name: Optional[str] = None


@router.post("/", response_model=AlertResponse)
async def create_alert(alert: AlertCreate):
    """Create a new price or upside alert."""
    try:
        alert_system = AlertSystem()

        alert_id = alert_system.create_alert(
            ticker=alert.ticker,
            alert_type=alert.alert_type,
            threshold=alert.threshold,
            name=alert.name
        )

        # Get the created alert
        created_alert = alert_system.get_alert(alert_id)

        return AlertResponse(**created_alert)

    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create alert: {str(e)}"
        )


@router.get("/", response_model=list[AlertResponse])
async def get_all_alerts(
    status: Optional[str] = Query(None, description="Filter by status (active, triggered, expired)")
):
    """Get all alerts, optionally filtered by status."""
    try:
        alert_system = AlertSystem()

        if status:
            alerts = alert_system.get_alerts_by_status(AlertStatus[status.upper()])
        else:
            alerts = alert_system.get_all_alerts()

        return [AlertResponse(**alert) for alert in alerts]

    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.get("/{ticker}", response_model=list[AlertResponse])
async def get_alerts_for_ticker(ticker: str):
    """Get all alerts for a specific ticker."""
    try:
        alert_system = AlertSystem()
        alerts = alert_system.get_alerts_for_ticker(ticker)

        return [AlertResponse(**alert) for alert in alerts]

    except Exception as e:
        logger.error(f"Error getting alerts for ticker: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.delete("/{alert_id}")
async def delete_alert(alert_id: int):
    """Delete an alert."""
    try:
        alert_system = AlertSystem()
        alert_system.delete_alert(alert_id)

        return {"message": "Alert deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete alert: {str(e)}"
        )


@router.post("/check")
async def check_alerts():
    """Check all active alerts and trigger if conditions are met."""
    try:
        alert_system = AlertSystem()
        triggered = alert_system.check_all_alerts()

        return {
            "message": "Alerts checked successfully",
            "triggered_count": len(triggered),
            "triggered_alerts": triggered
        }

    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check alerts: {str(e)}"
        )
