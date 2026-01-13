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


def extract_track_id(uri: str):
    """Extrahiert die Spotify Track-ID aus einer URI wie spotify:track:XYZ."""
    if isinstance(uri, str) and uri.startswith("spotify:track:"):
        return uri.split("spotify:track:")[1]
    return None


class SpotifyClient:
    """
    Sauberer, robuster Spotify-Client:
    - track_id aus URI oder Suche
    - artist_id IMMER aus API (nie auslassen)
    - Enrichment in Batches
    """

    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
        self.access_token = None

        self._validate_env()
        self.authenticate()

    # ---------------------------------------------------------
    # AUTHENTIFIZIERUNG
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # TRACK-ID + ARTIST-ID ERMITTELN
    # ---------------------------------------------------------
    def get_ids_for_tracks(self, df):
        """
        Liefert track_id und artist_id für jeden Track.
        Notebook-kompatibel: Jede Zeile bekommt beide IDs.
        """
        df = df.copy()

        # 1. track_id aus URI extrahieren
        if "uri" in df.columns:
            df["track_id"] = df["uri"].apply(extract_track_id)

        # 2. Fallback: Suche per Name/Artist
        missing_mask = df["track_id"].isna()

        if missing_mask.any():
            print(f"Suche Spotify IDs für {missing_mask.sum()} Tracks ohne URI...")

            def process_row(row):
                return get_spotify_ids(
                    track_name=row["track_name"],
                    artist_name=row["artist_names"],
                    token=self.access_token
                )

            ids = df[missing_mask].progress_apply(process_row, axis=1)
            df.loc[missing_mask, ["track_id", "artist_id"]] = pd.DataFrame(
                ids.tolist(), index=df[missing_mask].index
            )

        # 3. Artist-ID IMMER nachladen (Notebook-Verhalten)
        df = self._fill_missing_artist_ids(df)

        # 4. Sicherstellen, dass beide Spalten existieren
        if "artist_id" not in df.columns:
            df["artist_id"] = None

        return df.dropna(subset=["track_id", "artist_id"])

    # ---------------------------------------------------------
    # ARTIST-ID AUS TRACK-API HOLEN
    # ---------------------------------------------------------
    def _fill_missing_artist_ids(self, df):
        """Holt artist_id für alle Zeilen, die eine track_id aber keine artist_id haben."""
        if "artist_id" not in df.columns:
            df["artist_id"] = None

        missing = df["artist_id"].isna()

        if not missing.any():
            return df

        print(f"Ermittle Artist-IDs für {missing.sum()} Tracks...")

        track_ids = df.loc[missing, "track_id"].tolist()

        # Batch-weise abfragen
        batches = [track_ids[i:i+50] for i in range(0, len(track_ids), 50)]
        id_map = {}

        for batch in batches:
            tracks = get_tracks_batch(batch, self.access_token)
            for t in tracks:
                if t and "id" in t:
                    artist_id = t["artists"][0]["id"]
                    id_map[t["id"]] = artist_id

        df.loc[missing, "artist_id"] = df.loc[missing, "track_id"].map(id_map)
        return df

    # ---------------------------------------------------------
    # ENRICHMENT
    # ---------------------------------------------------------
    def enrich_data(self, df_with_ids, batch_size=50, sleep_time=0.3):
        """
        Holt Track- und Artist-Metadaten in Batches.
        """
        df_clean = df_with_ids.dropna(subset=["track_id", "artist_id"])
        track_ids = df_clean["track_id"].tolist()
        artist_ids = df_clean["artist_id"].tolist()

        print(f"Starte Enrichment für {len(df_clean)} Tracks...")

        enriched_rows = []

        for i in tqdm(range(0, len(track_ids), batch_size)):
            t_batch = track_ids[i:i + batch_size]
            a_batch = list(set(artist_ids[i:i + batch_size]))

            tracks = get_tracks_batch(t_batch, self.access_token) or []
            artists = get_artists_batch(a_batch, self.access_token) or []

            artist_map = {a["id"]: a for a in artists if a}

            for track in tracks:
                if not track or "id" not in track:
                    continue

                main_artist_id = track["artists"][0]["id"]
                artist_info = artist_map.get(main_artist_id, {})
                album_info = track.get("album", {})

                enriched_rows.append({
                    "track_id": track["id"],
                    "artist_id": main_artist_id,
                    "track_name": track.get("name"),
                    "release_date": album_info.get("release_date"),
                    "explicit": track.get("explicit", False),
                    "track_popularity": track.get("popularity", 0),
                    "artist_genres": "|".join(artist_info.get("genres", [])),
                    "artist_followers": artist_info.get("followers", {}).get("total", 0),
                    "artist_popularity": artist_info.get("popularity", 0),
                })

            time.sleep(sleep_time)

        return pd.DataFrame(enriched_rows)
