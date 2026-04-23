import asyncio
from playwright.async_api import async_playwright
import re

async def consultar_estacion_central(patente):
    async with async_playwright() as p:
        # Usamos camuflaje para evitar bloqueos
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. Navegar al portal de E-COM
            await page.goto("https://ww21.e-com.cl/Pagos/PagosVariosv3/?id=37", wait_until="networkidle", timeout=90000)
            
            # 2. Seleccionar la opción 'Placa' (Radio Button)
            # El valor según el HTML es 'Placa'
            await page.check("input[value='Placa']")
            
            # 3. Separar letras y números de la patente (Ej: TPVL82 -> TPVL y 82)
            letras = "".join(re.findall("[a-zA-Z]+", patente))
            numeros = "".join(re.findall("[0-9]+", patente))
            
            # 4. Llenar los campos que aparecen dinámicamente
            # Usamos selectores por nombre ya que suelen ser estándar en E-COM
            await page.wait_for_selector("input[name='txtPlacaL']", timeout=30000)
            await page.fill("input[name='txtPlacaL']", letras)
            await page.fill("input[name='txtPlacaN']", numeros)
            
            # 5. Click en ACCEDER
            await page.click("#acceder")
            
            # 6. Esperar resultados con paciencia
            await page.wait_for_load_state("networkidle", timeout=90000)
            content = await page.content()
            
            if "No registra deudas" in content or "No se encontraron registros" in content:
                return [], [], "Éxito"

            # 7. Extraer tabla de resultados (E-COM usa tablas con clases de texto azul)
            rows = await page.query_selector_all("table tr")
            pendientes = []
            
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) >= 8: # La tabla de la foto tiene unas 9 columnas
                    fila = [await c.inner_text() for c in cols]
                    fila_limpia = [item.strip() for item in fila]
                    
                    # Filtro de encabezados
                    if "Año Proceso" in fila_limpia[0] or "Monto" in fila_limpia:
                        continue
                    
                    # Estandarizamos al formato de 11 columnas de tu App
                    nueva_fila = [
                        "",                                  # Acción
                        fila_limpia[2] if len(fila_limpia)>2 else "", # Fecha Emisión
                        "Estación Central",                  # Juzgado
                        patente,                             # PPU
                        fila_limpia[8] if len(fila_limpia)>8 else fila_limpia[5], # Total
                        fila_limpia[1] if len(fila_limpia)>1 else "", # Orden Ingreso
                        fila_limpia[3] if len(fila_limpia)>3 else "Derechos Varios", # Observación
                        "---",                               # RUT
                        fila_limpia[4] if len(fila_limpia)>4 else "", # Vencimiento
                        fila_limpia[1] if len(fila_limpia)>1 else "", # Rol
                        "🚩 PENDIENTE"                       # Estado
                    ]
                    pendientes.append(nueva_fila)

            return pendientes, [], "Éxito"

        except Exception as e:
            if "Timeout" in str(e):
                return [], [], "Portal Estación Central no respondió (Timeout)."
            return [], [], f"Error Estación Central: {str(e)}"
        finally:
            await browser.close()
