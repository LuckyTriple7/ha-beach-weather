DOMAIN = "beach_weather"

CONF_NAME = "name"
CONF_SLUG = "slug"  # frozen at creation, never recomputed from a live name
CONF_LOCATION = "location"  # transient config-flow field (LocationSelector dict)
CONF_COORDINATES_PASTE = "coordinates_paste"  # transient config-flow field
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_BEACH_ORIENTATION = "beach_orientation"  # ° compass, used for surf-score direction diffs

DEFAULT_BEACH_ORIENTATION = 0

DEFAULT_SCAN_INTERVAL = 900  # seconds, per API
MIN_SCAN_INTERVAL = 300
MAX_SCAN_INTERVAL = 3600

MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
MARINE_CURRENT_PARAMS = (
    "wave_height,wave_period,sea_surface_temperature,"
    "swell_wave_height,swell_wave_direction"
)

FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_CURRENT_PARAMS = (
    "wind_speed_10m,wind_direction_10m,wind_gusts_10m,"
    "temperature_2m,weather_code"
)

# Global outbound-request pacing (shared across ALL config entries/coordinators)
RATE_LIMIT_MIN_SPACING = 3.0  # seconds between the start of any two outbound requests
INITIAL_JITTER_MAX = 15.0  # seconds, stagger before an entry's first refresh

# Open-Meteo error backoff (seconds) keyed by HTTP status
ERROR_BACKOFF: dict[int, int] = {403: 1800, 429: 900}
DEFAULT_ERROR_BACKOFF = 300

# Sensor keys (used for both unique_id suffix and entity_id prefix)
KEY_WATER_TEMPERATURE = "water_temperature"
KEY_WAVE_HEIGHT = "wave_height"
KEY_WAVE_PERIOD = "wave_period"
KEY_SWELL_HEIGHT = "swell_height"
KEY_SWELL_DIRECTION = "swell_direction"
KEY_TIMESTAMP_MARINE = "timestamp"
KEY_WIND_SPEED = "wind_speed"
KEY_WIND_GUSTS = "wind_gusts"
KEY_WIND_DIRECTION = "wind_direction"
KEY_AIR_TEMPERATURE = "air_temperature"
KEY_WEATHER_CONDITION = "weather_condition"
KEY_TIMESTAMP_WIND = "timestamp_wind"
KEY_BATHING_CONDITIONS = "bathing_conditions"
KEY_LOCATION = "location"
KEY_UPDATE_NOW = "update_now"
KEY_LAST_STATUS = "last_status"
KEY_LAST_STATUS_WIND = "last_status_wind"
KEY_SURF_SCORE = "surf_score"
KEY_SURF_CONDITION = "surf_condition"
KEY_SURF_STARS = "surf_stars"

# WMO weather interpretation codes (used by the Weather Condition sensor).
# Maps each code to a (translation-key, icon) pair — the key is a stable,
# language-independent enum value; the displayed label is looked up via
# entity.sensor.weather_condition.state.<key> in strings.json/translations.
WMO_CONDITIONS: dict[int, tuple[str, str]] = {
    0: ("clear_sky", "mdi:weather-sunny"),
    1: ("mainly_clear", "mdi:weather-sunny"),
    2: ("partly_cloudy", "mdi:weather-partly-cloudy"),
    3: ("overcast", "mdi:weather-cloudy"),
    45: ("fog", "mdi:weather-fog"),
    48: ("depositing_rime_fog", "mdi:weather-fog"),
    51: ("light_drizzle", "mdi:weather-partly-rainy"),
    53: ("moderate_drizzle", "mdi:weather-rainy"),
    55: ("dense_drizzle", "mdi:weather-rainy"),
    56: ("light_freezing_drizzle", "mdi:weather-snowy-rainy"),
    57: ("dense_freezing_drizzle", "mdi:weather-snowy-rainy"),
    61: ("slight_rain", "mdi:weather-rainy"),
    63: ("moderate_rain", "mdi:weather-pouring"),
    65: ("heavy_rain", "mdi:weather-pouring"),
    66: ("light_freezing_rain", "mdi:weather-snowy-rainy"),
    67: ("heavy_freezing_rain", "mdi:weather-snowy-rainy"),
    71: ("slight_snow_fall", "mdi:weather-snowy"),
    73: ("moderate_snow_fall", "mdi:weather-snowy"),
    75: ("heavy_snow_fall", "mdi:weather-snowy-heavy"),
    77: ("snow_grains", "mdi:weather-snowy"),
    80: ("slight_rain_showers", "mdi:weather-partly-rainy"),
    81: ("moderate_rain_showers", "mdi:weather-pouring"),
    82: ("violent_rain_showers", "mdi:weather-pouring"),
    85: ("slight_snow_showers", "mdi:weather-snowy"),
    86: ("heavy_snow_showers", "mdi:weather-snowy-heavy"),
    95: ("thunderstorm", "mdi:weather-lightning"),
    96: ("thunderstorm_slight_hail", "mdi:weather-lightning-rainy"),
    99: ("thunderstorm_heavy_hail", "mdi:weather-lightning-rainy"),
}
DEFAULT_WMO_CONDITION = ("unknown", "mdi:help-circle")

