"""Support for Template climates."""

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.climate import ClimateEntity, ENTITY_ID_FORMAT
from homeassistant.components.climate.const import (
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    ATTR_HVAC_MODE,
    ATTR_FAN_MODE,
    ATTR_SWING_MODE,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_CURRENT_HUMIDITY,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
)
from homeassistant.components.template.const import CONF_AVAILABILITY_TEMPLATE
from homeassistant.components.template.template_entity import TemplateEntity
from homeassistant.const import (
    STATE_ON,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    ATTR_TEMPERATURE,
    CONF_NAME,
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
    CONF_ICON_TEMPLATE,
    CONF_ENTITY_PICTURE_TEMPLATE,
)
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.script import Script
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

_LOGGER = logging.getLogger(__name__)

CONF_FAN_MODE_LIST = "fan_modes"
CONF_MODE_LIST = "modes"
CONF_SWING_MODE_LIST = "swing_modes"
CONF_TEMP_MIN = "min_temp"
CONF_TEMP_MAX = "max_temp"
CONF_PRECISION = "precision"
CONF_CURRENT_TEMP_TEMPLATE = "current_temperature_template"
CONF_TEMP_STEP = "temp_step"

CONF_CURRENT_HUMIDITY_TEMPLATE = "current_humidity_template"
CONF_SWING_MODE_TEMPLATE = "swing_mode_template"

CONF_SET_TEMPERATURE_ACTION = "set_temperature"
CONF_SET_HVAC_MODE_ACTION = "set_hvac_mode"
CONF_SET_FAN_MODE_ACTION = "set_fan_mode"
CONF_SET_SWING_MODE_ACTION = "set_swing_mode"

CONF_CLIMATES = "climates"

DEFAULT_NAME = "Template Climate"
DEFAULT_TEMP = 21
DEFAULT_PRECISION = 1.0
DOMAIN = "climate_template"

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_AVAILABILITY_TEMPLATE): cv.template,
        vol.Optional(CONF_ICON_TEMPLATE): cv.template,
        vol.Optional(CONF_ENTITY_PICTURE_TEMPLATE): cv.template,
        vol.Optional(CONF_CURRENT_TEMP_TEMPLATE): cv.template,
        vol.Optional(CONF_CURRENT_HUMIDITY_TEMPLATE): cv.template,
        vol.Optional(CONF_SWING_MODE_TEMPLATE): cv.template,
        vol.Optional(CONF_SET_TEMPERATURE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_HVAC_MODE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_FAN_MODE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_SWING_MODE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(
            CONF_MODE_LIST,
            default=[
                HVAC_MODE_AUTO,
                HVAC_MODE_OFF,
                HVAC_MODE_COOL,
                HVAC_MODE_HEAT,
                HVAC_MODE_DRY,
                HVAC_MODE_FAN_ONLY,
            ],
        ): cv.ensure_list,
        vol.Optional(
            CONF_FAN_MODE_LIST,
            default=[FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH],
        ): cv.ensure_list,
        vol.Optional(
            CONF_SWING_MODE_LIST, default=[STATE_ON, HVAC_MODE_OFF]
        ): cv.ensure_list,
        vol.Optional(CONF_TEMP_MIN, default=DEFAULT_MIN_TEMP): vol.Coerce(float),
        vol.Optional(CONF_TEMP_MAX, default=DEFAULT_MAX_TEMP): vol.Coerce(float),
        vol.Optional(CONF_PRECISION): vol.In(
            [PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE]
        ),
        vol.Optional(CONF_TEMP_STEP, default=DEFAULT_PRECISION): vol.Coerce(float),
        # vol.Optional(CONF_TEMP_INITIAL, default=DEFAULT_TEMP): cv.positive_int,
    }
)


async def async_setup_platform(
    hass: HomeAssistantType, config: ConfigType, async_add_entities, discovery_info=None
):
    """Set up the Template Climate."""
    async_add_entities([TemplateClimate(hass, config)])


