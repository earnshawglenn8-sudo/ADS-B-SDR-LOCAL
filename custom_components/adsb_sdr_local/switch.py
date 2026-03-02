from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ADSBCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: ADSBCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([MilitaryOnlySwitch(coordinator), UseOpenSkySwitch(coordinator)])


class MilitaryOnlySwitch(CoordinatorEntity[ADSBCoordinator], SwitchEntity):
    _attr_name = "ADS-B Military Only"
    _attr_unique_id = "adsb_military_only"
    _attr_icon = "mdi:shield-airplane"

    @property
    def is_on(self) -> bool:
        return self.coordinator.military_only

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.set_military_only(True)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.set_military_only(False)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class UseOpenSkySwitch(CoordinatorEntity[ADSBCoordinator], SwitchEntity):
    _attr_name = "ADS-B Use Worldwide (OpenSky)"
    _attr_unique_id = "adsb_use_opensky"
    _attr_icon = "mdi:earth"

    @property
    def is_on(self) -> bool:
        return self.coordinator.use_opensky

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.set_use_opensky(True)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.set_use_opensky(False)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
