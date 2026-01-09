# Analyse-Bericht: Musiknutzungs-Trends (Woche 1)

## 1. Datenbasis & Bereinigung

Der Datensatz umfasst die globalen Spotify-Charts von Januar 2024 bis Dezember 2025.

* **Volumen:** ~21.000 Datenpunkte (Top 200 pro Woche).
* **Bereinigung:** Normalisierung von Künstlernamen, Behandlung von Neueinsteigern (previous_rank) und Extraktion der Zeitreihen aus Dateinamen.

## 2. Identifizierte Marktdynamiken

Durch die statistische Ausreißer-Analyse (Threshold: > 1.5 std) wurden 6 signifikante Peaks identifiziert:
### A. Der "Superstar-Schock" (Event-Releases)

* **Zeitraum:** April 2024 & Oktober 2025.
* **Dynamik:** Massive Peaks getrieben durch Taylor Swift. Im April 2024 generierte allein "Fortnight" über 102 Mio. Streams.
* **Erkenntnis:** Ein einziger Artist kann das globale Streaming-Volumen kurzzeitig massiv heben. Der "Top 1 Share" stieg im Okt. 2025 auf rekordverdächtige 4.02%.

### B. Zyklische Saisonalität (Weihnachtshits)

* **Zeitraum:** Dezember 2024 & 2025.
* **Dynamik:** Vorhersehbare Rückkehr von Klassikern wie Mariah Carey und Wham!.
* **Erkenntnis:** Während die Streams im Dezember Rekordwerte erreichen (z.B. 92,5 Mio. für Mariah Carey 2024), sinkt die Varianz. Der Markt konzentriert sich auf wenige Katalog-Titel.

### C. Organisches Sommer-Wachstum

* **Zeitraum:** Mai – August.
* **Dynamik:** Breitere Plateaus statt scharfer Peaks. Vielfältige Top 5 mit Künstlern wie Tommy Richman, Billie Eilish und Sabrina Carpenter.
* **Erkenntnis:** Dies ist die "gesündeste" Marktphase mit hartem Wettbewerb um den Sommerhit und einem relativ niedrigen Top 1 Share (2.23% im Mai 2024).

## 3. Analyse der Top-Künstler & Diversität

Das Wechselspiel zwischen Streaming-Volumen und künstlerischer Vielfalt zeigt zwei gegensätzliche Phänomene:

### A. Der "Superstar-Effekt" (Monokultur-Peaks)

Im April 2024 und Oktober 2025 schießen die Streams in den Top 10 massiv in die Höhe (bis zu 700M Streams), während die Diversität zeitgleich einbricht.

* **Interpretation:** Der rote Balken im Okt. 2025 in der Diversitäts-Grafik zeigt nur ca. 2–3 verschiedene Künstler in den Top 10.
* **Ergebnis:** Ein Blockbuster-Release dominiert den Markt so stark, dass die Vielfalt kollabiert, da ein einzelner Artist fast alle Top-Plätze belegt.

### B. Die "Saisonale Katalog-Dominanz" (Weihnachten)

Um den Jahreswechsel sehen wir die höchsten Volumen-Peaks des gesamten Datensatzes.

* **Interpretation:** Die Diversität sinkt hier ebenfalls (gelbe/hellgrüne Bereiche), erreicht jedoch nicht die extrem niedrigen Werte der Superstar-Releases.
* **Ergebnis:** Kollektives Nutzerverhalten führt zu einer Marktverengung auf bekannte Klassiker, was die Charts jährlich "monotoner" macht.

### C. Die "Gesunde" Marktphase (Sommer-Plateaus)

Zwischen Juli und September (2024 & 2025) zeigt sich ein stabilisiertes Bild.

* **Volumen:** Die Kurve verläuft flacher ohne extreme Ausreißer.
* **Diversität:** Die Balken sind fast durchgehend dunkelgrün und berühren die "Max. Diversität"-Linie von 10 verschiedenen Künstlern.
* **Ergebnis:** Der Sommer ist die Zeit des echten Wettbewerbs ohne einzelnen Dominator.

## 4. Wachstumsdynamik & Nachhaltigkeit (Trend-Analyse)

Zusätzlich zum Volumen haben wir die Geschwindigkeit des Markterfolgs analysiert:

**Wachstums-Explosionen (Growth Rate):**
* **Identifikation von viralen Ereignissen:** Durch die Berechnung der prozentualen Veränderung zum Vorwert (pct_change) konnten wir Sprünge von über 500% bis 1000% isolieren.
* **Erkenntnis:** Diese "Explosionen" sind fast ausnahmslos an Major-Releases oder virale TikTok-Trends gekoppelt, während etablierte Hits oft konstante Wachstumsraten nahe 0% aufweisen.

**Trend-Glättung (4-Wochen Rolling Mean):**
* **Unterscheidung von Hype vs. Nachhaltigkeit:** Der gleitende Durchschnitt des Marktanteils zeigt, ob ein Künstler ein "One-Hit-Wonder" ist oder sich stabilisiert.
* **Beobachtung:** Während Taylor Swift nach Release-Peaks schnell an Anteil verliert, zeigen Künstler wie Sabrina Carpenter (Sommer 2024) stabilere Plateaus über mehrere Wochen.

## 5. Strategische Implikationen für die ML-Modellierung (Woche 2)

Basierend auf diesen Erkenntnissen werden für die Modellierungsphase folgende Maßnahmen getroffen:

* **Anomalie-Erkennung:** Identifikation von "Schockwellen-Events" (wie Okt. 2025), um das Modell gegen extreme Ausreißer zu stabilisieren.
* **Saisonalität als Prädiktor (Holiday-Flag):** Nutzung der Kalenderwoche als starkem Prädiktor, um die zyklischen Einbrüche der Diversität an Weihnachten abzubilden und Fehlerprognosen im Dezember zu vermeiden.
* **Genre-Hypothese:** Verifizierung der "grünen Wochen" (hohe Diversität) vs. "roter Wochen" (Monokultur) durch Anreicherung mit Genre-Daten via Spotify Web API in Woche 2.
* **Rolling Means & Lags:** Glättung kurzfristiger Hypes, um nachhaltige Trends von "Eintagesfliegen" zu unterscheiden. Der berechnete 4-Wochen-Schnitt wird als technisches Feature genutzt, da er eine deutlich höhere prädiktive Kraft für die Folgewoche besitzt als der reine Wochenwert.
* **Growth-Momentum:** Einführung einer Variable für "Virale Dynamik", um plötzliche Aufwärtstrends mathematisch für das Modell greifbar zu machen.