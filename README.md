# MundoMaterno-OpenClaw

> Sistema de Inteligencia Competitiva para el sector de ropa materna — monitoreo automatizado de competidores, almacenamiento histórico de precios y visualización ejecutiva de métricas.

---

## Tabla de contenidos

1. [Descripción del problema](#descripción-del-problema)
2. [Solución propuesta](#solución-propuesta)
3. [Arquitectura general](#arquitectura-general)
4. [Estructura de carpetas](#estructura-de-carpetas)
5. [Requisitos previos](#requisitos-previos)
6. [Instalación](#instalación)
7. [Correr el backend](#correr-el-backend)
8. [Correr el frontend](#correr-el-frontend)
9. [Endpoints principales](#endpoints-principales)
10. [Flujo del sistema](#flujo-del-sistema)
11. [Alcance y objetivos](#alcance-y-objetivos)
12. [Futuras mejoras](#futuras-mejoras)
13. [Integrantes](#integrantes)

---

## Descripción del problema

Mundo Materno opera en un mercado altamente competitivo de ropa materna donde precios, disponibilidad y promociones cambian de forma constante. El monitoreo de competidores se realizaba de manera manual y esporádica, lo que generaba tres consecuencias directas:

- Incapacidad para detectar variaciones de precio en tiempo oportuno.
- Ausencia de datos históricos que permitan identificar tendencias.
- Toma de decisiones comerciales sin respaldo en información real del mercado.

El prototipo previo, desarrollado en Google Colab, era limitado, no automatizado y no escalable.

---

## Solución propuesta

MundoMaterno-OpenClaw es un sistema de inteligencia competitiva que automatiza el ciclo completo de monitoreo: extrae datos de sitios competidores mediante scraping web, los normaliza y almacena en una base de datos relacional, calcula métricas estratégicas y los expone a través de un dashboard ejecutivo interactivo.

El sistema actúa como un agente central coordinado por OpenClaw, capaz de gestionar errores, adaptarse a cambios en la estructura de los sitios y generar reportes en lenguaje natural.

---

## Arquitectura general

```
┌─────────────────────────────────────────────────────────┐
│                   FRONTEND (React + Vite)               │
│             Dashboard ejecutivo con Chart.js            │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP / REST
┌───────────────────────────▼─────────────────────────────┐
│                    BACKEND (FastAPI)                     │
│         API REST · Lógica de negocio · Alertas          │
└──────────────┬──────────────────────────┬───────────────┘
               │                          │
┌──────────────▼──────────┐   ┌───────────▼───────────────┐
│   Base de datos          │   │  Scrapers (BeautifulSoup)  │
│  SQLite + SQLAlchemy     │   │  Extracción semanal        │
│  Histórico de precios    │   │  por competidor            │
└─────────────────────────┘   └───────────────────────────┘
```

**Stack tecnológico:**

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI |
| ORM | SQLAlchemy |
| Base de datos | SQLite |
| Extracción de datos | BeautifulSoup |
| Frontend | React + Vite |
| Visualización | Chart.js |

---

## Estructura de carpetas

```
MundoMaterno-OpenClaw/
│
├── backend/                  # API REST y lógica del servidor
│   ├── main.py               # Punto de entrada FastAPI
│   ├── models.py             # Modelos SQLAlchemy
│   ├── schemas.py            # Schemas Pydantic
│   ├── database.py           # Configuración de conexión SQLite
│   ├── crud.py               # Operaciones sobre la base de datos
│   └── routers/
│       ├── productos.py
│       ├── competidores.py
│       └── metricas.py
│
├── scrapers/                 # Scripts de extracción de datos
│   ├── base_scraper.py       # Clase base reutilizable
│   ├── competidor_a.py       # Scraper específico por sitio
│   └── runner.py             # Orquestador de ejecución
│
├── data/                     # Datos persistentes y respaldos
│   ├── mundomaterno.db       # Base de datos SQLite
│   └── exports/              # Exportaciones CSV o JSON
│
├── frontend/                 # Interfaz de usuario
│   ├── src/
│   │   ├── components/       # Componentes React reutilizables
│   │   ├── pages/            # Vistas del dashboard
│   │   ├── services/         # Llamadas a la API
│   │   └── main.jsx
│   ├── index.html
│   └── vite.config.js
│
├── docs/                     # Documentación del proyecto
│   ├── arquitectura.md
│   └── decisiones.md
│
└── README.md
```

---

## Requisitos previos

- Python 3.10 o superior
- Node.js 18 o superior
- pip
- npm o pnpm

---

## Instalación

**1. Clonar el repositorio**

```bash
git clone https://github.com/sofiasaso/MundoMaterno-OpenClaw.git
cd MundoMaterno-OpenClaw
```

**2. Crear entorno virtual e instalar dependencias del backend**

```bash
cd backend
python -m venv venv

# En Windows:
venv\Scripts\activate

# En Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

**3. Instalar dependencias del frontend**

```bash
cd ../frontend
npm install
```

---

## Correr el backend

Desde la carpeta `backend/` con el entorno virtual activo:

```bash
uvicorn main:app --reload
```

El servidor queda disponible en: `http://localhost:8000`

Documentación automática de la API en: `http://localhost:8000/docs`

---

## Correr el frontend

Desde la carpeta `frontend/`:

```bash
npm run dev
```

La interfaz queda disponible en: `http://localhost:5173`

---

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/productos/` | Lista todos los productos registrados |
| `GET` | `/productos/{id}` | Detalle de un producto específico |
| `GET` | `/competidores/` | Lista de competidores monitoreados |
| `GET` | `/metricas/precios` | Histórico de precios por competidor |
| `GET` | `/metricas/alertas` | Alertas activas (bajadas de precio, nuevos productos) |
| `POST` | `/scrapers/ejecutar` | Dispara manualmente una extracción |
| `GET` | `/reportes/resumen` | Resumen ejecutivo del periodo actual |

---

## Flujo del sistema

```
1. EXTRACCIÓN
   El scraper visita los sitios de competidores definidos
   y extrae precios, nombres y disponibilidad de productos.

2. NORMALIZACIÓN
   Los datos se limpian, estandarizan y validan antes
   de ser almacenados (nombres, monedas, categorías).

3. ALMACENAMIENTO
   SQLAlchemy persiste los registros en SQLite con
   marca de tiempo para mantener historial completo.

4. PROCESAMIENTO
   El backend calcula métricas: variación de precios,
   productos nuevos, tendencias por categoría.

5. ALERTAS
   Se detectan automáticamente eventos relevantes:
   reducción de precio significativa, nuevos ingresos.

6. VISUALIZACIÓN
   El dashboard React consume la API y muestra
   gráficas con Chart.js, filtradas por fecha y competidor.
```

---

## Alcance y objetivos

**Objetivo general**

Desarrollar un sistema automatizado que permita a Mundo Materno tomar decisiones comerciales basadas en datos reales y actualizados del mercado competidor.

**Objetivos específicos**

- Automatizar la recolección semanal de precios y productos de al menos tres competidores directos.
- Mantener un historial limpio y normalizado en base de datos relacional, con limpieza y normalización de los datos de cada competidor como paso obligatorio del pipeline.
- Detectar y notificar variaciones de precio iguales o superiores al 10%.
- Proveer un dashboard ejecutivo con métricas accionables.

**Alcance**

El sistema cubre el monitoreo de sitios web públicos de competidores en el segmento de ropa materna en Colombia. No incluye integración con sistemas internos de Mundo Materno ni procesamiento de imágenes de producto en esta fase.

---

## Futuras mejoras

- Integración con WhatsApp o correo para envío automático de alertas.
- Soporte para más competidores mediante scrapers modulares adicionales.
- Análisis de sentimiento sobre reseñas de productos de la competencia.
- Exportación de reportes en PDF con un solo clic.
- Autenticación de usuarios con roles (administrador / visualizador).
- Migración a PostgreSQL para mayor escalabilidad.
- Programación automática de scrapers mediante cron jobs.

---

## Integrantes

| Nombre | Rol |
|--------|-----|
| Lian Patricia Niño García | Desarrollo backend |
| Laura Sofía Sánchez Soto | Extracción y procesamiento de datos |
| David Esteban Forero Palomino | Base de datos y API |
| Laura Valentina Pardo Vargas | Frontend y visualización |

---

> Proyecto académico desarrollado con OpenClaw como agente central de inteligencia competitiva.
