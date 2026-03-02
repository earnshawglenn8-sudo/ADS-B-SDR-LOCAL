from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ADSBCoordinator

# HA changed geo base class names over time.
try:
    from homeassistant.components.geo_location import GeolocationEvent as _GeoBase  # type: ignore
except Exception:  # pragma: no cover
    from homeassistant.components.geo_location import GeoLocationEntity as _GeoBase  # type: ignore


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: ADSBCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: dict[str, ADSBAircraftGeo] = {}

    def _add_new():
        new = []
        for ac in coordinator.map_aircraft():
            if ac.hex not in entities:
                ent = ADSBAircraftGeo(coordinator, entry, ac.hex)
                entities[ac.hex] = ent
                new.append(ent)
        if new:
            async_add_entities(new)

    _add_new()

    @callback
    def _handle_update():
        _add_new()

    coordinator.async_add_listener(_handle_update)


class ADSBAircraftGeo(CoordinatorEntity[ADSBCoordinator], _GeoBase):
    _attr_should_poll = False

    def __init__(self, coordinator: ADSBCoordinator, entry: ConfigEntry, hex_code: str) -> None:
        super().__init__(coordinator)
        self._hex = hex_code
        self._attr_unique_id = f"{entry.entry_id}_geo_{hex_code}"
        self._attr_name = f"Aircraft {hex_code}"
        # some HA versions support _attr_source
        try:
            self._attr_source = DOMAIN  # type: ignore[attr-defined]
        except Exception:
            pass

    @property
    def source(self) -> str:
        return DOMAIN

    @property
    def latitude(self):
        ac = self.coordinator.get_by_hex(self._hex)
        return ac.lat if ac else None

    @property
    def longitude(self):
        ac = self.coordinator.get_by_hex(self._hex)
        return ac.lon if ac else None

    @property
    def extra_state_attributes(self):
        ac = self.coordinator.get_by_hex(self._hex)
        if not ac:
            return {}
        return {
            "hex": ac.hex,
            "flight": ac.flight,
            "alt_baro": ac.alt_baro,
            "category": ac.category,
            "type": ac.type,
            "seen": ac.seen,
            "rssi": ac.rssi,
            "military_only": self.coordinator.military_only,
        }
