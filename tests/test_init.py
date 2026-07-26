"""Tests for integration-level setup in __init__.py."""
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.beach_weather.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SLUG,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


def _make_entry(hass, slug):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: slug,
            CONF_SLUG: slug,
            CONF_LATITUDE: 39.8,
            CONF_LONGITUDE: 3.11,
            CONF_SCAN_INTERVAL: 900,
        },
    )
    entry.add_to_hass(hass)
    return entry


class TestFrontendRegistration:
    async def test_skips_when_http_not_loaded(self, hass, mock_marine_update, mock_forecast_update):
        # hass.http is None in the unit test harness (the `http` component
        # isn't set up); registration must not raise, and the guard flag
        # still ends up set so a second entry doesn't retry it.
        entry = _make_entry(hass, "platja_de_muro")
        assert await hass.config_entries.async_setup(entry.entry_id)
        assert hass.data[DOMAIN]["frontend_registered"] is True

    async def test_registers_only_once_across_multiple_entries(
        self, hass, mock_marine_update, mock_forecast_update
    ):
        with patch(
            "custom_components.beach_weather._async_register_frontend",
            new_callable=AsyncMock,
        ) as mock_register:
            entry_a = _make_entry(hass, "platja_de_muro")
            assert await hass.config_entries.async_setup(entry_a.entry_id)
            entry_b = _make_entry(hass, "maspalomas")
            assert await hass.config_entries.async_setup(entry_b.entry_id)

        mock_register.assert_called_once()
