---
type: Entscheidung
title: ACT23_WORLD_FULL_EVERY - der Welt-Fit bekommt einen Plan, Vorgabe jetzt 4
description: Der Fit je Episode laeuft nicht mehr nach jeder Episode voll, sondern jede vierte, mit 20 Epochen dazwischen. Nach dem A/B (je 200 Episoden, p = 0,92, Aneignung gleich, 61 Prozent mehr Episoden je Stunde) ist n=4 seit 2026-09-08 die Vorgabe. Rueckfall mit n=1.
tags: [act23, weltmodell, laufzeit, schalter]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-07T18:00:00Z }
sources:
  - id: befund
    resource: /befunde/welt-fit-warmstart.md
    title: Die Pruefstandsmessung, die den Schalter begruendet
  - id: lauf
    resource: "Kopflose Steuerungslaeufe auf einer Kopie von act23_state.pkl (11273 Zeilen), ACT23_AUTO_N=4 bzw. 2"
    title: Verifikation im echten act23-Lauf
---

# Entscheidung

Nutzerauftrag nach [Welt-Fit: Warmstart](/befunde/welt-fit-warmstart.md): *"Bau das hinter
ACT23_WORLD_FULL_EVERY, Vorgabe 1."*

Drei Schalter, alle Umgebungsvariablen:

| Schalter | Vorgabe | Wirkung |
|---|---|---|
| `ACT23_WORLD_FULL_EVERY` | `4` | jede n-te Episode voller Fit |
| `ACT23_WORLD_EPOCHS` | `600` | Epochen des vollen Fits |
| `ACT23_WORLD_EPOCHS_SHORT` | `20` | Epochen dazwischen |

**Zwei Stufen, zwei Daten.** Am 2026-09-07 wurde der Schalter mit Vorgabe `1` gebaut, also
zunaechst wirkungslos - erst danach durfte das A/B entscheiden. Am 2026-09-08 hat der Nutzer die
Vorgabe auf `4` gestellt, nachdem
[das A/B](/befunde/welt-fit-plan-ab.md) keinen Nachteil fand.

**Rueckfall in einer Zeile:** `ACT23_WORLD_FULL_EVERY=1`. Dann kehrt `welt_fit_epochen()` sofort
mit `WORLD_EPOCHS` zurueck, zaehlt nicht einmal mit, und `WORLD_EPOCHS_SHORT` wird nie gelesen -
zifferngenau der Stand vor `fec6c98`.

# Umfang

`epochs=600` steht an sechs Stellen in `pc_act23.py`. Umgestellt ist **genau eine**: der Fit je
Episode nach genau einer neuen Zeile (`run_self_learning_steering`, nach `world.observe`).

**`pc_act23.py:2055` bleibt bewusst voll** - das ist der Anfangsfit auf frisch gesammelten
eigenen Versuchen, also ein echter Kaltstart, fuer den die Konvergenzmessung nicht gilt. Die
uebrigen vier sind Diagnose-Einsprungpunkte ausserhalb des Steuerungslaufs.

Der Zaehler liegt auf Modulebene, nicht in einer der beiden Auto-Schleifen. Das ist Absicht: der
Riss zwischen kopfloser und GUI-Schleife hat hier schon **zweimal** dafuer gesorgt, dass ein
Schalter nur in einer Haelfte wirkte (siehe [Invarianten](/mechanismen/invarianten.md)).

Ein kurzer Fit ist im Protokoll **erkennbar** - die Kredit-Zeile bekommt `, Fit 20 Epochen`
angehaengt. Ohne diese Markierung waere in keiner spaeteren Auswertung trennbar, welche Episode
mit welchem Fit lief.

# Zahlen aus dem echten Lauf

