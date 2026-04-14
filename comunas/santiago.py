import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re

async def consultar_santiago(patente):
    async with async_playwright() as p:
        # Configuración del navegador para el servidor
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = await context.new_page()
        
        try:
            # Navegación
            await page.goto("https://tramites.munistgo.cl/pagosjpl/", wait_until="networkidle")
            await page.fill("#ContentPlaceHolder1_txt_placa", patente)
            await page.click("#ContentPlaceHolder1_img_buscar_placa")
            
            # Espera a que carguen las tablas de Telerik
            await page.wait_for_selector("#ContentPlaceHolder1_RadMultiPage1", timeout=10000)
            
            all_data = []

            # Función interna para extraer datos de las tablas gv_pendientes y gv_pagadas
            async def extraer_de_tabla(selector_id, situacion):
                rows = await page.query_selector_all(f"{selector_id} tr")
                tabla_rows = []
                for row in rows:
                    cols = await row.query_selector_all("td")
                    if len(cols) > 2:
                        fila = [await c.inner_text() for c in cols]
                        fila_limpia = [item.strip() for item in fila]
                        # Filtramos mensajes de "No existen datos"
                        if "No existen datos" not in str(fila_limpia):
                            fila_limpia.append(situacion)
                            tabla_rows.append(fila_limpia)
                return tabla_rows

            # Extraer de ambas secciones
            pendientes = await extraer_de_tabla("#ContentPlaceHolder1_gv_pendientes", "🚩 POR PAGAR")
            pagadas = await extraer_de_tabla("#ContentPlaceHolder1_gv_pagadas", "✅ PAGADA")
            
            total_rows = pendientes + pagadas
            await browser.close()

            if not total_rows:
                return None, "No se registran infracciones."

            # Creación del DataFrame con la estructura del sitio
            df = pd.DataFrame(total_rows)
            columnas_base = ["Acción", "Emisión", "Juzgado", "Patente", "Monto", "Denuncia", "Infracción", "RUT", "Pago", "Rol", "Situación"]
            df.columns = columnas_base[:len(df.columns)]
            
            # Limpieza de columnas técnicas
            if "Acción" in df.columns:
                df = df.drop(columns=["Acción"])
            
            # Ordenar por fecha de emisión
            df['Emisión_DT'] = pd.to_datetime(df['Emisión'], dayfirst=True, errors='coerce')
            df = df.sort_values(by='Emisión_DT', ascending=False).drop(columns=['Emisión_DT'])

            return df, "Éxito"

        except Exception as e:
            await browser.close()
            return None, f"Error de conexión: {str(e)}"
