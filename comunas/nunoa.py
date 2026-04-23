import asyncio
from playwright.async_api import async_playwright

async def consultar_nunoa(patente):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. URL de Ñuñoa
            await page.goto("https://sertex3.stonline.cl/Nunoa/Partes_Empadronados/asp/inplaca.asp", wait_until="domcontentloaded", timeout=90000)
            
            # 2. Llenar la patente (el ID es 'Placa' según tu HTML)
            await page.fill("#Placa", patente)
            
            # 3. Presionar el botón de INGRESAR
            # Usamos el texto del botón porque no tiene un ID claro, o el selector de clase btn-sm
            await page.click("text=INGRESAR")
            
            # 4. Esperar que carguen los resultados (wcova_pe.asp)
            await page.wait_for_load_state("networkidle", timeout=90000)
            
            content = await page.content()
            
            # Verificación estándar de 'sin deudas' para este sistema
            if "No registra infracciones" in content or "no tiene partes" in content or "Sin infracciones" in content:
                return [], [], "Éxito"

            # 5. Extracción de tablas (STONLINE suele usar tablas estándar sin clases raras)
            rows = await page.query_selector_all("table tr")
            tabla_rows = []
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) > 2:
                    fila = [await c.inner_text() for c in cols]
                    fila_limpia = [item.strip() for item in fila]
                    # Filtro para filas que realmente contengan datos
                    if len(fila_limpia[0]) > 1:
                        tabla_rows.append(fila_limpia)

            return tabla_rows, [], "Éxito"

        except Exception as e:
            if "Timeout" in str(e):
                return [], [], "El portal de Ñuñoa no respondió tras 90 segundos."
            return [], [], f"Error Ñuñoa: {str(e)}"
        finally:
            await browser.close()
