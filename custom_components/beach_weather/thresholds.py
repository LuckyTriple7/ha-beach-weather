from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DEFAULT_SURF_WEIGHTS,
    DEFAULT_THRESHOLDS,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_KEY_SURF_WEIGHTS,
    STORAGE_VERSION,
)


def _store(hass: HomeAssistant, key: str) -> Store:
    return Store(hass, STORAGE_VERSION, key)


async def async_load_thresholds(hass: HomeAssistant) -> dict[str, float]:
    saved = await _store(hass, STORAGE_KEY).async_load()
    return {**DEFAULT_THRESHOLDS, **(saved or {})}


async def async_save_thresholds(hass: HomeAssistant, values: dict[str, float]) -> None:
    await _store(hass, STORAGE_KEY).async_save(values)
    hass.data.setdefault(DOMAIN, {})["thresholds"] = values


async def async_load_surf_weights(hass: HomeAssistant) -> dict[str, float]:
    saved = await _store(hass, STORAGE_KEY_SURF_WEIGHTS).async_load()
    return {**DEFAULT_SURF_WEIGHTS, **(saved or {})}


async def async_save_surf_weights(hass: HomeAssistant, values: dict[str, float]) -> None:
    await _store(hass, STORAGE_KEY_SURF_WEIGHTS).async_save(values)
    hass.data.setdefault(DOMAIN, {})["surf_weights"] = values
