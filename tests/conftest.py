"""Shared fixtures for Beach Weather tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

# Generated relative to "now" (not fixed dates) since the Marine hourly
# forecast attribute filters out anything already in the past.
_MARINE_HOURLY_TIMES = [
    (datetime.now(timezone.utc) + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M")
    for i in range(1, 4)
]

MOCK_MARINE_CURRENT = {
    "time": "2026-07-22T15:30",
    "sea_surface_temperature": 23.8,
    "wave_height": 0.84,
    "wave_direction": 39,
    "wave_period": 6.3,
    "swell_wave_height": 0.6,
    "swell_wave_direction": 210,
    "swell_wave_period": 9.2,
    "wind_wave_height": 0.3,
    "wind_wave_direction": 45,
    "wind_wave_period": 3.1,
    "ocean_current_velocity": 1.4,
    "ocean_current_direction": 95,
    "_hourly": {
        "time": _MARINE_HOURLY_TIMES,
        "wave_height": [0.8, 0.9, 1.0],
        "wave_direction": [39, 40, 41],
        "wave_period": [6.3, 6.4, 6.5],
        "sea_surface_temperature": [23.8, 23.7, 23.6],
        "swell_wave_height": [0.6, 0.6, 0.7],
        "swell_wave_direction": [210, 211, 212],
        "swell_wave_period": [9.2, 9.3, 9.4],
        "wind_wave_height": [0.3, 0.3, 0.4],
        "wind_wave_direction": [45, 46, 47],
        "wind_wave_period": [3.1, 3.2, 3.3],
        "ocean_current_velocity": [1.4, 1.5, 1.6],
        "ocean_current_direction": [95, 96, 97],
    },
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
    "visibility": 24140.0,
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
