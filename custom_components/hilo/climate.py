from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_TENTHS,
    TEMP_CELSIUS,
)
from homeassistant.util import Throttle
import logging
_LOGGER = logging.getLogger(__name__)
from .const import (
    DOMAIN,
    CLIMATE_CLASSES
)
from .hilo_device import HiloBaseEntity

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = []
    for d in hass.data[DOMAIN].devices:
        if d.device_type in CLIMATE_CLASSES:
            d._entity = HiloClimate(d, hass.data[DOMAIN].scan_interval)
            entities.append(d._entity)
    async_add_entities(entities)
    return True


class HiloClimate(HiloBaseEntity, ClimateEntity):
    def __init__(self, d, scan_interval):
        super().__init__(d, scan_interval)
        self.operations = [HVAC_MODE_HEAT, HVAC_MODE_OFF]
        self._has_operation = False
        self._temp_entity = None
        self._temp_entity_error = False
        _LOGGER.debug(f"Setting up Climate entity: {self._name} Scan: {scan_interval}")

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_TENTHS

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        return self._get('CurrentTemperature', 0)

    @property
    def target_temperature(self):
        return self._get('TargetTemperature', 0)

    @property
    def max_temp(self):
        return self._get('MaxTempSetpoint', 0)

    @property
    def min_temp(self):
        return self._get('MinTempSetpoint', 0)

    def set_hvac_mode(self, hvac_mode):
        """Set operation mode."""
        return

    @property
    def hvac_mode(self):
        if not self._get('Heating'):
            return HVAC_MODE_OFF
        else:
            return HVAC_MODE_HEAT

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return [HVAC_MODE_HEAT, HVAC_MODE_OFF]

    @property
    def supported_features(self):
        return SUPPORT_TARGET_TEMPERATURE

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            _LOGGER.info(f"{self.d._tag} Setting temperature to {kwargs[ATTR_TEMPERATURE]}")
            await self.d.set_attribute(
                "TargetTemperature", kwargs[ATTR_TEMPERATURE]
            )
            if kwargs[ATTR_TEMPERATURE] < self._get('CurrentTemperature', 0):
                self.d.Heating = 100
            else:
                self.d.Heating = 0
