# ==============================================================================
# ARCHIVO: backend/services/scraping_service.py
# CAMBIOS EN ESTA VERSIÓN:
#   → Solicitud 2: se agrega _normalizar_categoria().
#     Mapea los nombres crudos de categoría que vienen del scraping
#     (ej: "overolmaterno", "blusamaterna") a nombres canónicos
#     (ej: "Overoles", "Blusas") antes de guardar en SQLite.
#     Esto hace que las búsquedas y comparativas por categoría sean
#     consistentes aunque cada sitio las llame diferente.
# ==============================================================================

import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy.orm import Session

from models.product import Product
from models.price_history import PriceHistory

HEADERS = {"User-Agent": "Mozilla/5.0"}
DELAY   = 1

# ==============================================================================
# SOLICITUD 2 — Mapa de normalización de categorías
# Clave: nombre crudo en minúsculas (como viene del scraping)
# Valor: nombre canónico que se guarda en la base de datos
# ==============================================================================
CATEGORIA_MAP = {
    # Blusas
    "blusas":          "Blusas",
    "blusa":           "Blusas",
    "blusa materna":   "Blusas",
    "blusamaterna":    "Blusas",
    # Jean
    "jean":            "Jean",
    "jeans":           "Jean",
    "overoldejean":    "Jean",
    "bluejeanmaterno": "Jean",
    "jean materno":    "Jean",
    # Leggings
    "leggings":        "Leggings",
    "legging":         "Leggings",
    # Overoles (incluye Enterizos → Overoles según solicitud)
    "overol":          "Overoles",
    "overoles":        "Overoles",
    "overol materno":  "Overoles",
    "overolmaterno":   "Overoles",
    "enterizo":        "Overoles",
    "enterizos":       "Overoles",
    # Shorts
    "short":           "Shorts",
    "shorts":          "Shorts",
    "short materno":   "Shorts",
    # Vestidos
    "vestido":         "Vestidos",
    "vestidos":        "Vestidos",
    "vestidomaternidad": "Vestidos",
    "vestido maternidad": "Vestidos",
    # Ropa Materna (categoría general)
    "ropa materna":    "Ropa Materna",
    "maternidad":      "Ropa Materna",
    "maternidadfeliz": "Ropa Materna",
    "maternidad feliz": "Ropa Materna",
}


def _normalizar_categoria(raw: str | None) -> str:
    """
    Convierte el nombre crudo de categoría al nombre canónico definido en
    CATEGORIA_MAP. Si no hay coincidencia exacta, intenta coincidencia parcial.
    Si tampoco hay, devuelve el nombre capitalizado tal como viene.

    Ejemplos:
      "overolmaterno"   → "Overoles"
      "blusamaterna"    → "Blusas"
      "enterizos"       → "Overoles"
      "maternidadfeliz" → "Ropa Materna"
      "camiseta"        → "Camiseta"   (sin match, capitaliza y devuelve)
    """
    if not raw:
        return "Sin categoría"

    normalizado = raw.strip().lower()

    # 1. Búsqueda exacta
    if normalizado in CATEGORIA_MAP:
        return CATEGORIA_MAP[normalizado]

    # 2. Búsqueda parcial: la clave está contenida en el raw o viceversa
    for clave, valor in CATEGORIA_MAP.items():
        if clave in normalizado or normalizado in clave:
            return valor

    # 3. Sin match: devolver capitalizado
    return raw.strip().title()


# ==============================================================================
# UTILIDADES
# ==============================================================================

def _normalizar_precio(precio_str: str) -> float | None:
    """
    Convierte strings de precio colombiano a float.
    "$55.000" → 55000.0  |  "$106,250" → 106250.0
    """
    if not precio_str or precio_str == "N/A":
        return None
    try:
        limpio = precio_str.replace("$", "").replace("\xa0", "").strip()
        if "." in limpio and "," not in limpio:
            limpio = limpio.replace(".", "")
        elif "," in limpio and "." not in limpio:
            limpio = limpio.replace(",", "")
        elif "." in limpio and "," in limpio:
            limpio = limpio.replace(".", "").replace(",", ".")
        return float(limpio)
    except (ValueError, AttributeError):
        return None


# ==============================================================================
# SCRAPER 1: CARYMAR (www.carymar.co) — Shopify
# ==============================================================================

