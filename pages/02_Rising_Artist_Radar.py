import os
import ast
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        hist_raw_path=PROCESSED_DIR / "hist_data_24-25.csv", 
        hist_updated_path=PROCESSED_DIR / "hist_data_updated.csv"
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
    # Schritt 5a: Prediction Pipeline 
    # -------------------------------------------------------- 
    st.subheader("🤖 KI‑Vorhersage starten") 
    
    preds, probs = run_prediction_pipeline(df_features) 
    
    df_features["is_rising"] = preds 
    df_features["probability"] = probs 

    st.session_state["df_features"] = df_features
    
    st.success("Die KI-Vorhersagen sind bereit.")

    # -------------------------------------------------------- 
    # Schritt 5b: Zukunfts-Horizont erzeugen (Forecast) 
    # -------------------------------------------------------- 
    
    # Parameter: wie viele Wochen in die Zukunft?
    FORECAST_WEEKS = 12  # z.B. 12 Wochen
    
    # Letztes historisches Datum bestimmen
    last_ds = df_features["ds"].max()
    
    # Zukünftige Wochen erzeugen
    future_dates = pd.date_range(
        start=last_ds + pd.Timedelta(weeks=1),
        periods=FORECAST_WEEKS,
        freq="W"
    )
    
    # DataFrame für zukünftige Wochen
    future_dates_df = pd.DataFrame({
        "ds_future": future_dates,
        "key": 1
    })
    
    # Pro Track die letzte bekannte Zeile nehmen
    last_per_track = (
        df_features.sort_values("ds")
        .groupby("track_id")
        .tail(1)
    )
    
    # Sicherstellen, dass 'ds' existiert
    if "ds" not in last_per_track.columns:
        last_per_track["ds"] = last_per_track["chart_week"]
    
    # 'ds' umbenennen, damit der Merge sauber funktioniert
    last_per_track = last_per_track.rename(columns={"ds": "ds_last"})
    
    # Cross Join: jeder Track × jede zukünftige Woche
    last_per_track = last_per_track.assign(key=1)
    
    future_df = last_per_track.merge(
        future_dates_df,
        on="key",
        how="outer"
    ).drop(columns=["key"])
    
    # ds auf ds_future setzen
    future_df["ds"] = future_df["ds_future"]
    
    # chart_week auf ds setzen (für Konsistenz)
    future_df["chart_week"] = future_df["ds"]
    
    # Aufräumen
    future_df = future_df.drop(columns=["ds_last", "ds_future"])
    
    # Zeitbasierte Regressoren aus der Historie ableiten
    regressor_time = (
        df_features.groupby("ds")[["genre_idx_lagged", "seasonality_score"]]
        .mean()
        .reset_index()
    )
    
    future_df = future_df.drop(columns=["genre_idx_lagged", "seasonality_score"], errors="ignore")
    future_df = future_df.merge(regressor_time, on="ds", how="left")
    
    # Robust füllen: erst bfill, dann ffill
    future_df["genre_idx_lagged"] = future_df["genre_idx_lagged"].bfill().ffill()
    future_df["seasonality_score"] = future_df["seasonality_score"].bfill().ffill()
    
    # Falls immer noch NaN (z. B. komplett fehlende Historie)
    future_df["genre_idx_lagged"] = future_df["genre_idx_lagged"].fillna(0)
    future_df["seasonality_score"] = future_df["seasonality_score"].fillna(0)

    
    # Prediction Pipeline auf Zukunft laufen lassen
    future_preds, future_probs = run_prediction_pipeline(future_df)
    
    future_df["is_rising"] = future_preds
    future_df["probability"] = future_probs
    
    # Flag für Zukunft
    df_features["is_future"] = False
    future_df["is_future"] = True
    
    # Historische + zukünftige Daten zusammenführen
    df_all = pd.concat([df_features, future_df], ignore_index=True)
    
    # In Session State speichern
    st.session_state["df_features"] = df_all
    
    st.success("Zukunftsprognosen wurden für alle Tracks berechnet.")

# ------------------------------------------------------------ 
# Dashboard (Visualisierungen)
# ------------------------------------------------------------
st.header("📊 Analyse & Visualisierung")

if "df_features" not in st.session_state:
    st.info("Bitte lade zuerst Spotify-Infos und starte die KI-Vorhersage.")
    st.stop()

df_all = st.session_state["df_features"].copy()
df_display = df_all.copy()

# KPI-Bereich
col1, col2, col3 = st.columns(3)
col1.metric("Analysierte Tracks", f"{len(df_all):,}")
col2.metric("Rising Artists", (df_all['probability'] >= 0.9).sum())
col3.metric("Max. Wahrscheinlichkeit", f"{df_all['probability'].max():.2%}")

st.divider()

# Filter für Historie vs. Zukunft
view_mode = st.radio(
    "Zeitraum für die Genre Trend Heatmap & TOP 10 Rising Artists:",
    ["Beides", "Nur Historie", "Nur Forecast"],
    horizontal=True
)

if view_mode == "Nur Historie":
    df_display = df_display[df_display["is_future"] == False]
elif view_mode == "Nur Forecast":
    df_display = df_display[df_display["is_future"] == True]
# "Beides" → keine Filterung

# Heatmap 
if "artist_genres" in df_display.columns:
    st.subheader("🔥 Genre Trend Heatmap")

    # Kopie für die Heatmap erstellen, um df_display nicht für andere Charts zu verändern
    df_heatmap = df_display.copy()
    
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
   
    # Forecast-Bereich einfärben 
    df_all = st.session_state["df_features"]
    future_start = df_all[df_all["is_future"] == True]["ds"].min()
    future_end = df_all["ds"].max()
    
    if pd.notna(future_start):
        fig_heatmap.add_vrect(
            x0=future_start,
            x1=future_end,
            fillcolor="orange",
            opacity=0.15,
            layer="below",
            line_width=0,
            annotation_text="Forecast",
            annotation_position="top left"
        )
        
    st.plotly_chart(fig_heatmap, use_container_width=True)

