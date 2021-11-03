from abc import ABC, abstractmethod
import asyncio
import async_timeout
import aiohttp
import logging
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_component import async_update_entity
import json
from datetime import datetime, timedelta
from time import time
import urllib

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_LIGHT_AS_SWITCH,
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)


class Hilo:
    _username = None
    _password = None
    _access_token = None
    _location_id = None
    is_event = None

    _base_url = "https://apim.hiloenergie.com/Automation/v1/api"
    _subscription_key = "20eeaedcb86945afa3fe792cea89b8bf"
    _token_expiration = None
    _timeout = 30
    _verify = True
    devices = []

    def __init__(
        self,
        username,
        password,
        hass,
        scan_interval=DEFAULT_SCAN_INTERVAL,
        light_as_switch=DEFAULT_LIGHT_AS_SWITCH,
        ):
        self._username = username
        self._password = urllib.parse.quote(password, safe="")
        self._hass = hass
        self.scan_interval = scan_interval
        self.light_as_switch = light_as_switch
        self.async_update = Throttle(self.scan_interval)(self._async_update)
        self.refresh_token = Throttle(timedelta(seconds=120))(self._refresh_token)

    @property
    async def location_url(self):
        self._location_id = await self.get_location_id()
        return f"{self._base_url}/Locations/{self._location_id}"

    @property
    def headers(self):
        return {
            "Ocp-Apim-Subscription-Key": self._subscription_key,
            "authorization": f"Bearer {self._access_token}",
        }

    async def async_call(self, url, method="get", headers={}, data={}, retry=3):
        async def try_again(err: str):
            if retry < 1:
                _LOGGER.error(f"Unable to {method} {url}: {err}")
                raise HomeAssistantError("Retry limit reached")
            _LOGGER.error(f"Retry #{retry - 1}: {err}")
            return await self.async_call(
                url, method=method, headers=headers, data=data, retry=retry - 1
            )

        #_LOGGER.debug(f"Request {method} {url}")
        try:
            session = async_get_clientsession(self._hass, self._verify)
            with async_timeout.timeout(self._timeout):
                resp = await getattr(session, method)(url, headers=headers, data=data)
            #_LOGGER.debug(f"Response: {resp.status} {resp.text}")
            if resp.status == 401:
                if "oauth2" not in url:
                    await self.refresh_token(True)
                    return await try_again(f"{resp.url} Token is expired, trying again")
                else:
                    _LOGGER.error(
                        "Access denied when refreshing token, unloading integration. Bad username / password"
                    )
                    self._hass.services.async_remove(DOMAIN)
                    raise HomeAssistantError("Wrong username / password")
            if resp.status != 200:
                _LOGGER.error(f"{method} on {url} failed: {resp.status} {resp.text}")
                return await try_again(f"{url} returned {resp.status}")
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error(f"{method} {url} failed")
            _LOGGER.exception(err)
            return await try_again(err)
        try:
            data = await resp.json()
        except aiohttp.client_exceptions.ContentTypeError:
            _LOGGER.warning(f"{resp.url} returned {resp.status} non-json: {resp.text}")
            return resp.text
        except Exception as e:
            _LOGGER.exception(e)
            return await try_again(f"{resp.url} returned {resp.status}: {resp.text}")
        return data

    async def _request(self, url, method="get", headers={}, data={}):
        await self.refresh_token()
        if not headers:
            headers = self.headers
        if method == "put":
            headers = {**headers, **{"Content-Type": "application/json"}}
        try:
            out = await self.async_call(url, method, headers, data)
        except HomeAssistantError as e:
            _LOGGER.exception(e)
            raise
        return out

    async def get_access_token(self):
        url = ("https://hilodirectoryb2c.b2clogin.com/"
               "hilodirectoryb2c.onmicrosoft.com/oauth2/"
               "v2.0/token?p=B2C_1A_B2C_1_PasswordFlow")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {
            "grant_type": "password",
            "scope": "openid 9870f087-25f8-43b6-9cad-d4b74ce512e1 offline_access",
            "client_id": "9870f087-25f8-43b6-9cad-d4b74ce512e1",
            "response_type": "token id_token",
            "username": self._username,
            "password": self._password
        }
        _LOGGER.debug("Calling oauth2 url")
        req = await self.async_call(url, method="post", headers=headers, data=body)
        return req.get("access_token", None)

    async def _refresh_token(self, force=False):
        expiration = self._token_expiration if self._token_expiration else time() - 200
        time_to_expire = time() - expiration
        _LOGGER.debug(
            f"Refreshing token, force: {force} Expiration: "
            f"{datetime.fromtimestamp(expiration)} "
            f"Time to expire: {time_to_expire}"
        )
        if force or not self._access_token or time() > expiration:
            self._token_expiration = time() + 3000
            self._access_token = await self.get_access_token()
            if not self._access_token:
                return False
        return True

    async def get_location_id(self):
        if self._location_id:
            return self._location_id
        url = f"{self._base_url}/Locations"
        req = await self._request(url)
        return req[0]["id"]

    async def get_events(self):
        url = f"{self._base_url}/Drms/Locations/{self._location_id}/Events"
        req = await self._request(url)
        event = {}
        now = datetime.utcnow() - timedelta(hours=5)
        for i in range(len(req)):
            start_time = datetime.strptime(
                req[i]["startTimeUTC"], "%Y-%m-%dT%H:%M:%SZ"
            ) - timedelta(hours=5)
            end_time = datetime.strptime(
                req[i]["endTimeUTC"], "%Y-%m-%dT%H:%M:%SZ"
            ) - timedelta(hours=5)
            if (
                (start_time.day == now.day)
                & (now.hour >= start_time.hour)
                & (now.hour < (end_time.hour))
            ):
                event[i] = True
            else:
                event[i] = False
        test = 0
        for i in range(len(event)):
            if event[i] == True:
                test = test + 1
        if test == 0:
            self.is_event = False
        else:
            self.is_event = True

    async def get_devices(self):
        """ Get list of all devices """
        url = f"{await self.location_url}/Devices"
        req = await self._request(url)
        for i, v in enumerate(req):
            device = next(
                (x for x in self.devices if x.device_id == v['id']),
                Device(self)
            )
            await device._set_hilo_attributes(**v)
            if not device in self.devices:
                self.devices.append(device)


    async def _async_update(self):
        # self.get_events()
        _LOGGER.info(f"Pulling all devices")
        await self.get_devices()


    async def async_update_all_devices(self):
        _LOGGER.info(f"Updating attributes for all devices")
        await self.get_devices()
        for d in self.devices:
            await d.async_update_device()


