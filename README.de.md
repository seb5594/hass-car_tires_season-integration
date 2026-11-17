# Car Tires Season

Sagt dir, wann es Zeit ist, zwischen Sommer- und Winterreifen zu wechseln. Die Integration
verbindet die Winterreifen-Regeln deines Landes (manche gelten zu festen Terminen, andere nur bei
winterlichen Straßen), die Wettervorhersage oder deinen eigenen Außentemperatursensor und den
Kalender. Heraus kommt ein Sensor für Automatisierungen und, wenn du willst, eine dauerhafte
Benachrichtigung, sobald die montierten Reifen nicht mehr zur Jahreszeit passen.

[🇬🇧 English](README.md) · **🇩🇪 Deutsch**

## Was sie kann

- **Kennt die Regeln von 47 Ländern**, von der situativen deutschen Winterreifenpflicht über den
  festen russischen Zeitraum (1.12. bis Ende Februar) bis zur Regel in Québec (1.12. bis 15.3.) und
  den baltischen Staaten. Jede Regel verweist auf ihre Quellen: [Ländervorschriften](docs/COUNTRY_RULES.md).
- **Schaut aufs Wetter.** Winterreifen werden empfohlen, wenn die Durchschnittstemperatur der
  nächsten Tage unter 7 °C bleibt oder Frost bzw. Schnee erwartet wird. Zurück zu Sommerreifen geht
  es erst mit Sicherheitsabstand. Gewechselt wird nur in der Nähe der Wintersaison deines Landes,
  eine kalte Julinacht ändert also nichts.
- **Läuft auch ohne Vorhersage.** Ein einfacher Außentemperatursensor genügt, die Integration führt
  daraus selbst eine kurze Historie. Ganz ohne Wetterdaten entscheidet der Kalender
  (in Deutschland die bekannte Regel „von O bis O“, Oktober bis Ostern).
- **Merkt sich, was montiert ist.** Eine Auswahl-Entität hält die aktuellen Reifen fest, der
  Binärsensor „Reifenwechsel fällig“ ist an, solange sie nicht zur Empfehlung passen.
- **Spricht deine Sprache.** Einrichtung, Entitätsnamen und Benachrichtigung sind in 35 Sprachen
  übersetzt, und die Regeln der jeweiligen Länder wurden für jede Sprache geprüft.

## Installation

### HACS

Suche in HACS (oder im eingebauten Marktplatz ab Home Assistant 2026.11) nach **Car Tires Season**
und lade die Integration herunter. Starte Home Assistant danach neu.

Als benutzerdefiniertes Repository: `https://github.com/seb5594/hass-car_tires_season-integration`
mit der Kategorie *Integration*.

### Manuell

