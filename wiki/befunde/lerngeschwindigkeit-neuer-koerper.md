---
type: Befund
title: Lerngeschwindigkeit mit neuem Koerper - drei von vier Laeufen eignen ihn sich an, nach 41 bis 75 Episoden; der Engpass ist die Wartezeit zwischen Geburt und Knopf
description: Nutzerauftrag. Vorab gemessen - obj_Y ist fuer den heutigen Zustand NICHT mehr neu (die T-Klasse beansprucht es in 14 von 16 Lagen, am 02.09. wurde es noch in 15-28 Episoden angeeignet), ein Zylinder liest als Wuerfel (16/16). Am wenigsten zuordenbar sind ein Stern (7/16 neu) und ein V (6/16). Mit beiden als neuem Koerper, je zwei Seeds zu 100 Episoden - Geburt einer Klasse nach 9 bis 38 Episoden, Knopf (kommandierbar) in 3 von 4 Laeufen nach 41, 68 und 75 Episoden, einmal gar nicht. Zwischen Geburt und Knopf liegen 30 bis 56 Episoden. Danach nur 4 bis 7 Kommandos je Lauf, 5 von 16 geliefert (31 Prozent gegen 44-54 Prozent Hausquote) - fuer eine motorische Lernkurve zu wenig.
tags: [act23, selbstlernen, formklassen, lernen, nutzeridee]
status: stable
evidenz: einzelmessung
ebene: act23-ab
generated: { by: claude/opus-5.5, at: 2026-09-25T00:00:00Z }
sources:
  - id: sonde
    resource: "Pruefstand auf act23_state.pkl (ad9d768c): je Koerper 16 Lagen, shape_clf.resolve gegen novel_th 7,72"
    title: Wie neu ist ein neuer Koerper fuer den heutigen Zustand
  - id: lauf
    resource: "Code 706c7f8 (act14: obj_Zyl/obj_V/obj_Stern nur bei Bedarf im Modell, ohne Schalter bitgleich geprueft). Kopien von act23_state.pkl, ACT23_NOVEL_BODY=obj_Stern bzw. obj_V, Seeds 11 und 23, je 100 Ep, sonst Vorgaben (NOVEL_EVERY 6, SCENE_EVERY 10); zwei Prozesse je Block"
    title: Vier Aneignungslaeufe
---

# Die Frage

Nach dem [Ruecksetz-Versuch](/befunde/ruecksetz-versuch.md) ist Lerngeschwindigkeit nur dort
messbar, wo das Lernziel noch nicht erreicht ist. Nutzerauftrag: mit einem **neuen Koerper**
messen - wie schnell eignet sich der Agent ihn an (erkennen, benennen, kommandieren, liefern)?

# Vorab: was ist fuer den heutigen Zustand ueberhaupt neu?

Ein Vorlauf mit obj_Y (Seed 11, 40 Episoden) ergab **nichts** - keine Geburt, null unzuordenbare
Sichtungen. Am 02.09. war obj_Y in 15 bzw. 28 Episoden angeeignet
([dort](/befunde/aneignung-neuer-formen.md)). Die Sonde zeigt warum:

    Koerper             als neu gesehen   zugeordnet zu
    obj_Zyl (34 mm)          0 / 16        Wuerfel 16
    obj_V   (60 Grad)        6 / 16        T-Klasse 7, Wuerfel 7
    obj_Stern (6 Arme)       7 / 16        Wuerfel 7, Kreuz 2
    obj_Y                    5 / 16        T-Klasse 14
    obj_T (Kontrolle)        0 / 16        T-Klasse 15
    obj_red (Kontrolle)      0 / 16        Wuerfel 16

**Die Wahrnehmung fasst neue Formen grosszuegig mit bekannten zusammen.** Ein runder Koerper ist
ein Wuerfel; das Y ist inzwischen ein T. Das ist Generalisierung - und zugleich das Ende der
Neuheit: was der Agent einer bekannten Klasse zuordnet, eignet er sich nicht als eigenes Ding an.
Dass die T-Klasse obj_Y seit dem 02.09. schluckt, spricht dafuer, dass sie seither breiter geworden
ist; nicht untersucht.