class Device:
    def __init__(self, hass):
        self._h = hass
        self._entity = None

    async def _set_hilo_attributes(self, **kw):
        self.name = kw.get('name')
        self.device_type = kw.get('type')
        self.supported_attributes = kw.get('supportedAttributes').split(", ")
        self.settable_attributes = kw.get('settableAttributes')
        self.device_id = kw.get('id')
        self.category = kw.get('category')
        self._tag = f"[Device {self.name} ({self.device_type})]"
        self._device_url = f"{await self._h.location_url}/Devices/{self.device_id}"
        # All devices like SmokeDetectors don't have the disconnected attribute
        # but it can be fetched
        if "Disconnected" not in self.supported_attributes:
            self.supported_attributes.append("Disconnected")
        if "None" in self.supported_attributes:
            self.supported_attributes.remove("None")

    async def get_device_attributes(self):
        url = f"{self._device_url}/Attributes"
        req = await self._h._request(url)
        self._raw_attributes = {k.lower(): v for k, v in req.items()}
        #_LOGGER.debug(f"[Device {index} {d.name} ({d.device_type})] get_device_attributes: {self.d[index].AttributeRaw}")

    async def set_attribute(self, key, value):
        _LOGGER.debug(
            f"{self._tag} setting remote attribute {key} to {value}"
        )
        setattr(self, key, value)
        url = f"{self._device_url}/Attributes"
        await self._h._request(url, method="put", data=json.dumps({key: str(value)}))

    async def async_update_device(self):
        await self.get_device_attributes()
        _LOGGER.debug(
            f"{self._tag} update_device attributes: {self.supported_attributes} "
        )
        for x in self.supported_attributes:
            value = self._raw_attributes.get(x.lower(), {}).get("value", None)
            #_LOGGER.debug(f"{self._tag} setting local attribute {x} to {value}")
            setattr(self, x, value)

    def __eq__(self, other):
        return self.device_id == other.device_id
