from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_SLUG,
    DEFAULT_ERROR_BACKOFF,
    DOMAIN,
    ERROR_BACKOFF,
    FORECAST_API_URL,
    FORECAST_CURRENT_PARAMS,
    FORECAST_DAILY_PARAMS,
    FORECAST_HOURLY_PARAMS,
    MARINE_API_URL,
    MARINE_CURRENT_PARAMS,
    MARINE_HOURLY_PARAMS,
)
from .ratelimiter import OpenMeteoRateLimiter

_LOGGER = logging.getLogger(__name__)


class OpenMeteoCoordinatorBase(DataUpdateCoordinator[dict[str, Any] | None]):
    """Base coordinator for an Open-Meteo endpoint, routed through the shared
    integration-wide rate limiter so no combination of locations/APIs can
    burst-fire requests and trigger a 403 from Open-Meteo."""

    API_NAME: str
    API_URL: str
    CURRENT_PARAMS: str
    HOURLY_PARAMS: str | None = None
    DAILY_PARAMS: str | None = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, update_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.data[CONF_SLUG]}_{self.API_NAME}",
            update_interval=timedelta(seconds=update_interval),
        )
        self.entry = entry
        self.latitude = entry.data[CONF_LATITUDE]
        self.longitude = entry.data[CONF_LONGITUDE]
        self._session: aiohttp.ClientSession | None = None
        self._backoff_until: float | None = None
        self.last_status_code: int | None = None

    @property
    def is_backing_off(self) -> bool:
        if self._backoff_until is None:
            return False
        return asyncio.get_running_loop().time() < self._backoff_until

    @property
    def backoff_remaining_seconds(self) -> float | None:
        if not self.is_backing_off:
            return None
        return round(self._backoff_until - asyncio.get_running_loop().time())

    @property
    def _http(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _set_backoff(self, status: int) -> None:
        loop = asyncio.get_running_loop()
        backoff = ERROR_BACKOFF.get(status, DEFAULT_ERROR_BACKOFF)
        self._backoff_until = loop.time() + backoff
        _LOGGER.warning(
            "[%s] Open-Meteo returned HTTP %s, backing off %ds", self.name, status, backoff
        )

    async def _fetch_current(self) -> dict[str, Any]:
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": self.CURRENT_PARAMS,
        }
        if self.HOURLY_PARAMS:
            params["hourly"] = self.HOURLY_PARAMS
        if self.DAILY_PARAMS:
            params["daily"] = self.DAILY_PARAMS

        async with async_timeout.timeout(15):
            async with self._http.get(self.API_URL, params=params) as resp:
                self.last_status_code = resp.status
                if resp.status in ERROR_BACKOFF:
                    self._set_backoff(resp.status)
                    raise UpdateFailed(f"HTTP {resp.status} from Open-Meteo")
                resp.raise_for_status()
                data = await resp.json()

        current = data.get("current")
        if not current:
            raise UpdateFailed("Open-Meteo response missing 'current' block")

        # Stashed alongside the flat current fields (not nested) so every
        # existing sensor reading coordinator.data["some_field"] is unaffected.
        result = dict(current)
        if self.HOURLY_PARAMS:
            result["_hourly"] = data.get("hourly")
        if self.DAILY_PARAMS:
            result["_daily"] = data.get("daily")
        return result

    async def _async_update_data(self) -> dict[str, Any] | None:
        loop = asyncio.get_running_loop()
        if self._backoff_until is not None and loop.time() < self._backoff_until:
            remaining = self._backoff_until - loop.time()
            raise UpdateFailed(f"In backoff for {remaining:.0f}s after previous error")

        limiter: OpenMeteoRateLimiter = self.hass.data[DOMAIN]["rate_limiter"]
        try:
            async with limiter:
                current = await self._fetch_current()
        except aiohttp.ClientResponseError as exc:
            self._set_backoff(exc.status or 0)
            raise UpdateFailed(f"Open-Meteo request failed: {exc}") from exc
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise UpdateFailed(f"Error communicating with Open-Meteo: {exc}") from exc

        self._backoff_until = None
        return current

    async def async_force_refresh(self) -> None:
        """Fetch immediately, bypassing the shared rate limiter and any active
        error backoff. Used by the manual 'Update Now' button — an explicit
        user action always wins over the automatic burst protection."""
        try:
            current = await self._fetch_current()
        except UpdateFailed as exc:
            # _fetch_current already called _set_backoff for the ERROR_BACKOFF
            # status branch (403/429) before raising this.
            self.async_set_update_error(exc)
            return
        except aiohttp.ClientResponseError as exc:
            self._set_backoff(exc.status or 0)
            self.async_set_update_error(UpdateFailed(f"Open-Meteo request failed: {exc}"))
            return
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            self.async_set_update_error(UpdateFailed(f"Error communicating with Open-Meteo: {exc}"))
            return

        self._backoff_until = None
        self.async_set_updated_data(current)

    async def async_close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


class MarineCoordinator(OpenMeteoCoordinatorBase):
    API_NAME = "marine"
    API_URL = MARINE_API_URL
    CURRENT_PARAMS = MARINE_CURRENT_PARAMS
    HOURLY_PARAMS = MARINE_HOURLY_PARAMS


class ForecastCoordinator(OpenMeteoCoordinatorBase):
    API_NAME = "forecast"
    API_URL = FORECAST_API_URL
    CURRENT_PARAMS = FORECAST_CURRENT_PARAMS
    HOURLY_PARAMS = FORECAST_HOURLY_PARAMS
    DAILY_PARAMS = FORECAST_DAILY_PARAMS
