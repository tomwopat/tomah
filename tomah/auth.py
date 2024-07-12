import logging
import time
from urllib.parse import urljoin

import httpx
from ratelimit import limits

_LOGGER = logging.getLogger(__name__)


class Auth(httpx.Auth):
    ACCESS_TOKEN_RENEWAL_PCT = 0.8

    def __init__(
        self,
        client_id,
        url_base,
        username,
        password,
        session=None,
        async_load_oauth=None,
        async_save_oauth=None,
        token_renewal_pct=ACCESS_TOKEN_RENEWAL_PCT,
    ):
        self._client_id = client_id
        self._url_base = url_base
        self._username = username
        self._password = password
        self._async_load_oauth_cb = async_load_oauth
        self._async_save_oauth_cb = async_save_oauth
        self.token_renewal_pct = token_renewal_pct

        if session:
            self._session = session
        else:
            self._session = httpx.AsyncClient()
        self._oauth = None

    # TODO: use aiohttp instead of requests?
    async def async_login(self):
        _LOGGER.debug("async_login")
        if self._async_load_oauth_cb:
            self._oauth = await self._async_load_oauth_cb()
            # TODO: force refresh of token regardless of whether it's expired?
            if self.should_refresh_access_token():
                _LOGGER.debug("async_login: access_token expired, refreshing access token")
                if not await self.refresh_access_token():
                    _LOGGER.debug("async_login: can't refresh access token, re-authenticating")
                    await self._authenticate()
        else:
            await self._authenticate()

    async def _save_oauth(self):
        if self._async_save_oauth_cb:
            await self._async_save_oauth_cb(self._oauth)

    def access_token_expired(self):
        if not self._oauth:
            return True
        if "expires_in" not in self._oauth or "created_at" not in self._oauth:
            return True
        if self._oauth["created_at"] + self._oauth["expires_in"] < time.time():
            _LOGGER.debug("token expired")
            return True
        return False

    # limit to 5 calls per minute
    @limits(calls=5, period=60)
    async def refresh_access_token(self):
        _LOGGER.debug("refresh access token")
        if not self.access_token:
            _LOGGER.info("no valid refresh token, can't refresh access token")
            return False
        resp = await self._session.post(
            urljoin(self._url_base, "oauth/token"),
            data={
                "grant_type": "refresh_token",
                "client_id": self._client_id,
                "refresh_token": self._oauth["refresh_token"],
            },
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        # tell caller to try and re-login
        if resp.status_code != 200:
            _LOGGER.info(f"got status code {resp.status_code} from refresh token, try to re-login? {resp.text}")
            return False
        _LOGGER.info(f"refreshed access token: {resp.text}")
        self._oauth = resp.json()
        await self._save_oauth()
        return True

    def should_refresh_access_token(self):
        if not self._oauth:
            return True
        if "expires_in" not in self._oauth or "created_at" not in self._oauth:
            return True
        if self._oauth["created_at"] + (self._oauth["expires_in"] * self.token_renewal_pct) < time.time():
            return True
        return False

    async def refresh_access_token_if_needed(self):
        if self.should_refresh_access_token():
            await self.refresh_access_token()

    # limit to 5 calls per minute
    @limits(calls=5, period=60)
    async def _authenticate(self):
        resp = await self._session.post(
            urljoin(self._url_base, "oauth/token"),
            data={
                "client_id": self._client_id,
                "grant_type": "password",
                "username": self._username,
                "password": self._password,
            },
        )
        if resp.status_code != 200:
            raise Exception(f"Failed to login: {resp.text}")
        self._oauth = resp.json()
        _LOGGER.debug(f"authentication successful {self._oauth}")
        await self._save_oauth()
        return True

    def valid_token(self):
        if not self._oauth:
            return False
        if self.access_token_expired():
            return False
        return True

    @property
    def access_token(self):
        if not self._oauth or "access_token" not in self._oauth:
            return None
        return self._oauth["access_token"]

    async def async_auth_flow(self, request):
        if self.should_refresh_access_token():
            await self.refresh_access_token()
            if not self.valid_token():
                await self._authenticate()
            if not self.valid_token():
                raise Exception("Failed to get a valid token")
        request.headers.update({"Authorization": f"Bearer {self.access_token}"})
        # print(self.access_token)
        yield request
