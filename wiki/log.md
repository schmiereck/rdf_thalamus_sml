# Chronik

Neueste zuerst. Datumsueberschriften in ISO-Form `YYYY-MM-DD`. Ein Eintrag je Vorgang, das
fuehrende fette Wort ist Konvention: **Anlage**, **Ergaenzung**, **Widerlegung**, **Ruecknahme**.

Fuer eine schnelle Uebersicht: `grep "^## " wiki/log.md | head -5`

## 2026-09-07

* **Anlage**: [Sparsamer Welt-Fit, A/B](/befunde/welt-fit-plan-ab.md) - `FULL_EVERY=4` gegen die
  Vorgabe `1`, je 200 Episoden im vollen Steuerungslauf, gleichzeitig gefahren. Lieferquote
  51,5 gegen 52,5 % (p = 0,92), Selbst-Aneignung ununterscheidbar (beide Arme gebaeren **keine**
  neue Klasse), Laufzeit 2,95 statt 4,74 h. **Die Pruefstandsvorhersage haelt diesmal auf
  act23-Ebene.** Vorbehalte in der Seite: "Griff hielt nicht" 11,0 gegen 17,0 % (p = 0,11) ist
  der einzige Wert, der gegen B lehnt, und die Anfahrgenauigkeit wurde mangels
  `ACT16_GLAUBDIAG` nicht mitgemessen. Vorgabe bleibt `1`.

* **Anlage**: [ACT23_WORLD_FULL_EVERY](/entscheidungen/welt-fit-plan.md) - auf Nutzerauftrag
  gebaut. Jede n-te Episode voller Fit, dazwischen kurz; **Vorgabe 1 = zifferngenau das
  bisherige Verhalten** (der kurze Zweig wird nicht betreten, `EPOCHS_SHORT` nicht gelesen).
  Umgestellt ist genau eine der sechs `epochs=600`-Stellen; der Anfangsfit (2055) bleibt voll.
  Im echten Lauf auf einer Kopie des 11273-Zeilen-Zustands: Lernphase 73,0/73,1 s voll gegen
  16,6/16,8 s kurz, Kontrolle ohne Schalter 73,4/73,7 s und 0 Markierungen. Die ersten beiden
  Episoden sind in beiden Laeufen zifferngenau gleich.

* **Anlage**: [Welt-Fit: Warmstart](/befunde/welt-fit-warmstart.md) - auf Nutzerfrage zum Hebel
  aus [Episodendauer](/befunde/episodendauer.md). Antwort: `Policy.fit` setzt die Gewichte nie
  zurueck, **der Fit ist bereits ein Warmstart**. Die MSE steht nach EINER Epoche
  (0,0854 -> 0,0844, danach +-0,001 ueber 599 weitere); mu und sigma weichen bei 5 bis 200
  Epochen **weniger** vom 600er-Fit ab als zwei 600er-Fits mit verschiedenen Seeds voneinander.
  Einziger gemessener Vorteil der 600 Epochen: rund dreifache Aufnahmekraft fuer
  widersprechende Erfahrung. Ein Plan "voll alle 4 Episoden, sonst 20" kostet 16,7 statt
  61,1 s je Episode bei ungeklaertem Abstand in der Aufnahme. Nebenbefund: das Modell folgt
  widersprechenden Etiketten in **keiner** Einstellung nennenswert - passt zu AUC 0,489.
  `ebene: pruefstand`, also **kein** Beleg fuer eine Wirkung auf act23.

* **Anlage**: [Rechnerlast und Lieferquote](/befunde/rechnerlast.md) - der lange gehegte Verdacht
  des Nutzers, die Lieferquote haenge an der CPU-Auslastung, ist mit zwei natuerlichen
  Lastfenstern (185 gegen 747 Episoden, p = 0,41, **die beiden Fenster widersprechen einander**)
  und einem Bitgleichheitstest der Physik unter 12-Kern-Volllast widerlegt. Auch die
  Nutzerhypothese "unter Last aendert sich Reibung oder Gravitation" faellt: Rutschquote flach
  (p = 0,51), Griffdruck je Objekt in verschiedene Richtungen, `qpos` auf 17 Stellen identisch.
  Die Seite traegt die **Nachweisgrenze fuer act23-A/Bs**: ein 50-Episoden-Fenster schwankt
  allein aus Zufall um 26 Punkte.
* **Anlage**: [Episodendauer](/befunde/episodendauer.md) - die `Lernen`-Phase ist exakt
  `world.train(600)` (173/173 gegen 759/759 trennscharf) und steigt unter Last von 77 auf 130 s.
  Ein Sprung, keine Rampe: **die Verlangsamung kommt nicht vom wachsenden Wissen.** Nennt den
  ungenutzten Hebel - 600 Epochen ueber 10500 Zeilen je Episode fuer eine neue Zeile.
* **Anlage**: [Ablenker-Bindung in der Anfahrt](/befunde/ablenker-anfahrt.md) - aus einer
  Nutzerbeobachtung zu `[Auto 810]`. Die Adressierung ist entlastet (Median 2 mm, 914/920
  eindeutig), der Fehler sitzt in der Ausfuehrung: 63 von 932 Episoden fahren die erste Anfahrt
  >80 mm daneben und liefern dann 1 von 63. Enthaelt die ehrliche Schwaeche der
  Permutationskontrolle.
