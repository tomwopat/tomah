#!/usr/bin/env python
import logging

from homeassistant.helpers.entity import Entity

from tomah import Client
from .const import ATTR_NAME, DEFAULT_NAME, STORAGE_VERSION, STORAGE_KEY, DOMAIN, DATA_STORAGE, DATA_ACCOUNTS

"""Tomah integration"""

_LOGGER = logging.getLogger(__name__)


# def setup(hass, config):
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up is called when Home Assistant is loading our component."""

    def handle_hello(call):
        """Handle the service call."""
        name = call.data.get(ATTR_NAME, DEFAULT_NAME)

        hass.states.set("tomah.hello", name)

    _LOGGER.warning("register service")
    hass.services.register(
        DOMAIN, "hello", handle_hello
    )  # Return boolean to indicate that initialization was successful.
    return True


async def async_setup(hass, config):
    store = hass.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY)
    _LOGGER.debug("save data")
    await store.async_save({"hello": "wbar"})
    return True


async def async_setup_entry(hass, entry):
    _LOGGER.warning(f"setup_entry {entry.data}")
    if DOMAIN in hass.data:
        _LOGGER.info("DOMAIN data exists")
    else:
        hass.data[DOMAIN] = {
            DATA_STORAGE: hass.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY),
            DATA_ACCOUNTS: {},
        }
        client = Client(
            entry.data["client_id"],
            entry.data["domain"],
            entry.data["username"],
            entry.data["password"],
        )
        # TODO: check account validity
        hass.data[DOMAIN][DATA_ACCOUNTS][entry.data["username"]] = client

        platforms = client.get_platforms()

        # TODO: use consts
        await hass.config_entries.async_forward_entry_setups(entry, platforms)

        # TODO: register stuff
        return True


class TomahEntity(Entity):
    pass
