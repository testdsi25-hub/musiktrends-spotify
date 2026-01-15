# 🎵 Musiknutzungs‑Trends & KI‑basierte Vorhersagen  
**Analyse von Spotify‑Charts, API‑Metadaten, Machine Learning & interaktivem Dashboard**

---

## 📅 Roadmap (Aktueller Stand des Projekts)
- [x] Woche 1: CSV‑Daten + Exploration  
- [x] Woche 2: API‑Daten + Modellierung  
- [ ] Woche 3: Dashboard + Storytelling

---

## 📌 Projektübersicht
Dieses Projekt untersucht Musiknutzungstrends anhand von Spotify‑Daten. Dazu werden **Charts‑CSVs**, **Spotify Web API‑Metadaten**, **Feature Engineering**, **Forecast‑Modelle** und ein **Plotly‑Dashboard** kombiniert. Ziel ist ein vollständiges **End‑to‑End Data‑Science‑Portfolio‑Projekt**, das Daten, KI und Storytelling verbindet.

💡 **Technical Note:** Aufgrund von API-Einschränkungen bei Spotify Ende 2024 (Einstellung des freien Zugriffs auf audio-features) wurde das Feature Engineering gezielt auf Artist-Metadaten und Genre-Trends umgestellt. Es hat sich gezeigt, dass Fanbase-Metriken (Follower) und Genre-Cluster stabilere Prädiktoren für Charterfolge sind als rein akustische Merkmale.

---

## 🚀 Features
- Analyse von Spotify‑Charts (CSV‑Daten)
- Abruf von Metadaten über die Spotify Web API (Fokus auf Artist-Metrics & Genres)
- Feature Engineering (Genre Popularity Index, Artist Growth Rate, Seasonality Score)
- Zeitreihen‑Forecasts (Prophet)
- Klassifikation von „Rising Artists“ (LightGBM)
- Interaktives Dashboard (Streamlit)
- Automatisch generierte Trendberichte (LLM‑Integration über Gemini-API)
- Vollständig reproduzierbar via Docker

---

## 📁 Projektstruktur
```
musiktrends-spotify/
│
├── data/          # Rohdaten, CSVs, API-Downloads (aktuell noch nicht verfügbar)
├── docs/          # Dokumentation, Diagramme, Berichte
├── models/        # Modelle (Prophet, LightGBM)
├── notebooks/     # Jupyter Notebooks für Exploration & Modellierung
├── src/           # Python-Module (Pipelines, Modelle, Utils)
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── README.md
└── requirements.txt
```

---

## 🗂️ Datenquellen
### **Spotify Charts (CSV)**
- Quelle: Spotify Weekly Top Songs Global (https://charts.spotify.com/charts/view/regional-global-weekly)
- Zeitraum:  2024–2025
- Frequenz: Weekly (TOP 200)
- Felder: chart_week, rank,	uri, artist_names, track_name, peak_rank, previous_rank, weeks_on_chart, streams
- Preprocessing:
    - Konsolidierung der Rohdaten: Alle wöchentlichen CSV-Dateien werden zu einer einzigen Tabelle zusammengeführt (Concatenation).
    - Standardisierung der Struktur: Spaltennamen werden vereinheitlicht, Datentypen harmonisiert und fehlende Werte behandelt.
    - Feature-Selektion: Es werden nur die für die Analyse relevanten Spalten beibehalten, siehe Felder.
    - Bereinigung: Daten wurden auf Duplikate, fehlerhafte Einträge und nicht benötigte Metadaten geprüft.
    - Export: Speicherung der bereinigten Gesamttabelle unter "data/processed" als Grundlage für die weitere Analyse.

### **Spotify Web API**
- Künstler‑Metadaten  
- ~~ Audio‑Features ~~ (Ersetzt durch erweiterte Artist-Metriken, siehe Note oben)  
- Popularität & Follower  
- Genre‑Informationen  

---

## 🧠 Modellierung
### **Zeitreihen‑Forecasts**
- Prophet  
 
### **Klassifikation**
- Random Forest (nur in der Entwicklungsumgebung)
- LightGBM 

---

## 📊 Dashboard
Das interaktive Dashboard zeigt:
- Genre‑Heatmaps  
- Forecast‑Kurven  
- KPIs für „Rising Artists“  
- Automatisch generierte Trendberichte  

---

## 🐳 Docker Setup

Dieses Projekt nutzt Docker, um eine konsistente Entwicklungsumgebung bereitzustellen. Dank **Docker Compose** werden alle Code-Änderungen auf deinem lokalen Rechner (Desktop) sofort mit dem Container synchronisiert, sodass du direkt im Browser arbeiten kannst.

### Voraussetzungen

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installiert und gestartet.
* Eine `.env`-Datei im Hauptverzeichnis mit deinen API-Credentials (siehe `.env.example`).

### 🔐 Beispiel `.env.example`

```env
# Spotify API Credentials
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Google Gemini API Key
GOOGLE_API_KEY=your_gemini_api_key
```

### Container bauen & starten

Öffne dein Terminal im Projektordner und führe folgenden Befehl aus. Dies installiert alle Abhängigkeiten aus der `requirements.txt`:
```
docker compose up --build
```

### Im Browser arbeiten 

Sobald der Container läuft, sind folgende Dienste verfügbar:

| Dienst | URL | Zweck |
|---------|---------|---------|
| 📊 Dashboard | [http://localhost:8501](http://localhost:8501) | Interaktive Visualisierung mit Streamlit |
| 📓 Jupyter | [http://localhost:8888](http://localhost:8888) | Exploration & Modellierung in Notebooks |

### Wichtige Befehle

* **Hintergrund-Modus:** ```docker compose up -d``` (Terminal bleibt frei).
* **Logs einsehen:** ```docker compose logs -f``` (hilfreich bei Fehlern).
* **Stoppen:** ```docker compose down``` (beendet beide Dienste).
* **Aufräumen:** ```docker image prune -f``` (entfernt veraltete Image-Versionen).

---

## 🛠 Installation (lokal)
```
pip install -r requirements.txt
```

---

## 📄 Lizenz
MIT License 

---

## 🤝 Mitwirken
Pull Requests und Issues sind willkommen.

