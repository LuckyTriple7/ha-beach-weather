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

Add the integration again for each additional location.

## Entities

One HA device per location, named after the location. All entity IDs include a slug of the location name, e.g. for "Platja de Muro":

| Entity | Description |
|--------|-------------|
| `sensor.water_temperature_platja_de_muro` | Sea surface temperature (°C) |
| `sensor.wave_height_platja_de_muro` | Wave height (m), with wave period as an attribute |
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

A sensor becomes `unavailable` when Open-Meteo doesn't return a value for that field, or when the request fails.
