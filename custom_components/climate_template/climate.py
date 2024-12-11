"""Support for Template climates."""

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    ENTITY_ID_FORMAT,
)
from homeassistant.components.climate.const import (
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    ATTR_MIN_TEMP,
    ATTR_MAX_TEMP,
    ATTR_HVAC_MODE,
    ATTR_FAN_MODE,
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_CURRENT_HUMIDITY,
    ATTR_MIN_HUMIDITY,
    ATTR_MAX_HUMIDITY,
    ATTR_HUMIDITY,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    PRESET_ACTIVITY,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_HOME,
    PRESET_SLEEP,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    HVACMode,
    HVACAction,
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
    CONF_UNIQUE_ID,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.script import Script
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

CONF_FAN_MODE_LIST = "fan_modes"
CONF_PRESET_MODE_LIST = "preset_modes"
CONF_MODE_LIST = "modes"
CONF_SWING_MODE_LIST = "swing_modes"
CONF_TEMP_MIN_TEMPLATE = "min_temp_template"
CONF_TEMP_MIN = "min_temp"
CONF_TEMP_MAX_TEMPLATE = "max_temp_template"
CONF_TEMP_MAX = "max_temp"
CONF_PRECISION = "precision"
CONF_CURRENT_TEMP_TEMPLATE = "current_temperature_template"
CONF_TEMP_STEP = "temp_step"

CONF_CURRENT_HUMIDITY_TEMPLATE = "current_humidity_template"
CONF_MIN_HUMIDITY_TEMPLATE = "min_humidity_template"
CONF_MAX_HUMIDITY_TEMPLATE = "max_humidity_template"
CONF_TARGET_HUMIDITY_TEMPLATE = "target_humidity_template"
CONF_TARGET_TEMPERATURE_TEMPLATE = "target_temperature_template"
CONF_TARGET_TEMPERATURE_HIGH_TEMPLATE = "target_temperature_high_template"
CONF_TARGET_TEMPERATURE_LOW_TEMPLATE = "target_temperature_low_template"
CONF_HVAC_MODE_TEMPLATE = "hvac_mode_template"
CONF_FAN_MODE_TEMPLATE = "fan_mode_template"
CONF_PRESET_MODE_TEMPLATE = "preset_mode_template"
CONF_SWING_MODE_TEMPLATE = "swing_mode_template"
CONF_HVAC_ACTION_TEMPLATE = "hvac_action_template"

CONF_SET_HUMIDITY_ACTION = "set_humidity"
CONF_SET_TEMPERATURE_ACTION = "set_temperature"
CONF_SET_HVAC_MODE_ACTION = "set_hvac_mode"
CONF_SET_FAN_MODE_ACTION = "set_fan_mode"
CONF_SET_PRESET_MODE_ACTION = "set_preset_mode"
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
        vol.Optional(CONF_MIN_HUMIDITY_TEMPLATE): cv.template,
        vol.Optional(CONF_MAX_HUMIDITY_TEMPLATE): cv.template,
        vol.Optional(CONF_TARGET_HUMIDITY_TEMPLATE): cv.template,
        vol.Optional(CONF_TARGET_TEMPERATURE_TEMPLATE): cv.template,
        vol.Optional(CONF_TARGET_TEMPERATURE_HIGH_TEMPLATE): cv.template,
        vol.Optional(CONF_TARGET_TEMPERATURE_LOW_TEMPLATE): cv.template,
        vol.Optional(CONF_HVAC_MODE_TEMPLATE): cv.template,
        vol.Optional(CONF_FAN_MODE_TEMPLATE): cv.template,
        vol.Optional(CONF_PRESET_MODE_TEMPLATE): cv.template,
        vol.Optional(CONF_SWING_MODE_TEMPLATE): cv.template,
        vol.Optional(CONF_HVAC_ACTION_TEMPLATE): cv.template,
        vol.Optional(CONF_SET_HUMIDITY_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_TEMPERATURE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_HVAC_MODE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_FAN_MODE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_PRESET_MODE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_SWING_MODE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(
            CONF_MODE_LIST,
            default=[
                HVACMode.AUTO,
                HVACMode.OFF,
                HVACMode.COOL,
                HVACMode.HEAT,
                HVACMode.DRY,
                HVACMode.FAN_ONLY,
            ],
        ): cv.ensure_list,
        vol.Optional(
            CONF_FAN_MODE_LIST,
            default=[FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH],
        ): cv.ensure_list,
        vol.Optional(
            CONF_PRESET_MODE_LIST,
            default=[
                PRESET_ECO,
                PRESET_AWAY,
                PRESET_BOOST,
                PRESET_COMFORT,
                PRESET_HOME,
                PRESET_SLEEP,
                PRESET_ACTIVITY,
            ],
        ): cv.ensure_list,
        vol.Optional(
            CONF_SWING_MODE_LIST, default=[STATE_ON, HVACMode.OFF]
        ): cv.ensure_list,
        vol.Optional(CONF_TEMP_MIN_TEMPLATE): cv.template,
        vol.Optional(CONF_TEMP_MIN, default=DEFAULT_MIN_TEMP): vol.Coerce(float),
        vol.Optional(CONF_TEMP_MAX_TEMPLATE): cv.template,
        vol.Optional(CONF_TEMP_MAX, default=DEFAULT_MAX_TEMP): vol.Coerce(float),
        vol.Optional(CONF_PRECISION): vol.In(
            [PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE]
        ),
        vol.Optional(CONF_TEMP_STEP, default=DEFAULT_PRECISION): vol.Coerce(float),
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistant, config: ConfigType, async_add_entities, discovery_info=None
):
    """Set up the Template Climate."""
    async_add_entities([TemplateClimate(hass, config)])


class TemplateClimate(TemplateEntity, ClimateEntity, RestoreEntity):
    """A template climate component."""

    def __init__(self, hass: HomeAssistant, config: ConfigType):
        """Initialize the climate device."""
        super().__init__(
            hass,
            availability_template=config.get(CONF_AVAILABILITY_TEMPLATE),
            icon_template=config.get(CONF_ICON_TEMPLATE),
            entity_picture_template=config.get(CONF_ENTITY_PICTURE_TEMPLATE),
        )
        self._config = config
        self._attr_unique_id = config.get(CONF_UNIQUE_ID, None)
        self._attr_name = config[CONF_NAME]
        self._min_temp_template = config.get(CONF_TEMP_MIN_TEMPLATE)
        self._attr_min_temp = config[CONF_TEMP_MIN]
        self._max_temp_template = config.get(CONF_TEMP_MAX_TEMPLATE)
        self._attr_max_temp = config[CONF_TEMP_MAX]
        self._attr_target_temperature_step = config[CONF_TEMP_STEP]

        self._current_temp = None
        self._current_humidity = None
        self._min_humidity = None
        self._max_humidity = None
        self._target_humidity = None

        self._current_fan_mode = FAN_LOW  # default optimistic state
        self._current_preset_mode = PRESET_COMFORT  # default optimistic state
        self._current_operation = HVACMode.OFF  # default optimistic state
        self._current_swing_mode = HVACMode.OFF  # default optimistic state
        self._target_temp = DEFAULT_TEMP  # default optimistic state
        self._attr_target_temperature_high = None
        self._attr_target_temperature_low = None

        self._current_temp_template = config.get(CONF_CURRENT_TEMP_TEMPLATE)
        self._current_humidity_template = config.get(CONF_CURRENT_HUMIDITY_TEMPLATE)
        self._min_humidity_template = config.get(CONF_MIN_HUMIDITY_TEMPLATE)
        self._max_humidity_template = config.get(CONF_MAX_HUMIDITY_TEMPLATE)
        self._target_humidity_template = config.get(CONF_TARGET_HUMIDITY_TEMPLATE)
        self._target_temperature_template = config.get(CONF_TARGET_TEMPERATURE_TEMPLATE)
        self._target_temperature_high_template = config.get(
            CONF_TARGET_TEMPERATURE_HIGH_TEMPLATE
        )
        self._target_temperature_low_template = config.get(
            CONF_TARGET_TEMPERATURE_LOW_TEMPLATE
        )
        self._hvac_mode_template = config.get(CONF_HVAC_MODE_TEMPLATE)
        self._fan_mode_template = config.get(CONF_FAN_MODE_TEMPLATE)
        self._preset_mode_template = config.get(CONF_PRESET_MODE_TEMPLATE)
        self._swing_mode_template = config.get(CONF_SWING_MODE_TEMPLATE)
        self._hvac_action_template = config.get(CONF_HVAC_ACTION_TEMPLATE)

        self._available = True
        self._unit_of_measurement = hass.config.units.temperature_unit
        self._attr_supported_features = 0

        if not hasattr(ClimateEntityFeature, "ON_OFF"):
            ON_OFF_FEATURE = 1 << 8
        else:
            ON_OFF_FEATURE = ClimateEntityFeature.ON_OFF

        if HVACMode.OFF in config[CONF_MODE_LIST] and len(config[CONF_MODE_LIST]) > 1:
            self._attr_supported_features |= ON_OFF_FEATURE

        self._attr_hvac_modes = config[CONF_MODE_LIST]
        self._attr_fan_modes = config[CONF_FAN_MODE_LIST]
        self._attr_preset_modes = config[CONF_PRESET_MODE_LIST]
        self._swing_modes_list = config[CONF_SWING_MODE_LIST]

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, config[CONF_NAME], hass=hass
        )

        # set script variables
        self._set_humidity_script = None
        set_humidity_action = config.get(CONF_SET_HUMIDITY_ACTION)
        if set_humidity_action:
            self._set_humidity_script = Script(
                hass, set_humidity_action, self._attr_name, DOMAIN
            )
            self._attr_supported_features |= ClimateEntityFeature.TARGET_HUMIDITY

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
            self._attr_supported_features |= ClimateEntityFeature.SWING_MODE

        self._set_fan_mode_script = None
        set_fan_mode_action = config.get(CONF_SET_FAN_MODE_ACTION)
        if set_fan_mode_action:
            self._set_fan_mode_script = Script(
                hass, set_fan_mode_action, self._attr_name, DOMAIN
            )
            self._attr_supported_features |= ClimateEntityFeature.FAN_MODE

        self._set_preset_mode_script = None
        set_preset_mode_action = config.get(CONF_SET_PRESET_MODE_ACTION)
        if set_preset_mode_action:
            self._set_preset_mode_script = Script(
                hass, set_preset_mode_action, self._attr_name, DOMAIN
            )
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE

        self._set_temperature_script = None
        set_temperature_action = config.get(CONF_SET_TEMPERATURE_ACTION)
        if set_temperature_action:
            self._set_temperature_script = Script(
                hass, set_temperature_action, self._attr_name, DOMAIN
            )
            if HVACMode.HEAT_COOL in self._attr_hvac_modes:
                self._attr_supported_features |= (
                    ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
                )
                if HVACMode.OFF in self._attr_hvac_modes:
                    if len(self._attr_hvac_modes) > 2:
                        # when heat_cool and off are not the only modes
                        self._attr_supported_features |= (
                            ClimateEntityFeature.TARGET_TEMPERATURE
                        )
                elif len(self._attr_hvac_modes) > 1:
                    # when heat_cool is not the only mode
                    self._attr_supported_features |= (
                        ClimateEntityFeature.TARGET_TEMPERATURE
                    )
            else:
                self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Check If we have an old state
        previous_state = await self.async_get_last_state()
        if previous_state is not None:
            if self._min_temp_template:
                if min_temp := previous_state.attributes.get(ATTR_MIN_TEMP):
                    self._attr_min_temp = min_temp

            if self._max_temp_template:
                if max_temp := previous_state.attributes.get(ATTR_MAX_TEMP):
                    self._attr_max_temp = max_temp

            if previous_state.state in self._attr_hvac_modes:
                self._current_operation = previous_state.state

            if temperature := previous_state.attributes.get(
                ATTR_TEMPERATURE, DEFAULT_TEMP
            ):
                self._target_temp = float(temperature)
            if temperature_high := previous_state.attributes.get(ATTR_TARGET_TEMP_HIGH):
                self._attr_target_temperature_high = float(temperature_high)
            if temperature_low := previous_state.attributes.get(ATTR_TARGET_TEMP_LOW):
                self._attr_target_temperature_low = float(temperature_low)

            self._current_fan_mode = previous_state.attributes.get(
                ATTR_FAN_MODE, FAN_LOW
            )
            self._current_preset_mode = previous_state.attributes.get(
                ATTR_PRESET_MODE, PRESET_COMFORT
            )
            self._current_swing_mode = previous_state.attributes.get(
                ATTR_SWING_MODE, HVACMode.OFF
            )

            if current_temperature := previous_state.attributes.get(
                ATTR_CURRENT_TEMPERATURE
            ):
                self._current_temp = float(current_temperature)

            if humidity := previous_state.attributes.get(ATTR_CURRENT_HUMIDITY):
                self._current_humidity = humidity

            if humidity := previous_state.attributes.get(ATTR_MIN_HUMIDITY):
                self._min_humidity = humidity

            if humidity := previous_state.attributes.get(ATTR_MAX_HUMIDITY):
                self._max_humidity = humidity

            if humidity := previous_state.attributes.get(ATTR_HUMIDITY):
                self._target_humidity = humidity

        # register templates
        if self._min_temp_template:
            self.add_template_attribute(
                "_attr_min_temp",
                self._min_temp_template,
                None,
                self._update_min_temp,
                none_on_template_error=True,
            )

        if self._max_temp_template:
            self.add_template_attribute(
                "_attr_max_temp",
                self._max_temp_template,
                None,
                self._update_max_temp,
                none_on_template_error=True,
            )

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

        if self._min_humidity_template:
            self.add_template_attribute(
                "_min_humidity",
                self._min_humidity_template,
                None,
                self._update_min_humidity,
                none_on_template_error=True,
            )

        if self._max_humidity_template:
            self.add_template_attribute(
                "_max_humidity",
                self._max_humidity_template,
                None,
                self._update_max_humidity,
                none_on_template_error=True,
            )

        if self._target_humidity_template:
            self.add_template_attribute(
                "_target_humidity",
                self._target_humidity_template,
                None,
                self._update_target_humidity,
                none_on_template_error=True,
            )

        if self._target_temperature_template:
            self.add_template_attribute(
                "_target_temp",
                self._target_temperature_template,
                None,
                self._update_target_temp,
                none_on_template_error=True,
            )

        if self._target_temperature_high_template:
            self.add_template_attribute(
                "_attr_target_temperature_high",
                self._target_temperature_high_template,
                None,
                self._update_target_temp_high,
                none_on_template_error=True,
            )

        if self._target_temperature_low_template:
            self.add_template_attribute(
                "_attr_target_temperature_low",
                self._target_temperature_low_template,
                None,
                self._update_target_temp_low,
                none_on_template_error=True,
            )

        if self._hvac_mode_template:
            self.add_template_attribute(
                "_current_operation",
                self._hvac_mode_template,
                None,
                self._update_hvac_mode,
                none_on_template_error=True,
            )
        if self._preset_mode_template:
            self.add_template_attribute(
                "_current_preset_mode",
                self._preset_mode_template,
                None,
                self._update_preset_mode,
                none_on_template_error=True,
            )

        if self._fan_mode_template:
            self.add_template_attribute(
                "_current_fan_mode",
                self._fan_mode_template,
                None,
                self._update_fan_mode,
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

        if self._hvac_action_template:
            self.add_template_attribute(
                "_hvac_action",
                self._hvac_action_template,
                None,
                self._update_hvac_action,
                none_on_template_error=True,
            )

    def _update_min_temp(self, temp):
        if temp not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._attr_min_temp = float(temp)
            except ValueError:
                _LOGGER.error("Could not parse min temperature from %s", temp)

    def _update_max_temp(self, temp):
        if temp not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._attr_max_temp = float(temp)
            except ValueError:
                _LOGGER.error("Could not parse max temperature from %s", temp)

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

    def _update_min_humidity(self, humidity):
        if humidity not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._min_humidity = float(humidity)
            except ValueError:
                _LOGGER.error("Could not parse min humidity from %s", humidity)

    def _update_max_humidity(self, humidity):
        if humidity not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._max_humidity = float(humidity)
            except ValueError:
                _LOGGER.error("Could not parse max humidity from %s", humidity)

    def _update_target_humidity(self, humidity):
        if humidity not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                new_humidity = float(humidity)
                if new_humidity != self._target_humidity:  # Only update if there's a change
                    self._target_humidity = new_humidity
                    self.async_write_ha_state()  # Update HA state without triggering an action
            except ValueError:
                _LOGGER.error("Could not parse target humidity from %s", humidity)

    def _update_target_temp(self, temp):
        if temp not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                # Update the internal state without triggering the set_temperature action
                new_target_temp = float(temp)
                if new_target_temp != self._target_temp:  # Only update if there's a change
                    self._target_temp = new_target_temp
                    self.async_write_ha_state()  # Update the HA state without triggering an action
            except ValueError:
                _LOGGER.error("Could not parse temperature from %s", temp)

    def _update_target_temp_high(self, temp):
        if temp not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                # Update the internal state without triggering the set_temperature action
                new_target_temp_high = float(temp)
                if new_target_temp_high != self._attr_target_temperature_high:
                    self._attr_target_temperature_high = new_target_temp_high
                    self.async_write_ha_state()
            except ValueError:
                _LOGGER.error("Could not parse temperature high from %s", temp)

    def _update_target_temp_low(self, temp):
        if temp not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                # Update the internal state without triggering the set_temperature action
                new_target_temp_low = float(temp)
                if new_target_temp_low != self._attr_target_temperature_low:
                    self._attr_target_temperature_low = new_target_temp_low
                    self.async_write_ha_state()
            except ValueError:
                _LOGGER.error("Could not parse temperature low from %s", temp)

    def _update_hvac_mode(self, hvac_mode):
        if hvac_mode in self._attr_hvac_modes:
            if self._current_operation != hvac_mode:  # Only update if there's a change
                self._current_operation = hvac_mode
                self.async_write_ha_state()  # Update HA state without triggering an action
        elif hvac_mode not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.error(
                "Received invalid hvac mode: %s. Expected: %s.",
                hvac_mode,
                self._attr_hvac_modes,
            )

    def _update_preset_mode(self, preset_mode):
        if preset_mode in self._attr_preset_modes:
            if self._current_preset_mode != preset_mode:  # Only update if there's a change
                self._current_preset_mode = preset_mode
                self.async_write_ha_state()  # Update HA state without triggering an action
        elif preset_mode not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.error(
                "Received invalid preset mode %s. Expected %s.",
                preset_mode,
                self._attr_preset_modes,
            )

    def _update_fan_mode(self, fan_mode):
        if fan_mode in self._attr_fan_modes:
            if self._current_fan_mode != fan_mode:  # Only update if there's a change
                self._current_fan_mode = fan_mode
                self.async_write_ha_state()  # Update HA state without triggering an action
        elif fan_mode not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.error(
                "Received invalid fan mode: %s. Expected: %s.",
                fan_mode,
                self._attr_fan_modes,
            )

    def _update_swing_mode(self, swing_mode):
        if swing_mode in self._swing_modes_list:
            if self._current_swing_mode != swing_mode:  # Only update if there's a change
                self._current_swing_mode = swing_mode
                self.async_write_ha_state()  # Update HA state without triggering an action
        elif swing_mode not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.error(
                "Received invalid swing mode: %s. Expected: %s.",
                swing_mode,
                self._swing_modes_list,
            )

    def _update_hvac_action(self, hvac_action):
        if hvac_action in [member.value for member in HVACAction] or hvac_action is None:
            if self._attr_hvac_action != hvac_action:  # Only update if there's a change
                self._attr_hvac_action = hvac_action
                self.async_write_ha_state()  # Update HA state without triggering an action
        elif hvac_action not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.error(
                "Received invalid hvac action: %s. Expected: %s.",
                hvac_action,
                [member.value for member in HVACAction],
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
    def min_humidity(self):
        """Return the min humidity."""
        return self._min_humidity

    @property
    def max_humidity(self):
        """Return the max humidity."""
        return self._max_humidity

    @property
    def target_humidity(self):
        """Return the target humidity."""
        return self._target_humidity

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return (
            self._target_temp if self._current_operation != HVACMode.HEAT_COOL else None
        )

    @property
    def target_temperature_high(self):
        """Return the temperature high we try to reach."""
        return (
            self._attr_target_temperature_high
            if self._current_operation == HVACMode.HEAT_COOL
            else None
        )

    @property
    def target_temperature_low(self):
        """Return the temperature low we try to reach."""
        return (
            self._attr_target_temperature_low
            if self._current_operation == HVACMode.HEAT_COOL
            else None
        )

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        return self._current_operation

    @property
    def preset_mode(self):
        """Return preset setting"""
        return self._current_preset_mode

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

    async def async_turn_on(self):
        """Turn the climate device on."""
        if HVACMode.OFF in self._attr_hvac_modes:
            self._current_operation = next(
                mode for mode in self._attr_hvac_modes if mode != HVACMode.OFF
            )
            self.async_write_ha_state()

    async def async_turn_off(self):
        """Turn the climate device off."""
        if HVACMode.OFF in self._attr_hvac_modes:
            self._current_operation = HVACMode.OFF
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new operation mode."""
        if hvac_mode != self._current_operation:  # Only proceed if there's a change
            self._current_operation = hvac_mode
            if self._set_hvac_mode_script is not None:
                await self._set_hvac_mode_script.async_run(
                    run_variables={ATTR_HVAC_MODE: hvac_mode}, context=self._context
                )
            self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode != self._current_preset_mode:  # Only proceed if there's a change
            self._current_preset_mode = preset_mode
            if self._set_preset_mode_script is not None:
                await self._set_preset_mode_script.async_run(
                    run_variables={ATTR_PRESET_MODE: preset_mode}, context=self._context
                )
            self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        if fan_mode != self._current_fan_mode:  # Only proceed if there's a change
            self._current_fan_mode = fan_mode
            if self._set_fan_mode_script is not None:
                await self._set_fan_mode_script.async_run(
                    run_variables={ATTR_FAN_MODE: fan_mode}, context=self._context
                )
            self.async_write_ha_state()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new swing mode."""
        if swing_mode != self._current_swing_mode:  # Only proceed if there's a change
            self._current_swing_mode = swing_mode
            if self._set_swing_mode_script is not None:
                await self._set_swing_mode_script.async_run(
                    run_variables={ATTR_SWING_MODE: swing_mode}, context=self._context
                )
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature explicitly triggered by user or automation."""
        updated = False

        if kwargs.get(ATTR_HVAC_MODE, self._current_operation) == HVACMode.HEAT_COOL:
            # Explicitly update high and low target temperatures if provided
            high_temp = kwargs.get(ATTR_TARGET_TEMP_HIGH)
            low_temp = kwargs.get(ATTR_TARGET_TEMP_LOW)

            if high_temp is not None and high_temp != self._attr_target_temperature_high:
                self._attr_target_temperature_high = high_temp
                updated = True

            if low_temp is not None and low_temp != self._attr_target_temperature_low:
                self._attr_target_temperature_low = low_temp
                updated = True

        else:
            # Explicitly update single target temperature if provided
            temp = kwargs.get(ATTR_TEMPERATURE)
            if temp is not None and temp != self._target_temp:
                self._target_temp = temp
                updated = True

        # Update Home Assistant state if any changes occurred
        if updated:
            self.async_write_ha_state()

        # Handle potential HVAC mode change
        if operation_mode := kwargs.get(ATTR_HVAC_MODE):
            if operation_mode != self._current_operation:
                await self.async_set_hvac_mode(operation_mode)

        # Run the set temperature script if defined
        if self._set_temperature_script is not None:
            await self._set_temperature_script.async_run(
                run_variables={
                    ATTR_TEMPERATURE: kwargs.get(ATTR_TEMPERATURE),
                    ATTR_TARGET_TEMP_HIGH: kwargs.get(ATTR_TARGET_TEMP_HIGH),
                    ATTR_TARGET_TEMP_LOW: kwargs.get(ATTR_TARGET_TEMP_LOW),
                    ATTR_HVAC_MODE: kwargs.get(ATTR_HVAC_MODE),
                },
                context=self._context,
            )

    async def async_set_humidity(self, humidity):
        """Set new target humidity."""
        if humidity != self._target_humidity:  # Only proceed if there's a change
            self._target_humidity = humidity
            if self._set_humidity_script is not None:
                await self._set_humidity_script.async_run(
                    run_variables={ATTR_HUMIDITY: humidity}, context=self._context
                )
            self.async_write_ha_state()
