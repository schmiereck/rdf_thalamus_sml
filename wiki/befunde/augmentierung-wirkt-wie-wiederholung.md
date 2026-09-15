---
type: Befund
title: Die latente Augmentierung wirkt genau wie eine Zeilenwiederholung - der Beitrag der Vorstellung selbst ist +0,0006 AUC
description: In beiden geprueften Regimen ist eine vorgestellte Zeile von einer exakten Kopie nicht zu unterscheiden. Im vollen Puffer schaden beide gleich viel (-0,051 gegen -0,052), in dem Regime, fuer das die Augmentierung gebaut ist, nuetzen beide gleich viel (+0,0154 gegen +0,0148). Der Unterschied ist +0,0006 - die aequivariante Variation traegt nichts bei, was das Weltmodell nutzen koennte. Drei eigene Erklaerungsversuche dafuer sind gemessen falsch.
tags: [act23, latent, augmentierung, weltmodell, negativ]
status: stable
evidenz: gemessen
ebene: pruefstand
generated: { by: claude/opus-5, at: 2026-09-14T00:00:00Z }
sources:
  - id: offline
    resource: "Offline auf einer Kopie von act23_state.pkl (12322 Weltzeilen): reiner Halteteil aus echten Zeilen, Training wahlweise mit Vorstellungen, mit exakten Kopien oder ohne; 3 bzw. 5 Seeds"
    title: Augmentierung gegen Wiederholung
  - id: bau
    resource: /mechanismen/latente-augmentierung-gebaut.md
    title: Der Bau, dessen Wirkung hier geprueft wird
---

# Warum offline und nicht im Lauf

Bestellt war ein A/B-Lauf. Die Zielgroesse - die Generalisierungs-AUC des Weltmodells - laesst sich
aber **ohne Lauf** pruefen, weil die Augmentierung eine reine Funktion einer Pufferzeile ist. Das
kostet Minuten statt Stunden und ist schaerfer, weil beide Seiten denselben Puffer sehen.

**Der Halteteil musste dafuer von Hand gebaut werden.** `generalisation_auc` nimmt die LETZTEN
Zeilen als Test; eine vorgestellte Zeile dort haette ihr Original im Training - ein
Beinah-Duplikat, das die AUC aufblaest. Der Halteteil besteht hier ausschliesslich aus echten
Zeilen, augmentiert wird nur der Trainingsteil.

# Das Ergebnis

    voller Puffer (10322 Trainingszeilen, davon 690 = 6,7 % augmentierbar)
      ohne          0,7401
      vorgestellt   0,6899   (-0,0502)
      wiederholt    0,6888   (-0,0513)      <- exakte Kopien, kein Versatz
      Unterschied Vorstellung gegen Wiederholung:  +0,0011

    nur die 690 Zeilen mit gueltigem Nachbar-Block (das Regime, fuer das gebaut wurde)
      ohne          0,7212
      vorgestellt   0,7366   (+0,0154)
      wiederholt    0,7360   (+0,0148)
      Unterschied Vorstellung gegen Wiederholung:  +0,0006

**In beiden Regimen ist eine vorgestellte Zeile von einer exakten Kopie nicht zu unterscheiden.**

~~Das erklaert auch das Vorzeichen: der Verlust von 0,05 ist die **Umgewichtung** der 690
augmentierbaren Zeilen.~~

> **DIESE ERKLAERUNG IST WIDERLEGT (2026-09-15).** Dieselbe Fuenffachgewichtung ueber `weight`
> statt ueber Duplikate kostet nur **-0,003** statt -0,051 - um mehr als eine Groessenordnung
> weniger. Waere die Umgewichtung die Ursache, muesste sie sich so reproduzieren lassen.
> Siehe [Keine Hoehergewichtung bringt etwas](/befunde/gewichtung-bringt-nichts.md).
>
> **Was die -0,051 verursacht, ist offen.** Duplikat und Gewicht sind hier nicht dasselbe: ein
> Duplikat aendert Zeilenzahl, Bootstrap-Zug und Stichprobenzahl je Epoche, `weight` nur den
> Verlustbeitrag. Welcher Unterschied die Zahl traegt, ist ungemessen.

**Der Kernbefund bleibt davon unberuehrt:** *vorgestellt ist von wiederholt nicht zu unterscheiden*
ist ein direkter Vergleich zweier Varianten unter denselben Bedingungen und haengt an keiner
Deutung des Vorzeichens.

> **Die aequivariante Variation traegt nichts bei.** Sie wirkt wie eine Zeilenwiederholung - was
> das seinerseits bewirkt, blieb zunaechst offen und ist inzwischen eingegrenzt: eine reine
> Umgewichtung ist es NICHT (s. Kasten oben).

# Zwei eigene Erklaerungen, beide gemessen falsch

