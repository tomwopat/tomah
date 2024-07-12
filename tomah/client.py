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

    def get_hass_platforms(self):
        return ["button"]

    """Provide callback to refresh access token if needed."""

    async def check_auth_refresh(self):
        await self._auth.refresh_access_token_if_needed()

    # def login(self):
    #     self._oauth = self.get_oauth()
    #     print(self._oauth)

    async def regions(self):
        resp = await self._session.get(urljoin(self._accounts_url_base, "api/mobile/regions"))
        print(resp.text)

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