Kopiere `custom_components/car_tires_season` in den Ordner `custom_components` deiner Home-Assistant-Konfiguration
oder entpacke dort die `car_tires_season.zip` eines
[Releases](https://github.com/seb5594/hass-car_tires_season-integration/releases) und starte neu.

## Einrichtung

### Automatisch

Nach dem Neustart, der auf die Installation folgt, richtet sich die Integration selbst ein. Home
Assistant kündigt sich per mDNS im Netzwerk an und reicht diese Ankündigung an alle installierten
Integrationen weiter; Car Tires Season greift die der eigenen Instanz auf und legt einen Eintrag an mit

- dem Land aus deinen Home-Assistant-Einstellungen (ersatzweise aus der Zeitzone),
- der ersten gefundenen Wetter-Entität,
- eingeschalteten Benachrichtigungen.

Voraussetzung sind die Integration `zeroconf` (Teil von `default_config`) und ein Netzwerk, das mDNS
durchlässt; typische Ausnahme ist Docker ohne Host-Netzwerk. Lässt sich das Land nicht ermitteln oder
hat es regionale Regeln (Kanada), erscheint die Integration unter **Einstellungen → Geräte & Dienste**
als *entdeckt* und fragt nach. Ein automatisch angelegter Eintrag, den du löschst, kommt nicht zurück.

### Manuell einrichten

**Einstellungen → Geräte & Dienste → Integration hinzufügen → Car Tires Season.**

| Option | Bedeutung |
| --- | --- |
| Name | Erscheint am Gerät und in der Benachrichtigung, z. B. der Name des Autos |
| Land | Bestimmt die geltenden Regeln. Länder ohne recherchierte Regeln nutzen eine allgemeine Saison und das Wetter |
| Wetter-Entität | Optional. Liefert Vorhersage und aktuelle Temperatur |
| Außentemperatur-Sensor | Optional. Wird statt der Temperatur der Wetter-Entität verwendet |

Über **Konfigurieren** am Eintrag stellst du die Temperaturschwelle (Standard 7 °C), die Zahl der
gemittelten Tage (Standard 5) und die Benachrichtigung ein. Die Integration lässt sich mehrfach
anlegen, etwa für ein zweites Auto, das im Ausland unterwegs ist.

### YAML

Optional und gleichwertig zur Oberfläche. Die Einträge werden bei jedem Start in normale Config-Entries
importiert, der YAML-Inhalt hat Vorrang vor Änderungen in der Oberfläche.

```yaml
car_tires_season:
  - name: Golf
    country: DE
    weather_entity: weather.home
    temperature_entity: sensor.aussentemperatur
    temperature_threshold: 7
    forecast_days: 5
    notifications: true
```

Alle Schlüssel sind optional; ein nacktes `car_tires_season:` legt einen Eintrag für das erkannte Land an.

## Entitäten

| Entität | Zustand | Verwendung |
| --- | --- | --- |
| `sensor.<name>_recommended_tires` | `summer` oder `winter` | Automatisierungen, Dashboards |
| `binary_sensor.<name>_tire_change_due` | `on`, solange die montierten Reifen nicht passen | Erinnerungen, „ab in die Werkstatt“ |
| `select.<name>_mounted_tires` | `summer`, `winter`, `all_season` | Nach dem Reifenwechsel umstellen |

Die Attribute des Empfehlungssensors (`reason`, `legal_status`, `season_start`, `season_end`,
`average_temperature` u. a.) sind in der [englischen README](README.md#entities) beschrieben.

Beim ersten Start gelten die montierten Reifen als passend, du wirst also nicht sofort erinnert.
Wähle `all_season`, wenn dein Auto Ganzjahresreifen trägt; der Binärsensor bleibt dann aus.

### Beispiel-Automatisierung

```yaml
automation:
  - alias: Reifenwechsel-Erinnerung
    trigger:
      - platform: state
        entity_id: binary_sensor.golf_tire_change_due
        to: "on"
    action:
      - service: notify.mobile_app_handy
        data:
          title: Reifen
          message: "Zeit für den Wechsel auf {{ state_attr('binary_sensor.golf_tire_change_due', 'change_to') }}-Reifen."
```

## Gut zu wissen

- Die Regeln sind bei Verbraucherzentren, Automobilclubs, Reifenherstellern und nationalen Quellen
  recherchiert und stammen vom November 2026. Sie sind eine Empfehlung, keine Rechtsberatung. Wer im
  Ausland fährt, prüft die dortigen Vorschriften. [docs/COUNTRY_RULES.md](docs/COUNTRY_RULES.md) zeigt,
  wie gut jedes Land belegt ist (`high`, `medium`, `low`); China und Südkorea sind `low`, weil keine
  offizielle Quelle zu finden war, beide kennen nach bisherigem Stand keine landesweite Winterreifenpflicht.
- Die Reifenkennzeichnung zählt: Viele Länder akzeptieren inzwischen nur noch das Alpine-Symbol (3PMSF), nicht mehr M+S allein.
- Getestet wird bei jeder Änderung von Home Assistant 2022.4 bis zur aktuellen Version.

## Danksagung

Die Idee stammt von [ha-snowtire](https://github.com/KrzysztofHajdamowicz/ha-snowtire), einem
vorhersagebasierten Schneereifen-Sensor. Vielen Dank an Andrey „Limych“ Khrolenok, der die
ursprüngliche Integration geschaffen hat, und an Krzysztof Hajdamowicz, der sie weiterpflegt.
Car Tires Season ist eine eigenständige Umsetzung mit eigenem Code und eigenem Datenmodell und
deshalb unter der MIT-Lizenz veröffentlicht.
