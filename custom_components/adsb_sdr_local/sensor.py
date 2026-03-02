from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ADSBCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: ADSBCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([AircraftCount(coordinator), AircraftFilteredCount(coordinator)])


class AircraftCount(CoordinatorEntity[ADSBCoordinator], SensorEntity):
    _attr_name = "ADS-B Aircraft Count"
    _attr_unique_id = "adsb_aircraft_count"
    _attr_icon = "mdi:airplane"

    @property
    def native_value(self):
        return len(self.coordinator.all_aircraft())


class AircraftFilteredCount(CoordinatorEntity[ADSBCoordinator], SensorEntity):
    _attr_name = "ADS-B Aircraft Count (Filtered)"
    _attr_unique_id = "adsb_aircraft_count_filtered"
    _attr_icon = "mdi:airplane-search"

    @property
    def native_value(self):
        return len(self.coordinator.filtered_aircraft())

    @property
    def extra_state_attributes(self):
        return {"military_only": self.coordinator.military_only}
