from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import (
    DOMAIN,
    DEFAULT_PORT,
    DEFAULT_PATH,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_MAX_AIRCRAFT,
    DEFAULT_MIL_PREFIXES,
    DEFAULT_USE_OPENSKY,
    DEFAULT_HOME_LAT,
    DEFAULT_HOME_LON,
    DEFAULT_RANGE_KM,
)


class ADSBConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            title = f"ADS-B SDR Local ({user_input['host']})"
            return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("host"): str,
                    vol.Required("port", default=DEFAULT_PORT): int,
                    vol.Required("path", default=DEFAULT_PATH): str,
                    vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
                    vol.Optional("max_aircraft", default=DEFAULT_MAX_AIRCRAFT): int,
                    vol.Optional("mil_prefixes", default=",".join(DEFAULT_MIL_PREFIXES)): str,

                    # OpenSky options (used when switch is ON)
                    vol.Optional("use_opensky", default=DEFAULT_USE_OPENSKY): bool,
                    vol.Optional("home_lat", default=DEFAULT_HOME_LAT): vol.Coerce(float),
                    vol.Optional("home_lon", default=DEFAULT_HOME_LON): vol.Coerce(float),
                    vol.Optional("range_km", default=DEFAULT_RANGE_KM): vol.Coerce(int),
                }
            ),
        )
