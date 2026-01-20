import os
import ast
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import time
import math

# ____ Pipeline-Module _____
from src.extraction_unique_entities import prepare_unique_tracks
from src.spotify_client import SpotifyClient
from src.merge_dataframes import merge_new_data
from src.features import build_features, genre_parser
from src.predict_pipeline import run_prediction_pipeline
from src.trend_reports import generate_gemini_report

# ------------------------------------------------------------ 
# Basisverzeichnisse 
# ------------------------------------------------------------ 
BASE_DIR = Path(__file__).resolve().parents[1] 
DATA_DIR = BASE_DIR / "data" 
RAW_DIR = DATA_DIR / "raw" 
INTERIM_DIR = DATA_DIR / "interim" 
PROCESSED_DIR = DATA_DIR / "processed" 
BACKUP_DIR = DATA_DIR / "backups" 
MODEL_DIR = BASE_DIR / "models" 

for d in [RAW_DIR, INTERIM_DIR, BACKUP_DIR]: 
    d.mkdir(parents=True, exist_ok=True)

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

missing_models = [name for name, path in MODEL_FILES.items() if not Path(path).exists()]

# ------------------------------------------------------------
# UI Header
# ------------------------------------------------------------
st.title("🎵 Musiktrends: Rising Artist Radar")

st.markdown("""
Entdecken Sie, welche Künstler gerade an Fahrt aufnehmen. Unsere KI analysiert aktuelle Chartdaten und erkennt frühzeitig, welche Newcomer das Potenzial haben, ganz groß zu werden.
""")

# Sidebar
st.sidebar.header("🔧 Systemstatus")
if missing_models:
    st.sidebar.error("Modelle konnten nicht geladen werden:")
    for m in missing_models:
        st.sidebar.write(f"• {m}")
else:
    st.sidebar.success("System bereit!")
    st.sidebar.caption("Alle Modelle geladen.")

# ------------------------------------------------------------
# Datei-Upload 
# ------------------------------------------------------------
st.header("📁 Neue Chart-Daten hochladen")
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
# Dateiname für raw_ "_origin" anhängen
file_path_raw = Path(uploaded_file.name)
origin_name = f"{file_path_raw.stem}_origin{file_path_raw.suffix}"

# Ursprungsdatei ohne Änderung in raw
raw_path = RAW_DIR / origin_name

with open(raw_path, "wb") as f: 
    f.write(uploaded_file.getbuffer())

st.success(f"Datei wurde erfolgreich hochgeladen.")
st.caption(f"Speicherort der Originaldatei: `{raw_path}`")

# ------------------------------------------------------------ 
# Schritt 1: Unique Tracks extrahieren 
# ------------------------------------------------------------
st.subheader("🔍 Titel & Künstler automatisch erkennen")

processed_path, unique_path, date_str = prepare_unique_tracks(
    input_path=raw_path, 
    processed_dir=PROCESSED_DIR, 
    output_dir=INTERIM_DIR
)

st.success(f"Titel und Künstler wurden erkannt und gespeichert.")
st.caption(f"Verarbeitete Datei gespeichert unter: `{processed_path}`") 
st.caption(f"Unique-Track-Datei gespeichert unter: `{unique_path}`")

# ---------------------------------------------------------------- 
# Schritt 2: Spotify Enrichment Pipeline mit anschließendem Merge 
# ----------------------------------------------------------------
st.subheader("🎼 Spotify-Daten erweitern")

