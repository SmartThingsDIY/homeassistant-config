"""
A component which presents Yahoo Finance stock quotes.

https://github.com/iprak/yahoofinance
"""

import logging
from timeit import default_timer as timer

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.entity import Entity, async_generate_entity_id

from .const import (
    ATTR_CURRENCY_SYMBOL,
    ATTR_MARKET_STATE,
    ATTR_QUOTE_SOURCE_NAME,
    ATTR_QUOTE_TYPE,
    ATTR_SYMBOL,
    ATTR_TRENDING,
    ATTRIBUTION,
    CONF_DECIMAL_PLACES,
    CONF_SHOW_TRENDING_ICON,
    CONF_SYMBOLS,
    CONF_TARGET_CURRENCY,
    CURRENCY_CODES,
    DATA_CURRENCY_SYMBOL,
    DATA_FINANCIAL_CURRENCY,
    DATA_MARKET_STATE,
    DATA_QUOTE_SOURCE_NAME,
    DATA_QUOTE_TYPE,
    DATA_REGULAR_MARKET_PREVIOUS_CLOSE,
    DATA_REGULAR_MARKET_PRICE,
    DATA_SHORT_NAME,
    DEFAULT_CURRENCY,
    DEFAULT_ICON,
    DEFAULT_NUMERIC_DATA_GROUP,
    DOMAIN,
    HASS_DATA_CONFIG,
    HASS_DATA_COORDINATOR,
    NUMERIC_DATA_GROUPS,
)

