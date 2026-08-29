from __future__ import annotations

import asyncio
import logging
import random

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.start import async_at_started

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

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button", "weather"]

# Up to 0.24.0 the Lovelace card shipped inside this integration, served from
# this static path and registered as a Lovelace resource by the integration.
# The card is its own HACS dashboard repository now
# (https://github.com/LuckyTriple7/ha-beach-weather-card), so the path is gone
# and any leftover resource pointing at it has to go with it.
LEGACY_STATIC_URL_PATH = "/beach_weather_static/"


async def _async_remove_legacy_card_resource(hass: HomeAssistant) -> None:
    """Delete the Lovelace resource earlier versions of this integration wrote.

    Without this, updating leaves a resource pointing at a path nothing serves
    any more, which Lovelace then retries on every dashboard render, forever.
    Only entries under the old static path are touched — the rest of the
    user's resource store is left alone, and once this has run the integration
    never writes to it again.
    """
    # Read through hass.data instead of importing from lovelace.const: the
    # LOVELACE_DATA key only exists from HA 2025.2, and the attribute holding
    # the resource mode was renamed in 2026.2. Neither is worth raising the
    # minimum HA version for a one-time cleanup.
    lovelace = hass.data.get("lovelace")
    if lovelace is None:
        return
    if isinstance(lovelace, dict):  # HA < 2025.2 kept a plain dict here
        resources = lovelace.get("resources")
    else:
        resources = getattr(lovelace, "resources", None)
    # YAML resource mode has no store behind it and can't be managed
    # programmatically — those users never got a resource written either.
    if resources is None or getattr(resources, "store", None) is None:
        return

    if not resources.loaded:
        await resources.async_load()
    for item in list(resources.async_items() or []):
        if not str(item.get("url", "")).startswith(LEGACY_STATIC_URL_PATH):
            continue
        _LOGGER.info(
            "Removing the Lovelace resource this integration registered before the card "
            "moved to its own repository: %s. Install 'Beach Weather Card' from HACS to "
            "keep using it",
            item["url"],
        )
        await resources.async_delete_item(item["id"])


async def _async_schedule_legacy_cleanup(hass: HomeAssistant) -> None:
    async def _run(_hass: HomeAssistant) -> None:
        try:
            await _async_remove_legacy_card_resource(hass)
        except Exception:  # noqa: BLE001 - cleanup must never break setup
            _LOGGER.warning("Could not clean up the legacy card resource", exc_info=True)

    # Lovelace may not be set up yet when this entry is added; running at
    # start covers both a cold boot and an entry added while HA is running.
    async_at_started(hass, _run)


async def _async_initial_refresh(marine: MarineCoordinator, forecast: ForecastCoordinator) -> None:
    # Avoids ~20 entries queuing for the shared rate limiter in lockstep at
    # HA boot. Not required for correctness, just a thundering-herd nicety.
    await asyncio.sleep(random.uniform(0, INITIAL_JITTER_MAX))
    # async_refresh (not async_config_entry_first_refresh) — this runs as a
    # background task, decoupled from HA's own startup, so there's no
    # ConfigEntryNotReady to raise; the coordinator's regular polling already
    # retries on failure.
    await marine.async_refresh()
    await forecast.async_refresh()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data.setdefault("rate_limiter", OpenMeteoRateLimiter(RATE_LIMIT_MIN_SPACING))
    if "thresholds" not in domain_data:
        domain_data["thresholds"] = await async_load_thresholds(hass)
    if "surf_weights" not in domain_data:
        domain_data["surf_weights"] = await async_load_surf_weights(hass)
    if not domain_data.get("legacy_cleanup_scheduled"):
        await _async_schedule_legacy_cleanup(hass)
        domain_data["legacy_cleanup_scheduled"] = True

    effective = {**entry.data, **entry.options}
    scan_interval = effective.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    marine = MarineCoordinator(hass, entry, scan_interval)
    forecast = ForecastCoordinator(hass, entry, scan_interval)
    # coordinates may have been changed via the options flow; the base class
    # reads them from entry.data at construction time, so patch if overridden
    for coord in (marine, forecast):
        coord.latitude = effective.get(CONF_LATITUDE, coord.latitude)
        coord.longitude = effective.get(CONF_LONGITUDE, coord.longitude)

    domain_data[entry.entry_id] = {"marine": marine, "forecast": forecast}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    # Entities come up "unavailable" and populate once the shared rate
    # limiter gets to this entry's turn — with 20+ locations that queue can
    # take a couple minutes, and none of it should hold up HA's own startup.
    entry.async_create_background_task(
        hass,
        _async_initial_refresh(marine, forecast),
        f"{DOMAIN}_{entry.entry_id}_initial_refresh",
    )
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data = hass.data.get(DOMAIN, {})
        domain_data.pop(entry.entry_id, None)

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
