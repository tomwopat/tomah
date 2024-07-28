#!/usr/bin/env python
import asyncio
import logging

from homeassistant.helpers.entity import Entity

from tomah import Client
from .const import ATTR_NAME, DEFAULT_NAME, STORAGE_VERSION, STORAGE_KEY, DOMAIN, DATA_STORAGE, DATA_ACCOUNTS

# pylint: disable=W0105
"""Tomah integration"""
# pylint: enable=W0105

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry):
    _LOGGER.debug(f"setup_entry {entry.data}")
    if DOMAIN in hass.data:
        _LOGGER.info("DOMAIN data exists")
        return True
    user_id = entry.data["username"]
    hass.data[DOMAIN] = {
        DATA_STORAGE: hass.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY),
        DATA_ACCOUNTS: {},
    }

    async def async_load_oauth():
        data = await hass.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY).async_load()
        if data and user_id in data:
            _LOGGER.debug(f"loaded oauth for {user_id}: {data[user_id]}")
            return data[user_id]
        _LOGGER.debug(f"no saved oauth for {user_id}")
        return None
    #
    # def save_oauth(oauth_data):
    #     _LOGGER.debug("saving oauth")
    #     return asyncio.run_coroutine_threadsafe(async_save_oauth(oauth_data), hass.loop).result()

    async def async_save_oauth(oauth_data):
        _LOGGER.debug(f"saving oauth for {user_id}: {oauth_data}")
        data = await hass.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY).async_load()
        data[user_id] = oauth_data
        await hass.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY).async_save(data)

    client = Client(
        entry.data["client_id"],
        entry.data["domain"],
        entry.data["username"],
        entry.data["password"],
        async_load_oauth=async_load_oauth,
        async_save_oauth=async_save_oauth,
    )

    await client.async_login()
    _LOGGER.info("login complete")

    regions = await client.regions()

    _LOGGER.debug(f"regions: {regions}")
    # TODO: check account validity
    hass.data[DOMAIN][DATA_ACCOUNTS][entry.data["username"]] = client

    async def refresh_oauth_task():
        _LOGGER.debug(f"start refresh task for {client}")
        while True:
            await asyncio.sleep(60)
            await client.check_auth_refresh()

    hass.async_create_task(refresh_oauth_task())

    platforms = client.get_hass_platforms()

    # TODO: use consts
    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    return True
# class TomahAuthRefresher(DataUpdateCoordinator):
#     """Refresh access token"""
#
#     def __init__(self, hass, check_refresh_cb):
#         super().__init__(hass, _LOGGER, name=self.__class__.__name__, update_interval=timedelta(seconds=30))
#
#         self.async_check_refresh_cb = check_refresh_cb
#
#     async def _async_update_data(self):
#         _LOGGER.debug("checking auth refresh")
#         await self.async_check_refresh_cb()
#


class TomahEntity(Entity):
    pass
