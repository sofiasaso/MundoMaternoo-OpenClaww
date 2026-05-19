#!/usr/bin/env python3
# ==============================================================================
# ARCHIVO: scrapers/main_scraper.py
# FUNCIÓN: Orquestador central. Ejecuta los tres scrapers en secuencia,
#          consolida los resultados y exporta un CSV de respaldo en data/raw/.
#
# EJECUTAR:
#   cd MundoMaternoo-OpenClaww/scrapers
#   python main_scraper.py
#
# El resultado se guarda en:
#   ../data/raw/scraping_YYYYMMDD_HHMMSS.csv
#
# NOTA: Este script NO guarda en SQLite.
#       Eso lo hace backend/services/scraping_service.py desde la API.
#       Este script sirve para probar y verificar que los scrapers funcionan
#       de forma independiente, antes de integrarlos al backend.
# ==============================================================================

import sys
import os
import csv
from datetime import datetime

# Asegura que Python encuentre los módulos hermanos
sys.path.insert(0, os.path.dirname(__file__))

from competitors.carymar_scraper  import scrape as scrape_carymar
from competitors.saraisa_scraper  import scrape as scrape_saraisa
from competitors.ohmama_scraper   import scrape as scrape_ohmama

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def guardar_csv(productos: list[dict], nombre_archivo: str):
    """Exporta la lista de productos a un CSV de respaldo."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ruta = os.path.join(OUTPUT_DIR, nombre_archivo)
    if not productos:
        print(f"[CSV] No hay productos para guardar.")
        return
    campos = ["name", "price", "category", "competitor", "product_url"]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(productos)
    print(f"[CSV] Guardado en: {ruta} ({len(productos)} registros)")


def run():
    inicio = datetime.now()
    print(f"\n{'='*55}")
    print(f"  MundoMaterno — Scraping iniciado: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")

    todos = []
    scrapers = [
        ("Carymar", scrape_carymar),
        ("Saraisa", scrape_saraisa),
        ("OhMama",  scrape_ohmama),
    ]

    for nombre, fn in scrapers:
        print(f"\n── {nombre} ──────────────────────────────────────")
        try:
            resultado = fn()
            todos.extend(resultado)
            print(f"   ✓ {len(resultado)} productos extraídos.")
        except Exception as e:
            print(f"   ✗ Error: {e}")

    fin = datetime.now()
    duracion = (fin - inicio).seconds

    print(f"\n{'='*55}")
    print(f"  Scraping finalizado en {duracion}s")
    print(f"  Total consolidado: {len(todos)} productos")
    print(f"{'='*55}\n")

    # Exportar CSV de respaldo
    nombre_csv = f"scraping_{inicio.strftime('%Y%m%d_%H%M%S')}.csv"
    guardar_csv(todos, nombre_csv)

    return todos


if __name__ == "__main__":
    run()