# TOP 10 Rising Artists

st.subheader("🏆 TOP 10 Rising Artists")

# Aktuelle (letzte historische Woche)
hist_df = df_display[df_display["is_future"] == False]
if not hist_df.empty:
    last_hist_week = hist_df["ds"].max()
    hist_last_week = hist_df[hist_df["ds"] == last_hist_week]

    hist_unique = (
        hist_last_week.sort_values("probability", ascending=False)
        .drop_duplicates(subset=["artist_names", "track_name"])
    )
    top_10_hist = hist_unique.nlargest(10, "probability")
else:
    top_10_hist = pd.DataFrame()

# Zukunft: nächste Woche nach letzter Historie
future_df = df_display[df_display["is_future"] == True]
if not future_df.empty:
    first_future_week = future_df["ds"].min()
    future_first_week = future_df[future_df["ds"] == first_future_week]

    future_unique = (
        future_first_week.sort_values("probability", ascending=False)
        .drop_duplicates(subset=["artist_names", "track_name"])
    )
    top_10_future = future_unique.nlargest(10, "probability")
else:
    top_10_future = pd.DataFrame()

col_hist, col_future = st.columns(2)


st.markdown("**Aktuelle TOP 10 (letzte historische Woche)**")
if not top_10_hist.empty:
    fig_bar_hist = px.bar(
        top_10_hist,
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
        title="TOP 10 (Historie)"
    )
    fig_bar_hist.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_bar_hist, use_container_width=True)
else:
    st.info("Keine historischen Daten für TOP 10 verfügbar.")


st.markdown("**Vorhergesagte TOP 10 (nächste Woche)**")
if not top_10_future.empty:
    fig_bar_future = px.bar(
        top_10_future,
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
        title="TOP 10 (Forecast)"
    )
    fig_bar_future.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_bar_future, use_container_width=True)
else:
    st.info("Keine Forecast-Daten für TOP 10 verfügbar.")

# SONG-FORECAST: Probability historisch vs. Zukunft
st.subheader("📈 Song-spezifischer Probability-Forecast")

selected_artist = st.selectbox("Künstler wählen:", df_all["artist_names"].unique())
selected_song = st.selectbox(
    "Song wählen:",
    df_all[df_all["artist_names"] == selected_artist]["track_name"].unique()
)

# Daten für diesen Song
song_data = df_all[
    (df_all["artist_names"] == selected_artist) &
    (df_all["track_name"] == selected_song)
].sort_values("ds")

if not song_data.empty:

    fig_line = make_subplots(specs=[[{"secondary_y": False}]])

    # Historische Probability
    hist = song_data[song_data["is_future"] == False]
    if not hist.empty:
        fig_line.add_trace(
            go.Scatter(
                x=hist["ds"],
                y=hist["probability"],
                name="Historische Probability",
                mode="lines+markers",
                line=dict(color="blue")
            )
        )

    # Zukünftige Probability
    fut = song_data[song_data["is_future"] == True]
    if not fut.empty:
        fig_line.add_trace(
            go.Scatter(
                x=fut["ds"],
                y=fut["probability"],
                name="Forecast Probability",
                mode="lines+markers",
                line=dict(color="orange", dash="dash")
            )
        )
    else: 
        st.info("Für diesen Song liegen keine Forecast-Daten vor.")
        
    fig_line.update_layout(
        title=f"Probability-Forecast: {selected_song}",
        yaxis=dict(title="Probability (0–1)", range=[0, 1])
    )

    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Keine Daten für diesen Song gefunden.")

# Tabelle
st.subheader("📋 Detaildaten (Forecast TOP 10)") 

if not top_10_future.empty: 
    df_show = top_10_future[["artist_names", "track_name", "probability"]].rename(columns={
        "artist_names": "Künstler",
        "track_name": "Song",
        "probability": "Wahrscheinlichkeit"
    })

    st.dataframe(df_show)
else:
    st.info("Keine Forecast-Daten verfügbar.")

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
            # Nur Forecast-Daten der ersten Zukunftswoche verwenden
            df_all = st.session_state["df_features"].copy()
            future_df = df_all[df_all["is_future"] == True]

            if future_df.empty:
                st.error("Keine Forecast-Daten verfügbar.")
            else:
                first_future_week = future_df["ds"].min()
                df_future_week = future_df[future_df["ds"] == first_future_week]

                future_unique = (
                    df_future_week.sort_values("probability", ascending=False)
                    .drop_duplicates(subset=["artist_names", "track_name"])
                )
                top_10_future = future_unique.nlargest(10, "probability")

                try:
                    report = generate_gemini_report(df_future_week, top_10_future)
                    st.session_state.last_ai_call = current_time
    
                    if report:
                        st.markdown(report)
                    else:
                        st.error("Der Bericht konnte nicht generiert werden.")
                except Exception as e:
                    st.warning("Der KI-Dienst ist momentan überlastet. Bitte versuchen Sie es später erneut.")

st.markdown(
    """
    <div style='text-align: center; margin-top: 50px; color: gray; font-size: 12px;'>
        © Eva Wolff Fabris · 23. Januar 2026 · Musiktrends vorhersagen und verstehen · Alle Rechte vorbehalten.
    </div>
    """,
    unsafe_allow_html=True
)