# Bathing Conditions enum values — the displayed label (including emoji) is
# looked up via entity.sensor.bathing_conditions.state.<key>.
BATHING_CONDITION_OPTIONS = [
    "too_cold",
    "perfect",
    "very_good",
    "good",
    "moderate",
    "poor",
    "no_data",
]

# Bathing Conditions thresholds — global across ALL locations, editable via
# sliders in the integration's Configure dialog (Options flow "thresholds"
# step). Persisted in a dedicated Store, not tied to any single config entry.
KEY_TOO_COLD_MAX = "too_cold_max"
KEY_CALM_WAVE_MAX = "calm_wave_max"
KEY_MODERATE_WAVE_MAX = "moderate_wave_max"
KEY_PERFECT_TEMP_MIN = "perfect_temp_min"
KEY_PERFECT_PERIOD_MIN = "perfect_period_min"
KEY_VERY_GOOD_TEMP_MIN = "very_good_temp_min"

DEFAULT_THRESHOLDS: dict[str, float] = {
    KEY_TOO_COLD_MAX: 18.0,
    KEY_CALM_WAVE_MAX: 1.0,
    KEY_MODERATE_WAVE_MAX: 1.5,
    KEY_PERFECT_TEMP_MIN: 22.0,
    KEY_PERFECT_PERIOD_MIN: 8.0,
    KEY_VERY_GOOD_TEMP_MIN: 20.0,
}

# (min, max, step) per slider
THRESHOLD_RANGES: dict[str, tuple[float, float, float]] = {
    KEY_TOO_COLD_MAX: (10.0, 30.0, 0.5),
    KEY_CALM_WAVE_MAX: (0.2, 3.0, 0.1),
    KEY_MODERATE_WAVE_MAX: (0.5, 4.0, 0.1),
    KEY_PERFECT_TEMP_MIN: (15.0, 35.0, 0.5),
    KEY_PERFECT_PERIOD_MIN: (2.0, 20.0, 0.5),
    KEY_VERY_GOOD_TEMP_MIN: (15.0, 35.0, 0.5),
}

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_thresholds"
SIGNAL_THRESHOLDS_UPDATED = f"{DOMAIN}_thresholds_updated"

# Surf Score — weighted blend of wave period/height, swell/wind direction
# alignment (vs. CONF_BEACH_ORIENTATION), wind speed and water temperature.
# Weights are global across ALL locations, editable via sliders in the
# integration's Configure dialog (Options flow "surf_weights" step).
KEY_WEIGHT_WAVE_PERIOD = "weight_wave_period"
KEY_WEIGHT_WAVE_HEIGHT = "weight_wave_height"
KEY_WEIGHT_SWELL_DIRECTION = "weight_swell_direction"
KEY_WEIGHT_WIND_DIRECTION = "weight_wind_direction"
KEY_WEIGHT_WIND_SPEED = "weight_wind_speed"
KEY_WEIGHT_WATER_TEMPERATURE = "weight_water_temperature"

DEFAULT_SURF_WEIGHTS: dict[str, float] = {
    KEY_WEIGHT_WAVE_PERIOD: 30.0,
    KEY_WEIGHT_WAVE_HEIGHT: 20.0,
    KEY_WEIGHT_SWELL_DIRECTION: 20.0,
    KEY_WEIGHT_WIND_DIRECTION: 15.0,
    KEY_WEIGHT_WIND_SPEED: 10.0,
    KEY_WEIGHT_WATER_TEMPERATURE: 5.0,
}

# Same (min, max, step) slider range for every weight — they're normalized
# by their sum at calculation time, so they don't need to add up to 100.
SURF_WEIGHT_RANGE: tuple[float, float, float] = (0.0, 100.0, 1.0)

# Surf Condition enum values — the displayed label (including emoji) is
# looked up via entity.sensor.surf_condition.state.<key>.
SURF_CONDITION_OPTIONS = ["no_surf", "poor", "okay", "good", "very_good", "perfect"]

STORAGE_KEY_SURF_WEIGHTS = f"{DOMAIN}_surf_weights"
SIGNAL_SURF_WEIGHTS_UPDATED = f"{DOMAIN}_surf_weights_updated"
