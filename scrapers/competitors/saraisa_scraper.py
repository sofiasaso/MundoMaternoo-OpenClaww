# ==============================================================================
# ARCHIVO: scrapers/competitors/saraisa_scraper.py
# FUNCIÓN: Extrae productos y precios de saraisa.co (WooCommerce).
#
# EJECUTAR (para probar):
#   cd MundoMaternoo-OpenClaww/scrapers
#   python competitors/saraisa_scraper.py
#
# RETORNA: lista de dicts { name, price, category, competitor, product_url }
# ==============================================================================

import time
import requests
from bs4 import BeautifulSoup

BASE_URL   = "https://saraisa.co"
COMPETITOR = "saraisa"
HEADERS    = {"User-Agent": "Mozilla/5.0"}
DELAY      = 1


def normalizar_precio(texto: str) -> float | None:
    if not texto or texto.strip() in ("", "N/A"):
        return None
    try:
        s = texto.replace("$", "").replace("\xa0", "").replace("\u00a0", "").strip()
        if "." in s and "," not in s:    s = s.replace(".", "")
        elif "," in s and "." not in s:  s = s.replace(",", "")
        elif "." in s and "," in s:      s = s.replace(".", "").replace(",", ".")
        return float(s)
    except (ValueError, AttributeError):
        return None


def scrape() -> list[dict]:
    """
    Descubre categorías desde /tienda/ y extrae productos de cada una.
    Saraisa usa WooCommerce; los selectores están tomados del notebook original.
    """
    print("[Saraisa] Iniciando scraping...")
    categorias, productos = [], []

    # Paso 1 — descubrir categorías
    try:
        resp = requests.get(f"{BASE_URL}/tienda/", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.select('a[href*="/categoria-producto/"]'):
            url = a["href"]
            if url not in categorias:
                categorias.append(url)
    except Exception as e:
        print(f"[Saraisa] Error descubriendo categorías: {e}")

    print(f"[Saraisa] {len(categorias)} categorías encontradas.")

    # Paso 2 — recorrer cada categoría
    for cat_url in categorias:
        try:
            resp = requests.get(cat_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("div.nm-shop-loop-title-price")
            for item in items:
                nombre_tag = item.select_one("h3.woocommerce-loop-product__title a")
                nombre     = nombre_tag.get_text(strip=True) if nombre_tag else None
                if not nombre:
                    continue
                url_prod = nombre_tag["href"] if nombre_tag else None
                precio_tag = (
                    item.select_one("span.price ins .woocommerce-Price-amount")
                    or item.select_one("span.price .woocommerce-Price-amount")
                )
                precio = normalizar_precio(precio_tag.get_text(strip=True) if precio_tag else None)
                if precio is None:
                    continue
                productos.append({
                    "name":        nombre,
                    "price":       precio,
                    "category":    cat_url.rstrip("/").split("/")[-1],
                    "competitor":  COMPETITOR,
                    "product_url": url_prod,
                })
            time.sleep(DELAY)
        except Exception as e:
            print(f"[Saraisa] Error en {cat_url}: {e}")

    print(f"[Saraisa] Total: {len(productos)} productos extraídos.")
    return productos


if __name__ == "__main__":
    import json
    resultados = scrape()
    print(json.dumps(resultados[:3], indent=2, ensure_ascii=False))
    print(f"\nTotal: {len(resultados)} productos")
