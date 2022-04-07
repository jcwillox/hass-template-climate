# <span style="font-family: 'Segoe UI Emoji'">❄</span> Template Climate

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![License](https://img.shields.io/github/license/jcwillox/hass-template-climate?style=for-the-badge)](https://github.com/jcwillox/hass-template-climate/blob/main/LICENSE)
[![Latest Release](https://img.shields.io/github/v/release/jcwillox/hass-template-climate?style=for-the-badge)](https://github.com/jcwillox/hass-template-climate/releases)
[![Size](https://img.badgesize.io/https:/github.com/jcwillox/hass-template-climate/releases/latest/download/climate_template.zip?style=for-the-badge)](https://github.com/jcwillox/hass-template-climate/releases)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)

The `climate_template` platform creates climate devices that combine integrations and provides the ability to run scripts or invoke services for each of the `set_*` commands of a climate entity.

## Configuration
All configuration variables are optional. The climate device will work in optimistic mode (assumed state) if a template isn't defined.

If you do not define a `template` or its corresponding `action` the climate device will not have that attribute, e.g. either `swing_mode_template` or `set_swing_mode` must be defined for the climate to have a swing mode.

| Name                         | Type                                                                      | Description                                                                                                                                                                                                                                                                         | Default Value                                      |
| ---------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| name                         | `string`                                                                  | The name of the climate device.                                                                                                                                                                                                                                                     | "Template Climate"                                 |
| icon_template                | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template for the icon of the sensor.                                                                                                                                                                                                                                      |                                                    |
| entity_picture_template      | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template for the entity picture of the sensor.                                                                                                                                                                                                                            |                                                    |
| availability_template        | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the `available` state of the component. If the template returns `true`, the device is `available`. If the template returns any other value, the device will be `unavailable`. If `availability_template` is not configured, the component will always be `available`. | true                                               |
|                              |                                                                           |                                                                                                                                                                                                                                                                                     |                                                    |
| current_temperature_template | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the current temperature.                                                                                                                                                                                                                                  |                                                    |
| current_humidity_template    | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the current humidity.                                                                                                                                                                                                                                     |                                                    |
| swing_mode_template          | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the swing mode of the climate device.                                                                                                                                                                                                                     |                                                    |
|                              |                                                                           |                                                                                                                                                                                                                                                                                     |                                                    |
| set_temperature              | [`action`](https://www.home-assistant.io/docs/scripts)                    | Defines an action to run when the climate device is given the set temperature command.                                                                                                                                                                                              |                                                    |
| set_hvac_mode                | [`action`](https://www.home-assistant.io/docs/scripts)                    | Defines an action to run when the climate device is given the set hvac mode command.                                                                                                                                                                                                |                                                    |
| set_fan_mode                 | [`action`](https://www.home-assistant.io/docs/scripts)                    | Defines an action to run when the climate device is given the set fan mode command.                                                                                                                                                                                                 |                                                    |
| set_swing_mode               | [`action`](https://www.home-assistant.io/docs/scripts)                    | Defines an action to run when the climate device is given the set swing mode command.                                                                                                                                                                                               |                                                    |
|                              |                                                                           |                                                                                                                                                                                                                                                                                     |                                                    |
| modes                        | `list`                                                                    | A list of supported hvac modes. Needs to be a subset of the default values.                                                                                                                                                                                                         | ["auto", "off", "cool", "heat", "dry", "fan_only"] |
| fan_modes                    | `list`                                                                    | A list of supported fan modes.                                                                                                                                                                                                                                                      | ["auto", "low", "medium", "high"]                  |
| swing_modes                  | `list`                                                                    | A list of supported swing modes.                                                                                                                                                                                                                                                    | ["on", "off"]                                      |
|                              |                                                                           |                                                                                                                                                                                                                                                                                     |                                                    |
| min_temp                     | `float`                                                                   | Minimum set point available.                                                                                                                                                                                                                                                        | 7                                                  |
| max_temp                     | `float`                                                                   | Maximum set point available.                                                                                                                                                                                                                                                        | 35                                                 |
| precision                    | `float`                                                                   | The desired precision for this device.                                                                                                                                                                                                                                              | 0.1 for Celsius and 1.0 for Fahrenheit.            |
| temp_step                    | `float`                                                                   | Step size for temperature set point.                                                                                                                                                                                                                                                | 1                                                  |

<!-- 
| temperature_template (N/A)   | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the target temperature of the climate device.                                                                                                                                                                                                             |                                                    |
| humidity_template (N/A)      | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the target humidity of the climate device.                                                                                                                                                                                                                |                                                    |
| action_template (N/A)        | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the swing mode of the climate device.                                                                                                                                                                                                                     |                                                    |
| hvac_mode_template (N/A)     | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the swing mode of the climate device.                                                                                                                                                                                                                     |                                                    |
| fan_mode_template (N/A)      | [`template`](https://www.home-assistant.io/docs/configuration/templating) | Defines a template to get the swing mode of the climate device.                                                                                                                                                                                                                     |                                                    |

| set_humidity (N/A)           | [`action`](https://www.home-assistant.io/docs/scripts)                    | Defines an action to run when the climate device is given the set humidity command.                                                                                                                                                                                                 |                                                    |
-->

<!-- away_mode_state_template
aux_state_template
hold_state_template

temperature_low_state_template
temperature_high_state_template

set_preset_mode
set_aux_heat -->

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

    # Example Action.
    set_hvac_mode:
    
      # allows me to disable sending commands to aircon via UI.
      - condition: state  
        entity_id: input_boolean.enable_aircon_controller
        state: "on"
        
      # send the climates current state to esphome.
      - service: esphome.bedroom_node_aircon_state  
        data_template:
          temperature: "{{ state_attr('climate.bedroom_aircon', 'temperature') | int }}"
          operation_mode: "{{ states('climate.bedroom_aircon') }}"
          fan_mode: "{{ state_attr('climate.bedroom_aircon', 'fan_mode') }}"
          swing_mode: "{{ is_state_attr('climate.bedroom_aircon', 'swing_mode', 'on') }}"
          light: "{{ is_state('light.bedroom_aircon_light', 'on') }}"
          
      # could also send IR command via broadlink service calls etc.
```

### Use Cases
* Merge multiple components into one climate device (just like any template platform).
* Control optimistic climate devices such as IR aircons via service calls.

<!-- ## Planned Features
- Support all climate actions.
- Support all climate state options (e.g. action, away, hold). -->
