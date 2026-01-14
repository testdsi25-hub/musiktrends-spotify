import pandas as pd
import re
from pathlib import Path

def extract_date_from_filename(filename: str) -> str: 
    """
    Extrahiert das Datum aus einem Dateinamen wie: 
    regional-global-weekly-2026-01-08.csv
    """
    match = re.search(r"\d{4}-\d{2}-\d{2}", filename)
    if not match: 
        raise ValueError(f"Kein Datum im Dateinnamen gefunden: {filename}")
    return match.group(0)

def prepare_unique_tracks(input_path: str, output_dir: str = "/data/interim"):
    """
    1. Die CSV-Datei laden
    2. Datum aus Dateinamen extrahieren
    3. Spalte chart_week einfügen (zunächst als String, später im Datumsformat)
    4. Eindeutige Kombinationen aus track_name + artist_names erzeugen
    5. Datei speichern
    """
    input_path = Path(input_path)
    date_str = extract_date_from_filename(input_path.name)

    df = pd.read_csv(input_path)

    # chart_week-Spalte einfügen
    df.insert(0, "chart_week", date_str)

    # chart_week als Datum casten
    df["chart_week"] = pd.to_datetime(df["chart_week"], format="%Y-%m-%d")

    # Eindeutige Kombinationen
    df_unique = df.drop_duplicates(subset=["track_name","artist_names"])

    output_dir_path = Path(output_dir) 
    output_dir_path.mkdir(parents=True, exist_ok=True) 
    output_path = output_dir_path / f"unique_tracks_to_enrich_{date_str}.csv"
    
    df_unique.to_csv(output_path, index=False)

    print(f"Gespeichert unter: {output_path}")
    return output_path, date_str