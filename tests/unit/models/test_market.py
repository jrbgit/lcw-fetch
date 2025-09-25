"""
Unit tests for the Market data model.

Tests cover model validation, serialization, InfluxDB point conversion,
and edge cases for the Market model.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.lcw_fetcher.models import Market
from tests.conftest import assert_influx_point_valid


class TestMarket:
    """Tests for the Market model."""

    def test_market_creation_minimal(self):
        """Test creating Market with minimal data."""
        market = Market()

        assert market.currency == "USD"  # Default value
        assert isinstance(market.fetched_at, datetime)
        assert market.cap is None
        assert market.volume is None
        assert market.liquidity is None
        assert market.btcDominance is None

    def test_market_creation_full_data(self, sample_market_data):
        """Test creating Market with full data."""
        market = Market(**sample_market_data)

        assert market.cap == 2500000000000.0
        assert market.volume == 95000000000.0
        assert market.liquidity == 8500000000.0
        assert market.btcDominance == 42.5
        assert market.currency == "USD"

    def test_market_optional_fields_none(self):
        """Test that all market fields can be None."""
        market = Market(cap=None, volume=None, liquidity=None, btcDominance=None)

        assert market.cap is None
        assert market.volume is None
        assert market.liquidity is None
        assert market.btcDominance is None

    def test_market_partial_data(self):
        """Test creating Market with partial data."""
        market = Market(
            cap=2500000000000.0,
            btcDominance=42.5,
            # volume and liquidity are None
        )

        assert market.cap == 2500000000000.0
        assert market.btcDominance == 42.5
        assert market.volume is None
        assert market.liquidity is None

    def test_market_custom_currency(self):
        """Test Market with custom currency."""
        market = Market(cap=2500000000000.0, currency="EUR")

        assert market.currency == "EUR"


class TestMarketInfluxConversion:
    """Tests for Market to InfluxDB point conversion."""

    def test_to_influx_point_minimal(self):
        """Test InfluxDB point conversion with minimal data."""
        market = Market()
        point = market.to_influx_point()

        assert_influx_point_valid(point)

        assert point["measurement"] == "market_overview"
        assert point["tags"]["currency"] == "USD"
        assert isinstance(point["time"], datetime)

        # Only record_count should be present when all values are None
        assert len(point["fields"]) == 1
        assert "record_count" in point["fields"]
        assert point["fields"]["record_count"] == 1

    def test_to_influx_point_full_data(self, sample_market_data):
        """Test InfluxDB point conversion with full data."""
        market = Market(**sample_market_data)
        point = market.to_influx_point()

        assert_influx_point_valid(point)

        # Check tags
        assert point["tags"]["currency"] == "USD"

        # Check fields
        assert point["fields"]["total_market_cap"] == 2500000000000.0
        assert point["fields"]["total_volume"] == 95000000000.0
        assert point["fields"]["total_liquidity"] == 8500000000.0
        assert point["fields"]["btc_dominance"] == 42.5

    def test_to_influx_point_partial_data(self):
        """Test InfluxDB point conversion with partial data."""
        market = Market(
            cap=2500000000000.0,
            btcDominance=42.5,
            # volume and liquidity are None
        )
        point = market.to_influx_point()

        assert_influx_point_valid(point)

        # Only non-None fields should be included
        assert "total_market_cap" in point["fields"]
        assert "btc_dominance" in point["fields"]
        assert "total_volume" not in point["fields"]
        assert "total_liquidity" not in point["fields"]

        assert point["fields"]["total_market_cap"] == 2500000000000.0
        assert point["fields"]["btc_dominance"] == 42.5

    def test_to_influx_point_custom_currency(self):
        """Test InfluxDB point conversion with custom currency."""
        market = Market(cap=2500000000000.0, currency="EUR")
        point = market.to_influx_point()

        assert point["tags"]["currency"] == "EUR"

    def test_to_influx_point_numeric_conversion(self):
        """Test that numeric values are properly converted to float."""
        market = Market(
            cap="2500000000000.0",  # String that should be converted to float
            volume="95000000000.0",  # String that should be converted to float
            liquidity="8500000000.0",  # String that should be converted to float
            btcDominance="42.5",  # String that should be converted to float
        )
        point = market.to_influx_point()

        assert isinstance(point["fields"]["total_market_cap"], float)
        assert isinstance(point["fields"]["total_volume"], float)
        assert isinstance(point["fields"]["total_liquidity"], float)
        assert isinstance(point["fields"]["btc_dominance"], float)

        assert point["fields"]["total_market_cap"] == 2500000000000.0
        assert point["fields"]["total_volume"] == 95000000000.0
        assert point["fields"]["total_liquidity"] == 8500000000.0
        assert point["fields"]["btc_dominance"] == 42.5


class TestMarketEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_market_with_very_large_numbers(self):
        """Test Market with very large numeric values."""
        market = Market(
            cap=1e25,  # Very large market cap
            volume=1e23,  # Very large volume
            liquidity=1e22,  # Very large liquidity
            btcDominance=99.99,  # Near 100% dominance
        )

        assert market.cap == 1e25
        assert market.volume == 1e23
        assert market.liquidity == 1e22
        assert market.btcDominance == 99.99

        point = market.to_influx_point()
        assert point["fields"]["total_market_cap"] == 1e25
        assert point["fields"]["total_volume"] == 1e23
        assert point["fields"]["total_liquidity"] == 1e22
        assert point["fields"]["btc_dominance"] == 99.99

    def test_market_with_zero_values(self):
        """Test Market with zero values."""
        market = Market(cap=0.0, volume=0.0, liquidity=0.0, btcDominance=0.0)

        point = market.to_influx_point()
        assert point["fields"]["total_market_cap"] == 0.0
        assert point["fields"]["total_volume"] == 0.0
        assert point["fields"]["total_liquidity"] == 0.0
        assert point["fields"]["btc_dominance"] == 0.0

    def test_market_with_negative_values(self):
        """Test Market with negative values (unusual but allowed by model)."""
        market = Market(
            cap=-1000.0,  # Negative market cap (unusual)
            volume=-500.0,  # Negative volume (unusual)
            liquidity=-100.0,  # Negative liquidity (unusual)
            btcDominance=-5.0,  # Negative dominance (unusual)
        )

        # These should be accepted by the model
        assert market.cap == -1000.0
        assert market.volume == -500.0
        assert market.liquidity == -100.0
        assert market.btcDominance == -5.0

    def test_market_btc_dominance_edge_cases(self):
        """Test Market with edge case BTC dominance values."""
        # 0% dominance
        market_zero = Market(btcDominance=0.0)
        assert market_zero.btcDominance == 0.0

        # 100% dominance
        market_full = Market(btcDominance=100.0)
        assert market_full.btcDominance == 100.0

        # Over 100% dominance (theoretically impossible but allowed by model)
        market_over = Market(btcDominance=150.0)
        assert market_over.btcDominance == 150.0

    def test_market_very_small_numbers(self):
        """Test Market with very small numeric values."""
        market = Market(
            cap=0.001,  # Very small market cap
            volume=0.0001,  # Very small volume
            liquidity=0.00001,  # Very small liquidity
            btcDominance=0.01,  # Very small dominance
        )

        assert market.cap == 0.001
        assert market.volume == 0.0001
        assert market.liquidity == 0.00001
        assert market.btcDominance == 0.01

        point = market.to_influx_point()
        assert point["fields"]["total_market_cap"] == 0.001
        assert point["fields"]["total_volume"] == 0.0001
        assert point["fields"]["total_liquidity"] == 0.00001
        assert point["fields"]["btc_dominance"] == 0.01

    def test_market_serialization_deserialization(self, sample_market_data):
        """Test that Market can be serialized and deserialized."""
        original_market = Market(**sample_market_data)

        # Serialize to dict
        market_dict = original_market.model_dump()

        # Deserialize back to Market
        restored_market = Market(**market_dict)

        # Compare key fields
        assert restored_market.cap == original_market.cap
        assert restored_market.volume == original_market.volume
        assert restored_market.liquidity == original_market.liquidity
        assert restored_market.btcDominance == original_market.btcDominance
        assert restored_market.currency == original_market.currency

    def test_market_json_serialization(self, sample_market_data):
        """Test JSON serialization of Market."""
        market = Market(**sample_market_data)

        json_str = market.model_dump_json()
        assert isinstance(json_str, str)
        assert "2500000000000.0" in json_str
        assert "42.5" in json_str
        assert "USD" in json_str

    def test_market_field_name_mapping(self):
        """Test that field names are properly mapped in InfluxDB conversion."""
        market = Market(cap=1000.0, volume=2000.0, liquidity=3000.0, btcDominance=50.0)
        point = market.to_influx_point()

        # Check that field names are properly mapped
        expected_fields = {
            "total_market_cap": 1000.0,
            "total_volume": 2000.0,
            "total_liquidity": 3000.0,
            "btc_dominance": 50.0,
        }

        for field_name, expected_value in expected_fields.items():
            assert field_name in point["fields"]
            assert point["fields"][field_name] == expected_value

    def test_market_timestamp_precision(self):
        """Test that timestamp is preserved correctly."""
        fixed_time = datetime(2024, 1, 15, 12, 30, 45)
        market = Market(cap=1000.0, fetched_at=fixed_time)
        point = market.to_influx_point()

        assert point["time"] == fixed_time

    def test_market_empty_vs_none_difference(self):
        """Test difference between empty Market and Market with explicit None values."""
        # Empty market (using defaults)
        empty_market = Market()

        # Market with explicit None values
        explicit_none_market = Market(
            cap=None, volume=None, liquidity=None, btcDominance=None
        )

        # Both should behave the same
        assert empty_market.cap == explicit_none_market.cap
        assert empty_market.volume == explicit_none_market.volume
        assert empty_market.liquidity == explicit_none_market.liquidity
        assert empty_market.btcDominance == explicit_none_market.btcDominance

        # Both should produce only the record_count field
        empty_point = empty_market.to_influx_point()
        explicit_point = explicit_none_market.to_influx_point()

        assert len(empty_point["fields"]) == 1
        assert "record_count" in empty_point["fields"]
        assert empty_point["fields"]["record_count"] == 1

        assert len(explicit_point["fields"]) == 1
        assert "record_count" in explicit_point["fields"]
        assert explicit_point["fields"]["record_count"] == 1
