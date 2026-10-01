---
type: Befund
title: Nur ein sichtbarer Marker - kein Effekt auf die Quote
description: Gepaartes act23-A/B, ob es die Marker-Ablage verbessert, wenn nur die aktive Magenta-Zielscheibe sichtbar ist (ACT23_EIN_MARKER=1) statt aller vier. 8 Seeds x 50 Episoden, vorab festgelegt mit dem Seed als Einheit. Vier sichtbar 58,2 %, einer 55,8 %; Seeds 5:3 fuer "vier sichtbar" (p = 0,73), McNemar 56:46 (p = 0,37). Kein Effekt; die Vorgabe 1 bleibt aus Gruenden der Lesbarkeit.
tags: [act23, marker, wahrnehmung, ab, nutzeridee]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-02T00:00:00Z }
sources:
  - id: lauf
    resource: "Kopflos (ACT23_VIZ=1 ACT23_VIZ_HEADLESS=1), Kopie von act23_state.pkl (a40c25cb), ACT23_NO_PERSIST=1, ACT23_STATE_HEADLESS=1, Seeds 9901-9908 je 50 Ep, ACT23_SZENE_JE_EPISODE=1 ACT23_AUTO_CURIOUS=0 ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1 ACT16_GOAL_Z=1 ACT16_GRIFF_Z=1, Choreo netz, Marker-Ablage, ohne Platte; Arm V ACT23_EIN_MARKER=0, Arm E =1; je Seed beide Arme parallel; Code 6f1c7e9"
    title: A/B-Lauf 2026-10-01/02
---

# Frage

Nutzeridee 2026-10-01: von den Magenta-Zielscheiben waren immer alle vier sichtbar (drei
waehlbare `target_sel_1..3` und die aktive `target_marker`) - "es waere viel einfacher fuer das
Netz, wenn immer nur einer davon sichtbar waere". Seitdem gilt `ACT23_EIN_MARKER=1`
([Steuer-GUI](/mechanismen/gui-bedienung.md)). Verbessert das die Quote?

**Vorab erwartet: kaum.** `perceive_all`, `select` und die Fovea-Einstiege parken die Marker
ohnehin vor jedem Blick (`_park_markers`). Wirken koennen sie nur ueber Bilder, die ohne Parken
gerendert werden (Fovea-Nachfuehrung waehrend der Ausfuehrung).

# Aufbau

Vorab festgelegt, mit der Lehre aus [Platte ausblenden](/befunde/platte-ausblenden-ab.md):
**Einheit ist der Seed** (Vorzeichentest) plus Gesamtquote; McNemar nur als Beiwerk; 8 Seeds,
danach Schluss. Aufgabe: Marker-Ablage - nur dort spielen die Marker eine Rolle. Ohne Platte,
damit nur ein Faktor variiert.

Paarung: 396 von 400 Aufgaben-Abdruecken gleich; die vier abweichenden (Seeds 9902, 9907) haben
dasselbe Objekt und dasselbe Ziel, nur eine Koerperlage weicht ab. Selbst-Urteil widerspricht der
Lieferzeile in keiner Episode.

# Ergebnis

| Seed | vier sichtbar | einer | nur vier | nur einer |
|---|---|---|---|---|
| 9901 | 33/50 | 32/50 | 7 | 6 |
| 9902 | 30/50 | 31/50 | 5 | 6 |
| 9903 | 30/50 | 28/50 | 7 | 5 |
| 9904 | 22/50 | 25/50 | 6 | 9 |
| 9905 | 33/50 | 26/50 | 11 | 4 |
| 9906 | 24/50 | 26/50 | 7 | 9 |
| 9907 | 31/50 | 26/50 | 7 | 2 |
| 9908 | 30/50 | 29/50 | 6 | 5 |
| **gesamt** | **233/400 = 58,2 %** | **223/400 = 55,8 %** | **56** | **46** |

* Seeds: 5 fuer "vier sichtbar", 3 fuer "einer", p = **0,73**.
* McNemar p = 0,37, Fisher p = 0,52. Median-Endabstand 22 gegen 23 mm. Je Objekt nichts
  trennbar.

# Lesart

**Kein Effekt.** Die Nutzeridee ist plausibel, trifft aber auf eine Wahrnehmung, die die Marker
vor jedem Blick ohnehin ausblendet - das Netz sah sie also schon vorher kaum. Wenn es eine
Richtung gibt, dann leicht zugunsten "vier sichtbar"; sie ist so weit von jeder Schwelle entfernt,
dass sie nicht zaehlt.

Die Vorgabe `ACT23_EIN_MARKER=1` bleibt: sie macht das Kamerabild fuer den Menschen eindeutig und
kostet nachweislich nichts. Sie ist aber **kein Hebel fuer die Quote**.

# Verwandt

* [Platte ausblenden - A/B](/befunde/platte-ausblenden-ab.md) - derselbe Aufbau, dieselbe Antwort
* [Steuer-GUI](/mechanismen/gui-bedienung.md)
* [Kopfloses A/B](/messungen/act23-headless-ab.md)
