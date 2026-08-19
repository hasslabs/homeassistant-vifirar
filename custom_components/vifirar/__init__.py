"""Vi firar - se din eventsajt som sensorer i Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_API_KEY, CONF_URL, DOMAIN, SCAN_INTERVAL_MINUTES, STATE_PATH

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


class VifirarCoordinator(DataUpdateCoordinator):
    """Pollar sajtens state-API och håller senaste svaret."""

    def __init__(self, hass: HomeAssistant, url: str, api_key: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )
        self._url = url.rstrip("/")
        self._api_key = api_key

    async def _async_update_data(self):
        session = async_get_clientsession(self.hass)
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            async with asyncio.timeout(15):
                resp = await session.get(self._url + STATE_PATH, headers=headers)
                if resp.status == 401:
                    raise ConfigEntryAuthFailed("API-nyckeln är återkallad eller fel")
                if resp.status != 200:
                    raise UpdateFailed(f"Oväntat svar {resp.status} från sajten")
                return await resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Kunde inte nå sajten: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = VifirarCoordinator(hass, entry.data[CONF_URL], entry.data[CONF_API_KEY])
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
