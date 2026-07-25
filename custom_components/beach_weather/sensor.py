from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    EntityCategory,
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BATHING_CONDITION_OPTIONS,
    CONF_BEACH_ORIENTATION,
    CONF_NAME,
    CONF_SLUG,
    DEFAULT_BEACH_ORIENTATION,
    DEFAULT_SURF_WEIGHTS,
    DEFAULT_THRESHOLDS,
    DEFAULT_WMO_CONDITION,
    DOMAIN,
    IS_DAY_OPTIONS,
    KEY_AIR_TEMPERATURE,
    KEY_BATHING_CONDITIONS,
    KEY_CALM_WAVE_MAX,
    KEY_CLOUD_COVER,
    KEY_HUMIDITY,
    KEY_IS_DAY,
    KEY_LAST_STATUS,
    KEY_LAST_STATUS_WIND,
    KEY_LOCATION,
    KEY_MODERATE_WAVE_MAX,
    KEY_PERFECT_PERIOD_MIN,
    KEY_PERFECT_TEMP_MIN,
    KEY_PRECIPITATION,
    KEY_PRESSURE,
    KEY_RAIN,
    KEY_SHOWERS,
    KEY_SURF_CONDITION,
    KEY_SURF_SCORE,
    KEY_SURF_STARS,
    KEY_SWELL_DIRECTION,
    KEY_SWELL_HEIGHT,
    KEY_TIMESTAMP_MARINE,
    KEY_TIMESTAMP_WIND,
    KEY_TOO_COLD_MAX,
    KEY_UV_INDEX,
    KEY_VERY_GOOD_TEMP_MIN,
    KEY_WATER_TEMPERATURE,
    KEY_WAVE_DIRECTION,
    KEY_WAVE_HEIGHT,
    KEY_WAVE_PERIOD,
    KEY_WEATHER_CONDITION,
    KEY_WIND_DIRECTION,
    KEY_WIND_GUSTS,
    KEY_WIND_SPEED,
    SIGNAL_SURF_WEIGHTS_UPDATED,
    SIGNAL_THRESHOLDS_UPDATED,
    SURF_CONDITION_OPTIONS,
    WMO_CONDITIONS,
)
from .coordinator import ForecastCoordinator, MarineCoordinator
from .surf import calculate_surf_score, surf_condition_for_score, surf_stars_for_score


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    marine: MarineCoordinator = data["marine"]
    forecast: ForecastCoordinator = data["forecast"]

    async_add_entities(
        [
            WaterTemperatureSensor(marine, entry),
            WaveHeightSensor(marine, entry),
            WaveDirectionSensor(marine, entry),
            WavePeriodSensor(marine, entry),
            SwellHeightSensor(marine, entry),
            SwellDirectionSensor(marine, entry),
            TimestampMarineSensor(marine, entry),
            WindSpeedSensor(forecast, entry),
            WindGustsSensor(forecast, entry),
            WindDirectionSensor(forecast, entry),
            AirTemperatureSensor(forecast, entry),
            HumiditySensor(forecast, entry),
            PrecipitationSensor(forecast, entry),
            RainSensor(forecast, entry),
            ShowersSensor(forecast, entry),
            PressureSensor(forecast, entry),
            CloudCoverSensor(forecast, entry),
            UvIndexSensor(forecast, entry),
            IsDaySensor(forecast, entry),
            WeatherConditionSensor(forecast, entry),
            TimestampWindSensor(forecast, entry),
            BathingConditionsSensor(marine, forecast, entry),
            LocationSensor(entry),
            LastStatusMarineSensor(marine, entry),
            LastStatusWindSensor(forecast, entry),
            SurfScoreSensor(marine, forecast, entry),
            SurfConditionSensor(marine, forecast, entry),
            SurfStarsSensor(marine, forecast, entry),
        ]
    )


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data[CONF_NAME],
        manufacturer="Open-Meteo",
        model="Beach Weather",
        configuration_url="https://open-meteo.com/",
    )


def _parse_open_meteo_time(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


class _BeachWeatherSensorBase(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, key: str) -> None:
        super().__init__(coordinator)
        slug = entry.data[CONF_SLUG]
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self.entity_id = f"sensor.{key}_{slug}"
        self._attr_device_info = _device_info(entry)

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None


class WaterTemperatureSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: MarineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WATER_TEMPERATURE)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("sea_surface_temperature") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["sea_surface_temperature"], 2)

    @property
    def extra_state_attributes(self) -> dict:
        if not self.available:
            return {}
        return {"time": self.coordinator.data.get("time")}


