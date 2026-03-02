from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Aircraft:
    hex: str
    flight: str | None
    lat: float | None
    lon: float | None
    alt_baro: int | float | None
    category: str | None
    type: str | None
    seen: float | None
    rssi: float | None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # returns distance in km
    import math
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(a))


class ADSBCoordinator(DataUpdateCoordinator[dict[str, Aircraft]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.session = async_get_clientsession(hass)

        self._mil_prefixes = [
            p.strip().upper()
            for p in str(entry.data.get("mil_prefixes", "")).split(",")
            if p.strip()
        ]
        self._max_aircraft = int(entry.data.get("max_aircraft", 75))

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=int(entry.data.get("scan_interval", 10))),
        )

    @property
    def url(self) -> str:
        host = self.entry.data["host"]
        port = int(self.entry.data["port"])
        path = self.entry.data["path"]
        if not path.startswith("/"):
            path = "/" + path
        return f"http://{host}:{port}{path}"

    @property
    def use_opensky(self) -> bool:
        return bool(self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {}).get("use_opensky", False))

    def set_use_opensky(self, value: bool) -> None:
        self.hass.data.setdefault(DOMAIN, {}).setdefault(self.entry.entry_id, {})["use_opensky"] = bool(value)

    @property
    def military_only(self) -> bool:
        return bool(self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {}).get("military_only", False))

    def set_military_only(self, value: bool) -> None:
        self.hass.data.setdefault(DOMAIN, {}).setdefault(self.entry.entry_id, {})["military_only"] = bool(value)

    def _is_military(self, flight: str | None) -> bool:
        if not flight:
            return False
        f = flight.strip().upper()
        return any(f.startswith(p) for p in self._mil_prefixes)

    def _opensky_url(self) -> str:
        # OpenSky states/all (optionally bbox)
        base = "https://opensky-network.org/api/states/all"
        try:
            home_lat = float(self.entry.data.get("home_lat", 0.0))
            home_lon = float(self.entry.data.get("home_lon", 0.0))
            range_km = int(self.entry.data.get("range_km", 0))
        except Exception:
            home_lat, home_lon, range_km = 0.0, 0.0, 0

        if range_km and home_lat and home_lon:
            # rough bbox degrees
            lat_delta = range_km / 111.0
            lon_delta = range_km / (111.0 * max(0.1, __import__("math").cos(__import__("math").radians(home_lat))))
            lamin = home_lat - lat_delta
            lamax = home_lat + lat_delta
            lomin = home_lon - lon_delta
            lomax = home_lon + lon_delta
            return f"{base}?lamin={lamin}&lamax={lamax}&lomin={lomin}&lomax={lomax}"
        return base

    async def _async_update_data(self) -> dict[str, Aircraft]:
        try:
            if self.use_opensky:
                url = self._opensky_url()
                resp = await self.session.get(url, timeout=20)
                resp.raise_for_status()
                payload: dict[str, Any] = await resp.json(content_type=None)
                return self._parse_opensky(payload)

            resp = await self.session.get(self.url, timeout=10)
            resp.raise_for_status()
            payload = await resp.json(content_type=None)
            return self._parse_local(payload)
        except Exception as err:
            raise UpdateFailed(str(err)) from err

    def _parse_local(self, payload: dict[str, Any]) -> dict[str, Aircraft]:
        out: dict[str, Aircraft] = {}
        for ac in payload.get("aircraft", []) or []:
            hx = ac.get("hex")
            if not hx:
                continue
            out[hx] = Aircraft(
                hex=hx,
                flight=(ac.get("flight") or None),
                lat=ac.get("lat"),
                lon=ac.get("lon"),
                alt_baro=ac.get("alt_baro"),
                category=ac.get("category"),
                type=ac.get("type"),
                seen=ac.get("seen"),
                rssi=ac.get("rssi"),
            )
        return out

    def _parse_opensky(self, payload: dict[str, Any]) -> dict[str, Aircraft]:
        # OpenSky "states": [ [icao24, callsign, origin_country, time_position, last_contact, lon, lat, baro_altitude, on_ground, ...], ... ]
        out: dict[str, Aircraft] = {}
        states = payload.get("states") or []
        for st in states:
            try:
                hx = (st[0] or "").strip()
                if not hx:
                    continue
                callsign = (st[1] or "").strip() or None
                lon = st[5]
                lat = st[6]
                alt = st[7]
                out[hx] = Aircraft(
                    hex=hx,
                    flight=callsign,
                    lat=lat,
                    lon=lon,
                    alt_baro=alt,
                    category=None,
                    type=None,
                    seen=None,
                    rssi=None,
                )
            except Exception:
                continue
        return out

    def all_aircraft(self) -> list[Aircraft]:
        return list((self.data or {}).values())

    def filtered_aircraft(self) -> list[Aircraft]:
        aircraft = self.all_aircraft()
        if not self.military_only:
            return aircraft
        return [a for a in aircraft if self._is_military(a.flight)]

    def map_aircraft(self) -> list[Aircraft]:
        aircraft = [a for a in self.filtered_aircraft() if a.lat is not None and a.lon is not None]
        # If using OpenSky and home coords are set, sort by distance
        try:
            home_lat = float(self.entry.data.get("home_lat", 0.0))
            home_lon = float(self.entry.data.get("home_lon", 0.0))
        except Exception:
            home_lat = home_lon = 0.0

        if home_lat and home_lon:
            aircraft.sort(key=lambda a: _haversine_km(home_lat, home_lon, float(a.lat), float(a.lon)))
        return aircraft[: self._max_aircraft]

    def get_by_hex(self, hx: str) -> Aircraft | None:
        return (self.data or {}).get(hx)
