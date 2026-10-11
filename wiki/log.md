# Chronik

## 2026-10-11

* **Nachtrag 2**: [Balken-Welt: schraeg schadet nicht](/befunde/balken-welt-schraeg.md) - Schalter
  ACT23_BALKEN_LAENGE; langer schmaler Balken 100/130 x 12/18 mm (auch mit Klaue bis 37 mm), je 12 Ep quer gegen 45 Grad:
  kein Gefaelle (21/48 gegen 22/48). Welt-Fehler gefunden: geom_rbound/aabb des gestreckten Balkens bleiben beim
  24-mm-Wuerfel (120-mm-Balken: 0 statt 4 Kontakte an den Enden); mit LAENGE nachgefuehrt, Vorgabe unveraendert.

* **Nachtrag + Berichtigung**: [Balken-Welt: schraeg schadet nicht](/befunde/balken-welt-schraeg.md) - Schalter
  ACT23_KLAUE_OFFEN_MAX (Anschlag am Greifermotor). Klaue bis 44/37/34 mm und Balken 10-29 g / Reibung 1,7-2,0, je 12 Ep
  quer gegen 45 Grad: kein Gefaelle (Klaue gepoolt 17/36 gegen 13/36, p = 0,47). Schraeg haelt auch ohne Eindrehen
  (Median 1 Grad) - "die Klaue dreht ihn ein" war nicht der Grund. Berichtigt: die Klaue oeffnet innen 56 mm, nicht 24.

* **Anlage**: [Balken-Welt: schraeg schadet nicht](/befunde/balken-welt-schraeg.md) - Schalter
  ACT23_BALKEN_BREITE/MASSE/REIBUNG, ACT23_SZENE_MIT, ACT23_FORCE_WRIST=rel:<Grad>; Pruefstand 90 gegen 45 Grad in
  8 Welten: kein Gefaelle. Klaue dreht den Balken ein; wo nicht (schwer+griffig), scheitert auch quer. 10x-Arme wegen
  Speichermangel abgebrochen, nicht neu gestartet.

* **Ergaenzung + Berichtigung**: [Klauenlage und Griffversatz](/befunde/klauenlage-und-griffversatz.md) - Messzeile
  [Schub] (ef282a4), 60 Episoden L/T/X: beim Absenken bewegt sich das Objekt nicht (Median 0 mm), beim Schliessen
  4 mm (T 7 mm, 8,5 Grad), meist zur Klauenmitte hin, ohne Zusammenhang mit der Lieferung. Berichtigt: "Schieben beim
  Absenken" war falsch; "entlang" ist gegen den Reichpunkt gemessen, die Backenmitte liegt 4-9 mm davor.

* **Ergaenzung**: [Klauenlage und Griffversatz](/befunde/klauenlage-und-griffversatz.md) - geprueft, ob die
  Versatzkette das Blickkorrektur-Negativ ([Aufmerksamkeit](/fragen/aufmerksamkeit-objekt-ziel.md)) entkraeftet: nein.
  Der Versatz entsteht unter der Klaue, wo der Blick verdeckt ist; der Sitz sagt die Lieferung je Form nicht
  vorher (96 Ep, gepoolt nur quer p = 0,016). Hinweis auf der Aufmerksamkeitsseite ergaenzt.

* **Ergaenzung**: [Klauenlage und Griffversatz](/befunde/klauenlage-und-griffversatz.md) - Messzeile
  [Versatzkette] (dd701c5), 60 Episoden L/U/T/X: Sehfehler Median 1 mm, 2-3 % der Streuung. Der Versatz beim
  Zufassen stammt je etwa zur Haelfte aus dem Schieben des Objekts beim Absenken (+6 mm in Anfahrtrichtung)
  und zu kurzem Reichen der Hand (-5 mm bei L/T/X); er sagt den Sitz beim Ablegen vorher (r = 0,50, p = 0,001).

* **Anlage**: [Klauenlage und Griffversatz](/befunde/klauenlage-und-griffversatz.md) - zwei Laeufe je 60
  Episoden mit den neuen Log-Zeilen (158c866). Balken: Klaue Median 65 Grad zur Laengsachse, nur 4/32
  quer; Achse auf 5 Grad gesehen, Klaue auf 0 Grad ausgefuehrt, Lieferung winkelunabhaengig (p = 0,98) -
  das Weltmodell hat keinen Grund fuer quer. Griffversatz: gesehen sagt die Ablage nicht vorher, wahr schon.
  Offener Punkt in [Verluste nach dem Anheben](/befunde/verluste-nach-dem-anheben.md) damit beantwortet.

* **Anlage**: [Verluste nach dem Anheben](/befunde/verluste-nach-dem-anheben.md) - 760 angehobene
  Episoden aus GUI-Lauf, Langlauf-A/B und Wertprobe-Kontrolle je Form zerlegt. L/U setzen knapp daneben
  ab (32/35 % gegen Wuerfel 11 %; obj_blue ist der Balken, am selben Tag berichtigt), Hand steht gleich weit vom Ziel, die Policy gleicht nur den mittleren
  Versatz in der Hand aus. Unterwegs verlieren die Zinkenformen nicht mehr als Wuerfel. Messfalle: `trug True` ist kein Anheben
  des kommandierten Objekts.

* **Anlage**: [Wertprobe lokaler Griff](/befunde/lokaler-griff-wertprobe.md) - Stufe 0 der
  formabhaengigen Griffwahl, gepaartes A/B 100 Aufgaben L/U/T/X: geliefert 49 gegen 66 (p = 0,019);
  L/U/T 42 gegen 43, Kreuz 7 gegen 23. Vorab-Kriterium verfehlt, Faden geschlossen; Konzeptseite
  auf widerlegt, Eintrag unter "Ausdruecklich geschlossen".

## 2026-10-10

* **Anlage**: [Formabhaengige Griffwahl](/fragen/formabhaengige-griffwahl.md) - Konzept nach der
  Nutzerbeobachtung. Am Code belegt, dass der Teilgriff "diese Zinke, quer zu ihr" nicht darstellbar ist.
  Stufe 0 ist eine Wertprobe (act23-A/B, nur L/U/T/X) mit Kriterium +10 Punkte; Abgrenzung gegen FORCE_GRASP=prong.

* **Ergaenzung**: [GUI-Lauf 2026-10-09](/befunde/gui-lauf-2026-10-09.md) - Abfall kopflos nachgemessen,
  2 x 300 Episoden: mit Kopf 51/45/44, ohne 48/40/39 je 100. Schwach, kopfunabhaengig, nicht signifikant
  (gepoolt p = 0,10); Kopf gegen ohne 140 gegen 127 (p = 0,32). Offener Arm: eingefrorenes Lernen.

* **Anlage**: [GUI-Lauf 2026-10-09](/befunde/gui-lauf-2026-10-09.md) - Nutzerlauf 667 Episoden zerlegt:
  Quote faellt im Lauf (55 -> 39 %), Tragen-Verluste rutschen schon beim Anheben, Fehlgriff-Kopf oeffnet
  bei lose gehaltenem Objekt; Messfalle der Ablage-Zeile; Nutzerbeobachtung Griffwahl festgehalten.

## 2026-10-09

* **Entscheidung**: [Fehlgriff-Kopf](/befunde/fehlgriff-kopf.md) ist Vorgabe in der Steuer-GUI
  (Nutzerentscheid; kopflose Laeufe behalten 0).

* **Ergaenzung**: [Fehlgriff-Kopf](/befunde/fehlgriff-kopf.md) - zweiter Seed (9223) bestaetigt:
  gehoben 81 gegen 66 (p = 0,01), geliefert 55 gegen 43 (p = 0,03). Gepoolt 200 Aufgaben: geliefert
  121 gegen 95 (p = 0,0005). evidenz -> gemessen.

* **Ergaenzung**: [Fehlgriff-Kopf](/befunde/fehlgriff-kopf.md) - mit Nachsehen nach dem Eingriff
  (Kamera sucht den eigenen Fleck): Neugriffe 10 statt 38 mm daneben; gehoben 80 gegen 68 (p = 0,03),
  geliefert 66 gegen 52 (p = 0,01), gepaart, ein Seed. Signifikanter Gewinn, Vorgabe bleibt 0 bis Nutzerentscheid.

## 2026-10-08

* **Anlage**: [Fehlgriff-Kopf](/befunde/fehlgriff-kopf.md) - eigener Kopf entscheidet das Neugreifen
  (offline 645/653, 1 Fehlalarm in 329). act23-A/B gepaart: gehoben 69 gegen 68, geliefert 55 gegen 52,
  nichts signifikant. Der Kopf oeffnet richtig, die Neugriffe zielen 38 mm daneben (Objekt beim Rutschen
  verschoben, kein Nachsehen). Ehrliches Negativ fuer die Quote; Vorgabe bleibt 0.

* **Anlage**: [Zwischen Zufassen und Anheben](/befunde/zwischen-zufassen-und-anheben.md) - Greif-Spur
  ueber 98 Episoden; Herausrutschen durch falschen Objektglauben (15 gegen 9 mm), danach Schweben an
  der Teacher-Schwelle. ACT16_NACHGRIFF_FIX gemessen: verschiebt nur den Haengepunkt, ehrliches Negativ.

* **Ergaenzung**: [Ablage im Netzbetrieb](/befunde/ablage-im-netzbetrieb.md) - Sitz in der Klaue vor dem Bau
  geprueft: der Gesamtgradient (79 -> 30 %) ist die Form; innerhalb der Formen kein sichtbarer Hebel.
  Ehrliches Negativ, nicht gebaut.

* **Anlage**: [Ablage im Netzbetrieb](/befunde/ablage-im-netzbetrieb.md) - 380 Episoden zerlegt: eigene
  Ablagen treffen 86 %; die Ablage ist nur der drittgroesste Verlust (9 %), hinter Hochbringen (20 %) und
  Verlieren unterwegs (11 %).

* **Ergaenzung**: [Noch an der Hand?](/befunde/halt-sehen.md) - Ablage nach dem Neugreifen: Efferenzkopie
  `_nachgreifen` (Oeffnen zum Nachgreifen beendet die Episode nicht) und Nachsehen (Kamera findet das
  gefallene Objekt, 4 mm). Ablage danach so gut wie die erste; Quote 49 / 50 / 52 / 51, nichts signifikant.

## 2026-10-07

* **Ergaenzung**: [Noch an der Hand?](/befunde/halt-sehen.md) - A/B je 100 Ep: 49 gegen 50 %
  (p = 1,00); der Agent erkennt Verluste selbst, die neu gegriffenen Objekte scheitern an der Ablage.
  Bestaetigt das positive Vorzeichen aus halt-kopf NICHT.

* **Anlage**: [Noch an der Hand?](/befunde/halt-sehen.md) - gelernter Vorschlag mit Kamera-Etikett;
  Lernlauf 100 Ep, Etikett 44/46 richtig; Verdrahtungsfehler behoben; A/B laeuft.

* **Ergaenzung**: [Haelt der Griff noch?](/befunde/halt-kopf.md) - A/B je 100 Ep nacheinander: 55 gegen
  51 % (p = 0,52), Verluste gerettet 4/6 gegen 2/8, Fehlalarme folgenlos. Vorgabe bleibt aus.

## 2026-10-06

* **Anlage**: [Haelt der Griff noch?](/befunde/halt-kopf.md) - Kopf gebaut, Sammellauf 100 Ep:
  11 Vorschlaege, 8 echte Verluste; Veto-Netz noch nicht bereit. A/B Modus 2 gegen 3 laeuft.

* **Anlage**: [Zufassen aus dem eigenen Ergebnis](/befunde/zufassen-selbst.md) - 76 Versuche, 84 %
  gehalten, Aspekte trennen nicht; Veto nicht gebaut. Nebenfund: unbemerktes Verlieren beim Tragen.

* **Anlage**: [Aufgeben aus eigener Erfahrung](/befunde/aufgeben.md) - ehrliches Negativ, 52,3 gegen
  45,9 %, 3 Seeds (vierter wegen Speichermangels abgebrochen).

* **Entscheidung**: [Loslassen am Ziel](/befunde/loslassen.md) - in der Steuer-GUI eingeschaltet
  (Nutzer); kopflose Laeufe unveraendert.

* **Ergaenzung**: [Loslassen am Ziel](/befunde/loslassen.md) - vollstaendiger Durchgang, 4 Seeds:
  nach der Lernphase 102/200 gegen 102/200 (Intervall +-9,8), Loslassen gelingt 81 statt 72 %.

* **Ergaenzung**: [Loslassen am Ziel](/befunde/loslassen.md) - Erfolgsnetz aus dem eigenen Ergebnis
  (`ACT23_LOSLASS_SELBST`): allein gescheitert (93 mm daneben), als Veto 83 statt 72 % gelungenes
  Loslassen, nach der Lernphase 53 gegen 51 % geliefert. Dritter Seed wegen Speichermangels abgebrochen.

* **Ergaenzung**: [Loslassen am Ziel](/befunde/loslassen.md) - Umetikettierung schadet dem Greifen
  nicht; "erst bei ruhiger Hand" wirkungslos (Kopf extrapoliert ausserhalb der Teacher-Etiketten);
  Schritt 3 nicht gefahren. Codex-Integration c745ce6 in main uebernommen (fast-forward).

## 2026-10-05

* **Integration geprueft**: [ACT23-Worktrees](/befunde/act23-worktree-integration.md) - main efb3ae2 und Codex daa44af vereinigt, neue Lernspeicher in D0-Freeze aufgenommen. FSM-/Netz-Rauchtest und mathematische Regressionen bestehen; eigener Zustand pro Lauf. 15-Kanal-Vertrag fuer aktuellen Claude-Checkpoint dokumentiert. Kein Leistungs-A/B.

* **Anlage**: [Rueckmeldung je Aspekt](/fragen/aspekt-rueckmeldung.md) - Nutzeridee, mit erstem Beleg.

* **Anlage**: [Loslassen am Ziel](/befunde/loslassen.md) - Teacher-Fehler `ACT16_ABLAGE_FIX`, Loslass-Kopf;
  laesst selbst los, liefert aber weniger (2 Seeds, wegen Speichermangels abgebrochen).

* **Anlage**: [Das Episodenende entscheidet der Agent selbst](/befunde/episodenende-selbst.md) -
  gepaart, 8 Seeds x 50: Orakel 53,1 %, selbst 60,7 %, Seeds 7:1. `ACT16_ENDE_SELBST` ist in act23
  Vorgabe. Gefunden: die Policy laesst am Ziel nicht los (das Orakel nahm es ihr immer ab).

* **Claudes Aspekt-Idee und Branch-Abstand gelesen**: [Analyse](/fragen/aspekte-und-worktree-integration.md).
  Einzelaspekte passen als Hypothese zum Koerpermodell; Loslassen im Pruefstand stark,
  im ACT23-Zwischenstand noch schlechter. 119/56 exklusive Commits, sechs gemeinsam
  bearbeitete Dateien. Kontrollierte Integration in drittem Worktree empfohlen, noch
  nicht ausgefuehrt; kein neuer Lauf und keine gemeinsamen Zustaende veraendert.

* **Native ACT23-Datengrundlage abgeschlossen**: [Befund](/befunde/act23-bewegungsdaten.md).
  3.035 Trainings-/5.979 Testübergänge und 362 Kamerabildpaare, tatsächliche ACT23-Bewegung
  bei unveränderter Kamera. Positionsport v2 umfasst sechs Servos und gemessene Grenzüberschreitungen.
  Zeit-/Sensoranschluss, Rundlauf, Hashes und Lern-Freeze bestehen. Noch kein Modellfit;
  nächster Vergleich sechs Gelenke/4 ms mit getrennter Episodenbewertung gegen Persistenz.

## 2026-10-04

* **Widerlegung**: [Flache Objekte tiefer greifen](/befunde/greifhoehe-flach.md) - Teacher auf
  16 mm 13/30 alt gegen 11/30 tiefer; die Kanten-Vermutung stand auf 9 Episoden. In
  [Neue Objekthoehen](/befunde/neue-hoehen-gelernt.md) korrigiert: 16 mm endet auf Teacher-Niveau.

* **Ergaenzung**: [Neue Objekthoehen](/befunde/neue-hoehen-gelernt.md) - zweiter Seed: 32 mm wird
  robust gelernt, 16 mm nicht; Ursache vermutlich die Teacher-Greifhoehe (Mitte + 6 mm = Kante).
  Evidenz auf `gemessen`.

* **Anlage**: [Neue Objekthoehen selbst gelernt](/befunde/neue-hoehen-gelernt.md) - `ACT23_HOEHEN`;
  die Policy lernt 16/32-mm-Objekte im Betrieb (15 -> 57 % bzw. 24 -> 63 % mit geschaetzter Hoehe).
  Ein Seed; der Lauf wurde wegen Speichermangels abgebrochen.

* **Widerlegung**: [Riegel und Reflex entfernt](/befunde/riegel-reflex-entfernt.md) - gepaart,
  8 Seeds x 50: an 196/400, aus 196/400, Intervall [-7, +7]. Die Riegel-Messung vom 25.08.
  ("nicht abschalten") gilt fuer den heutigen Zustand nicht mehr. Riegel und Reflex sind im
  Netzbetrieb aus (`ACT23_REGELN_NETZ`, Vorgabe 0).

* **Umstellung auf tatsächliche ACT23-Bewegungen festgelegt**: [Datenvertrag](/messungen/act23-bewegungsdaten.md).
  Sechs gemessene Servos inkl. Greifer, reversibler Positionsport v2; native Übergänge mit
  tatsächlichem Horizont (Bewegungszyklus 4 ms), unveränderte Kamera. Seeds 431/443 nach Läufen
  getrennt. Keine Extrapolation des alten S1-Forecasts und noch kein neuer Fit.

* **Native ACT23-Arbeitsposen geprüft**: [Befund](/befunde/act23-arbeitsposen-kamera.md).
  Unveränderte Roboterkamera 240×240, vier eingefrorene FSM-Episoden: 16/16 platzierte
  Objektvorkommen sichtbar, mindestens eine Klaue 238/238 Ansichten, beide 207/238. Alle
  Arbeitsstellungen außerhalb S1-Box; 24 zudem außerhalb Positionsport-v1-Intervall.
  Eigene Zustandskopie und Lernparameter unverändert. Nächste Datengrundlage aus ACT23-Bewegungen,
  explizit erweiterter Positionsvertrag; keine Kameraverschiebung und kein neues Training.

* **ACT23-Arbeitsposenprüfung festgelegt**: [Vertrag](/messungen/act23-arbeitsposen-kamera.md).
  Nutzer bindet Kamerablick an die reale Hardware. Unverändertes overview 240×240 und native
  ACT23-Slots/FSM-Bewegungen, vier eingefrorene Episoden auf eigener Zustandskopie; kein Training.

* **B1-Schlussfolgerung korrigiert**: [Abdeckung](/befunde/s1-koerpermodell-abdeckung.md).
  Nutzer verweist auf den erprobten ACT23-Arbeitsraum. Gleiche Simulatorklasse/Kamera,
  aber B1 zog unabhängige Gelenkstellungen aus der S1-Box statt ACT23-Arbeitsposen.
  Daher zuerst repräsentative Arbeitsposen bei bestehender Kamera prüfen; keine belegte
  Notwendigkeit einer zusätzlichen Körperkamera. Messwerte bleiben gültig für B1.

## 2026-10-03

* **Anlage**: [Die Schliess-Entscheidung offline](/befunde/schliessen-offline.md) - Schritt 3,
  Pruefstand: die Riegel-Lesart "schliesst zu hoch" ist ein Zaehlartefakt; echt sind ein 4-mm-Band
  und ein im Zustand unsichtbarer Stillstand. Neue Schalter `ACT16_IMIT_AUSGEFUEHRT`,
  `ACT23_IMIT_UMETIKETT`, Zaehler `frueh zu`.

* **Anlage**: [Der privilegierte Rueckfall rettet nichts](/befunde/rueckfall-privileg-gemessen.md) -
  Schritt 2: Rueckfall sichtbar gemacht und gemessen (1/400 Namensbetrieb, 2/200 Eigenschaften,
  1 Lieferung gerettet). Zweiter Kanal (Wiederfinden in der Episode) gefunden und geschlossen.
  `ACT23_RUECKFALL=aufgeben` ist Vorgabe.

* **Anlage**: [Groesse sehen statt wissen - A/B](/befunde/groesse-sehen-ab.md) - 8 Seeds x 50,
  gepaart: Privileg 52,2 %, Schaetzung 53,8 %, Seeds 3:3:2. `ACT23_GROESSE_SEHEN` ist Vorgabe,
  act23 sammelt beim Start selbst, wenn der Schaetzer leer ist.

* **B1-Abdeckung geprüft**: [Befund](/befunde/s1-koerpermodell-abdeckung.md).
  224/224 RGB-/Encoder-Replays exakt; in 145 Posen liegen beide Klauen außerhalb der Kamera,
  beide sichtbar nur 20/224. 36/64 Testposen außerhalb der Trainingshülle, aber selbst innerhalb
  Fehlerfaktor 1,12482 gegen Mittelbild. Kein Nachtraining. Erst Körperblick/Erhebung korrigieren,
  dann neuer B2-Vertrag mit frischen Testposen; bloße Auflösungserhöhung behebt den Blickfehler nicht.

* **B1-Abdeckungsaudit festgelegt**: [Vorgehen](/messungen/s1-koerpermodell-abdeckung.md).
  Vorhandene 224 Posen ohne Fit: nächste Gelenknachbarn und konvexe Hülle, danach RGB-identischer
  Replay mit ausschließlich evaluativer Geometriesegmentierung und Kameraprojektion.

* **B1 ausgeführt, Vorhersagetor verfehlt**: [Befund](/befunde/s1-visuelles-koerpermodell.md).
  Erster lernender Positions-Latent-Verbraucher, 160 Trainings-/64 neue Testposen: Bild-MSE
  Faktor 1,28015 gegen Mittelbild; variable Pixel 1,28056, vertauschte Kontrolle 0,37562.
  Erhebung, Gradienten und Checkpoint-Replay bestehen. Nächstes Thema: sichtbare Abdeckung
  und Generalisierung auditieren; keine Nachoptimierung auf diesem Test und keine ACT23-Integration.

* **Visuellen Körpermodell-Verbraucher festgelegt**: [B1-Vertrag](/messungen/s1-visuelles-koerpermodell.md).
  Direkter Positions-Latent → Kameraansicht, getrennte Posen und vertauschte Bildzuordnung als
  Kontrolle. Kein als bestanden angenommener Greifer-Landmark, keine Handpositionsetiketten.

* **Unabhängiger S1-Test bestanden, Latent-Port gebaut**: [Befund](/befunde/s1-unabhaengige-rollouts.md).
  2.400 neue Testübergänge Seeds 211/307 ohne Nachtraining: Faktor 0,09224 gegen Persistenz,
  je 5/5 Gelenke besser. [Portvertrag](/mechanismen/servo-latent-port.md) erhält gemessene
  Position reversibel und getrennt von Übergangs-Latent/Forecast für das künftige Körpermodell.

* **Unabhängiger S1-Test festgelegt**: [Vertrag](/messungen/s1-unabhaengige-rollouts.md).
  Seeds 211/307, je 20x60 neue Testübergänge, kein Nachtraining. Nutzerwunsch als
  Latent-Port-Vertrag aufgenommen: gemessene Position getrennt vom aktionsbedingten Latent erhalten.

* **S1-Online-Kopftraining abgeschlossen**: [Befund](/befunde/s1-online-kopf.md).
  Lokale komplexe Updates aus zufälliger Initialisierung erreichen 1,20244e-5 rad²,
  Faktor 0,0874 gegen Persistenz, 5/5 Gelenke besser. Batch bleibt genauer; nächstes Tor
  ist ein neuer unabhängiger Rolloutsatz bei eingefrorenem Modell, kein weiteres Diagnosesplit-Tuning.

* **S1-Online-Kopftraining festgelegt**: [Vertrag](/messungen/s1-online-kopf.md).
  Zwölf Epochen lokaler komplexer Updates aus zufälliger Kopfinitialisierung; gleicher
  eingefrorener Kontextencoder, kein Batch-Warmstart und keine Parametersuche.

* **S1-Vorhersagesignal erschlossen**: [Lernziel-Audit](/befunde/s1-lernziel-audit.md).
  Konvergiertes generatives Training bleibt bei Faktor 4,36 gegen Persistenz; bedingter
  Batch-Kopf auf identischer kontextinferierter Repräsentation erreicht 9,49e-8 rad² (5/5 besser).
  Zielvergiftung/Replay bestehen; Nullprior entfernen ergibt perfekte Rekonstruktion ohne
  Lernen. Nächster Schritt: gleiche bedingte Merkmale mit lokaler Online-Lernregel.

* **S1-Lernzielvergleich festgelegt**: [Vertrag](/messungen/s1-lernziel-audit.md).
  Konvergiertes Training gegen analytische lineare Referenzen, mit/ohne Nullprior;
  bedingte Köpfe und direkter linearer Vergleich trennen verbleibende Hypothesen.

* **S1 mit korrekter Energie-Inferenz abgeschlossen**: [Befund](/befunde/s1-energie-inferenz.md).
  128 Schritte im Test zu kurz; lange Inferenz und unabhängiger reduzierter Solver stimmen
  auf 2,01e-8 rad überein. MSE 0,000599 gegen 0,000138 Persistenz, 2/5 Gelenke besser.
  Tor verfehlt, Trainingskonvergenz bleibt Vorbehalt; kein Gesamturteil gegen PC-CVNN.

* **Isolierte Energie-Inferenz gebaut und validiert**: [Vertrag](/messungen/s1-energie-inferenz.md).
  18 unabhängige Gradientenkontrollen, analytische Inferenz und Lebenszyklus bestehen.
  S1-Rezept vor dem Lauf festgelegt; Claudes Normalisierungsfund 59c85c4 berücksichtigt.

## 2026-10-02

* **Anlage**: [Konstante Spalte sprengt die Policy](/befunde/konstante-spalte-sprengt-policy.md) -
  im A/B "Groesse sehen" gefunden: im Training konstante Policy-Spalten (obj_h, Greifhoehe) werden
  mit 1e6 verstaerkt. Schutz gebaut und offline belegt; das laufende A/B war ungueltig (zudem
  wegen Speichermangel gestoppt).

* **Ergaenzung**: [Laufzeitregeln](/mechanismen/laufzeit-regeln.md) - Bestandsaufnahme am Code:
  was seit 25.08. gefallen ist (Oberkante beim Stapeln), was weiter laeuft (Riegel, Reflex & Co.),
  dass `obj_h` beim GREIFEN noch aus MuJoCo kommt, und die gemessenen Negative fuer den Riegel-Ersatz.

* **Anlage**: [Nur ein Marker - A/B](/befunde/ein-marker-ab.md) - gepaart, 8 Seeds x 50, Seed als
  Einheit vorab festgelegt: vier sichtbar 58,2 %, einer 55,8 %, Seeds 5:3, p = 0,73. Kein Effekt.

* **PC-Engine mathematisch geprüft**: [Audit](/befunde/pc-engine-mathematik-audit.md)
  findet drei Abweichungen vom Energiegradientenvertrag; zwölf Zustandskontrollen scheitern,
  unabhängige Referenzen bestehen. Exakter Gegenfall erhöht Energie 0,50 → 0,61.
  Ein-Eingang-W-Lernen, temporaler Gradient und acht Vektorregressionen bestehen.
  Engine unverändert; Reparaturfolge E0–E4 vor erneutem S1-Urteil dokumentiert.

* **S1-Ursachenurteil korrigiert**: [Gegenprüfung](/befunde/s1-vorwaertsmodell-gegenpruefung.md)
  reproduziert den alten Fehler, findet aber fehlendes commit_step im Test und eine fehlende
  Konjugation im linearen Fehlergradienten. Kein Nachweis einer brauchbaren Motorik; zuerst
  isolierte Engine-Validierung, bevor ein neuer Architekturvergleich sinnvoll ist.

## 2026-10-01

* **Widerlegung**: [Platte ausblenden - A/B](/befunde/platte-ausblenden-ab.md) - vorab
  festgelegte Replikation auf 6 neuen Seeds kehrt die erste Lesart um (mit Platte 55,7 gegen
  49,3 %); ueber alle 9 Seeds 54,9 gegen 52,9 %, p = 0,41, Seeds 5:3. Kein Effekt. Neue Falle in
  der [Messvorschrift](/messungen/act23-headless-ab.md): Episoden-McNemar ueberschaetzt, weil
  der Agent im Lauf weiterlernt.

* **Anlage**: [Platte ausblenden - A/B](/befunde/platte-ausblenden-ab.md) - gepaartes act23-A/B,
  Marker-Ablage, 3 x 50 Episoden je Arm: ohne Platte 60,0 %, mit 53,3 %, McNemar 20:10, p = 0,099.
  Neuer Schalter `ACT23_SOCKEL_AUS` (1 ausgeblendet, 2 dazu gleiche Zielverteilung) und
  Aufgaben-Abdruck fuer Paarungen ueber Arme mit verschiedenen Stuetzen.

* **Ergaenzung**: [Steuer-GUI](/mechanismen/gui-bedienung.md) - Platte (Stapelauflage) in der GUI
  ein-/ausblendbar, versetzbar (wuerfeln, Mittelklick) und umfaerbbar; "Objekte neu" respektiert
  die Wahl. Nur noch die aktive Magenta-Zielscheibe sichtbar (`ACT23_EIN_MARKER`, Vorgabe 1).
  Wirkung auf Quoten nicht gemessen.

## 2026-09-30

* **Ergaenzung**: [Steuer-GUI](/mechanismen/gui-bedienung.md) - Bezugskoerper waehlbar
  (Klappliste), Klick ins Kamerabild (links Objekt, rechts Ziel/Punkt), lesbare Klapplisten.

* **Neu**: [Steuer-GUI](/mechanismen/gui-bedienung.md) - Umbau nach Nutzerbeobachtungen im
  GUI-Lauf: farbneutrale Wuerfelnamen, aktuelle Farbe in Log und GUI, drei Gruppen mit
  Klapplisten, Aufgabenzeile, Relation fest waehlbar.

* **Ergaenzung**: [Farb-Mischung](/befunde/farb-mischung.md) - Nutzerbeobachtung im GUI-Lauf
  ("Gruenes Wuerfel" ohne gruenen Wuerfel): kein Auswahlfehler, die festen Knopf-Namen tragen
  Farbwoerter, waehrend FARB_MISCHUNG die Farben je Szene permutiert.

* **Ergaenzung**: [Ablage beim echten Oeffnen](/befunde/ablage-beim-oeffnen.md) - Farbtoleranz
  0,08: 70 statt 49 Blicke gesehen (4 falsch), nachgefuehrt 25 statt 18, geliefert 59 gegen 59
  (p = 1,00), gegen Kontrolle 59 gegen 56 (p = 0,65). Hinschau-Linie ausgeschoepft.

## 2026-09-29

* **Ergaenzung**: [Ablage beim echten Oeffnen](/befunde/ablage-beim-oeffnen.md) - Diagnose der
  Blick-Blindheit (35 Faelle): 16 verdeckt, 10 knapp ueber der Farbtoleranz, 9 Mischfleck.

* **Nachtrag**: [Ablage beim echten Oeffnen](/befunde/ablage-beim-oeffnen.md) - Referenzfarbe aus der
  Hand endgueltig: geliefert 59 gegen 56 (Kontrolle) / 57 (hinschauen) / 45 (Tisch-Farbe, p = 0,016),
  0 falsche Objekte, 103 Blicke "nicht gesehen". Diagnoselauf zur Blindheit gestartet.

* **Ergaenzung (vorlaeufig)**: [Ablage beim echten Oeffnen](/befunde/ablage-beim-oeffnen.md) -
  Referenzfarbe aus der Hand (`ACT23_OBJ_EIG=2`): Farbe in der Hand = Tischfarbe (Vermutung widerlegt),
  Blick bleibt meist blind; ~100 Paare: 52 gegen 47 (Kontrolle) / 49 (hinschauen), nicht signifikant.
  Diagnosezeile fuer die Blindheit eingebaut.

* **Ergaenzung**: [Ablage beim echten Oeffnen](/befunde/ablage-beim-oeffnen.md) - absetzen + ueber
  die Farbe suchen: geliefert 45 gegen 56 (Kontrolle) / 57 (hinschauen), p = 0,05/0,04, nicht
  Bonferroni-signifikant. Der Farbfilter findet das gehaltene Objekt kaum (18 statt 51 Sichtungen),
  trifft aber, wenn er findet (2 statt 14 Fehlgriffe). Schalter aus.

* **Ergaenzung**: [Ablage beim echten Oeffnen](/befunde/ablage-beim-oeffnen.md) - vor dem Oeffnen
  hinschauen und nachfuehren (`ACT16_PRUEF_TOL`, zeichengleich): zum wahren Ziel 22 -> 17 mm,
  geliefert 56 gegen 57 von 120 (p = 1,00). Die Fehlablagen: verdeckt, Bezugskoerper statt Objekt
  gesehen, nach dem Anheben aus der Luft gefallen.

## 2026-09-28

* **Neu**: [Ablage beim echten Oeffnen](/befunde/ablage-beim-oeffnen.md) - Nutzerauftrag "mittig
  greifen": Schnappschuss im echten Moment des Oeffnens. Griff bei Erfolg und Misserfolg gleich mittig
  (3 mm); Fehlablagen verrutschen danach seitlich in der Klaue (15 mm beim Oeffnen). Hand genau.

* **Berichtigung**: [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md),
  [Ablage-Schwelle](/befunde/ablage-schwelle-im-teacher.md) - der Ablage-Schnappschuss liegt bei
  14 mm Objekthoehe, nicht beim Oeffnen; mit SENK_NAH ist die Hand dann noch 28 mm unterwegs. Werte
  "beim Loslassen"/"Drift" der heutigen Reihen betroffen, Endlagen und Lieferungen nicht. Diagnose
  zur Klaue: Griff stabil (6 mm Wanderung), Objekt 12 mm vor dem Reichpunkt, quer 0.