class WaveHeightSensor(_BeachWeatherSensorBase):
    _attr_icon = "mdi:waves"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.METERS

    def __init__(self, coordinator: MarineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WAVE_HEIGHT)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("wave_height") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["wave_height"], 2)

    @property
    def extra_state_attributes(self) -> dict:
        if not self.available:
            return {}
        return {"time": self.coordinator.data.get("time")}


class WaveDirectionSensor(_BeachWeatherSensorBase):
    _attr_icon = "mdi:compass-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = DEGREE

    def __init__(self, coordinator: MarineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WAVE_DIRECTION)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("wave_direction") is not None

    @property
    def native_value(self) -> int | None:
        if not self.available:
            return None
        return round(self.coordinator.data["wave_direction"])


class WavePeriodSensor(_BeachWeatherSensorBase):
    _attr_icon = "mdi:sine-wave"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, coordinator: MarineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WAVE_PERIOD)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("wave_period") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["wave_period"], 2)


class SwellHeightSensor(_BeachWeatherSensorBase):
    """Swell wave height — surf-relevant, distinct from local wind chop."""

    _attr_icon = "mdi:waves"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.METERS

    def __init__(self, coordinator: MarineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_SWELL_HEIGHT)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("swell_wave_height") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["swell_wave_height"], 2)


class SwellDirectionSensor(_BeachWeatherSensorBase):
    _attr_icon = "mdi:compass-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = DEGREE

    def __init__(self, coordinator: MarineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_SWELL_DIRECTION)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("swell_wave_direction") is not None

    @property
    def native_value(self) -> int | None:
        if not self.available:
            return None
        return round(self.coordinator.data["swell_wave_direction"])


class TimestampMarineSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: MarineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_TIMESTAMP_MARINE)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("time") is not None

    @property
    def native_value(self) -> datetime | None:
        if not self.available:
            return None
        return _parse_open_meteo_time(self.coordinator.data.get("time"))


class WindSpeedSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.WIND_SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WIND_SPEED)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("wind_speed_10m") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["wind_speed_10m"], 1)

    @property
    def extra_state_attributes(self) -> dict:
        if not self.available:
            return {}
        return {"time": self.coordinator.data.get("time")}


class WindGustsSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.WIND_SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WIND_GUSTS)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("wind_gusts_10m") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["wind_gusts_10m"], 1)


class WindDirectionSensor(_BeachWeatherSensorBase):
    _attr_icon = "mdi:compass-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = DEGREE

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WIND_DIRECTION)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("wind_direction_10m") is not None

    @property
    def native_value(self) -> int | None:
        if not self.available:
            return None
        return round(self.coordinator.data["wind_direction_10m"])


class AirTemperatureSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_AIR_TEMPERATURE)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("temperature_2m") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["temperature_2m"], 1)


class HumiditySensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_HUMIDITY)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("relative_humidity_2m") is not None

    @property
    def native_value(self) -> int | None:
        if not self.available:
            return None
        return round(self.coordinator.data["relative_humidity_2m"])


class PrecipitationSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.PRECIPITATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPrecipitationDepth.MILLIMETERS

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_PRECIPITATION)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("precipitation") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["precipitation"], 2)


class RainSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.PRECIPITATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPrecipitationDepth.MILLIMETERS

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_RAIN)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("rain") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["rain"], 2)


class ShowersSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.PRECIPITATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPrecipitationDepth.MILLIMETERS

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_SHOWERS)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("showers") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["showers"], 2)


class PressureSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPressure.HPA

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_PRESSURE)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("pressure_msl") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["pressure_msl"], 1)


class CloudCoverSensor(_BeachWeatherSensorBase):
    _attr_icon = "mdi:cloud-percent-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_CLOUD_COVER)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("cloud_cover") is not None

    @property
    def native_value(self) -> int | None:
        if not self.available:
            return None
        return round(self.coordinator.data["cloud_cover"])


class UvIndexSensor(_BeachWeatherSensorBase):
    _attr_icon = "mdi:weather-sunny-alert"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_UV_INDEX)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("uv_index") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["uv_index"], 1)


