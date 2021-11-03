from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)
from homeassistant.util import Throttle
import logging
_LOGGER = logging.getLogger(__name__)
from .const import (
    DOMAIN,
    LIGHT_CLASSES
)
from .hilo_device import HiloBaseEntity

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    light_classes = LIGHT_CLASSES
    if hass.data[DOMAIN].light_as_switch:
        light_classes.remove("LightSwitch")
    for d in hass.data[DOMAIN].devices:
        if d.device_type in light_classes:
            d._entity = HiloDimmer(d, hass.data[DOMAIN].scan_interval)
            entities.append(d._entity)
    async_add_entities(entities)


class HiloDimmer(HiloBaseEntity, LightEntity):
    def __init__(self, d, scan_interval):
        super().__init__(d, scan_interval)
        _LOGGER.debug(f"Setting up Light entity: {self._name} Scan: {scan_interval}")

    @property
    def brightness(self):
        return self._get('Intensity', 0) * 255

    @property
    def state(self):
        return "on" if self.is_on else "off"

    @property
    def supported_features(self):
        """Flag supported features."""
        supports = 0
        if "Intensity" in self.d.supported_attributes:
            supports = SUPPORT_BRIGHTNESS
        return supports

    async def async_turn_on(self, **kwargs):
        _LOGGER.info(f"{self.d._tag} Tunring on")
        await self.d.set_attribute("OnOff", True)
        if ATTR_BRIGHTNESS in kwargs:
            _LOGGER.info(
                f"{self.d._tag} Setting brightness to {kwargs[ATTR_BRIGHTNESS]}"
            )
            await self.d.set_attribute(
                "Intensity", kwargs[ATTR_BRIGHTNESS] / 255
            )
