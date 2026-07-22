DOMAIN = "beach_weather"

CONF_NAME = "name"
CONF_SLUG = "slug"  # frozen at creation, never recomputed from a live name
CONF_LOCATION = "location"  # transient config-flow field (LocationSelector dict)
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_SCAN_INTERVAL = "scan_interval"

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

# WMO weather interpretation codes (used by the Weather Condition sensor)
WMO_CONDITIONS: dict[int, tuple[str, str]] = {
    0: ("Clear sky", "mdi:weather-sunny"),
    1: ("Mainly clear", "mdi:weather-sunny"),
    2: ("Partly cloudy", "mdi:weather-partly-cloudy"),
    3: ("Overcast", "mdi:weather-cloudy"),
    45: ("Fog", "mdi:weather-fog"),
    48: ("Depositing rime fog", "mdi:weather-fog"),
    51: ("Light drizzle", "mdi:weather-partly-rainy"),
    53: ("Moderate drizzle", "mdi:weather-rainy"),
    55: ("Dense drizzle", "mdi:weather-rainy"),
    56: ("Light freezing drizzle", "mdi:weather-snowy-rainy"),
    57: ("Dense freezing drizzle", "mdi:weather-snowy-rainy"),
    61: ("Slight rain", "mdi:weather-rainy"),
    63: ("Moderate rain", "mdi:weather-pouring"),
    65: ("Heavy rain", "mdi:weather-pouring"),
    66: ("Light freezing rain", "mdi:weather-snowy-rainy"),
    67: ("Heavy freezing rain", "mdi:weather-snowy-rainy"),
    71: ("Slight snow fall", "mdi:weather-snowy"),
    73: ("Moderate snow fall", "mdi:weather-snowy"),
    75: ("Heavy snow fall", "mdi:weather-snowy-heavy"),
    77: ("Snow grains", "mdi:weather-snowy"),
    80: ("Slight rain showers", "mdi:weather-partly-rainy"),
    81: ("Moderate rain showers", "mdi:weather-pouring"),
    82: ("Violent rain showers", "mdi:weather-pouring"),
    85: ("Slight snow showers", "mdi:weather-snowy"),
    86: ("Heavy snow showers", "mdi:weather-snowy-heavy"),
    95: ("Thunderstorm", "mdi:weather-lightning"),
    96: ("Thunderstorm with slight hail", "mdi:weather-lightning-rainy"),
    99: ("Thunderstorm with heavy hail", "mdi:weather-lightning-rainy"),
}
DEFAULT_WMO_CONDITION = ("Unknown", "mdi:help-circle")
