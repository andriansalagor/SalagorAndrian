import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json

# -----------------------------
# CONFIGURAZIONE GENERALE APP
# -----------------------------
st.set_page_config(
    page_title="Qualità dell'aria a Milano",
    layout="wide"
)

# -----------------------------
# SEZIONE INFORMATIVA SUGLI INQUINANTI
# -----------------------------
def mostra_inquinanti():
    st.header("📌 Conoscere gli inquinanti atmosferici")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("PM10")
        st.write(
            "Particelle sottili con diametro inferiore a 10 µm, "
            "provenienti principalmente da traffico e riscaldamento urbano."
        )
        st.error(
            "Possono raggiungere i polmoni causando problemi respiratori e cardiovascolari."
        )

    with col2:
        st.subheader("NO₂ – Biossido di azoto")
        st.write(
            "Gas prodotto dai motori dei veicoli e dalla combustione di combustibili fossili."
        )
        st.error(
            "Può irritare le vie respiratorie e peggiorare l’asma."
        )

    with col3:
        st.subheader("O₃ – Ozono")
        st.write(
            "Si forma al suolo tramite reazioni chimiche tra altri inquinanti e luce solare."
        )
        st.error(
            "È irritante, soprattutto nei mesi estivi."
        )

# -----------------------------
# CARICAMENTO E PULIZIA DEI DATI
# -----------------------------
@st.cache_data
def prepara_dati():
    file_json_annuali = [
        "aria15.json", "aria16.json", "aria17.json",
        "aria18.json", "aria19.json", "aria20.json",
        "aria23.json", "aria24.json", "aria25.json"
    ]

    lista_dati = []

    for file_name in file_json_annuali:
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                contenuto = json.load(f)
                lista_dati.append(pd.DataFrame(contenuto))
        except FileNotFoundError:
            st.warning(f"Attenzione: {file_name} non trovato!")

    df = pd.concat(lista_dati, ignore_index=True)

    # Pulizia
    df["valore"] = pd.to_numeric(df["valore"], errors="coerce")
    df["data"] = pd.to_datetime(df["data"])
    df["anno"] = df["data"].dt.year
    df = df.dropna(subset=["valore"])

    # Stazioni
    with open("dati_milano.json", "r", encoding="utf-8") as f:
        geojson = json.load(f)

    stazioni = [
        {"stazione_id": int(feat["properties"]["id_amat"]),
         "nome_stazione": feat["properties"]["nome"]}
        for feat in geojson["features"]
    ]

    df_stazioni = pd.DataFrame(stazioni)

    # Unione dati misurazioni e stazioni
    df["stazione_id"] = df["stazione_id"].astype(int)
    df_completo = pd.merge(df, df_stazioni, on="stazione_id")

    return df_completo

# -----------------------------
# FUNZIONE PRINCIPALE
# -----------------------------
def avvia_app():
    st.title("🌍 Monitoraggio qualità dell’aria a Milano")
    st.markdown(
        "App interattiva per analizzare inquinanti atmosferici "
        "usando i dati ufficiali del Comune di Milano."
    )

    mostra_inquinanti()

    df = prepara_dati()

    # Sidebar
    st.sidebar.header("⚙️ Selezione parametri")
    lista_inquinanti = sorted(df["inquinante"].unique())
    inquinante = st.sidebar.selectbox("Scegli un inquinante", lista_inquinanti)

    # -------------------------
    # ANALISI TEMPORALE
    # -------------------------
    st.divider()
    st.header(f"📈 Evoluzione annuale di {inquinante}")

    media_annuale = (
        df[df["inquinante"] == inquinante]
        .groupby("anno")["valore"]
        .mean()
    )

    col_plot, col_note = st.columns([2, 1])

    with col_plot:
        fig, ax = plt.subplots(figsize=(10, 5))
        media_annuale.plot(ax=ax, marker="o")
        ax.set_ylabel("Valore medio (µg/m³)")
        ax.grid(alpha=0.3)
        st.pyplot(fig)

    with col_note:
        st.write("**Osservazioni:**")
        if len(media_annuale) > 1:
            delta = media_annuale.iloc[-1] - media_annuale.iloc[0]
            trend = "diminuito" if delta < 0 else "aumentato"
            st.write(f"- L’inquinamento è **{trend}** nel periodo analizzato.")
        st.write("- Picchi possono dipendere da eventi climatici o lockdown.")

    # -------------------------
    # STAZIONI PIÙ CRITICHE
    # -------------------------
    st.divider()
    st.header(f"🏭 Stazioni più inquinate per {inquinante}")

    media_stazioni = (
        df[df["inquinante"] == inquinante]
        .groupby("nome_stazione")["valore"]
        .mean()
        .sort_values(ascending=False)
        .head(5)
    )

    c_plot, c_tab = st.columns(2)

    with c_plot:
        fig2, ax2 = plt.subplots()
        media_stazioni.plot(kind="barh", ax=ax2)
        ax2.invert_yaxis()
        ax2.set_xlabel("Media periodo (µg/m³)")
        st.pyplot(fig2)

    with c_tab:
        st.table(media_stazioni.reset_index().rename(columns={"valore": "Media µg/m³"}))

    # -------------------------
    # DETTAGLIO ULTIMO ANNO
    # -------------------------
    st.divider()
    st.header("📆 Analisi dettagliata ultimo anno disponibile")

    stazione = st.selectbox(
        "Seleziona una stazione",
        sorted(df["nome_stazione"].unique())
    )

    anno_corrente = df["anno"].max()

    df_focus = df[
        (df["nome_stazione"] == stazione) &
        (df["inquinante"] == inquinante) &
        (df["anno"] == anno_corrente)
    ].sort_values("data")

    if not df_focus.empty:
        fig3, ax3 = plt.subplots(figsize=(12, 4))
        ax3.plot(df_focus["data"], df_focus["valore"])
        ax3.fill_between(df_focus["data"], df_focus["valore"], alpha=0.2)
        ax3.set_ylabel("µg/m³")
        st.pyplot(fig3)

        st.info(
            "Il grafico evidenzia picchi e variazioni stagionali "
            "dell’inquinante selezionato."
        )
    else:
        st.warning("Nessun dato disponibile per la selezione effettuata.")

# -----------------------------
# AVVIO APP
# -----------------------------
if __name__ == "__main__":
    avvia_app()
