import asyncio
from playwright.async_api import async_playwright
import pandas as pd

async def consultar_santiago(patente):
    async with async_playwright() as p:
        # Lanzamos el navegador con configuración para servidor
        browser = await p.chromium.launch(headless=True)
        # Usamos un User Agent moderno para evitar que la muni nos bloquee
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. Navegación con tiempo de espera extendido (90 seg)
            # Santiago a veces tarda mucho en responder el primer 'ping'
            await page.goto("https://tramites.munistgo.cl/pagosjpl/", wait_until="domcontentloaded", timeout=90000)
            
            # 2. Llenado de patente y clic
            await page.fill("#ContentPlaceHolder1_txt_placa", patente)
            await page.click("#ContentPlaceHolder1_img_buscar_placa")
            
            # 3. Espera a que aparezca el contenedor de resultados (60 seg)
            # Este es el paso donde antes te daba el error por lentitud del servidor
            await page.wait_for_selector("#ContentPlaceHolder1_RadMultiPage1", timeout=60000)
            
            # Función interna para limpiar y extraer datos de las tablas
            async def extraer_de_tabla(selector_id, situacion):
                rows = await page.query_selector_all(f"{selector_id} tr")
                tabla_rows = []
                for row in rows:
                    cols = await row.query_selector_all("td")
                    if len(cols) > 2:
                        fila = [await c.inner_text() for c in cols]
                        fila_limpia = [item.strip() for item in fila]
                        # Solo agregamos si no es el mensaje de "No existen datos"
                        if "No existen datos" not in str(fila_limpia):
                            fila_limpia.append(situacion)
                            tabla_rows.append(fila_limpia)
                return tabla_rows

            # Extraemos tanto las multas pendientes como las pagadas
            pendientes = await extraer_de_tabla("#ContentPlaceHolder1_gv_pendientes", "🚩 POR PAGAR")
            pagadas = await extraer_de_tabla("#ContentPlaceHolder1_gv_pagadas", "✅ PAGADA")
            
            return pendientes, pagadas, "Éxito"

        except Exception as e:
            # Si hay timeout o error, enviamos las listas vacías y el mensaje de error
            return [], [], f"El portal de Santiago no respondió a tiempo o está caído. ({str(e)})"
            
        finally:
            # IMPORTANTE: Cerramos el navegador siempre, incluso si hubo error, 
            # para no dejar procesos 'zombie' en el servidor de Streamlit.
            await browser.close()
