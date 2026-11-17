<!-- header:begin (generated from project metadata) -->
<h1 align="center">Car Tires Season</h1>

<p align="center">
  <img src="https://raw.githubusercontent.com/seb5594/hass-car_tires_season-integration/main/custom_components/car_tires_season/brand/icon@2x.png" alt="Car Tires Season" width="160" height="160">
</p>

---

<p align="center">
  <a href="https://paypal.me/seb5594"><img src="https://img.shields.io/static/v1?label=Support&amp;message=PayPal&amp;color=0070BA&amp;logo=paypal&amp;logoColor=white&amp;style=for-the-badge" alt="PayPal" height="40"></a>
  <a href="https://buymeacoffee.com/seb5594"><img src="https://img.shields.io/static/v1?label=Support&amp;message=Buy%20Me%20a%20Coffee&amp;color=FFDD00&amp;logo=buy-me-a-coffee&amp;logoColor=black&amp;style=for-the-badge" alt="Buy Me a Coffee" height="40"></a><br>
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=seb5594&amp;repository=hass-car_tires_season-integration&amp;category=integration"><img src="https://img.shields.io/static/v1?label=HACS%20%C2%B7%20Marketplace&amp;message=Add%20integration&amp;color=41BDF5&amp;logo=homeassistantcommunitystore&amp;logoColor=white&amp;style=for-the-badge" alt="HACS · Marketplace" height="28"></a>
  <a href="https://github.com/seb5594/hass-car_tires_season-integration/actions/workflows/compat.yml"><img src="https://img.shields.io/static/v1?label=home%20assistant&amp;message=%E2%89%A5%202022.4.0&amp;color=1877A5&amp;style=for-the-badge" alt="home assistant" height="28"></a>
  <a href="https://github.com/seb5594/hass-car_tires_season-integration/releases"><img src="https://img.shields.io/static/v1?label=version&amp;message=2026.11.17.0&amp;color=1877A5&amp;style=for-the-badge" alt="version" height="28"></a><br>
  <a href="https://github.com/seb5594/hass-car_tires_season-integration/stargazers"><img src="https://img.shields.io/github/stars/seb5594/hass-car_tires_season-integration?label=stars&amp;style=flat" alt="stars" height="20"></a>
  <a href="https://github.com/seb5594/hass-car_tires_season-integration/releases"><img src="https://img.shields.io/github/downloads/seb5594/hass-car_tires_season-integration/latest/total?label=downloads&amp;color=1877A5&amp;style=flat" alt="downloads" height="20"></a>
  <a href="https://github.com/seb5594/hass-car_tires_season-integration/issues"><img src="https://img.shields.io/github/issues/seb5594/hass-car_tires_season-integration?label=issues&amp;style=flat" alt="issues" height="20"></a>
  <a href="https://github.com/seb5594/hass-car_tires_season-integration/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/seb5594/hass-car_tires_season-integration/ci.yml?branch=main&amp;label=checks&amp;style=flat" alt="checks" height="20"></a>
  <a href="https://github.com/seb5594/hass-car_tires_season-integration#license"><img src="https://img.shields.io/github/license/seb5594/hass-car_tires_season-integration?label=license&amp;style=flat" alt="license" height="20"></a>
</p>
<!-- header:end -->

Tells you when it is time to switch between summer and winter tires. The integration combines
the winter tire rules of your country (many of them have fixed dates, some only apply when the
roads are wintry), the weather forecast or your own outdoor temperature sensor, and the plain
calendar. The result is a sensor you can use in automations, plus an optional persistent
notification when the tires on your car no longer match the season.

**🇬🇧 English** · [🇩🇪 Deutsch](README.de.md)

## What it does

- **Knows the rules of 47 countries**, from the German "situational" winter tire duty to the fixed
  Russian period (1 Dec – end of Feb), the Quebec rule (1 Dec – 15 Mar) and the Baltic states.
  Every rule links to its sources, see [Country rules](docs/COUNTRY_RULES.md).
- **Looks at the weather.** Winter tires are recommended when the average temperature of the next
  days stays below 7 °C, when frost or snow is expected, and are only released again with a margin
  (the classic spring "no more frost, clearly above 8 °C"). Switching only happens close to the
  winter season of your country, so a cold night in July changes nothing.
- **Works without a forecast.** A plain outdoor temperature sensor is enough, the integration
  builds its own short history from it. Without any weather data the calendar decides.
- **Remembers what is on your car.** A select entity holds the mounted tires; the "tire change due"
  binary sensor is on while they do not match the recommendation.
- **Speaks your language.** Setup, entity names and the notification text are translated into
  35 languages, and the rules of the matching countries were checked for each of them.

## Installation

### HACS

Search for **Car Tires Season** in HACS (or in the built-in marketplace of Home Assistant 2026.11
and newer) and download it. Restart Home Assistant afterwards.

For a custom repository use `https://github.com/seb5594/hass-car_tires_season-integration` with the
category *Integration*.

### Manual

