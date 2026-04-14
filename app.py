import streamlit as st
import asyncio
import pandas as pd
import os
import sys

# --- CONFIGURACIÓN DE ENTORNO ---
# Instalación automática de Playwright en el servidor de Streamlit
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    try:
        os.system("playwright install chromium")
    except Exception as e:
        st.error(f"Error instalando dependencias: {e}")

# Asegurar que Python encuentre la carpeta 'comunas'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comunas.santiago import consultar_santiago

# --- INTERFAZ VISUAL ---
st.set_page_config(page_title="Busca Tu Multa", page_icon="🔍", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #022873; color: white; border-radius: 10px; height: 3em; font-weight: bold; }
    .disclaimer { font-size: 11px; color: #666; text-align: justify; margin-top: 50px; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔍 Busca tu Multa")
st.write("Consulta centralizada de infracciones de tránsito en Chile.")

patente = st.text_input("Ingrese patente", placeholder="Ej: ABCD12 o AB1234").upper().strip().replace("-", "")

if st.button("Buscar en todas las municipalidades"):
    if len(patente) >= 6:
        # Registro de comunas disponibles
        tareas = [
            ("Santiago", consultar_santiago),
        ]
        
        resultados_totales = False
        
        for nombre_comuna, funcion_busqueda in tareas:
            with st.expander(f"Resultados en {nombre_comuna}", expanded=True):
                with st.spinner(f"Consultando base de datos de {nombre_comuna}..."):
                    try:
                        # Manejo de bucle asíncrono compatible con Streamlit Cloud
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        df, msg = loop.run_until_complete(funcion_busqueda(patente))
                        loop.close()
                        
                        if df is not None:
                            st.dataframe(df, use_container_width=True)
                            resultados_totales = True
                        else:
                            st.info(f"✅ {msg}")
                    except Exception as e:
                        st.error(f"La conexión con {nombre_comuna} tardó demasiado o falló.")
        
        if not resultados_totales:
            st.toast("Búsqueda finalizada sin multas pendientes.")
            
    else:
        st.warning("Por favor, ingrese una patente válida (6 caracteres).")

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div class="disclaimer">
    <b>Aviso Legal:</b> buscatumulta.cl es una plataforma independiente y no gubernamental. 
    Los datos mostrados son de carácter referencial, obtenidos en tiempo real desde portales públicos municipales. 
    Esta aplicación no realiza cobros ni gestiona pagos; para trámites oficiales, diríjase al Juzgado de Policía Local respectivo.
</div>
""", unsafe_allow_html=True)
