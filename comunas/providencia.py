import asyncio
from playwright.async_api import async_playwright

async def consultar_providencia(patente):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. URL de Providencia con paciencia de 90 segundos
            await page.goto("https://pago.smc.cl/pagoRMNPv2/Login.aspx", wait_until="domcontentloaded", timeout=90000)
            
            # 2. Selectores flexibles (ID que termine en...)
            selector_input = "input[id$='txtPlaca']"
            selector_boton = "input[id$='btnAceptar']"
            
            # Espera larga para que aparezca el cuadro de texto (60 segundos)
            await page.wait_for_selector(selector_input, timeout=60000)
            
            # 3. Llenado y búsqueda
            await page.fill(selector_input, patente)
            await page.click(selector_boton)
            
            # 4. Espera ridícula para que el servidor de la muni procese y devuelva la tabla
            # Usamos 'networkidle' para estar seguros de que terminó de cargar todo
            await page.wait_for_load_state("networkidle", timeout=90000)
            
            content = await page.content()
            
            # Verificación de deudas
            if "No existen" in content or "No registra" in content or "no presenta deudas" in content:
                return [], [], "Éxito"

            # 5. Extracción de datos
            rows = await page.query_selector_all("table tr")
            tabla_rows = []
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) > 2:
                    fila = [await c.inner_text() for c in cols]
                    fila_limpia = [item.strip() for item in fila]
                    if len(fila_limpia[0]) > 0:
                        tabla_rows.append(fila_limpia)

            return tabla_rows, [], "Éxito"

        except Exception as e:
            # Mensaje amigable si el servidor municipal simplemente no despertó
            if "Timeout" in str(e):
                return [], [], "El portal de Providencia no respondió tras 90 segundos (Servidor lento o caído)."
            return [], [], f"Error Providencia: {str(e)}"
        finally:
            await browser.close()
