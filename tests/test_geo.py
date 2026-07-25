"""Tests for coordinate parsing and the Nominatim/Overpass auto-suggest helpers."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.beach_weather.geo import (
    async_search_place,
    async_suggest_name,
    async_suggest_orientation,
    haversine_m,
    initial_bearing,
    parse_pasted_coordinates,
)


class TestParsePastedCoordinates:
    def test_google_maps_format(self):
        assert parse_pasted_coordinates("27.787333069282973, -15.723408112756257") == (
            27.787333069282973,
            -15.723408112756257,
        )

    def test_no_space_after_comma(self):
        assert parse_pasted_coordinates("27.787,-15.723") == (27.787, -15.723)

    def test_surrounding_whitespace(self):
        assert parse_pasted_coordinates("  27.787, -15.723  \n") == (27.787, -15.723)

    def test_rejects_garbage(self):
        assert parse_pasted_coordinates("not coordinates") is None

    def test_rejects_out_of_range(self):
        assert parse_pasted_coordinates("200, 0") is None
        assert parse_pasted_coordinates("0, 400") is None

    def test_rejects_empty(self):
        assert parse_pasted_coordinates("") is None


class TestHaversineAndBearing:
    def test_haversine_zero_for_same_point(self):
        assert haversine_m(27.0, -15.0, 27.0, -15.0) == 0

    def test_haversine_known_distance(self):
        # Roughly 1 degree of latitude ~ 111km
        distance = haversine_m(0.0, 0.0, 1.0, 0.0)
        assert 110_000 < distance < 112_000

    def test_bearing_due_north(self):
        assert initial_bearing(0.0, 0.0, 1.0, 0.0) == pytest.approx(0, abs=0.01)

    def test_bearing_due_east(self):
        assert initial_bearing(0.0, 0.0, 0.0, 1.0) == pytest.approx(90, abs=0.01)


def _mock_response(status=200, json_data=None):
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data or {})
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


class TestAsyncSuggestName:
    async def test_prefers_beach_over_settlement(self, hass):
        session = MagicMock()
        session.get = MagicMock(
            return_value=_mock_response(
                200, {"address": {"beach": "Platja de Muro", "town": "Muro"}}
            )
        )
        with patch(
            "custom_components.beach_weather.geo.async_get_clientsession", return_value=session
        ):
            name = await async_suggest_name(hass, 39.8, 3.11)
        assert name == "Platja de Muro"

    async def test_falls_back_to_town_when_no_beach(self, hass):
        session = MagicMock()
        session.get = MagicMock(return_value=_mock_response(200, {"address": {"town": "Muro"}}))
        with patch(
            "custom_components.beach_weather.geo.async_get_clientsession", return_value=session
        ):
            name = await async_suggest_name(hass, 39.8, 3.11)
        assert name == "Muro"

    async def test_returns_none_on_http_error(self, hass):
        session = MagicMock()
        session.get = MagicMock(return_value=_mock_response(500, {}))
        with patch(
            "custom_components.beach_weather.geo.async_get_clientsession", return_value=session
        ):
            name = await async_suggest_name(hass, 39.8, 3.11)
        assert name is None


class TestAsyncSearchPlace:
    async def test_returns_lat_lon_name_from_top_result(self, hass):
        session = MagicMock()
        session.get = MagicMock(
            return_value=_mock_response(
                200,
                [
                    {
                        "lat": "27.787333",
                        "lon": "-15.723408",
                        "name": "Playa de Maspalomas",
                        "display_name": "Playa de Maspalomas, Gran Canaria, Spain",
                    }
                ],
            )
        )
        with patch(
            "custom_components.beach_weather.geo.async_get_clientsession", return_value=session
        ):
            result = await async_search_place(hass, "Maspalomas beach")
        assert result == (27.787333, -15.723408, "Playa de Maspalomas")

    async def test_falls_back_to_display_name_when_no_short_name(self, hass):
        session = MagicMock()
        session.get = MagicMock(
            return_value=_mock_response(
                200, [{"lat": "1.0", "lon": "2.0", "display_name": "Somewhere, Region, Country"}]
            )
        )
        with patch(
            "custom_components.beach_weather.geo.async_get_clientsession", return_value=session
        ):
            result = await async_search_place(hass, "somewhere")
        assert result == (1.0, 2.0, "Somewhere, Region, Country")

    async def test_returns_none_when_no_results(self, hass):
        session = MagicMock()
        session.get = MagicMock(return_value=_mock_response(200, []))
        with patch(
            "custom_components.beach_weather.geo.async_get_clientsession", return_value=session
        ):
            result = await async_search_place(hass, "nonexistent place xyz")
        assert result is None

    async def test_returns_none_on_http_error(self, hass):
        session = MagicMock()
        session.get = MagicMock(return_value=_mock_response(500, []))
        with patch(
            "custom_components.beach_weather.geo.async_get_clientsession", return_value=session
        ):
            result = await async_search_place(hass, "somewhere")
        assert result is None


class TestAsyncSuggestOrientation:
    async def test_returns_seaward_normal_of_nearest_segment(self, hass):
        # A coastline segment running due north near the query point -> the
        # OSM "water on the right" convention makes the seaward normal due east (90°).
        overpass_response = {
            "elements": [
                {
                    "geometry": [
                        {"lat": 39.80, "lon": 3.11},
                        {"lat": 39.81, "lon": 3.11},
                    ]
                }
            ]
        }
        session = MagicMock()
        session.post = MagicMock(return_value=_mock_response(200, overpass_response))
        with patch(
            "custom_components.beach_weather.geo.async_get_clientsession", return_value=session
        ):
            orientation = await async_suggest_orientation(hass, 39.805, 3.111)
        assert orientation == pytest.approx(90, abs=1)

    async def test_returns_none_when_no_coastline_found(self, hass):
        session = MagicMock()
        session.post = MagicMock(return_value=_mock_response(200, {"elements": []}))
        with patch(
            "custom_components.beach_weather.geo.async_get_clientsession", return_value=session
        ):
            orientation = await async_suggest_orientation(hass, 39.8, 3.11)
        assert orientation is None
