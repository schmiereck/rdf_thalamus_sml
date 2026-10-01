---
type: Befund
title: Platte ausblenden - Richtung stimmt, nicht signifikant
description: Gepaartes act23-A/B, ob die feste 70-mm-Stapelplatte (ACT23_SOCKEL=1) die gewoehnliche Transportaufgabe stoert. Ohne Platte 60,0 % gegen 53,3 % mit (je 150 Episoden, 3 Seeds, alle 150 Aufgaben paarweise identisch); McNemar 20 gegen 10 diskordante Paare, p = 0,099. Alle drei Seeds in dieselbe Richtung, kein Seed signifikant. Endabstand unveraendert.
tags: [act23, sockel, platte, stapeln, ab, nutzeridee]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-10-01T00:00:00Z }
sources:
  - id: code
    resource: "Commit nach 14700e0: ACT23_SOCKEL_AUS (0/1/2), state.ZIEL_SPERRE, Aufgaben-Abdruck im [Szenen-Abdruck]"
    title: Messschalter
  - id: lauf
    resource: "Kopflos (ACT23_VIZ=1 ACT23_VIZ_HEADLESS=1), Kopie von act23_state.pkl (a40c25cb, 12576 Welt-Modell-Versuche), ACT23_NO_PERSIST=1, Seeds 9801-9803 je 50 Ep, ACT23_SZENE_JE_EPISODE=1 ACT23_AUTO_CURIOUS=0 ACT23_SOCKEL=1 ACT23_EIG_DIREKT=1 ACT23_EIG_STETIG=1 ACT16_GOAL_Z=1 ACT16_GRIFF_Z=1, Choreo netz, Marker-Ziele (ACT23_ZIEL_ADRESSE aus); Arm B zusaetzlich ACT23_SOCKEL_AUS=2; Arme nacheinander (parallel lief ein GUI-Lauf des Nutzers)"
    title: A/B-Lauf 2026-10-01
---

# Frage

Nutzerbefund: mit `ACT23_SOCKEL=1` steht die blaue 70-mm-Platte in JEDER Szene an derselben
Stelle `[-0.018, +0.149]`, nimmt viel Tisch ein "und duerfte das Netz verwirren". Seit
2026-10-01 laesst sie sich in der GUI ausblenden ([Steuer-GUI](/mechanismen/gui-bedienung.md)).
Verbessert das die Quote?

# Aufbau

* Aufgabe: die gewoehnliche Marker-Ablage (keine Zieladresse) - die einzige, die in beiden Armen
  moeglich ist. "Auf die Platte" gibt es ohne Platte nicht.
* Arm A: Platte steht wie im Nutzerlauf. Arm B: `ACT23_SOCKEL_AUS=2` - geparkt, **aber die
  Marker-Ziele meiden ihre Stelle weiter** (`state.ZIEL_SPERRE`). Ohne diese Sperre haette Arm B
  Ziele bis 10 cm um die Plattenstelle bekommen, und man haette die Zielverteilung gemessen statt
  der Platte.
* Paarung geprueft ueber einen neuen **Aufgaben-Abdruck** (Objekt, Ziel, Marker, Lagen aller
  STEHENDEN Objekte; ohne Stuetzen, Farbbindungen und Geparktes): **150 von 150 identisch.**
* Gegenprobe der Zaehlung: `[Selbst-Urteil] ... Welt:` widerspricht der `[Auto N]`-Zeile in
  keiner Episode; in 1-2 Episoden je Seed fehlt die Urteilszeile (in beiden Armen dieselben).

# Ergebnis

| Seed | mit Platte | ohne Platte | nur mit | nur ohne |
|---|---|---|---|---|
| 9801 | 24/50 | 26/50 | 5 | 7 |
| 9802 | 29/50 | 32/50 | 3 | 6 |
| 9803 | 27/50 | 32/50 | 2 | 7 |
| **gesamt** | **80/150 = 53,3 %** | **90/150 = 60,0 %** | **10** | **20** |

* McNemar exakt: p = **0,099**. Fisher ungepaart: p = 0,29. Vorzeichen ueber Seeds 3 von 3
  (p = 0,25).
* Median-Endabstand 22 gegen 21 mm - unveraendert.
* Je Objekt (mit/ohne, n): U 4/7 (19), rot 14/16, blau 16/18, L 9/10, T 10/11, X 12/13,
  gruen 15/15 - ueberall gleich oder ohne Platte besser, keines einzeln trennbar
  (Bonferroni 7 Objekte: 0,0071).

# Lesart

**Die Richtung stimmt, belegt ist sie nicht.** +6,7 Punkte, doppelt so viele Episoden gelingen
nur ohne Platte wie nur mit ihr, und kein Seed kehrt das um - aber p = 0,099 bei 30 diskordanten
Paaren. Dass der Endabstand gleich bleibt, passt zu einer Stoerung, die eher Ausreisser
(Verwechslung, Kollision) als die Genauigkeit trifft; das ist eine Vermutung, nicht gemessen.

Praktisch: wer keine Stapelaufgaben faehrt, verliert durch das Ausblenden nichts Messbares und
gewinnt vermutlich etwas. Wer stapelt, braucht die Platte - dann ist `ACT23_SOCKEL_WANDERT=1`
die bessere Wahl als eine feste Stelle ([Lernen ohne Verlernen](/befunde/policy-lernt-hoehe-als-ort.md)).

Um 6-7 Punkte bei dieser Paarungsdichte sicher zu trennen, braucht es rund doppelt so viele
Episoden (etwa 6 Seeds x 50); nicht gefahren.

# Verwandt

* [Steuer-GUI](/mechanismen/gui-bedienung.md) - Platte ein-/ausblenden, `ACT23_SOCKEL_AUS`
* [Sockel braucht 80 mm](/befunde/sockel-braucht-80mm-freiraum.md)
* [Kopfloses A/B](/messungen/act23-headless-ab.md)
