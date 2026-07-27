"""Tests for the weather.<slug> entity: WMO->HA condition mapping and
Open-Meteo hourly/daily -> HA Forecast list builders (pure functions), plus
a basic entity-setup smoke test."""
from custom_components.beach_weather.weather import (
    build_daily_forecast,
    build_hourly_forecast,
    condition_for_wmo_code,
)


class TestConditionForWmoCode:
    def test_none_code_returns_none(self):
        assert condition_for_wmo_code(None) is None

    def test_clear_sky_day_vs_night(self):
        assert condition_for_wmo_code(0, is_day=True) == "sunny"
        assert condition_for_wmo_code(0, is_day=False) == "clear-night"
        assert condition_for_wmo_code(1, is_day=True) == "sunny"
        assert condition_for_wmo_code(1, is_day=False) == "clear-night"

    def test_common_codes(self):
        assert condition_for_wmo_code(2) == "partlycloudy"
        assert condition_for_wmo_code(3) == "cloudy"
        assert condition_for_wmo_code(45) == "fog"
        assert condition_for_wmo_code(61) == "rainy"
        assert condition_for_wmo_code(65) == "pouring"
        assert condition_for_wmo_code(71) == "snowy"
        assert condition_for_wmo_code(95) == "lightning"
        assert condition_for_wmo_code(99) == "lightning-rainy"

    def test_unmapped_code_returns_none(self):
        assert condition_for_wmo_code(12345) is None


class TestBuildHourlyForecast:
    def test_builds_one_entry_per_timestamp(self):
        hourly = {
            "time": ["2026-07-22T16:00", "2026-07-22T17:00"],
            "temperature_2m": [27.0, 26.5],
            "weather_code": [1, 3],
            "precipitation": [0.0, 0.2],
            "precipitation_probability": [0, 20],
            "wind_speed_10m": [20.0, 18.0],
            "wind_direction_10m": [50, 55],
            "pressure_msl": [1009.0, 1009.2],
            "relative_humidity_2m": [65, 66],
            "uv_index": [3.0, 2.0],
        }
        forecast = build_hourly_forecast(hourly)
        assert len(forecast) == 2
        assert forecast[0]["native_temperature"] == 27.0
        assert forecast[0]["condition"] == "sunny"
        assert forecast[1]["condition"] == "cloudy"
        assert forecast[1]["native_precipitation"] == 0.2
        assert forecast[0]["datetime"].startswith("2026-07-22T16:00")

    def test_empty_time_returns_empty_list(self):
        assert build_hourly_forecast({"time": []}) == []
        assert build_hourly_forecast({}) == []


class TestBuildDailyForecast:
    def test_builds_one_entry_per_day(self):
        daily = {
            "time": ["2026-07-22", "2026-07-23"],
            "weather_code": [1, 61],
            "temperature_2m_max": [30.0, 29.0],
            "temperature_2m_min": [24.0, 23.5],
            "precipitation_sum": [0.0, 3.5],
            "precipitation_probability_max": [0, 80],
            "wind_speed_10m_max": [25.0, 22.0],
            "wind_direction_10m_dominant": [48, 52],
            "uv_index_max": [7.0, 6.5],
        }
        forecast = build_daily_forecast(daily)
        assert len(forecast) == 2
        assert forecast[0]["native_temperature"] == 30.0
        assert forecast[0]["native_templow"] == 24.0
        assert forecast[1]["condition"] == "rainy"
        assert forecast[1]["native_precipitation"] == 3.5

    def test_empty_time_returns_empty_list(self):
        assert build_daily_forecast({"time": []}) == []


class TestWeatherEntitySetup:
    async def test_entity_exposes_current_conditions(
        self, hass, mock_marine_update, mock_forecast_update, enable_custom_integrations
    ):
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

        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_NAME: "Platja de Muro",
                CONF_SLUG: "platja_de_muro",
                CONF_LATITUDE: 39.8,
                CONF_LONGITUDE: 3.11,
                CONF_SCAN_INTERVAL: 900,
                CONF_BEACH_ORIENTATION: 340,
            },
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        # First refresh now runs as a background task so it never blocks HA
        # startup — force it here for a deterministic state in the test.
        data = hass.data[DOMAIN][entry.entry_id]
        await data["marine"].async_refresh()
        await data["forecast"].async_refresh()
        await hass.async_block_till_done()

        state = hass.states.get("weather.platja_de_muro")
        assert state is not None
        assert state.state == "sunny"  # weather_code=1, is_day=1 in MOCK_FORECAST_CURRENT
        assert state.attributes["temperature"] == 27.4
        assert state.attributes["humidity"] == 67
        assert state.attributes["visibility"] == 24.1  # 24140 m -> km, rounded
