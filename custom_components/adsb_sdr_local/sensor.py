
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class ADSBSensor(SensorEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "ADS-B Aircraft Count"
        self._attr_unique_id = "adsb_aircraft_count"

    @property
    def state(self):
        return self.coordinator.data

async def async_setup_entry(hass, entry, async_add_entities):
    host = entry.data["host"]
    port = entry.data["port"]

    async def async_update_data():
        url = f"http://{host}:{port}/data/aircraft.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return len(data.get("aircraft", []))

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="adsb_sdr_local",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_config_entry_first_refresh()
    async_add_entities([ADSBSensor(coordinator)])
