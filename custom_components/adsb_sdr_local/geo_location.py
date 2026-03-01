from __future__ import annotations

from datetime import datetime, timedelta, timezone

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_STALE_SECONDS, DEFAULT_STALE_SECONDS
from .coordinator import LocalAdsbCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: LocalAdsbCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    store = hass.data[DOMAIN][entry.entry_id]["geo_entities"]

    def add_new_entities():
        entities = []
        if coordinator.data:
            for a in coordinator.data.aircraft:
                hx = (a.get("hex") or "").strip().upper()
                if not hx:
                    continue
                if hx not in store:
                    ent = AdsbAircraftEvent(coordinator, entry, hx)
                    store[hx] = ent
                    entities.append(ent)
        if entities:
            async_add_entities(entities)

    def cleanup_stale():
        stale = int(entry.options.get(CONF_STALE_SECONDS, DEFAULT_STALE_SECONDS))
        now = datetime.now(timezone.utc)
        for hx, ent in list(store.items()):
            last_seen = ent.last_seen
            if last_seen and now - last_seen > timedelta(seconds=stale):
                hass.async_create_task(ent.async_remove())
                store.pop(hx, None)

    def _handle_update():
        add_new_entities()
        cleanup_stale()

    add_new_entities()
    coordinator.async_add_listener(_handle_update)


class AdsbAircraftEvent(CoordinatorEntity, GeolocationEvent):
    _attr_should_poll = False

    def __init__(self, coordinator: LocalAdsbCoordinator, entry, hex_code: str):
        CoordinatorEntity.__init__(self, coordinator)
        self.entry = entry
        self.hex_code = hex_code.upper()
        self._attr_unique_id = f"{entry.entry_id}_aircraft_{self.hex_code}"
        self._attr_name = f"ADS-B {self.hex_code}"
        self._attr_source = DOMAIN
        self.last_seen: datetime | None = None

    def _get_aircraft(self):
        data = self.coordinator.data
        if not data:
            return None
        for a in data.aircraft:
            if (a.get("hex") or "").strip().upper() == self.hex_code:
                return a
        return None

    @property
    def latitude(self):
        a = self._get_aircraft()
        if a and isinstance(a.get("lat"), (int, float)):
            return float(a["lat"])
        return None

    @property
    def longitude(self):
        a = self._get_aircraft()
        if a and isinstance(a.get("lon"), (int, float)):
            return float(a["lon"])
        return None

    @property
    def extra_state_attributes(self):
        a = self._get_aircraft() or {}
        seen = a.get("seen")
        if isinstance(seen, (int, float)):
            self.last_seen = datetime.now(timezone.utc) - timedelta(seconds=float(seen))

        cs = (a.get("flight") or "").strip()
        return {
            "hex": a.get("hex"),
            "callsign": cs or None,
            "alt_baro": a.get("alt_baro"),
            "alt_geom": a.get("alt_geom"),
            "gs": a.get("gs"),
            "track": a.get("track"),
            "squawk": a.get("squawk"),
            "rssi": a.get("rssi"),
            "seen": a.get("seen"),
        }
