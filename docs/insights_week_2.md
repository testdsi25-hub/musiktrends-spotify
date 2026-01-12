# Analyse-Bericht: Zeitreihen-Analyse & Modell-Validierung (Woche 2)

## 1. Auswertung der Prophet-Komponenten

Die Zerlegung der Zeitreihe liefert tiefe Einblicke in die Mechanik des Streaming-Marktes:

* **Trend:** Starker Anstieg bis Mitte 2024, gefolgt von einer Stabilisierung ab 2025 auf einem hohen Plateau. Dies repräsentiert das "Grundrauschen" des Marktes nach einem massiven Wachstumsschub.
* **Holidays:** Massive Ausschläge (>30 %) durch Taylor Swift Releases und Weihnachten.
* **Yearly:** Kollektives Hörverhalten mit Sommer-Tief und Dezember-Peak.
* **Extra Regressors (Genre Popularity Index):** Zeigt den massiven Einfluss von Genre-Hypes auf das Gesamtvolumen.
* **Gesamt-Forecast:** Das Modell kombiniert historische Daten mit der Schätzung. Es erklärt extreme Spitzen präzise durch die Holiday-Komponente und liefert eine valide Prognose für die kommenden Wochen.

## 2. Interpretation der Modellparameter & Metriken

Durch Hyperparameter-Tuning wurden optimale Einstellungen gefunden:

* **Flexibilität:** `changepoint_prior_scale = 0.5` erlaubt schnelle Reaktionen auf volatile Marktänderungen.
* **Präzision:** Mit einem **MAPE von 0.06 (6 % Fehler)** liegt das Modell im „Goldstandard-Bereich“. Der **RMSE von ~188 Mio.** ist bei einem Milliarden-Gesamtvolumen vernachlässigbar gering (absoluter Fehler entspricht etwas 5%). Die statistische Validierung bestätigt die hohe Güte des Modells.

Das entwickelte Modell sagt globale Streaming-Trends mit einer **Genauigkeit von 94 %** vorher. Es erkennt, dass der Markt zwar stabil ist, aber massiv durch Events und Genre-Dynamiken gesteuert wird.

## 3. Modell-Evolution: Von Random Forest zu LightGBM

Um subtile Muster und unbalancierte Klassen (Rising Artists als Minderheit) besser zu erfassen, wurde das Modell auf LightGBM umgestellt.

### Der Performance-Sprung

| Metrik (Klasse 1) | Random Forest | LightGBM (Opt. Threshold) | **Veränderung** |
| --- | --- | --- | --- |
| Precision | 0.67 | 0.65 | -2 % |
| **Recall** | 0.56 | **0.65** | **+9 % (Durchbruch)** |
| **F1-Score** | 0.61 | **0.65** | **+4 % (Gesamtsieg)** |

Durch die Senkung des Entscheidungs-Thresholds auf 0.36 identifiziert das Tool nun 65 % aller potenziellen Aufsteiger (Recall), was für A&R-Manager einen massiven Mehrwert bietet.

### Die neue Feature-Hierarchie

LightGBM gewichtet die Faktoren intelligenter als der Random Forest:

1. **`genre_pop_idx` (Platz 1):** Das Genre ist das Fundament; Künstler steigen meist auf einer „Genre-Welle“ auf.
2. **`artist_growth_rate`:** Bleibt der entscheidende Motor für individuelles Momentum.
3. **`prophet_trend`:** Das Zeitreihen-Modell liefert den nötigen makroökonomischen Kontext.

## 4. Explainable Artificial Intelligence-Insights (SHAP-Analyse)

Die SHAP-Analyse macht die „Blackbox“ LightGBM transparent:

* **Wachstum:** Es besteht ein klarer linearer Zusammenhang zwischen Momentum und Aufstiegswahrscheinlichkeit.
* **Markt-Barrieren:** Ein schwacher Genre-Index zieht die Erfolgswahrscheinlichkeit aktiv nach unten („totes Genre“).
* **Newcomer-Logik:** Hohe Track-Popularität wirkt oft negativ auf das „Rising“-Label, da das Modell lernt, zwischen etablierten Stars und echten Newcomern zu unterscheiden.

## 5. Top 10 Rising Artists & Trendbericht

Die aktuelle Vorhersage zeigt eine Dominanz von Titeln mit einer Aufstiegswahrscheinlichkeit von nahezu 1.00 (100 %):

* **Sabrina Carpenter – 'Taste':** Profitiert von einer extremen Genre-Dynamik (79.64) bei starkem Eigen-Momentum (4.10).
* **Billie Eilish – 'BIRDS OF A FEATHER':** Absolute Marktführerin mit Genre-Werten bis zu **88.14**.
* **Jimin – 'Who':** Höchstes individuelles **Artist-Momentum (6.09)** im Testfeld, was auf eine massive Fan-Power hindeutet.
* **KPop Demon Hunters – 'Golden':** Ein klassischer „Hype-Rider“ mit extrem hoher Genre-Dynamik (85.97), aber moderatem Eigen-Momentum.

## Fazit

* **Prophet** liefert das „Spielfeld“ und sagt globale Markttrends mit einer Genauigkeit von 94 % (MAPE: 0,06) voraus.

* **LightGBM** agiert als „Talentscout“ auf diesem Spielfeld: Durch den optimierten Threshold (0,36) identifiziert es 65 % aller tatsächlichen Rising Artists (Recall).

&rarr; Die Kombination ermöglicht es, individuelle Künstler-Erfolge (Mikro-Ebene) immer im Kontext der allgemeinen Marktdynamik (Makro-Ebene) zu bewerten.





