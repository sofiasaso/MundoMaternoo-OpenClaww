# ==============================================================================
# ARCHIVO 5: /backend/models/price_history.py
# TIPO: Modelo de datos ORM (Python)
# FUNCIÓN: Registra cada cambio de precio detectado en un producto
#          competidor. Permite a Mundo Materno ver la evolución histórica
#          de precios de Carymar, Saraisa y OhMama a lo largo del tiempo.
#
# CUÁNDO SE GENERA UN REGISTRO:
#   Cada vez que el scraper visita un producto que ya existía en la base
#   de datos y detecta que su precio cambió respecto al anterior.
#
# RELACIÓN: Muchos PriceHistory pertenecen a un Product.
# ==============================================================================

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database.connection import Base


class PriceHistory(Base):
    __tablename__ = "price_history"

    # ─── Identificación ───────────────────────────────────────
    id          = Column(Integer, primary_key=True, index=True)

    # Clave foránea al producto cuyo precio cambió.
    product_id  = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ─── Precios ──────────────────────────────────────────────
    old_price   = Column(Float, nullable=False)  # Precio registrado antes
    new_price   = Column(Float, nullable=False)  # Precio nuevo detectado

    # ─── Timestamp ────────────────────────────────────────────
    # Momento exacto en que el scraper detectó el cambio.
    detected_at = Column(DateTime, default=datetime.utcnow)

    # ─── Relación inversa ─────────────────────────────────────
    product     = relationship("Product", back_populates="price_history")

    @property
    def reduction_pct(self):
        """Calcula el porcentaje de reducción de precio."""
        if self.old_price <= 0:
            return 0.0
        return round((self.old_price - self.new_price) / self.old_price * 100, 2)

    def __repr__(self):
        return (
            f"<PriceHistory product_id={self.product_id} "
            f"{self.old_price} → {self.new_price} "
            f"({self.reduction_pct}%)>"
        )
