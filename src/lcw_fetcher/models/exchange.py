from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class Exchange(BaseModel):
    """Exchange data model based on LCW API"""
    code: str = Field(..., description="Exchange code")
    name: Optional[str] = Field(None, description="Exchange name")
    rank: Optional[int] = Field(None, description="Exchange rank")
    
    # Market data
    volume: Optional[float] = Field(None, description="24h trading volume")
    visitors: Optional[int] = Field(None, description="Daily visitors")
    volumePerVisitor: Optional[float] = Field(None, description="Volume per visitor")
    
    # Metadata
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    currency: str = Field(default="USD")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if not v or not v.strip():
            raise ValueError('Exchange code cannot be empty')
        return v.upper().strip()
    
    def to_influx_point(self) -> Dict[str, Any]:
        """Convert to InfluxDB point format"""
        fields = {
            'record_count': 1  # Always include at least one field for valid InfluxDB point
        }
        tags = {
            'code': self.code,
            'name': self.name or '',
            'currency': self.currency
        }
        
        if self.volume is not None:
            fields['volume'] = float(self.volume)
        if self.visitors is not None:
            fields['visitors'] = int(self.visitors)
        if self.volumePerVisitor is not None:
            fields['volume_per_visitor'] = float(self.volumePerVisitor)
        if self.rank is not None:
            fields['rank'] = int(self.rank)
        
        return {
            'measurement': 'exchange_data',
            'tags': tags,
            'fields': fields,
            'time': self.fetched_at
        }
