import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)

# Configuration:
LANGUAGE = "language"
LANGUAGES = [
    "English",
    "Danish",
    "German",
    "Spanish",
    "French",
    "Italian",
    "Norwegian",
    "Romanian",
    "Swedish",
    "Dutch",
    "Slovak"
]
SIDEPANEL_TITLE = "sidepanel_title"
SIDEPANEL_ICON = "sidepanel_icon"
THEME = "theme"
PRIMARY_COLOR = "primary_color"
THEME_OPTIONS = [
    "Auto Mode (Dark/Light)",
    "Dark Mode",
    "Light Mode",
    "Auto Mode (Black/White)",
    "Black Mode",
    "White Mode",
    "HA selected theme"
]
CUSTOMIZE_PATH = "customize_path"

@config_entries.HANDLERS.register("dwains_dashboard")
class DwainsDashboardConfigFlow(config_entries.ConfigFlow):
    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(title="", data={})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DwainsDashboardEditFlow(config_entry)

class DwainsDashboardEditFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = {
            vol.Optional(LANGUAGE, default=self.config_entry.options.get("language", "English")): vol.In(LANGUAGES),
            vol.Optional(SIDEPANEL_TITLE, default=self.config_entry.options.get("sidepanel_title", "Dwains Dashboard")): str,
            vol.Optional(SIDEPANEL_ICON, default=self.config_entry.options.get("sidepanel_icon", "mdi:alpha-d-box")): str,
            vol.Optional(THEME, default=self.config_entry.options.get("theme", "Auto Mode (Dark/Light)")): vol.In(THEME_OPTIONS),
            vol.Optional(PRIMARY_COLOR, default=self.config_entry.options.get("primary_color", "#299ec2")): str,
            vol.Optional(CUSTOMIZE_PATH, default=self.config_entry.options.get("customize_path", "customize.yaml")): str,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema)
        )
