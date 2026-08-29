"""Tests for integration-level setup in __init__.py."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.beach_weather import _async_remove_legacy_card_resource
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


class _FakeResources:
    """Stand-in for Lovelace's ResourceStorageCollection."""

    def __init__(self, items, *, loaded=True, store=object()):
        self._items = list(items)
        self.loaded = loaded
        self.store = store
        self.deleted = []
        self.load_calls = 0

    def async_items(self):
        return list(self._items)

    async def async_load(self):
        self.loaded = True
        self.load_calls += 1

    async def async_delete_item(self, item_id):
        self.deleted.append(item_id)
        self._items = [item for item in self._items if item["id"] != item_id]


class _FakeLovelace:
    def __init__(self, resources):
        self.resources = resources


LEGACY_ITEM = {"id": "legacy", "url": "/beach_weather_static/beach-weather-card.js?v=0.24.0"}
HACS_ITEM = {"id": "hacs", "url": "/hacsfiles/ha-beach-weather-card/beach-weather-card.js?hacstag=1"}
OTHER_ITEM = {"id": "other", "url": "/local/some-unrelated-card.js"}


class TestLegacyResourceCleanup:
    async def test_removes_only_the_legacy_resource(self, hass):
        resources = _FakeResources([LEGACY_ITEM, HACS_ITEM, OTHER_ITEM])
        hass.data["lovelace"] = _FakeLovelace(resources)

        await _async_remove_legacy_card_resource(hass)

        assert resources.deleted == ["legacy"]
        assert [item["id"] for item in resources.async_items()] == ["hacs", "other"]

    async def test_loads_the_store_when_it_is_not_loaded_yet(self, hass):
        resources = _FakeResources([LEGACY_ITEM], loaded=False)
        hass.data["lovelace"] = _FakeLovelace(resources)

        await _async_remove_legacy_card_resource(hass)

        assert resources.load_calls == 1
        assert resources.deleted == ["legacy"]

    async def test_is_a_no_op_in_yaml_resource_mode(self, hass):
        # No store behind the collection — YAML resources can't be managed
        # programmatically, and those users never had a resource written.
        resources = _FakeResources([LEGACY_ITEM], store=None)
        hass.data["lovelace"] = _FakeLovelace(resources)

        await _async_remove_legacy_card_resource(hass)

        assert resources.deleted == []

    async def test_is_a_no_op_without_lovelace(self, hass):
        hass.data.pop("lovelace", None)

        await _async_remove_legacy_card_resource(hass)  # must not raise

    async def test_reads_a_plain_dict_as_used_before_ha_2025_2(self, hass):
        resources = _FakeResources([LEGACY_ITEM])
        hass.data["lovelace"] = {"resources": resources}

        await _async_remove_legacy_card_resource(hass)

        assert resources.deleted == ["legacy"]

    async def test_runs_once_across_multiple_entries(
        self, hass, mock_marine_update, mock_forecast_update
    ):
        with patch(
            "custom_components.beach_weather._async_schedule_legacy_cleanup",
            new_callable=AsyncMock,
        ) as mock_schedule:
            entry_a = _make_entry(hass, "platja_de_muro")
            assert await hass.config_entries.async_setup(entry_a.entry_id)
            entry_b = _make_entry(hass, "maspalomas")
            assert await hass.config_entries.async_setup(entry_b.entry_id)

        mock_schedule.assert_called_once()
        assert hass.data[DOMAIN]["legacy_cleanup_scheduled"] is True

    async def test_setup_survives_a_failing_cleanup(
        self, hass, mock_marine_update, mock_forecast_update
    ):
        # A best-effort cleanup must never take the config entry down with it.
        with patch(
            "custom_components.beach_weather._async_remove_legacy_card_resource",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ):
            entry = _make_entry(hass, "platja_de_muro")
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()


class TestEntityIdSuggestion:
    """The entity_id set in each entity's constructor is a *suggestion*.

    Core's entity_platform documents it as such ("An entity may suggest the
    entity_id by setting entity_id itself"): it is only consulted when the
    registry first creates the entry, and from then on the registry's value —
    including a rename the user made — is what the entity gets back.
    """

    async def test_ids_follow_the_documented_key_slug_shape(
        self, hass, mock_marine_update, mock_forecast_update
    ):
        entry = _make_entry(hass, "platja_de_muro")
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        assert registry.async_get("sensor.water_temperature_platja_de_muro") is not None
        assert registry.async_get("weather.platja_de_muro") is not None
        assert registry.async_get("button.update_now_platja_de_muro") is not None

    async def test_a_user_rename_survives_a_reload(
        self, hass, mock_marine_update, mock_forecast_update
    ):
        entry = _make_entry(hass, "platja_de_muro")
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        registry.async_update_entity(
            "sensor.water_temperature_platja_de_muro",
            new_entity_id="sensor.my_own_water_temperature",
        )
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.my_own_water_temperature") is not None
        assert hass.states.get("sensor.water_temperature_platja_de_muro") is None
