"""Best-effort location auto-suggest for the config flow: parsing a pasted
"lat, lon" string, reverse-geocoding a place name (Nominatim), and estimating
a beach's seaward orientation from the nearest OSM coastline segment
(Overpass). All of this only ever pre-fills form fields — the user reviews
and can override every value before the location is actually created."""
from __future__ import annotations

import asyncio
import logging
import math
import re

import aiohttp
import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

_COORD_PATTERN = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")

# Nominatim usage policy requires a distinguishing User-Agent and caps at
# ~1 request/sec — trivially satisfied since this only fires once per
# "add location" flow, a human-paced action, never a polling loop.
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_USER_AGENT = "beach-weather-ha-integration (https://github.com/LuckyTriple7/ha-beach-weather)"

_COASTLINE_SEARCH_RADIUS_M = 1500


def parse_pasted_coordinates(text: str) -> tuple[float, float] | None:
    """Parse a "lat, lon" string as copied straight out of Google Maps."""
    match = _COORD_PATTERN.match(text)
    if not match:
        return None
    lat, lon = float(match.group(1)), float(match.group(2))
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return lat, lon


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d_lambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def initial_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial compass bearing (0-360°) travelling from point 1 to point 2."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    d_lambda = math.radians(lon2 - lon1)
    x = math.sin(d_lambda) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(d_lambda)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


async def async_suggest_name(hass: HomeAssistant, lat: float, lon: float) -> str | None:
    """Reverse-geocode via Nominatim; prefers a beach/natural feature name,
    falls back to the nearest settlement. Returns None on any failure."""
    session = async_get_clientsession(hass)
    params = {"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 16}
    try:
        async with async_timeout.timeout(10):
            async with session.get(
                _NOMINATIM_URL, params=params, headers={"User-Agent": _USER_AGENT}
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
        _LOGGER.debug("Nominatim name suggestion failed: %s", exc)
        return None

    address = data.get("address", {})
    return (
        address.get("beach")
        or address.get("natural")
        or address.get("suburb")
        or address.get("town")
        or address.get("village")
        or address.get("city")
        or data.get("name")
    )


async def async_suggest_orientation(hass: HomeAssistant, lat: float, lon: float) -> float | None:
    """Estimate the seaward beach orientation from the nearest OSM coastline
    segment. OSM's natural=coastline convention draws the way with water on
    its right-hand side, so the seaward normal is the segment bearing +90°.
    Best-effort only — inaccurate on complex/bay coastlines. Returns None on
    any failure or if no coastline is found nearby."""
    query = (
        f"[out:json][timeout:10];"
        f'way(around:{_COASTLINE_SEARCH_RADIUS_M},{lat},{lon})["natural"="coastline"];'
        f"out geom;"
    )
    session = async_get_clientsession(hass)
    try:
        async with async_timeout.timeout(12):
            async with session.post(
                _OVERPASS_URL, data={"data": query}, headers={"User-Agent": _USER_AGENT}
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
        _LOGGER.debug("Overpass orientation suggestion failed: %s", exc)
        return None

    best_distance: float | None = None
    best_bearing: float | None = None
    for element in data.get("elements", []):
        geometry = element.get("geometry") or []
        for i in range(len(geometry) - 1):
            p1, p2 = geometry[i], geometry[i + 1]
            mid_lat = (p1["lat"] + p2["lat"]) / 2
            mid_lon = (p1["lon"] + p2["lon"]) / 2
            distance = haversine_m(lat, lon, mid_lat, mid_lon)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_bearing = initial_bearing(p1["lat"], p1["lon"], p2["lat"], p2["lon"])

    if best_bearing is None:
        return None
    return round((best_bearing + 90) % 360)