class IsDaySensor(_BeachWeatherSensorBase):
    """Day/night flag, translated to a stable enum key ("day"/"night")."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = IS_DAY_OPTIONS

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_IS_DAY)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("is_day") is not None

    @property
    def native_value(self) -> str | None:
        if not self.available:
            return None
        return "day" if self.coordinator.data["is_day"] else "night"

    @property
    def icon(self) -> str:
        if not self.available:
            return "mdi:help-circle"
        return "mdi:weather-sunny" if self.coordinator.data["is_day"] else "mdi:weather-night"


class WeatherConditionSensor(_BeachWeatherSensorBase):
    """WMO weather condition, derived from the raw weather_code.

    native_value is a stable, language-independent key (e.g. "clear_sky");
    the displayed label is translated per entity.sensor.weather_condition.state.<key>.
    """

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [key for key, _icon in WMO_CONDITIONS.values()] + [DEFAULT_WMO_CONDITION[0]]

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WEATHER_CONDITION)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("weather_code") is not None

    @property
    def _condition(self) -> tuple[str, str]:
        code = self.coordinator.data.get("weather_code")
        return WMO_CONDITIONS.get(code, DEFAULT_WMO_CONDITION)

    @property
    def native_value(self) -> str | None:
        if not self.available:
            return None
        return self._condition[0]

    @property
    def icon(self) -> str:
        if not self.available:
            return "mdi:help-circle"
        return self._condition[1]

    @property
    def extra_state_attributes(self) -> dict:
        if not self.available:
            return {}
        return {"code": self.coordinator.data.get("weather_code")}


class TimestampWindSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_TIMESTAMP_WIND)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("time") is not None

    @property
    def native_value(self) -> datetime | None:
        if not self.available:
            return None
        return _parse_open_meteo_time(self.coordinator.data.get("time"))


class BathingConditionsSensor(SensorEntity):
    """Purely computed from the Marine coordinator's raw values, no own API call.

    Listens to both the Marine and Forecast coordinators manually (instead of
    extending CoordinatorEntity, which only supports a single coordinator).

    native_value is a stable, language-independent key (e.g. "very_good");
    the displayed label (with emoji) is translated per
    entity.sensor.bathing_conditions.state.<key>.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = BATHING_CONDITION_OPTIONS

    def __init__(
        self,
        marine: MarineCoordinator,
        forecast: ForecastCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self._marine = marine
        self._forecast = forecast
        slug = entry.data[CONF_SLUG]
        self._attr_unique_id = f"{entry.entry_id}_{KEY_BATHING_CONDITIONS}"
        self._attr_translation_key = KEY_BATHING_CONDITIONS
        self.entity_id = f"sensor.{KEY_BATHING_CONDITIONS}_{slug}"
        self._attr_device_info = _device_info(entry)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._marine.async_add_listener(self._handle_update))
        self.async_on_remove(self._forecast.async_add_listener(self._handle_update))
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_THRESHOLDS_UPDATED, self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    def _value(self, field: str) -> float | None:
        if not self._marine.last_update_success or not self._marine.data:
            return None
        return self._marine.data.get(field)

    @property
    def _thresholds(self) -> dict[str, float]:
        return self.hass.data.get(DOMAIN, {}).get("thresholds", DEFAULT_THRESHOLDS)

    @property
    def available(self) -> bool:
        return True  # falls back to "No data" text state instead of unavailable

    @property
    def native_value(self) -> str:
        wave_height = self._value("wave_height")
        water_temp = self._value("sea_surface_temperature")
        wave_period = self._value("wave_period")
        t = self._thresholds

        if wave_height is None or water_temp is None:
            return "no_data"
        if water_temp < t[KEY_TOO_COLD_MAX]:
            return "too_cold"
        if wave_height < t[KEY_CALM_WAVE_MAX]:
            if (
                water_temp > t[KEY_PERFECT_TEMP_MIN]
                and wave_period is not None
                and wave_period > t[KEY_PERFECT_PERIOD_MIN]
            ):
                return "perfect"
            if water_temp > t[KEY_VERY_GOOD_TEMP_MIN]:
                return "very_good"
            return "good"
        if wave_height < t[KEY_MODERATE_WAVE_MAX]:
            return "moderate"
        return "poor"

    @property
    def icon(self) -> str:
        wave_height = self._value("wave_height")
        if wave_height is None:
            return "mdi:help-circle"
        t = self._thresholds
        if wave_height < t[KEY_CALM_WAVE_MAX]:
            return "mdi:emoticon-happy"
        if wave_height < t[KEY_MODERATE_WAVE_MAX]:
            return "mdi:emoticon-neutral"
        return "mdi:emoticon-sad"

    @property
    def extra_state_attributes(self) -> dict:
        wave_height = self._value("wave_height")
        wave_period = self._value("wave_period")
        water_temp = self._value("sea_surface_temperature")
        return {
            "wave_height": wave_height,
            "wave_period": f"{wave_period:.2f} s" if wave_period is not None else None,
            "temperature": f"{water_temp:.1f} °C" if water_temp is not None else None,
        }


