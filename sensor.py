from __future__ import annotations

from dataclasses import asdict

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import LocalAdsbCoordinator

SENSORS = [
    ("aircraft_count", "Aircraft Count", None),
    ("nearest_km", "Nearest Aircraft Distance", "km"),
    ("nearest_callsign", "Nearest Callsign", None),
    ("lowest_altitude_ft", "Lowest Altitude", "ft"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LocalAdsbCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [LocalAdsbSensor(coordinator, entry, key, name, unit) for key, name, unit in SENSORS]
    async_add_entities(entities)


class LocalAdsbSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LocalAdsbCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        unit: str | None,
    ):
        self.coordinator = coordinator
        self.entry = entry
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        data = self.coordinator.data
        if data is None:
            return None
        return getattr(data, self.key)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if data is None:
            return {}
        attrs = asdict(data)
        attrs["source_url"] = self.coordinator.url
        return attrs

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self) -> None:
        await self.coordinator.async_request_refresh()
