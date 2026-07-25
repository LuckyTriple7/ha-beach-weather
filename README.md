# Beach Weather

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/LuckyTriple7/ha-beach-weather)](https://github.com/LuckyTriple7/ha-beach-weather/releases)

Home Assistant custom integration for beach and water conditions (water temperature, waves, wind, bathing conditions), powered by the free [Open-Meteo](https://open-meteo.com/) Marine and Forecast APIs — no API key required.

## Features

- Any number of locations, each its own config entry — enter coordinates manually or pick them on a map
- Water temperature, wave height/period, wind speed/gusts/direction, plus a computed "bathing conditions" sensor
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
2. Enter a name (e.g. "Platja de Muro") and the location — either type coordinates directly or pick them on the map widget
3. Optionally adjust the polling interval (min. 300s)
4. Set the **beach orientation** (° compass, seaward) — used by the Surf Score to judge whether wind/swell direction is favorable

Add the integration again for each additional location.

## Entities

One HA device per location, named after the location. All entity IDs include a slug of the location name, e.g. for "Platja de Muro":

| Entity | Description |
|--------|-------------|
| `sensor.water_temperature_platja_de_muro` | Sea surface temperature (°C) |
| `sensor.wave_height_platja_de_muro` | Wave height (m) |
| `sensor.wave_period_platja_de_muro` | Wave period (s) |
| `sensor.swell_height_platja_de_muro` | Swell wave height (m) — surf-relevant, separate from local wind chop |
| `sensor.swell_direction_platja_de_muro` | Swell wave direction (°) |
| `sensor.timestamp_platja_de_muro` | Timestamp of the marine data |
| `sensor.wind_speed_platja_de_muro` | Wind speed (km/h) |
| `sensor.wind_gusts_platja_de_muro` | Wind gusts (km/h) |
| `sensor.wind_direction_platja_de_muro` | Wind direction (°) |
| `sensor.air_temperature_platja_de_muro` | Air temperature at 2m (°C) |
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

A sensor becomes `unavailable` when Open-Meteo doesn't return a value for that field, or when the request fails. The two "Last Status" sensors are the exception — they stay visible even after a failed update, showing the raw status code (e.g. `403`) so a rate-limit issue is diagnosable without digging through the log.

## Bathing condition thresholds

The Bathing Conditions sensor's thresholds (too-cold cutoff, calm/moderate wave height, perfect/very-good water temperature, perfect wave period) are **global across all locations**, not per-location. Adjust them via **Settings → Devices & Services → Beach Weather → Configure** (on any location) → **Bathing condition thresholds** — rendered as sliders. Changes apply to every location's Bathing Conditions sensor immediately, no restart needed.

## Surf Score

`sensor.surf_score` blends six factors into a single 0-100 quality score, each scored on its own curve (not linear) and combined via **global, user-adjustable weights** (Settings → Devices & Services → Beach Weather → Configure → **Surf score weighting**):

| Factor | Default weight | What's rewarded |
|--------|-----------------|------------------|
| Wave period | 30% | 10-14s ideal; very short periods (wind chop) score near 0 |
| Wave height | 20% | 0.8-1.5m ideal; too flat or too big scores lower |
| Swell direction | 20% | How closely swell direction matches the beach orientation |
| Wind direction | 15% | How closely wind direction matches the beach orientation |
| Wind speed | 10% | Calmer is better; 0-10 km/h ideal |
| Water temperature | 5% | 20-24°C ideal |

Weights don't need to add up to 100 — they're normalized by their sum automatically. Two bonuses (+10 each, stacking, total capped at 100): swell hits the beach head-on *and* wind blows offshore; or wave period > 10s *and* wave height > 0.8m. Direction scoring needs each location's **beach orientation** (set during setup or via Configure → Location); without it, the direction sub-scores default to comparing against 0°, which will usually be wrong for that beach.

## Error handling & backoff

If a request fails, the affected sensors go `unavailable` until the next successful update; other locations/APIs are unaffected. On HTTP 403 the coordinator backs off for 30 minutes, on 429 for 15 minutes, on other HTTP errors for 5 minutes, before it even attempts another request — this protects against repeatedly hammering an already-blocking Open-Meteo endpoint. The **Update Now** button ignores this backoff and the shared rate limiter entirely: pressing it always fires an immediate request, since a deliberate manual action should not be silently swallowed by the automatic burst protection.
