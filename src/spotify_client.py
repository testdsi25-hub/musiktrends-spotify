import os
import time
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

from .spotify_utils import (
    refresh_access_token, 
    get_spotify_ids, 
    get_artists_batch, 
    get_tracks_batch 
)

load_dotenv()

class SpotifyClient:
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
        """
        Generiert einen frischen Access Token.
        """
        self.access_token = refresh_access_token(
            self.refresh_token, self.client_id, self.client_secret
        )
        if not self.access_token:
            raise RuntimeError("Spotify-Authentifizierung fehlgeschlagen.")

        print("Spotify-Authentifizierung erfolgreich.")

    # ____ TRACK-ID UND ARTIST-ID MAPPING ____
    def get_ids_for_tracks(self, df_unique):
        """
        Mapping von Track-Namen zu Spotify-IDs.
        """
        print("Starte Suche nach Spotify IDs... ")

        def process_row(row):
            return get_spotify_ids(
                track_name=row["track_name"],
                artist_name=row["artist_names"],
                access_token=self.access_token
            )

        ids = df_unique.progress_apply(process_row, axis=1)
        df_unique[["track_id", "artist_id"]] = pd.DataFrame(ids.tolist(), index=df_unique.index)

        return df_unique.dropna(subset=["track_id", "artist_id"])

    # ____ ENRICHMENT ____
    def enrich_data(self, df_with_ids, batch_size=50, sleep_time=0.3):
        """
        Holt Track- und Artist-Metadaten in Batches.
        """
        df_clean = df_with_ids.dropna(subset=["track_id", "artist_id"])
        track_ids = df_clean["track_id"].tolist()
        artist_ids = df_clean["artist_id"].tolist()

        print(f"Starte Enrichment für {len(df_clean)} Tracks... ")

        enriched_rows = []

        for i in tqdm(range(0, len(track_ids), batch_size)):
            t_batch = track_ids[i:i + batch_size]
            a_batch = list(set(artist_ids[i:i + batch_size]))

            tracks = get_tracks_batch(t_batch, self.access_token) or []
            artists = get_artists_batch(a_batch, self.access_token) or []

            # Artist-Map für schnellen Zugriff
            artist_map = {a["id"]: a for a in artists if a}

            for track in tracks:
                if not track or "id" not in track:
                    continue

                main_artist_id = (
                    track.get("artists", [{}])[0].get("id")
                    if track.get("artists")
                    else None
                )

                artist_info = artist_map.get(main_artist_id, {}) 
                
                album_info = track.get("album", {}) 
                release_date = album_info.get( 
                    "release_date", 
                    track.get("release_date", "1900-01-01") 
                ) 
                
                enriched_rows.append({ 
                    "track_id": track.get("id"), 
                    "track_name": track.get("name"), 
                    "artist_id": main_artist_id, 
                    "release_date": release_date, 
                    "explicit": track.get("explicit", False), 
                    "track_popularity": track.get("popularity", 0), 
                    "artist_genres": "|".join(artist_info.get("genres", [])), 
                    "artist_followers": artist_info.get("followers", {}).get("total", 0), 
                    "artist_popularity": artist_info.get("popularity", 0), 
                }) 
                
            time.sleep(sleep_time) 
        
        return pd.DataFrame(enriched_rows)
        