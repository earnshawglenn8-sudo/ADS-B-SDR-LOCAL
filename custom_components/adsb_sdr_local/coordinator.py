from __future__ import annotations

import asyncio
import logging
import re
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
    CONF_MAX_RANGE_KM,
    CONF_MIN_ALT_FT,
    CONF_MIL_ONLY,
    CONF_CALLSIGN_PREFIXES,
    CONF_CALLSIGN_REGEX,
    CONF_HEX_PREFIXES,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_MAX_RANGE_KM,
    DEFAULT_MIN_ALT_FT,
    DEFAULT_MIL_ONLY,
    DEFAULT_CALLSIGN_PREFIXES,
    DEFAULT_CALLSIGN_REGEX,
    DEFAULT_HEX_PREFIXES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


@dataclass
class AdsbData:
    aircraft: list[dict[str, Any]]
    aircraft_count: int
    nearest_km: float | None
    nearest_callsign: str | None
    lowest_altitude_ft: int | None


def _split_csv(s: str) -> list[str]:
    return [p.strip().upper() for p in (s or "").split(",") if p.strip()]


def _is_military(a: dict[str, Any], prefixes: list[str], callsign_re: re.Pattern | None, hex_prefixes: list[str]) -> bool:
    cs = ((a.get("flight") or "").strip().upper())
    hx = ((a.get("hex") or "").strip().upper())

    if callsign_re and cs and callsign_re.search(cs):
        return True

    if cs:
        for p in prefixes:
            if cs.startswith(p):
                return True

    if hx and hex_prefixes:
        for hp in hex_prefixes:
            if hx.startswith(hp):
                return True

    return False


class LocalAdsbCoordinator(DataUpdateCoordinator[AdsbData]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=__import__("datetime").timedelta(seconds=self._scan_interval()),
        )

    def _scan_interval(self) -> int:
        return int(self.entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

    def _rebuild_update_interval(self) -> None:
        self.update_interval = __import__("datetime").timedelta(seconds=self._scan_interval())

    @property
    def url(self) -> str:
        host = self.entry.data[CONF_HOST]
        port = self.entry.data[CONF_PORT]
        path = self.entry.data.get(CONF_PATH)
        if not path.startswith("/"):
            path = "/" + path
        return f"http://{host}:{port}{path}"

    async def _async_update_data(self) -> AdsbData:
        # allow scan interval changes via options without restart
        self._rebuild_update_interval()

        try:
            async with asyncio.timeout(10):
                resp = await self.session.get(self.url)
                resp.raise_for_status()
                payload: dict[str, Any] = await resp.json(content_type=None)
        except Exception as err:
            raise UpdateFailed(f"Error fetching ADS-B data: {err}") from err

        aircraft_all = payload.get("aircraft", []) or []

        home_lat = self.entry.options.get(CONF_LAT)
        home_lon = self.entry.options.get(CONF_LON)

        try:
            home_lat_f = float(home_lat) if home_lat not in (None, "", " ") else None
            home_lon_f = float(home_lon) if home_lon not in (None, "", " ") else None
        except Exception:
            home_lat_f = None
            home_lon_f = None

        max_range_km = float(self.entry.options.get(CONF_MAX_RANGE_KM, DEFAULT_MAX_RANGE_KM))
        min_alt_ft = int(self.entry.options.get(CONF_MIN_ALT_FT, DEFAULT_MIN_ALT_FT))

        mil_only = bool(self.entry.options.get(CONF_MIL_ONLY, DEFAULT_MIL_ONLY))
        prefixes = _split_csv(self.entry.options.get(CONF_CALLSIGN_PREFIXES, DEFAULT_CALLSIGN_PREFIXES))
        hex_prefixes = _split_csv(self.entry.options.get(CONF_HEX_PREFIXES, DEFAULT_HEX_PREFIXES))
        callsign_regex = (self.entry.options.get(CONF_CALLSIGN_REGEX, DEFAULT_CALLSIGN_REGEX) or "").strip()
        callsign_re = None
        if callsign_regex:
            try:
                callsign_re = re.compile(callsign_regex, re.IGNORECASE)
            except re.error:
                _LOGGER.warning("Invalid callsign regex in options: %s", callsign_regex)
                callsign_re = None

        filtered: list[dict[str, Any]] = []
        nearest_km: float | None = None
        nearest_callsign: str | None = None
        lowest_alt: int | None = None

        for a in aircraft_all:
            alt = a.get("alt_baro") or a.get("alt_geom")
            alt_ok = True
            alt_int = None
            if isinstance(alt, (int, float)) and alt > 0:
                alt_int = int(alt)
                alt_ok = alt_int >= min_alt_ft
            elif min_alt_ft > 0:
                alt_ok = False

            if not alt_ok:
                continue

            if mil_only and not _is_military(a, prefixes, callsign_re, hex_prefixes):
                continue

            d = None
            if home_lat_f is not None and home_lon_f is not None:
                alat = a.get("lat")
                alon = a.get("lon")
                if isinstance(alat, (int, float)) and isinstance(alon, (int, float)):
                    d = haversine_km(home_lat_f, home_lon_f, float(alat), float(alon))
                    if d > max_range_km:
                        continue

            filtered.append(a)

            if alt_int is not None:
                if lowest_alt is None or alt_int < lowest_alt:
                    lowest_alt = alt_int

            if d is not None:
                if nearest_km is None or d < nearest_km:
                    nearest_km = d
                    cs = (a.get("flight") or "").strip()
                    nearest_callsign = cs or a.get("hex")

        return AdsbData(
            aircraft=filtered,
            aircraft_count=len(filtered),
            nearest_km=nearest_km,
            nearest_callsign=nearest_callsign,
            lowest_altitude_ft=lowest_alt,
        )
