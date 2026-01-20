import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ------------------------------------------------------------
# Pfade korrekt auflösen (wichtig, da Datei im pages/ Ordner liegt)
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "df_cleaned_full.csv"

# ------------------------------------------------------------
# Seiteneinstellungen
# ------------------------------------------------------------
st.set_page_config(
    page_title="Analyse des Marktes",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Wie globale Streaming‑Peaks entstehen (2024–2025)")

st.header("💥 Warum das Streaming explodiert und wann")
st.markdown("""
Diese Analyse zeigt die drei zentralen Marktmechaniken, die das globale 
Streaming‑Volumen prägen. Anhand der aggregierten Spotify‑Charts (2024–2025) 
lassen sich klare Muster erkennen, die erklären, **warum Peaks entstehen, 
wie sie sich unterscheiden und welche Dynamiken dahinterstehen.**
""")

st.markdown("---")

# ------------------------------------------------------------
# Daten laden
# ------------------------------------------------------------
df = pd.read_csv(DATA_PATH, parse_dates=["chart_week"])
seasonal_trends = df.groupby("chart_week")["streams"].sum().reset_index()

# ------------------------------------------------------------
# Abschnitt: Marktmechaniken
# ------------------------------------------------------------
fig = px.line(
    seasonal_trends,
    x="chart_week",
    y="streams",
    title="Globale Streaming‑Trends & Key Events (2024–2025)",
    labels={"streams": "Gesamt‑Streams", "chart_week": "Woche"},
    template="plotly_dark"
)

# Superstar‑Releases
fig.add_annotation(
    x="2024-04-25", y=3605841989,
    text="Taylor Swift: Album Release (TTPD)",
    showarrow=True, arrowhead=2, opacity=0.8,
    ax=-60, ay=-40, bgcolor="#636EFA", bordercolor="white"
)

fig.add_annotation(
    x="2025-10-09", y=3205166486,
    text="Swift: Single (TFoO) & Album (TLoS)",
    showarrow=True, arrowhead=2, opacity=0.8,
    ax=-90, ay=-60, bgcolor="#00CC96", bordercolor="white"
)

# Sommerhits
fig.add_annotation(
    x="2024-05-23", y=3184277186,
    text="Sommerhits",
    showarrow=True, arrowhead=2, opacity=0.9,
    ax=50, ay=-40, bgcolor="#FF8C00", bordercolor="white"
)

# Weihnachten
fig.add_annotation(
    x="2024-12-26", y=3893017659,
    text="Weihnachtshits '24",
    showarrow=True, arrowhead=2, opacity=0.8,
    ax=0, ay=-50, bgcolor="#EF553B", bordercolor="white"
)

fig.add_annotation(
    x="2025-12-25", y=3667133246,
    text="Weihnachtshits '25",
    showarrow=True, arrowhead=2, opacity=0.8,
    ax=-40, ay=-60, bgcolor="#EF553B", bordercolor="white"
)

fig.update_traces(line_color="#1DB954", line_width=2)

# Plot anzeigen
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ------------------------------------------------------------
# Peak-Wochen identifizieren
# ------------------------------------------------------------

# Durchschnitt und Standardabweichung der Streams berechnen
mean_streams = seasonal_trends['streams'].mean()
std_streams = seasonal_trends['streams'].std()

# Threshold definieren: alles, was mehr als 1.5 Standardabweichungen über dem Durchschnitt liegt
threshold = mean_streams + 1.5 * std_streams

# Peak-Wochen identifizieren
peaks = seasonal_trends[seasonal_trends['streams'] > threshold]

# Liste der identifizierten Peak-Wochen erstellen
peak_dates = peaks['chart_week'].tolist()

# ------------------------------------------------------------
# Visualisierung: Top 10 Künstler in den Peak-Wochen
# ------------------------------------------------------------

# Daten für die Peak-Wochen filtern
peak_df_details = df[df['chart_week'].isin(peak_dates)]
top_artists_peaks = peak_df_details[peak_df_details['rank'] <= 10]

fig_peaks = px.bar(
    top_artists_peaks,
    x="chart_week",
    y="streams",
    color="artist_names",
    title="Wer dominierte die Spitzenwochen im Streaming? (Top 10 Künstler)",
    hover_data=["track_name"],
    labels={
        "streams": "Gesamt‑Streams",
        "chart_week": "Woche",
        "artist_names": "Künstler"
    },
    template="plotly_dark"
)

fig_peaks.update_traces(marker_line_color="black", marker_line_width=1) 

fig_peaks.update_layout(barmode="stack")

st.plotly_chart(fig_peaks, use_container_width=True)

# ------------------------------------------------------------
# Marktmechaniken erklären
# ------------------------------------------------------------

with st.expander("🔍 Die drei Kräfte hinter den Streaming-Peaks"):

    # 1. Superstar Releases
    st.subheader("1️⃣ Superstar‑Releases (Taylor Swift)")
    st.markdown("""
    **Wochen:** April 2024 & Oktober 2025  
    
    **April 2024:**  
    Der Peak wird durch das Release von *The Tortured Poets Department* ausgelöst.  
    Der Top‑Song *Fortnight* generiert über **102 Mio. Streams**, und Taylor 
    Swift dominiert fast die gesamten Top 5.
    
    **Oktober 2025:**  
    Der stärkste Ausschlag im gesamten Datensatz.  
    Mit einem Top‑1‑Share von **4,02 %** deutet alles auf einen massiven 
    Überraschungs‑Release hin (*The Fate of Ophelia*).
    
    **Erkenntnis:**  
    Superstar‑Peaks sind **Anomalien**: Sie entstehen nicht organisch, 
    sondern wirken wie eine Schockwelle, die das gesamte System kurzfristig 
    verzerrt. Die Diversität des Marktes bricht ein.
    """)
    
    # 2. Weihnachten
    st.subheader("2️⃣ Weihnachtshits (zyklische Saisonalität)")
    st.markdown("""
    **Wochen:** Dezember 2024 & Dezember 2025  
    
    **Muster:**  
    Ende Dezember übernehmen die Klassiker die Charts.  
    Mariah Carey und Wham! verdrängen aktuelle Pophits fast vollständig aus den Top 5.
    
    **Dynamik:**  
    - 2024 führt Mariah Carey mit **92,5 Mio. Streams**  
    - 2025 führt Wham! (*Last Christmas*) mit **85,8 Mio. Streams**
    
    **Erkenntnisse:**  
    Das Streaming‑Volumen ist extrem hoch, aber die **Diversity sinkt**, 
    da fast alle Nutzer dieselben 10–20 Klassiker hören.
    """)
    
    # 3. Sommerhits
    st.subheader("3️⃣ Sommer‑Hits (Organisches Wachstum)")
    st.markdown("""
    **Woche:** Mai 2024  
    
    **Charakter:**  
    Im Gegensatz zu den Swift‑Peaks sehen wir hier eine **bunte Mischung**:
    - Tommy Richman: *Million Dollar Baby* (Viral-Hit) – **70,98 Mio. Streams**
    - Billie Ellish: *Hit me hard and soft* (Album-Release)
        - *Lunch*: **65,58 Mio. Streams**
        - *Chihiro*: **56,15 Mio. Streams**
        - *Birds of a Feather*: **46,94 Mio. Streams**
     - Sabrina Carpenter: *Espresso* (Sommerhit) – **63,97 Mio. Streams**
     - Kendrick Lamar: *Not like us* (Diss-Track gegen Drake) – **63,90 Mio. Streams**
    
    **Erkenntnisse:**  
    Dies ist die **gesündeste Form eines Peaks**.  
    Das hohe Volumen verteilt sich auf verschiedene Künstler und Genres.  
    Der Top‑1‑Share liegt bei **2,23 %**, das ein Zeichen für starken Wettbewerb ist.
    """)

st.markdown("---")

# ------------------------------------------------------------
# Abschnitt: Volumen vs. Vielfalt – Dominanz & Diversität
# ------------------------------------------------------------

st.header("📊 Wie sich Marktvolumen und Künstlerbreite entwickeln")

st.markdown("""
Dieser Abschnitt untersucht, wie sich **Streaming‑Volumen** und 
**künstlerische Vielfalt** in den Top 10 der globalen Charts entwickeln. 
Die Kombination aus Area‑Chart (Volumen) und Bar‑Chart (Diversität) zeigt, 
wie stark einzelne Künstler den Markt dominieren oder wie breit der 
Wettbewerb verteilt ist.
""")

st.markdown("---")

# ------------------------------------------------------------
# TOP 10 Künstler pro Woche
# ------------------------------------------------------------
top_artists_weekly = df[df['rank'] <= 10] \
    .groupby(['chart_week', 'artist_names'])['streams'] \
    .sum().reset_index()

# Anzahl eines Künstlers in den TOP 10 pro Woche
top_artists_count = top_artists_weekly \
    .groupby(['chart_week', 'artist_names']) \
    .size().reset_index(name='dominance')

top_artists_count = top_artists_count.sort_values('chart_week')

# ------------------------------------------------------------
# TOP 5 Künstler für übersichtliche Visualisierung
# ------------------------------------------------------------
top_overall_artists = df.groupby('artist_names')['streams'] \
    .sum().nlargest(5).index

df_filtered = top_artists_weekly[
    top_artists_weekly['artist_names'].isin(top_overall_artists)
]

# ------------------------------------------------------------
# Area‑Chart: Dominanz der Top‑Künstler
# ------------------------------------------------------------
fig_area = px.area(
    df_filtered,
    x="chart_week",
    y="streams",
    color="artist_names",
    title="Wöchentliche Dominanz der Top‑Künstler",
    labels={
        'streams': 'Streams in den Top 10',
        'chart_week': 'Woche',
        'artist_names': 'Künstler'
    },
    template="plotly_dark",
    line_group="artist_names"
)

st.plotly_chart(fig_area, use_container_width=True)

st.markdown("---")

# ------------------------------------------------------------
# Diversität: Anzahl eindeutiger Künstler pro Woche
# ------------------------------------------------------------
diversity_analysis = df[df['rank'] <= 10] \
    .groupby('chart_week')['artist_names'] \
    .nunique().reset_index()

diversity_analysis.columns = ['chart_week', 'unique_artists']

fig_div = px.bar(
    diversity_analysis,
    x='chart_week',
    y='unique_artists',
    title='Chart‑Diversität: Anzahl eindeutiger Künstler in den Top 10',
    labels={
        'unique_artists': 'Anzahl verschiedener Künstler',
        'chart_week': 'Woche'
    },
    template='plotly_dark',
    color='unique_artists',
    color_continuous_scale='RdYlGn'
)

fig_div.add_hline(
    y=10,
    line_dash='dash',
    line_color='white',
    annotation_text='Max. Diversität'
)

st.plotly_chart(fig_div, use_container_width=True)

# ------------------------------------------------------------
# Interpretation der Marktmechaniken
# ------------------------------------------------------------

with st.expander("🔍 Wie Dominanz und Vielfalt den Markt formen"):

    st.markdown("""
    Die beiden Grafiken zeigen, **wie unterschiedlich Marktpeaks entstehen** 
    und wie stark sie die künstlerische Vielfalt beeinflussen. Während der 
    erste Abschnitt konkrete Beispiele beleuchtet, fokussiert sich 
    dieser Teil auf die **übergeordneten Muster**.
    """)
    
    # 1. Monokulturelle Peaks
    st.markdown("""
    ### 1️⃣ Monokulturelle Peaks (Superstar‑Effekt)
    
    In einigen Wochen steigt das Streaming‑Volumen sprunghaft an, 
    während die Zahl der unterschiedlichen Künstler in den Top 10 
    gleichzeitig stark sinkt.
    
    **Was die Grafik zeigt:**
    - Das Volumen schießt nach oben.
    - Die Diversität fällt auf nur wenige Künstler.
    - Die Area‑Chart wird von einer einzigen Farbe dominiert.
    
    **Interpretation:**  
    Solche Peaks entstehen, wenn ein einzelner Künstler die Charts 
    nahezu vollständig kontrolliert.
    Das System wird kurzfristig **monokulturell**: 
    Hohe Nutzung, aber geringe Vielfalt.
    """)
    
    # 2. Saisonale Konzentration
    st.markdown("""
    ### 2️⃣ Saisonale Konzentration (Weihnachten)
    
    Rund um die Feiertage steigt das Gesamtvolumen ebenfalls deutlich an, 
    allerdings mit einem anderen Muster als bei den Superstar‑Releases.
    
    **Was die Grafik zeigt:**
    - Das Volumen steigt stark an.  
    - Die Diversität sinkt, aber nicht auf ein Minimum.  
    - Mehrere Künstler teilen sich die Top‑Plätze. 
    
    **Interpretation:**  
    Weihnachten erzeugt eine wiederkehrende, saisonale Dominanz weniger Klassiker.  
    Der Markt wird homogener, aber nicht vollständig einseitig.
    """)
    
    # 3. Organische Vielfalt
    st.markdown("""
    ### 3️⃣ Organische Vielfalt (Sommer‑Plateaus)
    
    In den Sommermonaten zeigt sich ein stabileres, wettbewerbsorientiertes Marktverhalten.
    
    **Was die Grafik zeigt:**
    - Das Volumen bleibt relativ konstant.
    - Die Diversität erreicht häufig den Maximalwert. 
    - Viele Künstler teilen sich die Top 10.
    
    **Interpretation:**  
    Dies ist die „gesündeste“ Marktphase:  
    Hohe Vielfalt, breiter Wettbewerb, keine einzelne dominante Kraft.  
    Das Streaming‑Verhalten ist hier am diversesten und am wenigsten vorhersehbar.
    """)

st.markdown("---")

# ------------------------------------------------------------
# Abschnitt: Nachhaltigkeit vs. Hype – Rolling Mean & Growth Dynamics
# ------------------------------------------------------------

st.header("📈 Marktanteile und Wachstum im Zeitverlauf")

st.markdown("""
Dieser Abschnitt untersucht, wie sich Marktanteile der führenden Künstler über die Zeit entwickeln
und welche Dynamiken hinter nachhaltigem Wachstum oder kurzfristigen Hype‑Peaks stehen.
""")

# ------------------------------------------------------------
# Daten vorbereiten
# ------------------------------------------------------------

# Auf TOP 10 jeder Woche filtern
top_10_weekly = df[df['rank'] <= 10].copy()

# Summe der Streams pro Woche
weekly_total = top_10_weekly.groupby('chart_week')['streams'].sum()

# Stream‑Share pro Künstler und Woche
artist_dominance = top_10_weekly.groupby(['chart_week', 'artist_names'])['streams'] \
    .sum().reset_index()

artist_dominance['stream_share'] = artist_dominance.apply(
    lambda row: (row['streams'] / weekly_total[row['chart_week']]) * 100,
    axis=1
)

# Top‑Künstler auswählen
top_artist_list = artist_dominance.groupby('artist_names')['streams'] \
    .mean().nlargest(10).index

df_growth = artist_dominance[
    artist_dominance['artist_names'].isin(top_artist_list)
].copy()

# Rolling Mean (4 Wochen)
df_growth['rolling_avg'] = df_growth.groupby('artist_names')['stream_share'] \
    .transform(lambda x: x.rolling(window=4, min_periods=1).mean())

# Wachstumsrate
df_growth['growth_rate'] = df_growth.groupby('artist_names')['stream_share'] \
    .transform(lambda x: x.pct_change() * 100)

# Cleanup
df_growth['growth_rate'] = df_growth['growth_rate'] \
    .replace([float('inf'), -float('inf')], 0).fillna(0)

st.markdown("---")

# ------------------------------------------------------------
# Visualisierung 1: Rolling Mean
# ------------------------------------------------------------
fig_rolling = px.line(
    df_growth,
    x='chart_week',
    y='rolling_avg',
    color='artist_names',
    title='Geglätteter Trend: 4‑Wochen Rolling Mean des Marktanteils',
    labels={
        'rolling_avg': 'Marktanteil (4W‑Schnitt %)',
        'artist_names': 'Künstler',
        'chart_week': 'Woche'
    },
    template='plotly_dark'
)

st.plotly_chart(fig_rolling, use_container_width=True)

st.markdown("---")

# ------------------------------------------------------------
# Visualisierung 2: Growth Dynamics
# ------------------------------------------------------------
fig_growth = px.scatter(
    df_growth,
    x='chart_week',
    y='growth_rate',
    color='artist_names',
    size='stream_share',
    title='Wachstums‑Dynamik: Wer explodiert in den Charts?',
    labels={
        'growth_rate': 'Wachstumsrate (%)',
        'chart_week': 'Woche',
        'artist_names': 'Künstler'
    },
    template='plotly_dark'
)

fig_growth.add_hline(y=0, line_dash="dash", line_color="gray")

st.plotly_chart(fig_growth, use_container_width=True)

# ------------------------------------------------------------
# Interpretation (Expander)
# ------------------------------------------------------------
with st.expander("🔍 Nachhaltige Trends vs. Hype-Explosionen"):
    
    st.markdown("""
    ## 📌 Nachhaltigkeit vs. Hype (Rolling Mean)

    Der 4‑Wochen‑Rolling‑Mean glättet kurzfristige Schwankungen und legt die **echten Karrieretrends** offen:

    **Plateau‑Bildung:**  
    Künstler mit stabilen Rolling‑Mean‑Kurven etablieren sich nachhaltig im Markt.  
    Ein kontinuierlicher Anstieg gefolgt von einer stabilen Phase deutet auf **dauerhafte Relevanz** hin.

    **Peak‑Verfall:**  
    Event‑getriebene Peaks fallen nach einem extremen Ausschlag schnell wieder ab.  
    Das ist typisch für **Superstar‑Releases**, die kurzfristig dominieren, aber nicht langfristig tragen.
    """)

    st.markdown("""
    ## 📌 Marktdynamik & Breakout‑Events (Scatter Plot)

    Der Scatter‑Plot zeigt, wie unterschiedlich Künstler an Fahrt gewinnen:

    **Virale Explosionen:**  
    Extreme Wachstums‑Ausreißer über 500% bis 1.000% innerhalb einer Woche markieren **keine organischen Trends**,   
    sondern globale Events, Releases oder virale Momente (&rarr; Taylor Swift im April 2024 oder Oktober 2025).

    **Volumen vs. Geschwindigkeit:**  
    Etablierte Künstler (große Punkte) = hoher Marktanteil  
    Newcomer (kleine Punkte) = geringerer Marktanteil, aber oft **explosives Wachstum** 
    """)

st.markdown(
    """
    <div style='text-align: center; margin-top: 50px; color: gray; font-size: 12px;'>
        © Eva Wolff Fabris · 23. Januar 2026 · Musiktrends vorhersagen und verstehen · Alle Rechte vorbehalten.
    </div>
    """,
    unsafe_allow_html=True
)
