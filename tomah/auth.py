import json
import os
import pprint
import time
from urllib.parse import urljoin

import requests
from ratelimit import limits
from requests.auth import AuthBase


class Auth(AuthBase):
    def __init__(self, client_id, url_base, username, password, session=None):
        self._client_id = client_id
        self._url_base = url_base
        self._username = username
        self._password = password
        if session:
            self._session = session
        else:
            self._session = requests.Session()
        self._oauth = None
        self.access_token = None
        self._load_oauth()

    def _load_oauth(self):
        # load self._oauth from disk
        if not os.path.exists(self.CREDENTIALS_FILE):
            return False
        try:
            with open(self.CREDENTIALS_FILE, "r") as f:
                self._oauth = json.load(f)
                print(f"loaded oauth from file {pprint.pformat(self._oauth)}")
        except Exception as e:
            print(f"Failed to load oauth from file: {e}")
            return False
        return False

    def _save_oauth(self):
        with open(self.CREDENTIALS_FILE, "w") as f:
            json.dump(self._oauth, f)

    def access_token_expired(self):
        if not self._oauth:
            return True
        if "expires_in" not in self._oauth or "created_at" not in self._oauth:
            return True
        if self._oauth["created_at"] + self._oauth["expires_in"] < time.time():
            print("token expired")
            return True
        return False

    # limit to 5 calls per minute
    @limits(calls=5, period=60)
    def refresh_access_token(self):
        print("refresh access token")
        if not self._oauth:
            print("no valid refresh token, can't refresh access token")
            return False
        resp = self._session.post(
            urljoin(self._url_base, "oauth/token"),
            data={
                "grant_type": "password",
                "client_id": self._client_id,
                "refresh_token": self._oauth["refresh_token"],
            },
        )

        # tell caller to try and re-login
        if resp.status_code != 200:
            print(f"got status code {resp.status_code} from refresh token, try to re-login? {resp.text}")
            return False
        print(f"refreshed access token: {resp.text}")
        self._oauth = resp.json()
        self._save_oauth()
        return True

    # limit to 5 calls per minute
    @limits(calls=5, period=60)
    def login(self):
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

    #
    # def valid_token(self):
    #     if not self.access_token_expired()
    #     if not self._oauth:
    #         return False
    #     if self.access_token_expired():
    #         return False
    #     return True

    def __call__(self, req):
        if self.access_token_expired():
            self.login()
            if not self.access_token_expired():
                raise Exception("Failed to get a valid token")
        self.access_token = self._oauth["access_token"]
        req.headers.update({"Authorization": f"Bearer {self.access_token}"})
        # print(self.access_token)
        return req