* **Ergaenzung**: [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md) -
  Blick-Lernen Seed 9812 nachgetragen: Vorhersage besser, Endlage 17 -> 20 mm. Beide Seeds: geliefert
  126 gegen 125 von 300 (p = 1,00). Ehrliches Negativ, Schalter bleibt aus.

* **Ergaenzung**: [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md) -
  `ACT23_BLICK_LERNEN` (b92c299): Blickkorrektur aus eigenem Kamera-Etikett gelernt. Etikett 1-3 mm
  genau, Endlage 17 -> 17 mm, geliefert 68 gegen 69 von 150 (Seed 9811; 9812 ausstehend).

* **Ergaenzung**: [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md) -
  `ACT16_LUFT_H` (in der Luft korrigieren, zeichengleich geprueft): Objekt wandert seit dem Blick
  nur 3 mm (Schleif-Vermutung widerlegt), zum wahren Ziel 17 -> 15 mm, geliefert 49 gegen 51
  (p = 0,85). Fehlerbudget: Blick ~8 mm, Hand-Toleranz 8 mm, Wandern 3 mm.

* **Widerlegt**: [Ablage-Schwelle im Teacher](/befunde/ablage-schwelle-im-teacher.md) - die
  "Abwuerfe aus der Hoehe" waren ein Zeitgrenzen-Artefakt der 8-mm-Schwelle (FSM erreicht sie beim
  Tragen nie, 17-29 von 60 Ep). Neuer Schalter `ACT16_SENK_NAH` (11c651a, zeichengleich geprueft).
  A/B: Hand auf 8 mm am Ziel, Objekt trotzdem 21-22 mm daneben entlang der Klaue; geliefert 53
  gegen 47 von 120 (p = 0,24). Die Ursache ist der Sitz des Objekts in der Hand.

* **Ergaenzung**: [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md) -
  Objektblick mit SENK_NAH wiederholt: loest bei 57 von 79 Ablagen aus, wo gesehen 21 -> 15 mm zum
  wahren Ziel; geliefert 56 gegen 49 (18 | 11, p = 0,27). Schalter bleiben aus.

## 2026-09-27

* **Ergaenzung**: [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md) - das
  Objekt in der Hand ansehen (9159ab2): aus Traghoehe 8/17 verdeckt und 7-30 mm daneben, aus der
  Tiefe 8/8 gesehen und ~5 mm daneben. A/B 120 Paare: wo gesehen, 18 -> 12 mm zum wahren Ziel;
  greift bei 26 von 80 Ablagen, Lieferungen 51 gegen 51. Vorgaben 0.

* **Ergaenzung**: [Ablage-Schwelle im Teacher](/befunde/ablage-schwelle-im-teacher.md) - `ACT23_RELABEL`
  (cb714c4): 455 von 24000 Zeilen neu beschriftet; der Ablagefehler faellt ueber 150 Ep stetig
  23 -> 16 mm (ohne Neu-Etikett schwankend 17-25), Lieferungen 87 gegen 86. Die Selbst-Imitation
  traegt noch die alte Schwelle.

* **Ergaenzung**: [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md) - Nutzerschritt 2:
  `ACT23_ZIEL_NACHSEHEN` (980d305) gemessen, 120 Paare: geliefert 52 gegen 52, zum wahren Ziel 20
  gegen 21 mm. Das Ziel wird schon beim ersten Blick auf 1-2 mm gesehen; der Fehler steckt beim
  Objekt in der Hand (16 mm) und in der Drift nach dem Loslassen. Vorgabe 0.

* **Ergaenzung**: [Ablage-Schwelle im Teacher](/befunde/ablage-schwelle-im-teacher.md) - Netz-Betrieb,
  150 Ep gepaart: die Policy folgt der 8-mm-Schwelle nur zoegerlich (Loslassen 25 -> ~21 mm, ihre
  Abweichung vom Teacher steigt). Ursache am Code: 24000 alte Etiketten, 8000 davon geschuetzt.
  Vorschlag: den ganzen Puffer mit dem neuen Teacher neu etikettieren.

* **Entscheidung + Ergaenzung**: [Die Direkt-Adresse verkuerzt die Aneignung](/befunde/direkt-adresse-verkuerzt-aneignung.md) -
  `ACT23_EIG_DAUERHAFT` ist Vorgabe 1 (Nutzerauftrag, 82b9aa5). `ACT23_EIG_NACHFUEHREN` gebaut und
  gemessen: 7 Nachfuehrungen in 400 Ep, alle 0,15-0,62 Toleranzen von der alten Adresse; Lieferungen
  gleich (21 gegen 19), Fehlaufloesungen > 40 mm 16/67 gegen 9/56, mehrdeutig 51 gegen 26. Bleibt
  Vorgabe 0. Folgerung: Gegenbeispiele statt mehr Beispiele.

* **S1-PC-Vorwärtsmodell verworfen**: [Vorwärtsmodell](/befunde/s1-pc-vorwaertsmodell.md) -
  der 24er komplexe Ein-Latent-Experte erreicht 0,021131 statt 0,000138 rad² Persistenz-MSE
  und ist auf 0/5 Gelenken besser. Keine Parameter- oder Architektursuche unter diesem Vertrag.

* **S1-PC-Vorwärtsvertrag**: [Vorwärtsmodell](/messungen/s1-pc-vorwaertsmodell.md) - der
  isolierte 24-dimensionale komplexe PC-Experte erhält nur Encoderzustand und direkte
  Stellwerte. Zwölf Epochen und die Tore gegen Persistenz sind vor dem Lauf festgelegt.

## 2026-09-26

* **Ergaenzung**: [Ablage-Schwelle im Teacher](/befunde/ablage-schwelle-im-teacher.md) - A/B unter FSM,
  117 Paare: `ACT16_NEAR_ABLAGE` 8 statt 20 mm -> Abstand beim Loslassen 22 -> 10 mm, entlang der
  Klaue 20 -> 6, geliefert 46 -> 54 (McNemar 6:14, p = 0,12). Mechanismus belegt, Quote nicht.

* **Ergaenzung**: [Die Direkt-Adresse verkuerzt die Aneignung](/befunde/direkt-adresse-verkuerzt-aneignung.md) -
  `ACT23_EIG_GEGEN` (91f9fa3): Gegenbeispiele aus derselben Sichtung. Mehrdeutig 26/56 -> 7/51,
  > 40 mm 9 -> 6, geliefert 19 -> 21. Die Reste sind eindeutige Fehltreffer (V/11), gegen die keine
  Quelle hilft. Vorgabe 0.

* **Anlage**: [Aufmerksamkeit fuer Objekt und Ziel](/fragen/aufmerksamkeit-objekt-ziel.md) - Nutzerfrage,
  am Code: Objekt laufend beobachtet, Ziel einmal je Episode, Ablage gegenueber dem Ziel offen.

* **Anlage**: [Ablage-Schwelle im Teacher](/befunde/ablage-schwelle-im-teacher.md) - 224 Ablagen
  zerlegt: 25-31 mm beim Loslassen kommen aus NEAR = 20 mm im Teacher (loslassen nach Hoehe, nicht
  nach seitlicher Ankunft). Schalter `ACT16_NEAR_ABLAGE` gebaut, Vorgabe zeichengleich.

* **Ergaenzung**: [Die Direkt-Adresse verkuerzt die Aneignung](/befunde/direkt-adresse-verkuerzt-aneignung.md) -
  Nutzerauftrag, die cube-Luecke geschlossen: `ACT23_EIG_DAUERHAFT` (b94bb66). Ursache zweiteilig
  (kuerzeste in DIESER Szene eindeutige Adresse; bei Mehrdeutigkeit der flaechengroesste Treffer),
  nicht der Klassenname. V/11 0/15 -> 5/16, Klaue am Koerper 2/15 -> 13/16; Rest unveraendert. Offen:
  9 von 56 Aufloesungen noch > 40 mm daneben.

* **Anlage**: [Die Direkt-Adresse verkuerzt die Aneignung](/befunde/direkt-adresse-verkuerzt-aneignung.md) -
  Nutzerauftrag, die offene Frage der Zeitverkuerzung. Vier Paare Kette gegen Direkt: erstes
  Kommando Ep 8/22/8/20 statt nie/43/80/76, 4 von 4 Paaren (p = 0,125). Lieferquote auf dem neuen
  Koerper gleich. Eine Adresse `'cube'` trifft den neuen Koerper nicht (V/11: 0 von 15).

* **S1-Übergangssatz gültig**: [Propriozeptionsübergänge](/befunde/s1-proprio-uebergaenge.md) -
  3.000 druckfreie, freie Servoübergänge bestehen nach dem neuen inneren Stellbereich die
  harte Encoderschranke. Der erste Satz mit Randüberschwinger bleibt vom Training ausgeschlossen.

* **S1-Übergangssammler gebaut**: [Propriozeptionsübergänge](/messungen/s1-proprio-uebergaenge.md) -
  50 ganze freie Rollouts erfassen nur direkte Stellwerte und Encoderfolgen. Der Testsplit ist
  trajektoriengetrennt; Druck, Kontakt, Kamera, Objekt, IK und Teacher sind ausgeschlossen.

* **S0-Aktuatorvertrag bestanden**: [Servogrundaudit](/befunde/s0-servo-grundaudit.md) - fünf
  begrenzte direkte Gelenkimpulse folgen innerhalb maximal 0,19°; Greifer, Drucksensor,
  IK und Teacher sind ausgeschlossen. Lernaufgabe und Kontrollvergleich bleiben als S0 offen.

* **S0 gestartet**: [Servogrundaudit](/messungen/s0-servo-grundaudit.md) - der direkte
  Motorzweig beginnt mit einem begrenzten, druckfreien Gelenkimpuls. Kein IK, Teacher,
  Objekt-, Kontakt- oder Drucksignal ist zulässig; erst der bestandene Aktuatorvertrag öffnet
  selbst gesammelte Propriozeptionsübergänge.

## 2026-09-25

* **Anlage**: [Lerngeschwindigkeit mit neuem Koerper](/befunde/lerngeschwindigkeit-neuer-koerper.md) -
  Vorlauf mit obj_Y ergab nichts: die T-Klasse beansprucht es heute in 14 von 16 Lagen. Drei neue
  Koerper (act14, nur bei Bedarf im Modell, 706c7f8), Sonde: Zylinder = Wuerfel, Stern und V
  teilweise neu. Vier Laeufe: Knopf nach 41/68/75 Ep, einmal nie; Geburt->Knopf 30-56 Ep.

* **Anlage**: [Lernkurven in der Rueckschau](/befunde/lernkurven-rueckschau.md) - Nutzerauftrag
  "aus der Lerngeschwindigkeit lernen". Prequentiell ueber die beiden Langlaeufe des Live-Zustands:
  alle Lerner flach; Weltmodell AUC 0,60 im Lauf (0,76 nach eigener Angabe), ueberzuversichtlich.

* **Anlage**: [Ruecksetz-Versuch](/befunde/ruecksetz-versuch.md) - je ein Lerner frisch gegen die
  Kontrolle, 100 Ep. Policy: 60 -> 0 %, Erholung auf 25-30 %, stockt bei 21 mm vom Teacher.
  Weltmodell leer: 26 gegen 26 in den ersten 50 Ep. Fovea: sichtbare Online-Lernkurve, ohne
  Quotenwirkung. Spaete Rueckgaenge bei Weltmodell/Fovea unter Bonferroni. Deutung: satt am Teacher.

* **Ergaenzung**: [Struktur-Experte](/fragen/struktur-experte.md) - Lerngeschwindigkeit nur auf
  NEUEM eine sinnvolle Fitness.

* **D0b-Hubantwort, feste Rohregel verworfen**: [Hubantwort](/befunde/d0b-hubantwort.md) -
  Seed 103 erfüllt die technische Abdeckung mit 17 Trajektorien, verfehlt aber mit 11 TP,
  3 FP, 1 FN und 0 TN die fixierte Precision 0,80 (erreicht 0,786). Kein Schwellen-Tuning,
  keine zweite Rettungsfamilie und keine Integration als Greifzustand.

* **D0b-Hubantwort, Replikationsvertrag v1**: [Messvorschrift](/messungen/d0b-hubantwort.md) -
  zwei neue 20-Episoden-Familien (Seeds 103/107) prüfen ausschließlich die nun fixierte
  Schwerpunktantwort: getragen ab 1,50, nicht getragen bis 0,75 Zellen, sonst Enthaltung.
  Der neue Auswerter prüft ID-Gleichheit und liest die getrennte Wahrheit erst nach dem Label.

* **D0b-Hubantwort, Beobachtbarkeit belegt**: [Hubantwort](/befunde/d0b-hubantwort.md) -
  zwölf eingefrorene Episoden liefern 389/389 Liftframes mit festem Blick und vollständigem
  Fovea-Schwerpunkt. Bei sechs getragenen gegen vier nicht getragenen Trajektorien beträgt die
  Schwerpunktänderung Median 3,89 gegen 0,60 Zellen (explorativ einseitig p=0,057). Das ist
  eine Einzelmessung und noch kein Klassifikator; eine vorab festgelegte Replikation folgt.

## 2026-09-24

* **Anlage**: [Generalisierung Relation x Zielart](/befunde/generalisierung-relation-zielart.md) -
  `ACT23_ZIEL_ZELLEN` (5ec268b). Diagonale auf:balken / links:wuerfel im Training ausgelassen,
  zwei Ketten je 100 Ep, Test gepaart gegen untrainiert. Die vorher festgehaltene Erwartung ist
  eingetreten: **das Training verbessert nichts nachweisbar** (geuebt 34 -> 41/44 %, p = 0,73/0,55),
  also ist die Generalisierung nicht streng pruefbar. Die ausgelassenen Zellen ziehen in beiden
  Ketten mit, auf:balken am staerksten (23 -> 54/62 %, p = 0,22/0,06).

* **Anlage**: [Auf beliebige Koerper](/befunde/auf-beliebige-koerper.md) - `ACT23_AUF_ALLE`,
  `ACT23_AUF_LOSLASSEN` und `ACT23_ZIEL_RELATION=alle` gebaut (Nutzerwuensche). Zwei Seeds, 80 Ep:
  getragene Koerper landen auf Platte 10/14, Wuerfel 9/16, Balken 10/18 auf dem Ziel, liegen bleiben
  10/4/3. Meine Vorhersage war fuer die Ablage falsch. Wertungsfehler behoben: stabil auf der Platte
  liegende Koerper, 25-26 mm neben der Mitte losgelassen, galten als nicht abgelegt.

* **Ergaenzung**: [Die Auflagenhoehe ertasten](/mechanismen/hoehe-ertasten.md) - Nutzervorgabe
  Kamera statt Tasten; das Tasten wird nicht weiter ausgebaut.

* **Ergaenzung**: [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md) - Nutzerwunsch, auf
  BELIEBIGE Koerper zu stapeln. Einschaetzung: Wuerfel tragen bis ~12 mm Versatz, Balkenformen bis
  ~7 mm, die gemessene Ablagegenauigkeit liegt bei 19-25 mm - der Engpass ist die Ablage. Chance:
  die Tragfaehigkeit als selbst gelernte Eigenschaft.

* **Ergaenzung**: [Richtungs-Relationen](/fragen/richtungs-relationen.md) - Klarstellung des
  Nutzers: die Relationen waren nur als ZIELPUNKT der Ablage gemeint (gebaut und gemessen), nicht
  als Relation in der Adresse. Der Punkt "Relation in der Adresse" ist damit kein offener Faden.
  "Herunter" war laut Nutzer ein Versehen - die Idee ist mit den vier Richtungswoertern erledigt.

* **Anlage**: [Richtungswoerter selbst gelernt](/befunde/richtungswoerter-selbst-gelernt.md) -
  `ACT23_ZIEL_RELATION=richtung` (b8a0f00), Bezugssystem Kamerabild nach Nutzerentscheidung.
  Spielphase 40 Ep "an": 27 Etiketten im Nachhinein, danach 3 von 4 Woertern innerhalb 1,5 Grad
  der Kamera-Achse ("links" 18 Grad bei n = 5). Gepaart, 75 Episoden: gelernte Bedeutung gegen
  Kamera-Geruest Worttreffer 51 gegen 47 (p = 0,42), geliefert 35 gegen 35, kein Rueckfall.
  Neben dem Bezug trifft das Wort in 92-94 %, die Fehltreffer sind Ablagen 100 mm und mehr weg.
  Selbsturteil = Welt in 123 von 124.

* **Anlage**: [Richtungs-Relationen](/fragen/richtungs-relationen.md) und
  [Struktur-Experte](/fragen/struktur-experte.md) - zwei Nutzerideen, am Code und an den gepaarten
  Messungen analysiert. Relationen: im Ablageziel zuerst, weil nur dort die Aufgabe sie erzwingt;
  Wortbedeutung aus eigener Ablage etikettieren. Experte: das Urteil ist der Engpass, nicht das
  Vorschlagen; zuerst ein Experimentverwalter mit dreistufigem Urteil.

* **Anlage**: [Der Stapel neben der Mitte](/befunde/stufe4-stapel-neben-der-mitte.md) - die drei
  gepaarten Arme noch einmal, der Koerper 16 mm neben der Plattenmitte
  (`ACT23_ABSTAPELN_VERSATZ`, Code 7b2405e; K2 mit `ACT23_ADR_REL_ANTEIL=1.0`, weil eine
  Vorpruefung zeigte, dass 0,5 schon fuer zentrierte Stapel grenzwertig ist). 88 von 90 Episoden
  szenengleich. **K0 30 %, K1 41 %, K2 42 %, nichts unter Bonferroni** (K0-K1 16 zu 6, p = 0,053).
  Das sah zuerst wie die Bestaetigung der Mitten-Vermutung aus. **Der direkte Test widerlegt das:**
  die Szenen beider Reihen sind bis auf die Koerperlage gleich (90/90 gleiches Kommando und Ziel),
  jeder Arm laesst sich also mit sich selbst paaren - K0 zentriert gegen versetzt 12 zu 9, p = 0,66.
  **Der Versatz schadet dem blinden Arm nicht; die Vermutung aus der Drei-Arme-Seite ist dort als
  nicht gestuetzt markiert.** Die Relation traegt auch hier nichts (11 zu 10) und loest neben der
  Mitte seltener auf (47 statt 63 Episoden).

* **D0b-F1b, zeitlicher Expertenpfad verworfen**: [F1b-Vertrag](/messungen/d0b-fovea-zeitbindung.md) -
  die echte Bildfolge vor/nach eigenem Fingerimpuls erreicht in drei Seeds Median 42,4 px und
  2/29, 5/29 bzw. 4/29 Klauen innerhalb 24 px. Zeitinformation allein löst die Bindung nicht.

* **D0b-F1a, Architektur-Experte verworfen**: [F1a-Vertrag](/messungen/d0b-fovea-selbstbewegung.md) -
  der neue räumliche Fovea-Crop-MLP verfehlt auf demselben 64/32-Positionssplit in allen drei
  Initialisierungen beide Tore (Median 42,4/42,4/46,3 px; jeweils 5/29 innerhalb 24 px). Keine
  Nachoptimierung; nächste Hypothese braucht zeitliche Selbstbewegungsbindung.

* **Architektur als Forschungsvariable**: [Architektur-Expertenpfad](/entscheidungen/architektur-evolution-expertenpfad.md) -
  PC-CVNN und gewachsene Module sind veränderbar. Neue Experten bauen isolierte Varianten,
  prüfen sie gegen vorab gesetzte Tore und integrieren nur reproduzierbare Gewinne.

* **D0b-Fovea-Raumbindung negativ**: [Selbstbewegung](/befunde/d0b-hand-selbstbewegung.md) -
  auf 64/32 ganzen Trainings-/Testpositionen verbessert der eingefrorene komplexe Fovea-Topzustand
  die Sakkadenwahl gegenüber der Bildmitte (Median 53,5 statt 80,5 px), erreicht aber nur 4/29
  sichtbare Klauen innerhalb 24 px. Kein Kopf; ein neuer Selbstbewegungs-Fovea-Zweig braucht
  einen getrennten Lernvertrag.

* **D0b-Handmaske, lokaler Ausleser negativ**: [Selbstbewegung](/befunde/d0b-hand-selbstbewegung.md) -
  auf 64/32 ganzen Trainings-/Testpositionen senkt der ausschließlich visuell trainierte
  Patch-Ausleser die Masken-MSE um 10,1 %, verfehlt aber den Landmark-Ort (Median 57,8 px,
  5/29 innerhalb 20 px). Keine Epochen-/Schwellensuche; Fovea-Raumbindung ist das nächste Tor.

* **D0b-Handlandmark, erster Audit**: [Selbstbewegung](/befunde/d0b-hand-selbstbewegung.md) -
  36 ausgeführte Öffnen/Schließen-Impulse erzeugen 36 sichtbare Kameradifferenzen. Deren fester
  Schwerpunkt erreicht aber nur 12/31 sichtbare Klauen innerhalb 20 px (Median 24,2 px).
  Selbstbewegung bleibt als Trainingsziel offen; fester Punktdetektor und Greifzustandskopf nicht.

## 2026-09-23

* **D0b-Selbstetikett angehalten**: [Portaudit](/befunde/d0b-fovea-portaudit.md) - die neue
  12-Episoden-Serie ordnet 3.329 Fovea-Frames und getrennte Evaluationszeilen exakt zu; 2.809
  enthalten eine echte Fovea-Auswahl. Ein Fehlgriff hat dennoch 125/125 sichtbare Carry-Frames.
  Ohne Bildraumreferenz der eigenen Hand ist Mitbewegung nicht berechenbar; kein Lernkopf und
  zuerst Audit eines Hand-Landmarks oder einer 3D-Kameraprojektion.

* **D0b-Portaudit**: [eingefrorene Fovea-Frames](/befunde/d0b-fovea-portaudit.md) - 200 vollständige,
  rein agentensichtbare Bildraum-/Topzustands-/Hand-Frames, keine Lernmutation. Die Wegwerfepisode
  hatte keinen Hub; damit ist nur die Sonde, nicht ein Greifzustandssignal belegt.

* **D0b-Hubabdeckung**: [Portaudit](/befunde/d0b-fovea-portaudit.md) - zwölf eingefrorene Episoden
  liefern 3.329 vollständige Frames, darunter 358 Hub- und 338 Trageframes bei 95,4 % sichtbaren
  Beobachtungen. Der Trace erhält eine äußere Episoden-ID für gruppierte Auswertung.

* **Neue D0-Entscheidung**: [D0b: visueller Greifzustand](/entscheidungen/d0b-visueller-greifzustand.md) -
  nach dem negativen Wrist-Pilot folgt kein Tuning, sondern die Vorprüfung eines selbstbeobachteten
  Objekt-im-Greifer-Signals aus Fovea-Bildfolge und eigener Hubbewegung. Servopfad und höhere
  Auflösung bleiben getrennte, nachgelagerte Entscheidungen.

## 2026-09-22

* **D0 negativ geschlossen**: [D0 Seed 29: Wrist-Evaluation](/befunde/dream-rsi-d0-seed29-wrist-evaluation.md) -
  auch der zweite unabhängige Trainingsseed besteht den Wrist-Pilotvertrag nicht. Seed 101
  verliert Lieferung und Selbsturteil, Seed 103 gewinnt Lieferung, aber nur +7,5 statt +20
  Punkte Ausrichtung; gepoolt betragen beide primären Gewinne +3,75 Punkte. Kein Nachtraining.

* **Seed-29-Basis Seed 103 bestätigt**: [D0 Seed 29: Wrist-Evaluation](/befunde/dream-rsi-d0-seed29-wrist-evaluation.md) -
  die zweite gefrorene Basisfamilie ist vollständig und integer (40/40 Episoden, keine
  Lernmutation, Basis-SHA unverändert) und liefert 26/40 Welt-Lieferungen, 3/40 ausgerichtete
  Wrist-Wahlen sowie 9/40 Enthaltungen. Der Checkpointvergleich folgt.

* **Seed-29-Zwischenbefund negativ**: [D0 Seed 29: Wrist-Evaluation](/befunde/dream-rsi-d0-seed29-wrist-evaluation.md) -
  der eingefrorene Checkpointvergleich auf Seed 101 ist integer, verändert aber die ausgerichtete
  Wahl nicht (6/40 -> 6/40), senkt Lieferung (21/40 -> 19/40) und Selbsturteil (23/40 -> 20/40).
  Die vorab festgelegte Familie Seed 103 bleibt offen.

## 2026-09-20

* **Anlage**: [Drei Arme je Episode gepaart](/befunde/stufe4-drei-arme-gepaart.md) - nach dem
  Speicherabbruch mit hoechstens zwei Prozessen neu gefahren. **Die Paarung haelt: 89 von 90
  Episoden in allen drei Armen szenengleich**, auch zwischen K0 und K1, die verschieden
  wahrnehmen. **Ergebnis: K0 (ohne Chroma-Schnitt) 34 %, K1 (Schnitt) 37 %, K2 (Schnitt +
  relationale Adresse) 43 % -- kein paarweiser Unterschied signifikant** (McNemar 0,65 / 0,38 /
  0,20, Bonferroni 0,0167). **Meine vorher aufgeschriebene Erwartung war falsch:** der Sprung liegt
  NICHT bei der Sichtbarkeit (3 Punkte). Der Trichter zeigt warum: **auch K0 greift den
  gestapelten Koerper in 51 von 90 Episoden**, obwohl er fuer diesen Arm keine eigene Detektion hat.
  **Vermutung, nicht gemessen:** der Abstapel-Aufbau stellt den Koerper genau in die Plattenmitte,
  der Schwerpunkt des verschmolzenen Flecks liegt also auf ihm -- der Test macht die Relation
  ueberfluessig. Pruefbar mit einem Stapel ausserhalb der Mitte (bei 20 mm Versatz zielte K0 etwa
  16 mm daneben). Nebenbei: auf identischer Szene kippt eine Wahrnehmungsaenderung den Ausgang in
  rund einem Fuenftel der Episoden, in beide Richtungen fast gleich oft -- die 10 von 10 gleichen
  Paare der ersten Pruefung waren Zufall.

* **Abbruch**: die Drei-Arme-Reihe (K0 ohne Chroma-Schnitt | K1 mit | K2 mit + relationale
  Adresse) wurde vom System **wegen kritischen Speichers gestoppt** -- drei parallele act23-Prozesse
  drueckten den Rechner auf 2,9 von 11,8 GB frei. **Ergebnis: keine einzige Episode**, die Arme
  steckten noch im Start. Erhalten ist der Warmlauf (23 Tastwerte, verpflanzter Schaetzer), ein
  Neustart ueberspringt ihn. Beim Aufraeumen liefen die Python-Kinder verwaist weiter, und die noch
  lebende Schleife startete nach dem Beenden der Kinder sofort den naechsten Seed; erst das Beenden
  ihrer Wurzel hat es gestoppt. **In die [Messvorschrift](/messungen/act23-headless-ab.md): hoechstens
  zwei Prozesse gleichzeitig, und beim Aufraeumen zuerst die Wurzel.**

* **Bau + Messvorschrift**: [Gepaart je Episode](/messungen/act23-headless-ab.md) -
  `ACT23_SZENE_JE_EPISODE` (Vorgabe 0, `322972b`). Im Stufe-4-Sweep sahen zwei Arme mit demselben
  Seed nur 88 von 200 Episoden in derselben Szene. **Drei Divergenzquellen**, zwei davon behebt der
  Schalter, weil sie zur Szene gehoeren: (1) `crng` lief ueber alle Episoden durch -> wird je
  Episode auf `default_rng([SEED, ep])` zurueckgesetzt, und zwar IM PLATZ, weil Dutzende Closures
  ihn gebunden haben; (2) das kommandierte Objekt blieb liegen, wo der jeweilige Arm es hinlegte
  -> die Szene wird jede Episode neu gebaut. (3) Die NEUGIER waehlt das Objekt nach gelernten
  Werten -- das ist Verhalten des Agenten, bewusst nicht mitgeschaltet, der Start meldet es
  (`ACT23_AUTO_CURIOUS=0` fuer gepaarte Messungen). **Messinstrument:** ein `[Szenen-Abdruck]` je
  Episode, eine Pruefsumme ueber Objektwahl, Ziel, Koerperlagen, Farben und Sockel. **Geprueft
  auf Seed 8103**, im Sweep der am schlechtesten gepaarte (5 von 25): **10 von 10 Abdruecken
  identisch**, bei nachweislich verschieden fahrenden Armen (B loest 7-mal relational auf, A nie).
  **Erste Beobachtung, noch kein Befund:** alle 10 Episodenpaare gingen GLEICH aus -- auf
  identischer Szene hat die Adressart in keiner dieser zehn das Ergebnis geaendert. Auswertung
  kuenftig mit McNemar auf den abweichenden Paaren.

* **Nachtrag**: [Der gepaarte Sweep](/befunde/stufe4-sweep-widerlegt.md) - zwei Befunde aus den
  vorhandenen Protokollen. (1) **Die Arme sind nur je Seed gepaart, nicht je Episode:** nur 88 von
  200 Episodenpaaren sahen dieselbe Szene, meist weichen sie ab Episode 2-3 ab, weil Szenenwahl und
  Entscheidungen aus demselben `crng` ziehen. (2) **Der Vergleichsarm findet den Stapel ebenfalls**
  - A hebt ihn in 99 von 200 Episoden, weil der Chroma-Schnitt in BEIDEN Armen lief. Verglichen
  wurde also nur die Adresse, nicht Stufe 4 als Ganzes. Daraus drei naechste Schritte auf
  [Stapeln als Aufgabe](/fragen/stapeln-als-aufgabe.md): Szenen-Zufall entkoppeln (Episoden-
  Paarung, McNemar), ein Arm ohne Schnitt als echte Kontrolle, dann die Richtungsfrage.

* **Anlage**: [Der gepaarte Sweep widerlegt die Stufe-4-Wirkung](/befunde/stufe4-sweep-widerlegt.md)
  - **meine Wirkungsaussage von heute Mittag faellt.** Gepaarter Sweep ueber acht Seeds (8101-8108),
  je Arm 25 Ep aus demselben Zustand, A und B parallel, ein gemeinsamer Hoehenschaetzer:
  **B gewinnt in 4 Seeds, A in 2, zwei gleich -> Vorzeichentest p = 0,69**; gepoolt 76 von 200
  gegen 66 von 200, also **38 gegen 33 %** bei Fisher p = 0,35. **Der Einzelseed war in BEIDEN
  Armen ein Ausreisser, und zwar in entgegengesetzte Richtungen:** A mit 14 % unter der
  Sweep-Spanne von 20-60 %, B mit 49 % ueber der von 28-44 %. Die 35 Punkte Abstand waren nicht
  der Effekt, sondern die Summe zweier Zufaelle. **Die Streuung zwischen den Seeds ist riesig**
  (Arm A 20 bis 60 %); ueber sie hinweg sind 10 Punkte mit acht Seeds nicht aufzuloesen.
  **Was bleibt:** alle Sprachzahlen (28 von 31 aufgeloest, 6 mm) und der Mechanismus -- die
  Adresse loest auf, der Arm findet den gestapelten Koerper, greift auf der richtigen Hoehe und
  traegt ihn fort. **Was faellt:** "die erste signifikante Wirkung dieser Linie" und "die
  relationale Adresse verdoppelt das Abstapeln". Die Einzelmessungs-Seite ist entsprechend
  eingeschraenkt. Der eingebaute Gegencheck der beiden Urteilszeilen hat in zwei Seeds
  angeschlagen; nachgesehen fehlte dort je einmal die Selbst-Urteil-Zeile ganz (kein Widerspruch
  im Urteil) -- er sollte kuenftig nur vergleichen, wo beide Zeilen existieren.

* **Anlage**: [Stufe 4 belegt](/befunde/stufe4-abstapeln-belegt.md) - der saubere Durchgang,
  nachdem vier Maengel behoben waren. **17 von 35 gegen 5 von 35, also 49 gegen 14 %, Fisher
  p = 0,004 - die erste signifikante Wirkung dieser Linie.** Zur Einordnung: die gewoehnliche
  Transportaufgabe liefert auf demselben Zustand 40-66 %, das Abstapeln liegt damit im Bereich des
  gewoehnlichen Transports. **Die Vorhersage vor dem Lauf ist eingetroffen:** alle Reparaturen
  zielen auf den relationalen Zweig, und der Vergleichsarm bleibt bei GENAU 5 von 35 - sie wirken
  armspezifisch. Ohne sie waren es 32 %. Die Zwischenschritte sagen dasselbe: Adresse 28 von 31
  aufgeloest statt 27 von 38, mehrdeutig 3 statt 6, kein Stapel 0 statt 5, Adressfehler
  unveraendert 6 mm (die Moebel-Schranke verwirft also Falsches, nicht Richtiges), und der Glaube
  liegt mit 19 mm fast wieder im gewoehnlichen Bereich (5-18), nachdem der Tracker seinen Keim
  bekommt. **Belegt ist damit die REKURSION der Sprache** (`ADRESSE := ... | RELATION ADRESSE`):
  der Agent adressiert einen Koerper ueber seine Lage zu einem anderen, findet ihn im eigenen
  Bild, greift auf der richtigen Hoehe und traegt ihn fort - keine dieser Groessen kommt aus dem
  Simulator. **Offen:** ein Seed und ein Lauf je Arm statt eines gepaarten Sweeps; welche der vier
  Reparaturen den Sprung traegt; das belegte Aussehen bleibt mit 1 von 23 Tastwerten duenn.

