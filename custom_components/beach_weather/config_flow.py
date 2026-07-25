from __future__ import annotations

import asyncio

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.selector import (
    LocationSelector,
    LocationSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)
from homeassistant.util import slugify

from .const import (
    CONF_BEACH_ORIENTATION,
    CONF_COORDINATES_PASTE,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SLUG,
    DEFAULT_BEACH_ORIENTATION,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SURF_WEIGHTS,
    DEFAULT_THRESHOLDS,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    SIGNAL_SURF_WEIGHTS_UPDATED,
    SIGNAL_THRESHOLDS_UPDATED,
    SURF_WEIGHT_RANGE,
    THRESHOLD_RANGES,
)
from .geo import async_suggest_name, async_suggest_orientation, parse_pasted_coordinates
from .thresholds import async_save_surf_weights, async_save_thresholds

_ORIENTATION_SELECTOR = NumberSelector(
    NumberSelectorConfig(min=0, max=359, step=1, mode=NumberSelectorMode.SLIDER, unit_of_measurement="°")
)


async def _async_apply_pasted_coordinates(hass, paste: str, prefill: dict, *, suggest_name: bool) -> bool:
    """Parse a pasted "lat, lon" string into prefill[CONF_LOCATION] and, best
    effort, look up a suggested name/orientation for it. Returns False (with
    an error placed by the caller) if the text couldn't be parsed."""
    parsed = parse_pasted_coordinates(paste)
    if parsed is None:
        return False

    lat, lon = parsed
    prefill[CONF_LOCATION] = {"latitude": lat, "longitude": lon}

    lookups = [async_suggest_orientation(hass, lat, lon)]
    if suggest_name:
        lookups.insert(0, async_suggest_name(hass, lat, lon))
    results = await asyncio.gather(*lookups, return_exceptions=True)

    if suggest_name:
        suggested_name, suggested_orientation = results
        if isinstance(suggested_name, str) and suggested_name:
            prefill[CONF_NAME] = suggested_name
    else:
        (suggested_orientation,) = results

    if isinstance(suggested_orientation, (int, float)):
        prefill[CONF_BEACH_ORIENTATION] = suggested_orientation
    return True


class BeachWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        super().__init__()
        self._prefill: dict = {}

    def _schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Optional(CONF_COORDINATES_PASTE, default=""): str,
                vol.Required(CONF_NAME, default=self._prefill.get(CONF_NAME, "")): str,
                vol.Required(
                    CONF_LOCATION,
                    default=self._prefill.get(
                        CONF_LOCATION,
                        {
                            "latitude": self.hass.config.latitude,
                            "longitude": self.hass.config.longitude,
                        },
                    ),
                ): LocationSelector(LocationSelectorConfig(radius=False)),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)),
                vol.Required(
                    CONF_BEACH_ORIENTATION,
                    default=self._prefill.get(CONF_BEACH_ORIENTATION, DEFAULT_BEACH_ORIENTATION),
                ): _ORIENTATION_SELECTOR,
            }
        )

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            paste = (user_input.get(CONF_COORDINATES_PASTE) or "").strip()
            if paste:
                # Re-show the same step with parsed coordinates + best-effort
                # name/orientation suggestions pre-filled, for the user to
                # review/adjust — don't create the entry on this pass.
                ok = await _async_apply_pasted_coordinates(
                    self.hass, paste, self._prefill, suggest_name=True
                )
                if not ok:
                    errors[CONF_COORDINATES_PASTE] = "invalid_coordinates"
                else:
                    return self.async_show_form(step_id="user", data_schema=self._schema())
            else:
                name = user_input[CONF_NAME].strip()
                if not name:
                    errors["name"] = "invalid_name"
                else:
                    slug = slugify(name)
                    await self.async_set_unique_id(slug)
                    self._abort_if_unique_id_configured()

                    location = user_input[CONF_LOCATION]
                    data = {
                        CONF_NAME: name,
                        CONF_SLUG: slug,
                        CONF_LATITUDE: location["latitude"],
                        CONF_LONGITUDE: location["longitude"],
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_BEACH_ORIENTATION: user_input[CONF_BEACH_ORIENTATION],
                    }
                    return self.async_create_entry(title=name, data=data)

        return self.async_show_form(step_id="user", data_schema=self._schema(), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return BeachWeatherOptionsFlow()


class BeachWeatherOptionsFlow(config_entries.OptionsFlow):
    def __init__(self) -> None:
        super().__init__()
        self._prefill: dict = {}

    async def async_step_init(self, user_input=None) -> FlowResult:
        return self.async_show_menu(
            step_id="init", menu_options=["location", "thresholds", "surf_weights"]
        )

    async def async_step_location(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            paste = (user_input.get(CONF_COORDINATES_PASTE) or "").strip()
            if paste:
                # No name field on this step (name/slug stay frozen), so only
                # location + orientation get suggested.
                ok = await _async_apply_pasted_coordinates(
                    self.hass, paste, self._prefill, suggest_name=False
                )
                if not ok:
                    errors[CONF_COORDINATES_PASTE] = "invalid_coordinates"
                else:
                    return self.async_show_form(
                        step_id="location", data_schema=self._location_schema(), errors=errors
                    )
            else:
                # Flatten the LocationSelector dict into CONF_LATITUDE/CONF_LONGITUDE
                # — __init__.py reads those flat keys off entry.options, not a
                # nested "location" dict.
                location = user_input.pop(CONF_LOCATION)
                user_input.pop(CONF_COORDINATES_PASTE, None)
                user_input[CONF_LATITUDE] = location["latitude"]
                user_input[CONF_LONGITUDE] = location["longitude"]
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="location", data_schema=self._location_schema(), errors=errors
        )

    def _location_schema(self) -> vol.Schema:
        effective = {**self.config_entry.data, **self.config_entry.options}
        return vol.Schema(
            {
                vol.Optional(CONF_COORDINATES_PASTE, default=""): str,
                vol.Required(
                    CONF_LOCATION,
                    default=self._prefill.get(
                        CONF_LOCATION,
                        {
                            "latitude": effective[CONF_LATITUDE],
                            "longitude": effective[CONF_LONGITUDE],
                        },
                    ),
                ): LocationSelector(LocationSelectorConfig(radius=False)),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=effective.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)),
                vol.Required(
                    CONF_BEACH_ORIENTATION,
                    default=self._prefill.get(
                        CONF_BEACH_ORIENTATION,
                        effective.get(CONF_BEACH_ORIENTATION, DEFAULT_BEACH_ORIENTATION),
                    ),
                ): _ORIENTATION_SELECTOR,
            }
        )

    async def async_step_thresholds(self, user_input=None) -> FlowResult:
        # Global across every location — persisted in a dedicated Store, not
        # in this (or any single) entry's options, and pushed live to all
        # Bathing Conditions sensors via a dispatcher signal on save.
        if user_input is not None:
            await async_save_thresholds(self.hass, user_input)
            async_dispatcher_send(self.hass, SIGNAL_THRESHOLDS_UPDATED)
            return self.async_create_entry(title="", data=self.config_entry.options)

        current = self.hass.data.get(DOMAIN, {}).get("thresholds", DEFAULT_THRESHOLDS)
        schema = vol.Schema(
            {
                vol.Required(key, default=current[key]): NumberSelector(
                    NumberSelectorConfig(
                        min=min_, max=max_, step=step, mode=NumberSelectorMode.SLIDER
                    )
                )
                for key, (min_, max_, step) in THRESHOLD_RANGES.items()
            }
        )
        return self.async_show_form(step_id="thresholds", data_schema=schema)

    async def async_step_surf_weights(self, user_input=None) -> FlowResult:
        # Same global-across-locations pattern as thresholds: own Store,
        # pushed live via a dispatcher signal instead of entry.options. The
        # weights don't need to add up to 100 — calculate_surf_score()
        # normalizes by their sum.
        if user_input is not None:
            await async_save_surf_weights(self.hass, user_input)
            async_dispatcher_send(self.hass, SIGNAL_SURF_WEIGHTS_UPDATED)
            return self.async_create_entry(title="", data=self.config_entry.options)

        current = self.hass.data.get(DOMAIN, {}).get("surf_weights", DEFAULT_SURF_WEIGHTS)
        min_, max_, step = SURF_WEIGHT_RANGE
        schema = vol.Schema(
            {
                vol.Required(key, default=current[key]): NumberSelector(
                    NumberSelectorConfig(
                        min=min_, max=max_, step=step, mode=NumberSelectorMode.SLIDER
                    )
                )
                for key in DEFAULT_SURF_WEIGHTS
            }
        )
        return self.async_show_form(step_id="surf_weights", data_schema=schema)