**Erster Versuch: "das Weltmodell ignoriert die Lage, deshalb bringt eine Verschiebung nichts."**
Widerlegt. Merkmalsbloecke im Halteteil vertauschen und den AUC-Verlust messen:

    Aktion             +0,1920
    Lage (pos xy)      +0,1458      <- zweitwichtigster Block
    Winkelphasen       +0,1423
    Formeinbettung     +0,1179
    Nachbar-Block      +0,0000      <- dritte Bestaetigung, s. unten

**Zweiter Versuch: "es nutzt die Lage nur grob, 20 mm sind darin ein Punkt."** Ebenfalls
widerlegt. Den Halteteil um r verschieben statt vertauschen:

     5 mm  ->  +0,0226 AUC-Verlust
    10 mm  ->  +0,0426
    20 mm  ->  +0,0731      (die Haelfte des gesamten Lage-Signals)
    40 mm  ->  +0,1067
    80 mm  ->  +0,1235
    vertauscht +0,1458

**Das Modell liest die Lage fein.** Schon 5 mm kosten messbar, 20 mm kosten die Haelfte dessen, was
ein vollstaendiges Vertauschen kostet.

Damit bleibt ein unbequemer Befund ohne bequeme Erklaerung: das Modell behandelt eine um 20 mm
verschobene Lage als **deutlich andere Situation** - und trotzdem aendert es nichts, ob man ihm
diese andere Situation mit demselben Etikett zeigt oder einfach die alte noch einmal. Zwei
Wirkungen, die sich aufheben koennten (lokales Glaetten hilft, falsche Etiketten schaden), oder
ein Effekt unterhalb der Aufloesung dieser Messung. **Gemessen ist die Differenz, nicht ihre
Ursache.**

# Der Nachbar-Block, zum dritten Mal

`+0,0000` AUC-Verlust beim Vertauschen. Das deckt sich mit
[Der Nachbar-Block steht auf 6 Prozent der Zeilen](/befunde/merkmale-kommen-zu-spaet.md)
(+0,004 AUC auf den gueltigen Zeilen allein) und ist hier unabhaengig reproduziert: **das
Weltmodell benutzt die Nachbar-Information nicht.** Fuer die Augmentierung ist das eine Ironie -
sie BRAUCHT den Block als Zulaessigkeitsschranke, und derselbe Block traegt zur Vorhersage nichts
bei.

# Folgen

**Kein A/B-Lauf.** Ein Beitrag von +0,0006 AUC ist bei 150 bis 300 Episoden nicht aufzuloesen; ein
Lauf waere genau das Muster, an dem diese Sitzung schon sieben Vergleiche verloren hat. Die
Offline-Messung ist hier die schaerfere, nicht die schwaechere.

`ACT23_AUGMENT` bleibt auf `0`. Der Bau bleibt samt Begruendung im Code: er ist korrekt, er ist
gemessen unschaedlich, und er waere sofort einsetzbar, falls das Weltmodell einmal ein Merkmal
bekommt, das auf der Laengenskala der Vorstellung etwas unterscheidet.

~~**Was statt dessen billiger zu haben waere:** dieselbe Wirkung ueber `weight` bei `observe`.~~
**Geprueft und ebenfalls negativ** (2026-09-15): kein Gewichtungsschema hilft, das beste liegt
mit +0,004 in der Streuung des Bezugs. Siehe
[Keine Hoehergewichtung bringt etwas](/befunde/gewichtung-bringt-nichts.md).

# Fallen

* **`ebene: pruefstand`.** Gemessen ist die Generalisierungs-AUC auf einem stehenden Puffer, nicht
  der geschlossene Kreis (besseres Modell -> bessere Aktionswahl -> andere Daten). Bei einem
  Modellunterschied von +0,0006 hat der Kreis allerdings nichts zu verstaerken.
* **690 Zeilen im zweiten Regime** sind wenig, und der Halteteil dort umfasst 120 Zeilen mit
  43 Positiven. Die Streuung ueber 5 Seeds ist entsprechend gross (-0,006 bis +0,043); die
  DIFFERENZ Vorstellung-gegen-Wiederholung ist trotzdem stabil klein.
* **Die Vertausch-Analyse misst, worauf das Modell REAGIERT, nicht was kausal zaehlt.** Ein Block
  kann wichtig aussehen, weil er mit etwas anderem korreliert.

# Verwandt

* [Die latente Augmentierung, gebaut](/mechanismen/latente-augmentierung-gebaut.md) - der Bau
* [Die Daempfungsfunktion](/befunde/daempfungsfunktion.md) - die Regeln, nach denen er gebaut ist
* [Der Nachbar-Block steht auf 6 Prozent der Zeilen](/befunde/merkmale-kommen-zu-spaet.md) - hier unabhaengig bestaetigt
* [Keine Hoehergewichtung bringt etwas](/befunde/gewichtung-bringt-nichts.md) - die Nachpruefung, die eine Deutung hier widerlegt
* [Latente Augmentierung](/fragen/latente-augmentierung.md) - die Idee
