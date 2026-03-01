import asyncio
import logging
from dataclasses import dataclass
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_PATH, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass
class AdsbSummary:
    aircraft_count: int


class LocalAdsbCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=__import__("datetime").timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        try:
            async with asyncio.timeout(10):
                host = self.entry.data[CONF_HOST]
                port = self.entry.data[CONF_PORT]
                path = self.entry.data[CONF_PATH]
                url = f"http://{host}:{port}{path}"
                resp = await self.session.get(url)
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except Exception as err:
            raise UpdateFailed(err)

        aircraft = data.get("aircraft", [])
        return AdsbSummary(aircraft_count=len(aircraft))
