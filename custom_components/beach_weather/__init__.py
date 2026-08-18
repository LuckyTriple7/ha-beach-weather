from __future__ import annotations

import asyncio
import random
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
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

PLATFORMS = ["sensor", "button", "weather"]

# Bump alongside manifest.json's "version" so browsers pick up card changes
# after a HACS update instead of serving a cached copy of the old script.
CARD_VERSION = "0.24.0"
STATIC_URL_PATH = "/beach_weather_static"
CARD_PATH = f"{STATIC_URL_PATH}/beach-weather-card.js"
CARD_URL = f"{CARD_PATH}?v={CARD_VERSION}"


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
    # Lovelace may not be set up yet when this entry is added; registering at
    # start covers both a cold boot and an entry added while HA is running.
    async_at_started(hass, _async_register_card_resource)


async def _async_register_card_resource(hass: HomeAssistant) -> None:
    """Publish the bundled card as a regular Lovelace resource.

    Deliberately not frontend.add_extra_js_url(): Home Assistant renders those
    into the index page as `<script>if (isModern) { import("<url>"); }</script>`,
    where `isModern` is a user-agent regex plus a feature check. On a browser
    that check rejects, the import never runs and the card silently ends up as
    "Custom element doesn't exist" — while HACS cards keep working, because
    Lovelace loads its own resources regardless of that check.
    """
    # Imported lazily so this module still imports where lovelace isn't set up.
    from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE

    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None or lovelace.resource_mode != MODE_STORAGE:
        # Resources come from YAML (or Lovelace is missing) — those can't be
        # managed programmatically, so fall back to the extra module URL.
        add_extra_js_url(hass, CARD_URL)
        return

    resources = lovelace.resources
    await resources.async_get_info()  # does nothing but force the store to load

    for item in resources.async_items():
        if item["url"].split("?")[0] != CARD_PATH:
            continue
        # Same card, stale ?v= (or wrong type) — update in place so browsers
        # fetch the new file after an update instead of serving a cached one.
        if item["url"] != CARD_URL or item.get("type") != "module":
            await resources.async_update_item(
                item["id"], {"res_type": "module", "url": CARD_URL}
            )
        return

    await resources.async_create_item({"res_type": "module", "url": CARD_URL})


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
