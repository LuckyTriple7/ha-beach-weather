from __future__ import annotations

import asyncio
import random
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    INITIAL_JITTER_MAX,
    RATE_LIMIT_MIN_SPACING,
)
from .coordinator import ForecastCoordinator, MarineCoordinator
from .ratelimiter import OpenMeteoRateLimiter
from .thresholds import async_load_surf_weights, async_load_thresholds

PLATFORMS = ["sensor", "button", "weather"]

# Bump alongside manifest.json's "version" so browsers pick up card changes
# after a HACS update instead of serving a cached copy of the old script.
CARD_VERSION = "0.15.4"
STATIC_URL_PATH = "/beach_weather_static"
CARD_URL = f"{STATIC_URL_PATH}/beach-weather-card.js?v={CARD_VERSION}"


async def _async_register_frontend(hass: HomeAssistant) -> None:
    # The `http` component isn't loaded in the unit test harness (it's not
    # requested by any fixture there, so hass.http stays None); skip
    # registration rather than error.
    if getattr(hass, "http", None) is None:
        return
    www_path = Path(__file__).parent / "www"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL_PATH, str(www_path), cache_headers=False)]
    )
    add_extra_js_url(hass, CARD_URL)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data.setdefault("rate_limiter", OpenMeteoRateLimiter(RATE_LIMIT_MIN_SPACING))
    if "thresholds" not in domain_data:
        domain_data["thresholds"] = await async_load_thresholds(hass)
    if "surf_weights" not in domain_data:
        domain_data["surf_weights"] = await async_load_surf_weights(hass)
    if not domain_data.get("frontend_registered"):
        await _async_register_frontend(hass)
        domain_data["frontend_registered"] = True

    effective = {**entry.data, **entry.options}
    scan_interval = effective.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    marine = MarineCoordinator(hass, entry, scan_interval)
    forecast = ForecastCoordinator(hass, entry, scan_interval)
    # coordinates may have been changed via the options flow; the base class
    # reads them from entry.data at construction time, so patch if overridden
    for coord in (marine, forecast):
        coord.latitude = effective.get(CONF_LATITUDE, coord.latitude)
        coord.longitude = effective.get(CONF_LONGITUDE, coord.longitude)

    # Avoids ~20 entries queuing for the shared rate limiter in lockstep at
    # HA boot. Not required for correctness, just a thundering-herd nicety.
    await asyncio.sleep(random.uniform(0, INITIAL_JITTER_MAX))

    await marine.async_config_entry_first_refresh()
    await forecast.async_config_entry_first_refresh()

    domain_data[entry.entry_id] = {"marine": marine, "forecast": forecast}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data = hass.data.get(DOMAIN, {})
        entry_data = domain_data.pop(entry.entry_id, None)
        if entry_data:
            await entry_data["marine"].async_close()
            await entry_data["forecast"].async_close()

        other_loaded = [
            e
            for e in hass.config_entries.async_entries(DOMAIN)
            if e.entry_id != entry.entry_id and e.state is ConfigEntryState.LOADED
        ]
        if not other_loaded:
            domain_data.pop("rate_limiter", None)
            domain_data.pop("thresholds", None)
            domain_data.pop("surf_weights", None)
        if not domain_data:
            hass.data.pop(DOMAIN, None)
    return unload_ok