Copy `custom_components/car_tires_season` into the `custom_components` folder of your Home
Assistant configuration, or unpack the `car_tires_season.zip` of a
[release](https://github.com/seb5594/hass-car_tires_season-integration/releases) there, and restart.

## Setup

### Automatic

After the restart that follows the installation, the integration sets itself up. Home Assistant
announces itself on the network via mDNS and offers that announcement to every installed
integration, and Car Tires Season picks up the one of its own instance. It then creates an entry
with

- the country from your Home Assistant settings (or from your time zone if none is set),
- the first weather entity it finds,
- notifications switched on.

This needs the `zeroconf` integration (part of `default_config`) and a network that lets mDNS
through; Docker without host networking is the usual exception. If the country cannot be found,
or the country has regional rules (Canada), the integration shows up as *discovered* in
**Settings → Devices & services** and asks for the missing detail. Deleting an automatically
created entry is final: it will not come back.

### Manually

**Settings → Devices & services → Add integration → Car Tires Season.**

| Option | Meaning |
| --- | --- |
| Name | Shown on the device and in the notification, e.g. the name of the car |
| Country | Decides which rules apply. Countries without researched rules use a generic season and rely on the weather |
| Weather entity | Optional. Provides the forecast and the current temperature |
| Outdoor temperature sensor | Optional. Used instead of the temperature of the weather entity |

**Configure** on the entry adds the temperature threshold (default 7 °C), the number of days to
average (default 5) and the switch for notifications. You can add the integration several times,
for example for a second car that is driven abroad.

### YAML

Optional and entirely equivalent to the UI. The entries are imported into regular config entries
on every start, and the YAML content wins over changes made in the UI.

```yaml
car_tires_season:
  - name: Golf
    country: DE
    weather_entity: weather.home
    temperature_entity: sensor.outdoor_temperature
    temperature_threshold: 7
    forecast_days: 5
    notifications: true
```

Every key is optional; a bare `car_tires_season:` creates one entry for the detected country.

## Entities

| Entity | State | Use it for |
| --- | --- | --- |
| `sensor.<name>_recommended_tires` | `summer` or `winter` | Automations, dashboards |
| `binary_sensor.<name>_tire_change_due` | `on` while the mounted tires do not fit | Reminders, "go to the garage" scenes |
| `select.<name>_mounted_tires` | `summer`, `winter`, `all_season` | Set it after you changed the tires |

Attributes of the recommendation sensor:

| Attribute | Meaning |
| --- | --- |
| `reason` | `legal_period`, `snow_expected`, `frost_risk`, `cold_weather`, `mild_weather`, `season_calendar` or `outside_season` |
| `legal_status` | `required`, `conditional` (required as soon as it gets wintry), `regional` (signposted roads or zones) or `not_required` |
| `legal_obligation` | The kind of rule in your country: `none`, `conditions`, `season_conditions`, `season`, `regional_season` |
| `season_start`, `season_end` | The current or next legal period (or practical season where there is no law) |
| `in_season` | Is today inside that period? |
| `average_temperature`, `minimum_temperature` | The values the decision is based on, in °C |
| `data_source` | `forecast`, `history` or `calendar` |
| `rule_confidence`, `rule_sources` | How well the rule of your country is backed, and where to read it |

On the first start the mounted tires are assumed to fit, so you are not reminded right away.
Choose `all_season` if your car wears all-season tires; the change-due sensor then stays off.

### Automation example

```yaml
automation:
  - alias: Tire change reminder
    trigger:
      - platform: state
        entity_id: binary_sensor.golf_tire_change_due
        to: "on"
    action:
      - service: notify.mobile_app_phone
        data:
          title: Tires
          message: "Time to switch to {{ state_attr('binary_sensor.golf_tire_change_due', 'change_to') }} tires."
```

## Good to know

- The rules are researched from consumer organisations, automobile clubs, tire makers and national
  sources, and date from November 2026. They are a recommendation, not legal advice. If you drive
  abroad, check the local rules. [docs/COUNTRY_RULES.md](docs/COUNTRY_RULES.md) shows how well each
  country is backed (`high`, `medium`, `low`); China and South Korea are `low` because no official
  source could be found, and both have no nationwide winter tire law as far as known.
- Tire markings matter in some countries: many now only accept the Alpine symbol (3PMSF), not plain M+S.
- Home Assistant 2022.4 up to the current release is tested on every change.

## Credits

The idea comes from [ha-snowtire](https://github.com/KrzysztofHajdamowicz/ha-snowtire), a forecast
based snow tire sensor. Many thanks to Andrey "Limych" Khrolenok, who created the original
integration, and to Krzysztof Hajdamowicz for keeping it alive. Car Tires Season is a separate
implementation with its own code and data model, so it can be published under the MIT license.

<!-- support:begin (generated, shared text) -->
## Say thanks

All my projects are built in my spare time, just for the fun of it. Still, they take a lot of time and care, and many of the smart home gadgets I buy end up here because I want to make them cloud-free and smart-home ready. Every bit of support means a lot to me.

If my work helped you or turned out to be useful, show your appreciation with a hot drink for my next sleepless night.

[![PayPal](https://img.shields.io/static/v1?label=Support&message=PayPal&color=0070BA&logo=paypal&logoColor=white&style=for-the-badge)](https://paypal.me/seb5594) [![Buy Me a Coffee](https://img.shields.io/static/v1?label=Support&message=Buy%20Me%20a%20Coffee&color=FFDD00&logo=buy-me-a-coffee&logoColor=black&style=for-the-badge)](https://buymeacoffee.com/seb5594)
<!-- support:end -->

<!-- license:begin (generated from the license file) -->
## License

[![license](https://img.shields.io/static/v1?label=license&message=MIT&color=5B6770&style=flat)](LICENSE)

Published under the [MIT License](LICENSE).
<!-- license:end -->
