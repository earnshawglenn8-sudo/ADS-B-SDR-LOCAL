DOMAIN = "adsb_sdr_local"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_PATH = "path"

CONF_LAT = "lat"
CONF_LON = "lon"
CONF_MAX_RANGE_KM = "max_range_km"
CONF_MIN_ALT_FT = "min_alt_ft"
CONF_MIL_ONLY = "military_only"
CONF_CALLSIGN_PREFIXES = "callsign_prefixes"
CONF_CALLSIGN_REGEX = "callsign_regex"
CONF_HEX_PREFIXES = "hex_prefixes"
CONF_STALE_SECONDS = "stale_seconds"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = 8080
DEFAULT_PATH = "/data/aircraft.json"

DEFAULT_SCAN_INTERVAL = 10
DEFAULT_MAX_RANGE_KM = 50.0
DEFAULT_MIN_ALT_FT = 0
DEFAULT_MIL_ONLY = False
DEFAULT_CALLSIGN_PREFIXES = "RCH,QID,RRR,ASY,HKY,DUKE,SHF,BAF,RAF,NATO"
DEFAULT_CALLSIGN_REGEX = ""
DEFAULT_HEX_PREFIXES = ""  # comma-separated, e.g. "43C,AE0"
DEFAULT_STALE_SECONDS = 120

PLATFORMS = ["sensor", "geo_location"]
