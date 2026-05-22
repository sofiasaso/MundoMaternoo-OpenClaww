# ==============================================================================
# ARCHIVO: backend/routes/metrics.py
# CAMBIOS EN ESTA VERSIÓN:
#   → Solicitud 1: se agrega "ultimas_variaciones" al response.
#     Cada entrada muestra: producto, competidor, precio anterior,
#     precio nuevo, diferencia porcentual y fecha de detección.
# ==============================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database.connection import get_db
from models.product import Product
from models.price_history import PriceHistory

router = APIRouter()


@router.get("/", summary="Métricas ejecutivas del mercado competidor")
def get_metrics(db: Session = Depends(get_db)):

    # ─── Totales generales ────────────────────────────────────
    total_productos = db.query(func.count(Product.id)).scalar() or 0
    total_cambios   = db.query(func.count(PriceHistory.id)).scalar() or 0

    # ─── Promedio global ──────────────────────────────────────
    avg_global = db.query(func.avg(Product.price)).scalar()
    avg_global = round(avg_global, 2) if avg_global else 0.0

    # ─── Por competidor ───────────────────────────────────────
    por_competidor = (
        db.query(
            Product.competitor,
            func.count(Product.id).label("total"),
            func.avg(Product.price).label("promedio"),
            func.min(Product.price).label("minimo"),
            func.max(Product.price).label("maximo"),
        )
        .group_by(Product.competitor)
        .all()
    )

    competidores = [
        {
            "competitor":      row.competitor,
            "total_productos": row.total,
            "precio_promedio": round(row.promedio, 2),
            "precio_minimo":   round(row.minimo, 2),
            "precio_maximo":   round(row.maximo, 2),
        }
        for row in por_competidor
    ]

    mas_barato = (
        min(competidores, key=lambda x: x["precio_promedio"])
        if competidores else None
    )

    # ─── Por categoría ────────────────────────────────────────
    por_categoria = (
        db.query(
            Product.category,
            func.count(Product.id).label("total"),
            func.avg(Product.price).label("promedio"),
        )
        .group_by(Product.category)
        .order_by(func.avg(Product.price).desc())
        .all()
    )

    categorias = [
        {
            "category":        row.category,
            "total_productos": row.total,
            "precio_promedio": round(row.promedio, 2),
        }
        for row in por_categoria
    ]

    # ─── Comparativa categoría × competidor ───────────────────
    comparativa_categorias = (
        db.query(
            Product.category,
            Product.competitor,
            func.avg(Product.price).label("promedio")
        )
        .filter(Product.category.isnot(None))
        .group_by(Product.category, Product.competitor)
        .all()
    )

    comparativas = {}
    for row in comparativa_categorias:
        cat = row.category
        if cat not in comparativas:
            comparativas[cat] = []
        comparativas[cat].append({
            "competitor":      row.competitor,
            "precio_promedio": round(row.promedio, 2)
        })

    # ─── SOLICITUD 1: Últimas variaciones de precio ───────────
    # Retorna las 20 variaciones más recientes con nombre del
    # producto, competidor, precios y porcentaje de cambio.
    variaciones_raw = (
        db.query(
            PriceHistory.old_price,
            PriceHistory.new_price,
            PriceHistory.detected_at,
            Product.name,
            Product.competitor,
            Product.category,
        )
        .join(Product, PriceHistory.product_id == Product.id)
        .order_by(desc(PriceHistory.detected_at))
        .limit(20)
        .all()
    )

    ultimas_variaciones = []
    for row in variaciones_raw:
        diff = round(row.new_price - row.old_price, 2)
        pct  = round(diff / row.old_price * 100, 1) if row.old_price else 0
        ultimas_variaciones.append({
            "product_name": row.name,
            "competitor":   row.competitor,
            "category":     row.category,
            "old_price":    row.old_price,
            "new_price":    row.new_price,
            "diff":         diff,
            "diff_pct":     pct,          # negativo = bajó, positivo = subió
            "detected_at":  row.detected_at,
        })

    # ─── Response final ───────────────────────────────────────
    return {
        "resumen_general": {
            "total_productos":          total_productos,
            "total_cambios_detectados": total_cambios,
            "precio_promedio_global":   avg_global,
        },
        "competidor_mas_barato":       mas_barato,
        "por_competidor":              competidores,
        "por_categoria":               categorias,
        "comparativas_por_categoria":  comparativas,
        "ultimas_variaciones":         ultimas_variaciones,   # ← NUEVO
    }