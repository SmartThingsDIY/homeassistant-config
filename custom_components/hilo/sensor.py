from homeassistant.const import POWER_WATT
from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import logging
_LOGGER = logging.getLogger(__name__)
from .const import DOMAIN
from .hilo_device import HiloBaseEntity



async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for d in hass.data[DOMAIN].devices:
        if "Power" in d.supported_attributes:
            d._entity = PowerSensor(d, hass.data[DOMAIN].scan_interval)
            entities.append(d._entity)
    async_add_entities(entities)

class PowerSensor(HiloBaseEntity, Entity):
    def __init__(self, d, scan_interval):
        super().__init__(d, scan_interval)
        _LOGGER.debug(f"Setting up PowerSensor entity: {self._name}")

    @property
    def state(self):
        return str(int(self._get('Power', 0)))

    @property
    def state_class(self):
        return STATE_CLASS_MEASUREMENT

    @property
    def device_class(self):
        return "power"

    @property
    def unit_of_measurement(self):
        return POWER_WATT

    async def _async_update(self):
        # Other devices are updated within their own
        # classes. If we don't escape them, they will
        # be double-polled
        if self.d.device_type != "Meter":
            return
        _LOGGER.debug(f"{self.d._tag} Updating")
        await self.d.async_update_device()
