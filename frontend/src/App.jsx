import { useEffect, useState } from "react";
import "./App.css";

function App() {

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  const [competitor, setCompetitor] = useState("");

  useEffect(() => {

    let url = "http://127.0.0.1:8000/products/";

    if (competitor) {
      url += `?competitor=${competitor}`;
    }

    fetch(url)
      .then((res) => res.json())
      .then((data) => {

        setProducts(data.products || []);
        setLoading(false);

      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });

  }, [competitor]);

  return (
    <div className="container">

      <h1>MundoMaterno</h1>

      <p>Sistema de inteligencia competitiva.</p>

      <div className="filters">

        <select
          value={competitor}
          onChange={(e) => setCompetitor(e.target.value)}
        >
          <option value="">Todos</option>
          <option value="carymar">Carymar</option>
          <option value="saraisa">Saraisa</option>
          <option value="ohmama">OhMama</option>
        </select>

      </div>

      {loading ? (
        <p>Cargando productos...</p>
      ) : (
        <div className="grid">

          {products.map((product) => (

            <div className="card" key={product.id}>

              <h3>{product.name}</h3>

              <p>
                <strong>Competidor:</strong> {product.competitor}
              </p>

              <p>
                <strong>Categoría:</strong> {product.category}
              </p>

              <p>
                <strong>Precio:</strong> ${product.price}
              </p>

              {product.product_url ? (
                <a
                  href={product.product_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Ver producto
                </a>
              ) : (
                <p>Sin URL</p>
              )}

            </div>

          ))}

        </div>
      )}

    </div>
  );
}

export default App;