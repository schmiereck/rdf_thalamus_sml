---
type: Mechanismus
title: Die Pruefstandsfalle
description: Isolierte Teilmessungen haben in diesem Projekt dreimal das Gegenteil dessen vorhergesagt, was ein sauberes act23-A/B dann zeigte. Deshalb traegt jede Wiki-Seite das Feld `ebene`.
tags: [methodik, messen]
status: stable
evidenz: gemessen
ebene: act23-ab
generated: { by: claude/opus-5, at: 2026-09-07T00:00:00Z }
sources:
  - id: bestand
    resource: "Memory-Bestand act23-nagelneigung, act23-faktorisierung, act23-fingerdruck-ersatz"
    title: drei dokumentierte Fehlvorhersagen
---

# Behauptung

Ein Ergebnis aus einem isolierten Teilaufbau sagt den vollen act23-Lauf **in keiner Richtung**
vorher. Das ist hier dreimal aufgetreten, jedesmal mit derselben Struktur: der Prueftstand zeigt
einen klaren, oft grossen Effekt, das saubere act23-A/B zeigt nichts.

# Zahlen

| Fall | Prueftstand sagt | act23-A/B sagt |
|---|---|---|
| **Nagelneigung** (57,3 Grad -> 20 Grad) | der Nagel traegt 95 % der Griffkraft | -2,0 Punkte, p = 0,76 |
| **Dicken-Wache** (Groesse dominiert Form) | Wache feuert: Ansprueche -36 %, Neuheit x3 | Engpass unberuehrt - er sitzt bei der Klassen-**Geburt**, nicht am Anspruch |
| **Fingerdruck als Schliess-Signal** | Kontaktsignal ist vorhanden | dreifach gemessen: traegt die Entscheidung nicht |

# Bewertung

Der gemeinsame Grund ist nicht Zufall: ein isolierter Aufbau haelt genau die Groessen fest, die
im vollen Lauf mitwandern. Der Prueftstand misst deshalb einen **Mechanismus**, der volle Lauf
misst einen **Engpass**. Ein Mechanismus, der nicht der Engpass ist, wirkt nicht.

Das heisst **nicht**, dass Pruefstaende wertlos sind. Sie sind gut darin, eine Ursache zu
lokalisieren und eine Hypothese zu toeten. Sie sind untauglich, eine Wirkung auf die Lieferquote
oder die Selbst-Aneignung zu **behaupten**.

# Fallen

Zwei weitere Messfehler, die hier real passiert sind und die dieselbe Kategorie betreffen:

* **Bewertung ueber einen benachbarten Halteteil ist zu optimistisch.** Aufeinanderfolgende
  Pufferzeilen stammen aus demselben GUI-Lauf, in dem die Szene stehenbleibt - Testzeilen haben
  Beinah-Duplikate im Training. AUC 0,860 bei Luecke 0 gegen 0,656 bei Luecke 3000. Kuenftig
  nach **Zeit mit Luecke** oder nach Lauf/Szene teilen, nie zufaellig.
  Siehe [Exekutionsvarianz](/befunde/exekutionsvarianz.md).
* **Prozesskontext als Konfounder.** Der Sprung 44,7 % -> 56,4 % zwischen zwei Langlaeufen war
  **nicht** der geaenderten Greifergeometrie zuzuschreiben (das A/B fand dafuer nichts), sondern
  Zustand und Prozesskontext. Siehe [Vorgaben 2026-08-30](/entscheidungen/defaults-2026-08-30.md).

# Folgen

Jede Wiki-Seite traegt `ebene` im Frontmatter. Eine Aussage ueber Wirkung auf act23 braucht
`ebene: act23-ab` oder `langlauf`; alles darunter ist Lokalisierung, nicht Wirkung. Siehe
[Das Verfahren](/wiki.md).
