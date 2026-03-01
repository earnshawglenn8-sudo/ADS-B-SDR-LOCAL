from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_PATH,
    CONF_LAT,
    CONF_LON,
    CONF_MAX_RANGE_KM,
    CONF_MIN_ALT_FT,
    CONF_MIL_ONLY,
    CONF_CALLSIGN_PREFIXES,
    CONF_CALLSIGN_REGEX,
    CONF_HEX_PREFIXES,
    CONF_STALE_SECONDS,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_PATH,
    DEFAULT_MAX_RANGE_KM,
    DEFAULT_MIN_ALT_FT,
    DEFAULT_MIL_ONLY,
    DEFAULT_CALLSIGN_PREFIXES,
    DEFAULT_CALLSIGN_REGEX,
    DEFAULT_HEX_PREFIXES,
    DEFAULT_STALE_SECONDS,
    DEFAULT_SCAN_INTERVAL,
)


async def _can_connect(hass, host: str, port: int, path: str) -> bool:
    if not path.startswith("/"):
        path = "/" + path
    url = f"http://{host}:{port}{path}"
    session = async_get_clientsession(hass)
    try:
        resp = await session.get(url, timeout=10)
        resp.raise_for_status()
        await resp.json(content_type=None)
        return True
    except Exception:
        return False


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            path = user_input.get(CONF_PATH, DEFAULT_PATH)

            if await _can_connect(self.hass, host, port, path):
                await self.async_set_unique_id(f"{DOMAIN}_{host}_{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"ADS-B SDR Local ({host})",
                    data={CONF_HOST: host, CONF_PORT: port, CONF_PATH: path},
                )

            errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_PATH, default=DEFAULT_PATH): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(CONF_LAT, default=opts.get(CONF_LAT, "")): str,
                vol.Optional(CONF_LON, default=opts.get(CONF_LON, "")): str,
                vol.Optional(CONF_MAX_RANGE_KM, default=opts.get(CONF_MAX_RANGE_KM, DEFAULT_MAX_RANGE_KM)): vol.Coerce(float),
                vol.Optional(CONF_MIN_ALT_FT, default=opts.get(CONF_MIN_ALT_FT, DEFAULT_MIN_ALT_FT)): vol.Coerce(int),
                vol.Optional(CONF_MIL_ONLY, default=opts.get(CONF_MIL_ONLY, DEFAULT_MIL_ONLY)): bool,
                vol.Optional(CONF_CALLSIGN_PREFIXES, default=opts.get(CONF_CALLSIGN_PREFIXES, DEFAULT_CALLSIGN_PREFIXES)): str,
                vol.Optional(CONF_CALLSIGN_REGEX, default=opts.get(CONF_CALLSIGN_REGEX, DEFAULT_CALLSIGN_REGEX)): str,
                vol.Optional(CONF_HEX_PREFIXES, default=opts.get(CONF_HEX_PREFIXES, DEFAULT_HEX_PREFIXES)): str,
                vol.Optional(CONF_STALE_SECONDS, default=opts.get(CONF_STALE_SECONDS, DEFAULT_STALE_SECONDS)): vol.Coerce(int),
                vol.Optional(CONF_SCAN_INTERVAL, default=opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.Coerce(int),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
