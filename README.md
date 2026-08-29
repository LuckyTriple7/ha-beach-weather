# Beach Weather

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/LuckyTriple7/ha-beach-weather)](https://github.com/LuckyTriple7/ha-beach-weather/releases)

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/luckytriple7)

**English** · [Deutsch](README.de.md)

Home Assistant custom integration for beach and water conditions (water temperature, waves, wind, bathing conditions), powered by the free [Open-Meteo](https://open-meteo.com/) Marine and Forecast APIs — no API key required.

## Features

- Any number of locations, each its own config entry — enter coordinates manually or pick them on a map
- Water temperature, wave height/period, wind speed/gusts/direction, plus a computed "bathing conditions" sensor
- A standard HA `weather.<slug>` entity per location with hourly + daily forecast, for the native weather card
- Matching Lovelace card, [Beach Weather Card](https://github.com/LuckyTriple7/ha-beach-weather-card) (`custom:beach-weather-card`) — freely position sensor values over a beach photo; installed separately from HACS
- All requests across every location are routed through a single shared rate limiter, so having many locations configured never bursts Open-Meteo with parallel requests (avoids HTTP 403)
- Automatic error backoff on 403/429 responses
- Fully configured through the HA UI, no YAML required
- Configurable polling interval (default 900s / 15 min, matching Open-Meteo's update cadence)

## Installation via HACS

1. Open HACS → **Integrations** → Menu (⋮) → **Custom repositories**
2. Enter URL: `https://github.com/LuckyTriple7/ha-beach-weather`
3. Category: **Integration** → **Add**
4. Search for **Beach Weather** → **Download**
5. Restart Home Assistant

## Configuration

1. **Settings → Devices & Services → Add Integration → Beach Weather**
2. Optionally fill in **Paste coordinates or search a place** with either a "lat, lon" pair (e.g. copied straight out of Google Maps) or a free-text place name (e.g. "Maspalomas beach"), then submit — this pre-fills the map, a suggested name and a suggested beach orientation below for you to review, without creating the location yet
3. Enter/confirm a name (e.g. "Platja de Muro") and the location — either type coordinates directly or pick them on the map widget
4. Optionally adjust the polling interval (min. 300s)
5. Set/confirm the **beach orientation** (° compass, seaward) — used by the Surf Score to judge whether wind/swell direction is favorable

Add the integration again for each additional location. All auto-suggestions are best-effort (Nominatim for place search/name, nearest OSM coastline segment via Overpass for the orientation) — review them before saving, especially the orientation on bays or complex coastlines.

> After updating via HACS, **restart Home Assistant** (not just reload the integration) — new translation strings (like this field's label) are only picked up on a full restart.

## Entities

One HA device per location, named after the location. Home Assistant derives the entity IDs from the device name and each entity's own name, e.g. for "Platja de Muro":

| Entity | Description |
|--------|-------------|
| `sensor.platja_de_muro_water_temperature` | Sea surface temperature (°C) |
| `sensor.platja_de_muro_wave_height` | Wave height (m) |
| `sensor.platja_de_muro_wave_direction` | Overall wave direction (°) |
| `sensor.platja_de_muro_wave_period` | Wave period (s) |
| `sensor.platja_de_muro_swell_height` | Swell wave height (m) — surf-relevant, separate from local wind chop |
| `sensor.platja_de_muro_swell_direction` | Swell wave direction (°) |
| `sensor.platja_de_muro_swell_period` | Swell period (s) — surf-quality signal, distinct from the mixed wave period; used by the Surf Score |
| `sensor.platja_de_muro_wind_wave_height` | Wind-wave height (m) — local wind-driven chop, separate from swell |
| `sensor.platja_de_muro_wind_wave_direction` | Wind-wave direction (°) |
| `sensor.platja_de_muro_wind_wave_period` | Wind-wave period (s) |
| `sensor.platja_de_muro_ocean_current_velocity` | Ocean current velocity (km/h) |
| `sensor.platja_de_muro_ocean_current_direction` | Ocean current direction (°) |
| `sensor.platja_de_muro_timestamp` | Timestamp of the marine data |
| `sensor.platja_de_muro_wind_speed` | Wind speed (km/h) |
| `sensor.platja_de_muro_wind_gusts` | Wind gusts (km/h) |
| `sensor.platja_de_muro_wind_direction` | Wind direction (°) |
| `sensor.platja_de_muro_air_temperature` | Air temperature at 2m (°C) |
| `sensor.platja_de_muro_humidity` | Relative humidity (%) |
| `sensor.platja_de_muro_precipitation` | Precipitation, current interval (mm) |
| `sensor.platja_de_muro_rain` | Rain, current interval (mm) |
| `sensor.platja_de_muro_showers` | Showers, current interval (mm) |
| `sensor.platja_de_muro_pressure` | Sea-level air pressure (hPa) |
| `sensor.platja_de_muro_cloud_cover` | Cloud cover (%) |
| `sensor.platja_de_muro_uv_index` | UV index |
| `sensor.platja_de_muro_visibility` | Horizontal visibility (km) |
| `sensor.platja_de_muro_day_night` | Day/Night |
| `sensor.platja_de_muro_weather_condition` | Human-readable weather condition (from WMO weather code), with the raw code as an attribute |
| `sensor.platja_de_muro_wind_timestamp` | Timestamp of the wind/weather data |
| `sensor.platja_de_muro_bathing_conditions` | Computed bathing-conditions text/icon (no own API call) |
| `sensor.platja_de_muro_location` | Static display name of the location |
| `sensor.platja_de_muro_marine_api_status` | Last raw HTTP status code from the Marine API (diagnostic) |
| `sensor.platja_de_muro_weather_api_status` | Last raw HTTP status code from the Forecast/Wind API (diagnostic) |
| `button.platja_de_muro_update_now` | Forces an immediate refresh of both APIs for this location — bypasses the shared rate limiter and any active error backoff |
| `sensor.platja_de_muro_surf_score` | Surf quality, 0-100 |
| `sensor.platja_de_muro_surf_condition` | Surf quality as a category (No surf / Poor / Okay / Good / Very good / Perfect conditions) |
| `sensor.platja_de_muro_surf_stars` | Surf quality as star rating (★ to ★★★★★), with the numeric score and star count as attributes |
| `weather.platja_de_muro` | Standard HA weather entity — current conditions plus hourly/daily forecast |

> Locations created with 0.24.0 or earlier keep the IDs they were given back then (`sensor.water_temperature_platja_de_muro`) — the entity registry never rewrites an existing entity's ID, and neither does an update. Only locations added from 1.1.0 on use the shape above. The Lovelace card finds its entities by their registry `translation_key`, so it works with either, and with entities you have renamed yourself.

A sensor becomes `unavailable` when Open-Meteo doesn't return a value for that field, or when the request fails. The two "Last Status" sensors are the exception — they stay visible even after a failed update, showing the raw status code (e.g. `403`) so a rate-limit issue is diagnosable without digging through the log.

The 12 Marine sensors (water temperature, wave height/direction/period, swell height/direction/period, wind-wave height/direction/period, ocean current velocity/direction) each carry a `forecast` attribute — the next 48 hours as `[{"time": ..., "value": ...}, ...]`, `null` if no forecast data is available yet.

## Weather entity

`weather.<slug>` is a standard Home Assistant weather entity — works with the built-in weather card, `weather.get_forecasts`, and anything else that expects a normal `weather.*` entity. It covers only the atmospheric side (temperature, wind, pressure, humidity, cloud cover, UV index, visibility, precipitation, condition) from the Forecast API's `current`/`hourly`/`daily` blocks — wave/swell/surf data has no place in HA's weather model and stays on the dedicated sensors above. WMO weather codes are mapped to HA's standard condition strings (`sunny`/`clear-night` for codes 0-1, day/night aware; `partlycloudy`, `cloudy`, `fog`, `rainy`, `pouring`, `snowy`, `snowy-rainy`, `lightning`, `lightning-rainy` for the rest).

## Lovelace Card

The card has its own repository: **[Beach Weather Card](https://github.com/LuckyTriple7/ha-beach-weather-card)** (`custom:beach-weather-card`) — a location's sensor values freely positioned over a beach photo, dragged into place in the card editor.

![Beach Weather Card](images/beach-weather-card.webp)

Install it from HACS → **Dashboard** → **Beach Weather Card**. HACS registers the Lovelace resource itself; this integration does not write to your resource store.

### Upgrading from 0.24.0 or earlier

The card used to ship inside this integration, which registered a Lovelace resource pointing at `/beach_weather_static/beach-weather-card.js`. Version 1.0.0 removes that resource on the next start and stops serving that path.

**Install the card first, then update the integration** — that way the card is never missing:

1. Install **Beach Weather Card** from HACS → **Dashboard**. While it is not in the HACS catalogue yet: HACS → ⋮ → **Custom repositories** → URL `https://github.com/LuckyTriple7/ha-beach-weather-card`, category **Dashboard**
2. Update this integration and restart Home Assistant. The old resource is removed on that start
3. Reload the browser (Ctrl+F5 / Cmd+Shift+R)

Between steps 1 and 2 both resources exist briefly; that is harmless, the card only registers its custom element once. Doing it the other way round leaves your cards as "Custom element doesn't exist" until the card is installed — nothing breaks, but they render empty.

Existing dashboards need no changes: same card type, same config format, same entity IDs. The one thing to check is a custom `background_image` pointing at a `/beach_weather_static/...` URL — that path is gone.

## Bathing condition thresholds

The Bathing Conditions sensor's thresholds (too-cold cutoff, calm/moderate wave height, perfect/very-good water temperature, perfect wave period) are **global across all locations**, not per-location. Adjust them via **Settings → Devices & Services → Beach Weather → Configure** (on any location) → **Bathing condition thresholds** — rendered as sliders. Changes apply to every location's Bathing Conditions sensor immediately, no restart needed.

## Surf Score

`sensor.surf_score` blends six factors into a single 0-100 quality score, each scored on its own curve (not linear) and combined via **global, user-adjustable weights** (Settings → Devices & Services → Beach Weather → Configure → **Surf score weighting**):

| Factor | Default weight | What's rewarded |
|--------|-----------------|------------------|
| Wave period | 30% | Uses the **swell period** (not the mixed wave period, which includes local wind chop); 10-14s ideal, very short periods score near 0 |
| Wave height | 20% | 0.8-1.5m ideal; too flat or too big scores lower |
| Swell direction | 20% | How closely swell direction matches the beach orientation |
| Wind direction | 15% | How closely wind direction matches the beach orientation |
| Wind speed | 10% | Calmer is better; 0-10 km/h ideal |
| Water temperature | 5% | 20-24°C ideal |

Weights don't need to add up to 100 — they're normalized by their sum automatically. Two bonuses (+10 each, stacking, total capped at 100): swell hits the beach head-on *and* wind blows offshore; or wave period > 10s *and* wave height > 0.8m. Direction scoring needs each location's **beach orientation** (set during setup or via Configure → Location); without it, the direction sub-scores default to comparing against 0°, which will usually be wrong for that beach.

`sensor.surf_score`'s attributes break down exactly how the number was reached: each factor's own 0-100 sub-score (`wave_period_score`, `wave_height_score`, `swell_direction_score`, `wind_direction_score`, `wind_speed_score`, `water_temperature_score`), the weights actually used, both direction diffs in degrees, which of the two bonuses fired, and the weighted average before bonuses were added.

## Diagnostics

Each location supports HA's **Download Diagnostics** (Settings → Devices & Services → Beach Weather → the location's device → ⋮ → Download Diagnostics). Includes both coordinators' last update status, HTTP status code, backoff state and raw data, plus the global bathing-condition thresholds and surf-score weights — coordinates, the location name and its slug are redacted, in the config entry and in the raw coordinator data alike.

## Error handling & backoff

If a request fails, the affected sensors go `unavailable` until the next successful update; other locations/APIs are unaffected. On HTTP 403 the coordinator backs off for 30 minutes, on 429 for 15 minutes, on 503 (Open-Meteo temporarily overloaded, a transient condition rather than a rate-limit lockout) for 30 seconds, on any other HTTP error for 5 minutes, before it even attempts another request — this protects against repeatedly hammering an already-blocking Open-Meteo endpoint. The **Update Now** button ignores this backoff and the shared rate limiter entirely: pressing it always fires an immediate request, since a deliberate manual action should not be silently swallowed by the automatic burst protection.

Each location's very first data fetch runs in the background and never blocks Home Assistant's own startup — with many locations sharing the global rate limiter, entities simply come up `unavailable` and populate once their turn in the queue comes up, usually within a minute or two.
