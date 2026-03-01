import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_PATH, DEFAULT_PORT, DEFAULT_PATH


async def _can_connect(hass, host, port, path):
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
        errors = {}

        if user_input is not None:
            if await _can_connect(self.hass,
                                  user_input[CONF_HOST],
                                  user_input[CONF_PORT],
                                  user_input[CONF_PATH]):
                return self.async_create_entry(title="ADS-B SDR Local", data=user_input)

            errors["base"] = "cannot_connect"

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_PATH, default=DEFAULT_PATH): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
