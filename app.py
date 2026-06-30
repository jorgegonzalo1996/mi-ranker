import streamlit as st
import pandas as pd
import random
import requests
import json

# Configuración del algoritmo Elo
K_FACTOR = 32  
INITIAL_ELO = 1200

# Enlaces de conexión (¡Asegúrate de cambiar SCRIPT_URL por tu enlace real de Apps Script!)
SHEET_URL = "https://docs.google.com/spreadsheets/d/15aNvtR-6S3o3shFybzhC_Hi3w8jhOgBSoZ7lrFWB6r8/gviz/tq?tqx=out:csv&sheet=Datos"
SCRIPT_URL = "TU_URL_DE_APPS_SCRIPT_AQUÍ"

def cargar_datos_online():
    try:
        # Añadimos un parámetro aleatorio al final para obligar a Google a enviar los datos más recientes
        url_dinamica = f"{SHEET_URL}&nocache={random.randint(0, 100000)}"
        df = pd.read_csv(url_dinamica)
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        st.stop()

st.set_page_config(page_title="Ranker 1vs1 Online", layout="centered")
st.title("🏆 Mi Ranker 1vs1 Online")

# Cada vez que se recarga la página de forma limpia, se comprueba si hay datos nuevos
if "df" not in st.session_state:
    st.session_state.df = cargar_datos_online()

df = st.session_state.df

# Asegurar tipos numéricos para el cálculo
df["Elo"] = pd.to_numeric(df["Elo"], errors='coerce').fillna(INITIAL_ELO)
df["Partidos"] = pd.to_numeric(df["Partidos"], errors='coerce').fillna(0)

# Selección de rivales
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

def actualizar_y_guardar(idx_ganador, idx_perdedor):
    nuevo_g, nuevo_p = calcular_elo(df.loc[idx_ganador, "Elo"], df.loc[idx_perdedor, "Elo"])
    df.loc[idx_ganador, "Elo"] = nuevo_g
    df.loc[idx_perdedor, "Elo"] = nuevo_p
    df.loc[idx_ganador, "Partidos"] += 1
    df.loc[idx_perdedor, "Partidos"] += 1
    
    st.session_state.df = df
    
    # Preparar la matriz de datos para Google Sheets
    payload = [df.columns.tolist()] + df.values.tolist()
    payload_json = json.dumps(payload)
    
    # Enviar los datos de forma directa asegurando el guardado inmediato
    try:
        response = requests.post(SCRIPT_URL, data=payload_json, headers={"Content-Type": "application/json"})
        if response.status_code != 200:
            st.error("Google Sheets rechazó la actualización.")
    except Exception as e:
        st.error(f"Error al enviar datos: {e}")
        
    del st.session_state.rivales
    st.rerun()

with col1:
    if st.button(f"👉 {jugador_a}", use_container_width=True):
        actualizar_y_guardar(idx_a, idx_b)

with col2:
    if st.button(f"👉 {jugador_b}", use_container_width=True):
        actualizar_y_guardar(idx_b, idx_a)

st.markdown("---")
st.write("### 📊 Top Actual")
ranking_actual = df.sort_values(by="Elo", ascending=False).reset_index(drop=True)
ranking_actual.index += 1
st.dataframe(ranking_actual[["Jugador", "Elo", "Partidos"]], use_container_width=True, height=400)