class TemplateClimate(TemplateEntity, ClimateEntity, RestoreEntity):
    """A template climate component."""

    def __init__(self, hass: HomeAssistantType, config: ConfigType):
        """Initialize the climate device."""
        super().__init__(
            hass,
            availability_template=config.get(CONF_AVAILABILITY_TEMPLATE),
            icon_template=config.get(CONF_ICON_TEMPLATE),
            entity_picture_template=config.get(CONF_ENTITY_PICTURE_TEMPLATE),
        )
        self._config = config
        self._attr_name = config[CONF_NAME]
        self._attr_min_temp = config[CONF_TEMP_MIN]
        self._attr_max_temp = config[CONF_TEMP_MAX]
        self._attr_target_temperature_step = config[CONF_TEMP_STEP]

        self._current_temp = None
        self._current_humidity = None

        self._current_fan_mode = FAN_LOW  # default optimistic state
        self._current_operation = HVAC_MODE_OFF  # default optimistic state
        self._current_swing_mode = HVAC_MODE_OFF  # default optimistic state
        self._target_temp = DEFAULT_TEMP  # default optimistic state

        self._current_temp_template = config.get(CONF_CURRENT_TEMP_TEMPLATE)
        self._current_humidity_template = config.get(CONF_CURRENT_HUMIDITY_TEMPLATE)
        self._swing_mode_template = config.get(CONF_SWING_MODE_TEMPLATE)

        self._available = True
        self._unit_of_measurement = hass.config.units.temperature_unit
        self._attr_supported_features = 0

        self._attr_hvac_modes = config[CONF_MODE_LIST]
        self._attr_fan_modes = config[CONF_FAN_MODE_LIST]
        self._swing_modes_list = config[CONF_SWING_MODE_LIST]

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, config[CONF_NAME], hass=hass
        )

        # set script variables
        self._set_hvac_mode_script = None
        set_hvac_mode_action = config.get(CONF_SET_HVAC_MODE_ACTION)
        if set_hvac_mode_action:
            self._set_hvac_mode_script = Script(
                hass, set_hvac_mode_action, self._attr_name, DOMAIN
            )

        self._set_swing_mode_script = None
        set_swing_mode_action = config.get(CONF_SET_SWING_MODE_ACTION)
        if set_swing_mode_action:
            self._set_swing_mode_script = Script(
                hass, set_swing_mode_action, self._attr_name, DOMAIN
            )
            self._attr_supported_features |= SUPPORT_SWING_MODE

        self._set_fan_mode_script = None
        set_fan_mode_action = config.get(CONF_SET_FAN_MODE_ACTION)
        if set_fan_mode_action:
            self._set_fan_mode_script = Script(
                hass, set_fan_mode_action, self._attr_name, DOMAIN
            )
            self._attr_supported_features |= SUPPORT_FAN_MODE

        self._set_temperature_script = None
        set_temperature_action = config.get(CONF_SET_TEMPERATURE_ACTION)
        if set_temperature_action:
            self._set_temperature_script = Script(
                hass, set_temperature_action, self._attr_name, DOMAIN
            )
            self._attr_supported_features |= SUPPORT_TARGET_TEMPERATURE

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Check If we have an old state
        previous_state = await self.async_get_last_state()
        if previous_state is not None:
            self._current_operation = previous_state.state
            self._target_temp = float(
                previous_state.attributes.get(ATTR_TEMPERATURE, DEFAULT_TEMP)
            )
            self._current_fan_mode = previous_state.attributes.get(
                ATTR_FAN_MODE, FAN_LOW
            )
            self._current_swing_mode = previous_state.attributes.get(
                ATTR_SWING_MODE, HVAC_MODE_OFF
            )

            if ATTR_CURRENT_TEMPERATURE in previous_state.attributes:
                self._current_temp = float(
                    previous_state.attributes.get(ATTR_CURRENT_TEMPERATURE)
                )

            if ATTR_CURRENT_HUMIDITY in previous_state.attributes:
                self._current_humidity = previous_state.attributes.get(
                    ATTR_CURRENT_HUMIDITY
                )

        # register templates
        if self._current_temp_template:
            self.add_template_attribute(
                "_current_temp",
                self._current_temp_template,
                None,
                self._update_current_temp,
                none_on_template_error=True,
            )

        if self._current_humidity_template:
            self.add_template_attribute(
                "_current_humidity",
                self._current_humidity_template,
                None,
                self._update_current_humidity,
                none_on_template_error=True,
            )

        if self._swing_mode_template:
            self.add_template_attribute(
                "_current_swing_mode",
                self._swing_mode_template,
                None,
                self._update_swing_mode,
                none_on_template_error=True,
            )

    def _update_current_temp(self, temp):
        if temp not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._current_temp = float(temp)
            except ValueError:
                _LOGGER.error("Could not parse temperature from %s", temp)

    def _update_current_humidity(self, humidity):
        if humidity not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._current_humidity = float(humidity)
            except ValueError:
                _LOGGER.error("Could not parse humidity from %s", humidity)

    def _update_swing_mode(self, swing_mode):
        if swing_mode in self._swing_modes_list:
            # check swing mode actually changed
            if self._current_swing_mode != swing_mode:
                self._current_swing_mode = swing_mode
                self.hass.async_create_task(self.async_set_swing_mode(swing_mode))
        elif swing_mode not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.error(
                "Received invalid swing mode: %s. Expected: %s.",
                swing_mode,
                self._swing_modes_list,
            )

    @property
    def precision(self):
        """Return the precision of the system."""
        if self._config.get(CONF_PRECISION) is not None:
            return self._config.get(CONF_PRECISION)
        return super().precision

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temp

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._current_humidity

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temp

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        return self._current_operation

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._current_fan_mode

    @property
    def swing_mode(self):
        """Return the swing setting."""
        return self._current_swing_mode

    @property
    def swing_modes(self):
        """List of available swing modes."""
        return self._swing_modes_list

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new operation mode."""
        self._current_operation = hvac_mode  # always optimistic
        self.async_write_ha_state()

        if self._set_hvac_mode_script is not None:
            await self._set_hvac_mode_script.async_run(context=self._context)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        self._current_fan_mode = fan_mode  # always optimistic
        self.async_write_ha_state()

        if self._set_fan_mode_script is not None:
            await self._set_fan_mode_script.async_run(context=self._context)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new swing mode."""
        if self._swing_mode_template is None:  # use optimistic mode
            self._current_swing_mode = swing_mode
            self.async_write_ha_state()

        if self._set_swing_mode_script is not None:
            await self._set_swing_mode_script.async_run(context=self._context)

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        self._target_temp = kwargs.get(ATTR_TEMPERATURE)  # always optimistic
        self.async_write_ha_state()

        if (
            kwargs.get(ATTR_HVAC_MODE) is not None
        ):  # set temperature calls can contain a new hvac mode.
            operation_mode = kwargs.get(ATTR_HVAC_MODE)
            await self.async_set_hvac_mode(operation_mode)

        if self._set_temperature_script is not None:
            await self._set_temperature_script.async_run(context=self._context)
