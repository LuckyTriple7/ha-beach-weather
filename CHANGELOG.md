# Changelog

All notable changes to this project will be documented in this file.

## [0.19.1] - 2026-07-27
### Changed
- Each location's first data fetch no longer blocks Home Assistant startup — with 20+ locations sharing the global rate limiter (min. 3s between any two requests), waiting for every location's first refresh before startup could finish could add minutes to boot. Entities now come up as "unavailable" and populate in the background as their turn in the queue comes up; the regular polling cycle still retries on failure the same as before

## [0.19.0] - 2026-07-27
### Added
- New `sensor.visibility` (horizontal visibility, km) — was already part of the Forecast API response but had no sensor. Also added to the `weather.<slug>` entity's `visibility` attribute

## [0.18.1] - 2026-07-27
### Fixed
- The UV Index value now auto-hides on the card at night (`sensor.is_day` = "night") instead of showing a meaningless 0 — applies wherever a UV Index sensor is placed on the card, no config needed

### Changed
- Renamed the "Automatic (weather)" background preset to "Automatic (day/night)" — it was never actually based on weather condition, only `sensor.is_day`

## [0.18.0] - 2026-07-27
### Added
- Dedicated bundled night background photo — new "Night" preset in the background dropdown, and "Automatic (weather)" now uses it instead of the sunset photo as a placeholder
- Separate "Text color (night)" setting — the card's text color now follows the location's live `sensor.is_day`, independent of which background is selected, so values stay legible against a dark night photo without manually flipping the color yourself

## [0.17.1] - 2026-07-26
### Fixed
- "Automatic (weather)" background inferred day/night from the `weather.<slug>` condition string, which HA only distinguishes for "clear-night" — a cloudy or rainy night still showed the sunny photo. Now reads `sensor.is_day` directly, which is correct regardless of weather condition
- Selecting "Eigene URL"/"Custom URL" in the background dropdown did nothing — it set `background_image` to `""`, which is also the "default photo" value, so the dropdown immediately snapped back and the URL field never appeared

## [0.17.0] - 2026-07-26
### Added
- Per-value "Y zentriert"/"Centered Y" toggle, alongside the existing X one — locks a value's y to 50% so it only moves horizontally, for the symmetric case of the X-centering toggle
- New background option "Automatisch (Wetter)"/"Automatic (weather)" — picks a bundled photo based on the location's live `weather.<slug>` condition instead of a fixed photo. Currently only distinguishes day (sunny photo) vs. `clear-night` (sunset photo as a placeholder); more conditions can get dedicated photos later by extending `AUTO_BACKGROUND_MAP`

## [0.16.2] - 2026-07-26
### Fixed
- Switching the location dropdown in the editor emptied the whole layout instead of re-applying the default — it now rebuilds the default layout against the newly selected location's entities, matching what a freshly added card gets

## [0.16.1] - 2026-07-26
### Changed
- Reworked the card's default layout (used when adding a new card, before touching the editor) to a fuller 10-value layout — location + weather icon centered on top, then air temperature, UV index, water temperature, wind speed, wave height/period, surf stars and bathing conditions — plus darker default text color and smaller font/icon size, based on a user-refined layout meant to work unchanged across many locations

## [0.16.0] - 2026-07-26
### Added
- Per-value "Zentriert"/"Centered" toggle — locks the value to horizontal center (x stays at 50%, only vertical position is draggable), handy for stacking a title and the weather below it on the same center line
- The card editor's UI text (labels, buttons, toggles) is now translated based on the HA UI language (English/German), matching the rest of the integration instead of always showing German

## [0.15.5] - 2026-07-26
### Added
- Editor's drag canvas now shows a 5% grid and snaps values to it while dragging — makes lining values up on the same row/column much easier. Hold Alt while dragging for free (unsnapped) positioning

## [0.15.4] - 2026-07-26
### Added
- Hovering a value on the card now shows its entity name as a native tooltip, even when "Name anzeigen" is off

### Fixed
- Button entities (e.g. "Update Now") no longer show up in the card's value picker — they have no state worth displaying

## [0.15.3] - 2026-07-26
### Fixed
- `manifest.json` keys weren't alphabetically sorted (Hassfest requirement), causing CI to fail on the previous release

### Added
- Configurable font size (`font_size`) and icon size (`icon_size`) for the card's values, editable in the editor's "Erweitert" section

## [0.15.2] - 2026-07-26
### Changed
- Water Temperature sensor now uses `mdi:pool-thermometer` instead of the generic device-class thermometer icon

## [0.15.1] - 2026-07-26
### Fixed
- Hassfest failed on the `http`/`frontend` dependency check the new card relies on — moved them to `after_dependencies` instead of a hard `dependencies` entry (which forced a real frontend startup, breaking the unit test harness)
- The card refused to render without a `device_id` set — that field is only needed by the editor's pickers, not by rendering itself, so hand-written YAML with just `items:` now works

### Added
- Configurable text color for the card's values (`text_color`, default white), editable via a color picker in the editor's "Erweitert" section
- Clicking a value on the card now opens that entity's more-info dialog, same as tapping any other HA entity

## [0.15.0] - 2026-07-26
### Added
- New Lovelace card (`custom:beach-weather-card`), bundled with the integration and auto-registered — no manual resource setup needed. Pick a location and drag sensor values (icon + value, name optional) freely onto a beach photo background, right in the card's visual editor. Ships with two default background photos (sunny / sunset), a custom image URL is also supported. Card width is responsive, with a configurable aspect ratio

## [0.14.0] - 2026-07-25
### Added
- Marine coordinator now also requests an hourly forecast (wave height/direction/period, swell height/direction/period, sea surface temperature). The 7 corresponding sensors each expose a `forecast` attribute — next 48 hours as `[{"time", "value"}, ...]`, filtered to future timestamps only

## [0.13.0] - 2026-07-25
### Added
- New `weather.<slug>` entity per location — standard HA weather entity (current conditions + hourly/daily forecast) for the native weather card and `weather.get_forecasts`, covering only atmospheric data from the Forecast API. Requests now also fetch `hourly`/`daily` blocks for the Forecast coordinator (Marine stays current-only)

## [0.12.0] - 2026-07-25
### Added
- New `sensor.swell_period` (swell_wave_period from the Marine API), and the Surf Score's "wave period" factor now uses it instead of the mixed `wave_period` — isolates groundswell quality from local wind chop, sharpening the score
- HA's "Download Diagnostics" is now supported per location: coordinator status, HTTP status, backoff state and raw data, plus global thresholds/surf weights (coordinates redacted)
- Entity-level test coverage: setting up a real config entry and checking actual sensor states/attributes, not just the underlying pure logic

## [0.11.0] - 2026-07-25
### Added
- `sensor.surf_score` now exposes a full breakdown as attributes: each factor's own sub-score, the weights used, both direction diffs, which bonuses fired, and the pre-bonus weighted average — the 0-100 number is no longer a black box

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
