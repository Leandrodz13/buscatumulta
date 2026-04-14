import streamlit as st
import asyncio
import pandas as pd
from comunas.santiago import consultar_santiago
# Aquí importarás las nuevas comunas a futuro, ej:
# from comunas.providencia import consultar_providencia

# Configuración visual de la página
st.set_page_config(page_title="Busca Tu Multa", page_icon="🔍", layout="centered")

# Estilos para que se vea como una App
st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #022873; color: white; border-radius: 10px; }
    .disclaimer { font-size: 11px; color: #666; text-align: justify; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# Logo y Título
st.title("🔍 Busca tu Multa")
st.write("Consulta centralizada de infracciones de tránsito en Chile.")

# Casilla de búsqueda
patente = st.text_input("Ingrese patente", placeholder="Ej: ABCD12").upper().strip()

if st.button("Buscar en todas las municipalidades"):
    if len(patente) >= 6:
        # Lista de tareas: Aquí es donde la app crece sola
        # Estructura: (Nombre para mostrar, Función de búsqueda)
        tareas = [
            ("Santiago", consultar_santiago),
            # ("Providencia", consultar_providencia),
        ]
        
        resultados_encontrados = False
        
        for nombre_comuna, funcion_busqueda in tareas:
            with st.expander(f"Resultados en {nombre_comuna}", expanded=True):
                with st.spinner(f"Consultando {nombre_comuna}..."):
                    try:
                        # Ejecutamos el bloque de la comuna
                        df, msg = asyncio.run(funcion_busqueda(patente))
                        
                        if df is not None:
                            st.dataframe(df, use_container_width=True)
                            resultados_encontrados = True
                        else:
                            st.info(f"✅ {msg}")
                    except Exception as e:
                        st.error(f"Error al conectar con {nombre_comuna}")
        
        if not resultados_encontrados:
            st.toast("No se encontraron multas en los registros consultados.")
            
    else:
        st.warning("Por favor, ingrese una patente válida de 6 caracteres.")

# Disclaimer Obligatorio
st.markdown("---")
st.markdown("""
<div class="disclaimer">
    <b>Aviso Legal:</b> buscatumulta.cl es una plataforma independiente. Los datos son referenciales y se obtienen 
    en tiempo real desde portales públicos municipales. Para pagos oficiales o apelaciones, diríjase 
    directamente al Juzgado de Policía Local correspondiente.
</div>
""", unsafe_allow_html=True)
