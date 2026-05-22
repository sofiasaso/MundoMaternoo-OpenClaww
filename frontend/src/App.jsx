import { useState, useEffect, useMemo, useCallback } from "react";
import "./App.css";

import igMM from "./assets/igMM.png";
import fkMM from "./assets/fkMM.png";
import wpMM from "./assets/wpMM.png";
import correoMM from "./assets/correoMM.png";

/* ── Constantes ─────────────────────────────────────────── */
const API = "http://127.0.0.1:8000";
const COMPETITORS = ["carymar", "ohmama"];

/* ── Utilidades ─────────────────────────────────────────── */
const cop = (n) =>
  n != null
    ? "$" + Number(n).toLocaleString("es-CO", { maximumFractionDigits: 0 })
    : "—";

const fdate = (iso) =>
  iso
    ? new Date(iso).toLocaleDateString("es-CO", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "—";

const capitalize = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : "");

/* ================================================================
   COMPONENTES INTERNOS
================================================================ */

/* ── KPI Card ──────────────────────────────────────────────── */
function KpiCard({ label, value, sub, barColor, loading }) {
  return (
    <div className="kpi-card">
      <div className="kpi-bar" style={{ background: barColor }} />
      <p className="kpi-label">{label}</p>
      {loading ? (
        <div className="kpi-skeleton" />
      ) : (
        <p className="kpi-value" style={{ color: barColor }}>
          {value ?? "—"}
        </p>
      )}
      {sub && <p className="kpi-sub">{sub}</p>}
    </div>
  );
}

