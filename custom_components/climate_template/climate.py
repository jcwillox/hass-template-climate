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
from homeassistant.core import HomeAssistant, callback
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

    _attr_should_poll = False
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, hass: HomeAssistant, config: ConfigType):
        """Initialize the climate device."""
        super().__init__(
            hass,
            availability_template=config.get(CONF_AVAILABILITY_TEMPLATE),
            icon_template=config.get(CONF_ICON_TEMPLATE),
            entity_picture_template=config.get(CONF_ENTITY_PICTURE_TEMPLATE),
            unique_id=config.get(CONF_UNIQUE_ID, None),
        )
        self.hass = hass
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, config[CONF_NAME], hass=hass
        )

        # set attrs
        self._attr_name = config[CONF_NAME]
        self._attr_min_temp = config[CONF_TEMP_MIN]
        self._attr_max_temp = config[CONF_TEMP_MAX]
        self._attr_target_temperature_step = config[CONF_TEMP_STEP]
        self._attr_temperature_unit = hass.config.units.temperature_unit
        self._attr_hvac_modes = config[CONF_MODE_LIST]
        self._attr_fan_modes = config[CONF_FAN_MODE_LIST]
        self._attr_preset_modes = config[CONF_PRESET_MODE_LIST]
        self._attr_swing_modes = config[CONF_SWING_MODE_LIST]
        # set optimistic default attrs
        self._attr_fan_mode = FAN_LOW
        self._attr_preset_mode = PRESET_COMFORT
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_swing_mode = HVACMode.OFF
        self._attr_target_temperature = DEFAULT_TEMP
        self._attr_target_temperature_high = None
        self._attr_target_temperature_low = None

        if (precision := config.get(CONF_PRECISION)) is not None:
            self._attr_precision = precision

        # set template properties
        self._min_temp_template = config.get(CONF_TEMP_MIN_TEMPLATE)
        self._max_temp_template = config.get(CONF_TEMP_MAX_TEMPLATE)
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

        # set turn on/off features
        if len(self._attr_hvac_modes) >= 2:
            self._attr_supported_features |= ClimateEntityFeature.TURN_ON
        if HVACMode.OFF in self._attr_hvac_modes:
            self._attr_supported_features |= ClimateEntityFeature.TURN_OFF
        elif len(self._attr_hvac_modes) > 1:
            self._attr_supported_features |= ClimateEntityFeature.TURN_OFF

        # set script variables
        self._set_humidity_script = None
        if set_humidity_action := config.get(CONF_SET_HUMIDITY_ACTION):
            self._set_humidity_script = Script(
                hass, set_humidity_action, self._attr_name, DOMAIN
            )
            self._attr_supported_features |= ClimateEntityFeature.TARGET_HUMIDITY

        self._set_hvac_mode_script = None
        if set_hvac_mode_action := config.get(CONF_SET_HVAC_MODE_ACTION):
            self._set_hvac_mode_script = Script(
                hass, set_hvac_mode_action, self._attr_name, DOMAIN
            )

        self._set_swing_mode_script = None
        if set_swing_mode_action := config.get(CONF_SET_SWING_MODE_ACTION):
            self._set_swing_mode_script = Script(
                hass, set_swing_mode_action, self._attr_name, DOMAIN
            )
            self._attr_supported_features |= ClimateEntityFeature.SWING_MODE

        self._set_fan_mode_script = None
        if set_fan_mode_action := config.get(CONF_SET_FAN_MODE_ACTION):
            self._set_fan_mode_script = Script(
                hass, set_fan_mode_action, self._attr_name, DOMAIN
            )
            self._attr_supported_features |= ClimateEntityFeature.FAN_MODE

        self._set_preset_mode_script = None
        if set_preset_mode_action := config.get(CONF_SET_PRESET_MODE_ACTION):
            self._set_preset_mode_script = Script(
                hass, set_preset_mode_action, self._attr_name, DOMAIN
            )
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE

        self._set_temperature_script = None
        if set_temperature_action := config.get(CONF_SET_TEMPERATURE_ACTION):
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
                self._attr_hvac_mode = HVACMode(previous_state.state)

            if temperature := previous_state.attributes.get(
                ATTR_TEMPERATURE, DEFAULT_TEMP
            ):
                self._attr_target_temperature = float(temperature)
            if temperature_high := previous_state.attributes.get(ATTR_TARGET_TEMP_HIGH):
                self._attr_target_temperature_high = float(temperature_high)
            if temperature_low := previous_state.attributes.get(ATTR_TARGET_TEMP_LOW):
                self._attr_target_temperature_low = float(temperature_low)

            self._attr_fan_mode = previous_state.attributes.get(ATTR_FAN_MODE, FAN_LOW)
            self._attr_preset_mode = previous_state.attributes.get(
                ATTR_PRESET_MODE, PRESET_COMFORT
            )
            self._attr_swing_mode = previous_state.attributes.get(
                ATTR_SWING_MODE, HVACMode.OFF
            )

            if current_temperature := previous_state.attributes.get(
                ATTR_CURRENT_TEMPERATURE
            ):
                self._attr_current_temperature = float(current_temperature)

            if humidity := previous_state.attributes.get(ATTR_CURRENT_HUMIDITY):
                self._attr_current_humidity = humidity

            if humidity := previous_state.attributes.get(ATTR_MIN_HUMIDITY):
                self._attr_min_humidity = humidity

            if humidity := previous_state.attributes.get(ATTR_MAX_HUMIDITY):
                self._attr_max_humidity = humidity

            if humidity := previous_state.attributes.get(ATTR_HUMIDITY):
                self._attr_target_humidity = humidity

    @callback
    def _async_setup_templates(self) -> None:
        """Set up templates."""
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
                "_attr_current_temperature",
                self._current_temp_template,
                None,
                self._update_current_temp,
                none_on_template_error=True,
            )

        if self._current_humidity_template:
            self.add_template_attribute(
                "_attr_current_humidity",
                self._current_humidity_template,
                None,
                self._update_current_humidity,
                none_on_template_error=True,
            )

        if self._min_humidity_template:
            self.add_template_attribute(
                "_attr_min_humidity",
                self._min_humidity_template,
                None,
                self._update_min_humidity,
                none_on_template_error=True,
            )

        if self._max_humidity_template:
            self.add_template_attribute(
                "_attr_max_humidity",
                self._max_humidity_template,
                None,
                self._update_max_humidity,
                none_on_template_error=True,
            )

        if self._target_humidity_template:
            self.add_template_attribute(
                "_attr_target_humidity",
                self._target_humidity_template,
                None,
                self._update_target_humidity,
                none_on_template_error=True,
            )

        if self._target_temperature_template:
            self.add_template_attribute(
                "_attr_target_temperature",
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
                "_attr_hvac_mode",
                self._hvac_mode_template,
                None,
                self._update_hvac_mode,
                none_on_template_error=True,
            )
        if self._preset_mode_template:
            self.add_template_attribute(
                "_attr_preset_mode",
                self._preset_mode_template,
                None,
                self._update_preset_mode,
                none_on_template_error=True,
            )

        if self._fan_mode_template:
            self.add_template_attribute(
                "_attr_fan_mode",
                self._fan_mode_template,
                None,
                self._update_fan_mode,
                none_on_template_error=True,
            )

        if self._swing_mode_template:
            self.add_template_attribute(
                "_attr_swing_mode",
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
        super()._async_setup_templates()

    @callback
    def _update_min_temp(self, temp):
        if temp not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._attr_min_temp = float(temp)
            except ValueError:
                _LOGGER.error("Could not parse min temperature from %s", temp)

    @callback
    def _update_max_temp(self, temp):
        if temp not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._attr_max_temp = float(temp)
            except ValueError:
                _LOGGER.error("Could not parse max temperature from %s", temp)

    @callback
    def _update_current_temp(self, temp):
        if temp not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._attr_current_temperature = float(temp)
            except ValueError:
                _LOGGER.error("Could not parse temperature from %s", temp)

    @callback
    def _update_current_humidity(self, humidity):
        if humidity not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._attr_current_humidity = int(humidity)
            except ValueError:
                _LOGGER.error("Could not parse humidity from %s", humidity)

    @callback
    def _update_min_humidity(self, humidity):
        if humidity not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._attr_min_humidity = float(humidity)
            except ValueError:
                _LOGGER.error("Could not parse min humidity from %s", humidity)

    @callback
    def _update_max_humidity(self, humidity):
        if humidity not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._attr_max_humidity = float(humidity)
            except ValueError:
                _LOGGER.error("Could not parse max humidity from %s", humidity)

    @callback
    def _update_target_humidity(self, humidity):
        if humidity not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                new_humidity = float(humidity)
                if (
                    new_humidity != self._attr_target_humidity
                ):  # Only update if there's a change
                    self._attr_target_humidity = new_humidity
                    self.async_write_ha_state()  # Update HA state without triggering an action
            except ValueError:
                _LOGGER.error("Could not parse target humidity from %s", humidity)

    @callback
    def _update_target_temp(self, temp):
        if temp not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                # Update the internal state without triggering the set_temperature action
                new_target_temp = float(temp)
                if (
                    new_target_temp != self._attr_target_temperature
                ):  # Only update if there's a change
                    self._attr_target_temperature = new_target_temp
                    self.async_write_ha_state()  # Update the HA state without triggering an action
            except ValueError:
                _LOGGER.error("Could not parse temperature from %s", temp)

    @callback
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

    @callback
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

    @callback
    def _update_hvac_mode(self, hvac_mode):
        if hvac_mode in self._attr_hvac_modes:
            hvac_mode = HVACMode(hvac_mode) if hvac_mode else None
            if self._attr_hvac_mode != hvac_mode:  # Only update if there's a change
                self._attr_hvac_mode = hvac_mode
                self.async_write_ha_state()  # Update HA state without triggering an action
        elif hvac_mode not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.error(
                "Received invalid hvac mode: %s. Expected: %s.",
                hvac_mode,
                self._attr_hvac_modes,
            )

    @callback
    def _update_preset_mode(self, preset_mode):
        if preset_mode in self._attr_preset_modes:
            if self._attr_preset_mode != preset_mode:  # Only update if there's a change
                self._attr_preset_mode = preset_mode
                self.async_write_ha_state()  # Update HA state without triggering an action
        elif preset_mode not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.error(
                "Received invalid preset mode %s. Expected %s.",
                preset_mode,
                self._attr_preset_modes,
            )

    @callback
    def _update_fan_mode(self, fan_mode):
        if fan_mode in self._attr_fan_modes:
            if self._attr_fan_mode != fan_mode:  # Only update if there's a change
                self._attr_fan_mode = fan_mode
                self.async_write_ha_state()  # Update HA state without triggering an action
        elif fan_mode not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.error(
                "Received invalid fan mode: %s. Expected: %s.",
                fan_mode,
                self._attr_fan_modes,
            )

    @callback
    def _update_swing_mode(self, swing_mode):
        if swing_mode in self._attr_swing_modes:
            if self._attr_swing_mode != swing_mode:  # Only update if there's a change
                self._attr_swing_mode = swing_mode
                self.async_write_ha_state()  # Update HA state without triggering an action
        elif swing_mode not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.error(
                "Received invalid swing mode: %s. Expected: %s.",
                swing_mode,
                self._attr_swing_modes,
            )

    @callback
    def _update_hvac_action(self, hvac_action):
        if hvac_action in HVACAction or hvac_action is None:
            if self._attr_hvac_action != hvac_action:  # Only update if there's a change
                self._attr_hvac_action = hvac_action
                self.async_write_ha_state()  # Update HA state without triggering an action
        elif hvac_action not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.error(
                "Received invalid hvac action: %s. Expected: %s.",
                hvac_action,
                [str(member) for member in HVACAction],
            )

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return (
            self._attr_target_temperature
            if self._attr_hvac_mode != HVACMode.HEAT_COOL
            else None
        )

    @property
    def target_temperature_high(self):
        """Return the temperature high we try to reach."""
        return (
            self._attr_target_temperature_high
            if self._attr_hvac_mode == HVACMode.HEAT_COOL
            else None
        )

    @property
    def target_temperature_low(self):
        """Return the temperature low we try to reach."""
        return (
            self._attr_target_temperature_low
            if self._attr_hvac_mode == HVACMode.HEAT_COOL
            else None
        )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new operation mode."""
        if self._hvac_mode_template is None:
            self._attr_hvac_mode = hvac_mode  # always optimistic
            self.async_write_ha_state()

        if self._set_hvac_mode_script:
            await self.async_run_script(
                self._set_hvac_mode_script,
                run_variables={ATTR_HVAC_MODE: hvac_mode},
                context=self._context,
            )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if self._preset_mode_template is None:
            self._attr_preset_mode = preset_mode
            self.async_write_ha_state()

        if self._set_preset_mode_script:
            await self.async_run_script(
                self._set_preset_mode_script,
                run_variables={ATTR_PRESET_MODE: preset_mode},
                context=self._context,
            )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        if self._fan_mode_template is None:
            self._attr_fan_mode = fan_mode  # always optimistic
            self.async_write_ha_state()

        if self._set_fan_mode_script:
            await self.async_run_script(
                self._set_fan_mode_script,
                run_variables={ATTR_FAN_MODE: fan_mode},
                context=self._context,
            )

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new swing mode."""
        if self._swing_mode_template is None:  # use optimistic mode
            self._attr_swing_mode = swing_mode
            self.async_write_ha_state()

        if self._set_swing_mode_script:
            await self.async_run_script(
                self._set_swing_mode_script,
                run_variables={ATTR_SWING_MODE: swing_mode},
                context=self._context,
            )

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature explicitly triggered by user or automation."""
        updated = False

        if kwargs.get(ATTR_HVAC_MODE, self._attr_hvac_mode) == HVACMode.HEAT_COOL:
            # Explicitly update high and low target temperatures if provided
            high_temp = kwargs.get(ATTR_TARGET_TEMP_HIGH)
            low_temp = kwargs.get(ATTR_TARGET_TEMP_LOW)

            if (
                high_temp is not None
                and high_temp != self._attr_target_temperature_high
            ):
                self._attr_target_temperature_high = high_temp
                updated = True

            if low_temp is not None and low_temp != self._attr_target_temperature_low:
                self._attr_target_temperature_low = low_temp
                updated = True

        else:
            # Explicitly update single target temperature if provided
            temp = kwargs.get(ATTR_TEMPERATURE)
            if temp is not None and temp != self._attr_target_temperature:
                self._attr_target_temperature = temp
                updated = True

        # Update Home Assistant state if any changes occurred
        if updated:
            self.async_write_ha_state()

        # Handle potential HVAC mode change
        if operation_mode := kwargs.get(ATTR_HVAC_MODE):
            operation_mode = HVACMode(operation_mode) if operation_mode else None
            if operation_mode != self._attr_hvac_mode:
                await self.async_set_hvac_mode(operation_mode)

        # Run the set temperature script if defined
        if self._set_temperature_script:
            await self.async_run_script(
                self._set_temperature_script,
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
        if self._target_humidity_template is None:
            self._attr_target_humidity = humidity  # always optimistic
            self.async_write_ha_state()

        if self._set_humidity_script:
            await self.async_run_script(
                self._set_humidity_script,
                run_variables={ATTR_HUMIDITY: humidity},
                context=self._context,
            )
