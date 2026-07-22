from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEGREE, UnitOfLength, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_NAME,
    CONF_SLUG,
    DOMAIN,
    KEY_BADEBEDINGUNGEN,
    KEY_STANDORT,
    KEY_WASSERTEMPERATUR,
    KEY_WELLENHOEHE,
    KEY_WINDBOEEN,
    KEY_WINDGESCHWINDIGKEIT,
    KEY_WINDRICHTUNG,
    KEY_ZEITSTEMPEL_MARINE,
    KEY_ZEITSTEMPEL_WIND,
)
from .coordinator import ForecastCoordinator, MarineCoordinator


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
            WassertemperaturSensor(marine, entry),
            WellenhoeheSensor(marine, entry),
            ZeitstempelMarineSensor(marine, entry),
            WindgeschwindigkeitSensor(forecast, entry),
            WindboeenSensor(forecast, entry),
            WindrichtungSensor(forecast, entry),
            ZeitstempelWindSensor(forecast, entry),
            BadebedingungenSensor(marine, forecast, entry),
            StandortSensor(entry),
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

    def __init__(self, coordinator, entry: ConfigEntry, key: str, name: str) -> None:
        super().__init__(coordinator)
        slug = entry.data[CONF_SLUG]
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self.entity_id = f"sensor.{key}_{slug}"
        self._attr_device_info = _device_info(entry)

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None


class WassertemperaturSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: MarineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WASSERTEMPERATUR, "Wassertemperatur")

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


class WellenhoeheSensor(_BeachWeatherSensorBase):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.METERS

    def __init__(self, coordinator: MarineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WELLENHOEHE, "Wellenhöhe")

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
        return {
            "wave_period": self.coordinator.data.get("wave_period"),
            "time": self.coordinator.data.get("time"),
        }


class ZeitstempelMarineSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: MarineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_ZEITSTEMPEL_MARINE, "Zeitstempel")

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("time") is not None

    @property
    def native_value(self) -> datetime | None:
        if not self.available:
            return None
        return _parse_open_meteo_time(self.coordinator.data.get("time"))


class WindgeschwindigkeitSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.WIND_SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WINDGESCHWINDIGKEIT, "Windgeschwindigkeit")

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


class WindboeenSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.WIND_SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WINDBOEEN, "Windböen")

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("wind_gusts_10m") is not None

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return round(self.coordinator.data["wind_gusts_10m"], 1)


class WindrichtungSensor(_BeachWeatherSensorBase):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = DEGREE

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_WINDRICHTUNG, "Windrichtung")

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("wind_direction_10m") is not None

    @property
    def native_value(self) -> int | None:
        if not self.available:
            return None
        return round(self.coordinator.data["wind_direction_10m"])


class ZeitstempelWindSensor(_BeachWeatherSensorBase):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: ForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, KEY_ZEITSTEMPEL_WIND, "Zeitstempel Wind")

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("time") is not None

    @property
    def native_value(self) -> datetime | None:
        if not self.available:
            return None
        return _parse_open_meteo_time(self.coordinator.data.get("time"))


class BadebedingungenSensor(SensorEntity):
    """Purely computed from the Marine coordinator's raw values, no own API call.

    Listens to both the Marine and Forecast coordinators manually (instead of
    extending CoordinatorEntity, which only supports a single coordinator).
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        marine: MarineCoordinator,
        forecast: ForecastCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self._marine = marine
        self._forecast = forecast
        slug = entry.data[CONF_SLUG]
        self._attr_unique_id = f"{entry.entry_id}_{KEY_BADEBEDINGUNGEN}"
        self._attr_name = "Badebedingungen"
        self.entity_id = f"sensor.{KEY_BADEBEDINGUNGEN}_{slug}"
        self._attr_device_info = _device_info(entry)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._marine.async_add_listener(self._handle_update))
        self.async_on_remove(self._forecast.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    def _value(self, field: str) -> float | None:
        if not self._marine.last_update_success or not self._marine.data:
            return None
        return self._marine.data.get(field)

    @property
    def available(self) -> bool:
        return True  # falls back to "Keine Daten" text state instead of unavailable

    @property
    def native_value(self) -> str:
        wave_height = self._value("wave_height")
        water_temp = self._value("sea_surface_temperature")
        wave_period = self._value("wave_period")

        if wave_height is None or water_temp is None:
            return "⚪ Keine Daten"
        if water_temp < 18:
            return "❄️ Zu kalt"
        if wave_height < 1.0:
            if water_temp > 22 and wave_period is not None and wave_period > 8:
                return "🔥 Perfekt"
            if water_temp > 20:
                return "🟢 Sehr gut"
            return "🟢 Gut"
        if wave_height < 1.5:
            return "🟡 Mittel"
        return "🔴 Schlecht"

    @property
    def icon(self) -> str:
        wave_height = self._value("wave_height")
        if wave_height is None:
            return "mdi:help-circle"
        if wave_height < 1.0:
            return "mdi:emoticon-happy"
        if wave_height < 1.5:
            return "mdi:emoticon-neutral"
        return "mdi:emoticon-sad"

    @property
    def extra_state_attributes(self) -> dict:
        wave_height = self._value("wave_height")
        wave_period = self._value("wave_period")
        water_temp = self._value("sea_surface_temperature")
        return {
            "wellenhoehe": wave_height,
            "wellenperiode": f"{wave_period:.2f} s" if wave_period is not None else None,
            "temperatur": f"{water_temp:.1f} °C" if water_temp is not None else None,
        }


class StandortSensor(SensorEntity):
    """Static display-name sensor, kept so existing Lovelace picture-elements
    cards that reference it by entity_id keep working after migration."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:map-marker"

    def __init__(self, entry: ConfigEntry) -> None:
        slug = entry.data[CONF_SLUG]
        self._attr_unique_id = f"{entry.entry_id}_{KEY_STANDORT}"
        self._attr_name = "Standort"
        self.entity_id = f"sensor.{KEY_STANDORT}_{slug}"
        self._attr_device_info = _device_info(entry)
        self._attr_native_value = entry.data[CONF_NAME]
