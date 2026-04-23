import asyncio
from playwright.async_api import async_playwright

async def consultar_nunoa(patente):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            await page.goto("https://sertex3.stonline.cl/Nunoa/Partes_Empadronados/asp/inplaca.asp", wait_until="domcontentloaded", timeout=90000)
            await page.fill("#Placa", patente)
            await page.click("text=INGRESAR")
            
            await page.wait_for_load_state("networkidle", timeout=90000)
            content = await page.content()
            
            if "No registra infracciones" in content or "no tiene partes" in content:
                return [], [], "Éxito"

            rows = await page.query_selector_all("table tr")
            pendientes = []
            pagadas = []

            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) >= 10:
                    fila = [await c.inner_text() for c in cols]
                    fila_limpia = [item.strip() for item in fila]
                    
                    texto_fila = " ".join(fila_limpia).upper()
                    # Filtro de basura
                    if any(x in texto_fila for x in ["PLACA", "VALOR UTM", "TIPO-MULTA", "SEL", "TIPO"]):
                        continue
                    
                    # --- REESCRITURA PARA PARECERSE A SANTIAGO ---
                    # Ñuñoa suele entregar: [Tipo, N° Parte, Fecha Inf, Monto, Reba, Vence, Valor, Pago, Ingreso, Caja, etc]
                    # Santiago usa: [Acción, Emisión, Juzgado, PPU, Monto, Denuncia, Infracción, RUT, Vence/Pago, Rol, Estado]
                    
                    # Intentamos mapear los datos (esto varía según el portal, pero ajustamos al estándar)
                    # Si la columna 7 tiene números, es una multa PAGADA
                    es_pagada = len(fila_limpia) > 7 and any(char.isdigit() for char in fila_limpia[7])

                    nueva_fila = [
                        "",                               # Acción (vacío)
                        fila_limpia[2] if len(fila_limpia) > 2 else "",  # Emisión (Fecha Inf)
                        "Ñuñoa",                          # Juzgado
                        patente,                          # PPU
                        fila_limpia[6] if len(fila_limpia) > 6 else fila_limpia[3], # Monto
                        fila_limpia[1] if len(fila_limpia) > 1 else "",  # Denuncia (N° Parte)
                        fila_limpia[0] if len(fila_limpia) > 0 else "",  # Infracción (Tipo)
                        "---",                            # RUT (Ñuñoa no lo muestra siempre)
                        fila_limpia[7] if es_pagada else (fila_limpia[5] if len(fila_limpia) > 5 else ""), # Vence o Pago
                        fila_limpia[1] if len(fila_limpia) > 1 else "",  # Rol
                        "✅ PAGADA" if es_pagada else "🚩 PENDIENTE" # Estado
                    ]

                    if es_pagada:
                        pagadas.append(nueva_fila)
                    else:
                        pendientes.append(nueva_fila)

            return pendientes, pagadas, "Éxito"

        except Exception as e:
            return [], [], f"Error Ñuñoa: {str(e)}"
        finally:
            await browser.close()