_LOGGER = logging.getLogger(__name__)
ENTITY_ID_FORMAT = SENSOR_DOMAIN + "." + DOMAIN + "_{}"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Yahoo Finance sensor platform."""

    coordinator = hass.data[DOMAIN][HASS_DATA_COORDINATOR]
    domain_config = hass.data[DOMAIN][HASS_DATA_CONFIG]
    symbols = domain_config[CONF_SYMBOLS]

    sensors = [
        YahooFinanceSensor(hass, coordinator, symbol, domain_config)
        for symbol in symbols
    ]

    async_add_entities(sensors, update_before_add=False)
    _LOGGER.info("Entities added for %s", [item["symbol"] for item in symbols])


class YahooFinanceSensor(Entity):
    """Represents a Yahoo finance entity."""

    _currency = DEFAULT_CURRENCY
    _icon = DEFAULT_ICON
    _market_price = None
    _short_name = None
    _target_currency = None
    _original_currency = None
    _last_available_timer = None

    def __init__(self, hass, coordinator, symbol_definition, domain_config) -> None:
        """Initialize the sensor."""
        symbol = symbol_definition.get("symbol")
        self._hass = hass
        self._symbol = symbol
        self._coordinator = coordinator
        self._show_trending_icon = domain_config[CONF_SHOW_TRENDING_ICON]
        self._decimal_places = domain_config[CONF_DECIMAL_PLACES]
        self._previous_close = None
        self._target_currency = symbol_definition.get(CONF_TARGET_CURRENCY)

        self.entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, symbol, hass=hass)

        self._attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_CURRENCY_SYMBOL: None,
            ATTR_SYMBOL: symbol,
            ATTR_QUOTE_TYPE: None,
            ATTR_QUOTE_SOURCE_NAME: None,
            ATTR_MARKET_STATE: None,
        }

        # List of groups to include as attributes
        self._numeric_data_to_include = []

        # Initialize all numeric attributes which we want to include to None
        for group in NUMERIC_DATA_GROUPS:
            if group == DEFAULT_NUMERIC_DATA_GROUP or domain_config.get(group, True):
                for value in NUMERIC_DATA_GROUPS[group]:
                    self._numeric_data_to_include.append(value)

                    key = value[0]
                    self._attributes[key] = None

        # Delay initial data population to `available` which is called from `_async_write_ha_state`
        _LOGGER.debug(
            "Created %s target_currency=%s", self.entity_id, self._target_currency
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        if self._short_name is not None:
            return self._short_name

        return self._symbol

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._round(self._market_price)

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity, if any."""
        return self._currency

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend, if any."""
        return self._icon

    def _round(self, value):
        """Return formatted value based on decimal_places."""
        if value is None:
            return None

        if self._decimal_places < 0:
            return value
        if self._decimal_places == 0:
            return int(value)

        return round(value, self._decimal_places)

    def _get_target_currency_conversion(self) -> float:
        value = None

        if self._target_currency and self._original_currency:
            if self._target_currency == self._original_currency:
                _LOGGER.info("%s No conversion necessary", self._symbol)
                return None

            conversion_symbol = (
                f"{self._original_currency}{self._target_currency}=X".upper()
            )
            data = self._coordinator.data

            if data is not None:
                symbol_data = data.get(conversion_symbol)

                if symbol_data is not None:
                    value = symbol_data[DATA_REGULAR_MARKET_PRICE]
                    _LOGGER.debug("%s %s is %s", self._symbol, conversion_symbol, value)
                else:
                    _LOGGER.debug(
                        "%s No data found for %s",
                        self._symbol,
                        conversion_symbol,
                    )
                    self._coordinator.add_symbol(conversion_symbol)

        return value

    @staticmethod
    def safe_convert(value, conversion):
        """Return the converted value. The original value is returned if there is no conversion."""
        if value is None:
            return None
        if conversion is None:
            return value
        return value * conversion

    def _update_original_currency(self, symbol_data) -> bool:
        """Update the original currency."""

        # Symbol currency does not change so calculate it only once
        if self._original_currency is not None:
            return

        # Prefer currency over financialCurrency, for foreign symbols financialCurrency
        # can represent the remote currency. But financialCurrency can also be None.
        financial_currency = symbol_data[DATA_FINANCIAL_CURRENCY]
        currency = symbol_data[DATA_CURRENCY_SYMBOL]

        _LOGGER.debug(
            "%s currency=%s financialCurrency=%s",
            self._symbol,
            currency,
            financial_currency,
        )

        self._original_currency = currency or financial_currency or DEFAULT_CURRENCY

    def _update_properties(self) -> None:
        """Update local fields."""

        data = self._coordinator.data
        if data is None:
            _LOGGER.debug("%s Coordinator data is None", self._symbol)
            return

        symbol_data = data.get(self._symbol)
        if symbol_data is None:
            _LOGGER.debug("%s Symbol data is None", self._symbol)
            return

        self._update_original_currency(symbol_data)
        conversion = self._get_target_currency_conversion()

        self._short_name = symbol_data[DATA_SHORT_NAME]

        market_price = symbol_data[DATA_REGULAR_MARKET_PRICE]
        self._market_price = self.safe_convert(market_price, conversion)
        # _market_price gets rounded in the `state` getter.

        if conversion:
            _LOGGER.info(
                "%s converted %s X %s = %s",
                self._symbol,
                market_price,
                conversion,
                self._market_price,
            )

        self._previous_close = self.safe_convert(
            symbol_data[DATA_REGULAR_MARKET_PREVIOUS_CLOSE], conversion
        )

        for value in self._numeric_data_to_include:
            key = value[0]
            attr_value = symbol_data[key]

            # Convert if currency value
            if value[1]:
                attr_value = self.safe_convert(attr_value, conversion)

            self._attributes[key] = self._round(attr_value)

        # Add some other string attributes
        self._attributes[ATTR_QUOTE_TYPE] = symbol_data[DATA_QUOTE_TYPE]
        self._attributes[ATTR_QUOTE_SOURCE_NAME] = symbol_data[DATA_QUOTE_SOURCE_NAME]
        self._attributes[ATTR_MARKET_STATE] = symbol_data[DATA_MARKET_STATE]

        # Use target_currency if we have conversion data. Otherwise keep using the
        # currency from data.
        if conversion is not None:
            currency = self._target_currency or self._original_currency
        else:
            currency = self._original_currency

        self._currency = currency.upper()
        lower_currency = self._currency.lower()

        trending_state = self._calc_trending_state()

        # Fall back to currency based icon if there is no trending state
        if trending_state is not None:
            self._attributes[ATTR_TRENDING] = trending_state

            if self._show_trending_icon:
                self._icon = f"mdi:trending-{trending_state}"
            else:
                self._icon = f"mdi:currency-{lower_currency}"
        else:
            self._icon = f"mdi:currency-{lower_currency}"

        # If this one of the known currencies, then include the correct currency symbol.
        # Don't show $ as the CurrencySymbol even if we can't get one.
        self._attributes[ATTR_CURRENCY_SYMBOL] = CURRENCY_CODES.get(lower_currency)

    def _calc_trending_state(self):
        """Return the trending state for the symbol."""
        if self._market_price is None or self._previous_close is None:
            return None

        if self._market_price > self._previous_close:
            return "up"
        if self._market_price < self._previous_close:
            return "down"

        return "neutral"

    @property
    def available(self) -> bool:
        """Return if entity is available."""

        current_timer = timer()

        # Limit data update if available was invoked within 400 ms.
        # This matched the slow entity reporting done in Entity.
        if (self._last_available_timer is None) or (
            (current_timer - self._last_available_timer) > 0.4
        ):
            self._update_properties()
            self._last_available_timer = current_timer

        return self._coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self._coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        self._coordinator.async_remove_listener(self.async_write_ha_state)

    async def async_update(self) -> None:
        """Update symbol data."""
        await self._coordinator.async_request_refresh()
