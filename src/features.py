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

    # Prophet‑Regressor: genre_idx_lagged (Lag des Genre‑Index)
    df = df.sort_values("chart_week")
    df["genre_idx_lagged"] = df["genre_pop_idx"].shift(1)
    df["genre_idx_lagged"] = df["genre_idx_lagged"].fillna(method="bfill")

    return df
