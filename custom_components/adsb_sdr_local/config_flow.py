from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_PATH,
    CONF_LAT,
    CONF_LON,
    DEFAULT_PORT,
    DEFAULT_PATH,
)


async def _can_connect(hass: HomeAssistant, host: str, port: int, path: str) -> bool:
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
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            path = user_input.get(CONF_PATH, DEFAULT_PATH)
            lat = user_input.get(CONF_LAT)
            lon = user_input.get(CONF_LON)

            if await _can_connect(self.hass, host, port, path):
                await self.async_set_unique_id(f"{DOMAIN}_{host}_{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"ADS-B SDR Local ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_PATH: path,
                        CONF_LAT: lat,
                        CONF_LON: lon,
                    },
                )

            errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_PATH, default=DEFAULT_PATH): str,
                vol.Optional(CONF_LAT): vol.Coerce(float),
                vol.Optional(CONF_LON): vol.Coerce(float),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
