from abc import ABC, abstractmethod
import asyncio
import async_timeout
import aiohttp
import logging
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle
import json
from datetime import datetime, timedelta
from time import time
import urllib

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_LIGHT_AS_LIGHT,
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
    _access_token_expiration = None
    _timeout = 30
    _verify = True
    d = {}

    def __init__(
        self,
        username,
        password,
        hass,
        scan_interval=DEFAULT_SCAN_INTERVAL,
        light_as_light=DEFAULT_LIGHT_AS_LIGHT
        ):
        self._username = username
        self._password = urllib.parse.quote(password, safe="")
        self._hass = hass
        self.scan_interval = scan_interval
        self.light_as_light = light_as_light
        self.async_update = Throttle(self.scan_interval)(self._async_update)
        self.refreshAccessToken = Throttle(timedelta(seconds=120))(self._refreshAccessToken)

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
                    await self.refreshAccessToken(True)
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
        await self.refreshAccessToken()
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

    async def getAccessToken(self):
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

    async def _refreshAccessToken(self, force=False):
        time_to_expire = time() - self._access_token_expiration
        _LOGGER.debug(
            f"Refreshing token, force: {force} Expiration: "
            f"{datetime.fromtimestamp(self._access_token_expiration)} "
            f"Time to expire: {time_to_expire}"
        )
        if force or not self._access_token or time() > self._access_token_expiration:
            self._access_token_expiration = time() + 3000
            self._access_token = await self.getAccessToken()
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
        url_get_device = f"{await self.location_url}/Devices"
        req = await self._request(url_get_device)
        _LOGGER.debug(f"get_devices: {req}")

        for i, v in enumerate(req):
            _LOGGER.debug(f"Device {i} {v}")
            self.d[i] = Device(
                v["name"],
                v["identifier"],
                v["type"],
                v["supportedAttributes"],
                v["settableAttributes"],
                v["id"],
                v["category"],
            )

    async def get_device_attributes(self, index):
        d = self.d[index]
        url = f"{await self.location_url}/Devices/{d.deviceId}/Attributes"
        req = await self._request(url)
        self.d[index].AttributeRaw = {k.lower(): v for k, v in req.items()}
        #_LOGGER.debug(f"[Device {index} {d.name} ({d.deviceType})] get_device_attributes: {self.d[index].AttributeRaw}")

    async def _async_update(self):
        # self.get_events()
        await self.get_devices()
        _LOGGER.debug(f"updating all {len(self.d)} devices")

    async def _async_update_all_devices(self):
        for i, d in self.d.items():
            await self.update_device(i)

    async def async_update_device(self, index):
        d = self.d[index]
        await self.get_device_attributes(index)
        suppAttr = d.supportedAttributes.split(", ")
        # All devices like SmokeDetectors don't have the disconnected attribute
        # but it can be fetched
        if "Disconnected" not in suppAttr:
            suppAttr.append("Disconnected")
        if "None" in suppAttr:
            suppAttr.remove("None")
        _LOGGER.debug(
            f"[Device {index} {d.name} ({d.deviceType})] update_device attributes: {suppAttr}"
        )
        for x in suppAttr:
            value = d.AttributeRaw.get(x.lower(), {}).get("value", None)
            #_LOGGER.debug(f"[Device {index} {d.name} ({d.deviceType})] setting local attribute {x} to {value}")
            setattr(d, x, value)

    async def set_attribute(self, key, value, index):
        d = self.d[index]
        _LOGGER.debug(
            f"[Device {index} {d.name} ({d.deviceType})] setting remote attribute {key} to {value}"
        )
        setattr(d, key, value)
        url = f"{await self.location_url}/Devices/{d.deviceId}/Attributes"
        await self._request(url, method="put", data=json.dumps({key: str(value)}))

class Device:
    __name = None
    __identifier = None
    __deviceType = None
    __supportedAttributes = None
    __settableAttributes = None
    __deviceId = None
    __category = None
    OnOff = None
    Intensity = 0
    CurrentTemperature = None
    TargetTemperature = None
    Power = None
    Status = None
    Heating = None
    BatteryPercent = None
    BatteryStatus = None
    ActiveAlarm = None
    WaterLeakStatus = None
    MotorTargetPosition = None
    MotorPosition = None
    AlertLowBatt = None
    AlertWaterLeak = None
    AlertLowTemp = None
    MaxTempSetpoint = None
    MinTempSetpoint = None
    StateTemperatures = None
    LoadConnected = None
    Icon = None
    Category = None
    Disconnected = None
    ColorMode = None
    Hue = None
    Saturation = None
    LockKeypad = None
    BackLight = None
    LoadConnectedDB = None
    Humidity = None
    ColorTemperature = None
    DrmsState = None
    Noise = None
    Pressure = None
    Co2 = None
    WifiStatus = None
    GrapState = None
    AttributeRaw = {}

    def __init__(
        self,
        name,
        identifier,
        deviceType,
        supportedAttributes,
        settableAttributes,
        deviceId,
        category,
    ):
        self.__name = name
        self.__deviceType = deviceType
        self.__supportedAttributes = supportedAttributes
        self.__settableAttributes = settableAttributes
        self.__deviceId = deviceId
        self.__category = category

    @property
    def deviceId(self):
        return self.__deviceId

    @property
    def name(self):
        return self.__name

    @property
    def supportedAttributes(self):
        return self.__supportedAttributes

    @property
    def settableAttributes(self):
        return self.__settableAttributes

    @property
    def deviceType(self):
        return self.__deviceType

    @property
    def category(self):
        return self.__category

