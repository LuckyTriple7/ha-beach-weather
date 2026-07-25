from __future__ import annotations

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
from .thresholds import async_save_surf_weights, async_save_thresholds

_ORIENTATION_SELECTOR = NumberSelector(
    NumberSelectorConfig(min=0, max=359, step=1, mode=NumberSelectorMode.SLIDER, unit_of_measurement="°")
)


class BeachWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def _schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(
                    CONF_LOCATION,
                    default={
                        "latitude": self.hass.config.latitude,
                        "longitude": self.hass.config.longitude,
                    },
                ): LocationSelector(LocationSelectorConfig(radius=False)),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)),
                vol.Required(
                    CONF_BEACH_ORIENTATION, default=DEFAULT_BEACH_ORIENTATION
                ): _ORIENTATION_SELECTOR,
            }
        )

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
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
    async def async_step_init(self, user_input=None) -> FlowResult:
        return self.async_show_menu(
            step_id="init", menu_options=["location", "thresholds", "surf_weights"]
        )

    async def async_step_location(self, user_input=None) -> FlowResult:
        if user_input is not None:
            # Flatten the LocationSelector dict into CONF_LATITUDE/CONF_LONGITUDE
            # — __init__.py reads those flat keys off entry.options, not a
            # nested "location" dict.
            location = user_input.pop(CONF_LOCATION)
            user_input[CONF_LATITUDE] = location["latitude"]
            user_input[CONF_LONGITUDE] = location["longitude"]
            return self.async_create_entry(title="", data=user_input)

        effective = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_LOCATION,
                    default={
                        "latitude": effective[CONF_LATITUDE],
                        "longitude": effective[CONF_LONGITUDE],
                    },
                ): LocationSelector(LocationSelectorConfig(radius=False)),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=effective.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)),
                vol.Required(
                    CONF_BEACH_ORIENTATION,
                    default=effective.get(CONF_BEACH_ORIENTATION, DEFAULT_BEACH_ORIENTATION),
                ): _ORIENTATION_SELECTOR,
            }
        )
        return self.async_show_form(step_id="location", data_schema=schema)

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
