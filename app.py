import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Organizador de Tiers NBA", layout="wide")

# 1. CONEXIÓN A GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para leer los datos limpios de tu enlace
def cargar_datos():
    # Lee el enlace directo de tu hoja
    df = conn.read(
        spreadsheet="https://docs.google.com/spreadsheets/d/1NAxcX0MNJkQdIZ_aCz_qqc6z4y4MWq6msTEaJRiJUzQ/edit?gid=0#gid=0",
        usecols=[0, 1, 2, 3], 
        ttl=0
    )
    # Limpieza básica de registros vacíos y tipos de datos
    df = df.dropna(subset=["ID", "Jugador"])
    df["ID"] = df["ID"].astype(int)
    df["Tier"] = df["Tier"].fillna(0).astype(int)
    return df

# Inicializar datos en la sesión de Streamlit
if "df_jugadores" not in st.session_state:
    st.session_state.df_jugadores = cargar_datos()
if "jugador_actual" not in st.session_state:
    st.session_state.jugador_actual = None
if "tier_propuesto" not in st.session_state:
    st.session_state.tier_propuesto = 5

df = st.session_state.df_jugadores

# OBJETIVOS POR TIER PARA TUS 857 JUGADORES
OBJETIVOS = {1: 171, 2: 154, 3: 129, 4: 111, 5: 94, 6: 77, 7: 60, 8: 43, 9: 18}

# Buscar el siguiente jugador de la lista cuyo Tier sea 0
def obtener_siguiente():
    sin_clasificar = df[df["Tier"] == 0]
    if not sin_clasificar.empty:
        st.session_state.jugador_actual = sin_clasificar.iloc[0]
        st.session_state.tier_propuesto = 5
    else:
        st.session_state.jugador_actual = None

if st.session_state.jugador_actual is None:
    obtener_siguiente()

st.title("🏀 Organizador de Tiers - Juego de Cartas")

# ==========================================
# SECCIÓN 1: FILTRO PIRAMIDAL
# ==========================================
st.write("---")
st.subheader("🔄 Clasificador Rápido")

if st.session_state.jugador_actual is not None:
    j = st.session_state.jugador_actual
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"### **{j['Jugador']}** ({j['Posicion']})")
        st.metric(label="Tier Propuesto", value=f"Tier {st.session_state.tier_propuesto}")
        
        b_mejor, b_quedar, b_peor = st.columns(3)
        
        with b_mejor:
            if st.button("🔼 Es Mejor") and st.session_state.tier_propuesto < 9:
                st.session_state.tier_propuesto += 1
                st.rerun()
                
        with b_quedar:
            if st.button("🤝 Guardar en este Tier", type="primary"):
                df.loc[df["ID"] == j["ID"], "Tier"] = st.session_state.tier_propuesto
                # Sincroniza mandando de vuelta el DataFrame entero a tu URL
                conn.update(
                    spreadsheet="https://docs.google.com/spreadsheets/d/1NAxcX0MNJkQdIZ_aCz_qqc6z4y4MWq6msTEaJRiJUzQ/edit?gid=0#gid=0",
                    data=df
                )
                st.toast(f"¡{j['Jugador']} guardado en Tier {st.session_state.tier_propuesto}!")
                obtener_siguiente()
                st.rerun()
                
        with b_peor:
            if st.button("🔽 Es Peor") and st.session_state.tier_propuesto > 1:
                st.session_state.tier_propuesto -= 1
                st.rerun()
else:
    st.success("🎉 ¡Todos los jugadores han sido clasificados!")

# ==========================================
# SECCIÓN 2: VISTA GLOBAL Y SUSTITUCIONES
# ==========================================
st.write("---")
st.subheader("📋 Panel Global de Tiers y Modificaciones")

tabs = st.tabs([f"Tier {i}" for i in range(1, 10)])

for idx, tab in enumerate(tabs):
    tier_num = idx + 1
    with tab:
        jugadores_en_tier = df[df["Tier"] == tier_num]
        total_actual = len(jugadores_en_tier
