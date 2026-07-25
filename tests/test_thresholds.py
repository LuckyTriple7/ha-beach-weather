"""Tests for the global Bathing Conditions threshold Store."""
from custom_components.beach_weather.const import DEFAULT_THRESHOLDS, DOMAIN, KEY_TOO_COLD_MAX
from custom_components.beach_weather.thresholds import async_load_thresholds, async_save_thresholds


class TestThresholds:
    async def test_load_returns_defaults_when_nothing_saved(self, hass):
        values = await async_load_thresholds(hass)
        assert values == DEFAULT_THRESHOLDS

    async def test_save_then_load_roundtrips(self, hass):
        custom = {**DEFAULT_THRESHOLDS, KEY_TOO_COLD_MAX: 21.5}
        await async_save_thresholds(hass, custom)

        assert hass.data[DOMAIN]["thresholds"] == custom

        loaded = await async_load_thresholds(hass)
        assert loaded[KEY_TOO_COLD_MAX] == 21.5