Kopfloser Steuerungslauf auf einer **Kopie** des 11273-Zeilen-Zustands (`ACT23_STATE_PATH` +
`ACT23_STATE_HEADLESS=1`; die Datei des Nutzers blieb unveraendert, sha256 vorher wie nachher
`f8395ba2...`):

    ACT23_WORLD_FULL_EVERY=2, EPOCHS_SHORT=20
      Ep 1  voll   Lernen 73.0 s   gesamt  85.7 s
      Ep 2  kurz   Lernen 16.6 s   gesamt  27.0 s   [Kredit] ... Fit 20 Epochen
      Ep 3  voll   Lernen 73.1 s   gesamt  84.0 s
      Ep 4  kurz   Lernen 16.8 s   gesamt  44.1 s   [Kredit] ... Fit 20 Epochen

    Kontrolle ohne Schalter (Vorgabe)
      Ep 1         Lernen 73.4 s   gesamt  86.4 s
      Ep 2         Lernen 73.7 s   gesamt  84.2 s
      "Fit N Epochen" kommt 0-mal vor

Die Ersparnis von 56 s deckt sich mit den am Pruefstand gemessenen ~57 s fuer 600 Epochen x 5
Mitglieder. Die verbleibenden 16,7 s der Lernphase sind Kredit, Selbst-Imitation,
Runtime-Nachtraining und Speichern.

**Gegenprobe auf Unveraendertheit:** die ersten beiden Episoden sind in beiden Laeufen
zifferngenau gleich (Wrist 135 Grad / Guete 0,63 bei 17 mm; Wrist 138 Grad / Guete 0,87 bei
9 mm). Der kurze Fit in Episode 2 kann die Episode 2 nicht mehr beeinflussen - er laeuft danach;
ab Episode 3 duerfen die Arme auseinanderlaufen, und genau das misst ein A/B.

# Bewertung

**Der Schalter ist gebaut, nicht eingeschaltet.** Die Vorgabe bleibt `1`, weil der Nutzen
bislang nur am Pruefstand belegt ist und ein Pruefstandsergebnis einen act23-Lauf nicht
vorhersagt ([Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)). Was auf act23-Ebene belegt
ist, steht oben: die Zeit faellt wie erwartet, und die Vorgabe ist unberuehrt. Was **nicht**
belegt ist: dass `n > 1` die Lieferquote oder die Selbst-Aneignung nicht beruehrt.

Der offene Punkt aus der Pruefstandsmessung bleibt offen: der volle Fit folgt widersprechender
Erfahrung rund dreimal staerker, und ob ein Plan das auffaengt, war mit einem Seed nicht zu
entscheiden. Das ist jetzt messbar - vorher war es das nicht.

# Nachtrag: das A/B ist gefahren, die Vorgabe steht auf 4

`FULL_EVERY=1` gegen `4`, je 200 Episoden: Lieferquote 52,5 gegen 51,5 % (p = 0,92),
Selbst-Aneignung ununterscheidbar, Laufzeit 4,74 gegen 2,95 h. Kein Grund gegen die Umstellung
gefunden; der Nutzer hat sie am 2026-09-08 angeordnet. Zahlen und Vorbehalte:
[Sparsamer Welt-Fit, A/B](/befunde/welt-fit-plan-ab.md).

Geprueft **ohne jede Umgebungsvariable** auf einer Kopie des 11273-Zeilen-Zustands: Lernphase
73,1 s (voll) gegen 16,4 / 16,5 / 16,3 s (kurz) im Muster voll-kurz-kurz-kurz-voll, und
`ACT23_WORLD_*` taucht in der Zeile "Abweichungen von der Vorgabe" nicht mehr auf.

**Was sich im Alltag sichtbar aendert:** in drei von vier Kredit-Zeilen steht jetzt
`, Fit 20 Epochen`. Das ist Absicht - ohne die Markierung waere in keiner spaeteren Auswertung
trennbar, welche Episode mit welchem Fit lief.

**Was offen bleibt:** "Griff hielt nicht" lag im A/B bei 11,0 gegen 17,0 % (p = 0,11). Nicht
signifikant, aber der einzige Wert mit Richtung. Steigt die Rutschquote im naechsten Langlauf
spuerbar, ist das der erste Verdaechtige und `ACT23_WORLD_FULL_EVERY=1` die Gegenprobe.

# Verwandt

* [Welt-Fit: Warmstart](/befunde/welt-fit-warmstart.md) - die Messung dahinter
* [Episodendauer](/befunde/episodendauer.md)
* [Invarianten](/mechanismen/invarianten.md) - warum der Zaehler auf Modulebene liegt
