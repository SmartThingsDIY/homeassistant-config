from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT
from homeassistant.util import Throttle
import logging
from .const import (
    DOMAIN,
    HILO_SENSOR_CLASSES
)
from .hilo_device import HiloBaseEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for d in hass.data[DOMAIN].devices:
        if d.device_type in HILO_SENSOR_CLASSES:
            d._entity = HiloSensor(d, hass.data[DOMAIN].scan_interval)
            entities.append(d._entity)
    async_add_entities(entities)

class HiloSensor(HiloBaseEntity, BinarySensorEntity):
    def __init__(self, d, scan_interval):
        super().__init__(d, scan_interval)
        if d.name == "SmartEnergyMeter":
            self._name = "Défi Hilo"
        else:
            self._name = d.name
        _LOGGER.debug(f"Setting up BinarySensor entity: {self._name} Scan: {scan_interval}")

    @property
    def device_class(self):
        return "power"

    @property
    def state_class(self):
        return STATE_CLASS_MEASUREMENT

    async def _async_update(self):
        return
