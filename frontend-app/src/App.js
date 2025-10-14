import "./App.css";
import React, { useState, useEffect } from "react";

const API = ""; 

export default function App() {
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [resultado, setResultado] = useState(null);
  const [historial, setHistorial] = useState([]);

  // Filtros
  const [opFilter, setOpFilter] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [sortBy, setSortBy] = useState("date");
  const [order, setOrder] = useState("desc");

  async function callOp(path, a, b) {
    const res = await fetch(`${API}/calculadora/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ a: Number(a), b: Number(b) }),
    });
    const data = await res.json();
    if (!res.ok) {
      const msg =
        data?.detail?.error || data?.error || "Ocurrió un error"; 
      alert(msg);
      return null;
    }
    return data;
  }

  const onSum = async () => {
    const data = await callOp("sum", a, b);
    if (data) {
      setResultado(data.resultado);
      await loadHistory();
    }
  };
  const onSub = async () => {
    const data = await callOp("sub", a, b);
    if (data) {
      setResultado(data.resultado);
      await loadHistory();
    }
  };
  const onMul = async () => {
    const data = await callOp("mul", a, b);
    if (data) {
      setResultado(data.resultado);
      await loadHistory();
    }
  };
  const onDiv = async () => {
    const data = await callOp("div", a, b);
    if (data) {
      setResultado(data.resultado);
      await loadHistory();
    }
  };

  function toIso(s) {
    if (!s) return null;
    
    return new Date(`${s}T00:00:00Z`).toISOString();
  }

  async function loadHistory() {
    const params = new URLSearchParams();
    if (opFilter) params.set("op", opFilter);
    if (from) params.set("date_from", toIso(from));
    if (to) params.set("date_to", toIso(to));
    if (sortBy) params.set("sort_by", sortBy);
    if (order) params.set("order", order);

    const res = await fetch(
      `${API}/calculadora/historial?${params.toString()}`
    );
    const data = await res.json();
    setHistorial(Array.isArray(data.historial) ? data.historial : []);
  }

  useEffect(() => {
    loadHistory();
    
  }, []);

  const symbol = (op) =>
    op === "sum" ? "+" : op === "sub" ? "-" : op === "mul" ? "×" : "÷";

  const opNameEs = (op) =>
    op === "sum" ? "suma" : op === "sub" ? "resta" : op === "mul" ? "multiplicación" : "división";

  return (
    <div className="app">
      <div className="card">
        <h1>Calculadora</h1>

        <div className="row">
          <input
            type="number"
            value={a}
            onChange={(e) => setA(e.target.value)}
            placeholder="Número 1"
          />
          <input
            type="number"
            value={b}
            onChange={(e) => setB(e.target.value)}
            placeholder="Número 2"
          />
        </div>

        <div className="row buttons">
          <button onClick={onSum} className="btn">Sumar</button>
          <button onClick={onSub} className="btn">Restar</button>
          <button onClick={onMul} className="btn">Multiplicar</button>
          <button onClick={onDiv} className="btn">Dividir</button>
        </div>

        {resultado !== null && <div className="result">Resultado: {resultado}</div>}

        <h3>Historial (con filtros)</h3>
        <div className="filters">
          <label>
            Operación:
            <select
              value={opFilter}
              onChange={(e) => setOpFilter(e.target.value)}
            >
              <option value="">Todas</option>
              <option value="sum">suma</option>            {/* texto en español */}
              <option value="sub">resta</option>
              <option value="mul">multiplicación</option>
              <option value="div">división</option>
            </select>
          </label>
          <label>
            Desde:
            <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
          </label>
          <label>
            Hasta:
            <input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
          </label>
          <label>
            Ordenar por:
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="date">Fecha</option>
              <option value="result">Resultado</option>
            </select>
          </label>
          <label>
            Dirección:
            <select value={order} onChange={(e) => setOrder(e.target.value)}>
              <option value="desc">Desc</option>
              <option value="asc">Asc</option>
            </select>
          </label>
          <button className="btn" onClick={loadHistory}>Filtrar</button>
        </div>

        <ul className="history">
          {historial.map((op, i) => (
            <li key={i}>
              <span className="chip">[{opNameEs(op.operacion)}]</span>{" "}
              {op.a} {symbol(op.operacion)} {op.b} = <strong>{op.resultado}</strong>{" "}
              <span className="date">({op.date})</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
