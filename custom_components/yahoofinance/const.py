"""Constants for Yahoo Finance sensor."""

# Additional attributes exposed by the sensor
ATTR_CURRENCY_SYMBOL = "currencySymbol"
ATTR_QUOTE_TYPE = "quoteType"
ATTR_QUOTE_SOURCE_NAME = "quoteSourceName"
ATTR_SYMBOL = "symbol"
ATTR_TRENDING = "trending"
ATTR_MARKET_STATE = "marketState"

# Hass data
HASS_DATA_CONFIG = "config"
HASS_DATA_COORDINATOR = "coordinator"

# JSON data pieces
DATA_CURRENCY_SYMBOL = "currency"
DATA_FINANCIAL_CURRENCY = "financialCurrency"
DATA_QUOTE_TYPE = "quoteType"
DATA_QUOTE_SOURCE_NAME = "quoteSourceName"
DATA_SHORT_NAME = "shortName"
DATA_MARKET_STATE = "marketState"

DATA_REGULAR_MARKET_PREVIOUS_CLOSE = "regularMarketPreviousClose"
DATA_REGULAR_MARKET_PRICE = "regularMarketPrice"

CONF_DECIMAL_PLACES = "decimal_places"
CONF_INCLUDE_FIFTY_DAY_VALUES = "include_fifty_day_values"
CONF_INCLUDE_POST_VALUES = "include_post_values"
CONF_INCLUDE_PRE_VALUES = "include_pre_values"
CONF_INCLUDE_TWO_HUNDRED_DAY_VALUES = "include_two_hundred_day_values"
CONF_SHOW_TRENDING_ICON = "show_trending_icon"
CONF_TARGET_CURRENCY = "target_currency"

DEFAULT_CONF_DECIMAL_PLACES = 2
DEFAULT_CONF_INCLUDE_FIFTY_DAY_VALUES = True
DEFAULT_CONF_INCLUDE_POST_VALUES = True
DEFAULT_CONF_INCLUDE_PRE_VALUES = True
DEFAULT_CONF_INCLUDE_TWO_HUNDRED_DAY_VALUES = True
DEFAULT_CONF_SHOW_TRENDING_ICON = False

DEFAULT_NUMERIC_DATA_GROUP = "default"

# Data keys grouped into categories. The values for the categories (except for DEFAULT_NUMERIC_DATA_GROUP)
# can be conditionally pulled into attributes. The first value of the set is the key and the second
# boolean value indicates if the attribute is a currency.
NUMERIC_DATA_GROUPS = {
    DEFAULT_NUMERIC_DATA_GROUP: [
        ("averageDailyVolume10Day", False),
        ("averageDailyVolume3Month", False),
        ("regularMarketChange", True),
        ("regularMarketChangePercent", False),
        ("regularMarketDayHigh", True),
        ("regularMarketDayLow", True),
        (DATA_REGULAR_MARKET_PREVIOUS_CLOSE, True),
        (DATA_REGULAR_MARKET_PRICE, True),
        ("regularMarketVolume", False),
        ("regularMarketTime", False),
    ],
    CONF_INCLUDE_FIFTY_DAY_VALUES: [
        ("fiftyDayAverage", True),
        ("fiftyDayAverageChange", True),
        ("fiftyDayAverageChangePercent", False),
    ],
    CONF_INCLUDE_PRE_VALUES: [
        ("preMarketChange", True),
        ("preMarketChangePercent", False),
        ("preMarketTime", False),
        ("preMarketPrice", True),
    ],
    CONF_INCLUDE_POST_VALUES: [
        ("postMarketChange", True),
        ("postMarketChangePercent", False),
        ("postMarketPrice", True),
        ("postMarketTime", False),
    ],
    CONF_INCLUDE_TWO_HUNDRED_DAY_VALUES: [
        ("twoHundredDayAverage", True),
        ("twoHundredDayAverageChange", True),
        ("twoHundredDayAverageChangePercent", False),
    ],
}

STRING_DATA_KEYS = [
    DATA_CURRENCY_SYMBOL,
    DATA_FINANCIAL_CURRENCY,
    DATA_QUOTE_TYPE,
    DATA_QUOTE_SOURCE_NAME,
    DATA_SHORT_NAME,
    DATA_MARKET_STATE,
]


ATTRIBUTION = "Data provided by Yahoo Finance"
BASE = "https://query1.finance.yahoo.com/v7/finance/quote?symbols="

CONF_SYMBOLS = "symbols"
DEFAULT_CURRENCY = "USD"
DEFAULT_CURRENCY_SYMBOL = "$"
DEFAULT_ICON = "mdi:currency-usd"
DOMAIN = "yahoofinance"
SERVICE_REFRESH = "refresh_symbols"

CURRENCY_CODES = {
    "bdt": "৳",
    "brl": "R$",
    "btc": "₿",
    "cny": "¥",
    "eth": "Ξ",
    "eur": "€",
    "gbp": "£",
    "ils": "₪",
    "inr": "₹",
    "jpy": "¥",
    "krw": "₩",
    "kzt": "лв",
    "ngn": "₦",
    "php": "₱",
    "rial": "﷼",
    "rub": "₽",
    "sign": "",
    "try": "₺",
    "twd": "$",
    "usd": "$",
}
