# Changelog

All notable changes to this project will be documented in this file.

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
