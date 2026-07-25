"""Shared fixtures for Beach Weather tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

MOCK_MARINE_CURRENT = {
    "time": "2026-07-22T15:30",
    "sea_surface_temperature": 23.8,
    "wave_height": 0.84,
    "wave_direction": 39,
    "wave_period": 6.3,
    "swell_wave_height": 0.6,
    "swell_wave_direction": 210,
    "swell_wave_period": 9.2,
}

MOCK_FORECAST_CURRENT = {
    "time": "2026-07-22T15:30",
    "wind_speed_10m": 23.7,
    "wind_direction_10m": 47,
    "wind_gusts_10m": 49.7,
    "temperature_2m": 27.4,
    "weather_code": 1,
    "relative_humidity_2m": 67,
    "precipitation": 0.0,
    "rain": 0.0,
    "showers": 0.0,
    "pressure_msl": 1008.9,
    "cloud_cover": 92,
    "uv_index": 6.15,
    "is_day": 1,
    "_hourly": {
        "time": ["2026-07-22T16:00", "2026-07-22T17:00"],
        "temperature_2m": [27.0, 26.5],
        "weather_code": [1, 2],
        "precipitation": [0.0, 0.0],
        "precipitation_probability": [0, 5],
        "wind_speed_10m": [20.0, 18.0],
        "wind_direction_10m": [50, 55],
        "pressure_msl": [1009.0, 1009.2],
        "relative_humidity_2m": [65, 66],
        "uv_index": [3.0, 2.0],
    },
    "_daily": {
        "time": ["2026-07-22", "2026-07-23"],
        "weather_code": [1, 2],
        "temperature_2m_max": [30.0, 29.0],
        "temperature_2m_min": [24.0, 23.5],
        "precipitation_sum": [0.0, 0.1],
        "precipitation_probability_max": [0, 10],
        "wind_speed_10m_max": [25.0, 22.0],
        "wind_direction_10m_dominant": [48, 52],
        "uv_index_max": [7.0, 6.5],
    },
}


@pytest.fixture
def mock_marine_update():
    with patch(
        "custom_components.beach_weather.coordinator.MarineCoordinator._async_update_data",
        new_callable=AsyncMock,
        return_value=MOCK_MARINE_CURRENT,
    ) as mock:
        yield mock


@pytest.fixture
def mock_forecast_update():
    with patch(
        "custom_components.beach_weather.coordinator.ForecastCoordinator._async_update_data",
        new_callable=AsyncMock,
        return_value=MOCK_FORECAST_CURRENT,
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def no_startup_jitter():
    with patch("custom_components.beach_weather.random.uniform", return_value=0):
        yield
