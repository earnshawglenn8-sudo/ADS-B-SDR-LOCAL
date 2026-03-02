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
    def military_only(self) -> bool:
        return bool(self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {}).get("military_only", False))

    def set_military_only(self, value: bool) -> None:
        self.hass.data.setdefault(DOMAIN, {}).setdefault(self.entry.entry_id, {})["military_only"] = bool(value)

    def _is_military(self, flight: str | None) -> bool:
        if not flight:
            return False
        f = flight.strip().upper()
        return any(f.startswith(p) for p in self._mil_prefixes)

    async def _async_update_data(self) -> dict[str, Aircraft]:
        try:
            resp = await self.session.get(self.url, timeout=10)
            resp.raise_for_status()
            payload: dict[str, Any] = await resp.json(content_type=None)
        except Exception as err:
            raise UpdateFailed(str(err)) from err

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

    def all_aircraft(self) -> list[Aircraft]:
        return list((self.data or {}).values())

    def filtered_aircraft(self) -> list[Aircraft]:
        aircraft = self.all_aircraft()
        if not self.military_only:
            return aircraft
        return [a for a in aircraft if self._is_military(a.flight)]

    def map_aircraft(self) -> list[Aircraft]:
        aircraft = [a for a in self.filtered_aircraft() if a.lat is not None and a.lon is not None]
        aircraft.sort(key=lambda a: (a.seen if a.seen is not None else 999999))
        return aircraft[: self._max_aircraft]

    def get_by_hex(self, hx: str) -> Aircraft | None:
        return (self.data or {}).get(hx)
