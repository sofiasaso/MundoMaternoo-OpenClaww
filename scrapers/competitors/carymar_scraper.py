# ==============================================================================
# ARCHIVO: scrapers/competitors/carymar_scraper.py
# FUNCIÓN: Extrae productos y precios de www.carymar.co (Shopify).
#          Archivo independiente — puede correrse solo para probar.
#
# EJECUTAR (para probar):
#   cd MundoMaternoo-OpenClaww/scrapers
#   python competitors/carymar_scraper.py
#
# RETORNA: lista de dicts { name, price, category, competitor, product_url }
# ==============================================================================

import time
import requests
from bs4 import BeautifulSoup

BASE_URL   = "https://www.carymar.co"
COMPETITOR = "carymar"
HEADERS    = {"User-Agent": "Mozilla/5.0"}
DELAY      = 1   # segundos entre peticiones para no sobrecargar el sitio


def normalizar_precio(texto: str) -> float | None:
    """Convierte '$55.000' o '$106,250' a float."""
    if not texto or texto.strip() in ("", "N/A"):
        return None
    try:
        s = texto.replace("$", "").replace("\xa0", "").strip()
        if "." in s and "," not in s:    s = s.replace(".", "")
        elif "," in s and "." not in s:  s = s.replace(",", "")
        elif "." in s and "," in s:      s = s.replace(".", "").replace(",", ".")
        return float(s)
    except (ValueError, AttributeError):
        return None


def scrape() -> list[dict]:
    """
    Función principal del scraper.
    Descubre colecciones desde la home y extrae todos los productos.
    """
    print("[Carymar] Iniciando scraping...")
    colecciones, productos = [], []

    # Paso 1 — descubrir colecciones
    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.select("a[href*='/collections/']"):
            href = a.get("href", "")
            if "/collections/" in href and "all" not in href:
                url = BASE_URL + href if href.startswith("/") else href
                if url not in colecciones:
                    colecciones.append(url)
    except Exception as e:
        print(f"[Carymar] Error descubriendo colecciones: {e}")

    print(f"[Carymar] {len(colecciones)} colecciones encontradas.")

    # Paso 2 — recorrer cada colección página a página
    for col in colecciones:
        page = 1
        while True:
            url = col if page == 1 else f"{col}?page={page}"
            try:
                soup  = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=15).text, "html.parser")
                items = soup.select("div.product-card")
                if not items:
                    break
                for item in items:
                    nombre_tag = item.select_one("div.grid-view-item__title")
                    nombre     = nombre_tag.get_text(strip=True) if nombre_tag else None
                    if not nombre:
                        continue
                    precio_tag = (
                        item.select_one("span.price-item--sale")
                        or item.select_one("span.price-item--regular")
                    )
                    precio = normalizar_precio(precio_tag.get_text(strip=True) if precio_tag else None)
                    if precio is None:
                        continue
                    enlace = item.select_one("a")
                    productos.append({
                        "name":        nombre,
                        "price":       precio,
                        "category":    col.rstrip("/").split("/")[-1],
                        "competitor":  COMPETITOR,
                        "product_url": BASE_URL + enlace["href"] if enlace else None,
                    })
                time.sleep(DELAY)
                page += 1
            except Exception as e:
                print(f"[Carymar] Error en {url}: {e}")
                break

    print(f"[Carymar] Total: {len(productos)} productos extraídos.")
    return productos


if __name__ == "__main__":
    import json
    resultados = scrape()
    print(json.dumps(resultados[:3], indent=2, ensure_ascii=False))
    print(f"\nTotal: {len(resultados)} productos")
