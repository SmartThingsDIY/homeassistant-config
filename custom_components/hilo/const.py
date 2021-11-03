from datetime import timedelta

DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)
DEFAULT_LIGHT_AS_SWITCH = False
MIN_SCAN_INTERVAL = timedelta(seconds=15)
LIGHT_AS_SWITCH = "light_as_switch"
DOMAIN = "hilo"
# To prevent issues with automations for people that already deployed
# with the original code, the LightSwitch is dynamically added when
# light_as_switch boolean is enabled in configuration.
LIGHT_CLASSES = ["LightDimmer", "WhiteBulb", "ColorBulb", "LightSwitch"]
HILO_SENSOR_CLASSES = ["SmokeDetector"]
CLIMATE_CLASSES = ["Thermostat"]
SWITCH_CLASSES = ["LightSwitch"]
