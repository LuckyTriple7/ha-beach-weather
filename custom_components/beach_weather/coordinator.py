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
    MARINE_API_URL,
    MARINE_CURRENT_PARAMS,
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

    @property
    def _http(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _async_update_data(self) -> dict[str, Any] | None:
        loop = asyncio.get_running_loop()
        if self._backoff_until is not None and loop.time() < self._backoff_until:
            remaining = self._backoff_until - loop.time()
            raise UpdateFailed(f"In backoff for {remaining:.0f}s after previous error")

        limiter: OpenMeteoRateLimiter = self.hass.data[DOMAIN]["rate_limiter"]
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": self.CURRENT_PARAMS,
        }

        try:
            async with limiter:
                async with async_timeout.timeout(15):
                    async with self._http.get(self.API_URL, params=params) as resp:
                        if resp.status in ERROR_BACKOFF:
                            backoff = ERROR_BACKOFF[resp.status]
                            self._backoff_until = loop.time() + backoff
                            _LOGGER.warning(
                                "[%s] Open-Meteo returned HTTP %s, backing off %ds",
                                self.name,
                                resp.status,
                                backoff,
                            )
                            raise UpdateFailed(f"HTTP {resp.status} from Open-Meteo")
                        resp.raise_for_status()
                        data = await resp.json()
        except aiohttp.ClientResponseError as exc:
            backoff = ERROR_BACKOFF.get(exc.status or 0, DEFAULT_ERROR_BACKOFF)
            self._backoff_until = loop.time() + backoff
            raise UpdateFailed(f"Open-Meteo request failed: {exc}") from exc
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise UpdateFailed(f"Error communicating with Open-Meteo: {exc}") from exc

        self._backoff_until = None
        current = data.get("current")
        if not current:
            raise UpdateFailed("Open-Meteo response missing 'current' block")
        return current

    async def async_close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


class MarineCoordinator(OpenMeteoCoordinatorBase):
    API_NAME = "marine"
    API_URL = MARINE_API_URL
    CURRENT_PARAMS = MARINE_CURRENT_PARAMS


class ForecastCoordinator(OpenMeteoCoordinatorBase):
    API_NAME = "forecast"
    API_URL = FORECAST_API_URL
    CURRENT_PARAMS = FORECAST_CURRENT_PARAMS
