from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AdsbCountSensor(coordinator)])


class AdsbCountSensor(SensorEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "ADS-B Aircraft Count"
        self._attr_unique_id = "adsb_aircraft_count"

    @property
    def native_value(self):
        return self.coordinator.data.aircraft_count if self.coordinator.data else None

    async def async_update(self):
        await self.coordinator.async_request_refresh()
