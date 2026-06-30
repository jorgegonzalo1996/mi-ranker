import streamlit as st
import pandas as pd
import random

# Configuración del algoritmo Elo
K_FACTOR = 32  
INITIAL_ELO = 1200

# ⚠️ PEGA AQUÍ TU ENLACE MODIFICADO DE GOOGLE SHEETS
# Recuerda que debe terminar en /export?format=csv
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-......./pub?output=csv"def cargar_datos_online():
    try:
        df = pd.read_csv(SHEET_URL)
        return df
    except Exception as e:
        st.error("Error al conectar con Google Sheets. Verifica tu enlace.")
        st.stop()

st.set_page_config(page_title="Ranker 1vs1 Online", layout="centered")
st.title("🏆 Mi Ranker 1vs1 Online")

if "df" not in st.session_state:
    st.session_state.df = cargar_datos_online()

df = st.session_state.df

if "rivales" not in st.session_state:
    j1_idx = df["Partidos"].idxmin()
    j1_elo = df.loc[j1_idx, "Elo"]
    candidatos = df[df.index != j1_idx]
    candidatos_cercanos = candidatos.iloc[(candidatos["Elo"] - j1_elo).abs().argsort()[:30]]
    j2_idx = random.choice(candidatos_cercanos.index.tolist())
    st.session_state.rivales = (j1_idx, j2_idx)

idx_a, idx_b = st.session_state.rivales
jugador_a = df.loc[idx_a, "Jugador"]
jugador_b = df.loc[idx_b, "Jugador"]

st.write("### ¿Quién es mejor?")
col1, col2 = st.columns(2)

def calcular_elo(rating_ganador, rating_perdedor):
    esperada_ganador = 1 / (1 + 10 ** ((rating_perdedor - rating_ganador) / 400))
    nuevo_ganador = rating_ganador + K_FACTOR * (1 - esperada_ganador)
    nuevo_perdedor = rating_perdedor + K_FACTOR * (0 - (1 - esperada_ganador))
    return round(nuevo_ganador), round(nuevo_perdedor)

with col1:
    if st.button(f"👉 {jugador_a}", use_container_width=True):
        nuevo_a, nuevo_b = calcular_elo(df.loc[idx_a, "Elo"], df.loc[idx_b, "Elo"])
        df.loc[idx_a, "Elo"], df.loc[idx_b, "Elo"] = nuevo_a, nuevo_b
        df.loc[idx_a, "Partidos"] += 1; df.loc[idx_b, "Partidos"] += 1
        del st.session_state.rivales; st.rerun()

with col2:
    if st.button(f"👉 {jugador_b}", use_container_width=True):
        nuevo_b, nuevo_a = calcular_elo(df.loc[idx_b, "Elo"], df.loc[idx_a, "Elo"])
        df.loc[idx_a, "Elo"], df.loc[idx_b, "Elo"] = nuevo_a, nuevo_b
        df.loc[idx_a, "Partidos"] += 1; df.loc[idx_b, "Partidos"] += 1
        del st.session_state.rivales; st.rerun()

st.markdown("---")
st.write("### 📊 Top Actual")
ranking_actual = df.sort_values(by="Elo", ascending=False).reset_index(drop=True)
ranking_actual.index += 1
st.dataframe(ranking_actual[["Jugador", "Elo", "Partidos"]], use_container_width=True, height=400)
