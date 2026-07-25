from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DEFAULT_THRESHOLDS, DOMAIN, STORAGE_KEY, STORAGE_VERSION


def _store(hass: HomeAssistant) -> Store:
    return Store(hass, STORAGE_VERSION, STORAGE_KEY)


async def async_load_thresholds(hass: HomeAssistant) -> dict[str, float]:
    saved = await _store(hass).async_load()
    return {**DEFAULT_THRESHOLDS, **(saved or {})}


async def async_save_thresholds(hass: HomeAssistant, values: dict[str, float]) -> None:
    await _store(hass).async_save(values)
    hass.data.setdefault(DOMAIN, {})["thresholds"] = values