if st.button("🎧 Spotify-Infos laden"):
    with st.spinner("Hole Spotify-IDs und Metadaten..."):
        client = SpotifyClient()

        df_enriched = client.run_full_pipeline(
            unique_tracks_csv=unique_path,
            date_str=date_str,
            output_dir=INTERIM_DIR
        )
    st.success("Die Titel wurden erfolgreich mit Spotify-Infos angereichert.")

    # ------------------------------------------------------------ 
    # Schritt 3: Merge: Charts + enriched_data + Historie 
    # ------------------------------------------------------------
    
    df_final = merge_new_data(
        charts_csv=PROCESSED_DIR / f"regional_global_weekly_{date_str}.csv", 
        enriched_csv=INTERIM_DIR / f"enriched_data_{date_str}.csv", 
        date_str=date_str, 
        processed_dir=PROCESSED_DIR, 
        hist_path=PROCESSED_DIR / "hist_data_24-25.csv", 
        backup_dir=BACKUP_DIR
    )

    st.success("Die neuen Daten wurden erfolgreich mit der Historie verbunden.")
    
    st.write("Vorschau der angereicherten Daten:")
    st.dataframe(df_final.tail())
    
    # -------------------------------------------------------- 
    # Schritt 4: Feature Engineering 
    # -------------------------------------------------------- 
    st.header("🧠 Daten verarbeiten")
    st.subheader("🧩 Merkmale berechnen") 
    
    df_features = build_features(df_final) 
    df_features["ds"] = pd.to_datetime(df_features["chart_week"], errors="coerce") 
    
    st.success("Die Daten wurden erfolgreich aufbereitet.")

    # -------------------------------------------------------- 
    # Schritt 5: Prediction Pipeline 
    # -------------------------------------------------------- 
    st.subheader("🤖 KI‑Vorhersage starten") 
    
    preds, probs = run_prediction_pipeline(df_features) 
    
    df_features["is_rising"] = preds 
    df_features["probability"] = probs 

    st.session_state["df_features"] = df_features
    
    st.success("Die KI-Vorhersagen sind bereit.")

# ------------------------------------------------------------ 
# Dashboard (Visualisierungen)
# ------------------------------------------------------------
st.header("📊 Analyse & Visualisierung")

if "df_features" not in st.session_state:
    st.info("Bitte lade zuerst Spotify-Infos und starte die KI-Vorhersage.")
    st.stop()

df_display = st.session_state["df_features"].copy()

# KPI-Bereich
col1, col2, col3 = st.columns(3)
col1.metric("Analysierte Tracks", f"{len(df_display):,}")
col2.metric("Rising Artists", (df_display['probability'] >= 0.9).sum())
col3.metric("Max. Wahrscheinlichkeit", f"{df_display['probability'].max():.2%}")

st.divider()

# Heatmap 
if "artist_genres" in df_display.columns:
    st.subheader("🔥 Genre Trend Heatmap")

    # Kopie für die Heatmap erstellen, um df_display nicht für andere Charts zu verändern
    df_heatmap = df_display.copy()
    
    # Sicherstellen, dass Genres Listen sind (falls sie als Strings gespeichert wurden)
    df_heatmap["artist_genres"] = df_heatmap["artist_genres"].apply(genre_parser)
    
    # Explode: Erstellt pro Genre eine eigene Zeile
    df_heatmap = df_heatmap.explode("artist_genres")

    # Ungültige Genres entfernen
    df_heatmap = df_heatmap.dropna(subset=["artist_genres"])
    df_heatmap = df_heatmap[df_heatmap["artist_genres"] != ""]
    
    # Aggregation: Durchschnittliche Wahrscheinlichkeit pro Woche und Genre
    genre_trend = (
        df_heatmap.groupby(["ds", "artist_genres"])["probability"]
        .mean()
        .reset_index()
        .sort_values("ds")
    )

    # Nur Top-Genres anzeigen (optional, verhindert eine zu lange Y-Achse)
    top_genres = (
        genre_trend.groupby("artist_genres")["probability"]
        .sum()
        .nlargest(20)
        .index
    )
    genre_trend = genre_trend[genre_trend["artist_genres"].isin(top_genres)]

    # Heatmap erzeugen
    fig_heatmap = px.density_heatmap(
        genre_trend, 
        x="ds",
        y="artist_genres",
        z="probability",
        color_continuous_scale="Viridis",
        labels={
            'probability': 'Trend-Stärke', 
            'artist_genres': 'Genre',
            'ds': 'Datum'
        },
        title="Genre-Momentum über die Zeit"
    )

    fig_heatmap.update_coloraxes(colorbar_title="Kumulierte Trendstärke")

    st.plotly_chart(fig_heatmap, use_container_width=True)

