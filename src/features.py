import pandas as pd
import ast
import streamlit as st

# ____ GENRE PARSER ____
def genre_parser(val):
    """Bringt die Zeilen der Spalte 'artist_genres' in ein einheitliches Format."""
    if isinstance(val, list):
        return val

    if pd.isna(val) or val in ['unknown', "['unknown']"]:
        return ['unknown']

    val_str = str(val).strip()

    # Pipe-getrennte Genres
    if '|' in val_str:
        return [g.strip() for g in val_str.split('|')]

    # Liste als String
    if val_str.startswith('[') and val_str.endswith(']'):
        try:
            parsed = ast.literal_eval(val_str)
            return parsed if isinstance(parsed, list) else ['unknown']
        except:
            return ['unknown']

    # Einzelnes Genre
    return [val_str]

# ____ FEATURE ENGINEERING PIPELINE ____

@st.cache_data
def build_features(df):
    """
    Berechnet alle Features, die das LightGBM-Modell benötigt.
    Funktioniert für historische Daten und neue Wochen.
    """
    df = df.copy()

    # chart_week → datetime
    if "chart_week" in df.columns:
        df["chart_week"] = pd.to_datetime(df["chart_week"], errors="coerce")

    # Genre Parsing
    if "artist_genres" in df.columns:
        df["artist_genres"] = df["artist_genres"].apply(genre_parser)

    # Genre Popularity Index (genre_pop_idx)
    if "streams" in df.columns and "artist_genres" in df.columns:
        genre_df = df.explode("artist_genres")

        # Durchschnittliche Streams pro Genre pro Woche
        genre_stats = (
            genre_df.groupby(["chart_week", "artist_genres"])["streams"]
            .mean()
            .rename("genre_pop_idx")
            .reset_index()
        )

        # Merge Genre-Stats zurück
        genre_df = genre_df.merge(
            genre_stats, on=["chart_week", "artist_genres"], how="left"
        )

        # Durchschnittlicher Genre-Index pro Track
        song_genre_index = (
            genre_df.groupby(["chart_week", "track_id"])["genre_pop_idx"]
            .mean()
            .reset_index()
        )

        df = df.merge(song_genre_index, on=["chart_week", "track_id"], how="left")
    else:
        df["genre_pop_idx"] = 0

    # Artist Growth Rate
    if "streams" in df.columns:
        df = df.sort_values(by=["artist_names", "chart_week"])
        df["artist_growth_rate"] = (
            df.groupby("artist_names")["streams"]
            .pct_change()
            .replace([float("inf"), -float("inf")], 0)
            .fillna(0)
        )
    else:
        df["artist_growth_rate"] = 0

    # Seasonality Score
    if "streams" in df.columns:
        df["month"] = df["chart_week"].dt.month
        monthly_avg = df.groupby("month")["streams"].transform("mean")
        total_avg = df["streams"].mean()
        df["seasonality_score"] = monthly_avg / total_avg
    else:
        df["seasonality_score"] = 1.0

    return df

# ____ TRENDBERICHT ____

def generate_trend_report(row):
    """
    Erzeugt einen dynamischen Trendbericht für einen einzelnen Artist/Track.
    Erwartet eine Zeile aus df_final (nach Prediction).
    """

    artist = row.get("artist_names", "Unbekannter Artist")
    track = row.get("track_name", "Unbekannter Track")

    growth = row.get("artist_growth_rate", 0)
    genre_idx = row.get("genre_pop_idx", 0)
    season = row.get("seasonality_score", 1)
    popularity = row.get("track_popularity", 0)
    trend = row.get("prophet_trend", 0)
    prob = row.get("probability", 0)

    statements = []

    # Artist Growth
    if growth > 0.15:
        statements.append("zeigt ein starkes Wachstum bei Streams und Followern")
    elif growth > 0.05:
        statements.append("verzeichnet ein moderates, aber stabiles Wachstum")
    else:
        statements.append("zeigt aktuell nur leichtes Wachstum")

    # Genre Popularity
    if genre_idx > 60:
        statements.append("profitiert von einem sehr populären Genre")
    elif genre_idx > 40:
        statements.append("bewegt sich in einem Genre mit solider Nachfrage")
    else:
        statements.append("kommt aus einem Genre, das derzeit weniger im Trend liegt")

    # Seasonality
    if season > 1.1:
        statements.append("passt perfekt zur aktuellen saisonalen Nachfrage")
    elif season < 0.9:
        statements.append("performt trotz schwacher Saison überraschend gut")

    # Prophet Trend
    if trend > 0:
        statements.append("wird zusätzlich durch positive Makro‑Trends unterstützt")
    else:
        statements.append("setzt sich trotz schwacher Markttrends durch")

    # Track Popularity
    if popularity > 70:
        statements.append("und erreicht bereits hohe Popularitätswerte")
    elif popularity > 40:
        statements.append("und baut seine Popularität weiter aus")

    # Probability
    if prob > 0.8:
        confidence = "Das Modell sieht eine sehr hohe Wahrscheinlichkeit für einen Durchbruch."
    elif prob > 0.6:
        confidence = "Das Modell sieht gute Chancen für einen Aufstieg."
    else:
        confidence = "Das Modell erkennt frühe Signale eines möglichen Aufstiegs."

    report = (
        f"**{artist} – '{track}'**\n\n"
        f"{artist} {', '.join(statements)}. "
        f"{confidence}"
    )

    return report