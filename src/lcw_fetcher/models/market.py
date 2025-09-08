from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class Market(BaseModel):
    """Market overview data model"""
    cap: Optional[float] = Field(None, description="Total market capitalization")
    volume: Optional[float] = Field(None, description="Total 24h volume")
    liquidity: Optional[float] = Field(None, description="Total liquidity")
    btcDominance: Optional[float] = Field(None, description="Bitcoin dominance ratio")
    
    # Metadata
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    currency: str = Field(default="USD")
    
    def to_influx_point(self) -> Dict[str, Any]:
        """Convert to InfluxDB point format"""
        fields = {
            'record_count': 1  # Always include at least one field for valid InfluxDB point
        }
        tags = {
            'currency': self.currency
        }
        
        if self.cap is not None:
            fields['total_market_cap'] = float(self.cap)
        if self.volume is not None:
            fields['total_volume'] = float(self.volume)
        if self.liquidity is not None:
            fields['total_liquidity'] = float(self.liquidity)
        if self.btcDominance is not None:
            fields['btc_dominance'] = float(self.btcDominance)
        
        return {
            'measurement': 'market_overview',
            'tags': tags,
            'fields': fields,
            'time': self.fetched_at
        }
