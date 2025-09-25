"""
Unit tests for the Coin data model.

Tests cover model validation, serialization, InfluxDB point conversion,
and edge cases for the Coin model.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.lcw_fetcher.models import Coin, CoinDelta, CoinHistory
from tests.conftest import assert_influx_point_valid


class TestCoinDelta:
    """Tests for the CoinDelta model."""

    def test_coin_delta_creation_with_all_fields(self):
        """Test creating CoinDelta with all fields."""
        delta = CoinDelta(
            hour=1.5, day=2.3, week=-0.8, month=15.2, quarter=8.7, year=45.6
        )

        assert delta.hour == 1.5
        assert delta.day == 2.3
        assert delta.week == -0.8
        assert delta.month == 15.2
        assert delta.quarter == 8.7
        assert delta.year == 45.6

    def test_coin_delta_creation_with_partial_fields(self):
        """Test creating CoinDelta with only some fields."""
        delta = CoinDelta(hour=1.5, day=2.3)

        assert delta.hour == 1.5
        assert delta.day == 2.3
        assert delta.week is None
        assert delta.month is None
        assert delta.quarter is None
        assert delta.year is None

    def test_coin_delta_creation_empty(self):
        """Test creating empty CoinDelta."""
        delta = CoinDelta()

        assert delta.hour is None
        assert delta.day is None
        assert delta.week is None
        assert delta.month is None
        assert delta.quarter is None
        assert delta.year is None


class TestCoinHistory:
    """Tests for the CoinHistory model."""

    def test_coin_history_creation_valid(self):
        """Test creating valid CoinHistory."""
        history = CoinHistory(
            date=1642204800000,  # Valid timestamp
            rate=45000.0,
            volume=28500000000.0,
            cap=850000000000.0,
        )

        assert history.date == 1642204800000
        assert history.rate == 45000.0
        assert history.volume == 28500000000.0
        assert history.cap == 850000000000.0

    def test_coin_history_invalid_date(self):
        """Test CoinHistory with invalid date."""
        with pytest.raises(ValidationError) as exc_info:
            CoinHistory(
                date=-1,  # Invalid negative timestamp
                rate=45000.0,
                volume=28500000000.0,
                cap=850000000000.0,
            )

        assert "Date must be a positive timestamp" in str(exc_info.value)

    def test_coin_history_zero_date(self):
        """Test CoinHistory with zero date."""
        with pytest.raises(ValidationError):
            CoinHistory(date=0, rate=45000.0, volume=28500000000.0, cap=850000000000.0)


class TestCoin:
    """Tests for the Coin model."""

    def test_coin_creation_minimal(self, sample_coin_data):
        """Test creating Coin with minimal required data."""
        minimal_data = {"code": "BTC", "rate": 45000.0}

        coin = Coin(**minimal_data)

        assert coin.code == "BTC"
        assert coin.rate == 45000.0
        assert coin.currency == "USD"  # Default value
        assert isinstance(coin.fetched_at, datetime)

    def test_coin_creation_full_data(self, sample_coin_data):
        """Test creating Coin with full data."""
        coin = Coin(**sample_coin_data)

        assert coin.code == "BTC"
        assert coin.name == "Bitcoin"
        assert coin.symbol == "BTC"
        assert coin.rank == 1
        assert coin.rate == 45000.50
        assert coin.volume == 28500000000.0
        assert coin.cap == 850000000000.0
        assert coin.currency == "USD"
        assert coin.delta is not None
        assert coin.delta.hour == 0.5

    def test_coin_code_validation_uppercase(self):
        """Test that coin code is converted to uppercase."""
        coin = Coin(code="btc", rate=45000.0)
        assert coin.code == "BTC"

    def test_coin_code_validation_trimmed(self):
        """Test that coin code is trimmed."""
        coin = Coin(code="  btc  ", rate=45000.0)
        assert coin.code == "BTC"

    def test_coin_code_validation_empty(self):
        """Test validation with empty code."""
        with pytest.raises(ValidationError):
            Coin(code="", rate=45000.0)

    def test_coin_code_validation_whitespace_only(self):
        """Test validation with whitespace-only code."""
        with pytest.raises(ValidationError):
            Coin(code="   ", rate=45000.0)

    def test_coin_rank_validation_positive(self):
        """Test rank validation with positive values."""
        coin = Coin(code="BTC", rate=45000.0, rank=1)
        assert coin.rank == 1

    def test_coin_rank_validation_negative(self):
        """Test rank validation with negative values."""
        with pytest.raises(ValidationError):
            Coin(code="BTC", rate=45000.0, rank=-1)

    def test_coin_rank_validation_zero(self):
        """Test rank validation with zero."""
        with pytest.raises(ValidationError):
            Coin(code="BTC", rate=45000.0, rank=0)

    def test_coin_with_delta(self):
        """Test creating Coin with delta data."""
        delta_data = {"hour": 1.5, "day": 2.3, "week": -0.8}

        coin = Coin(code="BTC", rate=45000.0, delta=delta_data)

        assert coin.delta.hour == 1.5
        assert coin.delta.day == 2.3
        assert coin.delta.week == -0.8

    def test_coin_with_history(self, sample_coin_history_data):
        """Test creating Coin with historical data."""
        coin = Coin(code="BTC", rate=45000.0, history=sample_coin_history_data)

        assert len(coin.history) == 3
        assert coin.history[0].rate == 44500.0
        assert coin.history[-1].rate == 45000.0

    def test_coin_categories_default(self):
        """Test that categories defaults to empty list."""
        coin = Coin(code="BTC", rate=45000.0)
        assert coin.categories == []

    def test_coin_history_default(self):
        """Test that history defaults to empty list."""
        coin = Coin(code="BTC", rate=45000.0)
        assert coin.history == []


class TestCoinInfluxConversion:
    """Tests for Coin to InfluxDB point conversion."""

    def test_to_influx_point_minimal(self):
        """Test InfluxDB point conversion with minimal data."""
        coin = Coin(code="BTC", rate=45000.0)
        point = coin.to_influx_point()

        assert_influx_point_valid(point)

        assert point["measurement"] == "cryptocurrency_data"
        assert point["tags"]["code"] == "BTC"
        assert point["tags"]["currency"] == "USD"
        assert point["fields"]["rate"] == 45000.0
        assert isinstance(point["time"], datetime)

    def test_to_influx_point_full_data(self, sample_coin_data):
        """Test InfluxDB point conversion with full data."""
        coin = Coin(**sample_coin_data)
        point = coin.to_influx_point()

        assert_influx_point_valid(point)

        # Check tags
        assert point["tags"]["code"] == "BTC"
        assert point["tags"]["name"] == "Bitcoin"
        assert point["tags"]["currency"] == "USD"

        # Check fields
        assert point["fields"]["rate"] == 45000.50
        assert point["fields"]["volume"] == 28500000000.0
        assert point["fields"]["market_cap"] == 850000000000.0
        assert point["fields"]["rank"] == 1

        # Check delta fields
        assert point["fields"]["delta_1h"] == 0.5
        assert point["fields"]["delta_24h"] == 2.3
        assert point["fields"]["delta_7d"] == -1.2
        assert point["fields"]["delta_30d"] == 15.7

    def test_to_influx_point_with_none_values(self):
        """Test InfluxDB point conversion with None values."""
        coin = Coin(code="BTC", rate=45000.0, volume=None, cap=None, rank=None)
        point = coin.to_influx_point()

        assert_influx_point_valid(point)

        # Only rate should be in fields (non-None values)
        assert "rate" in point["fields"]
        assert "volume" not in point["fields"]
        assert "market_cap" not in point["fields"]
        assert "rank" not in point["fields"]

    def test_to_influx_point_no_code(self):
        """Test InfluxDB point conversion when code is None."""
        coin = Coin(rate=45000.0)
        coin.code = None  # Set to None after creation
        point = coin.to_influx_point()

        assert point["tags"]["code"] == "UNKNOWN"

    def test_to_influx_point_no_name(self):
        """Test InfluxDB point conversion when name is None."""
        coin = Coin(code="BTC", rate=45000.0)
        point = coin.to_influx_point()

        assert point["tags"]["name"] == ""

    def test_to_influx_point_partial_delta(self):
        """Test InfluxDB point conversion with partial delta data."""
        delta_data = {
            "hour": 1.5,
            "day": 2.3,
            # week, month, quarter, year are None
        }

        coin = Coin(code="BTC", rate=45000.0, delta=delta_data)
        point = coin.to_influx_point()

        # Only non-None delta fields should be included
        assert point["fields"]["delta_1h"] == 1.5
        assert point["fields"]["delta_24h"] == 2.3
        assert "delta_7d" not in point["fields"]
        assert "delta_30d" not in point["fields"]

    def test_to_influx_point_numeric_conversion(self):
        """Test that numeric values are properly converted to float/int."""
        coin = Coin(
            code="BTC",
            rate="45000.50",  # String that should be converted
            volume="28500000000",  # String that should be converted
            rank="1",  # String that should be converted to int
        )
        point = coin.to_influx_point()

        assert isinstance(point["fields"]["rate"], float)
        assert isinstance(point["fields"]["volume"], float)
        assert isinstance(point["fields"]["rank"], int)

        assert point["fields"]["rate"] == 45000.50
        assert point["fields"]["volume"] == 28500000000.0
        assert point["fields"]["rank"] == 1


class TestCoinEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_coin_with_very_large_numbers(self):
        """Test Coin with very large numeric values."""
        coin = Coin(
            code="BTC",
            rate=1e15,  # Very large rate
            volume=1e20,  # Very large volume
            cap=1e25,  # Very large market cap
        )

        assert coin.rate == 1e15
        assert coin.volume == 1e20
        assert coin.cap == 1e25

        point = coin.to_influx_point()
        assert point["fields"]["rate"] == 1e15

    def test_coin_with_very_small_numbers(self):
        """Test Coin with very small numeric values."""
        coin = Coin(
            code="SHIB",
            rate=0.00000001,  # Very small rate
        )

        assert coin.rate == 0.00000001

        point = coin.to_influx_point()
        assert point["fields"]["rate"] == 0.00000001

    def test_coin_with_zero_values(self):
        """Test Coin with zero values."""
        coin = Coin(code="TEST", rate=0.0, volume=0.0, cap=0.0)

        point = coin.to_influx_point()
        assert point["fields"]["rate"] == 0.0
        assert point["fields"]["volume"] == 0.0
        assert point["fields"]["market_cap"] == 0.0

    def test_coin_serialization_deserialization(self, sample_coin_data):
        """Test that Coin can be serialized and deserialized."""
        original_coin = Coin(**sample_coin_data)

        # Serialize to dict
        coin_dict = original_coin.model_dump()

        # Deserialize back to Coin
        restored_coin = Coin(**coin_dict)

        # Compare key fields
        assert restored_coin.code == original_coin.code
        assert restored_coin.rate == original_coin.rate
        assert restored_coin.volume == original_coin.volume
        assert restored_coin.cap == original_coin.cap

    def test_coin_json_serialization(self, sample_coin_data):
        """Test JSON serialization of Coin."""
        coin = Coin(**sample_coin_data)

        json_str = coin.model_dump_json()
        assert isinstance(json_str, str)
        assert "BTC" in json_str
        assert "Bitcoin" in json_str

    @pytest.mark.parametrize("invalid_code", [None, "", "  ", "\t\n"])
    def test_coin_invalid_codes(self, invalid_code):
        """Test various invalid code values."""
        if invalid_code is None:
            # None is allowed for code
            coin = Coin(rate=45000.0)
            assert coin.code is None
        else:
            # Empty or whitespace-only codes should raise ValidationError
            with pytest.raises(ValidationError):
                Coin(code=invalid_code, rate=45000.0)
