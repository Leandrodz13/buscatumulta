import asyncio
from playwright.async_api import async_playwright

async def consultar_providencia(patente):
    async with async_playwright() as p:
        # 1. Lanzamos con argumentos para evitar detección
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        
        # 2. Contexto con dimensiones de pantalla real y User Agent de humano
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 3. Vamos a la URL (esperamos solo lo básico para ganar tiempo)
            await page.goto("https://pago.smc.cl/pagoRMNPv2/Login.aspx", wait_until="domcontentloaded", timeout=60000)
            
            selector_input = "input[id$='txtPlaca']"
            selector_boton = "input[id$='btnAceptar']"
            
            # 4. Esperamos el input
            await page.wait_for_selector(selector_input, state="visible", timeout=30000)
            
            # Llenamos la patente
            await page.fill(selector_input, patente)
            
            # 5. Clic "Humano": Primero movemos el mouse y luego clickeamos vía JS
            await page.hover(selector_boton)
            await page.evaluate(f"document.querySelector(\"{selector_boton}\").click()")
            
            # 6. La clave: Esperamos a que la URL cambie o aparezca el resultado
            # SMC suele redirigir a Principal.aspx o mostrar una tabla
            try:
                # Esperamos que el botón de carga desaparezca o aparezca contenido
                await page.wait_for_function("document.body.innerText.includes('registra') || document.body.innerText.includes('Multa') || document.querySelectorAll('table tr').length > 5", timeout=45000)
            except:
                pass # Si falla la función, seguimos para ver qué hay en el content

            content = await page.content()
            
            if "No existen" in content or "No registra" in content or "no presenta deudas" in content:
                return [], [], "Éxito"

            # 7. Extracción de datos (buscamos tablas con datos reales)
            rows = await page.query_selector_all("table tr")
            tabla_rows = []
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) > 2:
                    fila = [await c.inner_text() for c in cols]
                    fila_limpia = [item.strip() for item in fila]
                    # Filtro para evitar filas de diseño o vacías
                    if len(fila_limpia[0]) > 2 and "Aceptar" not in fila_limpia[0]:
                        tabla_rows.append(fila_limpia)

            return tabla_rows, [], "Éxito"

        except Exception as e:
            if "Timeout" in str(e):
                return [], [], "El portal de Providencia no respondió (Timeout de seguridad)."
            return [], [], f"Error Providencia: {str(e)}"
        finally:
            await browser.close()
