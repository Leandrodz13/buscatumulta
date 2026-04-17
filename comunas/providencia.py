import asyncio
from playwright.async_api import async_playwright
import pandas as pd

async def consultar_providencia(patente):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # URL de Providencia (SMC)
            await page.goto("https://pago.smc.cl/pagoRMNPv2/Login.aspx", wait_until="domcontentloaded", timeout=60000)
            
            # Llenamos la patente en el campo de la 3ra casilla (TAG/Vías Exclusivas)
            await page.fill("#ctl00_ContentPlaceHolder1_txtPlaca", patente)
            
            # Clic en el botón Aceptar de esa misma casilla
            await page.click("#ctl00_ContentPlaceHolder1_btnAceptar")
            
            # Esperamos a que la página reaccione (SMC a veces recarga la misma página con error o tabla)
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            content = await page.content()
            
            # Verificamos si no hay deudas (SMC suele poner un mensaje de texto)
            if "No existen" in content or "No registra" in content or "no presenta deudas" in content:
                return [], [], "Éxito"

            # Intentamos extraer la tabla de resultados si existe
            # Usualmente SMC usa una clase llamada 'TABLA_INTERNA' o simplemente tablas de datos
            rows = await page.query_selector_all("table tr")
            tabla_rows = []
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) > 2:
                    fila = [await c.inner_text() for c in cols]
                    fila_limpia = [item.strip() for item in fila]
                    # Filtramos filas vacías o de cabecera que no sirven
                    if len(fila_limpia[0]) > 0:
                        tabla_rows.append(fila_limpia)

            return tabla_rows, [], "Éxito"

        except Exception as e:
            return [], [], f"Error Providencia: {str(e)}"
        finally:
            await browser.close()
