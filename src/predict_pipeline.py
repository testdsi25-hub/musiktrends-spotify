import json
import pandas as pd
from prophet.serialize import model_from_json
import lightgbm as lgb

# ____ MODELLE UND ARTEFAKTE LADEN ____

MODEL_DIR = "../models/"

def load_artefacts(model_dir=MODEL_DIR):
    """Lädt Prophet, LightGBM, Threshold und Feature-Liste."""

    # Prophet
    with open(f"{model_dir}market_trend_prophet_v1.json", "r") as f:
        prophet_model = model_from_json(f.read())

    # LightGBM 
    lgbm_model = lgb.Booster(model_file=f"{model_dir}rising_artist_lgbm_v1.txt")

    # Threshold
    with open(f"{model_dir}rising_artist_threshold.json", "r") as f:
        best_t = json.load(f)["best_threshold"]

    # Feature-Liste
    with open(f"{model_dir}rising_artist_features.json", "r") as f:
        feature_cols = json.load(f)

    print(f"Modelle geladen. Optimaler Threshold: {best_t}")

    return prophet_model, lgbm_model, best_t, feature_cols

prophet_model, lgbm_model, best_t, feature_cols = load_artefacts()

# ____ PREDICTION PIPELINE ____

def run_prediction_pipeline(new_data):
    """
    new_data: Pandas DataFrame mit aktuellen Spotify-Daten.
    Muss enthalten: ['ds', 'genre_idx_lagged', 'seasonality_score']
    """

    # Prophet-Vorhersage (Trend extrahieren)
    forecast = prophet_model.predict(
        new_data[['ds', 'genre_idx_lagged', 'seasonality_score']]
    )
    new_data = new_data.copy()
    new_data['prophet_trend'] = forecast['trend'].values

    # Features für LightGBM
    X = new_data[feature_cols].fillna(0)

    # Vorhersage
    probs = lgbm_model.predict(X)
    preds = (probs > best_t).astype(int)

    return preds, probs

print("Pipeline erfolgreich geladen und bereit.")
    
    