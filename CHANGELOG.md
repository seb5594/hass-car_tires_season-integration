# Changelog

## 2026.11.19.2

- First release published with a plain version tag (no leading `v`).

## 2026.11.19.1

- Versions now read `YYYY.MM.DD` for the first build of a day and `YYYY.MM.DD.1`, `.2` and so on for later ones. Release tags no longer start with a `v`.

## 2026.11.19.0

- The integration name and the suggested name in the setup follow the language of the Home Assistant server (for example "Autoreifen Saison").
- The country is preselected from the Home Assistant settings or the time zone.
- README describes the special cases of the supported countries.
- Manifest categories added for the Home Assistant and HACS catalogs.

## 2026.11.17.0

- First release: winter tire rules of 47 countries with sources, recommendation sensor, "tire change due" binary sensor, mounted tires select and an optional persistent notification.
- Setup from the UI, from YAML, or automatically after the installation (self-discovery).
- Translated into 35 languages; supports Home Assistant 2022.4 and newer.
