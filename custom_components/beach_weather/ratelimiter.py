"""Global outbound-request pacing shared by every coordinator in this integration."""
from __future__ import annotations

import asyncio


class OpenMeteoRateLimiter:
    """Serializes ALL outbound Open-Meteo HTTP calls, across every config entry
    and both APIs, through a single async lock with enforced minimum spacing.

    One instance lives per HASS instance in hass.data[DOMAIN]["rate_limiter"],
    shared by every MarineCoordinator/ForecastCoordinator regardless of which
    config entry created it. Using it as `async with limiter:` for the full
    duration of a request guarantees no two requests are ever in flight
    concurrently, and a minimum gap between successive request starts.
    """

    def __init__(self, min_spacing: float) -> None:
        self._lock = asyncio.Lock()
        self._min_spacing = min_spacing
        self._last_start: float | None = None

    async def __aenter__(self) -> "OpenMeteoRateLimiter":
        await self._lock.acquire()
        loop = asyncio.get_running_loop()
        now = loop.time()
        if self._last_start is not None:
            wait = self._min_spacing - (now - self._last_start)
            if wait > 0:
                await asyncio.sleep(wait)
        self._last_start = loop.time()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        self._lock.release()
