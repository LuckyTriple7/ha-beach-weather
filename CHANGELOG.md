# Changelog

All notable changes to this project will be documented in this file.

## [0.10.1] - 2026-07-25
### Fixed
- Pasting coordinates/a place name into the new location form never worked in practice: the Name field was marked Required, and the frontend blocks submitting a form with an empty Required field before the integration's own code runs — so the paste/search never fired unless a name was also typed first, defeating the point. Name is now Optional at the schema level (still enforced server-side before an entry is actually created).

## [0.10.0] - 2026-07-25
### Added
- 8 new sensors per location, all from data already covered by the existing API calls (no extra requests): wave direction, humidity, precipitation, rain, showers, pressure, cloud cover, UV index, and day/night

## [0.9.0] - 2026-07-25
### Added
- The "Paste coordinates" field also accepts a free-text place name now (e.g. "Maspalomas beach") — forward-geocoded via Nominatim to coordinates + a suggested name, same review-before-save flow as pasting raw coordinates

## [0.8.0] - 2026-07-25
### Added
- "Paste coordinates" field when adding/editing a location: paste a "lat, lon" pair (e.g. copied from Google Maps) and submit to auto-fill the map, plus a suggested name (Nominatim reverse geocoding) and beach orientation (nearest OSM coastline segment, Overpass) — all pre-filled for review, nothing is saved until you confirm

## [0.7.0] - 2026-07-25
### Added
- Surf Score: three new sensors (`sensor.surf_score`, `sensor.surf_condition`, `sensor.surf_stars`) computing a 0-100 surf quality score from wave period/height, swell/wind direction alignment, wind speed and water temperature, weighted and combined into a category and star rating. Weights are global across all locations, adjustable via sliders in Configure → "Surf score weighting"
- New per-location "beach orientation" field (set during setup or via Configure → Location) — the reference compass direction the Surf Score uses to judge wind/swell alignment

### Fixed
- Changing coordinates via the integration's Configure dialog never actually applied — the location picker's value was saved as a nested object instead of being flattened into the fields the coordinator reads. Editing a location's coordinates now works.

## [0.6.0] - 2026-07-25
### Added
- Bathing Conditions thresholds are now configurable via sliders in the integration's Configure dialog (new "Bathing condition thresholds" menu option) — global across all locations, not per-location. Persisted in a dedicated Store and applied live to every location's sensor via a dispatcher signal, no restart needed
- Wave period is now its own sensor (`sensor.wave_period_<slug>`) instead of an attribute on the Wave Height sensor

## [0.5.0] - 2026-07-24
### Added
- "Update Now" button per location, forces an immediate refresh of both coordinators — bypasses the shared rate limiter and any active error backoff (an explicit manual action always wins over the automatic burst protection)
- Two diagnostic "Last Status" sensors per location (Marine API / Forecast API), showing the last raw HTTP status code returned by that endpoint. Unlike the other sensors, they stay visible after a failed update so a 403/429 is diagnosable without checking the log

## [0.4.0] - 2026-07-22
### Changed
- Bathing Conditions and Weather Condition are now `enum` sensors: the raw state is a stable, language-independent key (e.g. `very_good`, `clear_sky`), and the displayed label (including emoji) is translated per HA UI language via `translation_key` state translations. Automations matching on state are now unaffected by UI language; previously the raw state itself was hardcoded English text.

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
