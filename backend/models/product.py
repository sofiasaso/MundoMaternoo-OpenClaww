# ==============================================================================
# ARCHIVO 4: /backend/models/product.py
# TIPO: Modelo de datos ORM (Python)
# FUNCIÓN: Define la tabla 'products' en SQLite. Cada fila representa
#          un producto encontrado en el sitio de un competidor de Mundo
#          Materno durante el proceso de scraping automático.
#
# COMPETIDORES QUE ALIMENTAN ESTA TABLA:
#   - Carymar  (www.carymar.co)
#   - Saraisa  (saraisa.co)
#   - OhMama   (www.ohmama.com.co)
#
# RELACIÓN: Un Product puede tener muchos registros en PriceHistory.
# ==============================================================================

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from database.connection import Base


class Product(Base):
    __tablename__ = "products"

    # ─── Identificación ───────────────────────────────────────
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False, index=True)
    category    = Column(String, nullable=True, index=True)

    # ─── Precio ───────────────────────────────────────────────
    # Precio más reciente detectado. Se actualiza en cada scraping.
    # Los precios del notebook vienen como "$55.000" y se normalizan
    # a float (55000.0) antes de guardarse.
    price       = Column(Float, nullable=False)

    # ─── Competidor ───────────────────────────────────────────
    # Nombre normalizado del competidor. Valores posibles:
    # "carymar", "saraisa", "ohmama"
    competitor  = Column(String, nullable=False, index=True)

    # URL exacta de la página del producto para rastreo y verificación.
    product_url = Column(String, nullable=True)

    # ─── Timestamps ───────────────────────────────────────────
    scraped_at  = Column(DateTime, default=datetime.utcnow)

    # ─── Relación con historial de precios ────────────────────
    # cascade="all, delete-orphan": si se elimina un producto,
    # se eliminan también todos sus registros de historial.
    price_history = relationship(
        "PriceHistory",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Product id={self.id} name={self.name!r} "
            f"price={self.price} competitor={self.competitor!r}>"
        )
