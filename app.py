import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Organizador de Tiers NBA", layout="wide")

# 1. CONEXIÓN A GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

# URL Limpia sin parámetros extras de gid
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1NAxcX0MNJkQdIZ_aCz_qqc6z4y4MWq6msTEaJRiJUzQ/edit"

# Función para leer los datos limpios de tu enlace
def cargar_datos():
    df = conn.read(
        spreadsheet=SPREADSHEET_URL,
        ttl=0
    )
    
    # Limpiar nombres de columnas eliminando espacios
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
                
                # Intentar actualizar especificando los parámetros requeridos
                try:
                    conn.update(
                        spreadsheet=SPREADSHEET_URL,
                        data=df
                    )
                except Exception:
                    # Alternativa si el backend bloquea updates globales sin cuenta de servicio en la nube
                    st.error("Error de permisos de escritura. Asegúrate de añadir las credenciales en Secrets si continúa.")
                
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
                    conn.update(
                        spreadsheet=SPREADSHEET_URL,
                        data=df
                    )
                    st.toast(f"{jugador_selec} movido al Tier {nuevo_tier}")
                    st.rerun()
        else:
            st.caption("Aún no hay jugadores en este tier.")
