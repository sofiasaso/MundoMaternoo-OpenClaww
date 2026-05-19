# Constitución del Proyecto — MundoMaterno-OpenClaw

**Fecha:** Mayo 2026
**Metodología:** Spec Kit (Vibe Coding)

---

## Proyecto

**Nombre:** MundoMaterno-OpenClaw
**Objetivo:** Sistema de inteligencia competitiva para monitoreo automatizado de precios y productos de competidores en el mercado de ropa materna colombiana.

---

## Stack no negociable

| Capa | Tecnología |
|------|-----------|
| Frontend | React 19 + Vite 8 |
| Backend | FastAPI |
| Base de datos | SQLite + SQLAlchemy |
| Scraping | Python + BeautifulSoup + Requests |
| Visualización | CSS nativo (minimalista) |

---

## Reglas del proyecto

- Código modular y legible, separación estricta de responsabilidades
- Variables sensibles en `.env`, nunca en el código
- Scrapers desacoplados del backend (pueden correrse de forma independiente)
- Logs claros en terminal para debugging
- Evitar complejidad innecesaria — funcional sobre perfecto
- No usar `any` como tipo en TypeScript si se migrara

---

## Alcance de esta versión

**Incluye:**
- Monitoreo de productos de Carymar, Saraisa y OhMama
- Detección de cambios de precios con registro histórico
- Dashboard web con métricas ejecutivas
- Alertas de reducciones de precio ≥ 10%
- Scraping manual disparado desde el dashboard

**No incluye:**
- Autenticación de usuarios
- Despliegue en cloud
- Multiagentes reales
- Automatización con cron jobs (esta versión)
- PostgreSQL (migrado a SQLite por criterio técnico justificable)

---

## Decisión técnica: SQLite sobre PostgreSQL

Inicialmente se planeó usar PostgreSQL, pero se migró a SQLite por:
- Problemas de instalación en el entorno local de desarrollo
- Prioridad en la continuidad e iteración rápida
- SQLite es suficiente para el volumen de datos de un prototipo académico

Esta decisión está documentada y es defendible académicamente como criterio técnico real.

---

## Testing

- Tests básicos para endpoints críticos con `pytest`
- Validación de scrapers corriendo de forma independiente
- Verificación de integridad de datos en SQLite
