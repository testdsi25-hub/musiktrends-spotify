import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime, timedelta

def extract_track_id_from_uri(uri: str) -> str:
    """
    Entfernt 'spotify:track:' aus der URI und gibt die reine Track-ID zurück.
    """
    if pd.isna(uri):
        return None
    return uri.replace("spotify:track:", "")


def merge_new_data(
    ids_csv: str,
    enriched_csv: str,
    hist_path: str,
    output_path: str,
    backup_dir: str = "data/backups",
    cleanup_days: int = 180    # 6 Monate
):
    """
    Kombiniert:
    - unique_tracks_with_ids_YYYY-MM-DD.csv
    - enriched_data_YYYY-MM-DD.csv
    - historische Daten (final_data_with_metadata.csv)

    Schritte:
    1. Backup des historischen Datensatzes automatisch ablegen
    2. IDs laden + Track-ID aus URI extrahieren
    3. Enrichment laden
    4. Merge über track_id
    5. Historische Daten laden
    6. Neue Daten anhängen
    7. Duplikate entfernen
    8. Sortieren
    9. Speichern (Historischen Datensatz aktualisieren)
    10. Alte Backups löschen
    """
    hist_path = Path(hist_path) 
    backup_dir = Path(backup_dir) 
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # ____ 1. Backup des historischen Datensatzes erstellen ____ 

    # Prüfen, ob bereits ein Backup mit heutigem Datum besteht und ggf. löschen (pro Tag nur 1 Datei!)
    today_str = datetime.now().strftime("%Y-%m-%d")

    for file in backup_dir.glob(f"{hist_path.stem}_backup_{today_str}_*.csv"):
        file.unlink()
        print(f"Altes Backup für heute gelöscht: {file}")
        
    # Backup erstellen
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 
    backup_path = backup_dir / f"{hist_path.stem}_backup_{timestamp}.csv" 
    shutil.copy(hist_path, backup_path)
    print(f"Backup erstellt: {backup_path}")
    
    # ____ 2. IDs laden ____
    df_ids = pd.read_csv(ids_csv)

    # Track-ID aus URI extrahieren
    if "uri" not in df_ids.columns:
        raise KeyError("Spalte 'uri' fehlt in unique_tracks_with_ids_YYYY-MM-DD.csv.")
        
    df_ids["spotify_track_id"] = df_ids["uri"].apply(extract_track_id_from_uri)    

    # ____ 3. Enrichment laden ____
    df_enriched = pd.read_csv(enriched_csv)

    # ____ 4. Merge über track_id ____
    df_merged = df_ids.merge(
        df_enriched,
        left_on="spotify_track_id",
        right_on="track_id",
        how="inner"
    )

    # Unnötige Spalten entfernen
    columns_to_keep = [
    "chart_week", "rank", "artist_names", "track_name",
    "peak_rank", "previous_rank", "weeks_on_chart",
    "streams", "track_id", "artist_id", "release_date",
    "explicit", "track_popularity", "artist_genres",
    "artist_followers", "artist_popularity"
    ]
    
    df_merged = df_merged[[c for c in columns_to_keep if c in df_merged.columns]]

    
    # ____ 5. Historische Daten laden ____
    df_hist = pd.read_csv(hist_path)

    # ____ 6. Neue Daten anhängen ____
    df_all = pd.concat([df_hist, df_merged], ignore_index=True)

    # ____ 7. Duplikate entfernen ____
    df_all = df_all.drop_duplicates(subset=["chart_week", "track_id"], keep="last")

    # ____ 8. Sortieren ____
    df_all = df_all.sort_values(by=["chart_week", "track_id"]).reset_index(drop=True)

    # ____ 9. Historischen Datensatz aktualisieren (überschreiben) ____
    df_all.to_csv(hist_path, index=False)
    print(f"Historischer Datensatz aktualisiert unter: {hist_path}")

    # ____ 10. Alte Backups löschen ____ 
    
    if cleanup_days is not None: 
        cutoff = datetime.now() - timedelta(days=cleanup_days) 
        
        for file in backup_dir.glob(f"{hist_path.stem}_backup_*.csv"): 
            # Datum aus Dateinamen extrahieren 
            try: 
                date_str = file.stem.split("_backup_")[1] 
                file_date = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S") 
            except Exception: 
                continue 
            
            if file_date < cutoff: 
                file.unlink() 
                print(f"Backup gelöscht (älter als {cleanup_days} Tage): {file}")
                
    return df_all
