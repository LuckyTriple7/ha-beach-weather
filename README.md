# Beach Weather

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/LuckyTriple7/ha-beach-weather)](https://github.com/LuckyTriple7/ha-beach-weather/releases)

Home Assistant custom integration for beach and water conditions (water temperature, waves, wind, bathing conditions), powered by the free [Open-Meteo](https://open-meteo.com/) Marine and Forecast APIs — no API key required.

## Features

- Any number of locations, each its own config entry — enter coordinates manually or pick them on a map
- Water temperature, wave height/period, wind speed/gusts/direction, plus a computed "bathing conditions" sensor
- A standard HA `weather.<slug>` entity per location with hourly + daily forecast, for the native weather card
- Bundled Lovelace card (`custom:beach-weather-card`) — freely position sensor values over a beach photo, no manual resource setup needed
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

One HA device per location, named after the location. All entity IDs include a slug of the location name, e.g. for "Platja de Muro":

| Entity | Description |
|--------|-------------|
| `sensor.water_temperature_platja_de_muro` | Sea surface temperature (°C) |
| `sensor.wave_height_platja_de_muro` | Wave height (m) |
| `sensor.wave_direction_platja_de_muro` | Overall wave direction (°) |
| `sensor.wave_period_platja_de_muro` | Wave period (s) |
| `sensor.swell_height_platja_de_muro` | Swell wave height (m) — surf-relevant, separate from local wind chop |
| `sensor.swell_direction_platja_de_muro` | Swell wave direction (°) |
| `sensor.swell_period_platja_de_muro` | Swell period (s) — surf-quality signal, distinct from the mixed wave period; used by the Surf Score |
| `sensor.timestamp_platja_de_muro` | Timestamp of the marine data |
| `sensor.wind_speed_platja_de_muro` | Wind speed (km/h) |
| `sensor.wind_gusts_platja_de_muro` | Wind gusts (km/h) |
| `sensor.wind_direction_platja_de_muro` | Wind direction (°) |
| `sensor.air_temperature_platja_de_muro` | Air temperature at 2m (°C) |
| `sensor.humidity_platja_de_muro` | Relative humidity (%) |
| `sensor.precipitation_platja_de_muro` | Precipitation, current interval (mm) |
| `sensor.rain_platja_de_muro` | Rain, current interval (mm) |
| `sensor.showers_platja_de_muro` | Showers, current interval (mm) |
| `sensor.pressure_platja_de_muro` | Sea-level air pressure (hPa) |
| `sensor.cloud_cover_platja_de_muro` | Cloud cover (%) |
| `sensor.uv_index_platja_de_muro` | UV index |
| `sensor.is_day_platja_de_muro` | Day/Night |
| `sensor.weather_condition_platja_de_muro` | Human-readable weather condition (from WMO weather code), with the raw code as an attribute |
| `sensor.timestamp_wind_platja_de_muro` | Timestamp of the wind/weather data |
| `sensor.bathing_conditions_platja_de_muro` | Computed bathing-conditions text/icon (no own API call) |
| `sensor.location_platja_de_muro` | Static display name, kept for compatibility with existing Lovelace cards |
| `sensor.last_status_platja_de_muro` | Last raw HTTP status code from the Marine API (diagnostic) |
| `sensor.last_status_wind_platja_de_muro` | Last raw HTTP status code from the Forecast/Wind API (diagnostic) |
| `button.update_now_platja_de_muro` | Forces an immediate refresh of both APIs for this location — bypasses the shared rate limiter and any active error backoff |
| `sensor.surf_score_platja_de_muro` | Surf quality, 0-100 |
| `sensor.surf_condition_platja_de_muro` | Surf quality as a category (No surf / Poor / Okay / Good / Very good / Perfect conditions) |
| `sensor.surf_stars_platja_de_muro` | Surf quality as star rating (★ to ★★★★★), with the numeric score and star count as attributes |
| `weather.platja_de_muro` | Standard HA weather entity — current conditions plus hourly/daily forecast |

A sensor becomes `unavailable` when Open-Meteo doesn't return a value for that field, or when the request fails. The two "Last Status" sensors are the exception — they stay visible even after a failed update, showing the raw status code (e.g. `403`) so a rate-limit issue is diagnosable without digging through the log.

The 7 Marine sensors (water temperature, wave height/direction/period, swell height/direction/period) each carry a `forecast` attribute — the next 48 hours as `[{"time": ..., "value": ...}, ...]`, `null` if no forecast data is available yet.

## Weather entity

`weather.<slug>` is a standard Home Assistant weather entity — works with the built-in weather card, `weather.get_forecasts`, and anything else that expects a normal `weather.*` entity. It covers only the atmospheric side (temperature, wind, pressure, humidity, cloud cover, UV index, precipitation, condition) from the Forecast API's `current`/`hourly`/`daily` blocks — wave/swell/surf data has no place in HA's weather model and stays on the dedicated sensors above. WMO weather codes are mapped to HA's standard condition strings (`sunny`/`clear-night` for codes 0-1, day/night aware; `partlycloudy`, `cloudy`, `fog`, `rainy`, `pouring`, `snowy`, `snowy-rainy`, `lightning`, `lightning-rainy` for the rest).

## Lovelace Card

The integration ships its own card, `custom:beach-weather-card` — it registers itself automatically after installing/updating via HACS and restarting Home Assistant, no manual "Add resource" step required.

1. Open a dashboard → **Edit Dashboard** → **Add Card** → search for **Beach Weather Card**
2. In the card editor, pick a **location** (one of your Beach Weather devices)
3. Drag the value chips directly on the preview image to position them
4. Per value: choose the sensor, toggle whether the name is shown, toggle whether the icon is shown, or remove it
5. Under **Erweitert**: pick one of the two bundled background photos (sunny / sunset) or supply your own image URL, adjust the card's aspect ratio (e.g. `16:9`, `4:3`, `1:1`) and the text color — the card's width is always responsive to the dashboard column

Example YAML:

```yaml
type: custom:beach-weather-card
device_id: 3f8a1c2b9e4d5f6a7b8c9d0e1f2a3b4c
aspect_ratio: "16:9"
background_image: ""   # "" = sunny (default), "sunset" = bundled sunset photo, or any image URL
text_color: "#ffffff"
items:
  - entity: sensor.water_temperature_platja_de_muro
    x: 12
    y: 20
    show_name: false
    show_icon: true
  - entity: sensor.wave_height_platja_de_muro
    x: 12
    y: 35
    show_name: true
    show_icon: true
```

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

Each location supports HA's **Download Diagnostics** (Settings → Devices & Services → Beach Weather → the location's device → ⋮ → Download Diagnostics). Includes both coordinators' last update status, HTTP status code, backoff state and raw data, plus the global bathing-condition thresholds and surf-score weights — coordinates are redacted.

## Error handling & backoff

If a request fails, the affected sensors go `unavailable` until the next successful update; other locations/APIs are unaffected. On HTTP 403 the coordinator backs off for 30 minutes, on 429 for 15 minutes, on other HTTP errors for 5 minutes, before it even attempts another request — this protects against repeatedly hammering an already-blocking Open-Meteo endpoint. The **Update Now** button ignores this backoff and the shared rate limiter entirely: pressing it always fires an immediate request, since a deliberate manual action should not be silently swallowed by the automatic burst protection.
