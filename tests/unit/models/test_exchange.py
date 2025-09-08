"""
Unit tests for the Exchange data model.

Tests cover model validation, serialization, InfluxDB point conversion,
and edge cases for the Exchange model.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.lcw_fetcher.models import Exchange
from tests.conftest import assert_influx_point_valid


class TestExchange:
    """Tests for the Exchange model."""
    
    def test_exchange_creation_minimal(self):
        """Test creating Exchange with minimal required data."""
        exchange = Exchange(code="binance")
        
        assert exchange.code == "BINANCE"  # Should be uppercased
        assert exchange.currency == "USD"  # Default value
        assert isinstance(exchange.fetched_at, datetime)
    
    def test_exchange_creation_full_data(self, sample_exchange_data):
        """Test creating Exchange with full data."""
        exchange = Exchange(**sample_exchange_data)
        
        assert exchange.code == "BINANCE"  # Should be uppercased
        assert exchange.name == "Binance"
        assert exchange.volume == 15000000000.0
        assert exchange.visitors == 85000000
        assert exchange.volumePerVisitor == 176.47
        assert exchange.currency == "USD"
    
    def test_exchange_code_validation_uppercase(self):
        """Test that exchange code is converted to uppercase."""
        exchange = Exchange(code="binance")
        assert exchange.code == "BINANCE"
    
    def test_exchange_code_validation_trimmed(self):
        """Test that exchange code is trimmed."""
        exchange = Exchange(code="  binance  ")
        assert exchange.code == "BINANCE"
    
    def test_exchange_code_validation_empty(self):
        """Test validation with empty code."""
        with pytest.raises(ValidationError) as exc_info:
            Exchange(code="")
        assert "Exchange code cannot be empty" in str(exc_info.value)
    
    def test_exchange_code_validation_whitespace_only(self):
        """Test validation with whitespace-only code."""
        with pytest.raises(ValidationError) as exc_info:
            Exchange(code="   ")
        assert "Exchange code cannot be empty" in str(exc_info.value)
    
    def test_exchange_code_validation_none(self):
        """Test validation with None code."""
        with pytest.raises(ValidationError):
            Exchange(code=None)
    
    def test_exchange_optional_fields_none(self):
        """Test that optional fields can be None."""
        exchange = Exchange(
            code="binance",
            name=None,
            volume=None,
            visitors=None,
            volumePerVisitor=None,
            rank=None
        )
        
        assert exchange.code == "BINANCE"
        assert exchange.name is None
        assert exchange.volume is None
        assert exchange.visitors is None
        assert exchange.volumePerVisitor is None
        assert exchange.rank is None


class TestExchangeInfluxConversion:
    """Tests for Exchange to InfluxDB point conversion."""
    
    def test_to_influx_point_minimal(self):
        """Test InfluxDB point conversion with minimal data."""
        exchange = Exchange(code="binance")
        point = exchange.to_influx_point()
        
        assert_influx_point_valid(point)
        
        assert point['measurement'] == 'exchange_data'
        assert point['tags']['code'] == 'BINANCE'
        assert point['tags']['currency'] == 'USD'
        assert point['tags']['name'] == ''  # Empty when None
        assert isinstance(point['time'], datetime)
        
        # Only record_count should be present when all numeric values are None
        assert len(point['fields']) == 1
        assert 'record_count' in point['fields']
        assert point['fields']['record_count'] == 1
    
    def test_to_influx_point_full_data(self, sample_exchange_data):
        """Test InfluxDB point conversion with full data."""
        exchange = Exchange(**sample_exchange_data)
        point = exchange.to_influx_point()
        
        assert_influx_point_valid(point)
        
        # Check tags
        assert point['tags']['code'] == 'BINANCE'
        assert point['tags']['name'] == 'Binance'
        assert point['tags']['currency'] == 'USD'
        
        # Check fields
        assert point['fields']['volume'] == 15000000000.0
        assert point['fields']['visitors'] == 85000000
        assert point['fields']['volume_per_visitor'] == 176.47
    
    def test_to_influx_point_partial_data(self):
        """Test InfluxDB point conversion with partial data."""
        exchange = Exchange(
            code="binance",
            name="Binance",
            volume=15000000000.0,
            visitors=None,  # Missing
            volumePerVisitor=None,  # Missing
            rank=1
        )
        point = exchange.to_influx_point()
        
        assert_influx_point_valid(point)
        
        # Only non-None numeric fields should be included
        assert 'volume' in point['fields']
        assert 'rank' in point['fields']
        assert 'visitors' not in point['fields']
        assert 'volume_per_visitor' not in point['fields']
        
        assert point['fields']['volume'] == 15000000000.0
        assert point['fields']['rank'] == 1
    
    def test_to_influx_point_no_name(self):
        """Test InfluxDB point conversion when name is None."""
        exchange = Exchange(code="binance")
        point = exchange.to_influx_point()
        
        assert point['tags']['name'] == ''
    
    def test_to_influx_point_numeric_conversion(self):
        """Test that numeric values are properly converted to float/int."""
        exchange = Exchange(
            code="binance",
            volume="15000000000.0",  # String that should be converted to float
            visitors="85000000",  # String that should be converted to int
            volumePerVisitor="176.47",  # String that should be converted to float
            rank="1"  # String that should be converted to int
        )
        point = exchange.to_influx_point()
        
        assert isinstance(point['fields']['volume'], float)
        assert isinstance(point['fields']['visitors'], int)
        assert isinstance(point['fields']['volume_per_visitor'], float)
        assert isinstance(point['fields']['rank'], int)
        
        assert point['fields']['volume'] == 15000000000.0
        assert point['fields']['visitors'] == 85000000
        assert point['fields']['volume_per_visitor'] == 176.47
        assert point['fields']['rank'] == 1


class TestExchangeEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_exchange_with_very_large_numbers(self):
        """Test Exchange with very large numeric values."""
        exchange = Exchange(
            code="binance",
            volume=1e20,  # Very large volume
            visitors=1e10,  # Very large visitor count
        )
        
        assert exchange.volume == 1e20
        assert exchange.visitors == 1e10
        
        point = exchange.to_influx_point()
        assert point['fields']['volume'] == 1e20
        assert point['fields']['visitors'] == 1e10
    
    def test_exchange_with_zero_values(self):
        """Test Exchange with zero values."""
        exchange = Exchange(
            code="test",
            volume=0.0,
            visitors=0,
            volumePerVisitor=0.0,
            rank=1  # Rank should not be zero for a valid exchange
        )
        
        point = exchange.to_influx_point()
        assert point['fields']['volume'] == 0.0
        assert point['fields']['visitors'] == 0
        assert point['fields']['volume_per_visitor'] == 0.0
        assert point['fields']['rank'] == 1
    
    def test_exchange_serialization_deserialization(self, sample_exchange_data):
        """Test that Exchange can be serialized and deserialized."""
        original_exchange = Exchange(**sample_exchange_data)
        
        # Serialize to dict
        exchange_dict = original_exchange.model_dump()
        
        # Deserialize back to Exchange
        restored_exchange = Exchange(**exchange_dict)
        
        # Compare key fields
        assert restored_exchange.code == original_exchange.code
        assert restored_exchange.name == original_exchange.name
        assert restored_exchange.volume == original_exchange.volume
        assert restored_exchange.visitors == original_exchange.visitors
    
    def test_exchange_json_serialization(self, sample_exchange_data):
        """Test JSON serialization of Exchange."""
        exchange = Exchange(**sample_exchange_data)
        
        json_str = exchange.model_dump_json()
        assert isinstance(json_str, str)
        assert "BINANCE" in json_str
        assert "Binance" in json_str
    
    @pytest.mark.parametrize("invalid_code", ["", "  ", "\t\n", None])
    def test_exchange_invalid_codes(self, invalid_code):
        """Test various invalid code values."""
        with pytest.raises(ValidationError):
            Exchange(code=invalid_code)
    
    def test_exchange_negative_values(self):
        """Test Exchange with negative values (which should be allowed for some fields)."""
        exchange = Exchange(
            code="test",
            volume=-1000.0,  # Negative volume (unusual but not invalid)
            visitors=-100,  # Negative visitors (unusual but not invalid)
            volumePerVisitor=-10.0,  # Negative volume per visitor
            rank=-1  # Negative rank (unusual but not invalid in model)
        )
        
        # These should be accepted by the model
        assert exchange.volume == -1000.0
        assert exchange.visitors == -100
        assert exchange.volumePerVisitor == -10.0
        assert exchange.rank == -1
    
    def test_exchange_custom_currency(self):
        """Test Exchange with custom currency."""
        exchange = Exchange(
            code="binance",
            currency="EUR"
        )
        
        assert exchange.currency == "EUR"
        
        point = exchange.to_influx_point()
        assert point['tags']['currency'] == "EUR"
    
    def test_exchange_very_long_code(self):
        """Test Exchange with very long code."""
        long_code = "a" * 100  # Very long code
        exchange = Exchange(code=long_code)
        
        assert exchange.code == long_code.upper()
    
    def test_exchange_special_characters_in_code(self):
        """Test Exchange with special characters in code."""
        special_code = "binance-us_test.123"
        exchange = Exchange(code=special_code)
        
        assert exchange.code == special_code.upper()
    
    def test_exchange_unicode_name(self):
        """Test Exchange with Unicode characters in name."""
        exchange = Exchange(
            code="binance",
            name="Binance 币安"  # Mix of English and Chinese
        )
        
        assert exchange.name == "Binance 币安"
        
        point = exchange.to_influx_point()
        assert point['tags']['name'] == "Binance 币安"
