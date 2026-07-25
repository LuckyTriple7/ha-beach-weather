"""Entity-level tests: set up a real config entry (with mocked coordinator
fetches) and check what actually lands in the state machine — the pure-logic
tests elsewhere don't touch entity wiring (unique_id, entity_id, available,
translation_key) at all."""
import pytest
from homeassistant.const import STATE_UNAVAILABLE
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.beach_weather.const import (
    CONF_BEACH_ORIENTATION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SLUG,
    DOMAIN,
)

SLUG = "platja_de_muro"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


async def _setup_entry(hass, mock_marine_update, mock_forecast_update, beach_orientation=340):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "Platja de Muro",
            CONF_SLUG: SLUG,
            CONF_LATITUDE: 39.8,
            CONF_LONGITUDE: 3.11,
            CONF_SCAN_INTERVAL: 900,
            CONF_BEACH_ORIENTATION: beach_orientation,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


class TestSensorSetup:
    async def test_water_temperature_state(self, hass, mock_marine_update, mock_forecast_update):
        await _setup_entry(hass, mock_marine_update, mock_forecast_update)
        state = hass.states.get(f"sensor.water_temperature_{SLUG}")
        assert state is not None
        assert state.state == "23.8"

    async def test_bathing_conditions_uses_default_thresholds(
        self, hass, mock_marine_update, mock_forecast_update
    ):
        await _setup_entry(hass, mock_marine_update, mock_forecast_update)
        state = hass.states.get(f"sensor.bathing_conditions_{SLUG}")
        assert state is not None
        # MOCK_MARINE_CURRENT: wave_height=0.84 (<1.0 calm), water_temp=23.8
        # (>20, not >22-with-period>8) -> "very_good" under DEFAULT_THRESHOLDS.
        assert state.state == "very_good"

    async def test_surf_score_is_numeric_with_breakdown_attributes(
        self, hass, mock_marine_update, mock_forecast_update
    ):
        await _setup_entry(hass, mock_marine_update, mock_forecast_update)
        state = hass.states.get(f"sensor.surf_score_{SLUG}")
        assert state is not None
        assert 0 <= float(state.state) <= 100
        assert "wave_period_score" in state.attributes
        assert "weights_used" in state.attributes
        assert "bonus_frontal_offshore" in state.attributes

    async def test_swell_period_sensor_uses_swell_specific_field(
        self, hass, mock_marine_update, mock_forecast_update
    ):
        await _setup_entry(hass, mock_marine_update, mock_forecast_update)
        state = hass.states.get(f"sensor.swell_period_{SLUG}")
        assert state is not None
        assert state.state == "9.2"

    async def test_last_status_unavailable_without_a_real_http_response(
        self, hass, mock_marine_update, mock_forecast_update
    ):
        # mock_marine_update/mock_forecast_update patch _async_update_data
        # directly, bypassing _fetch_current entirely, so last_status_code
        # is never populated -> the diagnostic sensor stays unavailable.
        await _setup_entry(hass, mock_marine_update, mock_forecast_update)
        state = hass.states.get(f"sensor.last_status_{SLUG}")
        assert state is not None
        assert state.state == STATE_UNAVAILABLE

    async def test_update_now_button_exists(self, hass, mock_marine_update, mock_forecast_update):
        await _setup_entry(hass, mock_marine_update, mock_forecast_update)
        assert hass.states.get(f"button.update_now_{SLUG}") is not None


class TestDiagnostics:
    async def test_redacts_coordinates_and_includes_coordinator_state(
        self, hass, mock_marine_update, mock_forecast_update
    ):
        from custom_components.beach_weather.diagnostics import async_get_config_entry_diagnostics

        entry = await _setup_entry(hass, mock_marine_update, mock_forecast_update)
        diagnostics = await async_get_config_entry_diagnostics(hass, entry)

        assert diagnostics["entry_data"][CONF_LATITUDE] == "**REDACTED**"
        assert diagnostics["entry_data"][CONF_LONGITUDE] == "**REDACTED**"
        assert diagnostics["marine_coordinator"]["last_update_success"] is True
        assert diagnostics["marine_coordinator"]["data"]["sea_surface_temperature"] == 23.8
        assert diagnostics["global_bathing_thresholds"] is not None
        assert diagnostics["global_surf_weights"] is not None
