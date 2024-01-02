# ❄️ Template Climate

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![License](https://img.shields.io/github/license/litinoveweedle/hass-template-climate?style=for-the-badge)](https://github.com/litinoveweedle/hass-template-climate/blob/main/LICENSE)
[![Latest Release](https://img.shields.io/github/v/release/litinoveweedle/hass-template-climate?style=for-the-badge)](https://github.com/litinoveweedle/hass-template-climate/releases)
[![Size](https://img.badgesize.io/https:/github.com/litinoveweedle/hass-template-climate/releases/latest/download/climate_template.zip?style=for-the-badge)](https://github.com/litinoveweedle/hass-template-climate/releases)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)

The `climate_template` platform creates climate devices that combine integrations and provides the ability to run scripts or invoke services for each of the `set_*` commands of a climate entity.

This is a fork of the original repository jcwillox/hass-template-climate which seems to be unmaintained at the time with several pull requests pending. As those were very useful to my usage I decided to fork and merge the work of the corresponding authors to allow at least for me simple usage of the integration through HACS. Therefore all the corresponding rights belong to the original authors.

## Configuration

All configuration variables are optional. The climate device will work in optimistic mode (assumed state) if a template isn't defined.

If you do not define a `template` or its corresponding `action` the climate device will not have that attribute, e.g. either `swing_mode_template` or `set_swing_mode` must be defined for the climate to have a swing mode.

| Name                             | Type                                                                      | Description                                                                                                                                                                                                                                                                                     | Default Value                                      |
|----------------------------------| ------------------------------------------------------------------------- |-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|
| name                             | `string`                                                                  | The name of the climate device.                                                                                                                                                                                                                                                                 | "Template Climate"                                 |
| unique_id                        | `string`                                                                  | The [unique id](https://developers.home-assistant.io/docs/entity_registry_index/#unique-id) of the climate entity.                                                                                                                                                                              | None                                               |
| mode_action                      | `string`                                                                  | possible value: "parallel", "queued", "restart", "single"                                                                                                                                                                                                                                       | single                                             |
| max_action                       | `positive_int`                                                                  | positive number from 1                                                                                                                                                                                                                                                                          | 1                                                  |
| icon_template                    | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template for the icon of the sensor.                                                                                                                                                                                                                                                  |                                                    |
| entity_picture_template          | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template for the entity picture of the sensor.                                                                                                                                                                                                                                        |                                                    |
| availability_template            | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the `available` state of the component. If the template returns `true`, the device is `available`. If the template returns any other value, the device will be `unavailable`. If `availability_template` is not configured, the component will always be `available`. | true                                               |
|                                  |                                                                           |                                                                                                                                                                                                                                                                                                 |                                                    |
| current_temperature_template     | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the current temperature.                                                                                                                                                                                                                                              |                                                    |
| current_humidity_template        | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the current humidity.                                                                                                                                                                                                                                                 |                                                    |
| target_temperature_template      | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the target temperature of the climate device.                                                                                                                                                                                                                         |                                                    |
| target_temperature_high_template | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the target temperature high of the climate device.                                                                                                                                                                                                                    |                                                    |
| target_temperature_low_template  | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the target temperature low of the climate device.                                                                                                                                                                                                                     |                                                    |
| hvac_mode_template               | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the hvac mode of the climate device.                                                                                                                                                                                                                                  |                                                    |
| fan_mode_template                | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the fan mode of the climate device.                                                                                                                                                                                                                                   |                                                    |
| preset_mode_template             | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the preset mode of the climate device.                                                                                                                                                                                                                                |                                                    |
| swing_mode_template              | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the swing mode of the climate device.                                                                                                                                                                                                                                 |                                                    |
| hvac_action_template             | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the [`hvac action`](https://developers.home-assistant.io/docs/core/entity/climate/#hvac-action) of the climate device.                                                                                                                                                |                                                    |
|                                  |                                                                           |                                                                                                                                                                                                                                                                                                 |                                                    |
| set_temperature                  | [`action`](https://www.home-assistant.io/docs/scripts)                    | Defines an action to run when the climate device is given the set temperature command. Can use `temperature`, `target_temp_high`, `target_temp_low` and `hvac_mode` variables.                                                                                                                  |                                                    |
| set_hvac_mode                    | [`action`](https://www.home-assistant.io/docs/scripts)                    | Defines an action to run when the climate device is given the set hvac mode command. Can use `hvac_mode` variable.                                                                                                                                                                              |                                                    |
| set_fan_mode                     | [`action`](https://www.home-assistant.io/docs/scripts)                    | Defines an action to run when the climate device is given the set fan mode command. Can use `fan_mode` variable.                                                                                                                                                                                |                                                    |
| set_preset_mode                     | [`action`](https://www.home-assistant.io/docs/scripts)                 | Defines an action to run when the climate device is given the set preset mode command. Can use `preset_mode` variable.                                                                                                                                                                                |                                                    |
| set_swing_mode                   | [`action`](https://www.home-assistant.io/docs/scripts)                    | Defines an action to run when the climate device is given the set swing mode command. Can use `swing_mode` variable.                                                                                                                                                                            |                                                    |
|                                  |                                                                           |                                                                                                                                                                                                                                                                                                 |                                                    |
| modes                            | `list`                                                                    | A list of supported hvac modes. Needs to be a subset of the default values.                                                                                                                                                                                                                     | ["auto", "off", "cool", "heat", "dry", "fan_only"] |
| fan_modes                        | `list`                                                                    | A list of supported fan modes.                                                                                                                                                                                                                                                                  | ["auto", "low", "medium", "high"]                  |
| preset_modes                     | `list`                                                                    | A list of supported preset modes.                                                                                                                                                                                                                                                               | ["activity", "away", "boost", "comfort", "eco", "home", "sleep"] |
| swing_modes                      | `list`                                                                    | A list of supported swing modes.                                                                                                                                                                                                                                                                | ["on", "off"]                                      |
|                                  |                                                                           |                                                                                                                                                                                                                                                                                                 |                                                    |
| min_temp                         | `float`                                                                   | Minimum set point available.                                                                                                                                                                                                                                                                    | 7                                                  |
| max_temp                         | `float`                                                                   | Maximum set point available.                                                                                                                                                                                                                                                                    | 35                                                 |
| precision                        | `float`                                                                   | The desired precision for this device.                                                                                                                                                                                                                                                          | 0.1 for Celsius and 1.0 for Fahrenheit.            |
| temp_step                        | `float`                                                                   | Step size for temperature set point.                                                                                                                                                                                                                                                            | 1                                                  |

## Example Configuration

```yaml
climate:
  - platform: climate_template
    name: Bedroom Aircon
    
    modes:
      - "auto"
      - "dry"
      - "off"
      - "cool"
      - "fan_only"
    min_temp: 16
    max_temp: 30

    # get current temp.
    current_temperature_template: "{{ states('sensor.bedroom_temperature') }}"

    # get current humidity.
    current_humidity_template: "{{ states('sensor.bedroom_humidity') }}"

    # swing mode switch for UI.
    swing_mode_template: "{{ states('input_boolean.bedroom_swing_mode') }}"

    # available based on esphome nodes' availability.
    availability_template: "{{ is_state('binary_sensor.bedroom_node_status', 'on') }}"

    # example action
    set_hvac_mode:
      # allows me to disable sending commands to aircon via UI.
      - condition: state
        entity_id: input_boolean.enable_aircon_controller
        state: "on"

      # send the climates current state to esphome.
      - service: esphome.bedroom_node_aircon_state
        data:
          temperature: "{{ state_attr('climate.bedroom_aircon', 'temperature') | int }}"
          operation_mode: "{{ states('climate.bedroom_aircon') }}"
          fan_mode: "{{ state_attr('climate.bedroom_aircon', 'fan_mode') }}"
          swing_mode: "{{ is_state_attr('climate.bedroom_aircon', 'swing_mode', 'on') }}"
          light: "{{ is_state('light.bedroom_aircon_light', 'on') }}"

      # could also send IR command via broadlink service calls etc.
```

### Example action to control existing Home Assistant devices

```yaml
climate:
  - platform: climate_template
    # ...
    set_hvac_mode:
      # allows you to control an existing Home Assistant HVAC device
      - service: climate.set_hvac_mode
        data:
          entity_id: climate.bedroom_ac_nottemplate
          hvac_mode: "{{ states('climate.bedroom_ac_template') }}"
```

### Use Cases

- Merge multiple components into one climate device (just like any template platform).
- Control optimistic climate devices such as IR aircons via service calls.
