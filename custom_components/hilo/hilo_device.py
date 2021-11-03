from homeassistant.helpers.entity import ToggleEntity
from homeassistant.util import Throttle
import logging
_LOGGER = logging.getLogger(__name__)

class HiloBaseEntity:
    def __init__(self, d, scan_interval):
        self._name = d.name
        self.d = d
        self._should_poll = True
        self.async_update = Throttle(scan_interval)(self._async_update)

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._get('OnOff')

    @property
    def available(self):
        return not self._get('Disconnected')

    @property
    def should_poll(self) -> bool:
        return True

    async def async_turn_on(self, **kwargs):
        _LOGGER.info(f"{self.d._tag} Turning on")
        await self.d.set_attribute("OnOff", True)

    async def async_turn_off(self, **kwargs):
        _LOGGER.info(f"{self.d._tag} Turning off")
        await self.d.set_attribute("OnOff", False)

    async def _async_update(self):
        _LOGGER.debug(f"{self.d._tag} Updating")
        await self.d.async_update_device()

    def _get(self, att, default=None):
        try:
            return getattr(self.d, att)
        except AttributeError:
            return default
