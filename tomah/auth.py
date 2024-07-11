import json
import logging
import os
import pprint
import time
from urllib.parse import urljoin

import requests
from ratelimit import limits
from requests.auth import AuthBase

_LOGGER = logging.getLogger(__name__)


class Auth(AuthBase):
    def __init__(
        self, client_id, url_base, username, password, session=None, async_load_oauth=None, async_save_oauth=None
    ):
        self._client_id = client_id
        self._url_base = url_base
        self._username = username
        self._password = password
        self._async_load_oauth_cb = async_load_oauth
        self._async_save_oauth_cb = async_save_oauth

        if session:
            self._session = session
        else:
            self._session = requests.Session()
        self._oauth = None

    # TODO: use aiohttp instead of requests?
    async def async_login(self):
        if self._async_load_oauth_cb:
            self._oauth = await self._async_load_oauth_cb()
            # TODO: force refresh of token regardless of whether it's expired?
            if self.should_refresh_access_token():
                if not self.refresh_access_token():
                    self._authenticate()
        else:
            self._authenticate()

    def _load_oauth(self):
        # load self._oauth from disk
        if not os.path.exists(self.CREDENTIALS_FILE):
            return False
        try:
            with open(self.CREDENTIALS_FILE, "r") as f:
                self._oauth = json.load(f)
                _LOGGER.info(f"loaded oauth from file {pprint.pformat(self._oauth)}")
        except Exception as e:
            _LOGGER.error(f"Failed to load oauth from file: {e}")
            return False
        return True

    def _save_oauth(self):
        if self._async_save_oauth_cb:
            self._async_save_oauth_cb(self._oauth)

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
    def refresh_access_token(self):
        _LOGGER.debug("refresh access token")
        if not self.access_token:
            _LOGGER.info("no valid refresh token, can't refresh access token")
            return False
        resp = self._session.post(
            urljoin(self._url_base, "oauth/token"),
            data={
                "grant_type": "password",
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
        self._save_oauth()
        return True

    def should_refresh_access_token(self):
        if not self._oauth:
            return True
        if "expires_in" not in self._oauth or "created_at" not in self._oauth:
            return True
        if self._oauth["created_at"] + (self._oauth["expires_in"] * self.ACCESS_TOKEN_RENEWAL_PCT) < time.time():
            return True

    def refresh_access_token_if_needed(self):
        if self.should_refresh_access_token():
            self.refresh_access_token()

    # limit to 5 calls per minute
    @limits(calls=5, period=60)
    def _authenticate(self):
        resp = self._session.post(
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
        self._save_oauth()
        return True

    def valid_token(self):
        if not self._oauth:
            return False
        if self.access_token_expired():
            return False
        return True

    @property
    def access_token(self):
        if not self._oauth or "access_token" in self._oauth:
            return None
        return self._oauth["access_token"]

    def __call__(self, req):
        if self.should_refresh_access_token():
            self.refresh_access_token()
            if not self.valid_token():
                self._authenticate()
            if not self.valid_token():
                raise Exception("Failed to get a valid token")
        req.headers.update({"Authorization": f"Bearer {self.access_token}"})
        # print(self.access_token)
        return req
