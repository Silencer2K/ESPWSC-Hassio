"""ESPWSClock integration."""

import logging

from homeassistant.const import CONF_HOST
from homeassistant.exceptions import ConfigEntryNotReady

from .api import API
from .const import DOMAIN

LOGGER = logging.getLogger(__name__)

PLATFORMS = ["light"]


async def async_setup_entry(hass, entry):
    api = API(host=entry.data[CONF_HOST])

    await api.async_fetch()
    if api.state is None:
        raise ConfigEntryNotReady("Failed to connect to device")

    info = dict(api=api, task=hass.loop.create_task(api.async_task()))

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = info
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    info = hass.data[DOMAIN].pop(entry.entry_id)

    info["task"].cancel()

    return unload_ok
