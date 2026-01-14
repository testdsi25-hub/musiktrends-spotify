import json
import pandas as pd
from prophet.serialize import model_from_json
import lightgbm as lgb
import os
import streamlit as st

MODEL_DIR = "models/"


# ____ MODELLE LAZY LADEN ____

_prophet_model = None
_lgbm_model = None
_best_t = None
_feature_cols = None

@st.cache_resource
def load_artefacts(model_dir=MODEL_DIR):
    """Lädt Prophet, LightGBM, Threshold und Feature-Liste."""
    global _prophet_model, _lgbm_model, _best_t, _feature_cols

    if _prophet_model is not None:
        return _prophet_model, _lgbm_model, _best_t, _feature_cols

    # Prophet
    with open(os.path.join(model_dir, "market_trend_prophet_v1.json"), "r") as f:
        _prophet_model = model_from_json(f.read())

    # LightGBM
    _lgbm_model = lgb.Booster(
        model_file=os.path.join(model_dir, "rising_artist_lgbm_v1.txt")
    )

    # Threshold
    with open(os.path.join(model_dir, "rising_artist_threshold.json"), "r") as f:
        _best_t = json.load(f)["best_threshold"]

    # Feature-Liste
    with open(os.path.join(model_dir, "rising_artist_features.json"), "r") as f:
        _feature_cols = json.load(f)

    print(f"Modelle geladen. Optimaler Threshold: {_best_t}")

    return _prophet_model, _lgbm_model, _best_t, _feature_cols

# ____ PREDICTION PIPELINE ____ 

@st.cache_data
def run_prediction_pipeline(df):
    """
    df: DataFrame mit Features + Spalte 'ds'
    Erwartet:
        - ds (datetime)
        - alle Feature-Spalten aus rising_artist_features.json
    """
    prophet_model, lgbm_model, best_t, feature_cols = load_artefacts()

    df = df.copy()

    # Prophet: Trend extrahieren
    if "ds" not in df.columns:
        raise ValueError("Spalte 'ds' fehlt. Bitte chart_week → ds konvertieren.")

    forecast = prophet_model.predict(df[["ds"]])
    df["prophet_trend"] = forecast["trend"].values

    # LightGBM: Features vorbereiten
    # Fehlende Spalten automatisch ergänzen
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0

    X = df[feature_cols].fillna(0)

    # Vorhersage
    probs = lgbm_model.predict(X)
    preds = (probs > best_t).astype(int)

    return preds, probs
    
print("Prediction Pipeline erfolgreich geladen.")