def scrape_carymar() -> list[dict]:
    base_url  = "https://www.carymar.co"
    productos = []

    try:
        resp = requests.get(base_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        colecciones = []
        for link in soup.select("a[href*='/collections/']"):
            url = link.get("href")
            if url and "/collections/" in url and "all" not in url:
                url_completa = base_url + url if url.startswith("/") else url
                if url_completa not in colecciones:
                    colecciones.append(url_completa)

        print(f"[Carymar] {len(colecciones)} colecciones encontradas.")

        for coleccion_url in colecciones:
            page = 1
            while True:
                url = coleccion_url if page == 1 else f"{coleccion_url}?page={page}"
                try:
                    resp  = requests.get(url, headers=HEADERS, timeout=15)
                    soup  = BeautifulSoup(resp.text, "html.parser")
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
                        precio = _normalizar_precio(precio_tag.get_text(strip=True) if precio_tag else None)
                        if precio is None:
                            continue
                        enlace_tag = item.select_one("a")
                        enlace     = base_url + enlace_tag["href"] if enlace_tag else None
                        categoria  = coleccion_url.rstrip("/").split("/")[-1]
                        productos.append({
                            "name":        nombre,
                            "price":       precio,
                            "category":    categoria,  # se normaliza al guardar
                            "competitor":  "carymar",
                            "product_url": enlace,
                        })
                        time.sleep(DELAY)
                    page += 1
                except Exception as e:
                    print(f"[Carymar] Error en {url}: {e}")
                    break

    except Exception as e:
        print(f"[Carymar] Error general: {e}")

    print(f"[Carymar] {len(productos)} productos extraídos.")
    return productos


# ==============================================================================
# SCRAPER 2: SARAISA (saraisa.co) — WooCommerce
# ==============================================================================

def scrape_saraisa() -> list[dict]:
    base_url  = "https://saraisa.co"
    productos = []

    try:
        resp = requests.get(f"{base_url}/tienda/", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        categorias = []
        for link in soup.select('a[href*="/categoria-producto/"]'):
            url = link["href"]
            if url not in categorias:
                categorias.append(url)

        print(f"[Saraisa] {len(categorias)} categorías encontradas.")

        for cat_url in categorias:
            try:
                resp  = requests.get(cat_url, headers=HEADERS, timeout=15)
                soup  = BeautifulSoup(resp.text, "html.parser")
                items = soup.select("div.nm-shop-loop-title-price")
                for item in items:
                    nombre_tag = item.select_one("h3.woocommerce-loop-product__title a")
                    nombre     = nombre_tag.get_text(strip=True) if nombre_tag else None
                    if not nombre:
                        continue
                    url_producto = nombre_tag["href"] if nombre_tag else None
                    precio_tag = (
                        item.select_one("span.price ins .woocommerce-Price-amount")
                        or item.select_one("span.price .woocommerce-Price-amount")
                    )
                    precio = _normalizar_precio(precio_tag.get_text(strip=True) if precio_tag else None)
                    if precio is None:
                        continue
                    categoria = cat_url.rstrip("/").split("/")[-1]
                    productos.append({
                        "name":        nombre,
                        "price":       precio,
                        "category":    categoria,
                        "competitor":  "saraisa",
                        "product_url": url_producto,
                    })
                    time.sleep(DELAY)
            except Exception as e:
                print(f"[Saraisa] Error en {cat_url}: {e}")

    except Exception as e:
        print(f"[Saraisa] Error general: {e}")

    print(f"[Saraisa] {len(productos)} productos extraídos.")
    return productos


# ==============================================================================
# SCRAPER 3: OHMAMA (www.ohmama.com.co) — Shopify
# ==============================================================================

def scrape_ohmama() -> list[dict]:
    base_url  = "https://www.ohmama.com.co"
    productos = []

    try:
        resp = requests.get(base_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        categorias = []
        for link in soup.select("ul.list-menu li a"):
            url = link.get("href")
            if url and "/collections/" in url:
                url_completa = base_url + url if url.startswith("/") else url
                if url_completa not in categorias:
                    categorias.append(url_completa)

        print(f"[OhMama] {len(categorias)} colecciones encontradas.")

        for cat_url in categorias:
            page = 1
            while True:
                url = cat_url if page == 1 else f"{cat_url}?page={page}"
                try:
                    resp  = requests.get(url, headers=HEADERS, timeout=15)
                    soup  = BeautifulSoup(resp.text, "html.parser")
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
                        precio = _normalizar_precio(precio_tag.get_text(strip=True) if precio_tag else None)
                        if precio is None:
                            continue
                        enlace_tag = nombre_tag.get("href") if nombre_tag else None
                        enlace     = base_url + enlace_tag if enlace_tag and enlace_tag.startswith("/") else enlace_tag
                        categoria  = cat_url.rstrip("/").split("/")[-1]
                        productos.append({
                            "name":        nombre,
                            "price":       precio,
                            "category":    categoria,
                            "competitor":  "ohmama",
                            "product_url": enlace,
                        })
                        time.sleep(DELAY)
                    page += 1
                except Exception as e:
                    print(f"[OhMama] Error en {url}: {e}")
                    break

    except Exception as e:
        print(f"[OhMama] Error general: {e}")

    print(f"[OhMama] {len(productos)} productos extraídos.")
    return productos


# ==============================================================================
# ORQUESTADOR PRINCIPAL
# ==============================================================================

def run_all_scrapers(db: Session) -> dict:
    resumen = {
        "inicio":             datetime.utcnow().isoformat(),
        "competidores":       [],
        "total_procesados":   0,
        "total_nuevos":       0,
        "total_actualizados": 0,
        "errores":            []
    }

    scrapers = [
        ("carymar", scrape_carymar),
        ("saraisa", scrape_saraisa),
        ("ohmama",  scrape_ohmama),
    ]

    for nombre_competidor, funcion_scraper in scrapers:
        print(f"\n{'='*50}")
        print(f"Iniciando scraping: {nombre_competidor.upper()}")
        print(f"{'='*50}")
        try:
            productos_raw          = funcion_scraper()
            nuevos, actualizados   = _persistir_productos(db, productos_raw)
            resumen["competidores"].append({
                "competidor":   nombre_competidor,
                "extraidos":    len(productos_raw),
                "nuevos":       nuevos,
                "actualizados": actualizados,
                "estado":       "ok"
            })
            resumen["total_procesados"]   += len(productos_raw)
            resumen["total_nuevos"]       += nuevos
            resumen["total_actualizados"] += actualizados
            print(f"[{nombre_competidor.upper()}] OK: {nuevos} nuevos, {actualizados} actualizados.")
        except Exception as e:
            msg = f"Error en {nombre_competidor}: {str(e)}"
            resumen["errores"].append(msg)
            resumen["competidores"].append({
                "competidor": nombre_competidor,
                "estado":     "error",
                "detalle":    str(e)
            })
            print(f"[{nombre_competidor.upper()}] ERROR: {e}")

    resumen["fin"] = datetime.utcnow().isoformat()
    print(f"\nScraping finalizado. Total procesados: {resumen['total_procesados']}")
    return resumen


def _persistir_productos(db: Session, productos: list[dict]) -> tuple[int, int]:
    """
    Guarda productos en SQLite con normalización de categoría.
    SOLICITUD 2: _normalizar_categoria() se aplica antes de guardar/actualizar.
    """
    nuevos       = 0
    actualizados = 0

    for item in productos:
        nombre     = item.get("name", "").strip()
        competidor = item.get("competitor", "").strip()
        precio     = item.get("price")

        if not nombre or not competidor or precio is None:
            continue

        # Normalizar la categoría antes de guardar (Solicitud 2)
        categoria = _normalizar_categoria(item.get("category"))

        existente = (
            db.query(Product)
            .filter(
                Product.name       == nombre,
                Product.competitor == competidor
            )
            .first()
        )

        if existente:
            # Actualizar categoría si cambió (útil tras agregar nuevas reglas)
            if existente.category != categoria:
                existente.category = categoria

            # Detectar cambio de precio (tolerancia de 1 peso)
            if abs(existente.price - precio) > 1:
                historial = PriceHistory(
                    product_id  = existente.id,
                    old_price   = existente.price,
                    new_price   = precio,
                    detected_at = datetime.utcnow()
                )
                db.add(historial)
                existente.price      = precio
                existente.scraped_at = datetime.utcnow()
                actualizados += 1
        else:
            nuevo = Product(
                name        = nombre,
                category    = categoria,   # ya normalizada
                price       = precio,
                competitor  = competidor,
                product_url = item.get("product_url"),
                scraped_at  = datetime.utcnow()
            )
            db.add(nuevo)
            nuevos += 1

    db.commit()
    return nuevos, actualizados