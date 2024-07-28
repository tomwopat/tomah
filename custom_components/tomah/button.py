import logging

from homeassistant.components.button import ButtonEntity

from . import TomahEntity
from .const import DOMAIN, DATA_ACCOUNTS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.info(f"setup entry Button {config_entry.data}")
    client = hass.data[DOMAIN][DATA_ACCOUNTS][config_entry.data["username"]]

    if not client:
        _LOGGER.warning(f"asked to setup Button for {config_entry.data['username']} but no client found")
        return
    entities = []
    for a in client.access_points():
        _LOGGER.info(f"adding door release for {a}")
        entities.append(TomahDoorRelease(client, a))
    async_add_entities(entities)


class TomahDoorRelease(TomahEntity, ButtonEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:door"

    def __init__(self, client, access_point):
        # TODO: fetch client from hass.data or receive it here, and/or pass it to superclass?
        self._client = client
        self.access_point = access_point
        self._attr_unique_id = f"{access_point['unit_id']}_{access_point['device_id']}"
        self._attr_name = self.access_point["name"]
        _LOGGER.info("instantiating TomahDoorRelease")
        super().__init__()

    async def async_press(self):
        _LOGGER.info(f"pressing button for {self.access_point}")
        resp = await self._client.door_release(self.access_point)
        _LOGGER.debug(f"door release response: {resp}")
