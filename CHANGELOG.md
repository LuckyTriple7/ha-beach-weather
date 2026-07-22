# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-07-22
### Added
- Initial release: per-location config entries with map or manual coordinate entry
- Water temperature, wave height/period, wind speed/gusts/direction sensors via Open-Meteo Marine + Forecast APIs
- Computed bathing-conditions sensor (no own API call)
- Shared global rate limiter across all locations/APIs to avoid Open-Meteo HTTP 403
