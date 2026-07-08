import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(page_title="Organizador de Tiers NBA", layout="wide")

# CONFIGURACIÓN DE ENLACES
# 1. Tu enlace original de lectura por CSV
CSV_URL = "https://docs.google.com/spreadsheets/d/1NAxcX0MNJkQdIZ_aCz_qqc6z4y4MWq6msTEaJRiJUzQ/export?format=csv&gid=0"

# 2. URL de tu aplicación web de Google Apps Script
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzAQdxdxN2GjpM_tP04GihyidOy2mFYqF1ixWuvMZjUxPELYDbvlAfVfI39f4sh8gDewA/exec"

# Función para leer los datos de forma pública sin credenciales
def cargar_datos():
    df = pd.read_csv(CSV_URL)
    
    # Limpiar nombres de columnas
    df.columns = df.columns.astype(str).str.strip()
    
    # Renombrado inteligente automático
    col_id = [c for c in df.columns if 'id' in c.lower()][0]
    col_jugador = [c for c in df.columns if 'jugador' in c.lower() or 'nombre' in c.lower()][0]
    col_posicion = [c for c in df.columns if 'posic' in c.lower()][0]
    col_tier = [c for c in df.columns if 'tier' in c.lower()][0]
    
    df = df.rename(columns={col_id: "ID", col_jugador: "Jugador", col_posicion: "Posicion", col_tier: "Tier"})
    df = df.dropna(subset=["ID", "Jugador"])
    df["ID"] = df["ID"].astype(int)
    df["Tier"] = df["Tier"].fillna(0).astype(int)
    return df[["ID", "Jugador", "Posicion", "Tier"]]

# Función para guardar datos enviándolos al Webhook de Google Apps Script
def guardar_datos(df_a_guardar):
    # Convertimos el dataframe a formato JSON para mandarlo por HTTP
    data_json = df_a_guardar.to_dict(orient="records")
    
    with st.spinner("Sincronizando con Google Sheets..."):
        try:
            response = requests.post(WEBHOOK_URL, data=json.dumps(data_json), headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                st.success("¡Guardado correctamente en la nube!")
            else:
                st.error(f"Error al guardar. Código de estado: {response.status_code}")
        except Exception as e:
            st.error(f"Error de conexión: {e}")

# Inicializar estados de la sesión
if "df_jugadores" not in st.session_state:
    st.session_state.df_jugadores = cargar_datos()
if "jugador_actual" not in st.session_state:
    st.session_state.jugador_actual = None
if "tier_propuesto" not in st.session_state:
    st.session_state.tier_propuesto = 5

df = st.session_state.df_jugadores

# OBJETIVOS POR TIER PARA LOS 857 JUGADORES
OBJETIVOS = {1: 171, 2: 154, 3: 129, 4: 111, 5: 94, 6: 77, 7: 60, 8: 43, 9: 18}

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
                guardar_datos(df)
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
        total_actual = len(jugadores_en_tier)
        objetivo = OBJETIVOS[tier_num]
        
        if total_actual > objetivo:
            st.warning(f"Cupo: {total_actual} / {objetivo} (¡Te has pasado!)")
        else:
            st.info(f"Cupo: {total_actual} / {objetivo}")
            
        if not jugadores_en_tier.empty:
            col_lista, col_mover = st.columns([3, 2])
            
            with col_lista:
                st.dataframe(jugadores_en_tier[["ID", "Jugador", "Posicion"]], use_container_width=True, hide_index=True)
                
            with col_mover:
                st.write("**🔄 Cambiar de Tier a un jugador:**")
                jugador_selec = st.selectbox(
                    "Selecciona el jugador:", 
                    jugadores_en_tier["Jugador"].tolist(), 
                    key=f"sb_{tier_num}"
                )
                nuevo_tier = st.selectbox(
                    "Mover al Tier:", 
                    list(range(1, 10)), 
                    index=tier_num-1, 
                    key=f"nt_{tier_num}"
                )
                
                if st.button("Confirmar Cambio", key=f"btn_{tier_num}"):
                    id_j = jugadores_en_tier[jugadores_en_tier["Jugador"] == jugador_selec]["ID"].values[0]
                    df.loc[df["ID"] == id_j, "Tier"] = nuevo_tier
                    guardar_datos(df)
                    st.rerun()
        else:
            st.caption("Aún no hay jugadores en este tier.")
