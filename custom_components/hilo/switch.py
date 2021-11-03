from homeassistant.helpers.entity import ToggleEntity
from homeassistant.components.switch import DEVICE_CLASSES as SWITCH_CLASSES
from homeassistant.util import Throttle
import logging
_LOGGER = logging.getLogger(__name__)
from .const import (
    DOMAIN,
    SWITCH_CLASSES
)
from .hilo_device import HiloBaseEntity


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    switch_classes = SWITCH_CLASSES
    entities = []
    if hass.data[DOMAIN].light_as_switch:
        switch_classes.append("LightSwitch")
    for d in hass.data[DOMAIN].devices:
        if d.device_type in switch_classes:
            d._entity = HiloSwitch(d, hass.data[DOMAIN].scan_interval)
            entities.append(d._entity)
    async_add_entities(entities)

    return True


class HiloSwitch(HiloBaseEntity, ToggleEntity):
    def __init__(self, d, scan_interval):
        super().__init__(d, scan_interval)
        _LOGGER.debug(f"Setting up Switch entity: {self._name} Scan: {scan_interval}")

    @property
    def state(self):
        return "on" if self.is_on else "off"


