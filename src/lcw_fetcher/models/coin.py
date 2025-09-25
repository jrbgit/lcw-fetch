from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class CoinDelta(BaseModel):
    """Rate of change data for different time periods"""

    hour: Optional[float] = Field(None, description="Rate of change in the last hour")
    day: Optional[float] = Field(
        None, description="Rate of change in the last 24 hours"
    )
    week: Optional[float] = Field(None, description="Rate of change in the last 7 days")
    month: Optional[float] = Field(
        None, description="Rate of change in the last 30 days"
    )
    quarter: Optional[float] = Field(
        None, description="Rate of change in the last 90 days"
    )
    year: Optional[float] = Field(
        None, description="Rate of change in the last 365 days"
    )


class CoinHistory(BaseModel):
    """Historical data point for a coin"""

    date: int = Field(..., description="UNIX timestamp in milliseconds")
    rate: float = Field(..., description="Price at this timestamp")
    volume: float = Field(..., description="Trading volume at this timestamp")
    cap: float = Field(..., description="Market cap at this timestamp")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        if v <= 0:
            raise ValueError("Date must be a positive timestamp")
        return v


class Coin(BaseModel):
    """Complete coin data model based on LCW API"""

    code: Optional[str] = Field(None, description="Coin's code (e.g., BTC, ETH)")
    name: Optional[str] = Field(None, description="Coin's full name")
    symbol: Optional[str] = Field(None, description="Coin's symbol")
    rank: Optional[int] = Field(None, description="Coin's market rank")
    age: Optional[int] = Field(None, description="Coin's age in days")
    color: Optional[str] = Field(None, description="Hexadecimal color code")

    # Image URLs
    png32: Optional[str] = Field(None, description="32-pixel PNG image URL")
    png64: Optional[str] = Field(None, description="64-pixel PNG image URL")
    webp32: Optional[str] = Field(None, description="32-pixel WebP image URL")
    webp64: Optional[str] = Field(None, description="64-pixel WebP image URL")

    # Market data
    exchanges: Optional[int] = Field(None, description="Number of exchanges")
    markets: Optional[int] = Field(None, description="Number of markets")
    pairs: Optional[int] = Field(None, description="Number of trading pairs")

    # Price and supply data
    rate: Optional[float] = Field(None, description="Current price")
    volume: Optional[float] = Field(None, description="24h trading volume")
    cap: Optional[float] = Field(None, description="Market capitalization")
    liquidity: Optional[float] = Field(None, description="Liquidity depth")
    totalCap: Optional[float] = Field(None, description="Total market capitalization")

    allTimeHighUSD: Optional[float] = Field(None, description="All-time high in USD")
    circulatingSupply: Optional[float] = Field(None, description="Circulating supply")
    totalSupply: Optional[float] = Field(None, description="Total supply")
    maxSupply: Optional[float] = Field(None, description="Maximum supply")

    # Categories and deltas
    categories: Optional[List[str]] = Field(
        default_factory=list, description="Coin categories"
    )
    delta: Optional[CoinDelta] = Field(None, description="Rate of change data")

    # Historical data (for history endpoint)
    history: Optional[List[CoinHistory]] = Field(
        default_factory=list, description="Historical data points"
    )

    # Metadata
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow, description="When this data was fetched"
    )
    currency: str = Field(default="USD", description="Currency for price data")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if v is None:
            return None
        if not v or not v.strip():
            raise ValueError("Code cannot be empty")
        return v.upper().strip()

    @field_validator("rank")
    @classmethod
    def validate_rank(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Rank must be positive")
        return v

    def to_influx_point(self) -> Dict[str, Any]:
        """Convert to InfluxDB point format"""
        fields = {}
        tags = {
            "code": self.code or "UNKNOWN",
            "name": self.name or "",
            "currency": self.currency,
        }

        # Add numeric fields
        if self.rate is not None:
            fields["rate"] = float(self.rate)
        if self.volume is not None:
            fields["volume"] = float(self.volume)
        if self.cap is not None:
            fields["market_cap"] = float(self.cap)
        if self.liquidity is not None:
            fields["liquidity"] = float(self.liquidity)
        if self.rank is not None:
            fields["rank"] = int(self.rank)
        if self.circulatingSupply is not None:
            fields["circulating_supply"] = float(self.circulatingSupply)

        # Add delta fields if available
        if self.delta:
            if self.delta.hour is not None:
                fields["delta_1h"] = float(self.delta.hour)
            if self.delta.day is not None:
                fields["delta_24h"] = float(self.delta.day)
            if self.delta.week is not None:
                fields["delta_7d"] = float(self.delta.week)
            if self.delta.month is not None:
                fields["delta_30d"] = float(self.delta.month)

        return {
            "measurement": "cryptocurrency_data",
            "tags": tags,
            "fields": fields,
            "time": self.fetched_at,
        }
