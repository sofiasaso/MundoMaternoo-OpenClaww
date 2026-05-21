# ==============================================================================
# ARCHIVO 7: /backend/routes/metrics.py
# TIPO: Router / Controlador API (Python)
# FUNCIÓN:
#   Calcula métricas ejecutivas para el dashboard competitivo
#   de Mundo Materno.
#
# NUEVA LÓGICA:
#   - Elimina Saraisa automáticamente
#   - Ranking de competidores (más barato → más caro)
#   - Comparación por categorías
#   - Variación histórica más importante
#   - KPIs más útiles para el dashboard final
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

    # ==========================================================================
    # FILTRAR SOLO COMPETIDORES REALES
    # ==========================================================================

    competidores_validos = ["carymar", "ohmama"]

    # ==========================================================================
    # TOTAL PRODUCTOS
    # ==========================================================================

    total_productos = (
        db.query(func.count(Product.id))
        .filter(Product.competitor.in_(competidores_validos))
        .scalar()
    ) or 0

    # ==========================================================================
    # TOTAL CAMBIOS HISTÓRICOS
    # ==========================================================================

    total_cambios = db.query(func.count(PriceHistory.id)).scalar() or 0

    # ==========================================================================
    # PROMEDIO GLOBAL
    # ==========================================================================

    avg_global = (
        db.query(func.avg(Product.price))
        .filter(Product.competitor.in_(competidores_validos))
        .scalar()
    )

    avg_global = round(avg_global, 2) if avg_global else 0.0

    # ==========================================================================
    # RESUMEN POR COMPETIDOR
    # ==========================================================================

    por_competidor = (
        db.query(
            Product.competitor,
            func.count(Product.id).label("total"),
            func.avg(Product.price).label("promedio"),
            func.min(Product.price).label("minimo"),
            func.max(Product.price).label("maximo"),
        )
        .filter(Product.competitor.in_(competidores_validos))
        .group_by(Product.competitor)
        .order_by(func.avg(Product.price).asc())
        .all()
    )

    competidores = []

    for row in por_competidor:
        competidores.append({
            "competitor": row.competitor,
            "total_productos": row.total,
            "precio_promedio": round(row.promedio, 2),
            "precio_minimo": round(row.minimo, 2),
            "precio_maximo": round(row.maximo, 2),
        })

    # ==========================================================================
    # TOP COMPETIDOR MÁS BARATO
    # ==========================================================================

    mas_barato = competidores[0] if competidores else None

    # ==========================================================================
    # RANKING COMPLETO
    # ==========================================================================

    ranking_competidores = competidores

    # ==========================================================================
    # COMPARACIÓN POR CATEGORÍA
    # ==========================================================================

    categorias_raw = (
        db.query(
            Product.category,
            Product.competitor,
            func.avg(Product.price).label("promedio"),
            func.count(Product.id).label("total")
        )
        .filter(Product.competitor.in_(competidores_validos))
        .group_by(Product.category, Product.competitor)
        .all()
    )

    categorias_map = {}

    for row in categorias_raw:

        categoria = row.category or "Sin categoría"

        if categoria not in categorias_map:
            categorias_map[categoria] = []

        categorias_map[categoria].append({
            "competitor": row.competitor,
            "precio_promedio": round(row.promedio, 2),
            "total_productos": row.total
        })

    comparativa_categorias = []

    for categoria, data in categorias_map.items():

        ordenados = sorted(
            data,
            key=lambda x: x["precio_promedio"]
        )

        mas_economico = ordenados[0]

        comparativa_categorias.append({
            "category": categoria,
            "mas_barato": mas_economico["competitor"],
            "precio_promedio": mas_economico["precio_promedio"],
            "competidores": ordenados
        })

    # ==========================================================================
    # MAYOR CAMBIO HISTÓRICO
    # ==========================================================================

    mayor_cambio = (
        db.query(PriceHistory)
        .order_by(desc(PriceHistory.change_percentage))
        .first()
    )

    variacion_historica = None

    if mayor_cambio:

        producto = (
            db.query(Product)
            .filter(Product.id == mayor_cambio.product_id)
            .first()
        )

        variacion_historica = {
            "producto": producto.name if producto else "Producto desconocido",
            "competidor": producto.competitor if producto else "Desconocido",
            "porcentaje": round(mayor_cambio.change_percentage, 2),
            "precio_anterior": mayor_cambio.old_price,
            "precio_nuevo": mayor_cambio.new_price,
        }

    # ==========================================================================
    # RESPUESTA FINAL
    # ==========================================================================

    return {

        "resumen_general": {
            "total_productos": total_productos,
            "total_cambios_detectados": total_cambios,
            "precio_promedio_global": avg_global,
        },

        "competidor_mas_barato": mas_barato,

        "ranking_competidores": ranking_competidores,

        "comparativa_categorias": comparativa_categorias,

        "variacion_historica_destacada": variacion_historica,

        "por_competidor": competidores,
    }