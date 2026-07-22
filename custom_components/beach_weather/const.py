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
MARINE_CURRENT_PARAMS = "wave_height,wave_period,sea_surface_temperature"

FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_CURRENT_PARAMS = "wind_speed_10m,wind_direction_10m,wind_gusts_10m"

# Global outbound-request pacing (shared across ALL config entries/coordinators)
RATE_LIMIT_MIN_SPACING = 3.0  # seconds between the start of any two outbound requests
INITIAL_JITTER_MAX = 15.0  # seconds, stagger before an entry's first refresh

# Open-Meteo error backoff (seconds) keyed by HTTP status
ERROR_BACKOFF: dict[int, int] = {403: 1800, 429: 900}
DEFAULT_ERROR_BACKOFF = 300

# Sensor keys (used for both unique_id suffix and entity_id prefix)
KEY_WASSERTEMPERATUR = "wassertemperatur"
KEY_WELLENHOEHE = "wellenhoehe"
KEY_ZEITSTEMPEL_MARINE = "zeitstempel"
KEY_WINDGESCHWINDIGKEIT = "windgeschwindigkeit"
KEY_WINDBOEEN = "windboeen"
KEY_WINDRICHTUNG = "windrichtung"
KEY_ZEITSTEMPEL_WIND = "zeitstempel_wind"
KEY_BADEBEDINGUNGEN = "badebedingungen"
KEY_STANDORT = "standort"
