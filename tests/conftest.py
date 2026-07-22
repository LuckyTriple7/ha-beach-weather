"""Shared fixtures for Beach Weather tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

MOCK_MARINE_CURRENT = {
    "time": "2026-07-22T15:30",
    "sea_surface_temperature": 23.8,
    "wave_height": 0.84,
    "wave_period": 6.3,
}

MOCK_FORECAST_CURRENT = {
    "time": "2026-07-22T15:30",
    "wind_speed_10m": 23.7,
    "wind_direction_10m": 47,
    "wind_gusts_10m": 49.7,
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