# TOP 10 Rising Artists
st.subheader("🏆 Top 10 Rising Artists")

df_display_unique = (
    df_display.sort_values("probability", ascending=False)
        .drop_duplicates(subset=["artist_names", "track_name"])
)

top_10 = df_display_unique.nlargest(10, "probability")

fig_bar = px.bar(
    top_10,
    x="probability",
    y="track_name",
    color="artist_names",
    orientation="h",
    range_x=[0, 1],
    labels={
        'track_name': 'Song',
        'probability': 'Wahrscheinlichkeit',
        'artist_names': 'Künstler'
    },
    title="Top 10 Wahrscheinlichkeiten"
)

fig_bar.update_yaxes(autorange="reversed")

st.plotly_chart(fig_bar, use_container_width=True)

# Forecast
st.subheader("📈 Song-spezifischer Forecast")

selected_artist = st.selectbox("Künstler wählen:", df_display["artist_names"].unique())
selected_song = st. selectbox(
    "Song wählen:",
    df_display[df_display["artist_names"] == selected_artist]["track_name"].unique()
)

song_data = df_display[
    (df_display["artist_names"] == selected_artist) &
    (df_display["track_name"] == selected_song)
    ].sort_values("ds")

if not song_data.empty:
    from plotly.subplots import make_subplots
    
    # Erstelle Subplot mit zweiter Y-Achse
    fig_line = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Historische Streams (Haupt-Achse)
    if "streams" in song_data.columns and not song_data["streams"].isna().all():
        fig_line.add_trace(
            go.Scatter(
                x=song_data["ds"], 
                y=song_data["streams"], 
                name="Streams", 
                mode="lines+markers"
            ),
            secondary_y=False
        )
    
    # 2. Vorhersage-Wahrscheinlichkeit (Zweite Achse rechts)
    fig_line.add_trace(
        go.Scatter(
            x=song_data["ds"], 
            y=song_data["probability"], 
            name="KI-Wahrscheinlichkeit", 
            mode="lines+markers",
            line=dict(dash='dash', color='orange')
        ),
        secondary_y=True
    )
    
    fig_line.update_layout(
        title=f"Trend-Analyse: {selected_song}",
        yaxis=dict(title="Anzahl Streams"), 
        yaxis2=dict(title="Rising Probability (0-1)", range=[0, 1])
    )
    
    st.plotly_chart(fig_line, use_container_width=True)

# Tabelle
st.subheader("📋 Detaildaten") 

df_show = top_10[["artist_names", "track_name", "probability"]].rename(columns={
    "artist_names": "Künstler",
    "track_name": "Song",
    "probability": "Wahrscheinlichkeit"
})

st.dataframe(df_show)

# ------------------------------------------------------------ 
# Automatisierter Trendbericht
# ------------------------------------------------------------

# Session State initialisieren
if "last_ai_call" not in st.session_state:
    st.session_state.last_ai_call = 0

COOLDOWN_SECONDS = 60

if st.button("🪄 Analyse-Bericht generieren"):
    current_time = time.time()
    elapsed = current_time - st.session_state.last_ai_call

    if elapsed < COOLDOWN_SECONDS:
        remaining = math.ceil(COOLDOWN_SECONDS - elapsed)
        st.warning(f"Bitte warte noch {remaining} Sekunden.")
    else:
        with st.spinner("Gemini analysiert..."):
            report = generate_gemini_report(df_display, top_10)
            st.session_state.last_ai_call = current_time

            if report:
                st.markdown(report)
            else:
                st.error("Der Bericht konnte nicht generiert werden.")
