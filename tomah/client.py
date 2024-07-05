from urllib.parse import urljoin

import json_api_doc
import requests

from .auth import Auth


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
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": domain_components[0] + self.USER_AGENT_SUFFIX})

        self._auth_session = requests.Session()
        self._auth_session.headers.update({"User-Agent": domain_components[0] + self.USER_AGENT_SUFFIX})

        self._api_url_base = self.API_URL_PREFIX + domain
        self._accounts_url_base = self.ACCOUNTS_URL_PREFIX + domain
        self._session.auth = Auth(client_id, self._accounts_url_base, username, password, session=self._auth_session)

    def get_hass_platforms(self):
        pass

    # def login(self):
    #     self._oauth = self.get_oauth()
    #     print(self._oauth)

    def regions(self):
        resp = self._session.get(urljoin(self._accounts_url_base, "api/mobile/regions"))
        print(resp.text)

    def tokens(self):
        resp = self._session.get(urljoin(self._accounts_url_base, "api/v1/account/tokens"))
        print(f"tokens: {resp.text}")

    def devices(self):
        resp = self._session.get(urljoin(self._api_url_base, "mobile/v4/users/devices"))
        print(f"devices: {resp.text}")

    def me(self):
        resp = self._session.get(urljoin(self._api_url_base, "mobile/v3/me"))
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
