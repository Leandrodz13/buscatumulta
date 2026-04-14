import streamlit as st
import asyncio
import pandas as pd
import os
import sys


# 2. Asegurar rutas de módulos para encontrar la carpeta 'comunas'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comunas.santiago import consultar_santiago

# 3. Configuración de página
st.set_page_config(page_title="Busca Tu Parte", page_icon="🔍", layout="wide")

# Estilos personalizados (Tu diseño original)
st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #022873; color: white; border-radius: 10px; font-weight: bold; height: 3em; }
    .disclaimer { font-size: 11px; color: #666; text-align: justify; margin-top: 50px; border-top: 1px solid #eee; padding-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔍 Busca tu Parte")
st.write("Consulta centralizada de infracciones de tránsito.")

# Entrada de datos
patente = st.text_input("Ingrese patente (ej: ABCD12 O AB1234)", placeholder="ABCD12").upper().strip().replace("-", "")

if st.button("Buscar en todas las municipalidades"):
    if len(patente) >= 6:
        # Registro de comunas
        comunas = [("Santiago", consultar_santiago)]
        
        for nombre_comuna, funcion in comunas:
            with st.spinner(f"Consultando {nombre_comuna}... (El portal municipal es lento, por favor espera)"):
                try:
                    # --- CORRECCIÓN CLAVE AQUÍ ---
                    # Usamos asyncio.run() directamente para ser compatibles con el servidor
                    pend, pag, msg = asyncio.run(funcion(patente))

                    if msg == "Éxito":
                        st.subheader(f"📍 Municipio: {nombre_comuna}")
                        
                        # Layout de dos columnas
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### 🚩 Por Pagar")
                            if pend:
                                df_pend = pd.DataFrame(pend)
                                # Intentamos asignar nombres de columnas si la tabla trae los 11 campos esperados
                                if len(df_pend.columns) >= 11:
                                    df_pend.columns = ["Acción", "Emisión", "Juzgado", "PPU", "Monto", "Denuncia", "Infracción", "RUT", "Vence", "Rol", "Estado"]
                                    st.dataframe(df_pend.drop(columns=["Acción"]), use_container_width=True)
                                else:
                                    st.dataframe(df_pend, use_container_width=True)
                            else:
                                st.success("No se registran multas pendientes.")

                        with col2:
                            st.markdown("### ✅ Historial de Pagadas")
                            if pag:
                                df_pag = pd.DataFrame(pag)
                                if len(df_pag.columns) >= 11:
                                    df_pag.columns = ["Acción", "Emisión", "Juzgado", "PPU", "Monto", "Denuncia", "Infracción", "RUT", "Pago", "Rol", "Estado"]
                                    st.dataframe(df_pag.drop(columns=["Acción"]), use_container_width=True)
                                else:
                                    st.dataframe(df_pag, use_container_width=True)
                            else:
                                st.info("No hay registro de multas pagadas.")
                    else:
                        # Si el bot captura un error de tiempo o de la página, lo muestra aquí de forma elegante
                        st.warning(f"Aviso de {nombre_comuna}: {msg}")

                except Exception as e:
                    # Esto nos mostrará el error técnico real si algo falla en el servidor
                    st.error(f"Error técnico al conectar con {nombre_comuna}: {str(e)}")
    else:
        st.warning("Ingrese una patente válida de 6 caracteres.")

# Footer (Tu diseño original)
st.markdown("""
<div class="disclaimer">
    <b>Aviso Legal:</b> buscatuparte.cl es una herramienta independiente. Los datos son obtenidos de portales públicos. 
    Esta plataforma no procesa pagos. Ante dudas, contacte al Juzgado de Policía Local.
</div>
""", unsafe_allow_html=True)
