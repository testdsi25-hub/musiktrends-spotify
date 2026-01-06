import kagglehub
import shutil
import os

def fetch_kaggle_data():
    print("Starte Download von Kaggle ...")

    # Download der neuesten Version
    tmp_path = kagglehub.dataset_download("dhruvildave/spotify-charts")

    # Zielordner im Projekt
    target_dir = "data/raw/spotify-weekly"
    os.makedirs(target_dir, exist_ok=True)

    # Heruntergeladene Dateien finden und verschieben (Kagglehub lädt sie oft standardmäßig in einen Cache-Ordner!)
    for file in os.listdir(tmp_path):
        if file.endswith(".csv"):
            shutil.move(os.path.join(tmp_path, file), os.path.join(target_dir, file))
            print(f"Datei {file} wurde nach {target_dir} verschoben.")

if __name__ == "__main__":
    fetch_kaggle_data()