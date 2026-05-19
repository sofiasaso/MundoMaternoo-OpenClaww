# ==============================================================================
# ARCHIVO: scrapers/competitors/ohmama_scraper.py
# FUNCIÓN: Extrae productos y precios de www.ohmama.com.co (Shopify).
#
# EJECUTAR (para probar):
#   cd MundoMaternoo-OpenClaww/scrapers
#   python competitors/ohmama_scraper.py
#
# RETORNA: lista de dicts { name, price, category, competitor, product_url }
# ==============================================================================

import time
import requests
from bs4 import BeautifulSoup

BASE_URL   = "https://www.ohmama.com.co"
COMPETITOR = "ohmama"
HEADERS    = {"User-Agent": "Mozilla/5.0"}
DELAY      = 1


def normalizar_precio(texto: str) -> float | None:
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
    OhMama también usa Shopify (misma lógica que Carymar).
    Descubre colecciones desde el menú de navegación.
    """
    print("[OhMama] Iniciando scraping...")
    colecciones, productos = [], []

    # Paso 1 — descubrir colecciones desde el menú
    try:
        soup = BeautifulSoup(requests.get(BASE_URL, headers=HEADERS, timeout=15).text, "html.parser")
        for a in soup.select("ul.list-menu li a"):
            href = a.get("href", "")
            if "/collections/" in href:
                url = BASE_URL + href if href.startswith("/") else href
                if url not in colecciones:
                    colecciones.append(url)
    except Exception as e:
        print(f"[OhMama] Error descubriendo colecciones: {e}")

    print(f"[OhMama] {len(colecciones)} colecciones encontradas.")

    # Paso 2 — recorrer cada colección
    for col in colecciones:
        page = 1
        while True:
            url = col if page == 1 else f"{col}?page={page}"
            try:
                soup  = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=15).text, "html.parser")
                items = soup.select("div.product-card, li.grid__item")
                if not items:
                    break
                for item in items:
                    nombre_tag = (
                        item.select_one("div.card__heading a")
                        or item.select_one("h3.grid-view-item__title")
                        or item.select_one(".card__heading")
                    )
                    nombre = nombre_tag.get_text(strip=True) if nombre_tag else None
                    if not nombre:
                        continue
                    precio_tag = (
                        item.select_one("span.price-item--sale")
                        or item.select_one("span.price-item--regular")
                        or item.select_one(".price__regular .price-item")
                    )
                    precio = normalizar_precio(precio_tag.get_text(strip=True) if precio_tag else None)
                    if precio is None:
                        continue
                    href_prod = nombre_tag.get("href") if nombre_tag else None
                    enlace    = BASE_URL + href_prod if href_prod and href_prod.startswith("/") else href_prod
                    productos.append({
                        "name":        nombre,
                        "price":       precio,
                        "category":    col.rstrip("/").split("/")[-1],
                        "competitor":  COMPETITOR,
                        "product_url": enlace,
                    })
                time.sleep(DELAY)
                page += 1
            except Exception as e:
                print(f"[OhMama] Error en {url}: {e}")
                break

    print(f"[OhMama] Total: {len(productos)} productos extraídos.")
    return productos


if __name__ == "__main__":
    import json
    resultados = scrape()
    print(json.dumps(resultados[:3], indent=2, ensure_ascii=False))
    print(f"\nTotal: {len(resultados)} productos")
