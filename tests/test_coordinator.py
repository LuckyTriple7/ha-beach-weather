"""Tests for the Beach Weather coordinators and shared rate limiter."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.beach_weather.const import DOMAIN
from custom_components.beach_weather.coordinator import MarineCoordinator
from custom_components.beach_weather.ratelimiter import OpenMeteoRateLimiter


def _make_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"slug": "test", "latitude": 1.0, "longitude": 2.0},
    )
    entry.add_to_hass(hass)
    return entry


def _make_coordinator(hass, entry, min_spacing=0.0):
    hass.data.setdefault(DOMAIN, {})["rate_limiter"] = OpenMeteoRateLimiter(min_spacing)
    return MarineCoordinator(hass, entry, 900)


def _mock_session():
    session = MagicMock()
    session.closed = False
    return session


def _mock_response(status=200, json_data=None):
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data or {})
    if status >= 400:
        resp.raise_for_status = MagicMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=status
            )
        )
    else:
        resp.raise_for_status = MagicMock()
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


class TestOpenMeteoCoordinatorBase:
    async def test_success_returns_current(self, hass):
        entry = _make_entry(hass)
        coordinator = _make_coordinator(hass, entry)

        session = _mock_session()
        session.get = MagicMock(
            return_value=_mock_response(200, {"current": {"wave_height": 0.5}})
        )
        coordinator._session = session

        data = await coordinator._async_update_data()
        assert data == {"wave_height": 0.5}

    async def test_403_raises_update_failed_and_sets_backoff(self, hass):
        entry = _make_entry(hass)
        coordinator = _make_coordinator(hass, entry)

        session = _mock_session()
        session.get = MagicMock(return_value=_mock_response(403))
        coordinator._session = session

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
        assert coordinator._backoff_until is not None

    async def test_backoff_skips_request_without_calling_session(self, hass):
        entry = _make_entry(hass)
        coordinator = _make_coordinator(hass, entry)
        loop = asyncio.get_running_loop()
        coordinator._backoff_until = loop.time() + 100

        session = MagicMock()
        coordinator._session = session

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
        session.get.assert_not_called()

    async def test_missing_current_raises_update_failed(self, hass):
        entry = _make_entry(hass)
        coordinator = _make_coordinator(hass, entry)

        session = _mock_session()
        session.get = MagicMock(return_value=_mock_response(200, {}))
        coordinator._session = session

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


class TestOpenMeteoRateLimiter:
    async def test_enforces_minimum_spacing(self):
        limiter = OpenMeteoRateLimiter(min_spacing=0.2)
        loop = asyncio.get_running_loop()

        async def acquire():
            async with limiter:
                return loop.time()

        t1, t2 = await asyncio.gather(acquire(), acquire())
        assert abs(t2 - t1) >= 0.19
