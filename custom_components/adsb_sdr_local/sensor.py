from __future__ import annotations

from dataclasses import asdict

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LocalAdsbCoordinator

SENSORS = [
    ("aircraft_count", "Aircraft Count", None),
    ("nearest_km", "Nearest Aircraft Distance", "km"),
    ("nearest_callsign", "Nearest Callsign", None),
    ("lowest_altitude_ft", "Lowest Altitude", "ft"),
]


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: LocalAdsbCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [LocalAdsbSensor(coordinator, entry, key, name, unit) for key, name, unit in SENSORS]
    )


class LocalAdsbSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: LocalAdsbCoordinator, entry, key: str, name: str, unit):
        super().__init__(coordinator)
        self.entry = entry
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        data = self.coordinator.data
        return None if data is None else getattr(data, self.key)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if data is None:
            return {}
        attrs = asdict(data)
        attrs.pop("aircraft", None)
        attrs["source_url"] = self.coordinator.url
        return attrs
