import os
import time
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

from .spotify_utils import (
    refresh_access_token,
    get_spotify_ids,
    get_tracks_batch,
    get_artists_batch
)

load_dotenv()

class SpotifyClient:
    """
    Spotify-Client:
    1. Access Token holen
    2. unique_tracks_to_enrich_YYYY-MM-DD.csv laden
    3. Spotify IDs suchen (track_id + artist_id)
    4. Ergebnis speichern
    5. Enrichment durchführen (Genres, Popularity, Release Dates, etc.)
    6. enriched_data_YYYY-MM-DD.csv speichern
    """

    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
        self.access_token = None

        self._validate_env()
        self.authenticate()

    # ____ AUTHENTIFIZIERUNG ____
    def _validate_env(self):
        missing = [
            key for key in ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN"]
            if os.getenv(key) is None
        ]
        if missing:
            raise ValueError(f"Fehlende Umgebungsvariablen: {missing}")

    def authenticate(self):
        """Holt einen frischen Access Token über den Refresh Token."""
        self.access_token = refresh_access_token(
            self.refresh_token,
            self.client_id,
            self.client_secret
        )

        if not self.access_token:
            raise RuntimeError("Spotify-Authentifizierung fehlgeschlagen.")

        print("Spotify-Authentifizierung erfolgreich.")

    # ____ ID-MAPPING ____
    def map_spotify_ids(self, input_csv, output_csv):
        """
        Lädt unique_tracks_to_enrich_YYYY-MM-DD.csv, sucht Spotify IDs und speichert sie.
        """
        print(f"Lade Datei: {input_csv}")
        df = pd.read_csv(input_csv)

        tqdm.pandas()
        print("Starte Suche nach Spotify IDs...")

        ids = df.progress_apply(
            lambda row: get_spotify_ids(
                row["track_name"],
                row["artist_names"],
                self.access_token
            ), axis=1
        )
        df[["track_id","artist_id"]] = pd.DataFrame(ids.tolist(), index=df.index)

        df.to_csv(output_csv, index=False)
        print(f"Mapping fertig! {df['track_id'].notna().sum()} IDs gefunden.")
        return df

    # ____ ENRICHMENT ____
    def enrich_tracks(self, input_csv, output_csv, batch_size=50, sleep_time=1):
        """
        Lädt unique_tracks_with_ids.csv, erzeugt enriched_data.csv.
        """
        print(f"Lade Datei: {input_csv}")
        df_ids = pd.read_csv(input_csv).dropna(subset=["track_id","artist_id"])

        print(f"Starte Enrichment für {len(df_ids)} Tracks...")
        all_enriched_data = []

        for i in tqdm(range(0, len(df_ids), batch_size)):
            batch = df_ids.iloc[i:i + batch_size] 
            
            t_batch = batch["track_id"].tolist() 
            a_batch = batch["artist_id"].unique().tolist()
            
            tracks_res = get_tracks_batch(t_batch, self.access_token)
            artists_res = get_artists_batch(a_batch, self.access_token)

            artist_map = {a["id"]: a for a in artists_res if a}

            for track in tracks_res:
                if not track or "id" not in track:
                    continue

                main_artist_id = track["artists"][0]["id"] if track.get("artists") else None 
                artist_info = artist_map.get(main_artist_id, {}) 
                
                album_info = track.get("album", {}) 
                release_date = album_info.get( 
                    "release_date", 
                    track.get("release_date", "1900-01-01") 
                )

                all_enriched_data.append({ 
                    "track_id": track.get("id"), 
                    "track_name": track.get("name"), 
                    "artist_id": main_artist_id, 
                    "release_date": release_date, 
                    "explicit": track.get("explicit", False), 
                    "track_popularity": track.get("popularity", 0), 
                    "artist_genres": "|".join(artist_info.get("genres", [])), 
                    "artist_followers": artist_info.get("followers", {}).get("total", 0), 
                    "artist_popularity": artist_info.get("popularity", 0) 
                })

            time.sleep(sleep_time)

        df_final = pd.DataFrame(all_enriched_data)
        df_final.to_csv(output_csv, index=False)

        print(f"Fertig! {len(df_final)} Tracks angereichert.")
        return df_final
    
    # ____ KOMPLETTER WORKFLOW ____
    def run_full_pipeline(
        self,
        unique_tracks_csv,
        date_str, 
        output_dir="data/interim"
    ):
        """
        Führt den gesamten Prozess aus: 
        1. IDs mappen
        2. Enrichment durchführen
        """
    
        mapped_csv = f"{output_dir}/unique_tracks_with_ids_{date_str}.csv" 
        enriched_csv = f"{output_dir}/enriched_data_{date_str}.csv" 
        
        df_ids = self.map_spotify_ids(unique_tracks_csv, mapped_csv) 
        df_enriched = self.enrich_tracks(mapped_csv, enriched_csv) 
        
        return df_enriched
            


    