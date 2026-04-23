import asyncio
from playwright.async_api import async_playwright
import re

async def consultar_estacion_central(patente):
    async with async_playwright() as p:
        # Modo sigilo activo
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. Navegación rápida
            await page.goto("https://ww21.e-com.cl/Pagos/PagosVariosv3/?id=37", wait_until="commit", timeout=60000)
            
            # 2. ESPERA AGRESIVA POR EL FORMULARIO
            # Esperamos que el radio button de Placa esté disponible para interactuar
            await page.wait_for_selector("input[value='Placa']", state="attached", timeout=30000)
            await page.check("input[value='Placa']")
            
            # 3. Separar patente (Lógica Leandro: TPVL82 -> TPVL y 82)
            letras = "".join(re.findall("[a-zA-Z]+", patente))
            numeros = "".join(re.findall("[0-9]+", patente))
            
            # 4. Llenado directo
            await page.wait_for_selector("input[name='txtPlacaL']", state="visible", timeout=20000)
            await page.fill("input[name='txtPlacaL']", letras)
            await page.fill("input[name='txtPlacaN']", numeros)
            
            # 5. Ejecución directa de la función del portal
            await page.evaluate("validar(37);")
            
            # --- EL "WAIT FOR SELECTOR" AGRESIVO ---
            # Aquí le decimos al bot: "No esperes a que la página cargue completa, 
            # espera a que aparezca CUALQUIERA de estas tres cosas".
            try:
                await asyncio.wait([
                    page.wait_for_selector("text=No registra deudas", timeout=45000),
                    page.wait_for_selector("table tr", timeout=45000),
                    page.wait_for_selector(".titulo3", timeout=45000)
                ], return_when=asyncio.FIRST_COMPLETED)
            except:
                # Si falla, intentamos capturar lo que haya en el DOM
                pass

            content = await page.content()
            
            if "No registra deudas" in content or "no presenta deudas" in content.lower():
                return [], [], "Éxito"

            # 6. Extracción de datos
            rows = await page.query_selector_all("table tr")
            pendientes = []
            
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) >= 8:
                    fila = [await c.inner_text() for c in cols]
                    fila_limpia = [item.strip() for item in fila]
                    
                    # Filtro de cabeceras y filas vacías
                    if any(x in " ".join(fila_limpia) for x in ["Año Proceso", "Simbología", "Aprobado", "Placa"]):
                        continue
                        
                    if not fila_limpia[0].isdigit() and "No registra" not in fila_limpia[0]:
                        # Si la primera celda no es un año (2024, 2025), probablemente no es una multa
                        if len(fila_limpia[0]) < 4: continue

                    nueva_fila = [
                        "", "Estación Central", patente,
                        fila_limpia[2] if len(fila_limpia)>2 else "", 
                        fila_limpia[8] if len(fila_limpia)>8 else (fila_limpia[5] if len(fila_limpia)>5 else ""),
                        fila_limpia[1] if len(fila_limpia)>1 else "",
                        fila_limpia[3] if len(fila_limpia)>3 else "Multa Derechos Varios", 
                        "---", 
                        fila_limpia[4] if len(fila_limpia)>4 else "",
                        fila_limpia[1] if len(fila_limpia)>1 else "",
                        "🚩 PENDIENTE"
                    ]
                    pendientes.append(nueva_fila[:11])

            return pendientes, [], "Éxito"

        except Exception as e:
            if "Timeout" in str(e):
                return [], [], "Estación Central: Aún no está disponible en nuestra web."
            return [], [], f"Error Estación Central: {str(e)}"
        finally:
            await browser.close()