/* ── Panel de alertas ──────────────────────────────────────── */
function AlertsPanel({ alerts, loading }) {
  return (
    <div className="panel">
      <div className="panel-head alerts-head">
        <div>
          <p className="panel-title alerts-title">Alertas de precio</p>
          <p className="panel-count">Reducciones ≥ 10%</p>
        </div>
        {!loading && (
          <span className="alerts-badge">
            {alerts.length} alerta{alerts.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      <div className="alerts-body">
        {loading && <p className="state">Cargando alertas…</p>}

        {!loading && alerts.length === 0 && (
          <div className="alerts-empty">
            <span className="alerts-empty-icon">✓</span>
            <p>Sin alertas activas.</p>
            <p style={{ fontSize: ".74rem", marginTop: ".2rem", opacity: .7 }}>
              Se generan cuando un competidor baja precios ≥ 10%.
            </p>
          </div>
        )}

        {!loading &&
          alerts.map((a, i) => (
            <div key={i} className="alert-item">
              <div className="alert-top">
                <span className="alert-comp">{a.competitor}</span>
                <span className="alert-pct">-{a.reduction_pct}%</span>
              </div>
              <p className="alert-name">{a.product_name}</p>
              <div className="alert-prices">
                <span className="alert-old">{cop(a.old_price)}</span>
                <span className="alert-arrow">→</span>
                <span className="alert-new">{cop(a.new_price)}</span>
              </div>
              {a.product_url && (
                <a
                  href={a.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="alert-link"
                >
                  Ver producto ↗
                </a>
              )}
            </div>
          ))}
      </div>
    </div>
  );
}

/* ── Tabla de productos ────────────────────────────────────── */
function ProductTable({ products, loading, error }) {
  const [search, setSearch] = useState("");
  const [sortF, setSortF] = useState("scraped_at");
  const [sortD, setSortD] = useState("desc");

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    let list = products.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        (p.category ?? "").toLowerCase().includes(q)
    );
    list = [...list].sort((a, b) => {
      let va = a[sortF] ?? "",
        vb = b[sortF] ?? "";
      if (typeof va === "string") va = va.toLowerCase();
      if (typeof vb === "string") vb = vb.toLowerCase();
      if (va < vb) return sortD === "asc" ? -1 : 1;
      if (va > vb) return sortD === "asc" ? 1 : -1;
      return 0;
    });
    return list;
  }, [products, search, sortF, sortD]);

  const sort = (f) => {
    if (sortF === f) setSortD((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortF(f); setSortD("asc"); }
  };

  const SortIcon = ({ f }) =>
    sortF !== f ? (
      <span style={{ opacity: 0.3 }}>↕</span>
    ) : (
      <span style={{ color: "var(--agua)" }}>{sortD === "asc" ? "↑" : "↓"}</span>
    );

  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <p className="panel-title">Productos monitoreados</p>
          {!loading && (
            <p className="panel-count">
              {filtered.length} resultado{filtered.length !== 1 ? "s" : ""}
            </p>
          )}
        </div>
        <div className="controls">
          <input
            className="search-input"
            type="text"
            placeholder="Buscar por nombre o categoría…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {loading && (
        <div className="state">
          <span className="state-icon">⟳</span>Cargando productos…
        </div>
      )}

      {!loading && error && (
        <div className="state" style={{ color: "var(--fucsia)" }}>
          <span className="state-icon">✕</span>{error}
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="state">
          <span className="state-icon">◎</span>
          {search
            ? `Sin resultados para "${search}"`
            : "No hay productos aún. Ejecuta el scraping primero."}
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {[
                  { l: "Producto",    f: "name" },
                  { l: "Categoría",   f: "category" },
                  { l: "Precio",      f: "price" },
                  { l: "Tienda",      f: "competitor" },
                  { l: "Actualizado", f: "scraped_at" },
                ].map((col) => (
                  <th key={col.f} onClick={() => sort(col.f)}>
                    {col.l} <SortIcon f={col.f} />
                  </th>
                ))}
                <th>Ver</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id}>
                  <td className="td-name" title={p.name}>{p.name}</td>
                  <td>{p.category ?? "—"}</td>
                  <td className="td-price">{cop(p.price)}</td>
                  <td>
                    <span className={`badge badge-${p.competitor}`}>
                      {p.competitor}
                    </span>
                  </td>
                  <td className="td-muted">{fdate(p.scraped_at)}</td>
                  <td>
                    {p.product_url ? (
                      <a
                        href={p.product_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="td-link"
                      >
                        ↗
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/* ================================================================
   APP PRINCIPAL
================================================================ */
export default function App() {
  /* ── Estado ── */
  const [metrics,    setMetrics]    = useState(null);
  const [products,   setProducts]   = useState([]);
  const [alerts,     setAlerts]     = useState([]);
  const [status,     setStatus]     = useState(null);
  const [competitor, setCompetitor] = useState("");        // filtro activo
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [loadM,      setLoadM]      = useState(true);
  const [loadP,      setLoadP]      = useState(true);
  const [loadA,      setLoadA]      = useState(true);
  const [errorP,     setErrorP]     = useState(null);
  const [scraping,   setScraping]   = useState(false);
  const [toast,      setToast]      = useState(null);

  /* ── Helpers de fetch ── */
  const fetchMetrics = useCallback(async () => {
    setLoadM(true);
    try {
      const [m, s] = await Promise.all([
        fetch(`${API}/metrics/`).then((r) => r.json()),
        fetch(`${API}/scraping/status`).then((r) => r.json()),
      ]);
      setMetrics(m);
      setStatus(s);
    } catch { setMetrics(null); }
    finally { setLoadM(false); }
  }, []);

  const fetchProducts = useCallback(async (comp) => {
    setLoadP(true);
    setErrorP(null);
    try {
      const url = comp
        ? `${API}/products/?competitor=${comp}&limit=300`
        : `${API}/products/?limit=300`;
      const data = await fetch(url).then((r) => r.json());
      setProducts(data.products ?? []);
    } catch { setErrorP("No se pudo conectar con el backend."); }
    finally { setLoadP(false); }
  }, []);

  const fetchAlerts = useCallback(async () => {
    setLoadA(true);
    try {
      const data = await fetch(`${API}/alerts/`).then((r) => r.json());
      setAlerts(data.alertas ?? []);
    } catch { setAlerts([]); }
    finally { setLoadA(false); }
  }, []);

  /* ── Carga inicial ── */
  useEffect(() => {
    fetchMetrics();
    fetchProducts("");
    fetchAlerts();
  }, [fetchMetrics, fetchProducts, fetchAlerts]);

  /* ── Cambio de filtro de competidor ── */
  useEffect(() => { fetchProducts(competitor); }, [competitor, fetchProducts]);

  /* ── Ejecutar scraping ── */
  const handleScraping = async () => {
    setScraping(true);
    try {
      await fetch(`${API}/scraping/run-scraping`, { method: "POST" });
      showToast("ok", "Scraping iniciado. Actualizando datos en unos minutos.");
      setTimeout(() => {
        fetchMetrics();
        fetchProducts(competitor);
        fetchAlerts();
      }, 4000);
    } catch {
      showToast("err", "No se pudo conectar con el servidor.");
    } finally { setScraping(false); }
  };

  const showToast = (type, msg) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3500);
  };

  /* ── Datos derivados ── */
  const resumen  = metrics?.resumen_general;
  const masBar   = metrics?.competidor_mas_barato;
  const porComp = (metrics?.por_competidor ?? [])
    .filter(c => c.competitor !== "saraisa");
  const comparativas = metrics?.comparativas_por_categoria ?? {};
  const categoriasDisponibles = Object.keys(comparativas);
  const categoriaActiva = selectedCategory
    ? comparativas[selectedCategory] ?? []
    : [];
  const variaciones = metrics?.ultimas_variaciones ?? [];
  const comparativas = metrics?.comparativas_por_categoria ?? {};
  const categoriasDisponibles = Object.keys(comparativas);

  const categoriaActiva = selectedCategory
    ? comparativas[selectedCategory] ?? []
    : [];

  const lastScrape = status?.ultimo_scraping
    ? new Date(status.ultimo_scraping).toLocaleString("es-CO", {
        day: "2-digit", month: "short", year: "numeric",
        hour: "2-digit", minute: "2-digit",
      })
    : null;

  /* ── Render ── */
  return (
    <div className="layout">

      {/* ── Navbar ── */}
      <nav className="navbar">
        <div className="navbar-brand">
          <span className="navbar-dot" />
          <span className="navbar-logo">
            Mundo<span>Materno</span>
          </span>
          <span className="navbar-chip">Inteligencia Competitiva</span>
        </div>

        <div className="navbar-right">
          {lastScrape && (
            <span className="navbar-status">Último scraping: {lastScrape}</span>
          )}
          <button
            className="btn btn-fucsia"
            onClick={handleScraping}
            disabled={scraping}
          >
            {scraping ? (
              <><span className="btn-spinner" /> Extrayendo…</>
            ) : (
              <>↻ Actualizar datos</>
            )}
          </button>
        </div>
      </nav>

      {/* ── Contenido ── */}
      <main className="main">


        {/* Cabecera - ORIGINALLLLLL */}
        {/*<div className="page-header">
          <h1 className="page-title">Dashboard competitivo</h1>
          <p className="page-sub">
            Monitoreo de precios · Carymar, Saraisa y OhMama
          </p>
        </div>*/}

          <div className="hero">
            <div className="page-header">
              <h1 className="page-title">Dashboard competitivo</h1>

              <p className="page-sub">
                Monitoreo de precios · Carymar, Saraisa y OhMama
              </p>
            </div>

            <div className="hero-logo">
              <img
                src="/images/Logo.png"
                alt="Logo Mundo Materno"
                className="hero-logo-img"
              />
            </div>

          </div>


        {/* KPIs */}
        <div className="kpi-grid">
          <KpiCard
            label="Productos monitoreados"
            value={resumen?.total_productos}
            sub={
              porComp.length
                ? porComp
                    .map(c => `${capitalize(c.competitor)}: ${c.total_productos}`)
                    .join(" · ")
                : "Sin datos aún"
            }
            //sub={porComp.length ? `En ${porComp.length} tiendas` : "Sin datos aún"}
            barColor="var(--agua)"
            loading={loadM}
          />
          <KpiCard
            label="Precio promedio global"
            value={cop(resumen?.precio_promedio_global)}
            sub="Sobre todos los productos"
            barColor="var(--agua-dark)"
            loading={loadM}
          />
          <div className="kpi-card">

          <div
            className="kpi-bar"
            style={{ background: "var(--agua)" }}
          />

          <p className="kpi-label">
            Tienda más económica
          </p>

          <p
            className="kpi-value"
            style={{ color: "var(--agua)" }}
          >
            {masBar ? capitalize(masBar.competitor) : "—"}
          </p>

          <p className="kpi-sub">
            {masBar
              ? `Prom. ${cop(masBar.precio_promedio)}`
              : "Ejecuta un scraping"}
          </p>

          <div className="ranking-list">

            {[...porComp]
              .sort((a,b) => a.precio_promedio - b.precio_promedio)
              .map((c, i) => (
                <div key={i} className="ranking-item">

                  <span>
                    #{i + 1} {capitalize(c.competitor)}
                  </span>

                  <strong>
                    {cop(c.precio_promedio)}
                  </strong>

                </div>
              ))}

          </div>

        </div>

          <div className="ranking-list">
            {[...porComp]
              .sort((a,b) => a.precio_promedio - b.precio_promedio)
              .map((c, i) => (
                <div key={i} className="ranking-item">
                  <span>
                    #{i + 1} {capitalize(c.competitor)}
                  </span>

                  <strong>
                    {cop(c.precio_promedio)}
                  </strong>
                </div>
              ))}
          </div>

          <KpiCard
            label="Cambios de precio"
            value={resumen?.total_cambios_detectados}
            sub="Variaciones históricas detectadas"
            barColor="var(--fucsia)"
            loading={loadM}
          />
        </div>


        <div className="category-panel panel">

          <div className="panel-head">
            <div>
              <p className="panel-title">
                Comparativa por categoría
              </p>

              <p className="panel-count">
                Analiza quién vende más barato por tipo de prenda
              </p>
            </div>

            <select
              className="category-select"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="">
                Selecciona categoría
              </option>

              {categoriasDisponibles.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {categoriaActiva.length > 0 && (
            <div className="category-ranking">

              {[...categoriaActiva]
                .sort((a,b) => a.precio_promedio - b.precio_promedio)
                .map((c, i) => (
                  <div key={i} className="category-card">

                    <p className="category-rank">
                      #{i + 1}
                    </p>

                    <p className="category-name">
                      {capitalize(c.competitor)}
                    </p>

                    <p className="category-price">
                      {cop(c.precio_promedio)}
                    </p>

                  </div>
                ))}

            </div>
          )}

        </div>





        {/* Chips por tienda */}
        {!loadM && porComp.length > 0 && (
          <div className="comp-row">
            {porComp.map((c) => (
              <div key={c.competitor} className="comp-chip">
                <span className="comp-chip-name">{capitalize(c.competitor)}</span>
                <span className="comp-chip-count">{c.total_productos} prods</span>
                <span className="comp-chip-price">{cop(c.precio_promedio)} prom.</span>
              </div>
            ))}
          </div>
        )}

        {/* Filtro por tienda + tabla + alertas */}
        <div style={{ marginBottom: ".75rem", display: "flex", gap: ".5rem", flexWrap: "wrap" }}>
          <button
            className={`btn ${competitor === "" ? "btn-fucsia" : "btn-outline"}`}
            onClick={() => setCompetitor("")}
          >
            Todas
          </button>
          {COMPETITORS.map((c) => (
            <button
              key={c}
              className={`btn ${competitor === c ? "btn-fucsia" : "btn-outline"}`}
              onClick={() => setCompetitor(c)}
            >
              {capitalize(c)}
            </button>
          ))}
        </div>

        <div className="bottom-grid">
          <ProductTable products={products} loading={loadP} error={errorP} />
          <AlertsPanel  alerts={alerts}     loading={loadA} />
        </div>

        <footer className="footer">

  <div className="footer-left">
    <img
      src="/images/Logo.png"
      alt="Mundo Materno"
      className="footer-logo"
    />

    <div>
      <p className="footer-brand">
        MundoMaterno
      </p>

      <p className="footer-copy">
        © 2026 Mundo Materno · Todos los derechos reservados
      </p>

      <p className="footer-academic">
        Proyecto académico desarrollado para la materia
        Tecnologías Disruptivas.
        <p></p>
        Las 3L y David.
      </p>
    </div>
  </div>

  <div className="footer-right">

    <p className="footer-social-title">
      Redes sociales
    </p>

    <div className="footer-socials">

      {/* Instagram */}
      <a
        href="https://www.instagram.com/mundo_materno__?utm_source=qr&igsh=cnBtdXVyNXJxejcx"
        target="_blank"
        rel="noopener noreferrer"
        className="social-icon-btn"
      >
        <img
          src={igMM}
          alt="Instagram Mundo Materno"
          className="social-icon"
        />
      </a>

      {/* Correo */}
      <a
        href="mailto:mundomaternoco@gmail.com"
        target="_blank"
        rel="noopener noreferrer"
        className="social-icon-btn"
      >
        <img
          src={correoMM}
          alt="Mail Mundo Materno"
          className="social-icon"
        />
      </a>

      {/* Facebook */}
      <a
        href="https://www.facebook.com/share/1dFyBUH7wJ/"
        target="_blank"
        rel="noopener noreferrer"
        className="social-icon-btn"
      >
        <img
          src={fkMM}
          alt="Facebook Mundo Materno"
          className="social-icon"
        />
      </a>

      {/* WhatsApp */}
      <a
        href="https://wa.me/573144252939"
        target="_blank"
        rel="noopener noreferrer"
        className="social-icon-btn"
      >
        <img
          src={wpMM}
          alt="WhatsApp Mundo Materno"
          className="social-icon"
        />
      </a>

    </div>

  </div>

</footer>

      </main>

      {/* Toast */}
      {toast && (
        <div className={`toast toast-${toast.type === "ok" ? "ok" : "err"}`}>
          {toast.msg}
        </div>
      )}
    </div>
  );
}