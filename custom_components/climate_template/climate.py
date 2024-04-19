"""Support for Template climates."""

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import Context, callback
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    ENTITY_ID_FORMAT,
)
from homeassistant.components.climate.const import (
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_HUMIDITY,
    DEFAULT_MIN_HUMIDITY,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_FAN_MODE,
    ATTR_SWING_MODE,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_CURRENT_HUMIDITY,
    ATTR_HVAC_ACTION,
    ATTR_HUMIDITY,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    FAN_OFF,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    SWING_OFF,
    SWING_ON,
    PRESET_ACTIVITY,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_HOME,
    PRESET_SLEEP,
    HVACMode,
    HVACAction,
)
from homeassistant.components.template.const import CONF_AVAILABILITY_TEMPLATE
from homeassistant.components.template.template_entity import TemplateEntity
from homeassistant.exceptions import TemplateError
from homeassistant.const import (
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
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.script import Script
from homeassistant.helpers.typing import ConfigType, HomeAssistantType


_LOGGER = logging.getLogger(__name__)

CONF_HVAC_MODE_LIST = "hvac_modes"
CONF_PRESET_MODE_LIST = "preset_modes"
CONF_FAN_MODE_LIST = "fan_modes"
CONF_SWING_MODE_LIST = "swing_modes"
CONF_TEMPERATURE_MIN = "min_temp"
CONF_TEMPERATURE_MAX = "max_temp"
CONF_HUMIDITY_MIN = "min_humidity"
CONF_HUMIDITY_MAX = "max_humidity"
CONF_PRECISION = "precision"
CONF_TEMP_STEP = "temp_step"

CONF_CURRENT_TEMPERATURE_TEMPLATE = "current_temperature_template"
CONF_CURRENT_HUMIDITY_TEMPLATE = "current_humidity_template"
CONF_TARGET_TEMPERATURE_TEMPLATE = "target_temperature_template"
CONF_TARGET_TEMPERATURE_HIGH_TEMPLATE = "target_temperature_high_template"
CONF_TARGET_TEMPERATURE_LOW_TEMPLATE = "target_temperature_low_template"
CONF_TARGET_HUMIDITY_TEMPLATE = "target_humidity_template"
CONF_HVAC_MODE_TEMPLATE = "hvac_mode_template"
CONF_FAN_MODE_TEMPLATE = "fan_mode_template"
CONF_PRESET_MODE_TEMPLATE = "preset_mode_template"
CONF_SWING_MODE_TEMPLATE = "swing_mode_template"
CONF_HVAC_ACTION_TEMPLATE = "hvac_action_template"

CONF_SET_TEMPERATURE_ACTION = "set_temperature"
CONF_SET_HUMIDITY_ACTION = "set_humidity"
CONF_SET_HVAC_MODE_ACTION = "set_hvac_mode"
CONF_SET_FAN_MODE_ACTION = "set_fan_mode"
CONF_SET_PRESET_MODE_ACTION = "set_preset_mode"
CONF_SET_SWING_MODE_ACTION = "set_swing_mode"
CONF_MODE_ACTION = "mode_action"
CONF_MAX_ACTION = "max_action"

DEFAULT_NAME = "Template Climate"
DEFAULT_TEMPERATURE = 21
DEFAULT_HUMIDITY = 50
DEFAULT_HVAC_MODE = HVACMode.OFF
DEFAULT_PRESET_MODE = PRESET_COMFORT
DEFAULT_FAN_MODE = FAN_LOW
DEFAULT_SWING_MODE = SWING_OFF
DEFAULT_TEMP_STEP = 1
DEFAULT_MODE_ACTION = "single"
DEFAULT_MAX_ACTION = 1
DOMAIN = "climate_template"

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MODE_ACTION, default=DEFAULT_MODE_ACTION): vol.In(
            ["parallel", "queued", "restart", "single"]
        ),
        vol.Optional(CONF_MAX_ACTION, default=DEFAULT_MAX_ACTION): cv.positive_int,
        vol.Optional(CONF_AVAILABILITY_TEMPLATE): cv.template,
        vol.Optional(CONF_ICON_TEMPLATE): cv.template,
        vol.Optional(CONF_ENTITY_PICTURE_TEMPLATE): cv.template,
        vol.Optional(CONF_CURRENT_TEMPERATURE_TEMPLATE): cv.template,
        vol.Optional(CONF_CURRENT_HUMIDITY_TEMPLATE): cv.template,
        vol.Optional(CONF_TARGET_HUMIDITY_TEMPLATE): cv.template,
        vol.Optional(CONF_TARGET_TEMPERATURE_TEMPLATE): cv.template,
        vol.Optional(CONF_TARGET_TEMPERATURE_HIGH_TEMPLATE): cv.template,
        vol.Optional(CONF_TARGET_TEMPERATURE_LOW_TEMPLATE): cv.template,
        vol.Optional(CONF_HVAC_MODE_TEMPLATE): cv.template,
        vol.Optional(CONF_FAN_MODE_TEMPLATE): cv.template,
        vol.Optional(CONF_PRESET_MODE_TEMPLATE): cv.template,
        vol.Optional(CONF_SWING_MODE_TEMPLATE): cv.template,
        vol.Optional(CONF_HVAC_ACTION_TEMPLATE): cv.template,
        vol.Optional(CONF_SET_TEMPERATURE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_HUMIDITY_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_HVAC_MODE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_FAN_MODE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_PRESET_MODE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_SET_SWING_MODE_ACTION): cv.SCRIPT_SCHEMA,
        vol.Optional(CONF_HVAC_MODE_LIST, default=[]): cv.ensure_list,
        vol.Optional(CONF_PRESET_MODE_LIST, default=[]): cv.ensure_list,
        vol.Optional(CONF_FAN_MODE_LIST, default=[]): cv.ensure_list,
        vol.Optional(CONF_SWING_MODE_LIST, default=[]): cv.ensure_list,
        vol.Optional(CONF_TEMPERATURE_MIN, default=DEFAULT_MIN_TEMP): vol.Coerce(float),
        vol.Optional(CONF_TEMPERATURE_MAX, default=DEFAULT_MAX_TEMP): vol.Coerce(float),
        vol.Optional(CONF_HUMIDITY_MIN, default=DEFAULT_MIN_HUMIDITY): vol.Coerce(
            float
        ),
        vol.Optional(CONF_HUMIDITY_MAX, default=DEFAULT_MAX_HUMIDITY): vol.Coerce(
            float
        ),
        vol.Optional(CONF_PRECISION): vol.In(
            [PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE]
        ),
        vol.Optional(CONF_TEMP_STEP, default=DEFAULT_TEMP_STEP): vol.Coerce(float),
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistantType, config: ConfigType, async_add_entities, discovery_info=None
):
    """Set up the Template Climate."""
    async_add_entities([TemplateClimate(hass, config)])


