import asyncio
from playwright.async_api import async_playwright

async def consultar_pudahuel(patente):
    async with async_playwright() as p:
        # Camuflaje para evitar detección de bot en portales SMC
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. URL de Pudahuel (SMC) con paciencia de 90 segundos
            await page.goto("https://pago.smc.cl/pagoRMNPv2/Login.aspx", wait_until="domcontentloaded", timeout=90000)
            
            # 2. Selectores flexibles para la casilla de patente
            selector_input = "input[id$='txtPlaca']"
            selector_boton = "input[id$='btnAceptar']"
            
            await page.wait_for_selector(selector_input, state="visible", timeout=60000)
            
            # 3. Llenado y búsqueda
            await page.fill(selector_input, patente)
            await page.hover(selector_boton)
            await page.evaluate(f"document.querySelector(\"{selector_boton}\").click()")
            
            # 4. Espera a que cargue el resultado o el mensaje de 'sin deudas'
            try:
                await page.wait_for_function(
                    "document.body.innerText.includes('registra') || document.body.innerText.includes('Multa') || document.querySelectorAll('table tr').length > 5", 
                    timeout=60000
                )
            except:
                pass 

            content = await page.content()
            
            # Verificación de deudas (estándar SMC)
            if any(msg in content for msg in ["No existen", "No registra", "no presenta deudas"]):
                return [], [], "Éxito"

            # 5. Extracción de datos de la tabla
            rows = await page.query_selector_all("table tr")
            tabla_rows = []
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) > 2:
                    fila = [await c.inner_text() for c in cols]
                    fila_limpia = [item.strip() for item in fila]
                    # Filtro para evitar filas de diseño
                    if len(fila_limpia[0]) > 2 and "Aceptar" not in fila_limpia[0]:
                        tabla_rows.append(fila_limpia)

            return tabla_rows, [], "Éxito"

        except Exception as e:
            if "Timeout" in str(e):
                return [], [], "El portal de Pudahuel no respondió (Servidor lento o caído)."
            return [], [], f"Error Pudahuel: {str(e)}"
        finally:
            await browser.close()
