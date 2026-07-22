"""Tests for the Beach Weather config flow."""
import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.beach_weather.const import (
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SLUG,
    DOMAIN,
)

LOCATION_INPUT = {"latitude": 39.8, "longitude": 3.11}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def mock_setup(mock_marine_update, mock_forecast_update):
    yield


class TestConfigFlow:
    async def test_user_step_shows_form(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_full_flow_creates_entry(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Platja de Muro",
                CONF_LOCATION: LOCATION_INPUT,
                CONF_SCAN_INTERVAL: 900,
            },
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Platja de Muro"
        assert result["data"][CONF_SLUG] == "platja_de_muro"
        assert result["data"][CONF_LATITUDE] == LOCATION_INPUT["latitude"]
        assert result["data"][CONF_LONGITUDE] == LOCATION_INPUT["longitude"]

    async def test_empty_name_shows_error(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "   ",
                CONF_LOCATION: LOCATION_INPUT,
                CONF_SCAN_INTERVAL: 900,
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert "invalid_name" in result["errors"].values()

    async def test_duplicate_name_aborted(self, hass):
        result = None
        for _ in range(2):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_NAME: "Platja de Muro",
                    CONF_LOCATION: LOCATION_INPUT,
                    CONF_SCAN_INTERVAL: 900,
                },
            )
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"
