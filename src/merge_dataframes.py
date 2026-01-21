import pandas as pd
from pathlib import Path
from datetime import datetime

def merge_new_data(
    charts_csv: str, 
    enriched_csv: str,
    date_str: str, 
    processed_dir: Path,
    hist_raw_path: Path,
    hist_updated_path: Path,
    backup_dir:Path
):
    """
    Schritte: 
    1. Charts und Meta laden
    2. 'track_id' aus 'uri' extrahieren
    3. Merge über 'track_id'
    4. Bereinigung der Daten
    5. Speichern als data_week_YYYY-MM-DD
    6. Historie aktualisieren und Backup erzeugen
    """
    charts_csv = Path(charts_csv)
    enriched_csv = Path(enriched_csv)
    processed_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    # ____ Charts + Meta laden ____
    df_charts = pd.read_csv(charts_csv)
    df_meta = pd.read_csv(enriched_csv)

    # ____ track_id aus uri extrahieren
    df_charts["track_id"] = (
        df_charts["uri"]
        .astype(str)
        .str.replace("spotify:track:", "", regex=False)
    )

    # ____ Merge über track_id ____
    df_week = pd.merge(
        df_charts,
        df_meta,
        on="track_id",
        how="left",
        suffixes=("", "_api")
    )

    # ____ Bereinigung ____
    df_week = df_week.drop(columns=[c for c in ["uri", "track_name_api"] if c in df_week.columns])

    df_week["chart_week"] = pd.to_datetime(df_week["chart_week"], errors="coerce")
    df_week["release_date"] = pd.to_datetime(df_week["release_date"], errors="coerce")
    
    df_week["artist_genres"] = df_week["artist_genres"].fillna("unknown")

    # ____ data_week_YYYY-MM-DD.csv speichern ____
    weekly_path = processed_dir / f"data_week_{date_str}.csv"
    df_week.to_csv(weekly_path, index=False)

    # ____ Historie aktualisieren und speichern ____
    if hist_updated_path.exists():
        df_hist = pd.read_csv(hist_updated_path)
    else:
        # Falls noch keine updated_Datei gibt, starte mit raw
        df_hist = pd.read_csv(hist_raw_path)
    
    # Datumsfelder vereinheitlichen 
    df_hist["chart_week"] = pd.to_datetime(df_hist["chart_week"], errors="coerce") 
    df_hist["release_date"] = pd.to_datetime(df_hist["release_date"], errors="coerce")

    # Neue Woche anhängen
    df_all = pd.concat([df_hist, df_week], ignore_index=True)

    # Deduplizieren
    df_all = df_all.drop_duplicates(subset=["chart_week", "track_id"], keep="last") 

    # Sortieren
    df_all = df_all.sort_values(by=["chart_week", "track_id"]).reset_index(drop=True)
    
    # Datumsformat zurück zu Strings
    df_all["chart_week"] = df_all["chart_week"].dt.strftime("%Y-%m-%d")
    df_all["release_date"] = df_all["release_date"].dt.strftime("%Y-%m-%d")
    
    # Speichern der aktualisierten Historie 
    df_all.to_csv(hist_updated_path, index=False)

    # ____ Backup erzeugen (max. ein Backup pro Tag) ____
        
    today_str = datetime.now().strftime("%Y-%m-%d") 
    
    # Alte Backups des heutigen Tages löschen 
    for file in backup_dir.glob(f"hist_data_{today_str}_*.csv"): 
        file.unlink() 
    
    # Neues Backup speichern 
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 
    backup_path = backup_dir / f"hist_data_{today_str}_{timestamp}.csv" 
    df_all.to_csv(backup_path, index=False) 
    
    return df_all
    