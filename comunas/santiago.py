import asyncio
from playwright.async_api import async_playwright
import pandas as pd

async def consultar_santiago(patente):
    async with async_playwright() as p:
        # Lanzamos el navegador
        browser = await p.chromium.launch(headless=True)
        # Usamos un perfil de navegador real para evitar bloqueos
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # TIEMPO RIDÍCULO: 90 segundos para cargar la página inicial
            await page.goto("https://tramites.munistgo.cl/pagosjpl/", wait_until="networkidle", timeout=90000)
            
            await page.fill("#ContentPlaceHolder1_txt_placa", patente)
            await page.click("#ContentPlaceHolder1_img_buscar_placa")
            
            # ESPERA EXTENDIDA: 60 segundos para que aparezca la tabla de resultados
            await page.wait_for_selector("#ContentPlaceHolder1_RadMultiPage1", timeout=60000)
            
            async def extraer_de_tabla(selector_id, situacion):
                rows = await page.query_selector_all(f"{selector_id} tr")
                tabla_rows = []
                for row in rows:
                    cols = await row.query_selector_all("td")
                    if len(cols) > 2:
                        fila = [await c.inner_text() for c in cols]
                        fila_limpia = [item.strip() for item in fila]
                        if "No existen datos" not in str(fila_limpia):
                            fila_limpia.append(situacion)
                            tabla_rows.append(fila_limpia)
                return tabla_rows

            # Extraemos ambas realidades
            pendientes = await extraer_de_tabla("#ContentPlaceHolder1_gv_pendientes", "🚩 POR PAGAR")
            pagadas = await extraer_de_tabla("#ContentPlaceHolder1_gv_pagadas", "✅ PAGADA")
            
            await browser.close()
            return pendientes, pagadas, "Éxito"

        except Exception as e:
            await browser.close()
            # Retornamos listas vacías y el error para que la App sepa qué pasó
            return [], [], f"Tiempo de espera agotado o error: {str(e)}"