* **BERICHTIGUNG**: [Stufe 4 gemessen](/befunde/stufe4-abstapeln-gemessen.md) stand auf einem
  **Zaehlfehler von mir**, und die Seite sagte das Gegenteil des Gemessenen. Die Erfolgszeile des
  Laufs heisst `[Auto N] GELIEFERT` in GROSSBUCHSTABEN; mein fallunterscheidendes `grep geliefert`
  traf ausschliesslich das kleingeschriebene `NICHT geliefert` und **zaehlte damit jeden Erfolg als
  Misserfolg**. Weil es jeden Arm gleich traf, sah es nicht nach Fehler aus, sondern nach einem
  durchgaengigen Null -- und ueberlebte so ein ganzes A/B. **Richtig gezaehlt, ueber beide
  unabhaengigen Protokollzeilen, die Episode fuer Episode uebereinstimmen: A (gewoehnliche
  Adresse) 5 von 35 = 14 %, B (relationale Adresse) 11 von 34 = 32 %, Fisher p = 0,093. Die
  relationale Adresse VERDOPPELT das Abstapeln.** Zur Einordnung am selben Tag gemessen: die
  gewoehnliche Transportaufgabe liefert auf demselben Zustand 40 bis 66 % je nach Choreographie.
  **Was faellt:** die Schlussfolgerung "die Aufgabe ist nicht geloest" und die Zuschreibung, der
  Glaubensfehler und der Hoehenschaetzer seien die Ursache eines Totalausfalls -- es gab keinen.
  **Was bleibt:** alle Sprachzahlen (aus anderen Zeilen gezaehlt), die Hoehenschaetzer-Diagnose
  und der Glaubensfehler als Messwert. **Zwei Eintraege in der
  [Messvorschrift](/messungen/act23-headless-ab.md):** die Gross-/Kleinschreibung samt der Regel,
  beide Zeilen zu zaehlen und zu vergleichen -- und **eine Quote von exakt 0 ist ein
  Verdachtsfall, kein Ergebnis**; erst die Grundlinie mit demselben Befehl nachmessen.
  Der Fehler hat mich einen halben Tag Ursachensuche fuer einen Ausfall gekostet, den es nicht gab
  (Glaubensfehler, Chroma-Schnitt, Choreographie, Einsprungpunkt -- alle unschuldig).

* **Anlage**: [Der Schaetzer auf der belegten Auflage](/befunde/schaetzer-auf-der-belegten-auflage.md)
  - die Ursache des Stufe-4-Fehlschlags ist **offline reproduziert, beziffert und behoben**.
  Sonde mit 180 Zeilen (leere gegen belegte Auflage an denselben Stellen und Hoehen):
  **auf leer gelernt und auf belegt geprueft ergibt 34 %, also Grundrate** - genau der Lauf-Fall.
  Auf beidem gelernt: **97 % (leer) und 78 % (belegt)**, und die leere Auflage kostet es nichts
  (96 -> 97 %). Der Versatz ist **264 px** (leer 1424, belegt 1160) bei einem Hoehenhub von nur
  127-145, also rund doppelt so gross wie das Signal - und die Flaeche ist die staerkste Achse
  des Schaetzers. Bemerkenswert die Symmetrie: auch andersherum bricht es zusammen (nur belegt
  gelernt, leer geprueft: 33 %) - es geht nicht um "schwerer", sondern um **dieselbe Verteilung**.
  **Gebaut** (`ACT23_HOEHE_BELEGT`, Vorgabe 0): dieselbe Episode liefert zwei Aussehen mit EINEM
  Etikett, denn die Oberkante aendert sich nicht dadurch, dass etwas darauf steht.
  **Drei Dinge hat erst der Rauchtest erzwungen:** (1) aufgenommen wird beim NAECHSTEN
  Adressieren, nicht am Episodenende - dort verdeckt der Arm die Auflage (1 von 7 erkannt);
  (2) die Adresse trifft bei belegter Auflage oft den KLEINEN Teil (239 px gegen 1236 leer),
  gemeint ist der groessere; (3) ein Pruefstein aus derselben Episode - die belegte Auflage ist
  dieselbe Silhouette plus der Koerper, ihre Flaeche darf also nicht deutlich kleiner sein als die
  leere; er hat prompt ein Beispiel mit 227 gegen 990 px verworfen. **Ehrlich:** die Ausbeute ist
  duenn (1 belegtes Beispiel auf 6 Tastwerte, vier Bedingungen hintereinander), es ist
  `ebene: pruefstand`, und die ZWEITE Ursache des Stufe-4-Fehlschlags - der Arm verliert den
  getragenen Koerper aus dem Glauben - ist damit nicht behoben.

* **Anlage**: [Stufe 4 gemessen](/befunde/stufe4-abstapeln-gemessen.md) - das A/B zur Relation in
  der Adresse, und es ist ein **Negativ mit praeziser Ursache**. **Die Sprache traegt:**
  *"nimm das, was auf Y liegt"* loest in 27 von 38 Versuchen auf (Fehler Median 6 mm, 90 %-Wert
  12 mm), und der Arm hebt den gestapelten Koerper in **23 von 23** Ablagen wirklich herunter
  (15 mm ueber Ruhelage) - im Vergleichsarm ohne Relation 17 Ablagen mit 6-mal "nie getragen".
  **Geliefert wird trotzdem nichts: 0 von 30 und 0 von 24.** Zwei bezifferte Ursachen, **keine
  davon in der Sprache:** (1) der Arm verliert den getragenen Koerper aus dem GLAUBEN (28-45 mm
  daneben statt der sonst 5-18) und legt 29 mm neben dem Ziel ab; (2) der Hoehenschaetzer liest
  die Auflage voellig falsch - wahr 6/10/14 mm, geschaetzt 11,1/6,0/9,2, **die Reihenfolge ist
  zerstoert**, also schlechter als raten. **Die Ursache dafuer habe ich selbst erzeugt:** der
  Schaetzer hat auf Detektionen der LEEREN Auflage gelernt (~1400 px), gefragt wird er nach der
  BELEGTEN - und die zerfaellt durch den Konzentrisch-Schnitt, die Auflage ist dann nur noch der
  groessere Rest (738-1543 px). **Der Schnitt, der Stufe 4 erst moeglich macht, zerstoert die
  Eingabe des Hoehenschaetzers** - zwei Bausteine, jeder fuer sich gemessen gut, die sich
  gegenseitig untergraben. Naechster Schritt: der Schaetzer muss auf dem lernen, was er im
  Einsatz bekommt (das Tasten liefert das Etikett ohnehin an der belegten Auflage).
  **Zwei Programmierfehler haben den Lauf zweimal gekostet**, beide im Messaufbau: eine
  Hilfsfunktion, die ihre Schalter SETZTE statt sie auszugeben (alle Laeufe fuhren mit Vorgaben,
  erkannt nur an "0 Tastwerte"), und ein zweiter `perceive_fn`-Aufruf im Wiederfind-Pfad, dem die
  dritte Rueckgabe die Episode brach.

* **Anlage**: [Der Stapel wird sichtbar](/befunde/stapel-wird-sichtbar.md) - **Stufe 4 begonnen**,
  und ihre Voraussetzung ist geloest. Stufe 4 ist die Relation auch in der ADRESSE
  (`ADRESSE := ... | RELATION ADRESSE`, also *"nimm das, was auf Y liegt"*) - derselbe
  "Typ statt Verb"-Schnitt eine Ebene weiter, womit die Sprache **rekursiv** wird und das
  Umstapeln ohne ein weiteres Verb herausfaellt. Dafuer muss der gestapelte Koerper gefunden
  werden, und das ging bisher nicht (0 von 25). **Die Ursache ist berichtigt:** auf
  [Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md) stand, der
  Chroma-Schnitt sei auf "Deskriptor trifft keine Klasse" verriegelt - diese Sperre sitzt aber am
  EROSIONS-Split. Einzeln nachgerechnet faellt jedes Tor bis auf die **raeumliche Wache**
  (Chroma-Abstand 0,805 gegen Schwelle 0,12, Deckung 1,00, dann Trennung 0,29 gegen 1,0). Sie
  verwirft Teile mit zusammenfallenden Schwerpunkten, weil das Schattierungsschichten EINES
  Koerpers sind - **ein gestapelter Koerper sitzt konzentrisch und sieht fuer sie genauso aus.**
  **Abhilfe ohne neue Zahl:** die Wache wird ausgesetzt, sobald die Farbstreuung des Flecks den
  Einzelobjekt-Massstab ueberschreitet (leer 0,068, belegt 0,329, Massstab 0,120) - derselbe
  gemessene Massstab wie beim Selbstrichter und beim Lerntor, **dritte Verwendung**. Ergebnis:
  **24 von 25 getroffen statt 0 von 25, und 0 von 25 falsche Zerfaelle auf der leeren Platte.**
  Damit ist auch die Verallgemeinerung der alten Seite eingeschraenkt: ein Koerper auf einem
  groesseren ist in der SILHOUETTE unsichtbar, nicht in der Wahrnehmung - die Farbe traegt, was
  die Umrisslinie nicht hergibt, und die alte Seite hatte das selbst gemessen, aber als Anzeige
  statt als Lokalisierung gelesen. `ACT_SHAPE_CHROMA_KONZENTRISCH`, Vorgabe 0.

* **Anlage**: [Weniger Teacher kostet Genauigkeit und der Aufgabe nichts](/befunde/tastetikett-gegen-privileg.md)
  - das A/B zum Nutzerprinzip. Zwei Schaetzer, einer aus ERTASTETEN Etiketten (14 Zeilen), einer
  aus `geom_size` (22 Zeilen); danach wird **nur der Schaetzer** in denselben Basiszustand
  verpflanzt, damit im Test nicht Policy, Puffer und Welt-Modell mitverglichen werden. Getestet
  mit ABGESCHALTETEM Tasten, eine Auflagenform. **Ergebnis: der ertastete Schaetzer ist 3,7-mal
  ungenauer (2,20 gegen 0,60 mm) und stapelt genauso gut - 15/16 gegen 17/19, p = 1,00.** Die
  Fehlschlaege sind in beiden Armen seitlich (Versatz 94 und 156 mm gegen 12 und 23 mm), in P
  haben sie sogar den kleineren Hoehenfehler. **Der Preis des Etiketts ist unabhaengig beziffert:**
  Tastetikett gegen die Wahrheit Median -0,60 mm / Streuung 2,60 mm, und dieses Rauschen kostet
  einen Lerner rund **20 Punkte** (86 -> 69 % richtige Stufe bei 20 Zeilen).
  **Ein Fehler, der fast durchgegangen waere:** die Ablagephase beginnt, sobald die Hand SEITLICH
  am Ziel ist - sie kann dann noch zentimeterweit darueber stehen, und jeder Stillstand auf dem
  Weg nach unten galt als Beruehrung. Einzelne Etiketten lagen **17,9 mm** daneben (Streuung 5,79
  statt 2,60), was die Genauigkeit des Lerners halbierte (52 statt 69 %). Abhilfe: ein Fenster um
  die Schaetzung.
  **Und eine Methode, die ich ab jetzt immer anwende:** die erste Fassung dieses A/B war schon bis
  zu den Warmlaeufen durch; der Vergleich der verpflanzten Schaetzer gegen 270 vorhandene
  Sondenzeilen zeigte alle drei auf der Grundrate - die 105 Minuten Testlauf haetten drei gleich
  unbrauchbare Schaetzer verglichen. **Vor jedem teuren A/B beide Artefakte an einem vorhandenen
  Pruefsatz gegeneinanderhalten; sind sie dort ununterscheidbar, kann es der Lauf auch nicht.**
  Der Check taugt zum AUSSORTIEREN, nicht zum Vorhersagen: im Lauf lagen beide deutlich besser als
  auf dem Pruefsatz (T 2,20 gegen 4,26 mm), weil ein Lauf wenige Stellen mehrfach besucht.

* **Anlage**: [Die Auflagenhoehe ertasten](/mechanismen/hoehe-ertasten.md) - Nutzerprinzip
  **"weniger Teacher ist immer besser"**, umgesetzt fuer die letzte privilegiert gelabelte Groesse.
  **Der Ausgang "Stapel haelt oder nicht" taugt dafuer nachweislich NICHT:** der Hoehenfehler ist
  bei gelungenen und misslungenen Stapeln gleich gross (2,20 gegen 2,30 mm), was kippt, ist der
  seitliche Versatz - darauf zu lernen hiesse, auf Rauschen zu lernen. **Das Ausgangssignal muss
  koerperlich und ABGESTUFT sein**, und das ist die uebertragbare Form des Befundes. Was traegt,
  ist die **Beruehrung**: die Hand senkt das getragene Objekt `TAST_TIEF` unter die Schaetzung und
  haelt an, sobald sie fuehlt, dass es nicht mehr sinkt; die Aufsetzhoehe IST die gesuchte Groesse,
  gemessen an `site_xpos` (Vorwaertskinematik, Propriozeption - kein Simulatorwissen, kein
  Objektmass). Gegen die Wahrheit, die nirgends eingeht: **7 Tastwerte, Median -0,50 mm, |Median|
  1,10 mm** - so genau wie der Schaetzer, den es trainieren soll (0,7-2,2 mm). **Zwei
  Konstruktionsfehler gemessen und behoben:** (1) ohne das UEBERTASTEN waere das Signal einseitig
  (Beruehrung entstuende nur bei zu tiefer Schaetzung) und der Lerner driftete; (2) die
  Aufsetzhoehe ist die beim BEGINN des Stillstands, nicht am Ende - waehrend der
  Bestaetigungsschritte kriecht die Hand weiter und las die Oberkante systematisch zu tief
  (Median -2,65 -> -0,50 mm). **Offen:** ob ein aus Tastwerten gelernter Schaetzer im Lauf so gut
  ankommt wie einer aus dem Privileg - das ist der naechste Lauf. `ACT16_TASTEN` und
  `ACT23_HOEHE_TASTEN`, beide Vorgabe 0.

* **Berichtigung**: in den Quellenzeilen mehrerer Stapel-Befunde stand **"Teacher fahrend" - das
  war falsch.** `ACT23_POLICY=teacher` waehlt nur den GREIFER; wer die Teilziele faehrt,
  entscheidet `ACT23_CHOREO`, und dessen **Vorgabe ist `netz`**. Die Laeufe zu
  [Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md),
  [lokaler Schaetzer](/befunde/lokaler-schaetzer-im-lauf.md),
  [drei Auflagen](/befunde/drei-auflagen-im-lauf.md) und
  [Selbstrichter](/befunde/selbstrichter-stapel.md) hat also die **gelernte Policy** gefahren. Am
  A/B aendert das nichts (beide Arme gleich), an der Lesart schon - und zwar zugunsten der
  Befunde. Aufgefallen ist es erst, als eine neue Zeile im FSM-Zweig in keinem Lauf ansprang.
  Als Invariante abgelegt; drei aeltere Seiten, deren Rezept ich nicht nachweisen kann, tragen
  jetzt einen Vorbehalt statt einer Behauptung.

* **Anlage**: [Drei Auflagenformen im Lauf](/befunde/drei-auflagen-im-lauf.md) - die
  act23-Gegenprobe zur dritten Auflage, auf Wunsch des Nutzers gefahren, nachdem ich sie fuer
  nicht lohnend erklaert hatte. **Meine Begruendung war zu pauschal:** sie galt fuer die
  Stapelquote, nicht fuer den Schaetzfehler (stetig, ~30 Messwerte je Arm). **Die Sonde hatte
  recht: 45 % richtige Stufe gegen die vorhergesagten 48 %**, Schaetzfehler von 0,8 auf 2,2 mm.
  **Und es ist folgenlos: 17 von 20 gestapelt gegen 15 von 17 mit dem Privileg** (85 gegen 88 %,
  p = 1,00), die neue 60-mm-Platte sogar **7 von 7** - ausgerechnet die, fuer die 48 %
  vorhergesagt waren. **Der Grund ist gemessen:** die Fehlschlaege sind SEITLICH, nicht senkrecht
  (Versatz 65 gegen 15 mm), und der Hoehenfehler ist bei gelungenen und misslungenen Stapeln
  gleich gross (2,20 gegen 2,30 mm; in Arm A haben die Fehlschlaege sogar den kleineren).
  **Neue Spielart der [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md), als vierter Fall
  dort eingetragen:** der Pruefstand war nicht falsch, seine Messgroesse loest nur **feiner auf
  als die Aufgabe**. "Richtige Stufe von dreien" verlangt den Fehler unter 2 mm; ob ein Wuerfel
  liegen bleibt, entscheidet der seitliche Versatz. **Rueckwirkend fuer die ganze Stufe-3-Linie:**
  der Ertrag ist das gefallene Privileg, nicht die Genauigkeit - zwischen 0,8 und 2,2 mm liegt
  fuer die Aufgabe nichts.

* **Anlage**: [Die dritte Auflage bricht die Nachbarschaft](/befunde/dritte-auflage-bricht-die-nachbarschaft.md)
  - die offene Frage des Vortags, beantwortet und **negativ**. Dritte Platte 60 x 60 mm, bewusst
  ZWISCHEN den bekannten 50 und 70 (der schwere Fall: die Nachbarschaft enthaelt dann beide).
  **Ihr eigenes Signal ist perfekt** (allein trainiert 100 %, 0,41 mm - leichter als die anderen
  beiden). **Im Topf mit allen dreien faellt alles:** 62 % gesamt statt 92 % bei zweien, die neue
  Platte 48 %, und die alten verlieren mit. **Eigene Zeilen helfen NICHT** (0/3/6/12/24/45 Zeilen
  -> 33-42 %) und verschlechtern die alten (90 -> 77 %). **Ursache beziffert:** der naechste eigene
  Nachbar liegt bei 0,11-0,16, der naechste fremde bei 0,80-0,92 - fuenf- bis achtmal weiter -,
  und trotzdem sind 12 % der zehn Nachbarn fremd (bei zwei Platten waren es 0 %). **Ein einziger
  ferner Punkt unter zehn genuegt**, weil eine Ausgleichsrechnung mit fuenf Parametern gegen
  Hebelwirkung keinen Schutz hat. Orakel mit grundrissreinen Nachbarn: **86/98/98 %** - die
  Information ist vollstaendig da, es fehlt die AUSWAHL. **Vier Abhilfen gemessen, keine
  uebernommen:** "Aussehen zuerst" (55 %) und robustes Nachfitten (56 %) sind schlechter als der
  Ist-Zustand, kleinere Nachbarschaft und tricube-Gewichtung (69 %) helfen nur im schwersten Fall
  und verschlechtern die einfacheren - das zu nehmen hiesse, an 270 Sondenzeilen anzupassen und
  die act23-Messung des Vortags zu entwerten. **Der Code bleibt.** Und: meine Verallgemeinerung
  vom Vortag ("wird von selbst zu einem Modell je Grundriss") gilt nur bei weit auseinander
  liegenden Formen; sie ist auf der [Zwei-Grundriss-Seite](/befunde/zweiter-grundriss-bricht-die-hoehe.md)
  entsprechend eingeschraenkt. `ACT23_SOCKEL_N=3` stellt alle drei im Wechsel auf (Vorgabe 1);
  die ADRESSIERUNG der dritten Platte ist kein Problem (Rauchtest 4-6 mm), nur ihre Hoehe.

* **Anlage**: [Der lokale Hoehenschaetzer haelt im Lauf](/befunde/lokaler-schaetzer-im-lauf.md)
  - die act23-Bestaetigung zum lokalen Umbau, in einer Welt mit ZWEI Auflagenformen im Wechsel
  (`ACT23_SOCKEL2=1`). Warm 60 Episoden (51 Adressen, 9 verworfen -> 42 Zeilen), dann A und B je 40
  aus demselben Zustand. **Die Schaetzung traegt: 0,60 mm auf der 50er und 1,10 mm auf der 70er
  Platte** - dort, wo der globale Schaetzer auf der Grundrate gelegen haette (Pruefstand 3,38 mm).
  Das war die Frage des Laufs, und sie ist mit Ja beantwortet. **Nebenbefund:** er ist im Lauf
  BESSER als die Duennbesetzungs-Leiter der Sonde erwarten liess (42 Zeilen -> laut Sonde 50-60 %),
  weil ein Lauf wenige Stellen MEHRFACH besucht statt ein Raster gleichmaessig auszuduennen - fuer
  einen lokalen Schaetzer ist ein Lauf die guenstigere Welt. **Die Quote bleibt unentschieden:**
  A 16/17 = 94 % gegen B 14/18 = 78 %, p = 0,338, und signifikant waere erst B <= 11/18 = 61 %.
  16 Punkte nominell, zu gross um zu beruhigen und zu klein um sie zu zeigen. Die Luecke sitzt auf
  der KLEINEN Platte (7/7 gegen 6/9), wo die Schaetzung mit 0,60 gegen 0,60 mm gleich gut ist -
  die drei Fehlschlaege haben also keinen Hoehenfehler hinter sich; die kleine Platte ist
  mechanisch die schwerere (Toleranz 13 statt 23 mm). Das bleibt Erklaerung, nicht Messung.
  **Nicht vergleichbar mit den 85 % des ersten Stufe-3-A/B:** die XML hat einen Koerper mehr.

* **Umbau**: der `HoehenSchaetzer` rechnet **lokal statt global linear** (`76a0121`), und die Welt
  hat einen zweiten Grundriss (`ACT23_SOCKEL2`). Beim Bauen zeigte sich, dass der auf der Seite
  vorgeschlagene Weg - ein Schaetzer je adressierter Auflage - **gar nicht noetig und ohnehin
  versperrt** war: **die Groessenachse des Agenten saettigt bei Moebeln** (`GROESSEN_BAENDER`
  endet bei 6,5 px, die Platten lesen 13,0 und 10,0 - beide heissen "dick"; die mm-Achse saettigt
  genauso). Der tatsaechliche Ausweg braucht keine Identitaet: die Grundrisse liegen im
  Merkmalsraum weit auseinander, und ein Modell, das seine Ebene nur aus der **Nachbarschaft**
  legt, wird von selbst zu einem Modell je Grundriss. Stellenweise gehalten: **eine Auflage
  1,31 mm/77 % -> 0,45 mm/100 %, zwei Auflagen 3,38 mm/33 % -> 0,73 mm/92 %** - lokal ist auf
  beiden Welten besser, und besser als getrennte Schaetzer (68/77 %). `k = 10` ist nicht
  eingestellt, sondern doppelt so viele Nachbarn wie Parameter. **Gemessene Kehrseite:** der
  lokale braucht Zeilen (24 -> 36 %, 60 -> 74 %, 174 -> 93 %), waehrend der globale von Daten NIE
  besser wird; deshalb liegt der Schaetzer im Zustand und sammelt ueber Laeufe. **Alles davon ist
  `ebene: pruefstand`** - die act23-Bestaetigung steht aus, und `ACT23_HOEHE_SEHEN` bleibt auf 0.

* **Anlage**: [Die zweite Auflage bricht den Hoehenschaetzer](/befunde/zweiter-grundriss-bricht-die-hoehe.md)
  - die am Vortag angekuendigte Bewaehrungsprobe, **und sie faellt durch.** Zweite Platte in der
  Welt (`sockel2`, 50 x 50 gegen 70 x 70, gleiche Farbe und Bauart, einziger Unterschied der
  Grundriss), 180 Sondenzeilen. **(a)** Ein Schaetzer, der nur 70er kennt, liest eine 50er um
  **-6,00 mm** zu niedrig und faellt auf die Grundrate (33 %); auf 70ern bleibt er bei 81 %.
  **(b) Und beide zu sehen hilft NICHT** - 33 %, also ebenfalls Grundrate: in einem Topf sind
  Grundriss und Hoehe in der Flaeche ununterscheidbar vermengt. **(c)** Keine aufgezeichnete
  Bildgroesse trennt sie; der beste Kandidat `Flaeche/Dicke^2` (vergroesserungsfrei) reagiert auf
  Hoehe und Grundriss **gleich stark** (-0,24 gegen +0,26). Der Befund in zwei Zahlen: **der
  Grundriss hebt die Flaeche um 685, die Hoehe um 91.** ABER je Grundriss einzeln ist alles beim
  Alten (68 und 77 %), und die Reihe 33 -> 49 (Grundriss als Eingabe) -> 59 (Flaeche/Grundriss^2)
  -> 68/77 (je Auflage ein Schaetzer) zeigt den Ausweg: **die Hoehe ist keine Funktion des Bildes,
  sondern des Bildes GEGEBEN die Identitaet der Auflage.** Die hat der Agent, weil er sie in
  derselben Episode adressiert hat - und der befuerchtete Zirkelschluss ist gemessen keiner:
  dasselbe Verhaeltnis 685 zu 91, das die Hoehe unlesbar macht, macht die Identitaet sicher.
  [Die Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md) ist damit nicht widerlegt,
  sondern auf eine Welt mit EINER Auflagenform eingegrenzt - eine Grenze, die sie selbst benannt hatte.

* **Anlage**: [Die Oberkante ohne Privileg](/befunde/oberkante-ohne-privileg.md) - **Stufe 3 ist
  durch: das letzte Privileg auf dem Stapelpfad ist gefallen.** Drei Laeufe: warm 60 Episoden (der
  Schaetzer sammelt 32 Zeilen aus 46 Gelegenheiten, 14 verworfen), dann A und B je 40 aus DEMSELBEN
  warmen Zustand, Unterschied allein `ACT23_HOEHE_SEHEN`. **A (Oberkante aus `geom_size`) 17 von
  20, B (aus der eigenen Sicht) 15 von 18 - 85 gegen 83 %, p = 1,00.** Der Schalter hat wirklich
  gewirkt: in B 31 von 31 Episoden mit Schaetzung, **0 Rueckfaelle**, und die Klaue faehrt
  abgestufte Hoehen von 18 bis 29 mm an, keine Konstante. Der **Schaetzfehler im Lauf ist mit
  0,7 mm kleiner als die 1,31 mm der Sonde** - kein Widerspruch, sondern ein anderer Zuschnitt
  (die Sonde hielt jede Stelle heraus, hier sind fruehere Episoden derselben Stelle im Fit; die
  uebertragbare Zahl ist die der Sonde). Der alte blinde Fleck auf der flachen Auflage ist keiner:
  6 mm 5 von 7, 10 mm 5 von 6, 14 mm 4 von 4. **Was das wert ist:** nach [Ziel](/ziel.md) nicht
  die Quote, sondern dass eine Groesse, die der Agent gesagt bekam, jetzt aus seinem eigenen Bild
  kommt - ohne dass die Aufgabe leidet. **Was es nicht ist:** ein Leistungsfortschritt, und
  `p = 1,00` heisst nicht "gleich" - erst ein Einbruch auf 9 von 18 (50 %) waere bei dieser
  Fallzahl signifikant geworden. Das Geruest hat den Schaetzer trainiert (gelabelt mit dem
  Privileg); die Hoehe aus dem AUSGANG zu lernen ist die naechste, haertere Stufe. Und der
  Grundriss ist fest - eine zweite Auflage anderen Grundrisses ist die Bewaehrungsprobe.

* **Bau**: der `HoehenSchaetzer` (`ACT23_HOEHE_SEHEN`, Vorgabe 0, main `d6599aa`) - die Oberkante
  der Auflage aus Groessen DERSELBEN Detektion, die die Zieladresse ohnehin aufloest (scheinbare
  Flaeche, Materialdicke, wahrgenommener Ort), gelabelt mit dem Privileg als Geruest. An den
  Sondendaten reproduziert er die Sonde zifferngenau (1,31 mm, 77 %, stellenweise gehalten). **Drei
  Dinge beim Bauen gefunden, alle in die Mechanismus-Seiten geschrieben:**
  (1) **[Invariante](/mechanismen/invarianten.md): ein Lerner im Zustand gehoert in ein MODUL.**
  `pc_act23.py` laeuft als `__main__`, eine dort definierte Klasse wird als `__main__.<Name>`
  gepickelt, ist aus jedem anderen Skript unladbar - und der Startcode schiebt bei einem
  Ladefehler die GANZE Zustandsdatei nach `.bak`.
  (2) **[`ACT23_EIG_DIREKT` ist der FUENFTE Pflichtschalter fuer `auf`](/mechanismen/relation-auf-gebaut.md)**
  und stand nicht in der Liste. Eine STUETZE steht nicht in `state.OBJECTS`, kann deshalb **per
  Bauart nie eine gebundene Klasse bekommen**, und ohne Klasse hat ihre Adresse keine verfolgbare
  Achse: gemessen **0 von 4 Adressen ohne den Schalter, 4 von 4 mit ihm**. Der Startcheck meldet
  ihn jetzt mit. Erster Fall, in dem die klassenlose Adresse nicht Abkuerzung, sondern einziger Weg ist.
  (3) **Das Lerntor ist die Einzelfleck-Skala** (Median + 95er-Median der eigenen Bezugswerte,
  0,120), nicht `_merge_th` (0,339) - eine Auflage MIT Wuerfel liest im Median 0,20 und kaeme
  durch das grobe Tor. Direkte Folge der [Selbstrichter-Messung](/befunde/selbstrichter-stapel.md).

* **Anlage**: [Die Hoehe steckt in der Wahrnehmung](/befunde/hoehe-steckt-in-der-wahrnehmung.md)
  - Vorfrage vor dem Abbau des **letzten Privilegs auf dem Stapelpfad**: `_ziel_aufloesen` liest die
  Oberkante aus `sim.m.geom_size`. Sonde mit dem Sockel allein auf dem Tisch, 30 Rasterstellen x
  Hoehen 6/10/14 mm, je eine Detektion aus `perceive_all`. **Die scheinbare Flaeche steigt an 30
  von 30 Stellen streng monoton mit der Hoehe** (+102 px^2 von 6 auf 14 mm) - kein Rauschen, reine
  Perspektive. Allein taugt sie nichts, weil der Ort 2,7-mal so stark streut wie der Hoehenhub
  (33 % = Grundrate). Mit dem wahrgenommenen **Ort** und der Materialdicke dazu: **1,31 mm Fehler
  und 77 % richtige Stufe gegen 4,00 mm und 33 % Grundrate**, stellenweise gehalten, mit einem
  linearen Modell. Alle vier Groessen stehen in derselben Detektion, die die Zieladresse ohnehin
  aufloest - **das Privileg kann fallen.** Nebenbefund GEGEN meine Erwartung: der Ortsfehler
  SINKT mit der Hoehe (0 von 30 positiv), weil die Homographie auf die Hoehe der Kalibrierkoerper
  (~12 mm) geeicht ist und nicht auf den Tisch; dieselbe Physik wie in
  [16 mm daneben](/befunde/stapeln-bricht-die-tischebene.md), nur mit verschobenem Nullpunkt. Er
  ist als Kanal unbrauchbar - ihn zu messen setzt den wahren Ort voraus. `ebene: pruefstand`, sagt
  also ueber act23 nichts vorher; und die Flaeche traegt die Hoehe nur, solange alle Auflagen
  denselben Grundriss haben.

* **Ergaenzung**: [Der Stapel-Selbstrichter](/befunde/selbstrichter-stapel.md) - zweiter Anlauf
  mit der **eigenen leeren Auflage** als Bezug statt des globalen Massstabs, und der Massstab fuer
  "deutlich veraendert" aus denselben Bezugswerten gemessen, aus denen `_merge_th()` sein Quantil
  zieht: 400 Werte, Median 0,085, 95er 0,120, 0,995er 0,339 - **die uebliche Schwankung eines
  Einzelflecks ist 0,035**, und das erklaert zugleich, warum der alte Massstab viermal zu hoch war
  (sein Quantil sitzt im langen Auslaeufer). Beide Kriterien laufen in DERSELBEN Episode mit, das
  alte als "global waere" danebengeschrieben - so vergleicht ein Lauf beide.
  **Ergebnis: 17 von 25 erkannt statt 7 von 25, bei null Fehlalarmen in beiden Faellen**
  (Uebereinstimmung 74 statt 42 %). **Die verbleibenden Fehlanzeigen sind kein Schwellenproblem:**
  dort steigt die Farbstreuung um +0,003 statt +0,134 - das Objekt haengt ueber den Rand und ist
  gar nicht im Blob der Auflage (Versatz 23 gegen 10 mm). Der Flaechentest verwirft weiterhin
  keinen einzigen echten Stapel, und die vermeintliche Blindheit auf dem flachen Sockel kehrt sich
  um (14 mm 10 von 10, 6 mm 4 von 6) - die Hoehe war nie die Ursache. Vorgabe bleibt 0: als Tor
  fuer die Selbst-Imitation brauchbar, als Erfolgsmass nicht.

* **Anlage**: [Der Stapel-Selbstrichter](/befunde/selbstrichter-stapel.md) - gebaut und gemessen,
  `ACT23_SELBST_STAPEL` (Vorgabe 0). Der Agent beurteilt seinen eigenen Stapel ueber die
  **Farbstreuung** des Auflagen-Blobs gegen seinen EIGENEN Verschmelzungs-Massstab, und trennt
  "drauf" von "daneben verschmolzen" ueber die Flaeche: zwei nebeneinander liegende Koerper haben
  die SUMME der Flaechen, ein Stapel die der Auflage allein - beide Bezugswerte kennt der Agent
  (leere Auflage aus der Adressaufloesung, eigene Objektflaeche aus der Startdetektion), also ohne
  erfundene Schwelle. **Ergebnis: treffsicher, aber fast blind** - 7 von 7 Positivurteilen richtig,
  aber nur 7 von 25 Stapeln erkannt (Uebereinstimmung 13/31 = 42 %). **Alle 14 Fehlanzeigen
  scheitern an derselben Stelle:** Sockel mit Wuerfel liest 0,20, der eigene Massstab liegt bei
  0,34; der Flaechentest hat keinen einzigen echten Stapel verworfen. Nach Auflagenhoehe 0/6 (6 mm),
  2/3 (10 mm), 3/10 (14 mm). Die saubere Trennung der Offline-Sonde (kein Ueberlapp) kommt in
  echten Szenen nicht wieder. Der Massstab ist richtig geeicht, aber fuer eine andere Frage - er
  beantwortet "was ueberschreitet ein EINZELNES Objekt nie", und ein Blob mit 19 % zweiter Farbe
  ueberschreitet das nicht.