class LocationSensor(SensorEntity):
    """Static display-name sensor, kept so existing Lovelace picture-elements
    cards that reference it by entity_id keep working after migration."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:map-marker"

    def __init__(self, entry: ConfigEntry) -> None:
        slug = entry.data[CONF_SLUG]
        self._attr_unique_id = f"{entry.entry_id}_{KEY_LOCATION}"
        self._attr_translation_key = KEY_LOCATION
        self.entity_id = f"sensor.{KEY_LOCATION}_{slug}"
        self._attr_device_info = _device_info(entry)
        self._attr_native_value = entry.data[CONF_NAME]


class _LastStatusSensorBase(SensorEntity):
    """Last raw HTTP status code returned by this coordinator's endpoint —
    stays visible even after a failed update, so a 403/429 is diagnosable
    straight from the entity instead of digging through the log."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: ConfigEntry, key: str) -> None:
        self._coordinator = coordinator
        slug = entry.data[CONF_SLUG]
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self.entity_id = f"sensor.{key}_{slug}"
        self._attr_device_info = _device_info(entry)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self._coordinator.last_status_code is not None

    @property
    def native_value(self) -> int | None:
        return self._coordinator.last_status_code

    @property
    def icon(self) -> str:
        status = self._coordinator.last_status_code
        if status is None:
            return "mdi:help-circle"
        return "mdi:check-circle-outline" if status < 400 else "mdi:alert-circle-outline"


class LastStatusMarineSensor(_LastStatusSensorBase):
    def __init__(self, coordinator: MarineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_LAST_STATUS)


class LastStatusWindSensor(_LastStatusSensorBase):
    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_LAST_STATUS_WIND)


class _SurfSensorBase(SensorEntity):
    """Purely computed from Marine + Forecast raw values plus the location's
    beach orientation and the global surf-score weights, no own API call.

    Listens to both coordinators manually (like BathingConditionsSensor) plus
    the surf-weights dispatcher signal, so a slider change in the Configure
    dialog updates every location's surf sensors immediately."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        marine: MarineCoordinator,
        forecast: ForecastCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        self._marine = marine
        self._forecast = forecast
        self._entry = entry
        slug = entry.data[CONF_SLUG]
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self.entity_id = f"sensor.{key}_{slug}"
        self._attr_device_info = _device_info(entry)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._marine.async_add_listener(self._handle_update))
        self.async_on_remove(self._forecast.async_add_listener(self._handle_update))
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_SURF_WEIGHTS_UPDATED, self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def _score(self) -> float | None:
        if not self._marine.last_update_success or not self._marine.data:
            return None
        if not self._forecast.last_update_success or not self._forecast.data:
            return None
        m = self._marine.data
        f = self._forecast.data
        required = (
            m.get("wave_period"),
            m.get("wave_height"),
            m.get("swell_wave_direction"),
            f.get("wind_direction_10m"),
            f.get("wind_speed_10m"),
            m.get("sea_surface_temperature"),
        )
        if any(value is None for value in required):
            return None

        weights = self.hass.data.get(DOMAIN, {}).get("surf_weights", DEFAULT_SURF_WEIGHTS)
        effective = {**self._entry.data, **self._entry.options}
        orientation = effective.get(CONF_BEACH_ORIENTATION, DEFAULT_BEACH_ORIENTATION)

        return calculate_surf_score(
            wave_period=m["wave_period"],
            wave_height=m["wave_height"],
            swell_direction=m["swell_wave_direction"],
            wind_direction=f["wind_direction_10m"],
            wind_speed=f["wind_speed_10m"],
            water_temperature=m["sea_surface_temperature"],
            beach_orientation=orientation,
            weights=weights,
        )

    @property
    def available(self) -> bool:
        return self._score is not None


class SurfScoreSensor(_SurfSensorBase):
    _attr_icon = "mdi:surfing"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, marine: MarineCoordinator, forecast: ForecastCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(marine, forecast, entry, KEY_SURF_SCORE)

    @property
    def native_value(self) -> int | None:
        score = self._score
        return round(score) if score is not None else None


class SurfConditionSensor(_SurfSensorBase):
    _attr_icon = "mdi:surfing"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = SURF_CONDITION_OPTIONS

    def __init__(
        self, marine: MarineCoordinator, forecast: ForecastCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(marine, forecast, entry, KEY_SURF_CONDITION)

    @property
    def native_value(self) -> str | None:
        score = self._score
        return surf_condition_for_score(score) if score is not None else None


class SurfStarsSensor(_SurfSensorBase):
    _attr_icon = "mdi:star"

    def __init__(
        self, marine: MarineCoordinator, forecast: ForecastCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(marine, forecast, entry, KEY_SURF_STARS)

    @property
    def native_value(self) -> str | None:
        score = self._score
        if score is None:
            return None
        return "★" * surf_stars_for_score(score)

    @property
    def extra_state_attributes(self) -> dict:
        score = self._score
        if score is None:
            return {}
        return {"stars": surf_stars_for_score(score), "score": round(score)}
