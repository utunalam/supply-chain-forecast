import { useEffect, useState } from "react";
import ProductManager from "./ProductManager";
import "./App.css";

// Remove any trailing slash so we never call "//replenishment".
const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

function formatNumber(value, digits = 2) {
  if (value === "" || value === null || value === undefined) {
    return "—";
  }

  const number = Number(value);

  return Number.isFinite(number)
    ? number.toLocaleString("en-MY", {
        maximumFractionDigits: digits,
      })
    : value;
}

function statusClass(recommendation = "") {
  if (recommendation.startsWith("INACTIVE")) return "status status-inactive";
  if (recommendation.startsWith("SLOW-MOVING")) return "status status-slow";
  if (recommendation.includes("REVIEW")) return "status status-review";
  return "status status-ok";
}

function App() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // quiet = true refreshes the numbers without hiding the page,
  // used after every product change.
  async function loadReport(quiet = false) {
    if (!quiet) setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/replenishment`);

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data = await response.json();
      setReport(data);
    } catch (err) {
      setError(
        "Unable to load the replenishment report. The server may be waking up; try again in a minute."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReport();
  }, []);

  const items = report?.items ?? [];
  const totalStock = items.reduce(
    (sum, item) => sum + (Number(item.available_stock_latest_snapshot) || 0),
    0
  );
  const totalDemand = items.reduce(
    (sum, item) => sum + (Number(item.completed_units_in_window) || 0),
    0
  );
  const needsReorder = items.filter(
    (item) => item.recommendation === "REPLENISHMENT REVIEW"
  ).length;
  const needsReview = items.filter((item) =>
    item.recommendation?.includes("REVIEW")
  ).length;

  return (
    <main className="dashboard">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">SC</div>
          <div>
            <h1>Supply Chain</h1>
            <p>Inventory &amp; Replenishment Dashboard</p>
          </div>
        </div>
        <button className="refresh-button" onClick={() => loadReport()}>
          Refresh report
        </button>
      </header>

      <section className="intro">
        <span className="eyebrow">OPERATIONS OVERVIEW</span>
        <h2>Inventory at a glance</h2>
        <p>
          Review current stock, recent demand and provisional replenishment
          recommendations. Edit a product below to see the numbers change.
        </p>
      </section>

      <div className="notice">
        <strong>SYNTHETIC DATA — DEVELOPMENT / TESTING ONLY</strong>
        <span>Not for purchasing decisions.</span>
      </div>

      {loading && (
        <p className="message">
          Loading replenishment report… the free server can take up to a
          minute to wake up.
        </p>
      )}

      {error && (
        <div className="error-panel">
          <p>{error}</p>
          <button onClick={() => loadReport()}>Try again</button>
        </div>
      )}

      {!loading && !error && report && (
        <>
          <section className="metrics">
            <article className="metric-card">
              <span>Products in report</span>
              <strong>{report.count}</strong>
              <small>{report.linked_count} linked to the product list</small>
            </article>
            <article className="metric-card">
              <span>Latest stock total</span>
              <strong>{formatNumber(totalStock, 0)}</strong>
              <small>Units across displayed products</small>
            </article>
            <article className="metric-card">
              <span>Completed units sold</span>
              <strong>{formatNumber(totalDemand, 0)}</strong>
              <small>During the 14-day window</small>
            </article>
            <article className="metric-card">
              <span>Need reordering</span>
              <strong>{needsReorder}</strong>
              <small>At or below their reorder point</small>
            </article>
          </section>

          <section className="assumptions">
            <div>
              <span>Demand window</span>
              <strong>
                {items[0]?.demand_window_start ?? "—"} to{" "}
                {items[0]?.demand_window_end ?? "—"}
              </strong>
            </div>
            <div>
              <span>Lead time</span>
              <strong>Set per product (default {report.lead_time_days_assumed} days)</strong>
            </div>
            <div>
              <span>Safety stock</span>
              <strong>Set per product (default {report.safety_stock_days_assumed} days)</strong>
            </div>
          </section>

          <section className="report-section">
            <div className="section-heading">
              <div>
                <h2>Replenishment recommendations</h2>
                <p>
                  Reorder point = average daily demand × (lead time + safety
                  stock). Suggested units are rounded up.
                </p>
              </div>
              <span className="product-count">{items.length} products</span>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Completed sales</th>
                    <th>Avg. daily demand</th>
                    <th>Lead + safety</th>
                    <th>Latest stock</th>
                    <th>Reorder point</th>
                    <th>Suggested units</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={`${item.inventory_item_id}-${item.sales_item_id}`}>
                      <td>
                        <strong>
                          {item.product_name || item.inventory_description}
                        </strong>
                        <small>SKU: {item.inventory_item_id}</small>
                        <small>
                          Snapshot: {item.latest_snapshot_date || "Unavailable"}
                        </small>
                        {!item.in_product_list && (
                          <small className="pm-unlinked">
                            Not in product list, using defaults
                          </small>
                        )}
                      </td>
                      <td>{formatNumber(item.completed_units_in_window)}</td>
                      <td>{formatNumber(item.average_daily_demand, 4)}</td>
                      <td>
                        {item.lead_time_days_assumed} + {item.safety_stock_days_assumed} days
                      </td>
                      <td>
                        {formatNumber(item.available_stock_latest_snapshot, 0)}
                      </td>
                      <td>{formatNumber(item.provisional_reorder_point_units)}</td>
                      <td>
                        {formatNumber(
                          item.suggested_replenishment_units_provisional,
                          0
                        )}
                      </td>
                      <td>
                        <span className={statusClass(item.recommendation)}>
                          {item.recommendation}
                        </span>
                        {item.review_note && (
                          <small className="review-note">{item.review_note}</small>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="footnote">
              These recommendations use a simple 14-day average and
              provisional assumptions. Validate the assumptions before any
              operational use.
            </p>
          </section>

          {needsReview > 0 && (
            <p className="review-summary">
              {needsReview} product(s) have a review-related status or require
              additional attention.
            </p>
          )}
        </>
      )}

      {/* Product CRUD panel: every change reloads the report above. */}
      <ProductManager
        apiUrl={API_URL}
        reportItems={items}
        onChanged={() => loadReport(true)}
      />

      <footer>Supply Chain Forecasting System · Synthetic demonstration</footer>
    </main>
  );
}

export default App;