class TemplateClimate(TemplateEntity, ClimateEntity, RestoreEntity):
    """A template climate component."""

    _attr_should_poll = False

    def __init__(self, hass: HomeAssistantType, config: ConfigType):
        """Initialize the climate device."""
        super().__init__(
            hass,
            availability_template=config.get(CONF_AVAILABILITY_TEMPLATE),
            icon_template=config.get(CONF_ICON_TEMPLATE),
            entity_picture_template=config.get(CONF_ENTITY_PICTURE_TEMPLATE),
        )
        self._config = config
        self._enable_turn_on_off_backwards_compatibility = False

        self._attr_name = config[CONF_NAME]
        self._attr_entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, config[CONF_NAME], hass=hass
        )
        self._attr_unique_id = config.get(CONF_UNIQUE_ID, None)
        self._attr_supported_features = 0
        self._attr_temperature_unit = hass.config.units.temperature_unit
        self._attr_target_temperature_step = config[CONF_TEMP_STEP]
        self._attr_mode_action = config[CONF_MODE_ACTION]
        self._attr_max_action = config[CONF_MAX_ACTION]
        self._attr_min_temp = config[CONF_TEMPERATURE_MIN]
        self._attr_max_temp = config[CONF_TEMPERATURE_MAX]
        self._attr_min_humidity = config[CONF_HUMIDITY_MIN]
        self._attr_max_humidity = config[CONF_HUMIDITY_MAX]
        self._attr_hvac_modes = list(
            map(lambda item: str(item), config[CONF_HVAC_MODE_LIST]),
        )
        self._attr_fan_modes = list(
            map(lambda item: str(item), config[CONF_FAN_MODE_LIST]),
        )
        self._attr_preset_modes = list(
            map(lambda item: str(item), config[CONF_PRESET_MODE_LIST]),
        )
        self._attr_swing_modes = list(
            map(lambda item: str(item), config[CONF_SWING_MODE_LIST]),
        )
        self._attr_current_temperature = None
        self._attr_current_humidity = None
        self._attr_hvac_action = None
        self._attr_hvac_mode = DEFAULT_HVAC_MODE
        self._attr_preset_mode = DEFAULT_PRESET_MODE
        self._attr_fan_mode = DEFAULT_FAN_MODE
        self._attr_swing_mode = DEFAULT_SWING_MODE
        self._attr_target_temperature = DEFAULT_TEMPERATURE
        self._attr_target_temperature_low = DEFAULT_TEMPERATURE
        self._attr_target_temperature_high = DEFAULT_TEMPERATURE
        self._attr_target_humidity = DEFAULT_HUMIDITY

        self._off_mode = {}
        self._last_on_mode = {}

        self._template_hvac_action = config.get(CONF_HVAC_ACTION_TEMPLATE)
        self._template_hvac_mode = config.get(CONF_HVAC_MODE_TEMPLATE)
        self._template_preset_mode = config.get(CONF_PRESET_MODE_TEMPLATE)
        self._template_fan_mode = config.get(CONF_FAN_MODE_TEMPLATE)
        self._template_swing_mode = config.get(CONF_SWING_MODE_TEMPLATE)
        self._template_current_temperature = config.get(
            CONF_CURRENT_TEMPERATURE_TEMPLATE
        )
        self._template_current_humidity = config.get(
            CONF_CURRENT_HUMIDITY_TEMPLATE,
        )
        self._template_target_temperature = config.get(
            CONF_TARGET_TEMPERATURE_TEMPLATE,
        )
        self._template_target_temperature_low = config.get(
            CONF_TARGET_TEMPERATURE_LOW_TEMPLATE,
        )
        self._template_target_temperature_high = config.get(
            CONF_TARGET_TEMPERATURE_HIGH_TEMPLATE,
        )
        self._template_target_humidity = config.get(CONF_TARGET_HUMIDITY_TEMPLATE)

        self._action_hvac_mode = config.get(CONF_SET_HVAC_MODE_ACTION)
        self._action_preset_mode = config.get(CONF_SET_PRESET_MODE_ACTION)
        self._action_fan_mode = config.get(CONF_SET_FAN_MODE_ACTION)
        self._action_swing_mode = config.get(CONF_SET_SWING_MODE_ACTION)
        self._action_temperature = config.get(CONF_SET_TEMPERATURE_ACTION)
        self._action_humidity = config.get(CONF_SET_HUMIDITY_ACTION)

        # Set scripts callbacks.
        self._script_hvac_mode = None
        self._script_preset_mode = None
        self._script_fan_mode = None
        self._script_swing_mode = None
        self._script_temperature = None
        self._script_humidity = None

        # Check config entries and set entity supported features flags.
        if self._attr_hvac_modes and len(self._attr_hvac_modes) > 0:
            if (
                HVACMode.OFF in self._attr_hvac_modes
                and len(self._attr_hvac_modes) >= 2
            ):
                self._off_mode["hvac_mode"] = HVACMode.OFF
                self._attr_supported_features |= (
                    ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
                )
                if HVACMode.AUTO in self._attr_hvac_modes:
                    self._last_on_mode["hvac_mode"] = HVACMode.AUTO
                elif len(self._attr_hvac_modes) == 2:
                    self._last_on_mode["hvac_mode"] = list(
                        filter(lambda item: item != HVACMode.OFF, self._attr_hvac_modes)
                    )[0]
                else:
                    self._last_on_mode["hvac_mode"] = HVACMode.OFF
        else:
            _LOGGER.error(
                "Entity '%s' has no hvac mode, at least one hvac mode shall be configured!",
                self._attr_name,
            )
            return False

        if self._attr_preset_modes and len(self._attr_preset_modes) >= 2:
            if self._action_preset_mode or self._template_preset_mode:
                self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE
            else:
                _LOGGER.warning(
                    "Entity '%s' has preset mode configured, but there is neither action '%s' nor template '%s' configured.",
                    self._attr_name,
                    CONF_SET_PRESET_MODE_ACTION,
                    CONF_PRESET_MODE_TEMPLATE,
                )
                self._attr_preset_modes = []
        elif self._action_preset_mode or self._template_preset_mode:
            _LOGGER.warning(
                "Entity '%s' has no preset mode configured, but there is action '%s' and/or template '%s' configured.",
                self._attr_name,
                CONF_SET_PRESET_MODE_ACTION,
                CONF_PRESET_MODE_TEMPLATE,
            )
            self._action_preset_mode = None
            self._template_preset_mode = None

        if self._attr_fan_modes and len(self._attr_fan_modes) >= 2:
            if self._action_fan_mode or self._template_fan_mode:
                self._attr_supported_features |= ClimateEntityFeature.FAN_MODE
            else:
                _LOGGER.warning(
                    "Entity '%s' has fan mode configured, but there is neither action '%s' nor template '%s' configured.",
                    self._attr_name,
                    CONF_SET_FAN_MODE_ACTION,
                    CONF_FAN_MODE_TEMPLATE,
                )
                self._attr_fan_modes = []
        elif self._action_fan_mode or self._template_fan_mode:
            _LOGGER.warning(
                "Entity '%s' has not fan mode configured, but there is action '%s' and/or template '%s' configured.",
                self._attr_name,
                CONF_SET_FAN_MODE_ACTION,
                CONF_FAN_MODE_TEMPLATE,
            )
            self._action_fan_mode = None
            self._template_fan_mode = None

        if self._attr_swing_modes and len(self._attr_swing_modes) >= 2:
            if self._action_swing_mode or self._template_swing_mode:
                self._attr_supported_features |= ClimateEntityFeature.SWING_MODE
            else:
                _LOGGER.warning(
                    "Entity '%s' has swing mode configured, but there is neither action '%s' nor template '%s' configured.",
                    self._attr_name,
                    CONF_SET_SWING_MODE_ACTION,
                    CONF_SWING_MODE_TEMPLATE,
                )
                self._attr_swing_modes = []
        elif self._action_swing_mode or self._template_swing_mode:
            _LOGGER.warning(
                "Entity '%s' has no swing mode configured, but there is action '%s' and/or template '%s' configured.",
                self._attr_name,
                CONF_SET_SWING_MODE_ACTION,
                CONF_SWING_MODE_TEMPLATE,
            )
            self._action_swing_mode = None
            self._template_swing_mode = None

        if HVACMode.HEAT_COOL in self._attr_hvac_modes:
            if (
                not self._template_target_temperature_high
                and self._template_target_temperature_low
            ) or (
                not self._template_target_temperature_low
                and self._template_target_temperature_high
            ):
                _LOGGER.warning(
                    "Entity '%s' shall have either both templates '%s' and '%s' configured or none of them.",
                    self._attr_name,
                    CONF_TARGET_TEMPERATURE_LOW_TEMPLATE,
                    CONF_TARGET_TEMPERATURE_HIGH_TEMPLATE,
                )
                self._template_target_temperature_low = None
                self._template_target_temperature_high = None
            if self._action_temperature or (
                self._template_target_temperature_low
                and self._template_target_temperature_high
            ):
                self._attr_supported_features |= (
                    ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
                )
            else:
                _LOGGER.warning(
                    "Entity '%s' has hvac mode heat_cool configured, but there is no action neither template for high or low temperature configued.",
                    self._attr_name,
                )
        else:
            if (
                self._template_target_temperature_low
                or self._template_target_temperature_high
            ):
                _LOGGER.warning(
                    "Entity '%s' has no Hvac mode heat_cool configured, but there is '%s' and/or '%s' template configured.",
                    self._attr_name,
                    CONF_TARGET_TEMPERATURE_LOW_TEMPLATE,
                    CONF_TARGET_TEMPERATURE_HIGH_TEMPLATE,
                )
                self._template_target_temperature_low = None
                self._template_target_temperature_high = None

        if any(
            list(
                map(
                    lambda var: var in self._attr_hvac_modes,
                    [HVACMode.AUTO, HVACMode.HEAT, HVACMode.COOL],
                )
            )
        ):
            if self._action_temperature or self._template_target_temperature:
                self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
            else:
                _LOGGER.warning(
                    "Entity '%s' has hvac mode auto, heat or cool configured, but there is no action neither template for temperature configued.",
                    self._attr_name,
                )
        else:
            if self._action_temperature:
                _LOGGER.warning(
                    "Entity '%s' has no hvac mode auto, heat or cool configured, but there is action '%s' configured.",
                    self._attr_name,
                    CONF_SET_TEMPERATURE_ACTION,
                )
                self._action_temperature = None
            if self._template_target_temperature:
                _LOGGER.warning(
                    "Entity '%s' has no hvac mode auto, heat or cool configured, but there is template '%s' configured.",
                    self._attr_name,
                    CONF_TARGET_TEMPERATURE_TEMPLATE,
                )
                self._template_target_temperature = None

        if HVACMode.DRY in self._attr_hvac_modes:
            if self._action_humidity or self._template_target_humidity:
                self._attr_supported_features |= ClimateEntityFeature.TARGET_HUMIDITY
            else:
                _LOGGER.warning(
                    "Entity '%s' has hvac mode dry configured, but there is no '%s' action neither '%s' template configured.",
                    self._attr_name,
                    CONF_SET_HUMIDITY_ACTION,
                    CONF_TARGET_HUMIDITY_TEMPLATE,
                )
        else:
            if self._action_humidity:
                _LOGGER.warning(
                    "Entity '%s' has no hvac mode dry configured, but there is action '%s' configured.",
                    self._attr_name,
                    CONF_SET_HUMIDITY_ACTION,
                )
                self._action_humidity = None
            if self._template_target_humidity:
                _LOGGER.warning(
                    "Entity '%s' has no hvac mode dry configured, but there is template '%s' configured.",
                    self._attr_name,
                    CONF_TARGET_HUMIDITY_TEMPLATE,
                )
                self._action_humidity = None

        if self._action_hvac_mode:
            self._script_hvac_mode = Script(
                hass,
                self._action_hvac_mode,
                self._attr_name,
                DOMAIN,
                script_mode=self._attr_mode_action,
                max_runs=self._attr_max_action,
            )

        if self._action_preset_mode:
            self._script_preset_mode = Script(
                hass,
                self._action_preset_mode,
                self._attr_name,
                DOMAIN,
                script_mode=self._attr_mode_action,
                max_runs=self._attr_max_action,
            )

        if self._action_fan_mode:
            self._script_fan_mode = Script(
                hass,
                self._action_fan_mode,
                self._attr_name,
                DOMAIN,
                script_mode=self._attr_mode_action,
                max_runs=self._attr_max_action,
            )

        if self._action_swing_mode:
            self._script_swing_mode = Script(
                hass,
                self._action_swing_mode,
                self._attr_name,
                DOMAIN,
                script_mode=self._attr_mode_action,
                max_runs=self._attr_max_action,
            )

        if self._action_temperature:
            self._script_temperature = Script(
                hass,
                self._action_temperature,
                self._attr_name,
                DOMAIN,
                script_mode=self._attr_mode_action,
                max_runs=self._attr_max_action,
            )

        if self._action_humidity:
            self._script_humidity = Script(
                hass,
                self._action_humidity,
                self._attr_name,
                DOMAIN,
                script_mode=self._attr_mode_action,
                max_runs=self._attr_max_action,
            )

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Check if we have an previous stored state and use it as default state.
        previous_state = await self.async_get_last_state()
        if previous_state is not None:
            _LOGGER.debug(
                "Entity '%s' restoring previously stored attributes.",
                self._attr_name,
            )

            if (
                hvac_mode := self._validate_value(
                    "hvac_mode", previous_state.state, self._attr_hvac_modes
                )
            ) is not None:
                self._attr_hvac_mode = hvac_mode

            if (value := previous_state.attributes.get(ATTR_PRESET_MODE)) is not None:
                if (
                    preset_mode := self._validate_value(
                        "preset_mode",
                        value,
                        self._attr_preset_modes,
                    )
                ) is not None:
                    self._attr_preset_mode = preset_mode

            if (value := previous_state.attributes.get(ATTR_FAN_MODE)) is not None:
                if (
                    fan_mode := self._validate_value(
                        "fan_mode",
                        value,
                        self._attr_fan_modes,
                    )
                ) is not None:
                    self._attr_fan_mode = fan_mode

            if (value := previous_state.attributes.get(ATTR_SWING_MODE)) is not None:
                if (
                    swing_mode := self._validate_value(
                        "swing_mode",
                        value,
                        self._attr_swing_modes,
                    )
                ) is not None:
                    self._attr_swing_mode = swing_mode

            if (value := previous_state.attributes.get(ATTR_TEMPERATURE)) is not None:
                if (
                    target_temperature := self._validate_value(
                        "target_temperature",
                        value,
                        "target_temperature",
                    )
                ) is not None:
                    self._attr_target_temperature = target_temperature

            if (
                value := previous_state.attributes.get(ATTR_TARGET_TEMP_LOW)
            ) is not None:
                if (
                    target_temperature_low := self._validate_value(
                        "target_temperature_low",
                        value,
                        "target_temperature",
                    )
                ) is not None:
                    self._attr_target_temperature_low = target_temperature_low

            if (
                value := previous_state.attributes.get(ATTR_TARGET_TEMP_HIGH)
            ) is not None:
                if (
                    target_temperature_high := self._validate_value(
                        "target_temperature_high",
                        value,
                        "target_temperature",
                    )
                ) is not None:
                    self._attr_target_temperature_high = target_temperature_high

            if (value := previous_state.attributes.get(ATTR_HUMIDITY)) is not None:
                if (
                    target_humidity := self._validate_value(
                        "target_humidity",
                        value,
                        "target_humidity",
                    )
                ) is not None:
                    self._target_humidity = target_humidity

            if (
                value := previous_state.attributes.get(ATTR_CURRENT_TEMPERATURE)
            ) is not None:
                if (
                    current_temperature := self._validate_value(
                        "current_temperature",
                        value,
                        "current_temperature",
                    )
                ) is not None:
                    self._attr_current_temperature = current_temperature

            if (
                value := previous_state.attributes.get(ATTR_CURRENT_HUMIDITY)
            ) is not None:
                if (
                    current_humidity := self._validate_value(
                        "current_humidity",
                        value,
                        "current_humidity",
                    )
                ) is not None:
                    self._attr_current_humidity = current_humidity

            if (value := previous_state.attributes.get(ATTR_HVAC_ACTION)) is not None:
                if (
                    hvac_action := self._validate_value(
                        "hvac_action",
                        value,
                        [member.value for member in HVACAction],
                    )
                ) is not None:
                    self._attr_hvac_action = hvac_action

            if (value := previous_state.attributes.get("last_on_mode")) is not None:
                for mode in value.keys():
                    self._last_on_mode[mode] = value[mode]

        _LOGGER.debug(
            "Entity '%s' registering templates callbacks.",
            self._attr_name,
        )

        # Register templates callback.
        if self._template_hvac_mode:
            self.add_template_attribute(
                "_hvac_mode",
                self._template_hvac_mode,
                None,
                self._update_hvac_mode,
                none_on_template_error=True,
            )

        if self._template_preset_mode:
            self.add_template_attribute(
                "_preset_mode",
                self._template_preset_mode,
                None,
                self._update_preset_mode,
                none_on_template_error=True,
            )

        if self._template_fan_mode:
            self.add_template_attribute(
                "_fan_mode",
                self._template_fan_mode,
                None,
                self._update_fan_mode,
                none_on_template_error=True,
            )

        if self._template_swing_mode:
            self.add_template_attribute(
                "_swing_mode",
                self._template_swing_mode,
                None,
                self._update_swing_mode,
                none_on_template_error=True,
            )

        if self._template_target_temperature:
            self.add_template_attribute(
                "_target_temperature",
                self._template_target_temperature,
                None,
                self._update_target_temperature,
                none_on_template_error=True,
            )

        if self._template_target_temperature_high:
            self.add_template_attribute(
                "_target_temperature_high",
                self._template_target_temperature_high,
                None,
                self._update_target_temperature_high,
                none_on_template_error=True,
            )

        if self._template_target_temperature_low:
            self.add_template_attribute(
                "_target_temperature_low",
                self._template_target_temperature_low,
                None,
                self._update_target_temperature_low,
                none_on_template_error=True,
            )

        if self._template_target_humidity:
            self.add_template_attribute(
                "_target_humidity",
                self._template_target_humidity,
                None,
                self._update_target_humidity,
                none_on_template_error=True,
            )

        if self._template_current_temperature:
            self.add_template_attribute(
                "_current_temperature",
                self._template_current_temperature,
                None,
                self._update_current_temperature,
                none_on_template_error=True,
            )

        if self._template_current_humidity:
            self.add_template_attribute(
                "_current_humidity",
                self._template_current_humidity,
                None,
                self._update_current_humidity,
                none_on_template_error=True,
            )

        if self._template_hvac_action:
            self.add_template_attribute(
                "_hvac_action",
                self._template_hvac_action,
                None,
                self._update_hvac_action,
                none_on_template_error=True,
            )

        _LOGGER.debug(
            "Entity '%s' succesfully registered to homeassistant.",
            self._attr_name,
        )

    def _validate_value(self, attr, value, format):
        if value is None:
            _LOGGER.error(
                "Entity '%s' attribute '%s' returned value: 'None'.",
                self._attr_name,
                attr,
            )
            return None
        elif isinstance(value, TemplateError):
            _LOGGER.error(
                "Entity '%s' attribute '%s' returned exception: '%s'.",
                self._attr_name,
                attr,
                value,
            )
            return None
        elif value in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            _LOGGER.debug(
                "Entity '%s' attribute '%s' returned Uknown or Unavailable: '%s'.",
                self._attr_name,
                attr,
                value,
            )
            return None
        elif format is not None:
            if type(format) is list or type(format) is dict:
                value = str(value)
                if value not in format:
                    _LOGGER.error(
                        "Entity '%s' attribute '%s' returned invalid value: '%s'. Expected one of: '%s'.",
                        self._attr_name,
                        attr,
                        value,
                        format,
                    )
                    return None
            elif format == "current_temperature":
                try:
                    if self.precision == PRECISION_HALVES:
                        value = round(float(value) / 0.5) * 0.5
                    elif self.precision == PRECISION_TENTHS:
                        value = round(float(value), 1)
                    else:
                        value = round(float(value))
                except ValueError:
                    _LOGGER.error(
                        "Entity '%s' attribute '%s' returned invalid value: '%s'. Expected integer of float.",
                        self._attr_name,
                        attr,
                        value,
                    )
                    return None
            elif format == "target_temperature":
                try:
                    value = (
                        round(float(value) / self._attr_target_temperature_step)
                        * self._attr_target_temperature_step
                    )
                except ValueError:
                    _LOGGER.error(
                        "Entity '%s' attribute '%s' returned invalid value: '%s'. Expected integer or float.",
                        self._attr_name,
                        attr,
                        value,
                    )
                    return None
                if value > self._attr_max_temp:
                    _LOGGER.error(
                        "Entity '%s' attribute '%s' returned invalid value: '%s', which is bigger than max setpoint: '%s'.",
                        self._attr_name,
                        attr,
                        value,
                        self._attr_max_temp,
                    )
                    return None
                if value < self._attr_min_temp:
                    _LOGGER.error(
                        "Entity '%s' attribute '%s' returned invalid value: '%s', which is smaller than min setpoint: '%s'.",
                        self._attr_name,
                        attr,
                        value,
                        self._attr_min_temp,
                    )
                    return None
            elif format == "curent_humidity":
                try:
                    value = round(value)
                except ValueError:
                    _LOGGER.error(
                        "Entity '%s' attribute '%s' returned invalid value: '%s'. Expected integer of float.",
                        self._attr_name,
                        attr,
                        value,
                    )
                    return None
            elif format == "target_humidity":
                try:
                    value = round(value)
                except ValueError:
                    _LOGGER.error(
                        "Entity '%s' attribute '%s' returned invalid value: '%'s. Expected integer of float.",
                        self._attr_name,
                        attr,
                        value,
                    )
                    return None
                if value > self._attr_max_humidity:
                    _LOGGER.error(
                        "Entity '%s' attribute '%s' returned invalid value: '%s', which is bigger than max setpoint: '%s'.",
                        self._attr_name,
                        attr,
                        value,
                        self._attr_max_humidity,
                    )
                    return None
                if value < self._attr_min_humidity:
                    _LOGGER.error(
                        "Entity '%s' attribute '%s' returned invalid value: '%s', which is smaller than min setpoint: '%s'.",
                        self._attr_name,
                        attr,
                        value,
                        self._attr_min_humidity,
                    )
                    return None
            else:
                _LOGGER.debug(
                    "Entity '%s' attribute '%s' test called with invalid format: '%s'.",
                    self._attr_name,
                    attr,
                    format,
                )

        _LOGGER.debug(
            "Entity '%s' attribute '%s' triggered update with value: '%s'.",
            self._attr_name,
            attr,
            value,
        )
        return value

    @callback
    def _update_hvac_mode(self, hvac_mode: str):
        self.hass.async_create_task(
            self._async_set_attribute(
                "hvac_mode",
                {
                    "hvac_mode": {
                        "attr": ATTR_HVAC_MODE,
                        "value": hvac_mode,
                        "format": self._attr_hvac_modes,
                    }
                },
            ),
        )

    @callback
    def _update_preset_mode(self, preset_mode: str):
        self.hass.async_create_task(
            self._async_set_attribute(
                "preset_mode",
                {
                    "preset_mode": {
                        "attr": ATTR_PRESET_MODE,
                        "value": preset_mode,
                        "format": self._attr_preset_modes,
                    }
                },
            ),
        )

    @callback
    def _update_fan_mode(self, fan_mode: str):
        self.hass.async_create_task(
            self._async_set_attribute(
                "fan_mode",
                {
                    "fan_mode": {
                        "attr": ATTR_FAN_MODE,
                        "value": fan_mode,
                        "format": self._attr_fan_modes,
                    }
                },
            ),
        )

    @callback
    def _update_swing_mode(self, swing_mode: str):
        self.hass.async_create_task(
            self._async_set_attribute(
                "swing_mode",
                {
                    "swing_mode": {
                        "attr": ATTR_SWING_MODE,
                        "value": swing_mode,
                        "format": self._attr_swing_modes,
                    }
                },
            ),
        )

    @callback
    def _update_target_temperature(self, target_temperature: float):
        self.hass.async_create_task(
            self._async_set_attribute(
                "temperature",
                {
                    "target_temperature": {
                        "attr": ATTR_TEMPERATURE,
                        "value": target_temperature,
                        "format": "target_temperature",
                    }
                },
            ),
        )

    @callback
    def _update_target_temperature_low(self, target_temperature_low: float):
        self.hass.async_create_task(
            self._async_set_attribute(
                "temperature",
                {
                    "target_temperature_low": {
                        "attr": ATTR_TARGET_TEMP_LOW,
                        "value": target_temperature_low,
                        "format": "target_temperature",
                    },
                    "target_temperature_high": {
                        "attr": ATTR_TARGET_TEMP_HIGH,
                        "value": self._attr_target_temperature_high,
                        "format": "target_temperature",
                    },
                },
            ),
        )

    @callback
    def _update_target_temperature_high(self, target_temperature_high: float):
        self.hass.async_create_task(
            self._async_set_attribute(
                "temperature",
                {
                    "target_temperature_high": {
                        "attr": ATTR_TARGET_TEMP_HIGH,
                        "value": target_temperature_high,
                        "format": "target_temperature",
                    },
                    "target_temperature_low": {
                        "attr": ATTR_TARGET_TEMP_LOW,
                        "value": self._attr_target_temperature_low,
                        "format": "target_temperature",
                    },
                },
            ),
        )

    @callback
    def _update_target_humidity(self, target_humidity: int):
        self.hass.async_create_task(
            self._async_set_attribute(
                "humidity",
                {
                    "target_humidity": {
                        "attr": ATTR_HUMIDITY,
                        "value": target_humidity,
                        "format": "target_humidity",
                    }
                },
            ),
        )

    @callback
    def _update_current_temperature(self, current_temperature: float):
        if (
            value := self._validate_value(
                "current_temperature", current_temperature, "current_temperature"
            )
        ) is not None:
            self._attr_current_temperature = value

    @callback
    def _update_current_humidity(self, current_humidity: float):
        if (
            value := self._validate_value(
                "current_humidity", current_humidity, "current_humidity"
            )
        ) is not None:
            self._attr_current_humidity = value

    @callback
    def _update_hvac_action(self, hvac_action: str):
        if (
            value := self._validate_value(
                "hvac_action", hvac_action, [member.value for member in HVACAction]
            )
        ) is not None:
            self._attr_hvac_action = value

    async def _async_set_attribute(self, action, attributes) -> None:
        variables = {}
        for attr in attributes.keys():
            # Validate input values
            if (
                value := self._validate_value(
                    attr, attributes[attr]["value"], attributes[attr]["format"]
                )
            ) is not None:
                attributes[attr]["value"] = value
            else:
                _LOGGER.debug(
                    "Entity '%s' attribute '%s' update called with invalid value: '%s'.",
                    self._attr_name,
                    attr,
                    attributes[attr]["value"],
                )
                return False

            if getattr(self, "_attr_" + attr) == attributes[attr]["value"]:
                # Nothing to do.
                _LOGGER.debug(
                    "Entity '%s' attribute '%s' is already set to value: '%s'.",
                    self._attr_name,
                    attr,
                    attributes[attr]["value"],
                )
            else:
                # Update entity attribute.
                _LOGGER.debug(
                    "Entity '%s' updating attribute '%s' to value: '%s'.",
                    self._attr_name,
                    attr,
                    attributes[attr]["value"],
                )
                setattr(self, "_attr_" + attr, attributes[attr]["value"])
                # Update last_on modes if not off mode.
                if (
                    attr in self._off_mode.keys()
                    and attributes[attr]["value"] != self._off_mode[attr]
                ):
                    self._last_on_mode[attr] = attributes[attr]["value"]
                # Set script varaible
                variables[attributes[attr]["attr"]] = attributes[attr]["value"]

        self.async_write_ha_state()

        if len(variables) and (script := getattr(self, "_script_" + action)):
            # Create a context referring to the trigger context.
            trigger_context_id = None if self._context is None else self._context.id
            script_context = Context(parent_id=trigger_context_id)
            # Execute set action script.
            _LOGGER.debug(
                "Entity '%s' executing script 'set_action_%s' variables: '%s'.",
                self._attr_name,
                action,
                variables,
            )
            await script.async_run(
                run_variables=variables,
                context=script_context,
            )
            _LOGGER.debug(
                "Entity '%s' execution of script 'set_action_%s' finished.",
                self._attr_name,
                action,
            )
        return True

    @property
    def state(self):
        """Return the current state."""
        return self._attr_hvac_mode

    @property
    def extra_state_attributes(self):
        """Platform specific attributes."""
        return {
            "last_on_mode": self._last_on_mode,
            "off_mode": self._off_mode,
        }

    async def async_turn_off(self) -> None:
        """Turn climate off."""
        if "hvac_mode" in self._off_mode.keys():
            await self.async_set_hvac_mode(self._off_mode["hvac_mode"])

    async def async_turn_on(self) -> None:
        """Turn climate on."""
        if "hvac_mode" in self._last_on_mode.keys():
            await self.async_set_hvac_mode(self._last_on_mode["hvac_mode"])

    async def async_toggle(self) -> None:
        """Toggle climate."""
        if (
            "hvac_mode" in self._off_mode.keys()
            and "hvac_mode" in self._last_on_mode.keys()
        ):
            if self._attr_hvac_mode == self._off_mode["hvac_mode"]:
                await self.async_set_hvac_mode(self._last_on_mode["hvac_mode"])
            elif self._attr_hvac_mode == self._last_on_mode["hvac_mode"]:
                await self.async_set_hvac_mode(self._off_mode["hvac_mode"])

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new hvac mode."""
        await self._async_set_attribute(
            "hvac_mode",
            {
                "hvac_mode": {
                    "attr": ATTR_HVAC_MODE,
                    "value": hvac_mode,
                    "format": self._attr_hvac_modes,
                }
            },
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        await self._async_set_attribute(
            "preset_mode",
            {
                "preset_mode": {
                    "attr": ATTR_PRESET_MODE,
                    "value": preset_mode,
                    "format": self._attr_preset_modes,
                }
            },
        )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        await self._async_set_attribute(
            "fan_mode",
            {
                "fan_mode": {
                    "attr": ATTR_FAN_MODE,
                    "value": fan_mode,
                    "format": self._attr_fan_modes,
                }
            },
        )

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new swing mode."""
        await self._async_set_attribute(
            "swing_mode",
            {
                "swing_mode": {
                    "attr": ATTR_SWING_MODE,
                    "value": swing_mode,
                    "format": self._attr_swing_modes,
                }
            },
        )

    async def async_set_humidity(self, target_humidity: int) -> None:
        """Set new humidity target."""
        await self._async_set_attribute(
            "humidity",
            {
                "target_humidity": {
                    "attr": ATTR_HUMIDITY,
                    "value": target_humidity,
                    "format": "target_humidity",
                }
            },
        )

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperatures."""
        attributes = {}
        hvac_mode = self._attr_hvac_mode
        if (hvac_mode := kwargs.get(ATTR_HVAC_MODE)) is not None:
            attributes["hvac_mode"] = {
                "attr": ATTR_HVAC_MODE,
                "value": hvac_mode,
                "format": self._attr_hvac_modes,
            }
        else:
            hvac_mode = self._attr_hvac_mode

        if hvac_mode == HVACMode.HEAT_COOL:
            if (target_temperature_low := kwargs.get(ATTR_TARGET_TEMP_LOW)) is not None:
                attributes["target_temperature_low"] = {
                    "attr": ATTR_TARGET_TEMP_LOW,
                    "value": target_temperature_low,
                    "format": "target_temperature",
                }
            else:
                return False
            if (
                target_temperature_high := kwargs.get(ATTR_TARGET_TEMP_HIGH)
            ) is not None:
                attributes["target_temperature_high"] = {
                    "attr": ATTR_TARGET_TEMP_HIGH,
                    "value": target_temperature_high,
                    "format": "target_temperature",
                }
            else:
                return False
        else:
            if (target_temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
                attributes["target_temperature"] = {
                    "attr": ATTR_TEMPERATURE,
                    "value": target_temperature,
                    "format": "target_temperature",
                }
            else:
                return False

        await self._async_set_attribute("temperature", attributes)
