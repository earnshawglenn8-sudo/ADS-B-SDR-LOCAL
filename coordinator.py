from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_PATH,
    CONF_LAT,
    CONF_LON,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Earth radius (km)
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


@dataclass
class AdsbSummary:
    aircraft_count: int
    nearest_km: float | None
    nearest_callsign: str | None
    lowest_altitude_ft: int | None


class LocalAdsbCoordinator(DataUpdateCoordinator[AdsbSummary]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=__import__("datetime").timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    @property
    def url(self) -> str:
        host = self.entry.data[CONF_HOST]
        port = self.entry.data[CONF_PORT]
        path = self.entry.data.get(CONF_PATH)
        path = self.entry.options.get(CONF_PATH, path)
        if not path.startswith("/"):
            path = "/" + path
        return f"http://{host}:{port}{path}"

    async def _async_update_data(self) -> AdsbSummary:
        try:
            async with asyncio.timeout(10):
                resp = await self.session.get(self.url)
                resp.raise_for_status()
                payload: dict[str, Any] = await resp.json(content_type=None)
        except Exception as err:
            raise UpdateFailed(f"Error fetching ADS-B data: {err}") from err

        aircraft = payload.get("aircraft", []) or []
        count = len(aircraft)

        home_lat = self.entry.options.get(CONF_LAT, self.entry.data.get(CONF_LAT))
        home_lon = self.entry.options.get(CONF_LON, self.entry.data.get(CONF_LON))

        nearest_km: float | None = None
        nearest_callsign: str | None = None
        lowest_alt: int | None = None

        for a in aircraft:
            alt = a.get("alt_baro") or a.get("alt_geom")
            if isinstance(alt, (int, float)) and alt > 0:
                alt_int = int(alt)
                if lowest_alt is None or alt_int < lowest_alt:
                    lowest_alt = alt_int

            if home_lat is not None and home_lon is not None:
                alat = a.get("lat")
                alon = a.get("lon")
                if isinstance(alat, (int, float)) and isinstance(alon, (int, float)):
                    d = haversine_km(float(home_lat), float(home_lon), float(alat), float(alon))
                    if nearest_km is None or d < nearest_km:
                        nearest_km = d
                        cs = (a.get("flight") or "").strip()
                        nearest_callsign = cs or a.get("hex")

        return AdsbSummary(
            aircraft_count=count,
            nearest_km=nearest_km,
            nearest_callsign=nearest_callsign,
            lowest_altitude_ft=lowest_alt,
        )
