import os
import pandas as pd
import streamlit as st
import plotly.express as px

from src.extraction_unique_entities import prepare_unique_tracks
from src.spotify_client import SpotifyClient
from src.features import build_features, generate_trend_report
from src.predict_pipeline import run_prediction_pipeline


# ------------------------------------------------------------
# Seiteneinstellungen
# ------------------------------------------------------------
st.set_page_config(
    page_title="Spotify Rising Artist Predictor",
    page_icon="🎵",
    layout="wide"
)

# ------------------------------------------------------------
# Modell-Check
# ------------------------------------------------------------
MODEL_FILES = {
    "Prophet": "models/market_trend_prophet_v1.json",
    "LightGBM": "models/rising_artist_lgbm_v1.txt",
    "Threshold": "models/rising_artist_threshold.json",
    "Feature Columns": "models/rising_artist_features.json"
}

def check_models():
    missing = [name for name, path in MODEL_FILES.items() if not os.path.exists(path)]
    return missing

missing_models = check_models()

# ------------------------------------------------------------
# UI Header
# ------------------------------------------------------------
st.title("🎵 Musiktrends: Rising Artist Radar")

st.markdown("""
Dieses Dashboard nutzt **Prophet** für Makro-Trends und **LightGBM** zur Identifizierung 
von Newcomern mit hohem Aufstiegspotenzial.
""")

# Sidebar
st.sidebar.header("Systemstatus")
if missing_models:
    st.sidebar.error("Fehlende Modelle:")
    for m in missing_models:
        st.sidebar.write(f"• {m}")
else:
    st.sidebar.success("Alle Modelle erfolgreich geladen.")

# ------------------------------------------------------------
# Datei-Upload 
# ------------------------------------------------------------
st.subheader("Neue Chart-Daten hochladen")
uploaded_file = st.file_uploader(
    "Wähle die aktuelle Spotify-Charts CSV (Download von charts.spotify.com)",
    type="csv"
)

if uploaded_file is None:
    st.info("Bitte lade eine CSV-Datei hoch, um die Analyse zu starten.")
    st.stop()

# ------------------------------------------------------------ 
# Datei speichern 
# ------------------------------------------------------------
RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

temp_path = f"{RAW_DIR}/{uploaded.name}"

with open(temp_path, "wb") as f:
    f.write(uploaded_file.getbuffer())

st.success(f"Datei gespeichert unter: {temp_path}")

# ------------------------------------------------------------ 
# Schritt 1: Unique Tracks extrahieren 
# ------------------------------------------------------------
st.subheader("1. Unique Tracks extrahieren")

unique_path, date_str = prepare_unique_tracks(temp_path)

st.success(f"Unique Tracks gespeichert unter: {unique_path}")

# ------------------------------------------------------------ 
# Schritt 2: Spotify Enrichment Pipeline 
# ------------------------------------------------------------
st.subheader("2. Spotify Enrichment starten")

