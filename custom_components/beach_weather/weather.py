from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SLUG, DOMAIN
from .coordinator import ForecastCoordinator
from .sensor import _device_info

# WMO weather code -> HA weather condition string. Codes 0/1 (clear/mainly
# clear) are day/night-dependent, handled separately in _condition_for_code.
_WMO_TO_CONDITION: dict[int, str] = {
    2: ATTR_CONDITION_PARTLYCLOUDY,
    3: ATTR_CONDITION_CLOUDY,
    45: ATTR_CONDITION_FOG,
    48: ATTR_CONDITION_FOG,
    51: ATTR_CONDITION_RAINY,
    53: ATTR_CONDITION_RAINY,
    55: ATTR_CONDITION_POURING,
    56: ATTR_CONDITION_SNOWY_RAINY,
    57: ATTR_CONDITION_SNOWY_RAINY,
    61: ATTR_CONDITION_RAINY,
    63: ATTR_CONDITION_RAINY,
    65: ATTR_CONDITION_POURING,
    66: ATTR_CONDITION_SNOWY_RAINY,
    67: ATTR_CONDITION_SNOWY_RAINY,
    71: ATTR_CONDITION_SNOWY,
    73: ATTR_CONDITION_SNOWY,
    75: ATTR_CONDITION_SNOWY,
    77: ATTR_CONDITION_SNOWY,
    80: ATTR_CONDITION_RAINY,
    81: ATTR_CONDITION_RAINY,
    82: ATTR_CONDITION_POURING,
    85: ATTR_CONDITION_SNOWY,
    86: ATTR_CONDITION_SNOWY,
    95: ATTR_CONDITION_LIGHTNING,
    96: ATTR_CONDITION_LIGHTNING_RAINY,
    99: ATTR_CONDITION_LIGHTNING_RAINY,
}


def condition_for_wmo_code(code: int | None, *, is_day: bool = True) -> str | None:
    if code is None:
        return None
    if code in (0, 1):
        return ATTR_CONDITION_SUNNY if is_day else ATTR_CONDITION_CLEAR_NIGHT
    return _WMO_TO_CONDITION.get(code)


def _parse_forecast_time(raw: str | None) -> datetime | None:
    if not raw:
        return None
    fmt = "%Y-%m-%dT%H:%M" if "T" in raw else "%Y-%m-%d"
    try:
        return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def build_hourly_forecast(hourly: dict[str, Any]) -> list[Forecast]:
    times = hourly.get("time") or []
    forecasts: list[Forecast] = []
    for i, raw_time in enumerate(times):
        dt = _parse_forecast_time(raw_time)
        if dt is None:
            continue
        forecasts.append(
            Forecast(
                datetime=dt.isoformat(),
                condition=condition_for_wmo_code(_at(hourly, "weather_code", i)),
                native_temperature=_at(hourly, "temperature_2m", i),
                native_pressure=_at(hourly, "pressure_msl", i),
                humidity=_at(hourly, "relative_humidity_2m", i),
                native_wind_speed=_at(hourly, "wind_speed_10m", i),
                wind_bearing=_at(hourly, "wind_direction_10m", i),
                native_precipitation=_at(hourly, "precipitation", i),
                precipitation_probability=_at(hourly, "precipitation_probability", i),
                uv_index=_at(hourly, "uv_index", i),
            )
        )
    return forecasts


def build_daily_forecast(daily: dict[str, Any]) -> list[Forecast]:
    times = daily.get("time") or []
    forecasts: list[Forecast] = []
    for i, raw_time in enumerate(times):
        dt = _parse_forecast_time(raw_time)
        if dt is None:
            continue
        forecasts.append(
            Forecast(
                datetime=dt.isoformat(),
                condition=condition_for_wmo_code(_at(daily, "weather_code", i)),
                native_temperature=_at(daily, "temperature_2m_max", i),
                native_templow=_at(daily, "temperature_2m_min", i),
                native_precipitation=_at(daily, "precipitation_sum", i),
                precipitation_probability=_at(daily, "precipitation_probability_max", i),
                native_wind_speed=_at(daily, "wind_speed_10m_max", i),
                wind_bearing=_at(daily, "wind_direction_10m_dominant", i),
                uv_index=_at(daily, "uv_index_max", i),
            )
        )
    return forecasts


def _at(block: dict[str, Any], key: str, index: int) -> Any:
    values = block.get(key)
    if not values or index >= len(values):
        return None
    return values[index]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    forecast: ForecastCoordinator = hass.data[DOMAIN][entry.entry_id]["forecast"]
    async_add_entities([BeachWeatherEntity(forecast, entry)])


class BeachWeatherEntity(CoordinatorEntity, WeatherEntity):
    """Standard HA weather entity for the location's atmospheric conditions
    (Forecast API only) — separate from the beach/marine sensors, which HA's
    weather platform has no concept of (no wave/swell fields)."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        slug = entry.data[CONF_SLUG]
        self._attr_unique_id = f"{entry.entry_id}_weather"
        # Suggestion only: core treats an entity_id set here as the suggested
        # object id (entity_platform: "An entity may suggest the entity_id by
        # setting entity_id itself"), so the registry uses it when it first
        # creates the entry and its own value — including a user's rename —
        # wins on every later start. Keeps the ids the bundled card and
        # existing picture-elements cards look up by prefix.
        self.entity_id = f"weather.{slug}"
        self._attr_device_info = _device_info(entry)

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def condition(self) -> str | None:
        if not self.available:
            return None
        is_day = bool(self.coordinator.data.get("is_day", 1))
        return condition_for_wmo_code(self.coordinator.data.get("weather_code"), is_day=is_day)

    @property
    def native_temperature(self) -> float | None:
        return self.coordinator.data.get("temperature_2m") if self.available else None

    @property
    def native_pressure(self) -> float | None:
        return self.coordinator.data.get("pressure_msl") if self.available else None

    @property
    def humidity(self) -> float | None:
        return self.coordinator.data.get("relative_humidity_2m") if self.available else None

    @property
    def native_wind_speed(self) -> float | None:
        return self.coordinator.data.get("wind_speed_10m") if self.available else None

    @property
    def native_wind_gust_speed(self) -> float | None:
        return self.coordinator.data.get("wind_gusts_10m") if self.available else None

    @property
    def wind_bearing(self) -> float | None:
        return self.coordinator.data.get("wind_direction_10m") if self.available else None

    @property
    def native_precipitation(self) -> float | None:
        return self.coordinator.data.get("precipitation") if self.available else None

    @property
    def cloud_coverage(self) -> float | None:
        return self.coordinator.data.get("cloud_cover") if self.available else None

    @property
    def uv_index(self) -> float | None:
        return self.coordinator.data.get("uv_index") if self.available else None

    @property
    def native_visibility(self) -> float | None:
        if not self.available:
            return None
        visibility = self.coordinator.data.get("visibility")
        return round(visibility / 1000, 1) if visibility is not None else None

    async def async_forecast_daily(self) -> list[Forecast] | None:
        if not self.available:
            return None
        daily = self.coordinator.data.get("_daily")
        return build_daily_forecast(daily) if daily else None

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        if not self.available:
            return None
        hourly = self.coordinator.data.get("_hourly")
        return build_hourly_forecast(hourly) if hourly else None
