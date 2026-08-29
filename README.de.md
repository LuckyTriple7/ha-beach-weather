# Beach Weather

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/LuckyTriple7/ha-beach-weather)](https://github.com/LuckyTriple7/ha-beach-weather/releases)

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/luckytriple7)

[English](README.md) · **Deutsch**

Home-Assistant-Integration für Strand- und Wasserbedingungen (Wassertemperatur, Wellen, Wind, Badebedingungen), auf Basis der kostenlosen [Open-Meteo](https://open-meteo.com/) Marine- und Forecast-APIs — ohne API-Schlüssel.

## Funktionen

- Beliebig viele Standorte, jeder als eigener Config-Entry — Koordinaten manuell eingeben oder auf der Karte auswählen
- Wassertemperatur, Wellenhöhe/-periode, Windgeschwindigkeit/Böen/Richtung, dazu ein berechneter Sensor für die Badebedingungen
- Eine normale `weather.<slug>`-Entity pro Standort mit stündlicher und täglicher Vorhersage, für die native Wetterkarte
- Passende Lovelace-Karte, [Beach Weather Card](https://github.com/LuckyTriple7/ha-beach-weather-card) (`custom:beach-weather-card`) — Sensorwerte frei über einem Strandfoto positionieren; separat über HACS installiert
- Alle Anfragen sämtlicher Standorte laufen über einen gemeinsamen Rate-Limiter — auch viele Standorte feuern nie parallel auf Open-Meteo (vermeidet HTTP 403)
- Automatischer Fehler-Backoff bei 403/429
- Konfiguration komplett über die HA-Oberfläche, kein YAML nötig
- Einstellbares Abfrageintervall (Standard 900 s / 15 min, passend zum Aktualisierungsrhythmus von Open-Meteo)

## Installation über HACS

1. HACS öffnen → **Integrationen** → Menü (⋮) → **Benutzerdefinierte Repositories**
2. URL eintragen: `https://github.com/LuckyTriple7/ha-beach-weather`
3. Kategorie: **Integration** → **Hinzufügen**
4. Nach **Beach Weather** suchen → **Herunterladen**
5. Home Assistant neu starten

## Konfiguration

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Beach Weather**
2. Optional das Feld **Koordinaten einfügen oder Ort suchen** nutzen: entweder ein „lat, lon"-Paar (z. B. direkt aus Google Maps kopiert) oder ein Ortsname als Freitext (z. B. „Maspalomas beach"), dann absenden — das füllt Karte, Namensvorschlag und vorgeschlagene Strandausrichtung vor, ohne den Standort schon anzulegen
3. Namen eingeben/bestätigen (z. B. „Platja de Muro") und den Standort festlegen — Koordinaten direkt eintippen oder auf der Karte wählen
4. Optional das Abfrageintervall anpassen (min. 300 s)
5. Die **Strandausrichtung** setzen/bestätigen (° Kompass, seewärts) — der Surf Score beurteilt damit, ob Wind- und Swell-Richtung günstig stehen

Für jeden weiteren Standort die Integration erneut hinzufügen. Alle Vorschläge sind Näherungen (Nominatim für Ortssuche und Name, nächstgelegenes OSM-Küstensegment via Overpass für die Ausrichtung) — vor dem Speichern prüfen, besonders die Ausrichtung an Buchten oder komplizierten Küstenlinien.

> Nach einem Update über HACS Home Assistant **neu starten** (kein bloßer Reload der Integration) — neue Übersetzungstexte werden nur bei einem vollen Neustart übernommen.

## Entitäten

Ein HA-Gerät pro Standort, benannt nach dem Standort. Alle Entity-IDs enthalten einen Slug des Standortnamens, hier am Beispiel „Platja de Muro":

| Entität | Beschreibung |
|--------|-------------|
| `sensor.water_temperature_platja_de_muro` | Wasseroberflächentemperatur (°C) |
| `sensor.wave_height_platja_de_muro` | Wellenhöhe (m) |
| `sensor.wave_direction_platja_de_muro` | Gesamt-Wellenrichtung (°) |
| `sensor.wave_period_platja_de_muro` | Wellenperiode (s) |
| `sensor.swell_height_platja_de_muro` | Swell-Wellenhöhe (m) — surfrelevant, getrennt von lokaler Windsee |
| `sensor.swell_direction_platja_de_muro` | Swell-Richtung (°) |
| `sensor.swell_period_platja_de_muro` | Swell-Periode (s) — Qualitätssignal fürs Surfen, getrennt von der gemischten Wellenperiode; Grundlage des Surf Score |
| `sensor.wind_wave_height_platja_de_muro` | Windsee-Höhe (m) — lokal windgetriebene Kabbelung, getrennt vom Swell |
| `sensor.wind_wave_direction_platja_de_muro` | Windsee-Richtung (°) |
| `sensor.wind_wave_period_platja_de_muro` | Windsee-Periode (s) |
| `sensor.ocean_current_velocity_platja_de_muro` | Strömungsgeschwindigkeit (km/h) |
| `sensor.ocean_current_direction_platja_de_muro` | Strömungsrichtung (°) |
| `sensor.timestamp_platja_de_muro` | Zeitstempel der Marine-Daten |
| `sensor.wind_speed_platja_de_muro` | Windgeschwindigkeit (km/h) |
| `sensor.wind_gusts_platja_de_muro` | Windböen (km/h) |
| `sensor.wind_direction_platja_de_muro` | Windrichtung (°) |
| `sensor.air_temperature_platja_de_muro` | Lufttemperatur in 2 m (°C) |
| `sensor.humidity_platja_de_muro` | Relative Luftfeuchte (%) |
| `sensor.precipitation_platja_de_muro` | Niederschlag im aktuellen Intervall (mm) |
| `sensor.rain_platja_de_muro` | Regen im aktuellen Intervall (mm) |
| `sensor.showers_platja_de_muro` | Schauer im aktuellen Intervall (mm) |
| `sensor.pressure_platja_de_muro` | Luftdruck auf Meereshöhe (hPa) |
| `sensor.cloud_cover_platja_de_muro` | Bewölkung (%) |
| `sensor.uv_index_platja_de_muro` | UV-Index |
| `sensor.visibility_platja_de_muro` | Horizontale Sichtweite (km) |
| `sensor.is_day_platja_de_muro` | Tag/Nacht |
| `sensor.weather_condition_platja_de_muro` | Wetterlage im Klartext (aus dem WMO-Code), mit dem Rohcode als Attribut |
| `sensor.timestamp_wind_platja_de_muro` | Zeitstempel der Wind-/Wetterdaten |
| `sensor.bathing_conditions_platja_de_muro` | Berechnete Badebedingungen als Text/Icon (ohne eigenen API-Aufruf) |
| `sensor.location_platja_de_muro` | Statischer Anzeigename, aus Kompatibilität zu bestehenden Lovelace-Karten |
| `sensor.last_status_platja_de_muro` | Letzter roher HTTP-Statuscode der Marine-API (Diagnose) |
| `sensor.last_status_wind_platja_de_muro` | Letzter roher HTTP-Statuscode der Forecast-/Wind-API (Diagnose) |
| `button.update_now_platja_de_muro` | Erzwingt sofortiges Aktualisieren beider APIs für diesen Standort — umgeht den gemeinsamen Rate-Limiter und einen aktiven Fehler-Backoff |
| `sensor.surf_score_platja_de_muro` | Surf-Qualität, 0-100 |
| `sensor.surf_condition_platja_de_muro` | Surf-Qualität als Kategorie (Kein Surf / Schlecht / Okay / Gut / Sehr gut / Perfekte Bedingungen) |
| `sensor.surf_stars_platja_de_muro` | Surf-Qualität als Sternebewertung (★ bis ★★★★★), mit Punktzahl und Sternanzahl als Attribute |
| `weather.platja_de_muro` | Standard-HA-Wetterentity — aktuelle Bedingungen plus stündliche/tägliche Vorhersage |

Ein Sensor wird `unavailable`, wenn Open-Meteo für dieses Feld keinen Wert liefert oder die Anfrage scheitert. Ausnahme sind die beiden „Last Status"-Sensoren: Sie bleiben auch nach einem fehlgeschlagenen Update sichtbar und zeigen den rohen Statuscode (z. B. `403`), damit ein Rate-Limit-Problem ohne Log-Suche erkennbar ist.

Die 12 Marine-Sensoren (Wassertemperatur, Wellenhöhe/-richtung/-periode, Swell-Höhe/-Richtung/-Periode, Windsee-Höhe/-Richtung/-Periode, Strömungsgeschwindigkeit/-richtung) tragen jeweils ein `forecast`-Attribut — die nächsten 48 Stunden als `[{"time": ..., "value": ...}, ...]`, `null` solange keine Vorhersagedaten vorliegen.

## Wetter-Entity

`weather.<slug>` ist eine normale Home-Assistant-Wetterentity — funktioniert mit der eingebauten Wetterkarte, mit `weather.get_forecasts` und allem anderen, das eine gewöhnliche `weather.*`-Entity erwartet. Sie deckt nur die atmosphärische Seite ab (Temperatur, Wind, Luftdruck, Feuchte, Bewölkung, UV-Index, Sicht, Niederschlag, Wetterlage) aus den `current`/`hourly`/`daily`-Blöcken der Forecast-API — Wellen-, Swell- und Surf-Daten haben im Wettermodell von HA nichts verloren und bleiben auf den eigenen Sensoren oben. WMO-Wettercodes werden auf HAs Standard-Zustände abgebildet (`sunny`/`clear-night` für Codes 0-1, tag-/nachtabhängig; `partlycloudy`, `cloudy`, `fog`, `rainy`, `pouring`, `snowy`, `snowy-rainy`, `lightning`, `lightning-rainy` für den Rest).

## Lovelace-Karte

Die Karte hat ein eigenes Repository: **[Beach Weather Card](https://github.com/LuckyTriple7/ha-beach-weather-card)** (`custom:beach-weather-card`) — die Sensorwerte eines Standorts frei über einem Strandfoto positioniert, per Drag & Drop im Karteneditor.

![Beach Weather Card](images/beach-weather-card.webp)

Installation über HACS → **Dashboard** → **Beach Weather Card**. HACS registriert die Lovelace-Ressource selbst; diese Integration schreibt nicht in deinen Ressourcen-Speicher.

> **Umstieg von 0.24.0 oder älter:** Die Karte steckte bisher in dieser Integration, die dafür eine Lovelace-Ressource mit Ziel `/beach_weather_static/beach-weather-card.js` registriert hat. Version 1.0.0 entfernt diese Ressource beim nächsten Start und bedient den Pfad nicht mehr — die Karte also über HACS installieren, um sie weiter zu nutzen. Bestehende Dashboards müssen nicht angepasst werden: gleicher Kartentyp, gleiches Konfigurationsformat, gleiche Entity-IDs.

## Schwellenwerte für Badebedingungen

Die Schwellenwerte des Badebedingungs-Sensors (Kältegrenze, ruhige/mäßige Wellenhöhe, perfekte/sehr gute Wassertemperatur, perfekte Wellenperiode) gelten **global für alle Standorte**, nicht pro Standort. Anpassen über **Einstellungen → Geräte & Dienste → Beach Weather → Konfigurieren** (bei einem beliebigen Standort) → **Schwellenwerte für Badebedingungen** — dargestellt als Schieberegler. Änderungen wirken sofort auf den Badebedingungs-Sensor jedes Standorts, ohne Neustart.

## Surf Score

`sensor.surf_score` verrechnet sechs Faktoren zu einer einzigen Qualitätszahl von 0-100. Jeder Faktor wird über eine eigene Kurve bewertet (nicht linear) und über **globale, einstellbare Gewichte** kombiniert (Einstellungen → Geräte & Dienste → Beach Weather → Konfigurieren → **Surf-Score-Gewichtung**):

| Faktor | Standardgewicht | Was belohnt wird |
|--------|-----------------|------------------|
| Wellenperiode | 30 % | Nutzt die **Swell-Periode** (nicht die gemischte Wellenperiode, in der die lokale Windkabbelung steckt); 10-14 s ideal, sehr kurze Perioden nahe 0 |
| Wellenhöhe | 20 % | 0,8-1,5 m ideal; zu flach oder zu groß gibt weniger |
| Swell-Richtung | 20 % | Wie genau die Swell-Richtung zur Strandausrichtung passt |
| Windrichtung | 15 % | Wie genau die Windrichtung zur Strandausrichtung passt |
| Windgeschwindigkeit | 10 % | Ruhiger ist besser; 0-10 km/h ideal |
| Wassertemperatur | 5 % | 20-24 °C ideal |

Die Gewichte müssen sich nicht auf 100 summieren — sie werden automatisch über ihre Summe normalisiert. Dazu zwei Boni (je +10, kumulierbar, Gesamtwert bei 100 gedeckelt): Swell trifft den Strand frontal **und** der Wind weht ablandig; oder Wellenperiode > 10 s **und** Wellenhöhe > 0,8 m. Die Richtungsbewertung braucht die **Strandausrichtung** des Standorts (bei der Einrichtung oder über Konfigurieren → Standort gesetzt); fehlt sie, vergleichen die Richtungs-Teilwerte gegen 0°, was für den jeweiligen Strand meist falsch ist.

Die Attribute von `sensor.surf_score` schlüsseln auf, wie die Zahl zustande kam: der eigene 0-100-Teilwert jedes Faktors (`wave_period_score`, `wave_height_score`, `swell_direction_score`, `wind_direction_score`, `wind_speed_score`, `water_temperature_score`), die tatsächlich verwendeten Gewichte, beide Richtungsabweichungen in Grad, welcher der beiden Boni gegriffen hat, und der gewichtete Mittelwert vor den Boni.

## Diagnose

Jeder Standort unterstützt HAs **Diagnose herunterladen** (Einstellungen → Geräte & Dienste → Beach Weather → Gerät des Standorts → ⋮ → Diagnose herunterladen). Enthalten sind der letzte Update-Status beider Coordinators, HTTP-Statuscode, Backoff-Zustand und Rohdaten, dazu die globalen Badebedingungs-Schwellenwerte und Surf-Score-Gewichte — Koordinaten, Standortname und Slug werden geschwärzt, im Config-Entry ebenso wie in den Coordinator-Rohdaten.

## Fehlerbehandlung & Backoff

Scheitert eine Anfrage, gehen die betroffenen Sensoren bis zum nächsten erfolgreichen Update auf `unavailable`; andere Standorte und die jeweils andere API bleiben unberührt. Bei HTTP 403 wartet der Coordinator 30 Minuten, bei 429 15 Minuten, bei 503 (Open-Meteo vorübergehend überlastet — ein transienter Zustand, keine Rate-Limit-Sperre) 30 Sekunden, bei allen anderen HTTP-Fehlern 5 Minuten, bevor er überhaupt einen neuen Versuch startet — das schützt davor, einen ohnehin blockenden Open-Meteo-Endpunkt weiter zu bombardieren. Der **Update Now**-Button ignoriert diesen Backoff und den gemeinsamen Rate-Limiter vollständig: Ein Druck löst immer sofort eine Anfrage aus, denn eine bewusste manuelle Aktion soll nicht stillschweigend vom automatischen Burst-Schutz geschluckt werden.

Der allererste Datenabruf eines Standorts läuft im Hintergrund und blockiert nie den Start von Home Assistant — bei vielen Standorten am gemeinsamen Rate-Limiter kommen die Entities zunächst schlicht als `unavailable` hoch und füllen sich, sobald sie in der Warteschlange an der Reihe sind, meist innerhalb ein bis zwei Minuten.