* **Widerlegung**: [Der Arm stapelt](/befunde/stapeln-gemessen.md), Abschnitt zum Selbstrichter -
  **entwertet**. Die Aufraeumschleife setzt das kommandierte Objekt nach der Episode auf seine
  Ruhehoehe vom Anfang zurueck (um gekippte L/U aufzustellen) und **baut damit den Stapel ab, bevor
  irgendein Selbsturteil die Szene sieht**. Die dortige Beobachtung ("sagt bei 40 von 45 Stapeln
  geliefert, aber auch bei 6 von 9 Fehlablagen") hat eine aufgeraeumte Welt gemessen. Sichtbar wurde
  es daran, dass die Welt in ALLEN 15 Urteilszeilen "nicht drauf" meldete, waehrend im selben Lauf
  10 Stapel gelangen. Korrektur: liegt das Objekt hoeher als seine eigene Ruhehoehe, steht es auf
  etwas - dann bleibt die Hoehe; ein gekipptes Objekt liegt tiefer, der Aufstell-Fall bleibt
  unberuehrt. **Die Stapelraten sind nicht betroffen**, sie werden vor dem Aufraeumen gefaellt.

* **Anlage**: [Die Policy stapelt selbst](/befunde/netz-stapelt-selbst.md) - der erste Stapellauf,
  in dem die GELERNTE Choreographie faehrt. Zwei Arme je 50 Episoden aus DERSELBEN Kopie eines
  200-Episoden-Trainingsstands, Unterschied allein `ACT23_CHOREO` netz gegen fsm.
  **16 von 19 beurteilten Ablagen liegen auf dem Sockel, gegen 18 von 20 beim Teacher**
  (p = 0,66; je Episode 16/50 gegen 18/50, p = 0,83). Objektmitte in BEIDEN Armen +11 mm ueber der
  Auflage (Soll +12), Lieferquote 46 gegen 44 %. **Beide Arme loesen die Zieladresse in 100 % der
  Stapelauftraege auf** (0 Rueckfaelle, gegen 86/100 im Lauf davor) - der Sockel ist dem Agenten
  vertraut geworden. Die Policy laesst hoeher los (23 gegen 15 mm) und legt etwas weiter aus der
  Mitte ab (16 gegen 12 mm), beides ohne Folge. **Damit ist die AUSFUEHRUNG des Teachers
  entbehrlich** - aber ausdruecklich nicht das Privileg: die Auflagenhoehe steht weiter im Zustand
  und stammt aus dem Simulator. Gezeigt ist, dass die Policy auf die Hoehe HANDELN kann, nicht dass
  sie sie SEHEN kann; das ist Stufe 3 (Farbstreuung). Eigener Fehler im Ablauf: den trainierten
  Stand hatte ich beim Aufraeumen geloescht und musste ihn neu erzeugen - deterministisch
  reproduziert, aber nicht bitweise gegen den dokumentierten geprueft.

* **Anlage**: [Die Policy legt auf jeder Sockelhoehe richtig ab](/befunde/gemischt-lernen-zweiter-lauf.md) -
  zweiter gemischter Lauf, 200 Episoden, Szenenwechsel alle zwei Episoden und damit **100
  Kombinationen aus Sockelort und -hoehe** statt 10. **Die Verwechslung mit dem Zielort ist
  gebrochen:** Korrelation der Hoehenspalte mit dem Ort +0,00 / -0,06 (vorher -0,54 / +0,65),
  Ortsstreuung +-47 / +-25 mm. **In ihrer eigenen Verteilung trifft die Policy alle drei
  Sockelhoehen**, und der Fehler faellt stetig: +5/+6/+9 mm nach 50 Episoden, **+0/+4/+2 mm nach
  200** - so genau wie ihre Tischablage (+5,4 mm). 65 Stapel gelungen, 10 daneben. **Aber es ist
  keine uebertragbare Funktion:** die kontrafaktische Probe zeigt weiter Steigung ~2 statt 1 bei
  R2 < 0,32 - an Orten, an denen nie ein Sockel stand, ueberschiesst sie. Ungeprueft, aber
  naheliegend: die Hoehenspalte ist nicht der einzige Hinweis, die gemessene Objekthoehe traegt
  dieselbe Information, und die Probe aendert nur eine von beiden. **Die Tischablage haelt** auf
  aktuellen Zeilen (4,7 -> 9,7 -> 6,7 -> 9,2 -> 6,2 mm); auf dem alten festen Probenset (Szenen mit
  vier Objekten, die es hier nicht mehr gibt) faellt sie auf 21-31 mm - beide Zahlen stimmen, der
  Unterschied ist die Aussage. Naechster Schritt: ein `ACT23_CHOREO=netz`-Lauf, also ob die Policy
  selbst fahrend stapelt.

* **Anlage**: [Gemischt lernen, erster Lauf](/befunde/gemischt-lernen-erster-lauf.md) - nach
  Nutzervorgabe "auf jeden Fall gemischt": drei neue Schalter (`ACT23_ZIEL_MISCH`,
  `ACT23_SOCKEL_WANDERT`, `ACT23_SOCKEL_HOEHEN`), 100 Episoden halb Stapeln halb Tisch, Sockel
  wandernd mit 6/10/14 mm, `SCENE_N=3`. **Die Mischung haelt die alte Aufgabe im Puffer** (16000
  statt 8095 Tischzeilen). **Die Hoehe wird abgestuft genutzt** (Zielhoehe steigt in jedem Stand
  monoton mit h), **aber nicht als Funktion**: Steigung 2,2-2,3, dann 1,0 mit +13 mm Versatz,
  R2 < 0,3. **Die Tischablage schwankt** auf den aktuellen Tischzeilen 14,6 -> 3,0 -> 9,7 mm - kein
  stetiges Verlernen, sondern ein unruhiger Refit; die "12-15 mm zu hoch" des ersten Laufs sind
  deshalb auf der alten Seite als nicht sicher belegt nachgetragen. **Der messbare Grund:** nur 10
  Sockel-Szenen in 100 Episoden (`SCENE_EVERY=10`), die Spalte korreliert noch mit dem Zielort
  (r = -0,54 / +0,65). Unterwegs zwei weitere Wege dicht gemacht, auf denen Moebel zum Objekt
  wurde: die namenlose Uebung (im Rauchtest griff der Arm nach dem Sockel, weil die Formerkennung
  ihm eine junge Klasse gab) und `_try_bind` mit `FREIE_VERGABE`.

* **Anlage**: [Die Policy lernt die Ablagehoehe - als Ort](/befunde/policy-lernt-hoehe-als-ort.md) -
  Frage 2, gemessen. Ein Lauf, 20 + 30 + 50 Episoden, Teacher fahrend mit korrigiertem Etikett,
  offline am Netz geprobt ueber vier Zwischenstaende. **Die Policy reagiert auf die 14. Spalte schon
  nach 20 Episoden** (vorher exakt 0 - Bauart: konstante Spalte, Gradient 0, Gewichte null) und
  trifft die Stapelhoehe **in ihrer eigenen Verteilung** auf 4,6 mm (Netz 28,3 gegen Etikett
  25,6 mm). **Aber die Spalte allein verschiebt die Zielhoehe um +25 statt +8 mm**, das Dreifache.
  Ursache: der Sockel steht immer an derselben Stelle, Stapelzeilen haben Zielort
  (-19,8 +- 6,5 | 151,9 +- 8,7) mm - **Spalte und Ort sind vollstaendig verwechselt**, die Policy hat
  "dort hoeher ablegen" gelernt, nicht "Ablagehoehe = Auflagenhoehe". **Und es kostet die alte
  Aufgabe:** 100 Stapel-Episoden haben alle Tischzeilen ausser dem geschuetzten Kern aus dem Puffer
  verdraengt (24000 -> 8095), und die Tisch-Absenkung liegt bei ck020/ck050 **12-15 mm zu hoch**
  (|Fehler| 4,7 -> 16,8 -> 19,7 -> 7,9 mm). Zwei Abhilfen folgen direkt: **der Sockel muss wandern**
  (erst dann traegt die Spalte die Hoehe allein) und **Aufgaben mischen statt ersetzen**. Nebenbei
  geprueft und verworfen: meine Sorge, eine konstante Spalte explodiere nach der Normierung (isd
  1e-6, Faktor 8000) - sie haelt nicht, weil 8000 mal ein Gewicht von exakt null null ist. Nicht
  gemessen: das Verhalten, also ob die Policy selbst fahrend stapelt.

* **Anlage**: [Der Teacher widersprach dem Stapel](/befunde/teacher-widerspricht-dem-stapel.md) -
  **vor** dem Lernlauf fuer Frage 2 geprueft, ob die Policy die Ablagehoehe ueberhaupt lernen KANN.
  Sie konnte es nicht. `choreo_log` etikettiert jeden besuchten Zustand mit `reactive_subgoal`,
  **auch in FSM-Laeufen** und ausdruecklich unter Verzicht auf die Aktion der FSM; diese Funktion las
  aber nur `state[:11]` - die Ablagehoehe an Stelle 14 nie. Das Etikett kommandierte bei jeder
  Absenkung auf den Sockel **18 mm** (in die Platte hinein) und oeffnete bei 30 mm, waehrend die FSM
  auf 26 mm zielte. Praezisiert gegen meine erste Formulierung: die Policy haette nicht zwingend
  "gelernt, den Stapel in den Sockel zu rammen" (die Platte stoppt die Hand physisch), **der strikte
  Punkt ist, dass `aim_z` im Etikett unabhaengig von der 14. Spalte war** - Frage 2 war in dieser
  Form unbeantwortbar. **Korrektur:** `place_z = grasp_z + Auflagenhoehe`, und - beim Bauen nicht
  offensichtlich - auch die Hub-Schwelle wandert mit, aber nur ueber dem Ziel, sonst gilt ein auf
  der Auflage aufsetzendes Objekt als "nicht mehr gehoben" und der Greifzweig zielt wieder auf
  Tischhoehe. Der neue Teacher oeffnet 12 mm ueber der Ablagehoehe, **dieselbe Marge wie auf dem
  Tisch**. Gegen den echten alten Code: **0 Abweichungen auf 36000 echten Pufferzeilen**, auch mit
  14. Spalte = GRASP_Z. Die Live-Datei ist sauber (alle Stapel-Laeufe auf Kopien), die Messungen
  der Linie unberuehrt (Teacher folgt der FSM, nicht den Etiketten). Neuer Messplan fuer Frage 2:
  **kontrafaktische Probe am Netz** statt Freeze - echte Ablagezustaende, nur die 14. Spalte
  getauscht, `aim_z` vergleichen; vorher ist die Differenz exakt 0. Falle, die trotz Wiki-Eintrag
  zuschlug: in der `pc_cvnn`-Variante ist `J5_CLOSED_TH = 0,27`, meine erste Probe hielt `j5 = 0,30`
  fuer geschlossen.

* **Ergaenzung**: [Der Arm stapelt](/befunde/stapeln-gemessen.md) - **das korrigierte A/B**, beide
  Arme mit `EIG_DIREKT` + `EIG_STETIG`, je 100 Episoden, Teacher fahrend. **45 von 100 Episoden enden
  in einem Stapel** (83 % der Ablagen mit Sockelziel, Versatz Median 17 mm), gegen 49 Lieferungen
  im Marker-Arm (p = 0,67) - die Aufgabe kostet nichts Messbares. Zielwurf 100/100, aufgeloest
  86/100 (erstes A/B: 17 und 9). **Der Kontrollarm ist zeichengenau identisch zum ersten A/B**, alle
  100 Ausgaenge - die neuen Schalter beruehren ihn nicht. Zwei Befunde darueber hinaus: (1) **die
  Welt zaehlt nur 26 der 45 Stapel als geliefert** (58 %), weil das Kriterium 25 mm zum Zielpunkt
  misst statt "liegt auf der Auflage"; die Quote 44 % unterschaetzt die Aufgabe fast um die Haelfte.
  Nicht still umgestellt - das ist eine Entscheidung. (2) **Der Selbstrichter unterscheidet nicht**:
  "geliefert" bei 40 von 45 Stapeln UND bei 6 von 9 Ablagen neben dem Sockel (p = 0,12). Er findet
  vermutlich den Sockel-Blob am Zielort statt des Objekts. Folge, wenn es sich haelt: die
  Selbst-Imitation lernt misslungene Stapel als gelungen. Erste Zahl zu Frage 3.

* **Anlage**: [Der Arm stapelt 19 von 20](/befunde/stapeln-gemessen.md) - das Stapel-A/B (je 100
  Episoden, Sockel in BEIDEN Armen, nur das Ziel verschieden) und zwei Diagnoselaeufe. **Das A/B
  sah zuerst leer aus und war es nicht**: Quote 49 gegen 47 % (p = 0,89) und scheinbar 3 von 12
  Stapeln. Beides falsch gelesen. Nur **17** von 100 Episoden bekamen ueberhaupt eine Adresse, nur
  **9** loesten auf den Sockel auf - der Quotenvergleich ist also Marker gegen Marker. Und das
  Stapelurteil war **mein Messfehler, zweifach**: es fiel schon, wenn der WURF gelang, auch wenn der
  AUFLOESER danach still auf den Marker zurueckfiel (6 von 12 hatten gar nicht auf den Sockel
  gezielt - losgelassen 6 mm vom Ziel, aber 116 mm vom Sockel), und es verlangte "vollstaendig auf
  der Platte" (<23 mm) und verwarf stabile Stapel bei 27 und 35 mm. **Richtig gezaehlt: 5 von 6.**
  Beides im Code korrigiert (Urteil nur bei echter Aufloesung, nach der Hoehe). **Diagnose:** der
  Wurf lieferte bisher STILL `None`; die neue Zeile `[Zielwurf]` zeigte 37 von 40 mal denselben
  Grund - **der Sockel hat weder Farb- noch Formklasse**. Die Ursache habe ich selbst gebaut: ich
  hatte ihm die Farbe mit dem GROESSTEN Abstand zu allen bekannten gegeben, genau deshalb gehoert er
  zu keiner. **Der Agent kannte den Sockel nicht.** Die Loesung war diese Woche schon gebaut: die
  [Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md). Mit `EIG_DIREKT` + `EIG_STETIG`:
  Wurf **20 von 20**, Aufloesung 19 von 20, **Stapel 12 von 12**, zehn der Adressen lauten nur
  `auf ~gesehen` - ohne jede Klasse. Vorher dicht gemacht: `_direkt_adressieren` haette den Sockel
  sonst als kommandierbares Objekt registriert. **Zusammen 19 von 20 Stapeln**, wo der Sockel das
  aufgeloeste Ziel war. Offen: die Welt zaehlt nur 7 der 12 Stapel als geliefert (Kriterium misst
  25 mm zum Zielpunkt statt "liegt auf der Auflage" - bewusst NICHT still umgestellt), und der
  Selbstrichter sagt bei allen 12 "geliefert", entgegen meiner Vorhersage - ob aus dem richtigen
  Grund, ist Frage 3. **Kein Lernnachweis**: Teacher fahrend.

* **Seed-29-Basis bestätigt**: [D0 Seed 29: Wrist-Evaluation](/befunde/dream-rsi-d0-seed29-wrist-evaluation.md) -
  die gefrorene Seed-101-Familie ist vollständig und integer (40/40 Episoden, keine
  Lernmutation, Basis-SHA unverändert). Ihre vorregistrierten Zähler reproduzieren die frühere
  Basisfamilie exakt: Lieferung 21/40, ausgerichtete Wrist 6/40, Enthaltungen 8/40.

* **Seed-29-Training**: [D0 Seed 29: Wrist-Evaluation](/befunde/dream-rsi-d0-seed29-wrist-evaluation.md) -
  das unveraenderte 120-Episoden-Rezept besteht mit 92 vollen Selbst-Krediten in fuenf Wrist-
  Zellen. Die Checkpoint-Kopie ist erwartungsgemaess mutiert, die D0-Basis unveraendert;
  Wirkungsnachweis erst nach den beiden gefrorenen Testfamilien.

* **Negative Linie geschlossen**: [D0 Seed 17: Wrist-Evaluation](/befunde/dream-rsi-d0-seed17-wrist-evaluation.md) -
  auch auf Seed 103 verschiebt der Checkpoint die Wrist-Wahl Richtung Ausrichtung (3/40 -> 7/40),
  verliert aber Lieferung (26/40 -> 23/40). Gepoolt: Auswahl +10 statt +20 Punkte, Lieferung
  -3,75 Punkte. Seed 29 folgt nach unveraendertem Vertrag; kein Nachtraining von Seed 17.

* **Negativer Zwischenbefund**: [D0 Seed 17: Wrist-Evaluation](/befunde/dream-rsi-d0-seed17-wrist-evaluation.md) -
  nach 120 Trainingsfolgen liefert der Checkpoint auf der vollstaendig protokollierten
  Seed-101-Familie wie die Basis 21/40. Ausgerichtete Wrist-Wahl steigt nur 6/40 auf 8/40,
  das Selbsturteil 23/40 auf 21/40. Die zweite festgelegte Testfamilie folgt; kein
  Wirkungsurteil und kein Nachtraining nach diesem Zwischenstand.

## 2026-09-19

* **Messluecke geschlossen**: [D0-Integritaet](/mechanismen/dream-rsi-d0-integritaet.md) und
  [D0-Wrist-Lernaufgabe](/messungen/dream-rsi-d0-wrist-lernaufgabe.md) verlangen nun ein
  getrenntes `episodes.jsonl` fuer alle ausgefuehrten Aktionen. Die erste Seed-17-Auswertung
  liefert 21/40 wie die Basis, protokollierte aber nur 32 Kreditzeilen und kann daher die
  primaere Wrist-Auswahlmetrik nicht beantworten. Kein Wirkungsurteil vor der Wiederholung.

* **Reparatur und Preflight**: [D0-Zustandsmutation](/befunde/dream-rsi-d0-preflight-mutation.md) -
  der gefrorene 40-Episoden-Test fand eine Fovea-Lernmutation (1883 W, 65 V). Der isolierte
  `learn=False`-Test besteht; `HexFovea` erzwingt deshalb im D0-Modus zentral einen
  schreibgeschuetzten Schritt. Ein neuer FSM-L-Form-Gegenlauf auf eigener Pkl-Kopie besteht mit
  **0 Lernzustandsdifferenzen**, auch ueber die volle Seed-101-Familie von 40 Episoden.

## 2026-09-18

* **Anlage**: [Die Relation "auf", gebaut](/mechanismen/relation-auf-gebaut.md) - **Stufe 2 steht**,
  `ACT23_ZIEL_RELATION=auf` (Vorgabe "an"). Gegenueber "an" fallen Peilung und Abstand weg, dafuer
  liefert `goal_fn` eine dritte Groesse: `tgt_z = GRASP_Z + Oberkante des Bezugskoerpers`.
  Begruendung der Formel auf der Seite (GRASP_Z ist die HANDhoehe bei Ruhemitte 0,012, alle Koerper
  dieser Welt sind 24 mm hoch). **Die Oberkante ist das einzige Privileg auf diesem Pfad** - eine
  Ebenen-Homographie gibt keine Hoehe her -, zulaessig als Teacher-Geruest nach
  [Laufzeitregeln](/mechanismen/laufzeit-regeln.md), und solange die Policy die 14. Zustandsspalte
  nicht nutzt, **ist ein "auf"-Lauf ein Teacher-Lauf**. Dazu `ACT23_SOCKEL` (die Platte in die
  Szene) und `state.STUETZEN` - Moebel, getrennt von `OBJECTS`, damit die Neugier den 70-mm-Sockel
  nicht zum Greifen auswaehlt, aber im Posen-Schnappschuss, damit die Aufraeumschleife ihn
  zurueckstellt. **Vier fremde Schalter muessen mit** (`ACT16_GOAL_Z`, `ACT16_ZIEL_SAEUBERN=0`,
  `ACT16_ERFOLG_RUHT`, `ACT23_SOCKEL`); ohne sie ist "auf" nicht wirkungslos, sondern **still
  falsch**, deshalb prueft der Start und meldet jeden einzeln - keiner legt einen anderen heimlich
  um. **Rauchtest:** 2 saubere Stapel in 4 adressierten Episoden (Versatz 14 und 20 mm, beide als
  geliefert gezaehlt), Sockel auf 1-8 mm wahrgenommen. Kein Quotenbefund (n = 6, ein Seed, Teacher
  fahrend).

* **Anlage**: [Der Sockel braucht 80 mm Freiraum](/befunde/sockel-braucht-80mm-freiraum.md) - zwei
  Pruefstandsmessungen, und eine davon **korrigiert meinen eigenen Code**. (1) Der Sockel wird auf
  **5,9 mm** genau lokalisiert (max 8,5), systematisch zur Kamera hin und mit dem Kameraabstand
  wachsend - dieselbe Parallaxe wie beim gestapelten Wuerfel, nur klein, weil die Platte flach ist.
  0 % ueber der Stapeltoleranz von 23 mm; ein Wuerfel wird auf 0,8 mm lokalisiert. **Die Platte ist
  kein Ortsproblem.** (2) Ein Objekt daneben bleibt erst ab **60 mm entlang der Achsen und 80 mm
  auf den Diagonalen** eine eigene Detektion (die Ecken der quadratischen Platte reichen am
  weitesten). **Meine erste Freiraum-Schranke im Code rechnete Ueberlappung** - Halbdiagonale plus
  Halbdiagonale = 66 mm - und das ist die falsche Groesse: Blobs verschmelzen lange bevor sie sich
  beruehren. Mit der gemessenen Schranke passt der Sockel nur bei `ACT23_SCENE_N` bis **4** in den
  Arbeitsraum (bester Freiraum 105 / 86 / 72 / 62 mm bei 3 / 4 / 5 / 6 Objekten). Die Vorgabestelle
  ist jetzt gesucht statt geraten: mit der geratenen (81 mm) las der Agent die Platte 14-18 mm
  daneben, mit der gesuchten (86 mm) 1-8 mm. **Was sich nicht wegplanen laesst:** ein abgelegtes
  Objekt bleibt oben liegen, ab dem ersten Stapel ist der Sockel-Blob per Bauart verschmolzen - das
  ist die Aufgabe, nicht ein Layoutfehler, und genau dafuer ist die Farbstreuung da. Der Start sagt
  es laut, damit niemand die spaeteren Mehrdeutigkeiten fuer einen Fehler haelt.

* **Technische Validierung**: [D0 Seed 17](/befunde/dream-rsi-d0-seed17-block60.md) - der erste 60er-Block ist kein Lernbefund: sein neuer Filter liess `sicher geliefert` aus und meldete daher 4 statt 40 gueltige Selbst-Kredite. Die Rohdaten erreichen nach dem getesteten Filter fuenf Wrist-Zellen, bleiben aber nur Werkzeugvalidierung; Seed 17 wird auf neuer Kopie wiederholt.

* **Bau**: [D0-Integritaet](/mechanismen/dream-rsi-d0-integritaet.md) um den isolierten
  Trainingslinien-Runner ergaenzt. Er schreibt nur eine neue Checkpoint-Kopie, filtert die
  vorab definierten Selbst-Kredite und prueft die Wrist-Abdeckung an den 60-/120-Episoden-
  Toren. Kompilierung, Hilfe und ein synthetischer Filtertest sind OK; kein ACT23-Lauf gestartet.

* **Messvertrag**: [D0-Wrist-Lernaufgabe](/messungen/dream-rsi-d0-wrist-lernaufgabe.md) -
  Pilotvertrag v1 vor dem ersten Lernlauf festgelegt: zwei Linien (Seeds 17/29), je 120
  Trainingsepisoden, zwei getrennte 40er-Testfamilien (101/103), Selbst-Kreditfilter,
  Freeze-Kontrolle, Effekt- und technische Abbruchregeln. Die fehlende serialisierte
  Szenenliste ist als D0-Pilotgrenze explizit dokumentiert.

* **Freeze-Preflight**: [D0-Zustandsmutation](/befunde/dream-rsi-d0-preflight-mutation.md) - eine
  eingefrorene FSM-L-Form-Episode besteht: Pkl-Kopie bitgleich und **0 geaenderte
  Lernkomponenten**. Sechs Vollzustandsdifferenzen bleiben als Diagnose sichtbar und sind
  explizit von Gewichten, Puffern und dauerhaften Kalibrierungen getrennt. Werkzeugtest und
  Kompilierung OK; noch kein Lernvergleich.

* **Wiederholung**: [D0-Zustandsmutation](/befunde/dream-rsi-d0-preflight-mutation.md) fuer die
  nun exakt gepinnte L-Form. Die Kreditzeile ist ein sauberer eigener Aktion- und Selbsturteil-
  Fehlgriff (Gewicht 1,0, relativer Wrist 22,5 Grad); Pkl weiter bitgleich, dieselben 9/10
  beobachteten Komponenten mutieren. Der Preflight gilt damit fuer die D0-L-Aufgabe, ist aber
  kein Lernvergleich.

* **Preflight**: [D0-Zustandsmutation](/befunde/dream-rsi-d0-preflight-mutation.md) - erste
  kopflose FSM-Episode auf einer Kopie der D0-Basis: Pkl bitgleich, aber **9/10** beobachtete
  In-Process-Komponenten veraendert. Der erwartete FAIL belegt unmittelbar, dass `NO_PERSIST`
  keine eingefrorene Evaluation ist. Die Kreditzeile ist Selbst/Selbst und voll gewichtet; der
  Objektfilter traf wegen Teilwort `L` allerdings den roten Wuerfel. Runner auf `L-Form`
  korrigiert; noch kein L-Wrist-Vorversuch und kein Lernbefund.

* **Bau**: [D0-Integritaet](/mechanismen/dream-rsi-d0-integritaet.md) um den
  `D0EvaluationRunner` erweitert. Er kopiert die Pkl, startet eine begrenzte kopflose
  FSM-Evaluation, vergleicht In-Process-Manifeste und den Pkl-Hash und schreibt ein maschinell
  pruefbares Ergebnis. Runner-Hilfe, Integritaetstest und Kompilierung OK; kein ACT23-Lauf
  gestartet. Der erste Lauf ist bewusst ein Preflight auf Mutation, nicht schon die Kontrolle.

* **Bau**: [D0-Integritaet](/mechanismen/dream-rsi-d0-integritaet.md) - der Wegwerfpfad hat jetzt
  SHA-256-Fingerabdruecke je Lernkomponente und ein opt-in JSONL-Kreditprotokoll
  (`ACT23_D0_CREDIT_JSONL`). Werkzeugtest und Python-Kompilierung sind erfolgreich; kein
  ACT23-Lauf gestartet. Der noch fehlende Runner muss die Fingerabdruecke um feste Testepisoden
  legen und jede Mutation abbrechen.

* **Codeaudit**: [D0-Wrist-Audit](/befunde/dream-rsi-d0-wrist-audit.md) - das aktuelle
  Weltmodell kann Wrist-Kandidaten um den wahrgenommenen Objekt-Yaw bilden; Drucksensor- und
  FSM-Anfahrtsrouten liefern heute kausale Negativkredite. Zwei Bedingungen korrigieren den
  Entwurf: Primaerer Selbstlernbeleg zaehlt nur `Label Selbst`, weil sonst `s_ok=None` auf die
  privilegierte Welt faellt; `ACT23_NO_PERSIST` und `EXV_FREEZE` belegen keine vollstaendige,
  nichtmutierende D0-Kontrolle. Vor einer Serie wird deshalb ein wegwerfbarer Evaluator mit
  Komponentenhash und Kreditprotokoll gebaut. Kein Lauf gestartet.

Neueste zuerst. Datumsueberschriften in ISO-Form `YYYY-MM-DD`. Ein Eintrag je Vorgang, das
fuehrende fette Wort ist Konvention: **Anlage**, **Ergaenzung**, **Widerlegung**, **Ruecknahme**.

Fuer eine schnelle Uebersicht: `grep "^## " wiki/log.md | head -5`

* **Entscheidung**: [D0-Kandidat: Wrist-Lernaufgabe](/messungen/dream-rsi-d0-wrist-lernaufgabe.md)
  ausgewaehlt. Der historische `act23-ab`-Befund zeigt echte eigene Verbesserung der
  objektrelativen Wrist-Wahl; Formpiloten, sofortige Direktadressen, Stapeln und Fovea erfuellen
  die D0-Anforderung derzeit nicht. Noch kein Lauf: Kredit- und Zustandsaudit stehen davor.

* **Anlage**: [D0: Y/T-Trennbarkeit](/befunde/dream-rsi-yt-trennbarkeit.md) - zwei neue
  Klassifikator-Seeds: ein LOO-Nachbar trennt Y/T lokal zu 90,6 bzw. 92,2 %, die tatsaechliche
  Dreisicht-Open-Set-Klasse beansprucht aber 59/64 T-Sichten. Das lokalisiert die Grenze beim
  aktuellen Anspruchspfad; keine Aussage ueber Armleistung. D0 bleibt offen.

* **Ergaenzung**: [D0-Gegenprobe](/befunde/dream-rsi-d0-lernaufgabe.md) abgeschlossen:
  frischer Grundform-Lerner erkennt Y in beiden Seeds ab drei Sichten zu 24/24, beansprucht
  aber jeweils alle vier T-Kontrollen. Freeze 0/24; Gewichte und Live-Zustand unveraendert.
  Beide Varianten als Scheduler-Benchmark verworfen; D0 bleibt offen. Messwerkzeug und
  Rohbelegverweise gesichert, keine D1-Implementierung und kein Arm-Lernnachweis.

## 2026-09-17

* **Widerlegung**: [Der Mindestabstand ist die Mechanik](/befunde/nahe-ablage-ist-mechanik.md) -
  der Trennungstest zu Punkt 4, und er widerlegt **meine eigene** Ursachen-Lesart von heute
  Nachmittag. Zwei Arme je 60 Episoden bei 30 mm Ablageabstand, alles gleich ausser
  `ACT23_CHOREO` (fsm gegen netz). **Der geskriptete Teacher hat kein Training** - er ist eine
  reaktive Funktion, die stur auf `[tgt, GRASP_Z]` faehrt - und legt **genauso weit weg ab wie die
  Policy**: Ueberschuss +25,0 gegen +21,0 mm (Mann-Whitney p = 0,14), zu weit in 97,4 gegen
  96,8 %, 5. Perzentil 31,9 gegen 32,5 mm. Ein Verhalten, das ein untrainierter Regler genauso
  zeigt, ist nicht das Ergebnis fehlender Daten. **Es ist die Klauenmechanik**, und das neue
  Messfeld `Bezug verschoben` zeigt sie direkt: der Nachbarkoerper wird in **64,1 %** der
  Teacher-Ablagen verschoben (Netz 38,7 %, Fisher p = 0,053), Median 9 mm, max 45 mm.
  **Getrennt nach Beruehrung wird es eindeutig:** beruehrt der Teacher den Nachbarn, endet das
  Objekt +21 mm zu weit; beruehrt er ihn NICHT, endet es +55,5 mm zu weit. **Es gibt kein "nah UND
  sauber"** - eine Ablage unter 35 mm ohne Beruehrung gelingt 1 von 39 (Teacher) und 1 von 31
  (Netz), zusammen **3 von 70**. **Folge fuer das Stapeln, und sie ist die Umkehrung des
  Erwarteten:** die Sperre ist LATERAL (die Klaue senkt neben einem Hindernis ab); beim Stapeln
  liegt der Bezugskoerper UNTER dem Objekt und gar nicht im Absenkweg. **"auf B" ist mechanisch der
  leichtere Fall, "an B" bei kleinem Abstand der schwerere** - die Stufenfolge im Entwurf ist
  entsprechend umsortiert, und der geplante Trainingslauf ohne `ZIEL_SAEUBERN` **entfaellt**: es
  gibt nichts abzuschauen. Falle fuer die Nachwelt: `Bezug verschoben` muss VOR der
  Aufraeumschleife gemessen werden, die jeden nicht-kommandierten Koerper zuruecksetzt - danach
  bekommt man lauter Nullen und schliesst das Gegenteil.

* **Ergaenzung**: [Der Arm hat einen Mindestabstand von rund 37 mm](/befunde/mindestabstand-zur-ablage.md) -
  Titel, Kurzbeschreibung und der Ursachen-Abschnitt als **widerlegt** gekennzeichnet; die Zahlen
  der Seite stehen unveraendert. Der falsche Abschnitt bleibt als Beleg dafuer stehen, wie
  plausibel er war. Ebenso fortgeschrieben: [Stufe 2 vorbereitet](/mechanismen/stufe2-vorbereitet.md)
  (Punkt 4 beantwortet, Reihenfolge gedreht) und
  [Stapeln als neue Aufgabe](/fragen/stapeln-als-aufgabe.md) (Stufentabelle umsortiert).

* **Anlage**: [Der Arm hat einen Mindestabstand von rund 37 mm](/befunde/mindestabstand-zur-ablage.md) -
  Punkt 4 der Stufe-2-Liste, gemessen als Dosis-Wirkung: vier Arme je 100 Episoden mit
  Ablageabstand **30 / 50 / 70 / 90 mm**, aus identischen Zustandskopien, Seed 4242,
  `ACT16_ZIEL_SAEUBERN=0` in allen (sonst haette die Regel jede Vorgabe unter 50 mm still auf
  50 mm aufgeblasen und die Kurve waere flach gewesen, ohne dass man es sieht).
  **Das Ergebnis ist kein Zielfehler, sondern ein MINDESTABSTAND.** Ueberschuss (Ist minus Soll)
  zum Bezugskoerper: bei 90 mm **-0,5 mm** und sauber symmetrisch (48,5 % zu weit), bei 70 mm +8,
  bei 50 mm +7, bei 30 mm **+20,0 mm und in 93,3 % der Faelle zu weit** (Spearman rho = -0,389,
  p = 1,3e-10; Mann-Whitney 30 gegen 90 p = 3,2e-09). Ueber alle 254 Ablagen landen nur **1,2 %
  naeher als 20 mm** an einem Koerper, das 5. Perzentil liegt bei **37,6 mm**.
  **Woran es NICHT liegt:** nicht an einem Stoss nach dem Loslassen - die Drift ist in allen vier
  Armen gleich (Median 13,0-14,0 mm, Trend rho = +0,013, p = 0,83), das Objekt wird also **nicht
  weggestossen, sondern gar nicht erst hingebracht**; nicht hauptsaechlich an der Wahrnehmung (der
  neu protokollierte Glaubensfehler beim Loslassen liegt bei Median 12,5-16 mm in allen Armen,
  grobe Fehler >25 mm 19,7 % bei 30 gegen 7,6 % bei 90 mm - ein Nebeneffekt, kein 20-mm-Versatz in
  93 % der Ablagen); nicht an der Adressierung (86-93 von 99 eindeutig, ohne Trend). Die Quote
  (38 / 47 / 48 / 51 %) traegt **nichts** - bestes p = 0,087.
  **Die naechstliegende Ursache ist die Regel selbst:** `run_combined` saeubert seit jeher jedes
  Ziel auf 0,05 m Abstand zu jedem Koerper, also lag in der gesamten Vorgeschichte **kein einziges
  Ablageziel naeher als 50 mm an einem Koerper** - das ist Bauart, nicht Vermutung. Die Policy hat
  die Situation nie gesehen, und der gemessene Boden von ~37 mm ist die Extrapolationsreichweite
  jenseits des Trainingsrandes. **Die Regel, die das Stapeln verbietet, hat auch die Daten
  verhindert, mit denen man es lernen koennte.** Gegenkandidat ist die Klauenmechanik; beide sagen
  denselben Boden vorher und trennen sich an einer billigen Frage - bewegt sich der Bezugskoerper?
  Nicht protokolliert, naechste Messung. Gebaut dafuer: `ACT16_ZIEL_SAEUBERN` (Vorgabe 1) und zwei
  Messfelder in der Ablage-Zeile (`Glaube`, `zum Bezug`).

* **Widerlegung (Teil)**: [Die Zieladresse traegt](/befunde/ziel-als-adresse-gemessen.md) - der
  dort gemessene Schwanz **p90 = 86,0 mm** bei 50 mm Abstand **reproduziert sich nicht** (hier
  43,4 mm). Drei Unterschiede: Saeuberungsregel an statt aus, XML mit Sockel (und nach den
  Invarianten sind Laeufe ueber eine XML-Aenderung hinweg nicht vergleichbar), 140 gegen 100
  Episoden. Was sich BESTAETIGT, ist die Lesart darunter: die Drift nach dem Loslassen aendert sich
  ueber den Abstand nicht - falsch hingetragen, nicht weggestossen. Nachtrag auf der Seite; die
  Zahl gilt nur fuer ihre eigene Konfiguration.

* **Anlage**: [Stufe 2 vorbereitet](/mechanismen/stufe2-vorbereitet.md) - drei Teile gebaut, alle
  auf Schaltern mit Vorgabe 0: der **Sockel** (70 x 70 x 8 mm, tiefblau, schwer, geparkt),
  **`ACT16_GOAL_Z`** (goal_fn darf drei Werte liefern, die Ablagephase zielt auf `tgt_z` statt auf
  die Konstante `GRASP_Z`, und der Zustandsvektor der Policy bekommt die Hoehe als 14. Eingang) und
  **`ACT16_ERFOLG_RUHT`** (Erfolg heisst "ruht und Klaue offen" statt woertlich "liegt auf dem
  Tisch"). **Warum die 14. Spalte auf einen Schalter gehoert:** sie ist KEINE verhaltensneutrale
  Ergaenzung - der Vorwaertsdurchlauf bleibt bitgleich (gemessen, `max |diff| = 0.0` nach der
  Migration mit Nullspalten), aber ein frisches Netz wird mit anderer Breite gezogen und jeder
  Refit sieht eine Spalte mehr. **Die Migration braucht ausnahmsweise kein Gueltigkeits-Flag:**
  beim Tastsinn waere "0 N" die Luege "Klaue leer" gewesen, die Ablagehoehe dagegen WAR in jeder
  alten Episode `GRASP_Z` - der Neutralwert ist die Wahrheit.

* **Anlage**: [Der Sockel verschluckt den Stapel](/befunde/sockel-verschluckt-den-stapel.md) -
  die Messung am Sockel, und sie faellt anders aus als geplant. Ein Wuerfel auf der Platte wird in
  **0 von 25** Stellen eine eigene Detektion; die Flaeche aendert sich um **kein einziges Pixel**,
  weil die Silhouette des Wuerfels ganz innerhalb der Platte liegt. Nicht ungenau lokalisiert,
  sondern **verschluckt** - die Frage nach dem Parallaxenfehler stellt sich gar nicht. Der
  Chroma-Schnitt hilft nicht (ebenfalls 0 von 25): er ist auf "Deskriptor trifft KEINE Klasse"
  verriegelt, und der Sockel-Blob loest sauber als `U` auf. **Was ihn doch verraet, ist `cspread`:**
  leer 0,069 (max 0,118), belegt 0,149 bis 0,397 - ueber 100 Positiv- und 50 Negativfaelle **kein
  einziger Ueberlapp**, Abstand +0,030. Zusammen mit der unveraenderten Flaeche ergibt das eine
  Signatur aus schon berechneten Groessen: **Flaeche unveraendert + Farbstreuung hoch = da liegt
  etwas drauf**, und das trennt einen Stapel auch von zwei nebeneinander verschmolzenen Koerpern,
  deren Flaeche sich ADDIERT. "A liegt auf B" wird damit als RELATION lesbar statt als zweite
  Position. Engpass ist Violett (0,161), die dem Sockelblau naechste Farbe; der Sockel steht
  deshalb nicht in `_FARB_KOERPER`. Der Nachtrag im Entwurf entkraeftet entsprechend den Absatz
  "Hoehe aus dem Widerspruch Ort/Groesse lesen" fuer den Sockel-Fall.

* **Ergaenzung**: [Invarianten](/mechanismen/invarianten.md) - neue Regel aus diesem Einbau:
  **ein zusaetzlicher KOERPER im Modell veraendert das gerenderte Bild, immer.** Zustand bitgleich
  (`qpos` und `qvel` Zeichen fuer Zeichen identisch), Bild nicht: **2 von 57.600 Pixeln**, +44 im
  Rotkanal an der Silhouettenkante des roten Wuerfels. Der Effekt bleibt unveraendert 2 Pixel, wenn
  man den Koerper voellig durchsichtig, winzig oder in eine ausgeblendete Geom-Gruppe setzt - es ist
  der Szenengraph, nicht sein Aussehen. Da die ganze Wahrnehmung am Bild haengt, driften zwei
  Laeufe danach auseinander (Warmup ab Schritt ~100, `sensor_err` 40,05 gegen 40,04).
  **Wer einen Koerper hinzufuegt, kann keinen Lauf mehr bitweise mit einem Lauf von davor
  vergleichen; beide Arme eines A/B muessen dieselbe XML fahren.** Verhaltensneutral ist es
  trotzdem: 5 frische Episoden gegen einen `git worktree` auf `84a5d71`, Befehle und Ausgaenge
  identisch, 4 von 5 millimetergenau gleich, eine 87 gegen 89 mm.

* **Anlage**: [Die Zieladresse traegt](/befunde/ziel-als-adresse-gemessen.md) - das A/B zum
  Bau, drei Arme je 140 Episoden aus identischen Kopien von `ad9d768c`, Seed 4242:
  `ort` / `an05` / `an09`. **Die Adresse traegt:** 127/139 = 91,4 % bzw. 135/139 = 97,1 % loesen
  eindeutig auf, der Bezugskoerper wird auf **1,0 mm** Median wahrgenommen (p90 7 mm). Das
  Ablageziel kommt damit aus der Kamera statt aus `mocap_pos`. **Der Preis, und seine richtige
  Zuordnung:** Lieferquote 57,1 -> 35,7 % bei 50 mm Ablageabstand (Fisher p = 4,9e-4,
  Bonferroni-Schranke 0,0167), aber **49,3 % bei 90 mm und damit vom Marker-Arm nicht zu
  unterscheiden** (p = 0,231). Der Abstand allein holt **13,6 der 21,4 verlorenen Punkte** zurueck -
  und die unabhaengige Messung der [Nachbarnaehe](/befunde/nachbarnaehe-im-lauf.md) hatte
  **13,9 Punkte** vorhergesagt. Ohne diesen dritten Arm stuende hier eine falsch zugeordnete
  Aussage; der direkte Vergleich an05 gegen an09 (p = 0,029) traegt die Schranke NICHT, belastbar
  ist nur die Lage zum Marker-Arm. **Wo der Verlust sitzt:** nicht im Griff (129/120/126
  gegriffen), sondern in der letzten Etappe (liefern|abgelegt 75,5 -> 54,9 %, p = 0,0027) - und
  dort **nicht im Median, sondern im oberen Zehntel**: seitlicher Fehler beim Loslassen p90
  **86,0 mm gegen 31,5 mm**, waehrend der Median in allen drei Armen exakt 25,0 mm ist und die
  Drift nach dem Loslassen praktisch gleich. **Das Objekt wird also falsch hingetragen, nicht
  weggestossen** - die Signatur der [Ablenker-Bindung](/befunde/ablenker-anfahrt.md), diesmal am
  ZIEL statt am Objekt. Nicht bewiesen; der Gegenkandidat (Absenken ueber den Nachbarn hinweg)
  braucht die Schrittdaten des Transports. **Folge fuer Stufe 2:** Stapeln verlangt ein Ziel mit
  0 mm Abstand zu einem Koerper - der Transport muss das aushalten, und heute haelt er 90 mm gut
  und 50 mm schlecht. Das ist der naechste konkrete Zwischenschritt und war vorher nicht sichtbar.

* **Anlage**: [Das Ablageziel als Adresse](/mechanismen/ziel-als-adresse.md) - **Stufe 1 aus dem
  Stapel-Entwurf ist gebaut**, `ACT23_ZIEL_ADRESSE` (Vorgabe 0). Die Sprache waechst um einen TYP,
  nicht um ein Verb: `BEZUG := ORT | RELATION ADRESSE`, Relation "an". `_ziel_adresse_wuerfeln`
  waehlt je Episode einen Bezugskoerper und wuerfelt seine Adresse mit derselben
  `_adresse_wuerfeln`-Fassung wie fuer das Objekt; `_ziel_aufloesen` findet ihn beim Abholen des
  Ziels ueber `finde_nach_eigenschaften` wieder und gibt die Stelle `ZIEL_ABSTAND` (0,05 m) daneben
  zurueck. **Damit verliert das Kommando sein letztes Privileg:** `goal_fn` las bisher
  `marker_xy` -> `sim.d.mocap_pos`, eine Designer-Koordinate; jetzt kommt das Ziel aus der Kamera.
  Entscheidungen mit Begruendung auf der Seite: neben statt auf (die Hoehe ist mit einer
  Ebenen-Homographie nicht beurteilbar), 0,05 m ist die Zahl, mit der act16 ohnehin jedes Ziel von
  Koerpern wegschiebt, die Peilung wird gewuerfelt statt gesetzt, die Adresse darf hier die Farbe
  nennen (sie gilt nur fuer EINE Episode), mehrdeutig zaehlt wie nicht gefunden und wird laut
  protokolliert, und `mocap_pos` muss um `perceive_all` herum gesichert werden, sonst liefert
  ausgerechnet der Rueckfall eine GEPARKTE Markerkoordinate. **Verifikation:** Vorgabepfad ueber
  5 frische Episoden (Seed 4242) gegen `HEAD` - **64 Inhaltszeilen, 0 Unterschiede**; die 18
  Kopfzeilen weichen ab, weil der Vergleichsstand aus dem Scratchpad lief und `_source_defaults()`
  dort keine Nachbardateien findet (Artefakt des Aufbaus, auf der Seite als Falle vermerkt).
  Rauchtest mit Schalter auf einer Zustandskopie: **4 von 4 Zieladressen eindeutig**, Bezugskoerper
  auf 1-5 mm wahrgenommen, 2 von 4 geliefert. **Vorab benannter Konfounder fuer das A/B:** ein Ziel
  50 mm neben einem Koerper liegt in der Zone, in der
  [Nachbarnaehe](/befunde/nachbarnaehe-im-lauf.md) gemessen 13,9 Punkte kostet - die Kontrolle
  `ACT23_ZIEL_ABSTAND=0.09` ist eingebaut.

* **Anlage**: [Stapeln als neue Aufgabe](/fragen/stapeln-als-aufgabe.md) - Nutzeridee vom
  2026-09-17: als Ziel andere Objekte angeben koennen. **Machbar, und ungewoehnlich billig**, weil
  vier Voraussetzungen schon stehen: das Ablageziel ist ein HAKEN (`goal_fn`), es ist schon ein
  LATENT (`post_goal_fn` / `set_goal_vector`), es wird waehrend des Tragens in jedem Schritt NEU
  GELESEN (`place_servo_fn`), und Adressen aufloesen kann der Agent seit `ACT23_EIG_DIREKT` aus
  einer einzigen Sichtung. **Der Sprachvorschlag:** kein neues Verb, sondern ein Typ mehr -
  `BEZUG := ORT | RELATION ADRESSE`, der Zielplatz bekommt denselben Typ wie das Objekt. Die
  RELATION ist im Latentraum eine Verschiebung, und **RoPE macht eine Verschiebung zur exakten
  Phasendrehung** - "auf B" ist das Latent von B, um eine gelernte Objekthoehe phasengedreht, nicht
  ein Koordinatenaufschlag. Damit gilt die Relation an JEDER Stelle, weil die Phase die Position
  traegt; das ist die Hypothese, die dem komplexen Wrist-Kopf fehlte. **Nebengewinn:** das
  Ablageziel ist heute das einzige Stueck des Befehls, das der Agent NICHT wahrnimmt
  (`marker_xy` liest `mocap_pos`) - eine Zieladresse nimmt dieses Privileg weg. **Drei bezifferte
  Huerden:** (1) act16:382-394 schiebt ein uebergebenes Ziel in acht Durchgaengen um 0,05 m von
  jedem Koerper WEG - eine Laufzeitregel gegen Stapel; (2) der Erfolgsbegriff ist flach in beiden
  Richtungen, privilegiert `rested = cz < half+0,010` ("liegt auf dem Tisch") und beim Selbstrichter
  ueber die Homographie; (3) Ablagegenauigkeit Median 21-25 mm gegen eine geometrische
  Stapeltoleranz von 12 mm - **die Aufgabe verlangt die doppelte Genauigkeit des Vorhandenen**,
  Abhilfe waere ein breiter flacher Sockel als erstes Stapelziel. Die eigentliche Arbeit: das Ziel
  ist ueberall 2D (`GoalModule2D`, und im Policy-Zustand act16:601 steht kein `tgt_z`) - Stapeln ist
  die erste Aufgabe, die eine dritte Dimension im ZIEL braucht. Vier Stufen vorgeschlagen, Stufe 1
  ("an ADRESSE" statt Koordinate) ist fuer sich wertvoll und mit heutiger Wahrnehmung beurteilbar.

* **Anlage**: [Ein gestapelter Koerper liest 16 mm daneben](/befunde/stapeln-bricht-die-tischebene.md) -
  Stufe 0 dazu, offline am echten Wahrnehmungspfad (frischer Klassifikator, `calibrate()` aus 40
  Punkten, dann `perceive_all` an 49 Gitterstellen des Arbeitsraums, je z=0,012 und z=0,036).
  **Flach 0,8 mm, gestapelt 15,9 mm** (4,6-25,3 mm), an **12 % der Stellen ueber der
  Liefertoleranz** von 25 mm. Der Versatz zeigt zu **100 % radial von der Kamera weg** und
  korreliert mit **r = +1,00** mit dem Kameraabstand: reine Parallaxe, die Homographie ist eine
  EBENEN-Abbildung und wurde auf der Wuerfelmitte am Boden geeicht. Nebenbefund: der gestapelte
  Koerper erscheint 11-16 % groesser (span x1,114, area x1,161), und **das Groessenband kippt an
  einem Drittel der Stellen** (16/49 Dickenachse, 15/49 Spannenachse). Damit ist die scheinbare
  Groesse in einer Welt mit Stapeln keine Eigenschaft des Koerpers mehr - dieselbe Regel wie bei
  der Farbe, eine Achse weiter. **Das ist kein Hindernis, sondern der Inhalt der Aufgabe:** bei
  r = 1,00 ist die Hoehe rekonstruierbar, sie steckt im Widerspruch zwischen Ort und scheinbarer
  Groesse. Eine zweite Homographie fuer z=0,036 waere Geruest, kein Selbstlernen.

* **Anlage**: [D0: Ungebunden ist nicht unbekannt](/befunde/dream-rsi-d0-lernaufgabe.md) -
  erster vorab festgelegter Komponentenpilot: beide Seeds nach 24 Y-Sichtungen ohne neue
  Klasse, gehaltene Wiedererkennung 0/24 gegen 0/24. Kein Schaden an bekannten Formen,
  aber auch kein Lernsignal. Eine frische Grundform-Basis wird als separate Gegenprobe
  vorangemeldet; kein Nachstellen der v1-Kriterien. D0-Tor bleibt offen.

* **Anlage**: [D0-Pilotvertrag](/messungen/dream-rsi-d0-pilot.md), vor dem ersten Lernlauf
  festgelegt. Gemeinsame Basis `b351207` integriert main `15c063e`, eigener Startzustand
  `ad9d768c` per Hash geprueft. Message Board informiert. Der erste Technik-Rauchtest des
  isolierten Wahrnehmungsvergleichs besteht seine Integritaetspruefungen; nach drei
  Y-Sichten noch keine Klasse. **Kein ACT23-Lernbefund.** Der vorhandene EXV-Freeze schaltet
  nicht alle Lerner ab; deshalb zuerst ein explizit begrenzter Komponentenpilot.

* **Anlage**: [Dream-RSI: Forschungs- und Entwicklungsplan](/fragen/dream-rsi-forschungsplan.md)
  samt [Evaluationsvertrag](/messungen/dream-rsi-evaluation.md),
  [Servo-Zweig](/fragen/dream-rsi-servosteuerung.md) und
  [Fovea-Zweig](/fragen/dream-rsi-fovea.md). Nutzerauftrag: Konzept schrittweise umsetzen und
  evaluieren; alle ACT23-Bausteine duerfen untersucht werden. **Nur Planung**, alle
  Entwicklungspakete offen, `evidenz: vermutung`, `ebene: code`.
  Praezisierung der Gespraechsanalyse: historische Trainingsepisoden sind wegen geaenderter
  Lernzustaende nicht beliebig neu kombinierbar; zuerst Budgetverteilung auf getrennte echte
  Trainingslinien, erst spaeter adaptives Curriculum. D0-D7 erhalten Abhaengigkeiten und Tore;
  S0-S3 pruefen Eigenanpassung eines direkten Motorpfads, F0-F3 erst weitere Wahrnehmung auf
  vorhandenen Netzzustaenden, danach Detailausbau mit Bestandserhalt. Der historische
  F20/RES480-Versuch wird als Codehinweis mit Konfounder eingeordnet. Keine bisherigen
  Negativbefunde widerrufen, keine Trainingslaeufe und keine Implementierung gestartet.

## 2026-09-16

* **Anlage**: [Das Wrist-Gitter kostet nichts](/befunde/wrist-gitter-kostet-nichts.md) - offline am
  gelernten Weltmodell geprueft, ob der Wrist die vierte Problemachse ist (60 echte
  Puffersituationen, je 720 Winkel, LCB = mu - sigma, Gitter geschachtelt). **Er ist es nicht.**
  8 -> 16 Gitterpunkte bringt **exakt null** (gepaarter Median 0,0000); echte Gewinne beginnen erst
  unter 4 Grad Schrittweite und saettigen bei +0,023 Guete = rund 3,8 mm aequivalenter Ablage, bei
  25 mm Toleranz. **Die entscheidende Kontrolle:** das Maximum ueber 720 Punkte schlaegt das ueber
  8 auch bei reinem Rauschen. Auf der geglaetteten Kurve faellt der Gewinn 8 -> 720 von +0,0462 auf
  +0,0230 - **die Haelfte war Rausch-Jagd**, passend zu 23 % Restvariation nach Glaettung ueber eine
  halbe Stufe. Dieselben 8 Punkte nur um eine halbe Stufe zu VERSCHIEBEN kostet dagegen **-0,1057,
  also 2,3-mal so viel, wie die feinste Verfeinerung bringt.** **Die LAGE des Gitters ist wichtiger
  als seine DICHTE** - und sie ist gebaut: `ACT23_WRIST_REL` spannt das Gitter um die
  Objektachse, damit liegen zwei Punkte exakt parallel und exakt senkrecht, wo gemessen 35 % gegen
  17 % liefern. Die Messung bestaetigt WRIST_REL damit unabhaengig und von der anderen Seite.
  **Ein feineres Gitter ist nicht zu rechtfertigen und ein act23-Lauf eruebrigt sich** - genau der
  Zweck der Offline-Pruefung. Erste Fassung der Reihe war fehlerhaft (32/64/128 enthalten die 8
  Punkte nicht, die Reihe verglich verschiedene Punktmengen statt einer Verfeinerung) und ist auf
  der Seite korrigiert vermerkt.

* **Ruecknahme**: der Faden "Komplexer Wrist-Kopf" stand in
  [offene Faeden](/fragen/offene-faeden-act23.md) und der
  [Modullandschaft](/mechanismen/act23-modullandschaft.md) als **"nicht gemessen"** - beide Seiten
  korrigiert, denn **der Kern ist seit dem 2026-07-17 gebaut, Vorgabe an und gemessen.**
  `world_model.cross_augment` rechnet genau `z_w * conj(z_yaw)` (`c = cw*cy + sw*sy`,
  `s = sw*cy - cw*sy`, im Code als "Re(z_w * conj(z_yaw))" kommentiert), dazu die Schaerfe
  `|cos2(w-yaw)|` (`ACT23_WORLD_SHARP`), dasselbe Produkt gegen die ARMRICHTUNG mit
  Distanz-Interaktion (`ACT23_WORLD_ARMREL`) und die Neigung gegen die kinematisch erzwungene als
  `z_tilt * conj(z_kin)`. Belege: Kapazitaetstest **n ~ 150 statt ~3000** sauberen Zeilen fuer
  dieselbe bilineare Regel; Lauf 27/40 = 67,5 % gegen 45 % (Kontrolle: ausgerichtete Griffe 89 %,
  nicht ausgerichtete 48 % = Grundrate, der Gewinn ist also die Konditionierung).
  **Was der alte Eintrag zusaetzlich falsch nahelegte:** das Weltmodell laufe in einem
  komplexwertigen Netz. Es laeuft auf `Policy`, einem **reellen** MLP (`np.tanh`, reelle Gewichte);
  komplex sind `connection.py`, `node.py`, `relax_vec.py`, `rope.py`, `planner.py` und der
  Shape-Kopf. Dort IST `[cos2w, sin2w]` bereits `e^{2iw}` als (Re, Im) - es als komplexe Zahl zu
  schreiben aendert keine einzige Zahl. Ein nativer Kopf hiesse, ihn in die PC-Engine zu verlegen,
  und dafuer gibt es keine Hypothese, was er besser machen soll.
  **Was WIRKLICH offen bleibt:** der Wrist wird ueber ein Gitter gewaehlt (`wrist_grid=8`, also
  22,5-Grad-Stufen) und per Ensemble-Argmax gescort - die **vierte diskretisierte Achse** neben
  Farbe, Form und Groesse, und die einzige, an der die Diskretisierung nie gemessen wurde.

* **Widerlegung + Anlage**: [Eine dauerhafte Adresse darf keine Farbe nennen](/befunde/dauer-adresse-vertraegt-keine-farbe.md)
  - der entscheidende Versuch aus der Seite davor, gefahren als drei frische Arme je 140 Episoden
  (wuerfel / formzuerst / ohnefarbe, Seed 4242). **Er sollte trennen, ob die Formachse die gute ist
  oder obj_T der leichtere Koerper - und hat BEIDE Lesarten widerlegt.** Die Formachse zu erzwingen
  aendert nichts (obj_X 0 von 22 brauchbar gegen 0 von 18, p = 1,00; die Aufloesung steigt von 5,6
  auf 27,3 %, aber alle sechs Aufloesungen sind grobe Fehler). Die FARBACHSE zu streichen aendert
  alles: **0/18 -> 6/14 brauchbar, Median 141,3 -> 1,0 mm, grobe Fehler 1 -> 0** (p = 3,3e-3).
  **URSACHE:** `ACT23_FARB_MISCHUNG` (Vorgabe 1) faerbt JEDE Episode um -- eine eingefrorene
  Adresse mit `farbe-1` trifft nicht den Koerper, sondern was gerade diese Farbe traegt. Jede
  Aufloesung meldete "1 Treffer", also eindeutig, und lag 60-140 mm daneben ("eindeutig ist nicht
  richtig", zum wiederholten Mal). Der Docstring von `_farbe_wuerfeln` sagt es seit jeher, nur fuer
  den anderen Pfad: `_auto_eig_umschreiben` wuerfelt jede Episode neu und ist nie betroffen, eine
  Dauer-Adresse ist es immer. **Die Regel ist allgemeiner als der Schalter: eine dauerhafte Adresse
  darf nur Achsen nennen, die EIGENSCHAFTEN DES KOERPERS sind** -- in der gemischten Welt ist die
  Farbe ausdruecklich keine, sie wurde genau deshalb entkoppelt. Gebaut: keine Farbachse in einer
  Direkt-Adresse, solange FARB_MISCHUNG laeuft. Drei Alternativerklaerungen vorher geprueft und
  verworfen (Verformung geht nicht verloren; obj_X stand in 10 von 10 Rueckfaellen auf dem Tisch;
  eine getrennte Achsenmessung sagt sogar, **obj_X sei der LEICHTERE** Koerper -- genau dieser
  Widerspruch zwischen Pruefstand und Lauf war die Spur). Ausserdem repariert: `_adresse_wuerfeln`
  wuerfelt jetzt auch dann, wenn ein Startpunkt gesetzt ist -- sonst verbrauchte ein Arm drei
  Zufallszahlen weniger und die Arme divergierten ab Episode 8, obwohl der Schalter keine
  Entscheidung anders getroffen hatte (obj_X waere auf 569 gegen 924 px adressiert worden, der
  Vergleich haette die Szene gemessen statt die Achse). **Vorgabe bleibt 0.**
  Die Seite davor behaelt ihre Zahlen, bekommt aber einen Nachtrag und einen korrigierten Titel:
  [Aus einer Sichtung kommandierbar](/befunde/adresse-ohne-klasse-gemessen.md).

* **Anlage**: [Der Formvektor ist die gute Adresse](/befunde/adresse-ohne-klasse-gemessen.md) -
  drei frische Arme je 140 Episoden (kette / direkt / beides, alle mit NOVEL_WEITER=1, Seed 4242).
  **ZWEI Ergebnisse.** Erstens die Geschwindigkeit: der erste Koerper wird nach **7 statt 22
  Episoden** kommandierbar, ohne Geburt, Bestaetigung oder Knopf; in `beides` kommt die
  Direkt-Adresse der ersten Knopfvergabe um acht Episoden zuvor. Zweitens, und das ist das
  eigentliche Ergebnis, **die Aufloesung spaltet sich scharf nach der genannten Achse**: die reine
  Formvektor-Adresse `'~gesehen'` (EINE Achse, ohne Namen, nur der 8-dimensionale Vektor) loest in
  72,7 bzw. 76,5 % der Episoden auf, mit 5 mm Median, 100 % Eindeutigkeit und NULL groben Fehlern
  - die Adresse `'farbe-1 + dick'` aus Farbe und Groessenband in 5,6 bzw. 0,0 %, und ihr einziger
  Treffer lag 141 mm daneben. Zusammen 29/39 gegen 1/39, **p = 1,5e-11**. Die 72 % treffen die
  Offline-Vorhersage (72,2 %) auf den Punkt. **Zum ersten Mal spricht eine Messung FUER die stetige
  Adressierung statt nur nicht dagegen, und genau in der Richtung der Nutzeridee: das Gute ist der
  latente Vektor, das Schlechte sind die diskretisierten Achsen.** Lieferquote 10,0 / 5,0 / 9,3 %
  (p = 0,17 bzw. 1,00) - nicht das Kriterium, aber `beides` ist von `kette` nicht zu unterscheiden,
  die Direkt-Adressierung stoert den regulaeren Weg also nicht. **EHRLICHE GRENZE: ein Koerper je
  Adresstyp** (obj_T gegen obj_X) - ob die Formachse besser ist oder obj_T der leichtere Koerper,
  trennt die Messung NICHT; zwei unabhaengige Indizien stuetzen die Achsen-Lesart. Der billige
  naechste Schritt, der es entscheidet: die Formachse in jeder Direkt-Adresse erzwingen (bei obj_X
  war sie vorhanden -- `resolve()` gab `cube` -- die Wuerfelei hat sie nur nicht gezogen) und obj_X
  erneut messen. Ausserdem: reiner Formvektor heisst `servo=False`, weil kein Tracker einem Vektor
  folgen kann -- dass die Adresse trotzdem auf 5 mm trifft, macht eine Fovea auf dem
  Einbettungsvektor zu einem lohnenden eigenen Bau. **Vorgabe bleibt 0.**

* **Ergaenzung**: [Die Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md) - **der falsche
  Torwaechter, vom ersten Lauf entlarvt.** Meine erste Fassung benutzte `area_hi` als
  Verschmelzungssperre; der erste frische Lauf hat sie in der ALLERERSTEN Adresse widerlegt: der
  Fleck war im selben Blick von der Formstufe als `('verschmolzen', [-0.082, 0.087], 603)` gemeldet
  worden, die Direkt-Adressierung nahm ihn trotzdem, und die Adresse loeste danach in KEINER
  Episode mehr auf (5 von 5 privilegierter Rueckfall) - sie beschrieb einen Blob aus zwei Koerpern.
  **Der Grund stand seit dem 18.08. eine Datei weiter im Code:** *"Der vorhandene Flaechen-Schutz
  area_hi (1411) kann das prinzipiell nicht: die Verschmelzungen messen 822-1390, die groesste
  TRAININGSform ~940."* 603 px liegen weit darunter. Jetzt sperrt die FARBSTREUUNG (`_merge_th`,
  selbst gemessenes 0,995-Quantil), und solange die weniger als 12 Referenzwerte hat, wird gar
  nicht adressiert - die entfallende Bestaetigung WAR dieser Filter. Erste Adresse nach der
  Reparatur: `'~gesehen'` allein, also **nur der Formvektor**, ohne Farbe und Groesse (605px,
  Farbstreuung 0,097 < 0,111) - die reinste Fassung der Nutzeridee, zum Preis von `servo=False`,
  weil kein Tracker einem Vektor folgen kann. **Dazu eine getrennte Achsen-Messung** (40 echte
  Laufszenen, 90 Koerper-Szenenpaare, Pruefstand): chroma bricht 12,2 %, form 18,9 %, spanne 15,6 %
  der Faelle - **keine Achse ist der Ausreisser**, aber das UND kostet zusammen 28 Punkte, alle drei
  halten nur in 72,2 %. Eine eingefrorene Drei-Achsen-Adresse kann also halten, aber knapp; fuenf
  Rueckfaelle in Folge waren deshalb ein Signal und kein Rauschen. Drei frische Arme neu gestartet.

* **Anlage**: [Die Adresse ohne Klasse](/mechanismen/adresse-ohne-klasse.md) - `ACT23_EIG_DIREKT`
  gebaut, der Schritt, den der Befund davor als naechsten benannt hat. `_direkt_adressieren` sitzt
  als Gegenstueck zu `_try_bind` im selben Blick und macht einen Koerper OHNE Eintrag aus EINER
  Detektion adressierbar (Chromatizitaet, `desc_embed`, Spanne) - der Lebenszyklus faellt damit zum
  ersten Mal WEG statt ergaenzt zu werden. Drei Stellen mussten mit: der Platzhalter `~gesehen`
  (resolve() liefert fuer eine unbekannte Form keinen Namen -- genau daran ist der Weg diskret
  verschlossen; der Fovea-Tracker ueberspringt ihn ausdruecklich), `_probe_entdeckt()` (sonst haelt
  der Erzeuger den Koerper weiter fuer neu und gibt ihm einen zweiten Platz -- der Doppelplatz-Fehler
  vom 21.08.) und die Identitaetspruefung, die hier NICHT abschaltbar ist (eine Direkt-Adresse bleibt
  den ganzen Lauf stehen; geprueft wird gegen die Detektion, nicht gegen die wahre Lage, also ohne
  Privileg). Die Achsen-Wuerfelei steht jetzt als `_adresse_wuerfeln` fuer sich statt kopiert --
  dieselbe Logik lag schon einmal doppelt und die GUI-Kopie fehlte 332 Episoden unbemerkt.
  **GLEICHHEITSPROBE: der Vorgabepfad ist zeichengenau unveraendert** (2x12 Episoden, Seed 4242,
  HEAD gegen Arbeitsstand: 285 inhaltliche Zeilen, 0 Abweichungen; die 14 Rohunterschiede sind
  Pfadname und Wanduhr). **UND EIN BEFUND AUS DEM RAUCHTEST:** auf `ad9d768c` findet der Schalter
  NICHTS vor - alle sieben Koerper haben einen Eintrag (5 Basis-Knoepfe, obj_T und obj_X selbst
  erworben). Das ist die Saettigung in ihrer schaerfsten Form, kein Defekt; gemessen werden kann er
  nur frisch. Drei frische Arme je 140 Episoden laufen (kette / direkt / beides). **Vorgabe 0.**

* **Anlage**: [Die stetige Adressierung im Lauf](/befunde/stetige-adressierung-im-lauf.md) - der
  Einbau aus `ACT23_EIG_STETIG` zum ersten Mal in act23 gefahren, zwei Arme je 150 Episoden aus
  derselben Kopie von `ad9d768c`, sonst Vorgaben. **Nichts loest auf:** grobe Adressierungsfehler
  18/167 = 10,8 % gegen 14/164 = 8,5 % (p = 0,58), Quote 58,7 gegen 56,0 % (p = 0,73), Rueckfall
  7 gegen 10 (p = 0,62), Adress-Median 2,0 gegen 2,2 mm. **Das war die Vorhersage der Sonde** -
  bei `EIG_TOL_FORM=0,5` liegt die stetige Achse praktisch auf dem diskreten Bezug, und auch die
  Nebenrichtungen stimmen ueberein (Achsen je Adresse 1,81 -> 1,91, eindeutig 98,2 -> 99,4 %: die
  stetige Achse trennt minimal weniger, also legt die Wuerfelei haeufiger nach). **Zweck des Laufs
  war die Verifikation des Baus gegen seine Nachbildung, und die ist bestanden**; dazu reproduziert
  `st_aus` den bekannten Vorgabe-Bezug zifferngenau (58,7 %, 18/167, 7 Rueckfall - zum sechsten
  Mal). **Der Baustein ist bestaetigt, die These ist es nicht:** der Einbau ist additiv, die
  Formklassen entstehen weiter, bekommen weiter Knoepfe und verhungern weiter - der erhoffte Gewinn
  soll aber gerade aus dem Wegfall dieses Lebenszyklus kommen. Naechster pruefbarer Schritt waere,
  die Auto-Schleife eine Adresse fuer einen Koerper OHNE Klasse anlegen zu lassen; das ist stetig
  moeglich und diskret nicht. Offen bleiben eine Toleranz (nur 0,5 gefahren) und der GUI-Pfad
  (`_eig_setzen` schreibt kein `EIG_MESS`, faellt auf Namensvergleich zurueck). **Vorgabe bleibt 0.**

* **Anlage**: [Die stetige Formachse ist genauso trennscharf](/befunde/stetige-adressierung-erster-schritt.md)
  - der erste Schritt zur stetigen Adressierung, gemacht mit der Adress-Wiedervorlage: dieselben
  echten Laufszenen, dieselbe Wuerfelei, dieselbe Aufloesung, **nur die Matching-Regel getauscht**
  (Klassenname gegen Abstand im Einbettungsraum). Zwei der drei Toleranzen sind nicht geraten -
  die Farbschwelle ist `colour_openset.TH`, die Formtoleranz RELATIV zum je Lauf gemessenen
  Median-Abstand zweier verschiedener Koerper (1,858). **Ueber fuenf Toleranzen bleiben die groben
  Adressierungsfehler flach** (4,9 | 5,3 | 5,6 | 4,9 | 5,5 | 6,7 %), keine vom Bezug zu
  unterscheiden (p = 0,25 bis 1,00), bei `t0.50` sogar identisch (28 von 568 in beiden). **Der
  Einwand, ein Vektor sei nicht trennscharf genug, ist damit ausgeraeumt.** Was sich mit der
  Toleranz aendert, ist allein der **Rueckfall**: 60,2 % streng, 27,3 % diskret, 16,2 % locker -
  und die Achsenzahl daneben erklaert es (1,81 -> 1,89 -> 2,06): eine lockere Formachse trennt
  weniger, also legt die Wuerfelei mehr Achsen nach. `t1.00` ist nicht bessere Formerkennung,
  sondern fast "Form egal", kompensiert durch Farbe und Groesse. **Die stetige Achse ist also nicht
  besser, sondern ein anderer Punkt auf derselben Tauschkurve** - `t0.75` kauft 6,7 Punkte weniger
  Rueckfall mit 0,6 Punkten mehr groben Fehlern. **Fuer die Frage heisst das: der Weg ist frei, der
  Gewinn nicht belegt** - er muesste aus dem Wegfall des Klassen-Lebenszyklus kommen (Geburt,
  Bestaetigung, Knopf, Verhungern, Saettigung), und den misst die Adressierung per Konstruktion
  nicht. Werkzeug erweitert (`AW_VARIANTEN` kennt jetzt probe-lokale Schluessel STETIG/EMB_TOL/
  SPAN_TOL, die NICHT an pc_act23 durchgereicht werden).

* **Anlage**: [Stetig adressieren statt Klassen vergeben](/fragen/stetige-adressierung.md) - aus
  einer Nutzerfrage nach der urspruenglichen Vorstellung ("dem Netz ein Bild zeigen, die
  Repraesentation abgreifen, damit kommunizieren -- die Sprache des Netzes lernen, ohne ein
  Language-Model zu trainieren"). **Die Haelfte davon ist gebaut:** `desc_embed` liefert genau
  diesen Vektor, existiert fuer JEDES Objekt auch ohne Klassenslot, verschiebt sich mit dem
  Lernen mit, und das Weltmodell konditioniert bereits darauf. **Die andere Haelfte fehlt:** das
  Kommando vergleicht `str(det.get("shape")) != str(form)`, also Klassen-NAMEN aus `resolve(desc)`.
  Erst dieses Etikett hat einen Lebenszyklus - Geburt, Bestaetigung, Knopf, Verhungern; der Vektor
  hat davon nichts. **Und es gilt fuer alle drei Achsen** (Farbe ueber `colours.classify`, Form
  ueber `resolve`, Groesse ueber `groessen_band`). Damit erklaert sich rueckblickend ein ganzer
  Arbeitstag: Bandgrenzen und das oberste Band im 7-mm-Raster, verschmelzungsgeborene Farbklassen
  (`farbe-50`), die ganze Kette aus Vergabe-Engstelle und 29-Episoden-Saettigung - **durchweg
  Diskretisierungsartefakte, keine Wahrnehmungsfehler.** Die Frage ist, ob das Kommando direkt auf
  den stetigen Groessen arbeiten kann (Zielpunkt plus Toleranz statt Tripel aus Namen; bedient per
  "zeig auf das Objekt, nimm den Vektor"). Dann waeren Geburt, Knopfvergabe, Verhungerungsschutz,
  `NOVEL_BODY` und die Saettigung bei sieben Koerpern gegenstandslos. **Dagegen spricht nicht
  wenig:** eine Klasse entscheidet, wann zwei Dinge DASSELBE sind - beim Vektor wird daraus eine
  Schwelle, und Schwellen haben an dieser Stelle schon dreimal eigene Fehler produziert; dazu die
  Verrechnung dreier verschiedener Masse zu einer Entfernung und der gemessene Rauschboden des
  Deskriptors (13-16 % der Klassentrennung schon bei 2 mm). **Billigster erster Schritt, ohne
  Lauf:** die Adress-Wiedervorlage kann beide Adressierungen auf denselben echten Laufszenen
  gegeneinanderstellen. Idee, nichts gebaut, nichts gemessen.

* **Anlage**: [Die Aneignungskette traegt 29 Episoden](/befunde/kette-haelt-30-episoden.md) - der
  Langlauf zur Kette (400 frische Episoden, Erzeuger + freie Vergabe). **Alles Wesentliche passiert
  bis Episode 29:** drei Knoepfe (Ep 21, 26, 29), dazwischen bei Ep 23 die Meldung
  `Probe-Rolle weitergereicht: obj_T ist entdeckt -> obj_X (noch offen: keiner)`. **Danach 371
  Episoden ohne einen weiteren Knopf.** Fuenf Geburten nach der Saettigung (neu-5 bis neu-8), alle
  mit derselben Begruendung verhungert - *"nie stabil wiedererkannt"*, nach 24 bis 27 Episoden;
  freie Koerper gaebe es (obj_red, obj_green, obj_L, obj_U tragen keine Formklasse), aber keine
  Klasse bestaetigt sich dreimal auf demselben. **Eine der drei GEBUNDENEN Klassen stirbt:** neu-4
  auf obj_X nach 145 Episoden - ausgerechnet die, wegen der die Kette gebaut wurde. Der Koerper
  bleibt trotzdem adressierbar (Bloecke nach dem Tod: 10 und 18 Adressierungen), weil der Eintrag
  in `state.OBJECTS` das Sterben der Klasse ueberlebt und Farbe/Groesse weiter greifen - **verloren
  ist der selbst gegebene Name, nicht der Zugriff.** Quote je 100 Ep: 3/17/16/16 %, also Hochlauf
  und dann flach wie im 1109-Episoden-Langlauf. **Der Engpass ist damit nicht mehr die Maschinerie,
  sondern die Welt:** sieben Koerper sind die Obergrenze der Aneignung, erreicht in 29 Episoden;
  alles danach ist Churn. Das ist die schaerfste Fassung von *"laenger laufen lassen bringt
  nichts"* - jetzt mit einem Grund statt einer Beobachtung. **Naechster Schritt ist kein Schalter,
  sondern eine Quelle neuer Geometrie.** Beide Schalter bleiben auf 0.

## 2026-09-15

* **Anlage**: [Der Erzeuger reicht die Probe-Rolle weiter](/befunde/erzeuger-repariert.md) -
  `ACT23_NOVEL_WEITER` gebaut (Vorgabe 0) und zusammen mit der freien Vergabe gemessen.
  `spawn_novel_shape` hatte einen Riegel mit echtem Grund (nach der Entdeckung verwaltet
  `randomize_objects` den Koerper, zusaetzliches Hinstellen fuellte die Szene ueber SCENE_N) - mit
  der Folge, dass es NIE eine zweite neue Form gab. Die Reparatur ist klein, weil der schwierige
  Teil schon dastand: die else-Verzweigung behandelt einen Probe-Koerper ungleich obj_T bereits
  richtig, es fehlte nur die Weitergabe der Rolle. **Und genau der Erzeuger musste es sein** - er
  ist der einzige Pfad, der einen Koerper OHNE Knopf in die Szene stellt (das dritte Rad aus dem
  vorigen Befund).
  **Ergebnis, zwei frische Arme je 140 Episoden:** Knoepfe 1 gegen **3**, adressierte Koerper 6
  gegen **7**. `[Neuheit] Probe-Rolle weitergereicht: obj_T ist entdeckt -> obj_X`, und
  `'neu-4' -> 'Neue Form 5' auf obj_X`. **obj_X wird zum ersten Mal in die Szene gestellt, selbst
  benannt, kommandierbar und 17-mal adressiert** - kein einmaliger Treffer, sondern ein regulaerer
  Teilnehmer. Geburten 4 zu 4: **der Gewinn sind nicht mehr Geburten, sondern dass eine Geburt den
  Knopf erreicht.**
  **Die verhungerte Klasse stirbt erstmals aus dem richtigen Grund:** `neu-2: verhungert nach 27 Ep
  (nie stabil wiedererkannt)`. Die Null im Vorgabearm ist kein gutes Zeichen - dort wird nach dem
  ersten Knopf niemand mehr Kandidat, also kann auch niemand als Kandidat sterben; die
  13-von-13-Meldung aus dem Langlauf war Buchhaltung, keine Auslese. Zum ersten Mal wird der
  Verhungerungsschutz an der Sache gemessen statt an einer Engstelle davor.
  **Ehrliche Grenze, in der Meldung selbst:** "noch offen: keiner" - nach obj_X ist der Vorrat
  leer, die Welt hat sieben Koerper. Der Erzeuger verteilt Rollen, er erfindet keine Objekte.
  Nebenbei nachgemessen: nur die drei Wuerfel sind einzeln-geometrisch; `obj_T` hat zwei Geoms,
  `obj_U` drei - die Verformung trifft also stets nur das erste, was der Kommentar am Erzeuger
  bisher nur fuer obj_X nennt. Quote 7,1 gegen 5,7 % = 10 gegen 8 Lieferungen, sagt nichts.
  **Drei Schalter, eine Kette:** Erzeuger bringt in die Szene, freie Vergabe gibt den Knopf, der
  Verhungerungsschutz entscheidet ueber Leben. Einzeln bewegt keiner etwas.

* **Anlage / Korrektur**: [Die freie Vergabe oeffnet die erste Tuer](/befunde/freie-vergabe-erste-tuer.md)
  - `ACT23_FREIE_VERGABE` gebaut (Vorgabe 0) und gemessen. Der Eingriff ist absichtlich KEIN neuer
  Mechanismus: die Bestaetigungsschranke bleibt, entfernt ist nur die Festverdrahtung auf
  `NOVEL_BODY` - bestaetigt wird gegen den Koerper, auf dem die Klasse sitzt.
  **Der Riegel ist auf:** 2 vergebene Knoepfe gegen 1 (`neu-1` auf obj_T, `neu-3` auf obj_blue mit
  3 von 3 Blicken), zum ersten Mal einer auf einem anderen als dem Probe-Koerper.
  **Das Repertoire wird trotzdem nicht breiter:** der zweite Knopf ging an obj_blue, der ohnehin in
  `state.OBJECTS` steht; die adressierten Koerper sind in beiden Armen dieselben sechs.
  **Zwei weitere Tueren wurden dabei sichtbar.** (a) Drei Kandidaten verhungern vor der
  Bestaetigung (Vorgabearm: 0 - dort wird nach dem ersten Knopf niemand mehr Kandidat, also kann
  auch niemand verhungern). (b) **Korrektur an meiner eigenen Diagnose:** ich hatte geschrieben,
  obj_X werde nie adressiert, "obwohl er die ganze Zeit sichtbar auf dem Tisch liegt" - **im
  frischen Lauf steht er gar nicht in der Szene** (die `after ep`-Zeile fuehrt nur fuenf Koerper,
  obj_X kommt 0 mal im Protokoll vor). Er erscheint nur in Laeufen aus dem gespeicherten Zustand,
  weil `_try_bind` bei der Vergabe den Koerper in `act16.OBJS` eintraegt. Damit schliesst sich ein
  drittes Rad: **ein Koerper braucht die Szene fuer den Knopf und den Knopf fuer die Szene**, und
  als neues Objekt eingefuehrt wird nur der eine Probe-Koerper.
  **Die Reihenfolge ist damit klar:** erst muss die Welt etwas Neues anbieten (`spawn_novel_shape`,
  der tote Erzeuger), dann muss eine junge Klasse lange genug leben (Verhungerungsschutz), und erst
  dann traegt die freie Vergabe. Ich hatte die drei fuer EIN Problem gehalten.
  Eigener Fehler unterwegs: der erste Anlauf stuerzte ab, weil die Mitbewerber-Zeile weiter
  `sum(h)` rechnete, waehrend `hits` jetzt Koerpernamen traegt - behoben durch eine gemeinsame
  Zaehlhilfe `_zaehl` fuer beide Modi. Der Absturz kam ausgerechnet im Moment der zweiten Vergabe.

* **Anlage**: [Die Vergabe-Engstelle, diagnostiziert](/befunde/vergabe-engstelle-diagnose.md) -
  Nutzerauftrag "erst diagnostizieren, nicht bauen". **Die Engstelle liegt eine Ebene tiefer als
  der Langlauf-Befund sagt.** Der Knopf ist fest an `NOVEL_BODY` verdrahtet; ist er vergeben, kehrt
  `_register_open_class` zurueck, BEVOR die Klasse Kandidatin wird (`_bind_hits` bleibt leer), also
  kann `_try_bind` sie nie binden - **genau EINE selbst geborene Klasse je Zustand kann
  kommandierbar werden.** Entscheidend ist aber: **das Eigenschafts-Kommando umgeht das nicht**,
  obwohl es genau dafuer gebaut wurde. Seine drei Aufrufer sind eine Startvariable, die GUI-Felder
  (brauchen einen Menschen) und `_auto_eig_umschreiben`, das nur den BEREITS gewaehlten Koerper
  umetikettiert (`_b = state.selected()[1]`); und `curious_pick` zieht ausschliesslich aus
  `state.OBJECTS`. **Im autonomen Lauf gibt es keinen Pfad, der die Objektliste erweitert** - das
  Werkzeug gegen die Geburt ist nur fuer Objekte benutzbar, die die Geburt hinter sich haben.
  Bezeichnend: `_eig_setzen` (GUI) sucht seinen Koerper aus
  `OBJECTS + SHAPE_KEY + [NOVEL_BODY]` und KANN einen neuen einfuehren - der Mensch kann es, die
  Schleife nicht. Dasselbe Muster wie der zweimal dokumentierte Riss zwischen den zwei
  Auto-Schleifen. **Empirisch bestaetigt** an zwei frischen 300-Episoden-Laeufen: 12 bzw. 4
  Geburten, je **genau 1 vergebener Knopf**, und die adressierten Koerper sind in beiden Laeufen
  dieselben sechs (die fuenf Anfangseintraege plus obj_T, der den einen Knopf bekam) - **obj_X wird
  in 300 Episoden kein einziges Mal adressiert**, obwohl er die ganze Zeit sichtbar auf dem Tisch
  liegt. **Reparaturrichtung:** nicht mehr Probe-Koerper, sondern die Auto-Schleife muss eine
  Eigenschafts-Adresse fuer einen noch nicht gelisteten Koerper anlegen koennen - genau das, was
  `_eig_setzen` fuer den Menschen tut. Offen: ob eine so eingefuehrte Klasse dann auch ueberlebt
  (der Verhungerungsschutz zaehlt ueber Eigenschaften kommandierte als ungeschuetzt) - die
  Engstelle koennte zwei Tueren haben.

* **Anlage**: [fail_w kalibriert](/befunde/fail-w-kalibriert.md) - die Hoehe der `fail_w`-Daempfung,
  nie kalibriert, jetzt gemessen: 6 Werte x 2 Luecken x 5 Seeds, gepaart. **Unerwartetes zuerst:
  alle 946 gedaempften Zeilen sind Fehlschlaege** (davon positiv: 0) - bauartbedingt, weil die
  Route nur `outcome=False` vergibt, aber nirgends notiert. fail_w zu senken heisst also, unsichere
  NEGATIVE leiser zu stellen. **Bei Luecke 1500 monoton fallend, ohne Optimum in der Mitte:**
  0,0 +0,0079 (5/5), 0,1 +0,0031 (5/5), 0,5 -0,0031, 1,0 -0,0092 (je 0/5). Deutung: die unsicher
  zugeordneten Fehlschlaege sind verrauschte Etiketten, weniger ist besser. **Bei Luecke 4000
  flach** - ganze Spanne 0,0016, Vorzeichen Muenzwuerfe. **Der beste Wert darf nicht eingestellt
  werden:** `att_ok = att_full or fail_w > 0.0`, mit 0 wird die Route GANZ abgeschaltet, und der
  Kommentar dort sagt, wogegen sie gebaut wurde - *"a grasp-PREVENTING wrist was unfalsifiable ...
  the world model froze on it (L-Form wrist-112 deadlock)"*. **Die Route existiert gegen eine
  gemessene Blockade, nicht fuer die AUC**, und diese Messung kann die Blockade nicht sehen. Ein
  Optimum am Rand ist hier also kein Einstellwert, sondern eine Warnung, dass die Kennzahl nicht
  misst, wofuer die Sache gebaut wurde. **Empfehlung 0,1 statt 0,3**, falls ueberhaupt - es behaelt
  die Route und die Falsifizierbarkeit; nicht ohne einen Lauf aendern, der auf die Blockade schaut.
  **Bilanz der vier Gewichtungsfragen:** jeder Gewinn ist Nahfeld (Stufe nah +0,0156 / fern -0,0070,
  Verlauf +0,0089 / -0,0049, gespeicherte Daempfung +0,0108 / +0,0013, fail_w 0,3->0,0 +0,0079 /
  +0,0007). Keine Gewichtung verbessert die Verallgemeinerung; die inhaltlichen schaden fern
  wenigstens nicht, die positionsbasierten schon.

* **Anlage**: [Kein Gewichtungsverlauf hilft bei beiden Luecken](/befunde/sanfter-abfall.md) - die
  offene Frage des Vorbefundes, beantwortet mit **nein**. Vier Abklingzeiten
  (`0,1 + 0,9*exp(-Alter/tau)`), dazu die harte Stufe und eine Umkehrung, gegen Luecke 1500 UND
  4000, je 5 Seeds gepaart. **Jedes Schema, das nah hilft, schadet fern** (Stufe +0,0156 / -0,0070,
  tau=1000 +0,0089 / -0,0049, tau=2500 +0,0056 / -0,0042); je flacher, desto mehr verschwindet
  beides. Nicht die Stufe war das Problem, sondern die Positionsgewichtung selbst. **Damit ist der
  Faden zu.**
  **Der Ertrag steckt in der Nullkontrolle, und sie war nicht null:** `tau=20000` ist bei 10322
  Zeilen praktisch flach und kostet trotzdem -0,0108 (0/5). Grund ist ein Fehler in meinem Aufbau -
  der Bezug benutzt die GESPEICHERTEN Gewichte, und die sind nicht gleichfoermig (946 Zeilen auf
  0,3, das ist die `fail_w`-Daempfung unsicher zugeordneter Ausgaenge, 9,2 % des Trainingsteils).
  Ein flaches Schema ersetzt sie durch gleichfoermige, gemessen wird also "gespeichert gegen
  gleichfoermig" - und **die vorhandene Daempfung ist +0,0108 AUC wert**, erstmals beziffert, als
  Nebenprodukt einer Kontrolle fuer etwas anderes. Folge: alle Deltas dieser Reihe enthalten zwei
  Anteile (eigene Wirkung + Verlust der gespeicherten Gewichte); gegen gleichfoermig gerechnet
  stuenden die nahen Werte besser da, an der Kernaussage aendert das nichts, weil bei Luecke 4000
  auch dann alles unter null bleibt. Auch die gespeicherte Daempfung selbst ist ueberwiegend
  Nahfeld (+0,0108 nah, +0,0013 fern).
  **Die Gegenprobe ist nur eine halbe Spiegelung:** die Umkehrung (altes Ende schwer) schadet nah
  wie vorhergesagt und am staerksten von allen (-0,0221), nuetzt fern aber NICHT (-0,0031). Bei
  Luecke 4000 schadet jede Abweichung leicht. Die Naehe-Deutung erklaert die nahe Seite gut und die
  ferne gar nicht - so hingeschrieben, statt die halbe Spiegelung als ganze auszugeben.
  **Neuer Faden:** die Hoehe der `fail_w`-Daempfung (0,3) ist nie kalibriert worden.

* **Anlage**: [Alte Pufferzeilen abwerten](/befunde/alte-zeilen-abwerten.md) - der einzige Faden aus
  dem Gewichtungsbefund, gezogen mit 6 Seeds und vier Schnitten. **Mit Luecke 1500 sah es
  ueberzeugend aus:** alte Zeilen auf Gewicht 0,1, gepaart +0,0075 (ab 1000) und **+0,0115 (ab
  2000), bei 6 von 6 Seeds**, mit sauberer Dosis-Wirkungs-Kurve - Anstieg, Maximum bei 2000,
  Rueckkehr zur Null bei 8000, wobei `ab 8000` die eingebaute Kontrolle ist. Dazu: **Loeschen
  ruiniert** (-0,04 bis -0,05, 0/6), die alten Zeilen tragen also echte Information und sind nur
  ueberrepraesentiert. **Mit Luecke 4000 kehrt sich dasselbe Schema um:** -0,0054 und -0,0094, 0 von
  4 Seeds. Der Grund steht im Docstring von `generalisation_auc` selbst - die "juengsten"
  Trainingszeilen sind zugleich die dem Halteteil NAECHSTEN. **Alte Zeilen abzuwerten kauft NAEHE
  und kostet VERALLGEMEINERUNG**; es ist keine Aussage ueber das Alter der Daten. Fuer den Betrieb
  bleibt ein Rest (zur Laufzeit sagt das Modell immer *jetzt* vorher), aber das ist lokale
  Anpassung, nicht Lernen. **Die Lehre, verallgemeinert:** der Luecken-Parameter schuetzt nur, wenn
  man ihn VARIIERT - bei einer festen Luecke ist ein Schema, das die Naehe betont, nicht von einem
  zu unterscheiden, das die Verallgemeinerung verbessert. *Ein Schema, das Trainingszeilen nach
  ihrer POSITION im Puffer gewichtet, muss immer gegen mindestens zwei Luecken geprueft werden.*
  Ohne diese Kontrolle haette ich den Gewinn aufgeschrieben.

* **Anlage / Widerlegung**: [Keine Hoehergewichtung bringt etwas](/befunde/gewichtung-bringt-nichts.md)
  - der Schlusssatz des Augmentierungs-Befundes ("billiger ueber `weight`") geprueft, fuenf
  Schemata gegen den Bezug, je 3 Seeds, gleicher reiner Halteteil. **Keines hilft:** bestes
  `juengste 2000 nur` +0,0043 (n=2) bei einer Bezugs-Streuung von 0,007, `neuere schwerer` +0,0012,
  `NB-Zeilen 5x` -0,0031, `Fehlschlaege 3x` -0,0103, `Erfolge 3x` -0,0137. **Die Kontrolle hat
  getragen:** beide Klassenrichtungen schaden etwa gleich viel - gemessen wird also nicht "die
  falsifizierende Klasse zaehlt mehr", sondern nur, dass eine Stoerung des Klassenverhaeltnisses
  schadet. Nebenbei korrigiert: der Puffer ist mit 5690 Erfolgen gegen 4632 Fehlschlaege weit
  ausgewogener als das 1053-Ep-Protokoll vermuten liess (550 gegen 288) - es gibt kein
  Klassenungleichgewicht zu reparieren.
  **Die wichtigste Zahl ist eine Gegenprobe, und sie widerlegt mich:** dieselbe Fuenffachgewichtung
  der 690 augmentierbaren Zeilen kostet als DUPLIKAT -0,051, ueber `weight` aber nur **-0,003**.
  Meine Deutung des Augmentierungs-Verlusts als "Umgewichtung" ist damit falsch und auf der
  [Vorseite](/befunde/augmentierung-wirkt-wie-wiederholung.md) als widerlegt gekennzeichnet; ihr
  KERNBEFUND (vorgestellt = wiederholt, +0,0006) bleibt, weil er ein direkter Vergleich ist und an
  keiner Deutung haengt. **Was die -0,051 verursacht, ist offen** - Duplikat und Gewicht sind hier
  nicht dasselbe (Zeilenzahl, Bootstrap-Zug und Stichprobenzahl je Epoche gegen blossen
  Verlustbeitrag), und welcher Unterschied die Zahl traegt, ist ungemessen. Als offene Frage
  hingeschrieben, nicht als zweite Erklaerung.
  Methodisch: zwei Durchgaenge wurden wegen Systemspeicher abgeraeumt. Der erste hinterliess
  NICHTS, weil er erst am Ende druckte; danach auf laufende Ausgabe und eine einzige wiederverwendete
  Modellkopie umgebaut - der zweite Abbruch kostete dadurch nur den letzten Fit.

## 2026-09-14

* **Anlage / ehrliches Negativ**: [Die Augmentierung wirkt wie eine Zeilenwiederholung](/befunde/augmentierung-wirkt-wie-wiederholung.md)
  - statt des bestellten A/B-Laufs offline geprueft, weil die Augmentierung eine reine Funktion
  einer Pufferzeile ist: Minuten statt Stunden, und schaerfer, weil beide Seiten denselben Puffer
  sehen. Halteteil von Hand gebaut (nur echte Zeilen), weil `generalisation_auc` die LETZTEN Zeilen
  testet und eine Vorstellung dort ihr Original im Training haette. **Ergebnis: eine vorgestellte
  Zeile ist von einer exakten Kopie nicht zu unterscheiden.** Voller Puffer: vorgestellt -0,0502,
  wiederholt -0,0513 (Differenz **+0,0011**). Im Regime, fuer das gebaut wurde (nur die 690 Zeilen
  mit gueltigem NB-Block): vorgestellt +0,0154, wiederholt +0,0148 (Differenz **+0,0006**). Das
  erklaert auch das Vorzeichen: im vollen Puffer sind nur 6,7 % augmentierbar und zaehlen danach
  fuenffach - der Verlust ist **Umgewichtung**, kein Fehler der Vorstellung. **Zwei eigene
  Erklaerungen dafuer sind gemessen falsch:** (1) "das Modell ignoriert die Lage" - nein, sie ist
  der zweitwichtigste Block (+0,1458 AUC-Verlust beim Vertauschen, nach der Aktion mit +0,1920);
  (2) "es nutzt sie nur grob" - nein, schon 5 mm Verschiebung des Halteteils kosten +0,0226, 20 mm
  kosten +0,0731. Es bleibt ein Befund ohne bequeme Erklaerung: das Modell behandelt 20 mm als
  deutlich andere Situation und reagiert trotzdem nicht darauf, ob man ihm diese Situation zeigt
  oder die alte wiederholt. **Nebenbefund, dritte unabhaengige Bestaetigung:** der Nachbar-Block
  kostet beim Vertauschen **+0,0000** - das Weltmodell benutzt ihn nicht, und ausgerechnet ihn
  braucht die Augmentierung als Zulaessigkeitsschranke. **Kein A/B-Lauf:** +0,0006 ist bei 150-300
  Episoden nicht aufzuloesen, ein Lauf waere genau das Muster, an dem diese Sitzung schon sieben
  Vergleiche verloren hat. `ACT23_AUGMENT` bleibt auf 0; der Bau bleibt im Code, weil er korrekt
  und unschaedlich ist. Billiger zu haben waere dieselbe Wirkung ueber `weight` bei `observe` --
  eine Zahl statt eines Mechanismus.

* **Anlage**: [Die latente Augmentierung, gebaut](/mechanismen/latente-augmentierung-gebaut.md) -
  `ACT23_AUGMENT` (Vorgabe 0) erzeugt aus einer bestaetigten Erfahrung N vorgestellte Lagen. **Jede
  Regel kommt aus der Daempfungsmessung, keine aus der Annahme:** keine Daempfung nach dem Betrag
  (alle Vorstellungen `weight=1.0`), Schranke ist `delta < d_nah - 40 mm` gedeckelt bei 20 mm, nur
  Verschiebung. **Die Schranke liest, was der Agent ohnehin gesehen hat** - der Nachbarabstand steht
  im NB-Block des Merkmalsvektors, kein zusaetzliches Rendern, keine privilegierte Information.
  Der neue Abstand wird konservativ gesetzt (`d_nah - |delta|`), weil die Richtung zum Nachbarn nur
  mod pi bekannt ist. **Dieselbe Gruppe wie das Original** - sonst landete eine Vorstellung im
  Halteteil, waehrend ihr Original trainiert, und die Guete waere Selbstbetrug. Fehlschlaege werden
  mitaugmentiert, und die Forderung der Idee-Seite ("ein Negativ nur so weit, wie seine Ursache
  erklaert ist") ist dabei schon erfuellt: die Kredit-Zuordnung laesst nur ursaechlich zugeordnete
  Ausgaenge durch, "daneben platziert" kommt als `outcome=None` gar nicht an.
  **Der erste Rauchtest hat den entscheidenden Fehler gefunden:** `ACT23_NEIGHBOURS` steht per
  Vorgabe auf 0, der NB-Block wird dann nie gefuellt (11640 von 12330 Pufferzeilen ohne gueltigen
  Block) - die Schranke oeffnet nie, 8 Episoden ergaben 8 Zeilen und 0 Vorstellungen. **Ein A/B
  haette zwei Stunden gekostet und exakt nichts gemessen.** Der Schalter warnt jetzt laut beim
  Start; bewusst NICHT still mitgeschaltet, weil ein Schalter, der einen zweiten heimlich umlegt,
  jedes A/B mehrdeutig macht. Beide Arme brauchen `ACT23_NEIGHBOURS=1`.
  **Zweiter Rauchtest bestanden:** 8 Episoden -> Weltzeilen 12322 -> 12353, also **+31 statt +7**,
  rund **4,4 Pufferzeilen je physischer Episode**. Im Puffer geprueft: |delta| 10,9-17,9 mm, d_nah
  nie unter 40 mm, Label und alle uebrigen 43 Spalten identisch, Gewicht 1,0.
  **Was NICHT gezeigt ist:** dass ein Griff an der vorgestellten Lage geglueckt WAERE - die
  Daempfungsmessung zeigt nur, dass die WAHRNEHMUNG der Vorhersage entspricht. Die sinnvolle
  Zielgroesse eines A/B ist die Generalisierungs-AUC, nicht die Lieferquote.

* **Ergaenzung**: [Die Daempfungsfunktion](/befunde/daempfungsfunktion.md) um die **Drehung**
  erweitert (`DF_MODUS=dreh`), die auf der Idee-Seite als eigene Messung angekuendigt war.
  **Der praktisch wichtigste Fund ist ein Vorzeichen:** `yaw4` traegt die Drehung sauber (2 bis
  5 Grad Rest ueber alle Koerper), aber **mit UMGEKEHRTEM Vorzeichen** - eine Spiegelung im
  Kamera-/Homographie-Pfad. Die Vorzeichenprobe zeigt es eindeutig: mit `+theta` ist der Rest genau
  `2*theta` (10,0 / 19,2 / 38,1 Grad bei 5 / 10 / 20 Grad), mit `-theta` sind es 1,9 / 2,3 /
  3,3 Grad. **Wer das Vorzeichen raet, faelscht jede vorgestellte Drehung um den doppelten
  Winkel** - und das ist mir beim Bauen der Sonde selbst passiert, weshalb sie jetzt beide
  Konventionen prueft statt eine anzunehmen. **`yaw` (k=2) ist unbrauchbar:** auf den drei Wuerfeln
  ist der Rest gleich theta (die k=2-Phase ist auf einem Quadrat entartet), auf den laenglichen
  Koerpern noch die Haelfte des Winkels. Zwei weitere Vorhersagen fallen: **die Lage ist NICHT
  invariant** (der wahrgenommene Schwerpunkt wandert bei asymmetrischen Koerpern bis 2,5 mm bei
  20 Grad, bei Wuerfeln 0,3 mm), und **der "drehinvariante" Deskriptor ist es nicht** (21 bis 35 %
  der Klassentrennung bei 20 Grad gegen einen Rauschboden von 13 bis 16 %). **Verschiebung und
  Drehung sind wirklich nicht symmetrisch - aber anders als vermutet:** die Idee-Seite gab als
  Grund an, dass der Deskriptor die Phase wegwirft; gemessen ist der Grund, dass die Drehung
  schlicht TEURER ist - 20 Grad kosten so viel Formdrift wie 40 mm Verschiebung. Fuer den Bau:
  Drehungen nur ueber `yaw4` und mit umgekehrtem Vorzeichen, `yaw` herauslassen, den Greifbezug
  mitdrehen, Winkelbereich klein halten.

* **Anlage**: [Die Daempfungsfunktion](/befunde/daempfungsfunktion.md) +
  `src/pc_cvnn/act23_daempfung.py` - die Voraussetzungsmessung der [latenten
  Augmentierung](/fragen/latente-augmentierung.md), seit dem 31.08. offen, jetzt gemacht: 80 echte
  Laufszenen, rund 2400 gepruefte Verschiebungen. **Das Ergebnis kehrt die Annahme um.** Frei
  stehend (Nachbar > 90 mm) ist die Aequivarianz praktisch exakt - 0,33 mm Restfehler bei 40 mm
  Verschiebung, p90 0,76 mm, also **unter einem Prozent von delta**. Eine Daempfung nach dem BETRAG,
  die Intuition hinter "mit abnehmender Intensitaet", waere dort fast ueberfluessig. **In
  Nachbarnaehe bricht nicht der Median, sondern der Schwanz:** der Median bleibt bei 0,52 mm, der
  p90 springt auf 17 mm - keine sanfte Verschlechterung, sondern eine Minderheit vollstaendig
  falscher Vorstellungen. Einwand 1 der Seite ist damit bestaetigt UND verschaerft: der Kontext ist
  nicht *auch* eine Achse, er ist die **einzige**. **Und die Schwelle ist eine bekannte:** es bricht
  genau dort, wo die Verschiebung den Koerper in Verschmelzungsnaehe traegt (>90 mm: bis 40 mm
  sauber | 60-90 mm: bricht bei 30 | <60 mm: bricht bei 10). Brauchbare Regel:
  **`delta < Nachbarabstand - 40 mm`** - die Daempfungsfunktion IST die Verschmelzungsschwelle, in
  delta ausgedrueckt, und damit je Stichprobe aus der Szene selbst berechenbar statt zu schaetzen.
  **Zwei Nebenbefunde fuer den Bau:** (a) die Formeinbettung hat einen **Rauschboden** - schon bei
  2 mm driftet sie um 13-16 % der Klassentrennung und steigt bis 40 mm nur auf 23-27 %; die
  Formkanaele unveraendert zu uebernehmen ist also so genau, wie der Deskriptor ueberhaupt ist.
  (b) **Das Ziel-Latent ist NICHT exakt linear**, sondern auf 12-14 % genau, konstant relativ -
  das **korrigiert die Idee-Seite**, die "EXAKT eine Phasendrehung, per Konstruktion" sagt: das gilt
  fuer den RoPE-Code, aber `encode_world` ist eine Gitter-Interpolation ueber das trainierte
  Zielmodul. Bei 5 mm sind das 0,6 mm und belanglos, bei 40 mm 5,5 mm und damit mehr als die
  Greiftoleranz. Die Drehung ist NICHT mitgemessen und bleibt eine eigene Messung.
  `ebene: pruefstand`: gemessen ist die Wahrnehmung einer verschobenen Szene, nicht der Ausgang
  eines Griffs - und genau das ist die Behauptung, auf der die Augmentierung beruht.

* **Anlage**: [Spanne und Identitaetspruefung im Adress-Nachspiel](/befunde/spanne-ident-wiedervorlage.md)
  + `src/pc_cvnn/act23_adress_wiedervorlage.py`. Nutzerauftrag war, die beiden Schalter mit der
  Wiedervorlage zu pruefen - **die kann das nicht:** sie misst die WAHRNEHMUNG und laedt
  `shape_classifier` neu, waehrend beide Schalter in `pc_act23` sitzen und `perceive_all` gar nicht
  beruehren. Sie haette fuer alle Einstellungen dieselben Zahlen geliefert, und zwar nicht weil die
  Schalter wirkungslos sind, sondern weil das Instrument blind fuer sie ist. Deshalb dieselbe
  Methode eine Ebene hoeher: Adresse auf einer echten Laufszene bilden (Nachbildung der Wuerfelei)
  und aufloesen. **Der Fund, der die Sache erklaert:** in DERSELBEN stehenden Szene bewirken beide
  Schalter **nichts** (2,3 gegen 2,1 %, p = 0,65). Erst mit `AW_VERSATZ=1` - Adresse auf Szene i
  gebildet, auf Szene i+1 aufgeloest - erscheint der Handel: grobe Fehler 3,3 -> 1,8 % (p = 0,0001),
  Rueckfall 27,1 -> 32,7 % (p < 0,0001). **Die Schalter wirken also nicht, weil die Wahrnehmung
  besser wird, sondern weil eine spezifischere Adresse laenger gueltig bleibt** - das beantwortet
  eine seit dem siebten Anlauf offene Frage. Beziffert: je 3000 Adressen 47 vermiedene Fehladressen
  gegen 169 zusaetzliche privilegierte Rueckfaelle, also **rund 3,6 Rueckfaelle je vermiedener
  Fehladresse**. Derselbe Handel wie im Lauf (10,8 -> 3,1 % bei 4,7 -> 10,0 %), nur an 3000 statt
  160 Adressen und in Minuten. **Entschieden ist er damit nicht, nur beziffert.** Zwei eigene
  Fehler dokumentiert: das Neuladen ueber `from pc_cvnn import pc_act23` liefert das ATTRIBUT des
  Paketobjekts, also die alte Instanz - alle vier Varianten waren zifferngenau gleich, bis auf
  `importlib.import_module` umgestellt; und in der ersten Versatz-Fassung lief die
  Identitaetspruefung gegen die ZIEL-Szene, also gegen Information, die die Wuerfelei nicht hat
  (grob fiel dadurch auf 0,1 % - ein Artefakt des Privilegs). Beide Schalter bleiben auf 0.

* **Anlage**: [Die Wiedervorlage](/mechanismen/wiedervorlage.md) + `src/pc_cvnn/act23_wiedervorlage.py`
  - aus der Erkenntnis des Chroma-Nachspiels ein festes Werkzeug gemacht. `pc_act23` protokolliert
  unter `ACT23_DEBUG=1` je Episode die **wahren Lagen aller Koerper** (`[dbg] after ep`) nach
  `log/`; damit laesst sich jede je gefahrene Szene nachstellen und mit bekannter Wahrheit
  befragen - auf der TATSAECHLICHEN Lagenverteilung, beliebig viele Einstellungen auf DENSELBEN
  Szenen, in Minuten statt Stunden. Beliebige Schalter ueber `WV_VARIANTEN`
  ("Name:VAR=WERT,...|Name:...", die erste ist der Bezug), gesetzt per Neuladen von
  `shape_classifier` wie in `act23_relrings_ab.py`, Fisher gegen den Bezug.
  **Es misst absichtlich beides zugleich:** VERFEHLT (keine Detektion am Koerper -> privilegierter
  Rueckfall) und ZERTEILT (mehrere Detektionen am selben Koerper -> Phantomklasse), dazu die
  Neuheits-Aufteilung "auf einem Koerper / Bruchstueck / nirgends". *Ein Gewinn bei VERFEHLT, der
  ZERTEILT mitzieht, ist keiner* - genau diese Verwechslung hat den Chroma-Schnitt zweimal als
  Erfolg erscheinen lassen. Die Detektionen je Koerper werden als **Mittel** ausgewiesen, nicht als
  Median: eine Zerteilung, die nur jede vierte Szene trifft, ist im Median unsichtbar. Gegenprobe
  bestanden - das Werkzeug reproduziert den Befund vom selben Tag aus einem einzigen Aufruf
  (`t1.0` verfehlt 0,0 % bei 4,7 % zerteilt, `t2.2` 1,7 % bei 1,1 %). Grenzen auf der Seite: der
  Yaw steht nicht im Protokoll, die Zeile faellt am Episodenende, der Vorgabe-Glob vermischt 500+
  Protokolle aus allen Projektphasen. **Es ersetzt keinen Lauf** - es sagt vorher, ob einer lohnt.

* **Ruecknahme**: [Der Chroma-Schnitt wird Vorgabe](/entscheidungen/chroma-split-vorgabe.md) auf
  `status: widerlegt`, `ACT_SHAPE_CHROMA_SPLIT` zurueck auf **0**. Die bestellte Nachmessung
  (Nutzen bei TRENNUNG 2,2) ist gemacht, und zwar erstmals **beide Seiten auf denselben Szenen** -
  200 Szenen am Episodenende aus den Laufprotokollen, 783 Koerper:
  `aus 1,1 % verfehlt / 0,6 % zerteilt | 1,0 -> 0,0 / 4,9 | 1,6 -> 0,9 / 1,9 | 2,2 -> 1,1 / 1,1 |
  3,0 -> 1,1 / 1,0`. **Bei 2,2 sind die verfehlten Koerper wieder auf dem Wert OHNE Schnitt.**
  Der Gewinn verschwindet exakt so schnell wie der Schaden - **es gibt keine Einstellung, in der
  der Nutzen bleibt und die Zerteilung weg ist**, weil der Nutzen DAS aggressive Schneiden IST:
  dieselbe Schranke, die einen verschmolzenen Blob trennt, trennt auch einen schattierten
  Einzelkoerper. In Stueckzahlen ist jede Einstellung ein Verlustgeschaeft (bei 1,0: neun
  vermiedene verfehlte Koerper gegen 33 zusaetzlich zerteilte), und ein zerteilter Koerper gebiert
  eine Phantomklasse, waehrend ein verfehlter nur einen privilegierten Rueckfall kostet.
  Schalter und beide Schranken bleiben samt Begruendung im Code. **Methodisch:** die Szenen waren
  nicht verloren - `pc_act23` schreibt sein eigenes Protokoll nach `log/`, und dort stehen die
  `after ep`-Lagen jeder Episode. Das macht die Wiedervorlage zu einem jederzeit verfuegbaren
  Werkzeug, das keinen Lauf kostet.

* **Anlage / Vorbehalt**: [Die verdreifachte Geburtenrate ist reines Phantom](/befunde/geburtenrate-chroma-phantome.md)
  - Nutzerfrage "untersuche die Geburtenrate", 150 Szenen nach den Regeln des Laufs
  (`pc_act16.scatter`, 80 mm Mindestabstand). **Der Chroma-Schnitt erzeugt keinen zusaetzlichen
  Aneignungsdruck, sondern Phantome:** neue Detektionen 14 -> 82, aber die ECHTEN (die einen
  ganzen Koerper bedecken) bleiben bei **13 gegen 13**; der ganze Zuwachs sind 54 Bruchstuecke
  zerteilter Einzelkoerper und 15 Detektionen bei keinem Koerper. Er **zerteilt Einzelkoerper in
  28 % der Szenen** (gegen 1,3 %). **Wie mir das zweimal entgangen ist:** ich habe beide Male den
  MEDIAN der Detektionen je Szene genommen (2,0 bei 2 Koerpern, 4,0 bei 4) - der verdeckt eine
  Zerteilung, die nur jede vierte Szene trifft; das Mittel zeigt sie (4,49). Dazu misst die
  Wiedervorlage den Abstand zur NAECHSTEN Detektion und kann zusaetzliche per Konstruktion nicht
  sehen. **Damit steht die Entscheidung vom selben Tag unter Vorbehalt** - der gemessene Nutzen
  (verfehlte Koerper 20 -> 0) bleibt gueltig, war aber unvollstaendig. `ACT_SHAPE_CHROMA_TRENNUNG`
  2,2 drittelt die Phantome (82 -> 24) bei unveraendert 13 echten, aber ob der Nutzen dort erhalten
  bleibt, ist ungemessen. Nebenbefund: auf den Szenen bei EPISODENBEGINN verfehlt auch der feste
  Schnitt nichts (0 von 600) - der Nutzen stammt aus den Szenen am Episodenende, wo der Arm Objekte
  zusammengeschoben hat. Nutzen und Schaden treten in verschiedenen Phasen derselben Episode auf.

* **Entscheidung**: [Der Chroma-Schnitt wird Vorgabe](/entscheidungen/chroma-split-vorgabe.md) -
  `ACT_SHAPE_CHROMA_SPLIT` steht auf **1** (Nutzerentscheid), mit TRENNUNG 1,0 und TIEFE 3.
  **Begruendet am Wahrnehmungsmass, nicht an der Lieferquote:** Wiedervorlage der Laufszenen,
  1024 Koerper, verfehlte Detektionen 20 -> 0 (p = 2e-06), Preis 0,5 mm Median und ~4 %
  Rechenzeit. Eine Quotenbestaetigung gibt es nicht und wird es nicht geben - Verschmelzung ist
  im Lauf ein 2-%-Phaenomen. Nach [ziel.md](/ziel.md) ist das der richtige Massstab: bewertet
  wird nach Wahrnehmung und Selbstaneignung. **Warnung fuer den naechsten GUI-Lauf:** der
  bestehende `act23_state.pkl` hat seine Formklassen unter der ALTEN Segmentierung gelernt
  (geladen gemessen 66,0 -> 55,7 %, frisch dagegen 13,0 -> 17,0 % zugunsten des Schnitts) - ein
  Quoteneinbruch in den ersten Episoden ist erwartbar und kein Rueckschritt. `STATE_SCHEMA`
  bewusst NICHT hochgezaehlt: die Invariante gilt fuer Strukturaenderungen, hier aendert sich die
  Verteilung der Eingaben, nicht ihre Form - hochzaehlen wuerde den 1053-Episoden-Zustand
  verwerfen. Rueckholbar mit `ACT_SHAPE_CHROMA_SPLIT=0`. Offen und ungemessen: die verdreifachte
  Geburtenrate (12 gegen 4 Klassen, 9 gegen 2 verhungert) - ob das der Aneignung nutzt oder
  schadet.

* **Anlage / Aufloesung**: [Frisch bei null](/befunde/chroma-split-frisch.md) - der Vergleich noch
  einmal mit `ACT23_FRESH=1`, 300 Episoden je Arm, damit jeder Arm seine Formklassen unter seinem
  eigenen Schnitt lernt. **Beide Vorbefunde kehren sich um:** der Quotenverlust reproduziert NICHT
  (17,0 gegen 13,0 % zugunsten des Schnitts, und er steigt im letzten Block noch steil: 29 gegen
  16 %) - der Verlust im vorigen Lauf lag also am veralteten Exemplarbestand. Der
  Adressierungsgewinn reproduziert aber ebenfalls nicht, er kehrt sich um (3,0 gegen 0,7 %,
  p = 0,037), und der Rueckfall auch (26 gegen 13, p = 0,046). **Grund: die Arme sind nicht gleich
  weit** - 12 geborene Klassen gegen 4. Ein frischer Arm, der sich dreimal so viel aneignet,
  adressiert entsprechend viele junge, unkonsolidierte Klassen; grobe Adressfehler messen dort mit,
  *wie viel der Agent sich zutraut*. **Damit ist fuer eine geaenderte Wahrnehmung WEDER der
  geladene NOCH der frische Aufbau sauber** - der eine traegt unpassenden Bestand, der andere
  erzeugt auseinanderlaufende Lernverlaeufe. **Entschieden hat es eine Messung ohne Lauf:** die
  Protokolle enthalten je Episode die wahren Lagen aller Koerper, also lassen sich **die Szenen des
  Laufs nachstellen** und beide Segmentierungen auf denselben Lagen befragen, rein raeumlich.
  Ergebnis ueber 1024 Koerper: **verfehlte Detektionen 20 gegen 0 (p = 2e-06)**, Preis 0,5 mm
  Median, Detektionszahl unveraendert (4 fuer 4 Koerper - es zerschneidet keine Einzelkoerper).
  **Und es erklaert die ganze Serie:** im Lauf ist Verschmelzung ein **2-%**-Phaenomen; meine
  Handsonde mit 5 eng gestellten Koerpern ueberzeichnete sie um **Faktor 15**. Eine Wirkung auf 2 %
  der Wahrnehmungen ist bei 150-300 Episoden nicht aufzuloesen - deshalb blieben sieben
  Armvergleiche nacheinander uneindeutig. Kein Widerspruch zu "alle groben Fehler sind
  Verschmelzung": das war die Zusammensetzung, dies ist die Haeufigkeit. Einschalten ist jetzt eine
  **Entscheidung, keine Messfrage**. Nicht mehr zu versuchen: die Wirkung des Schnitts ueber die
  Lieferquote nachzuweisen.

* **Anlage**: [Die Verschmelzung an der Quelle](/befunde/verschmelzung-chroma-split.md) - nach drei
  gescheiterten Reparaturen an VERBRAUCHERN der Wahrnehmung diesmal an der Segmentierung selbst.
  **Zwei Vermutungen unterwegs widerlegt:** (a) der vorhandene farbfreie Erosions-Split laesst den
  Elternblob in der Liste, und `max(area)` waehlt ihn - gemessen nur 4,5 % der Faelle; der
  eigentliche Fall ist, dass in 29 % GAR KEIN Teil beim Koerper liegt. (b) Pixelweise nach den
  GELERNTEN Farbklassen zu trennen erreicht 99,5 % und wurde trotzdem verworfen: eine neue Farbe
  muss trennbar sein, BEVOR sie eine Klasse hat, sonst haengt die Wahrnehmung eines neuen Objekts
  daran, dass es schon bekannt ist. **Gebaut ist ein unsupervised Chroma-Schnitt** (Lloyd auf der
  Chromatizitaet, Annahmeschranke = `TH` des Farb-Offenmengen-Moduls, also keine neue Zahl), mit
  drei Eigenschaften, jede aus einem der Fehlschlaege gelernt: er **ersetzt** den Elternblob statt
  daneben zu stehen, er **fasst nicht an, was eins bleibt** (exakter Schwerpunkt erhalten), und er
  **rekursiert** (Tiefe 3: Trefferquote 84,5 -> 100 %). **Eine zweite Schranke war noetig und ist
  der interessante Teil:** ein EINZELNER Koerper zerfaellt chromatisch ebenfalls (Deckflaeche gegen
  Seitenflaechen), das kostete bei weit getrennten Koerpern 0,86 -> 3,85 mm und 3 Detektionen fuer
  2 Koerper. Das Unterscheidungsmerkmal ist **raeumlich, nicht farblich** - zwei Koerper haben weit
  getrennte Schwerpunkte, eine Schattierung teilt denselben Koerper in Schichten, deren
  Schwerpunkte fast zusammenfallen. **Lauf (3 Arme je 150 Ep): grobe Adressfehler 3,1 -> 0,6 %
  (p = 0,044), privilegierter Rueckfall 10,0 -> 5,0 % (p = 0,069) -- der erste Eingriff, der beide
  ZUGLEICH senkt** (alle bisherigen tauschten). **Aber die Quote faellt 66,0 -> 55,7 % (p = 0,042),
  und mit Bonferroni 0,025 uebersteht keine der drei Zahlen die Schranke.** Mechanismus-Beleg ohne
  Test: die Adressen im Band `riesig` fallen 21 -> 17 -> 10, die im Band `winzig` steigen 2 -> 3 ->
  10 - die uebergrossen Detektionen verschwinden wirklich. **Eigener Aufbaufehler benannt:** beide
  Chroma-Arme liefen auf einem Zustand, dessen Formklassen aus UNGETEILTEN Komponenten gelernt
  sind; beim Relrings-A/B wurde genau das vermieden (beide Arme `ACT23_FRESH=1`). Der
  Quotenverlust kann deshalb ein Artefakt des veralteten Exemplarbestands sein.
  `evidenz: einzelmessung`. `ACT_SHAPE_CHROMA_SPLIT` bleibt auf 0; der naechste Schritt ist
  derselbe Vergleich frisch bei null, nicht ein weiterer Schalter.

* **Anlage / Widerlegung**: [Die pixelweise Farbbindung](/befunde/farbbindung-pixelweise.md) -
  Weg 2 (Nutzerauftrag), gebaut und gemessen. **Die woertliche Fassung war unmoeglich:** die
  Bindung aus der letzten sauberen Episode zu uebernehmen scheitert daran, dass `_faerbe_neu` je
  Episode alle sieben Farben permutiert - eine uebernommene Klasse ist nicht veraltet, sondern
  systematisch falsch, und es waere wieder die abgeloeste Tabelle. Gebaut wurde die erste Haelfte
  des Wegs mit derselben Episode als Quelle: die Mischchroma ist eine Eigenschaft des
  KOMPONENTENMITTELS, pixelweise gibt es sie nicht. Neue Methode `colour_parts_all` trennt alle
  Farbklassen in EINEM Rendern; `perceive_colour` bleibt unangetastet. **Der Mechanismus ist
  einwandfrei: 34 von 34 und 53 von 53 erreichbaren Koerpern gebunden** (die gemeldeten "34 von
  127" taeuschen - `_offen` zaehlt die drei je Episode geparkten Koerper mit, die nie bindbar sind).
  Pruefstand: Deckung 63 -> 97 %, und die neuen Bindungen sind brauchbarer als die vorhandenen
  (76 gegen 63 %). **Und es aendert nichts:** grobe Adressierungsfehler 3,1 -> 3,8 % (p = 1,00),
  Rueckfall 15 -> 19 (p = 0,59). **Damit ist meine eigene Catch-22-Deutung aus dem vorigen Lauf
  widerlegt** - die Bindung fehlte tatsaechlich bei verschmolzenen Blobs, war aber nicht der Grund,
  warum der Eig-Split scheiterte: mit vollstaendiger Bindung liegt er weiter bei 6,1 % groben
  Fehlern. Die Erklaerung bleibt die aus dem vorigen Lauf: der Split kostet Feinheit in JEDER
  Episode und nuetzt nur in den wenigen verschmolzenen. **Methodisch neu und billig:** der
  halbierte Median (3,2 -> 1,4 mm) sieht nach Gewinn aus, liegt aber genauso in den 119 Episoden,
  in denen der Mechanismus gar nicht gefeuert hat - *wenn ein Gewinn auch dort auftritt, wo der
  Eingriff nicht gegriffen hat, ist er keiner.* `ACT23_BINDUNG_SPLIT` bleibt auf 0, der Schalter
  bleibt: er ist die einzige Fassung, die verschmolzene Koerper ueberhaupt bindet. Ausdruecklich
  geschlossen: den Eig-Split ueber eine bessere Farbquelle retten (drei Anlaeufe, drei Negative).

* **Anlage**: [Der Form-Split im Eigenschafts-Pfad schadet](/befunde/eig-split-im-lauf.md) - der
  Nutzerauftrag, gebaut und gemessen. Drei Arme je 150 Episoden (`ACT23_EIG_SPLIT` 0/1/2),
  Vorgabearm reproduziert zum vierten Mal zifferngenau. **Ehrliches Negativ, beide Fassungen
  schlechter:** grobe Adressierungsfehler 3,1 -> 9,9 % (Indiz, p = 0,022) bzw. 8,7 % (immer,
  p = 0,056). **Der Kern ist ein Konstruktionsfehler, kein Kalibrierfehler:** bei der Indiz-Fassung
  erzeugten **alle fuenf** Splits einen groben Fehler, und der Adressfehler ist jedes Mal genau die
  Verschiebung des Splits (93/54/217 mm) - vorher war die Adresse richtig. Das Indiz prueft einen
  ABSTAND, und weit weg liegt das farbreine Material aus zwei Gruenden: Verschmelzung *oder* ein
  falsch gewaehltes Objekt derselben Farbklasse - wobei das falsche Objekt **weiter** weg liegt
  (215 gegen 20-30 mm). **Ein Abstands-Schwellwert siebt also bevorzugt die Verwechslungen heraus,
  nicht die Verschmelzungen.** Ep 119 ist der Lehrfall: obj_X und obj_L teilen sich `farbe-4`, die
  gestufte Form-/Groessenfilterung faengt es nicht ab, weil die Formklasse des verschmolzenen Blobs
  auf keinem der beiden Teile passt. Die Immer-Fassung ist dagegen gutartig (Splits 3,1 % grob),
  kostet aber Feinheit (Median 5,8 statt 1,4 mm) - und ihre schlechten Adressen sind die **ohne**
  Split (30,3 % grob). **Daraus die Catch-22, der wertvollste Teil:** der Split braucht
  `colour_of_body`, und `_farbbindung_neu` ueberspringt verschmolzene Blobs per Bauart - **die
  Rettung ist genau in den Episoden nicht verfuegbar, fuer die sie gebaut wurde.** Das gilt fuer
  jeden Rettungsweg ueber die gebundene Farbklasse, auch fuer den Form-Pfad. Dazu die **fuenfte
  Pruefstandsfalle, erstmals mit Vorwarnung**: die Kalibrierseite sagte "immer trennen ist besser"
  (8,5 -> 5,8 mm, 11,9 -> 1,5 %), im Lauf kehrt sich beides um, und der Grund (Lagenverteilung der
  Sonde) stand vorher unter *Fallen* auf derselben Seite. **Eine benannte Einschraenkung ersetzt
  keine Messung.** `ACT23_EIG_SPLIT` bleibt auf 0.

* **Ergaenzung**: [Beim Trennen entscheidet die Farbquelle](/befunde/eig-split-farbquelle.md) -
  Nebenbefund "immer trennen ist besser" als im Lauf entkraeftet gekennzeichnet. Die Hauptaussage
  (gebundene Farbe statt Tripel-Farbe) bleibt gueltig: sie wurde im Lauf nicht gegeneinander
  geprueft, sondern durchgehend gebunden verwendet.

* **Anlage**: [Beim Trennen entscheidet die Farbquelle](/befunde/eig-split-farbquelle.md) -
  Kalibrierung vor dem Einbau des Form-Splits in den Eigenschafts-Pfad (Nutzerauftrag). Gesucht war
  nur der Schnitt fuer das Verschmelzungs-Indiz; gefunden wurde, dass meine erste Fassung die Sache
  **verschlimmert** haette. Ueber 480 Lagen, nur die verschmolzenen Faelle (n = 148): nichts tun
  18,2 mm Median und 38,5 % ueber 20 mm; Split auf der **Tripel-Farbe** 33,2 mm und **98,4 %** -
  schlechter als gar nichts; Split auf der **gebundenen** Farbe (`colour_of_body`) 6,7 mm und
  1,4 %. Grund: die Farbachse des Tripels hat die Wuerfelei AUS der Verschmelzung geschrieben, sie
  ist die Mischchroma-Klasse (im Lauf an den hohen Nummern `farbe-50/59/64` erkennbar) und trennt
  genau das falsche Material heraus. `_farbbindung_neu` ueberspringt verschmolzene Blobs bei der
  Bindung und ist deshalb per Bauart sauber - **der Form-Pfad hat das immer schon richtig gemacht.**
  Schnitt fuer das Indiz auf **0,8** gemessen (72 % erkannt bei 10 % Fehlalarm); mein geratener Wert
  0,7 lag auf einer falschen Groessenordnung. Nebenbefund: ueber ALLE 480 Lagen ist *immer* zu
  trennen besser als der heutige Pfad (8,5 -> 5,8 mm Median, ueber 20 mm 11,9 -> 1,5 %) - deshalb
  sind beide Fassungen gebaut (`ACT23_EIG_SPLIT` 1 = mit Indiz, 2 = immer). `ebene: pruefstand`,
  die Lagenverteilung der Sonde ueberwiegt nahe Nachbarn; welche Fassung traegt, entscheidet das
  laufende A/B, nicht diese Seite.

* **Anlage**: [Jeder grobe Adressfehler sitzt im obersten Band](/befunde/adressfehler-sind-verschmelzung.md)
  - beim Auswerten abgefallen, nicht gesucht, und der wichtigere der beiden Befunde des Tages.
  **26 von 26 groben Adressierungsfehlern liegen im Band `riesig`** (Spanne ab 36 mm); in den
  uebrigen **266 Adressen ueber alle anderen Baender: null** (p = 3,4e-21, und in jedem Arm einzeln
  auch). `riesig` ist faktisch das Band der VERSCHMOLZENEN Blobs - der groesste einzelne Koerper,
  obj_U, misst 37,4 mm. Getragen wird der Fehler von einer einzigen Klasse: `neu-13`, auf einem
  verschmolzenen Blob geboren (17/23 grobe Fehler in einem Arm). **Damit ist der Restfehler des
  siebten Anlaufs lokalisiert und er ist keine Frage der Achse:** die Spanne hat den Fehler nicht
  behoben, sondern ihn an einen Ort gelegt, an dem man ihn sehen kann. Das erklaert rueckwirkend
  auch, warum der Identitaetscheck erst ZUSAMMEN mit der Spanne wirkte. Naechster Schritt, billiger
  als jede weitere Arbeit an der Groessenachse: der **Form-Split existiert bereits** auf dem
  FORM-Pfad (verschmolzener Blob -> Form auf dem farb-getrennten Teil, gemessen 8,8 -> 81 %) und
  **fehlt dem Eigenschafts-Pfad**. Kein neuer Mechanismus, ein vorhandener an zweiter Stelle.

* **Anlage**: [Abstufung statt Privileg](/befunde/abstufung-statt-privileg.md) - der Nutzerauftrag,
  gebaut und gemessen: bei "kein Treffer" die Groessenachse fallen lassen statt auf die wahre Lage
  aus dem Simulator zu greifen. Drei Arme je 150 Episoden (`ACT23_EIG_ABSTUFUNG` 0/1/2), Vorgabearm
  reproduziert `g7_beide` zifferngenau - der Einbau hat den Vorgabepfad nicht angefasst.
  **Ehrliches Negativ.** Die Abstufung greift selten (3 von 6 Gelegenheiten; nur 11 der 15
  Rueckfaelle tragen ueberhaupt ein Band, der Rest scheitert an Farb- oder Formklassen), senkt den
  Rueckfall nur 15 -> 11 (p = 0,54), und einer der drei Faelle adressierte einen **fremden Wuerfel
  65 mm daneben**. **Die vorgesehene Sicherung existiert nicht:** Fassung 1 und 2 sind bitgleich,
  weil der mehrdeutige Fall `1 Treffer` meldet - die anderen zwei Wuerfel kamen gar nicht erst als
  eigene Detektion an. *Eindeutigkeit ist nicht Richtigkeit* zum dritten Mal, mit der neuen
  Folgerung: **beim SCHREIBEN einer Adresse loest die Identitaetspruefung das, beim LESEN nicht** -
  sie vergleicht gegen die wahre Lage und waere im Wahrnehmungspfad genau das Privileg, das die
  Abstufung abschaffen soll. Die grossen Zahlen des Arms (grobe Fehler 3,1 -> 13,1 %, Quote
  66,0 -> 54,7 %) sind **Abdrift, nicht Wirkung**: nur 2 der 23 groben Fehler sind Abstufungen, der
  Lauf ist nach dem ersten Eingriff bei Ep 14 ein anderer Lauf. `ACT23_EIG_ABSTUFUNG` bleibt auf 0.

* **Anlage**: [Das groebere 7-mm-Raster senkt den Rueckfall nicht](/befunde/spannen-raster-7mm.md)
  - die offene Frage des siebten Anlaufs, beantwortet mit **nein**. Drei Arme je 150 Episoden
  (Vorgabe / gemessene Liste / 7-mm-Raster). Der Adressierungsgewinn bleibt (**2,6 gegen 3,1 %**
  grobe Fehler, beide weit unter den 10,8 % der Vorgabe, p = 0,0038), aber der privilegierte
  Rueckfall wird nicht kleiner, sondern **groesser: 20 statt 15, gegen 7 in der Vorgabe**
  (p = 0,0142). **Die Ursache ist nicht die Rasterweite, sondern die Bandzahl:** das gleichmaessige
  Raster haengt ein siebtes Band `gewaltig` (ab 52,5 mm) an. Kein einzelner Koerper wird so gross
  - der groesste, obj_U, misst 37,4 mm -, also landet dort nur ein **verschmolzener Blob**. Wird
  `gewaltig` einmal in ein Eigenschafts-Tripel geschrieben, passt es im naechsten Bild nie wieder:
  6 der 20 Rueckfaelle gehen darauf zurueck, ohne sie waeren es 14 und damit wie beim feinen Arm.
  **Ein offenes oberstes Band ist keine Nachlaessigkeit, sondern haelt den Ausreisser im
  adressierbaren Bereich** - das Aufraeumen zum gleichmaessigen Raster hat es entfernt.
  Nebenbefund: `r7_aus` und `r7_fein` wiederholen `g7_aus` und `g7_beide` **zifferngenau**
  (58,7/66,0 %, 18/167 und 5/159, 7 und 15 Rueckfaelle) - der siebte Anlauf war kein Ausreisser.
  Eigene Falle dokumentiert: ein zweiter Auswerter, der gleiche `[dbg]`-Zeilen entdoppelte, kam
  auf 8/148 statt 18/167 - plausibel aussehend und mit der gemessenen Seite nicht vergleichbar.
  `ACT23_SPANNE_RASTER` bleibt auf `0`.

* **Anlage**: [Die Groessenachse mass die falsche Groesse](/befunde/groessenachse-spanne.md) -
  der siebte Anlauf. **Der Auftrag verschob sich:** bestellt war "das Groessenband feiner",
  gemessen ist die Achse aber nicht zu grob, sondern die **falsche**. Sie nutzte die
  MATERIALDICKE - und alle sieben Koerper liegen dort zwischen 5,61 und 6,08, also im selben Band
  "mittel"; Trennung 0,3-0,7 Streuungen. Die **Spanne** (Ausdehnung, in `perceive_all` laengst
  gerechnet, nie als Adressachse herausgefuehrt) trennt alle fuenf Formen mit 2,2-4,8 Streuungen.
  Dazu ein zweiter Fund beim Lesen: die Wuerfelei prueft beim Achsen-Nachlegen nur die **Anzahl**
  der Treffer, nicht die **Identitaet** - daher 316 von 318 "eindeutigen" Adressen bei 8,8 %
  groben Fehlern. **Faktorielles A/B (4 Arme je 150 Ep) zeigt eine Wechselwirkung:** `span` allein
  p = 0,58, `ident` allein **bitgleich zur Vorgabe** (nie gegriffen), **beide zusammen 10,8 ->
  3,1 %, p = 0,0086**. Grund: der Identitaetscheck kann nur nachlegen, wenn es eine trennende
  Achse gibt - mit der Dicke-Achse landen 75 von 89 Adressen im Band "mittel". *Schloss und
  Schluessel; wer sie einzeln misst, misst zweimal null.* **Preis, real:** der privilegierte
  Rueckfall verdoppelt sich (4,7 -> 10,0 % der Episoden). Beide Vorgaben bleiben 0.

* **Anlage + Selbstkorrektur**:
  [Sechster Anlauf: der Zielkonflikt](/befunde/relrings-split-zielkonflikt.md) - Klassifikation
  und Ausrichtung getrennt (`ACT_SHAPE_RELRINGS=2`: Klasse relativ, Yaw fest; der Greifpunkt
  haengt ohnehin nicht an den Harmonischen). Am Pruefstand bleibt die Klassifikations-Verbesserung
  **exakt** erhalten (25,9 -> 88,9 %). Im Lauf aber: **grobe Adressierungsfehler 2,1 -> 8,8 %
  (p = 0,0003)** gegen 9,8 % bei Fassung 1 - **der Split behebt nichts, meine Ursachenzuschreibung
  war falsch.** Die Quote ist diesmal unauffaellig (20,3 gegen 18,7 %, p = 0,68), der
  Quotenverlust der Fassung 1 ging also wirklich auf den Yaw. **Die wirkliche Ursache der
  Adressierungsfehler ist ein ZIELKONFLIKT:** Groessen-Invarianz macht Klassen breiter - im
  Split-Arm tragen drei Klassen mehrere Koerper statt zwei, darunter `cube` (3 Koerper) und
  `neu-3` (obj_T, obj_U, obj_blue) - und ein Eigenschafts-Tripel trifft dann oefter den falschen.
  21 der 28 groben Fehler haben eine Formachse. **Und 316 von 318 Adressen melden trotzdem "genau
  ein Treffer"** - woertlich "Eindeutigkeit ist nicht Richtigkeit", erstmals als Folge einer
  *Verbesserung*. Lehre: die Groesse war nicht nur ein Mangel des Deskriptors, sondern das, was
  obj_T von obj_U trennt. relrings-im-lauf.md traegt die Korrektur im Kopf.

## 2026-09-13

* **Anlage, ehrliches Negativ**: [Relative Ringe im Lauf](/befunde/relrings-im-lauf.md) - zwei
  FRISCHE Laeufe je 300 Episoden (der gespeicherte Bestand ist mit festen Ringen gerechnet, ein
  Vergleich gegen ihn waere unfair gewesen). **Die Pruefstandsverbesserung schlaegt nicht durch:**
  Geburtenrate identisch (5 zu 5, p = 1,00), Ueberleben 3 gegen 2, **Adressierung messbar
  schlechter** - grobe Fehler >20 mm von 2,1 auf 9,8 % (p = 0,0001), privilegierter Rueckfall
  25 -> 52, Lieferquote 20,3 -> 11,7 %. **Grund:** am selben Deskriptor haengt nicht nur die
  Klasse, sondern auch Greifpunkt und Yaw (`_harmonics_at` -> `_yaw_from`); die Lokalisierung
  verliert mehr, als die Klassifikation gewinnt. **Vierter Fall der
  [Pruefstandsfalle](/mechanismen/pruefstandsfalle.md)** - und diesmal war die Vorstufe bereits
  ein direktes Mass. Praezisere Lehre daraus: *ein direktes Mass ist nicht automatisch das
  richtige Mass; `ebene` sagt, WO gemessen wurde, nicht ob ALLES BETROFFENE mitgemessen wurde.*
  [relrings-rueckhalt.md](/befunde/relrings-rueckhalt.md) traegt die Entkraeftung im Kopf.
  Der Schalter bleibt auf 0; ein sechster Anlauf muesste Klassifikation und Lokalisierung
  trennen (feste Ringe fuer Greifpunkt/Yaw, relative nur fuer `resolve()`).

* **Anlage**: [Relative Ringe bestehen den Rueckhalte-Test](/befunde/relrings-rueckhalt.md) - die
  Pruefstandszahl aus [dem fuenften Anlauf](/befunde/groessen-invarianz-fuenfter-anlauf.md) ist am
  direkten Mass geprueft. Zwei **frisch angelernte** Klassifikatoren je Seed (der alte Bestand ist
  mit festen Ringen gerechnet und nicht vergleichbar), getestet an den drei trainierten Formen in
  0,7x bis 2,0x. **Bei den uebergrossen Faellen (>=1,4x): 18,1 % richtig mit festen Ringen, 68,8 %
  mit relativen**, ueber zwei Seeds stabil. Trainingsgenauigkeit bleibt 1,000, `novel_th`
  kalibriert sich gleich, bei 1,0x sind beide gleich gut - **kein Preis bei den bekannten
  Formen.** Ehrlich dazu: Verwechslungen steigen von exakt 0 auf 0,6-1,2 % (der feste Deskriptor
  irrt nie, er **enthaelt sich**; der relative trifft fast immer und irrt gelegentlich), und auch
  relativ bleiben 31 % der uebergrossen Faelle unerkannt - **verbessert, nicht hergestellt.** Neuer
  Schalter `ACT_SHAPE_RELRINGS` (Vorgabe 0). **Die Pruefstandsfalle ist diesmal nicht
  zugeschnappt** - was in diesem Projekt die Ausnahme ist.

## 2026-09-12

* **Anlage**: [Groessen-Invarianz, fuenfter Anlauf](/befunde/groessen-invarianz-fuenfter-anlauf.md)
  - der Hebel aus [Form-Rueckhalte-Test](/befunde/form-rueckhalt.md), neues Werkzeug
  `act23_groessen_invarianz.py`. Die vier bisherigen Fassungen normieren **Amplituden** oder
  skalieren Radien **global**; die Ringe liegen aber weiter an festen Weltradien, also misst
  Ring i bei einem groesseren Objekt eine andere Stelle der Form. Der fuenfte Ansatz haengt die
  Ringe an die **Eigenausdehnung**. Kennzahl K = groesster Groessen- / kleinster Form-Abstand,
  drei Seeds:
  `heute 3,68 | dicke 3,93 | dc 4,25 | fuellung 3,62` gegen `rms 2,37 | sqrtA 2,55 | rmax 2,08`.
  **Die vier alten Fassungen bewegen im selben Aufbau nichts** (ihr Misserfolg ist hier
  repliziert), **die relativen Ringe halbieren die Kennzahl** - und zwar in die richtige
  Richtung: der Form-Abstand *steigt*, der Groessen-Abstand faellt. **Das Ziel unter 1,0 ist
  trotzdem nicht erreicht.** Zwei wichtige Vorbehalte in der Seite: der Aufbau ist haerter als
  der urspruengliche (deshalb wurden die vier alten Fassungen nachgerechnet - sonst waere "2,37
  gegen 2,13" ein scheinbarer Rueckschritt), und ein geaenderter Deskriptor **entwertet den
  gesamten gelernten Klassenbestand** (die 80 Exemplare je Klasse sind mit festen Ringen
  gerechnet, die Masken nicht gespeichert). Empfehlung: nicht einbauen, sondern zuerst den
  Form-Rueckhalte-Test auf einem frisch angelernten Bestand fahren.

* **Anlage**: [Form-Rueckhalte-Test](/befunde/form-rueckhalt.md) - Weg 3 aus
  [Geburtenrate und Saettigung](/befunde/geburtenrate-und-saettigung.md), neues Werkzeug
  `act23_form_rueckhalt.py`. Statt Geburten zu zaehlen wird gefragt, ob eine nie gesehene Form in
  die **passende bestehende** Kategorie faellt. Bilanz ueber 72 Sichtungen: **36,1 % richtig,
  54,2 % neu (uebersegmentiert), 9,7 % falsch.** Aufgeschluesselt eine scharfe Asymmetrie -
  laengliche Formen 69,4 % richtig und **null** Verwechslungen, quadratische 2,8 %. Die
  Groessen-Kontrolle erklaert es: **beide** Kategorien brechen bei rund dem **1,3-fachen** des
  bekannten Masses, unabhaengig von der Form; der Wuerfel ist mit 12 mm nur der kleinste Koerper
  und hatte deshalb keine Luft nach oben. **Der Deskriptor verallgemeinert ueber die PROPORTION**
  (2,9:1 bis 8,5:1 alle als derselbe Balken - genau die Grobkategorie aus der Nutzerfrage)
  **und nicht ueber die GROESSE.** Das bestaetigt
  [Formfaktorisierung](/befunde/formfaktorisierung.md) und beziffert erstmals, was daran haengt:
  die Haelfte aller Verallgemeinerungsfaelle.

* **Klarstellung (Nutzerfrage)**: die Formklassen entstehen **nicht** aus der Fovea, sondern aus
  dem vollen Kamerabild - `perceive_all` -> `_render_u8` (240x240, Arm ausgeblendet) ->
  Saettigungsmaske -> CC-Segmentierung -> komplexe Winkelharmonische auf Polarringen (`RW`
  4-46 mm in Weltmassen). Die Fovea (16x16 Zellen) liefert den BLICK, nicht die Form. Das ist
  genau das Uebergangsgeruest, das [das Projektziel](/ziel.md) abbauen will.

* **Anlage**: [Geburtenrate und Saettigung](/befunde/geburtenrate-und-saettigung.md) - auf zwei
  Nutzerfragen. **(a) Der Neuheits-Erzeuger laeuft seit Langem nicht:** `spawn_novel_shape` kehrt
  in der ersten Zeile zurueck, weil `NOVEL_BODY` (Vorgabe `obj_T`) laengst in `SHAPE_KEY` steht -
  im 906-Episoden-Langlauf kommt `[Neuheit]` **null Mal** vor. Das erklaert auch, warum
  `NOVEL_EVERY=3` im [Schutz-A/B](/befunde/eig-schuetzt-null.md) nichts bewirkte.
  **(b) Die Saettigungshypothese des Nutzers ist bestaetigt, schaerfer als formuliert:** die
  Formklassen SIND bereits Grobkategorien - `cube` fasst drei Koerper zusammen, und `neu-9`
  (obj_T, 21x7) und `neu-285` (obj_X, 21x6) liegen mit 0,66 x novel_th **naeher beieinander als
  die Streuung innerhalb einer einzelnen Klasse** (neu-13: 1,14). Zwei Klassen, eine Kategorie.
  **(c) Die Haelfte des Neuheitsvorrats ist gar nicht neu:** die langen duennen Varianten
  (30x4, 32x5) werden als `neu-9` erkannt - korrekte Verallgemeinerung, keine Fehlfunktion.
  **Folge fuer die Messweise:** "mehr Geburten" ist kein gutes Ziel; in einer Welt mit vier
  Grobformen ist eine hohe Geburtenrate ein Zeichen von Uebersegmentierung. Die richtige Frage
  ist, ob ein NEUES Objekt in die passende bestehende Kategorie faellt - ein Form-Rueckhalte-Test
  nach dem Muster des [Farb-Tests](/befunde/farbe-form-rueckhalt.md), und der kostet keinen Lauf.

## 2026-09-11

* **Anlage, ehrliches Negativ**: [Der Eigenschafts-Schutz wirkt nicht](/befunde/eig-schuetzt-null.md)
  - der Langlauf mit `ACT23_EIG_SCHUETZT=1` gegen einen Kontrollarm, je 400 Episoden. Die Arme
  sind **bitgleich** - nicht "statistisch gleich", sondern jede Zeile identisch. Der Schalter hat
  nie eine Entscheidung geaendert. **Ursache ist ein Konstruktionsfehler meines Entwurfs:**
  `state.EIGENSCHAFT` ist ein Verzeichnis Koerper -> Tripel und wird je Koerper ueberschrieben,
  der Schutz liest also einen Schnappschuss statt einer Historie - und haelt genau so lange, wie
  die Klasse ohnehin zu jung zum Sterben ist. **Damit ist auch meine Begruendung entkraeftet**
  ("der Aufraeumer entfernt, was der Agent benutzt"): gemessen ueberleben die adressierten Klassen
  ohnehin, und die sterbenden werden schlicht nie adressiert - 5 Kommandos auf 5 junge Klassen
  gegen 107 auf die vier etablierten. Der Zaehler-Fix aus Schritt 1 hat sich trotzdem bezahlt
  gemacht: erst durch ihn ist "stirbt trotz Benutzung" von "stirbt mangels Benutzung"
  unterscheidbar. Nebenbefund, ungeklaert: trotz verdoppelter Neuheitsrate (`NOVEL_EVERY=3`) nur
  5 Geburten auf 400 Episoden - die Geburtenrate haengt kaum an diesem Schalter.

* **Anlage**: [Der blinde Fleck der Aneignung](/befunde/aneignung-blinder-fleck.md) - die zwei
  kleinen Schritte vor der latenten Augmentierung. Es sind **zwei Stellen mit demselben Fehler**:
  der Aneignungs-Zaehler (`pc_act23.py:4547`) verfaelscht die MESSUNG, der Verhungerungsschutz
  (`:2896`) veraendert das VERHALTEN - `_starve_and_cap` loescht nach 25 Blicken jede
  ungeschuetzte Klasse, und ueber Eigenschaften kommandierte gelten als ungeschuetzt. **Die
  Aufraeum-Mechanik entfernt damit genau die Klassen, die der Agent benutzt.** Der Zaehler-Fix
  ist unbedingt (eine Reparatur, kein Wahlrecht) und im Rauchtest verifiziert: `neu-285 57 %
  (5x kdo)`, wo vorher `0x` stand; dafuer wurde die Zahl fuer bestehende Klassen ueberhaupt erst
  sichtbar gemacht. Der Schutz liegt hinter `ACT23_EIG_SCHUETZT` (Vorgabe 0) und ist **noch nicht
  messbar**: 13 Geburten auf 906 Episoden = 1,4 %, ein 120-Ep-A/B saehe zwei - keine auswertbare
  Stichprobe. Das steht so in der Seite.

* **Korrektur (eigene, am selben Tag)**:
  [906 Episoden in der entkoppelten Welt](/befunde/langlauf-entkoppelt.md) nachgeschaerft. Die
  erste Fassung sagte "kein Lernproblem, sondern eine Vergabe-Engstelle" - zu grob. Nachgemessen:
  **sechs der dreizehn verhungerten Klassen erreichen 50-75 % Wiedererkennung**, sie funktionieren
  also und sterben trotzdem nach ~25 Episoden. Und: **der Aneignungs-Zaehler hat einen blinden
  Fleck** - er liest `state.SHAPE_KEY` (`pc_act23.py:4547`) und sieht das Eigenschafts-Kommando
  nicht. `neu-373` steht in allen 363 Zeilen mit `kommandiert 0x` und wurde fuenfmal adressiert.
  [Selbst-Aneignung stockt](/befunde/selbstaneignung-stockt.md) traegt deshalb jetzt einen
  Vorbehalt: fuer die dortigen August-Laeufe gilt die Aussage, wer sie heute nachmisst, misst am
  blinden Fleck vorbei.

* **Anlage**: [906 Episoden in der entkoppelten Welt](/befunde/langlauf-entkoppelt.md) - erster
  Langlauf des Nutzers mit `ACT23_FARB_MISCHUNG=1`, 26,8 h. **Die Quote haelt: 53,1 %**, also das
  alte Niveau - der im [A/B](/befunde/farb-mischung.md) gemessene Einbruch auf 47,6 % tritt NICHT
  ein, die dortige Warnung ("die Seeds widersprechen einander, der Vergleichsarm lag zu hoch")
  war richtig. Adressierung ueber 906 Episoden stabil (1,4 mm, 98,9 % eindeutig). **Eine reine
  FORM-Adresse liefert so gut wie eine Farb-Adresse** (49,8 gegen 53,0 %, p = 0,46) - eine
  Aussage, die es vor der Entkopplung nicht geben konnte. **97 Farb/Form-Kombinationen statt 7.**
  Und trotzdem: 13 Klassen geboren, **keine setzt sich fest**, Bestand am Ende identisch mit dem
  Anfang, unzuordenbare Sichtungen linear 16 -> 227. Alle 13 Geburten melden "kein Knopf zu
  vergeben" - **eine Vergabe-Engstelle, kein Wahrnehmungsproblem.** Nebenbefund: drei neue
  FARBklassen geboren (erwartet waren null), eine davon an obj_U gebunden - bei den Farben
  funktioniert, was bei den Formen stockt.

* **Relativierung**: [Farbe und Form entkoppelt](/befunde/farb-mischung.md) - der dortige
  Quotenbefund (57,5 -> 47,6 %) ist durch den Langlauf entkraeftet.

## 2026-09-10

* **Entscheidung**: `ACT23_FARB_MISCHUNG` steht auf Nutzerentscheid auf **1** - **die entkoppelte
  Welt ist ab jetzt die Standardwelt.** Farbe und Form sind unabhaengig, `colour_of_body` kommt je
  Episode aus der Wahrnehmung. Das ist eine Entscheidung ueber das **Szenario**, nicht ueber eine
  Verbesserung. **Alle Quotenzahlen ab hier sind mit denen davor nicht vergleichbar** - es ist
  eine andere Aufgabe, und wer die Vorgabe zurueckdreht, weil "die Quote gefallen ist", misst das
  Szenario statt eines Fehlers. Geprueft ohne Umgebungsvariable: `[Farbe]`-Zeile je Episode, 0
  neue Farbklassen. Rueckfall: `ACT23_FARB_MISCHUNG=0`. Seite:
  [Farbe und Form entkoppelt](/befunde/farb-mischung.md).

* **Anlage**: [Farbe und Form entkoppelt](/befunde/farb-mischung.md) - auf Nutzerauftrag gebaut
  (`ACT23_FARB_MISCHUNG`, Vorgabe 0): die sieben vorhandenen Koerperfarben werden je Episode
  **permutiert** (keine neuen Farben, sonst gebaeren sie Farbklassen - Kontrolle: 0 neue), und
  **`colour_of_body` kommt je Episode aus der Wahrnehmung** statt aus der persistierten Tabelle,
  mit den drei Wachen der Erstbindung. **Die Adressierung haelt** - Median 1,0-1,4 mm in allen
  vier Armen, Eindeutigkeit unveraendert, privilegierter Rueckfall 4-5 -> 6 %. Die Lieferquote
  faellt gepoolt 57,5 -> 47,6 % (p = 0,039), aber die Seeds widersprechen einander (-1,3 gegen
  -18,3 Punkte) und der Vergleichsarm m23_aus lag mit 63,8 % ohnehin weit ueber dem Ueblichen.
  **Wichtiger Vorbehalt in der Seite:** das ist ein WELT-Wechsel, kein Eingriff - "besser oder
  schlechter" ist die falsche Frage, "haelt die Maschinerie" die richtige, und die Antwort ist ja.
  Nebenwert: unzuordenbare Sichtungen 26 -> 45 in einem Arm, passend zu "vertraute Formen in
  ungewohnten Farben sind neu".

* **Anlage**: [Farb-Rueckhalte-Test](/befunde/farbe-form-rueckhalt.md) - auf Nutzerbeobachtung
  ("die Objekte haben immer die gleiche Farbe"). Nachgezaehlt stimmt sie und ist enger als
  vermutet: der Wuerfel gibt es in **drei** Farben, alle anderen Formen in genau einer, und in
  5 von 6 Farbklassen bestimmt die Farbe die Form eindeutig. Der Rueckhalte-Test (336
  Umfaerbungen) sagt aber: **die Wahrnehmung kuerzt NICHT ueber die Farbe ab** - bei allen
  trainierten Formen haelt die Klasse zu 100 %, der Deskriptor ist farbblind wie konstruiert.
  Freigelegt hat der Test etwas anderes: **obj_X haelt seine Formklasse schon in der EIGENEN
  Farbe nur in 4 von 8 Lagen** und wird meist als "cube" gelesen - die "wandernde
  Deskriptor"-Hypothese, erstmals ausserhalb einer Verschmelzungsszene belegt. Folge fuer die
  Entkopplung: sie wuerde die Formerkennung nicht brechen, sondern diese Schwaeche **aufdecken**.

* **Widerlegung (eigene)**: [Der Nachbar-Block traegt nichts](/befunde/merkmale-kommen-zu-spaet.md)
  - Weg 2a gefahren (Fit nur auf den 690 gueltigen Zeilen, Halteteil nach Zeit mit Luecke, 5
  Seeds): MIT Block AUC 0,603 +- 0,025, OHNE Block 0,599 +- 0,023. **+0,004, also nichts.** Meine
  Erklaerung "das Merkmal ist bloss verduennt" ist damit fuer diesen Block widerlegt. Die
  allgemeine Puffer-Frage bleibt offen, ihr Beispiel faellt weg - wer die Puffer-Architektur
  angeht, braucht ein Merkmal, von dem vorher gezeigt ist, dass es Signal traegt.

* **Entscheidung**: `ACT23_TRACK_KONTINUITAET` steht auf Nutzerentscheid auf **1** - der Tracker
  folgt bei ausgefallener Formklasse dem naechsten Farb-Teil, statt fuer dieses Bild blind zu
  werden. Kein grundsaetzlicher Preis (kein Privileg, rein wahrnehmungsbasiert), Gegenprobe
  sauber (p = 1,0000). **Ausdruecklich kein Quotengewinn** (p = 0,41, Seeds gegenlaeufig).
  Rueckfall: `ACT23_TRACK_KONTINUITAET=0`.

* **Anlage**: [Kontinuitaet statt Neuklassifikation](/befunde/kontinuitaet-statt-neuklassifikation.md)
  - der aus [der Diagnose](/befunde/formsplit-warum.md) empfohlene Weg ist gebaut
  (`ACT23_TRACK_KONTINUITAET`, Vorgabe 0) und im gepaarten Seed-Sweep gemessen. **Die
  Sicherheitsfrage ist sauber**: fremder Belief 8,8 -> 9,2 %, p = 1,0000 - die Ablenker-Bindung
  kommt ueber den klassenfreien Pfad nicht zurueck, die beiden Wachen tragen. **Das Loch ist
  aber kleiner als meine Begruendung nahelegte**: kein einziger Lauf war je ganz blind (0/120 in
  allen vier Armen), der Servo hatte auch ohne die Aenderung in 31-32 % der Anfahrschritte eine
  Beobachtung, und die Kontinuitaet fuellt 1,3-2,2 %. Lieferquote nicht aufgeloest, die Seeds
  widersprechen einander (-3,3 und +11,7 Punkte, gepoolt p = 0,41). Vorgabe bleibt `0`; anders
  als beim Rueckfall-Keim gibt es hier aber **keinen grundsaetzlichen Preis** - die Abwaegung
  steht in der Seite.

## 2026-09-09

* **Anlage**: [Warum der Split die Formklasse verliert](/befunde/formsplit-warum.md) - Diagnose
  vor der Reparatur, mit dem neuen Werkzeug `src/pc_cvnn/act23_formsplit_probe.py`. Beide
  Verdachte bestaetigt, und der eine verursacht den anderen: der Splitteil behaelt nur
  **31-58 %** der Pixel, und der Deskriptor dieser halben Silhouette springt von 0,44-0,53 auf
  **0,94-1,55 x novel_th**, also knapp darueber. **Der Ausfall ist eine ENTHALTUNG, keine
  Verwechslung** - in 55 von 58 Fehlern antwortet `resolve()` mit "neuartig", nur dreimal mit
  einer fremden Klasse. Drei Reparaturwege in der Seite, Empfehlung: **Kontinuitaet statt
  Neuklassifikation** im Tracker (die Identitaet steht seit dem Keim fest, je Bild wird nur die
  Position gebraucht - und die rettet der Split ab 35 mm vollstaendig). Nichts gebaut.

* **Anlage**: [Nachbarnaehe im Lauf](/befunde/nachbarnaehe-im-lauf.md) - die zweite Haelfte der
  Verschmelzungsfrage, ausgezaehlt ueber **1868 Episoden** aus den Protokollen. Der kritische
  Bereich unter 35 mm ist selten (2,1 %), der wirksame ist breiter: **unter 55 mm sind es 15,6 %
  der Episoden, und dort faellt die Quote von 54,9 auf 41,1 % (-13,9 Punkte, p < 0,0001)**, bei
  **7 von 7 Objekten gleichgerichtet** (Vorzeichentest p = 0,0156). Hochgerechnet ~2,2 Punkte der
  Gesamtquote - ausdruecklich als **Obergrenze**, denn Verschmelzung, Rammen des Nachbarn und
  schlechtere Greifpunktwahl sind hier nicht getrennt. **Der interessanteste Teil:** die Schwelle
  im Ausgang (55 mm) folgt der FORMKLASSEN-Rettung (ab 65 mm), nicht der Positions-Rettung (ab
  35 mm) - zu wissen wo etwas ist genuegt nicht, wenn unklar bleibt was es ist. Falle in der
  Seite: die protokollierten `[Farb-Split]`-Zeilen taugen NICHT als Haeufigkeitsmass (eine
  einzige in 1868 Episoden).

* **Anlage**: [Verschmelzung: die Abstandskurve](/befunde/verschmelzung-abstandskurve.md) - der
  seit August offene Faden ist gemessen, mit dem neuen Werkzeug
  `src/pc_cvnn/act23_fusion_probe.py` (864 Konstellationen). Verschmelzung reicht bis ~75 mm
  Mittenabstand und beherrscht alles unter 35 mm; der **Farb-Split rettet ab 35 mm zu 100 %**,
  bei 25 mm nur zu 72 %, bei 15 mm zu 29 %. Die **Formklasse** ueberlebt die Rettung viel
  schlechter als die Position (42 % bei 35 mm, erst ab 65 mm sicher) - das trifft die Formachse
  des Eigenschafts-Kommandos. Zwei Einschraenkungen in der Seite: **ein Paar (obj_X/obj_green)
  verschmilzt bei keinem Abstand**, Verschmelzung ist also paarabhaengig; und die 15-mm-Zeile ist
  ueberwiegend unphysikalisch, weil sich die Koerper dort durchdringen. Ebene `pruefstand` - wie
  oft das im Lauf vorkommt, ist damit NICHT gemessen.

* **Ruecknahme**: `ACT23_KEIM_RUECKFALL` steht auf Nutzerentscheid wieder auf **0**. Die
  Messung hatte keinen Nutzen gezeigt (Fehlstart p = 0,47, Quote p = 0,93), und der Keim kaeme
  aus dem Privileg - das in den Blick-Regelkreis zu lassen widerspricht
  [dem Projektziel](/ziel.md), ohne sich zu bezahlen. Der Schalter bleibt fuer die
  Reproduzierbarkeit stehen. Seite fortgeschrieben:
  [Keim im Rueckfall](/befunde/keim-im-rueckfall.md).

* **Anlage**: [Keim im Rueckfall](/befunde/keim-im-rueckfall.md) - auf Nutzerauftrag setzt der
  privilegierte Rueckfall jetzt auch einen Keim (`ACT23_KEIM_RUECKFALL`, Vorgabe 1). Die Luecke
  ist zu: **Episoden ohne Keim 10 -> 0**. Ein Nutzen ist **nicht nachweisbar** (Fehlstart
  2,9 -> 4,2 %, p = 0,47; Quote 52,9 -> 53,6 %, p = 0,93). Der Grund ist der eigentliche Ertrag:
  die sieben Rueckfall-Episoden sind **Verschmelzungsfaelle** - der gewaehlte Blob sitzt bei
  21 gegen 23 mm bzw. 19 gegen 23 mm fast genau zwischen zwei Koerpern. Gegen einen
  verschmolzenen Blob hilft kein Ortsanker. Der Keim ist privilegiert und wird deshalb als
  `Keim JA (PRIVILEGIERT)` protokolliert. Guenstiger Nebeneffekt: die 5-cm-Sprungschranke greift
  jetzt schon im ersten Bild.

* **Entscheidung**: `ACT23_KEIM_FIX` steht auf Nutzerentscheid jetzt auf **1** - der Tracker
  bekommt beim Eigenschafts-Kommando seinen Keim. Grundlage ist
  [Keim-Fix, A/B](/befunde/keim-fix-ab.md) (Fehlstarts unter mehrdeutigen Szenen 51,5 -> 6,7 %,
  p = 0,0001, beide Seeds gleichgerichtet). Ohne Umgebungsvariable geprueft: `Keim JA`, und der
  Schalter erscheint nicht mehr unter den Abweichungen. **Ausdruecklich nicht mitgekauft:** ein
  Quotengewinn (gepoolt 50,4 -> 52,9 %, p = 0,65). Rueckfall mit `ACT23_KEIM_FIX=0`.

* **Anlage**: [Keim-Fix, A/B](/befunde/keim-fix-ab.md) - der Schluesselfehler aus
  [Der Keim erreicht den Tracker nie](/befunde/keim-erreicht-tracker-nicht.md) ist hinter
  `ACT23_KEIM_FIX` (Vorgabe 0) repariert und gemessen. **Gepaarter Seed-Sweep** nach der Lehre
  aus [Zwei Laeufe sind dieselbe Rechnung](/befunde/laeufe-sind-reproduzierbar.md): 4 Laeufe je
  120 Episoden, zwei Seeds, ein Schnappschuss. Direkte Zielgroesse (Fehlstart unter mehrdeutigen
  Szenen) **51,5 -> 6,7 %, Fisher p = 0,0001**, beide Seeds gleichgerichtet; Keim greift 0 ->
  95/97 %. Lieferquote gepoolt 50,4 -> 52,9 %, **p = 0,65 - die eigene Hochrechnung von 3,5
  Punkten ist damit nicht bestaetigt**. Zwei benannte Restluecken: der privilegierte Rueckfall
  veroeffentlicht keinen Keim (3-5 % der Episoden), und die Kennzahl saettigt, wenn zwei Koerper
  wenige Millimeter auseinanderliegen. Vorgabe bleibt `0`.

## 2026-09-08

* **Anlage**: [Der Keim erreicht den Tracker nie](/befunde/keim-erreicht-tracker-nicht.md) - die
  Anschlussmessung zur Ablenker-Bindung, und sie findet einen **Schluesselfehler**: der
  Eigenschafts-Pfad veroeffentlicht die Erst-Wahrnehmung als `eig:{body}`, der Tracker fragt sie
  unter der Formklasse ab - **120 von 120 Episoden ohne Keim**. Der Tracker startet deshalb auf
  dem wahrscheinlichsten gleichklassigen Blob; bei mehreren Kandidaten (14,2 % der Episoden) sind
  das 41,2 % Fehlstarts, und **kein einziger Fehlstart wurde je geliefert** (0/8 gegen 67/112,
  Fisher p = 0,0011). Herkunft: `0d8c88f` - die "vier Stellen" des Eigenschafts-Kommandos waren
  fuenf. Neue Diagnose `ACT23_KEIMDIAG=1` (Vorgabe aus, rein messend). Reparaturvorschlag und
  geschaetzte Wirkung (~3,5 Punkte, Hochrechnung) stehen in der Seite; **nicht gebaut**.

* **Anlage**: [Der Tracker rastet auf dem Nachbarn ein](/befunde/ablenker-bindung-gemessen.md) -
  auf Nutzerauftrag der erste Schritt an der Ablenker-Bindung. Neue Diagnose
  `ACT16_ABLENKDIAG=1` (Vorgabe aus, privilegiert und rein messend wie `GLAUBDIAG`) zaehlt je
  Episode, auf welchen Koerper der Anfahr-Belief zeigt. Ergebnis ueber 64 Episoden: fremder
  Belief in 31,2 % der gescheiterten gegen 4,2 % der gelieferten Episoden, **Fisher p = 0,0086**
  - und der Belief steht dabei rund **4 mm** neben dem FALSCHEN Koerper, ist also eine sichere
  Bindung, keine Drift. In Episode 48 ab dem ersten Anfahrschritt. Damit ist die schwache
  Permutationskontrolle des Vorlaeuferbefunds ersetzt. Lauf bei 64 statt 150 Episoden beendet
  (Speichernot, GUI des Nutzers hatte Vorrang). Offen bleibt das **Warum** - naechster Schritt
  in der Seite benannt.

* **Anlage**: [Merkmale kommen zu spaet](/befunde/merkmale-kommen-zu-spaet.md) - bei der Suche
  nach naechsten Schritten ausgezaehlt: der Nachbar-Merkmalsblock ist auf **690 von 11563**
  Pufferzeilen gefuellt (6,0 %), der Rest traegt den neutralen "nie gemessen"-Wert. Die in
  [Exekutionsvarianz](/befunde/exekutionsvarianz.md) als "nicht pruefbar" vermerkte Frage ist
  nach 4800 weiteren Episoden immer noch fast nicht pruefbar. Auf den gueltigen Zeilen zeigt der
  Nachbarabstand ausserdem in die **unerwartete** Richtung (naeher = besser, vermutlich
  Lagen-Konfundierung). Folgerung fuer die Architektur: ein nachtraeglich eingefuehrtes Merkmal
  erreicht das Modell nicht - der Engpass ist die Zusammensetzung des Puffers.

* **Anlage**: [Zwei Laeufe sind dieselbe Rechnung](/befunde/laeufe-sind-reproduzierbar.md) - aus
  einer Nutzerbeobachtung in `run_history` ("die letzten drei Laeufe sehen extrem aehnlich aus").
  Sie sind nicht aehnlich: Arm B des Welt-Fit-A/B und der GUI-Lauf vom 08.09. sind ueber alle
  200 Episoden **identisch** - Szene, Objekt, Ausgang, Millimeter. Innerhalb eines Laufs
  wiederholt sich dagegen nichts (94,5 % verschiedene Szenen). Ein Lauf ist damit **eine**
  Stichprobe; die Replikate sind die Seeds.

* **Ergaenzung/Praezisierung**: [Rechnerlast](/befunde/rechnerlast.md) (die 26 Punkte sind
  Schwankung INNERHALB eines Laufs, es gibt keine Wiederholungsstreuung),
  [Kopfloses A/B](/messungen/act23-headless-ab.md) (die Seed-Warnung praeziser gefasst, plus die
  Regel "die Replikate sind die Seeds") und [Sparsamer Welt-Fit,
  A/B](/befunde/welt-fit-plan-ab.md) (beide Arme mit gleichem Seed - bis Ep 18 identisch,
  Reichweite enger als dargestellt).

* **Befund, nicht behoben**: ohne gesetztes `ACT23_SEED` meldet die Kopfzeile `SEED=11`,
  gefahren wird aber mit **7** (`_source_defaults()` nimmt den ersten von drei Treffern im
  Quelltext; die 11 stammt aus zwei Diagnose-Pruefstaenden, die im Steuerungslauf nicht laufen).
  Reproduktionsfalle fuer jeden Lauf ohne Seed. Eine Reparatur erzwingt eine Wahl und ist
  deshalb offen.

* **Entscheidung**: `ACT23_WORLD_FULL_EVERY` steht auf Nutzerentscheid jetzt auf **4** - der
  Welt-Fit laeuft nur noch jede vierte Episode voll, dazwischen 20 Epochen. Grundlage ist
  [das A/B](/befunde/welt-fit-plan-ab.md) (je 200 Episoden, p = 0,92, Selbst-Aneignung gleich,
  61 % mehr Episoden je Stunde). Ohne Umgebungsvariable geprueft: Lernphase 73,1 s voll gegen
  16,3-16,5 s kurz im Muster voll-kurz-kurz-kurz-voll. Sichtbare Alltagsfolge: drei von vier
  Kredit-Zeilen tragen jetzt `, Fit 20 Epochen`. Rueckfall in einer Zeile mit
  `ACT23_WORLD_FULL_EVERY=1`. Seite: [ACT23_WORLD_FULL_EVERY](/entscheidungen/welt-fit-plan.md).

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
