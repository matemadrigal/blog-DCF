"""Centralized configuration settings for DCF application."""

import os
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DCFDefaults:
    """Default values for DCF calculations."""

    # Growth rates
    default_growth_rate: float = 0.05
    default_terminal_growth: float = 0.025
    min_growth_rate: float = -0.5
    max_growth_rate: float = 1.0

    # WACC parameters
    default_risk_free_rate: float = 0.04
    default_market_risk_premium: float = 0.08
    default_tax_rate: float = 0.21

    # Projection parameters
    default_projection_years: int = 5
    min_projection_years: int = 3
    max_projection_years: int = 10


@dataclass
class APIConfig:
    """API configuration for data providers."""

    # API Keys (loaded from environment)
    alpha_vantage_key: Optional[str] = field(
        default_factory=lambda: os.getenv("ALPHA_VANTAGE_API_KEY")
    )
    fmp_key: Optional[str] = field(
        default_factory=lambda: os.getenv("FMP_API_KEY")
    )
    iex_cloud_key: Optional[str] = field(
        default_factory=lambda: os.getenv("IEX_CLOUD_API_KEY")
    )

    # API settings
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class CacheConfig:
    """Cache configuration."""

    cache_dir: Path = field(default_factory=lambda: Path("data"))
    db_name: str = "dcf_cache.db"
    cache_expiry_days: int = 7

    @property
    def db_path(self) -> Path:
        """Get full database path."""
        return self.cache_dir / self.db_name


@dataclass
class Settings:
    """Main application settings."""

    # App metadata
    app_name: str = "DCF Valuation Platform"
    version: str = "2.0.0"

    # Sub-configurations
    dcf: DCFDefaults = field(default_factory=DCFDefaults)
    api: APIConfig = field(default_factory=APIConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)

    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    assets_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "assets")
    outputs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "outputs")

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def __post_init__(self):
        """Create necessary directories."""
        self.cache.cache_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        (self.outputs_dir / "pdfs").mkdir(exist_ok=True)
        (self.outputs_dir / "reports").mkdir(exist_ok=True)


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
