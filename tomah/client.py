import logging
from urllib.parse import urljoin

import httpx
import json_api_doc

from .auth import Auth

_LOGGER = logging.getLogger(__name__)


class Client:
    ACCOUNTS_URL_PREFIX = "https://accounts."
    API_URL_PREFIX = "https://api."
    USER_AGENT_SUFFIX = "/986 CFNetwork/897.15 Darwin/17.5.0"

    def __init__(
        self,
        client_id,
        domain,
        username,
        password,
        async_load_oauth=None,
        async_save_oauth=None,
        token_renewal_pct=None,
    ):
        self.units = None

        domain_components = domain.split(".")

        self._auth_session = httpx.AsyncClient(headers={"User-Agent": domain_components[0] + self.USER_AGENT_SUFFIX})

        self._api_url_base = self.API_URL_PREFIX + domain
        self._accounts_url_base = self.ACCOUNTS_URL_PREFIX + domain
        kwargs = {}
        if token_renewal_pct is not None:
            kwargs["token_renewal_pct"] = token_renewal_pct
        self._auth = Auth(
            client_id,
            self._accounts_url_base,
            username,
            password,
            session=self._auth_session,
            async_load_oauth=async_load_oauth,
            async_save_oauth=async_save_oauth,
            **kwargs,
        )
        self._session = httpx.AsyncClient(
            headers={"User-Agent": domain_components[0] + self.USER_AGENT_SUFFIX}, auth=self._auth
        )

    async def async_login(self):
        await self._auth.async_login()
        await self.query_units()

    def get_hass_platforms(self):
        return ["button"]

    async def check_auth_refresh(self):
        """Provide callback to refresh access token if needed."""
        await self._auth.refresh_access_token_if_needed()

    # def login(self):
    #     self._oauth = self.get_oauth()
    #     print(self._oauth)

    async def query_units(self):
        me = await self.me()
        self.units = me["units"]

    def access_points(self):
        for unit in self.units:
            for access_point in unit["access_points"]:
                yield {
                    "name": access_point["name"],
                    "unit_id": unit["id"],
                    "device_id": access_point["device_id"],
                    "device_type": access_point["device_type"],
                }

    async def regions(self):
        resp = await self._session.get(urljoin(self._accounts_url_base, "api/mobile/regions"))
        _LOGGER.debug(f"regions: {resp.text}")
        return resp.json()

    async def tokens(self):
        """Deprecated."""
        resp = await self._session.get(urljoin(self._accounts_url_base, "api/v1/account/tokens"))
        print(f"tokens: {resp.text}")

    async def devices(self):
        resp = await self._session.get(urljoin(self._api_url_base, "mobile/v4/users/devices"))
        print(f"devices: {resp.text}")

    async def me(self):
        resp = await self._session.get(urljoin(self._api_url_base, "mobile/v3/me"))
        return json_api_doc.deserialize(resp.json())
        # return resp.json()

    # data[type]=door_release_requests
    # data[relationships][unit][data][id]=931502
    # data[relationships][device][data][type]=panels
    # data[relationships][device][data][id]=12064
    # data[attributes][release_method]=front_door_view

    async def door_release(self, access_point):
        if "unit_id" not in access_point or "device_id" not in access_point or "device_type" not in access_point:
            # TODO: raise exception?
            return None

        door_release_requests_payload = {
            "data[type]": "door_release_requests",
            "data[relationships][unit][data][id]": access_point["unit_id"],
            "data[relationships][device][data][type]": access_point["device_type"],
            "data[relationships][device][data][id]": access_point["device_id"],
            "data[attributes][release_method]": "front_door_view",
        }

        resp = await self._session.post(
            urljoin(self._api_url_base, "mobile/v3/door_release_requests"),
            data=door_release_requests_payload,
        )

        if resp.status_code < 200 or resp.status_code >= 300:
            _LOGGER.error(f"Failed to create door release request: {resp.text}")
            return None

        return json_api_doc.deserialize(resp.json())

    # def get_oauth(self):
    #     resp = self._session.post(
    #         urljoin(self.ACCOUNTS_URL_PREFIX, "oauth/token"),
    #         data={
    #             "client_id": self.CLIENT_ID,
    #             "grant_type": "password",
    #             "username": self.USERNAME,
    #             "password": self.PASSWORD,
    #         },
    #     )
    #     # print(resp)
    #     return resp.json()
