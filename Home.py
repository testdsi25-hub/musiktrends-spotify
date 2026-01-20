import streamlit as st

st.set_page_config(
    page_title="Musiknutzungs-Trends & KI",
    page_icon="🎵",
    layout="wide"
)

# ------------------------------------------------------------
# Hero Banner
# ------------------------------------------------------------
st.markdown("""
<div style="
    padding: 3rem 2rem;
    background: linear-gradient(90deg, #1DB954 0%, #191414 100%);
    border-radius: 12px;
    color: white;
    margin-bottom: 2rem;
">
    <h1 style="margin-bottom: 0.3rem;">🎵 Musiknutzungs‑Trends & KI‑basierte Vorhersagen</h1>
    <h3 style="font-weight: 400; margin-top: 0;">
        Ein datengetriebenes End‑to‑End‑Projekt über moderne Musiktrends.
    </h3>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Elevator Pitch
# ------------------------------------------------------------
st.markdown("""
## 🚀 Elevator Pitch

**Musik wird heute von Daten gesteuert.** Streaming‑Plattformen wie Spotify prägen, welche Künstler sichtbar werden und welche Trends sich durchsetzen. Mit **„Musiknutzungs‑Trends & KI‑basierte Vorhersagen“** entsteht ein vollständiges Data‑Science‑Ökosystem, das diese Dynamiken analysiert, erklärt und vorhersagbar macht.

In nur drei Wochen ist ein End‑to‑End‑Projekt entstanden, das zeigt, wie **Datenanalyse, KI‑Modelle und Storytelling** zusammenwirken.
""")

# ------------------------------------------------------------
# Exploration
# ------------------------------------------------------------
st.markdown("""
### 🔍 Exploration
Analyse der Spotify‑Charts (CSV‑Daten) mit Pandas, um Muster in Genres, Wachstumskurven und Nutzerverhalten sichtbar zu machen.

Leitfragen:
- Warum gehen manche Songs viral?
- Warum dominieren manche Künstler plötzlich alles?
- Warum wird der Markt im Sommer vielfältiger?
- Sind diese Muster vorhersagbar?

Datenquelle:
- Spotify Weekly Top Songs Global ('https://charts.spotify.com/charts/view/regional-global-weekly/latest')
- Zeitraum: 01/2024 bis 12/2025

""")

# ------------------------------------------------------------
# Modellierung
# ------------------------------------------------------------
st.markdown("""
### 🤖 Modellierung
- Erweiterung der Datenbasis über die Spotify Web API (Genres, Popularität, Follower)  
- Zeitreihen‑Forecasts für Playcounts (**Prophet**)  
- Klassifikations‑ und Boosting‑Modelle zur Identifikation von **Rising Artists** (LightGBM)
""")

# ------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------
st.markdown("""
### 📊 Dashboard & Storytelling
Ein interaktives Dashboard zeigt:
- Die Marktmechaniken
- Zentrale Muster & Dynamiken

Der Rising Artist Radar kombiniert:
- Heatmaps  
- Forecast‑Kurven  
- KPIs  
- automatisch generierte Trendberichte (Gemini‑API)

Das gesamte Projekt läuft reproduzierbar in Docker und ist vollständig auf GitHub dokumentiert – inklusive Code, Pipelines, Modellen und Dashboard.
""")

st.markdown("---")

st.info("👉 Nutze die Navigation links, um zur Analyse oder zum Rising Artist Radar zu wechseln.")