* **Ergaenzung**: [Invarianten](/mechanismen/invarianten.md) um zwei Regeln aus dem Startabsturz
  vom 06.09. - `state.OBJECTS` haelt **Adressen, nicht Koerper**, und eine Aenderung am
  persistierten Zustand braucht eine Speichern-Neustart-Runde (alle Sonden liefen mit
  `ACT23_NO_PERSIST=1` und konnten den Fehler prinzipiell nicht finden).

* **Ergaenzung**: die Belege, auf die das Wiki zeigt, sind jetzt selbst versioniert -
  `ARCHITECTURE_2026-07-25.md` (Quelle von [Modullandschaft](/mechanismen/act23-modullandschaft.md)
  und [Laufzeitregeln](/mechanismen/laufzeit-regeln.md)) sowie `act23_exec_variance.py` und
  `act23_split_probe.py` (in [Rohbelege](/raw/index.md) als Messwerkzeuge gelistet, bis dahin als
  einzige der acht nicht im Repo). Ein frischer Klon kann die
  [Messvorschriften](/messungen/exekutionsvarianz-exv.md) damit nachvollziehen.
* **Ergaenzung**: Nutzerentscheid zur offenen Frage aus
  [Wissensbasis als Wiki](/entscheidungen/wissensbasis-als-wiki.md) - **der act23-Teil des
  Memory-Bestands wandert ins Wiki**, die aelteren Akte (act5-act22) bleiben liegen; die alten
  Markdown-Dateien im Wurzelverzeichnis bleiben, wo sie sind, und werden nur referenziert.
* **Anlage**: Uebertragung der act23-Notizen. Neue Mechanismus-Seiten
  [Invarianten](/mechanismen/invarianten.md),
  [Wahrnehmungs-Splits](/mechanismen/wahrnehmungs-splits.md),
  [Formklassen-Lebenszyklus](/mechanismen/formklassen-lebenszyklus.md),
  [Kredit und Selbst-Urteil](/mechanismen/kredit-und-selbsturteil.md),
  [Fovea und Blick](/mechanismen/fovea-und-blick.md),
  [Eigenschafts-Kommando](/mechanismen/eigenschafts-kommando.md),
  [Ports und Takte](/mechanismen/ports-und-takte.md).
* **Anlage**: neue Befunde [Wrist-Ausrichtung](/befunde/wrist-ausrichtung.md),
  [U-Form-Engpass](/befunde/u-form-engpass.md), [Imitationspuffer](/befunde/imitationspuffer.md),
  [Ablage und Platzieren](/befunde/ablage-und-platzieren.md),
  [Nagelneigung](/befunde/nagelneigung.md),
  [Griff-Glaube und Tastsinn](/befunde/griff-glaube-und-tastsinn.md),
  [Aneignung neuer Formen](/befunde/aneignung-neuer-formen.md),
  [Formfaktorisierung](/befunde/formfaktorisierung.md),
  [Latent-Etappen](/befunde/latent-etappen.md); dazu
  [Latente Augmentierung](/fragen/latente-augmentierung.md).
* **Anlage**: neues Verzeichnis `chronik/` mit der
  [act23-Entwicklungslinie](/chronik/act23.md) - Verdichtung der 1001-zeiligen Volltext-Chronik
  aus dem Memory-Bestand.
* **Anlage**: Wiki aufgesetzt nach [Das Verfahren](/wiki.md) - Struktur, Frontmatter mit
  `evidenz` und `ebene`, Katalog und Chronik. Vorlagen: LLM Wiki (Karpathy) fuer die Idee,
  Open Knowledge Format v0.2 fuer das Format; angepasst darauf, dass das Wissen hier selbst
  erzeugt wird statt von aussen zu kommen.
* **Anlage**: [Projektziel](/ziel.md), [Die Wissensbasis wird ein Wiki im Repo](/entscheidungen/wissensbasis-als-wiki.md).
* **Anlage**: Mechanismen - [Modullandschaft](/mechanismen/act23-modullandschaft.md),
  [Laufzeitregeln](/mechanismen/laufzeit-regeln.md),
  [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md).
* **Anlage**: Befunde - [Exekutionsvarianz](/befunde/exekutionsvarianz.md),
  [1109 Episoden ohne Lernfortschritt](/befunde/langlauf-ohne-fortschritt.md),
  [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md),
  [Greif-Lerndeckel](/befunde/greif-lerndeckel.md). Alle vier verdichtet aus dem
  Memory-Bestand, nicht neu gemessen.
* **Anlage**: Messvorschriften [kopfloses A/B](/messungen/act23-headless-ab.md) und
  [EXV](/messungen/exekutionsvarianz-exv.md); [offene Faeden](/fragen/offene-faeden-act23.md);
  [Rohbelege](/raw/index.md).
* **Anlage**: `CLAUDE.md` im Wurzelverzeichnis als Schemaschicht - sie verpflichtet jeden
  Agenten, das Wiki zu lesen und fortzuschreiben.

## Davor

Das Projektwissen lag bis hierher im agenteneigenen Memory-Bestand und in verstreuten
Markdown-Dateien im Wurzelverzeichnis. Deren Chronik ist nicht rueckwirkend aufgearbeitet;
`generated.at` auf den einzelnen Seiten traegt das Datum der urspruenglichen Messung.