if st.button("🚀 Enrichment starten"):
    with st.spinner("Hole Spotify-IDs und Metadaten..."):
        client = SpotifyClient()

        df_enriched = client.run_full_pipeline(
            unique_tracks_csv=unique_path,
            date_str=date_str,
            output_dir="data/interim"
        )

    st.success("Enrichment abgeschlossen!")
    
    st.write("Vorschau der angereicherten Daten:")
    st.dataframe(df_enriched.head())

    # -------------------------------------------------------- 
    # Schritt 3: Feature Engineering 
    # -------------------------------------------------------- 
    st.subheader("3. Feature Engineering") 
    
    df_features = build_features(df_enriched) 
    df_features["ds"] = pd.to_datetime(df_features["chart_week"], errors="coerce") 
    
    st.success("Feature Engineering abgeschlossen.")

    # -------------------------------------------------------- 
    # Schritt 4: Prediction Pipeline 
    # -------------------------------------------------------- 
    st.subheader("4. KI‑Vorhersagen") 
    
    preds, probs = run_prediction_pipeline(df_features) 
    
    df_features["is_rising"] = preds 
    df_features["probability"] = probs 
    
    st.success("Vorhersagen berechnet.")

    # -------------------------------------------------------- 
    # Schritt 5: TOP‑10 Rising Artists 
    # -------------------------------------------------------- 
    st.subheader("🔥 TOP 10 Rising Artists") 
    
    df_top10 = df_features.sort_values("probability", ascending=False).head(10) 
    
    st.dataframe(df_top10[[ 
        "artist_names", "track_name", "probability", 
        "track_popularity", "artist_followers", "genre_pop_idx" 
    ]])

    # -------------------------------------------------------- 
    # Dashboard-Bereich 
    # -------------------------------------------------------- 
    st.subheader("📊 Dashboard – Überblick") 
    
    col1, col2, col3 = st.columns(3) 
    with col1: 
        st.metric("Anzahl Tracks", len(df_features)) 
    with col2: 
        st.metric("Identifizierte Rising Artists", int(df_features["is_rising"].sum())) 
    with col3: 
        st.metric( 
            "Max. Rising-Wahrscheinlichkeit", 
            f"{df_features['probability'].max():.2f}" if len(df_features) > 0 else "–" 
        ) 
    # Plot: Top 10 Rising Artists 
    if df_top10.empty: 
        st.warning("Keine Rising Artists mit positiver Vorhersage gefunden.") 
    else: 
        st.markdown("### 🎤 Top 10 – Modellwahrscheinlichkeiten") 
        
        fig = px.bar( 
            df_top10, 
            x="probability", 
            y="track_name", 
            color="artist_names", 
            orientation="h", 
            title="Top 10 Rising Artists (Modellwahrscheinlichkeiten)", 
            labels={ 
                "probability": "Wahrscheinlichkeit", 
                "track_name": "Track", 
                "artist_names": "Artist" 
            } 
        ) 
        
        fig.update_layout( 
            yaxis={"categoryorder": "total ascending"}, 
            template="plotly_dark" 
        ) 
        
        st.plotly_chart(fig, use_container_width=True) 

    # -------------------------------------------------------- 
    # Schritt 6: Trendbericht
    # -------------------------------------------------------- 
    st.subheader("📈 Trendbericht") 
    
    for _, row in df_top10.iterrows(): 
        report = generate_trend_report(row) 
        st.markdown(report) 
        st.markdown("---") 
        
    # -------------------------------------------------------- 
    # Historische Daten aktualisieren (Nur Metadaten!)
    # --------------------------------------------------------

    st.subheader("📦 Daten an Historie anhängen")

    if st.checkbox("Neue Woche an historische Daten anhängen"): 
        try: 
            HIST_PATH = "data/processed/final_data_with_metadata.csv" 
            os.makedirs("data/processed", exist_ok=True) 
            
            # Historische Datei laden oder neu erstellen 
            if os.path.exists(HIST_PATH): 
                df_hist = pd.read_csv(HIST_PATH) 
            else: 
                st.warning("Historische Datei existiert nicht. Sie wird neu erstellt.") 
                df_hist = pd.DataFrame() 
            
            # Nur Metadaten übernehmen 
            allowed_cols = [ 
                "chart_week", 
                "rank", 
                "artist_names", 
                "track_name", 
                "peak_rank", 
                "previous_rank", 
                "weeks_on_chart", 
                "streams", 
                "track_id", 
                "artist_id", 
                "release_date", 
                "explicit", 
                "track_popularity", 
                "artist_genres", 
                "artist_followers", 
                "artist_popularity" 
            ] 
            
            df_to_append = df_enriched.copy() 
            df_to_append = df_to_append[[c for c in allowed_cols if c in df_to_append.columns]] 
            
            # Historie und neue Daten kombinieren 
            df_updated = pd.concat([df_hist, df_to_append], ignore_index=True) 
            
            # Dubletten entfernen (Track + Woche) 
            df_updated = df_updated.drop_duplicates( 
                subset=["track_id", "chart_week"], keep="last" 
            ) 
            
            df_updated.to_csv(HIST_PATH, index=False) 
            
            st.success(f"Neue Woche erfolgreich gespeichert unter:\n**{HIST_PATH}**") 
        
        except Exception as e: 
            st.error(f"Fehler beim Aktualisieren der historischen Daten: {e}")