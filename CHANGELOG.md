# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-07-22
### Added
- Explicit icons for Wave Height, Swell Height (mdi:waves) and Swell/Wind Direction (mdi:compass-outline) — these had no `device_class` and were falling back to HA's generic default icon

### Changed
- Entity display names are now translated via `translation_key` (German/English follow the HA UI language) while entity IDs stay fixed in English, e.g. `sensor.water_temperature_platja_de_muro` shows as "Wassertemperatur" in a German UI and "Water Temperature" in English

## [0.2.0] - 2026-07-22
### Added
- Swell height and swell direction sensors (surf-relevant, separate from wind-driven chop)
- Air temperature sensor
- Weather condition sensor (human-readable, derived from Open-Meteo's WMO weather code)

### Changed
- All entity names and entity IDs switched from German to English (e.g. `sensor.wassertemperatur_*` → `sensor.water_temperature_*`) for better HACS/international consistency. This renames every entity — existing locations will get new entity IDs after updating.

## [0.1.0] - 2026-07-22
### Added
- Initial release: per-location config entries with map or manual coordinate entry
- Water temperature, wave height/period, wind speed/gusts/direction sensors via Open-Meteo Marine + Forecast APIs
- Computed bathing-conditions sensor (no own API call)
- Shared global rate limiter across all locations/APIs to avoid Open-Meteo HTTP 403
