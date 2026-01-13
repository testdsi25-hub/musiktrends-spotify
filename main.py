import os
import pandas as pd

from src.spotify_client import SpotifyClient
from src.predict_pipeline import run_prediction_pipeline

# ____ HILFSFUNKTIONEN ____

def load_csv(path, skip_header=False):
    """
    Lädt eine CSV-Datei sicher.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV nicht gefunden: {path}")
    return pd.read_csv(path, skiprows=1 if skip_header else 0)

def prepare_features(df):
    """
    Bereitet die Spalten so vor, wie Prophet & LightGBM sie erwarten.
    """
    if "chart_week" in df.columns:
        df["ds"] = pd.to_datetime(df["chart_week"])
    return df

# ____ HAUPTPROZESS ____

def main():
    print("Starte Backend-Pipeline...")

    # Historische Daten laden
    HIST_PATH = "data/processed/df_cleaned_full.csv"
    print("Lade historische Daten (01/2024 - 12/2025)...")
    df_hist = load_csv(HIST_PATH)

    # Neue Chart-Daten laden
    NEW_PATH = "data/raw/spotify_charts_this_week.csv"
    print("Lade neue Chart-Daten...")
    df_new = load_csv(NEW_PATH, skip_header=True)

    # Historische und neue Daten kombinieren
    print("Kombiniere historische und neue Daten...")
    df_combined = pd.concat([df_hist, df_new], ignore_index=True)

    # Dubletten entfernen, falls Track/Woche doppelt vorkommt
    df_combined = df_combined.drop_duplicates(
        subset=["track_name","artist_names","chart_week"]
    )

    # Spotify API Enrichment
    print("Starte Spotify API Enrichment...")
    client = SpotifyClient()

    df_with_ids = client.get_ids_for_tracks(df_combined)
    df_enriched = client.enrich_data(df_with_ids)

    # Feature Engineering
    df_enriched = prepare_features(df_enriched)

    # Prediction Pipeline (Prophet und LightGBM)
    print("Starte Vorhersage-Pipeline...")
    preds, probs = run_prediction_pipeline(df_enriched)

    df_enriched["is_rising_predicted"] = preds
    df_enriched["rising_probability"] = probs

    # Ergebnisse anzeigen
    output_path="data/processed/final_predictions.csv"
    df_enriched.to_csv(output_path, index=False)

    print("\nTOP 10 RISING ARTISTS DIESER WOCHE")
    top_10 = (
        df_enriched[df_enriched["is_rising_predicted"] == 1]
        .sort_values("rising_probability", ascending=False)
        .head(10)
    )
    print(top_10[["track_name","artist_names","rising_probability"]])

    print(f"\nErgebnisse gespeichert unter: {output_path}")

if __name__ == "__main__":
    main()
    