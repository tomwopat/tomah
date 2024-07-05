import logging

from homeassistant.components.button import ButtonEntity

from const import DOMAIN, DATA_ACCOUNTS
from . import TomahEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.info(f"setup entry Button {config_entry.data}")
    client = hass.data[DOMAIN][DATA_ACCOUNTS][config_entry.data["username"]]

    if not client:
        _LOGGER.warning(f"asked to setup Button for {config_entry.data['username']} but no client found")
        return
    entities = [TomahDoorRelease()]
    async_add_entities(entities)


class TomahDoorRelease(TomahEntity, ButtonEntity):
    def __init__(self):
        _LOGGER.info("instantiating TomahDoorRelease")
