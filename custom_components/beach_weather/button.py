from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_SLUG, DOMAIN, KEY_UPDATE_NOW
from .coordinator import ForecastCoordinator, MarineCoordinator
from .sensor import _device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([UpdateNowButton(data["marine"], data["forecast"], entry)])


class UpdateNowButton(ButtonEntity):
    """Forces an immediate refresh of both coordinators for this location,
    bypassing the shared rate limiter and any active error backoff — an
    explicit manual action always wins over the automatic burst protection."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        marine: MarineCoordinator,
        forecast: ForecastCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self._marine = marine
        self._forecast = forecast
        slug = entry.data[CONF_SLUG]
        self._attr_unique_id = f"{entry.entry_id}_{KEY_UPDATE_NOW}"
        self._attr_translation_key = KEY_UPDATE_NOW
        # Suggestion only: core treats an entity_id set here as the suggested
        # object id (entity_platform: "An entity may suggest the entity_id by
        # setting entity_id itself"), so the registry uses it when it first
        # creates the entry and its own value — including a user's rename —
        # wins on every later start. Keeps the ids the bundled card and
        # existing picture-elements cards look up by prefix.
        self.entity_id = f"button.{KEY_UPDATE_NOW}_{slug}"
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        await self._marine.async_force_refresh()
        await self._forecast.async_force_refresh()
