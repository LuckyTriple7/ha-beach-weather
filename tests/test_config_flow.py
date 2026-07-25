"""Tests for the Beach Weather config flow."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.beach_weather.const import (
    CONF_BEACH_ORIENTATION,
    CONF_COORDINATES_PASTE,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SLUG,
    DEFAULT_SURF_WEIGHTS,
    DEFAULT_THRESHOLDS,
    DOMAIN,
    KEY_TOO_COLD_MAX,
    KEY_WEIGHT_WAVE_PERIOD,
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
                CONF_BEACH_ORIENTATION: 340,
            },
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Platja de Muro"
        assert result["data"][CONF_SLUG] == "platja_de_muro"
        assert result["data"][CONF_LATITUDE] == LOCATION_INPUT["latitude"]
        assert result["data"][CONF_LONGITUDE] == LOCATION_INPUT["longitude"]
        assert result["data"][CONF_BEACH_ORIENTATION] == 340

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

    async def test_paste_coordinates_reflows_without_creating_entry(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        with (
            patch(
                "custom_components.beach_weather.config_flow.async_suggest_name",
                new_callable=AsyncMock,
                return_value="Suggested Beach",
            ),
            patch(
                "custom_components.beach_weather.config_flow.async_suggest_orientation",
                new_callable=AsyncMock,
                return_value=123,
            ),
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_COORDINATES_PASTE: "27.787333, -15.723408",
                    CONF_NAME: "",
                    CONF_LOCATION: LOCATION_INPUT,
                    CONF_SCAN_INTERVAL: 900,
                    CONF_BEACH_ORIENTATION: 0,
                },
            )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert not result["errors"]

        # Second submission (paste left empty this time) actually creates it,
        # using the reviewed/confirmed values.
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Suggested Beach",
                CONF_LOCATION: {"latitude": 27.787333, "longitude": -15.723408},
                CONF_SCAN_INTERVAL: 900,
                CONF_BEACH_ORIENTATION: 123,
            },
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_LATITUDE] == 27.787333
        assert result["data"][CONF_LONGITUDE] == -15.723408
        assert result["data"][CONF_BEACH_ORIENTATION] == 123

    async def test_paste_unresolvable_text_shows_error(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        with patch(
            "custom_components.beach_weather.config_flow.async_search_place",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_COORDINATES_PASTE: "not coordinates and no such place",
                    CONF_NAME: "",
                    CONF_LOCATION: LOCATION_INPUT,
                    CONF_SCAN_INTERVAL: 900,
                    CONF_BEACH_ORIENTATION: 0,
                },
            )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"][CONF_COORDINATES_PASTE] == "location_not_found"

    async def test_paste_place_name_searches_and_prefills(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        with (
            patch(
                "custom_components.beach_weather.config_flow.async_search_place",
                new_callable=AsyncMock,
                return_value=(27.787333, -15.723408, "Playa de Maspalomas"),
            ) as mock_search,
            patch(
                "custom_components.beach_weather.config_flow.async_suggest_name",
                new_callable=AsyncMock,
            ) as mock_reverse_name,
            patch(
                "custom_components.beach_weather.config_flow.async_suggest_orientation",
                new_callable=AsyncMock,
                return_value=45,
            ),
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_COORDINATES_PASTE: "Maspalomas beach",
                    CONF_NAME: "",
                    CONF_LOCATION: LOCATION_INPUT,
                    CONF_SCAN_INTERVAL: 900,
                    CONF_BEACH_ORIENTATION: 0,
                },
            )
        assert result["type"] == FlowResultType.FORM
        assert not result["errors"]
        mock_search.assert_awaited_once_with(hass, "Maspalomas beach")
        # Search already returned a name -> no need for the reverse-geocode fallback
        mock_reverse_name.assert_not_called()

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Playa de Maspalomas",
                CONF_LOCATION: {"latitude": 27.787333, "longitude": -15.723408},
                CONF_SCAN_INTERVAL: 900,
                CONF_BEACH_ORIENTATION: 45,
            },
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_NAME] == "Playa de Maspalomas"


class TestOptionsFlow:
    def _make_entry(self, hass):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_NAME: "Platja de Muro",
                CONF_SLUG: "platja_de_muro",
                CONF_LATITUDE: 39.8,
                CONF_LONGITUDE: 3.11,
                CONF_SCAN_INTERVAL: 900,
            },
        )
        entry.add_to_hass(hass)
        return entry

    async def test_init_shows_menu(self, hass):
        entry = self._make_entry(hass)
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == FlowResultType.MENU
        assert set(result["menu_options"]) == {"location", "thresholds", "surf_weights"}

    async def test_thresholds_step_saves_and_dispatches(self, hass):
        entry = self._make_entry(hass)
        hass.data.setdefault(DOMAIN, {})["thresholds"] = dict(DEFAULT_THRESHOLDS)

        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "thresholds"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "thresholds"

        new_values = {**DEFAULT_THRESHOLDS, KEY_TOO_COLD_MAX: 20.0}
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], new_values
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert hass.data[DOMAIN]["thresholds"][KEY_TOO_COLD_MAX] == 20.0

    async def test_surf_weights_step_saves_and_dispatches(self, hass):
        entry = self._make_entry(hass)
        hass.data.setdefault(DOMAIN, {})["surf_weights"] = dict(DEFAULT_SURF_WEIGHTS)

        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "surf_weights"}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "surf_weights"

        new_values = {**DEFAULT_SURF_WEIGHTS, KEY_WEIGHT_WAVE_PERIOD: 50.0}
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], new_values
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert hass.data[DOMAIN]["surf_weights"][KEY_WEIGHT_WAVE_PERIOD] == 50.0

    async def test_location_step_flattens_coordinates_into_options(self, hass):
        entry = self._make_entry(hass)

        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "location"}
        )
        assert result["step_id"] == "location"

        new_location = {"latitude": 40.0, "longitude": 4.0}
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_LOCATION: new_location,
                CONF_SCAN_INTERVAL: 900,
                CONF_BEACH_ORIENTATION: 200,
            },
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_LATITUDE] == 40.0
        assert result["data"][CONF_LONGITUDE] == 4.0
        assert CONF_LOCATION not in result["data"]

    async def test_location_step_paste_reflows_without_saving(self, hass):
        entry = self._make_entry(hass)

        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": "location"}
        )

        with (
            patch(
                "custom_components.beach_weather.config_flow.async_suggest_name",
                new_callable=AsyncMock,
            ) as mock_name,
            patch(
                "custom_components.beach_weather.config_flow.async_suggest_orientation",
                new_callable=AsyncMock,
                return_value=200,
            ),
        ):
            result = await hass.config_entries.options.async_configure(
                result["flow_id"],
                {
                    CONF_COORDINATES_PASTE: "40.0, 4.0",
                    CONF_LOCATION: {"latitude": 39.8, "longitude": 3.11},
                    CONF_SCAN_INTERVAL: 900,
                    CONF_BEACH_ORIENTATION: 0,
                },
            )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "location"
        mock_name.assert_not_called()  # no name field on this step
