import asyncio
from playwright.async_api import async_playwright
import re
import random

async def consultar_estacion_central(patente):
    async with async_playwright() as p:
        # 1. Argumentos extra para ocultar que es un navegador controlado por software
        browser = await p.chromium.launch(headless=True, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox"
        ])
        
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        
        # Script para eliminar la propiedad navigator.webdriver (el delator de bots)
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        
        try:
            # 2. Navegar con un tiempo de espera generoso
            await page.goto("https://ww21.e-com.cl/Pagos/PagosVariosv3/?id=37", wait_until="networkidle", timeout=90000)
            
            # Pausa aleatoria para simular lectura humana
            await asyncio.sleep(random.uniform(1, 3))

            # 3. Seleccionar 'Placa'
            # Forzamos el click con dispatch_event para que sea más natural
            radio_placa = await page.wait_for_selector("input[value='Placa']", timeout=30000)
            await radio_placa.click()
            
            # 4. Separar patente
            letras = "".join(re.findall("[a-zA-Z]+", patente))
            numeros = "".join(re.findall("[0-9]+", patente))
            
            # 5. Esperar los inputs y escribir como humano (con retraso entre teclas)
            await page.wait_for_selector("input[name='txtPlacaL']", state="visible", timeout=30000)
            
            await page.type("input[name='txtPlacaL']", letras, delay=random.randint(50, 150))
            await page.type("input[name='txtPlacaN']", numeros, delay=random.randint(50, 150))
            
            # 6. Clic en ACCEDER
            await asyncio.sleep(1)
            await page.click("#acceder")
            
            # 7. Esperar contenido real
            # En lugar de esperar 'networkidle', esperamos a que aparezca texto de resultado
            await page.wait_for_function(
                "document.body.innerText.includes('registra') || document.body.innerText.includes('Monto') || document.querySelectorAll('table tr').length > 10",
                timeout=60000
            )
            
            content = await page.content()
            
            if "No registra deudas" in content:
                return [], [], "Éxito"

            # 8. Extracción (Igual a la anterior pero filtrando mejor)
            rows = await page.query_selector_all("table tr")
            pendientes = []
            
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) >= 8:
                    fila = [await c.inner_text() for c in cols]
                    fila_limpia = [item.strip() for item in fila]
                    
                    if "Año Proceso" in fila_limpia[0] or not fila_limpia[0]:
                        continue
                        
                    nueva_fila = [
                        "", "Estación Central", patente,
                        fila_limpia[2], fila_limpia[8] if len(fila_limpia)>8 else fila_limpia[5],
                        fila_limpia[1], fila_limpia[3], "---", 
                        fila_limpia[4], fila_limpia[1], "🚩 PENDIENTE"
                    ]
                    # Ajustamos al orden de tu app (11 columnas)
                    pendientes.append(nueva_fila[:11])

            return pendientes, [], "Éxito"

        except Exception as e:
            if "Timeout" in str(e):
                return [], [], "Estación Central no respondió (Timeout de seguridad)."
            return [], [], f"Error Estación Central: {str(e)}"
        finally:
            await browser.close()