Die drei Kandidaten stehen NICHT in der Modelldatei, sondern werden nur bei Bedarf eingefuegt
(`ACT14_NEUE_KOERPER=1` oder `ACT23_NOVEL_BODY` auf einen von ihnen). Grund, gemessen: schon drei
geparkte Zusatzkoerper veraendern den Ablauf (Seed 11, Episode 2: 31 gegen 40 mm). Ohne Schalter
ist der Lauf wieder bitgleich.

# Ergebnis: vier Aneignungslaeufe

    Lauf          Geburt (Kandidat)   Knopf     Geburt->Knopf   kommandiert   geliefert   Haus
    Stern, 11     Ep 9, Ep 40          --           --              0            --        48 %
    Stern, 23     Ep 11                Ep 41        30              7            1 / 7     44 %
    V, 11         Ep 12, Ep 51         Ep 68        56              4            2 / 4     46 %
    V, 23         Ep 38, 48, 67, 72    Ep 75        37              5            2 / 5     54 %

    unzuordenbare Sichtungen je Lauf nach 20 / 50 / 100 Ep:  5/11/20, 5/17/30, 6/9/24, 4/13/34

1. **Die Aneignung gelingt** - in drei von vier Laeufen wird der neue Koerper ohne jedes Etikett
   kommandierbar. Einmal (Stern, Seed 11) nicht innerhalb von 100 Episoden.
2. **Sie dauert 41 bis 75 Episoden, und der groesste Teil davon ist Warten zwischen Geburt und
   Knopf** (30 bis 56 Episoden). Die Klasse ist frueh da (Ep 9-38); bis sie oft genug auf DEMSELBEN
   Koerper bestaetigt ist, vergeht die meiste Zeit. Plausible Ursache, nicht gemessen: der Koerper
   steht nur zeitweise in der Szene (alle 6 Episoden hingestellt, alle 10 umgebaut).
3. **Danach bleibt zu wenig Zeit fuer eine motorische Lernkurve**: 4 bis 7 Kommandos je Lauf,
   zusammen 5 von 16 geliefert (31 %) gegen 44-54 % Hausquote. Ob der Agent den neuen Koerper
   zu greifen LERNT oder sofort auf seinem Uebertragungsniveau liegt, ist daraus nicht zu lesen.

# Was die Lerngeschwindigkeit hier zeigt

> **GEMESSEN 2026-09-26:** die Direkt-Adresse verkuerzt die Zeit bis zum ersten Kommando auf 8-22
> Episoden, in allen vier Paaren - s. [dort](/befunde/direkt-adresse-verkuerzt-aneignung.md).

Sie misst **nicht das Lernen, sondern die Vergabe**: der Agent hat die Klasse schnell, die
Kommandierbarkeit spaet. Das ist die bekannte
[Vergabe-Engstelle](/befunde/vergabe-engstelle-diagnose.md), jetzt mit einer Zeitangabe. Damit ist
Lerngeschwindigkeit eine brauchbare Messgroesse fuer eine STRUKTURAENDERUNG an genau dieser Stelle
- etwa die Adresse ohne Klasse (`ACT23_EIG_DIREKT`, "eine Sichtung statt der Kette"): verkuerzt sie
die Zeit bis zum ersten Kommando?

# Fallen

* **Zwei Koerper, zwei Seeds, 100 Episoden.** Zeitpunkte je Lauf, keine Verteilung.
* **Nicht vergleichbar mit obj_Y vom 02.09.** Anderer Koerper, anderer Code, anderer Neuheitsgrad.
* **Die Knopf-Bindung ist an den Probe-Koerper verdrahtet** - eine Geburt auf einem anderen Koerper
  zaehlt nicht. Gezaehlt ist nur der Weg bis zum Kommando, nicht jede Aneignung.
* **Die Neuheit ist nur teilweise**: 6-7 von 16 Lagen lesen als neu. Ein voellig neuer Koerper waere
  schneller - es gibt im heutigen Zustand offenbar keinen.

# Verwandt

* [Ruecksetz-Versuch](/befunde/ruecksetz-versuch.md) - warum auf Neuem gemessen wird
* [Aneignung neuer Formen](/befunde/aneignung-neuer-formen.md) - obj_Y am 02.09.
* [Die Vergabe-Engstelle](/befunde/vergabe-engstelle-diagnose.md)
* [Stetig adressieren statt Klassen vergeben](/fragen/stetige-adressierung.md)
* [Struktur-Experte](/fragen/struktur-experte.md)
