# -slim: kleiner als das Standard-Image, enthält alles Wichtige
FROM python:3.11-slim

# BEST PRACTICES
# Snapshot der letzten Version
RUN apt-get update && apt-get install -y \
    # Metapaket für Software
    build-essential \
    # zwingend für LightGBM erforderlich
    g++ \
    libgomp1 \
    libstdc++6 \
    # Container prüft, ob eine Internetverbindung besteht
    curl \
    # hält das Image klein: rm (remove), -r(ecursive)f(orce)
    && rm -rf /var/lib/apt/lists/*  

# Arbeitsverzeichnis
WORKDIR /app

# Python-Abhängigkeiten (Caching, falls nur der Code geändert wird)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Projektstruktur kopieren
COPY . .

# Umgebungsvariablen 
# Cache-Dateien im Container vermeiden (verhindert default .pyc Dateien)
ENV PYTHONDONTWRITEBYTECODE=1
# Logs sofort an das Terminal weiterleiten
ENV PYTHONUNBUFFERED=1

# Ports freigeben
# 8888 für Jupyter, 8501 für Streamlit Dashboard
EXPOSE 8888
EXPOSE 8501

# Flexibler Startbefehl 
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
