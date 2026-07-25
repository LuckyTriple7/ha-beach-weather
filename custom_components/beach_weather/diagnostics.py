from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import OpenMeteoCoordinatorBase

TO_REDACT = {"latitude", "longitude"}


def _coordinator_diagnostics(coordinator: OpenMeteoCoordinatorBase | None) -> dict[str, Any] | None:
    if coordinator is None:
        return None
    return {
        "last_update_success": coordinator.last_update_success,
        "last_status_code": coordinator.last_status_code,
        "is_backing_off": coordinator.is_backing_off,
        "backoff_remaining_seconds": coordinator.backoff_remaining_seconds,
        "update_interval_seconds": (
            coordinator.update_interval.total_seconds() if coordinator.update_interval else None
        ),
        "data": coordinator.data,
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    domain_data = hass.data.get(DOMAIN, {})
    entry_data = domain_data.get(entry.entry_id, {})

    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "entry_options": async_redact_data(dict(entry.options), TO_REDACT),
        "marine_coordinator": _coordinator_diagnostics(entry_data.get("marine")),
        "forecast_coordinator": _coordinator_diagnostics(entry_data.get("forecast")),
        "global_bathing_thresholds": domain_data.get("thresholds"),
        "global_surf_weights": domain_data.get("surf_weights"),
    }
