from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import LocationSelector, LocationSelectorConfig
from homeassistant.util import slugify

from .const import (
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SLUG,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
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
                }
                return self.async_create_entry(title=name, data=data)

        return self.async_show_form(step_id="user", data_schema=self._schema(), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return BeachWeatherOptionsFlow()


class BeachWeatherOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
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
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
