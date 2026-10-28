
import { useEffect, useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

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

function App() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadReport() {
    setLoading(true);
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
        "Unable to load the replenishment report. Check that the FastAPI backend is running."
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
  const slowMoving = items.filter((item) =>
    item.recommendation?.startsWith("SLOW-MOVING")
  ).length;
  const needsReview = items.filter(
    (item) =>
      item.recommendation?.includes("REVIEW") ||
      item.recommendation?.includes("REPLENISHMENT")
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
        <button className="refresh-button" onClick={loadReport}>
          Refresh report
        </button>
      </header>

      <section className="intro">
        <span className="eyebrow">OPERATIONS OVERVIEW</span>
        <h2>Inventory at a glance</h2>
        <p>
          Review current stock, recent demand and provisional replenishment
          recommendations.
        </p>
      </section>

      <div className="notice">
        <strong>SYNTHETIC DATA — DEVELOPMENT / TESTING ONLY</strong>
        <span>Not for purchasing decisions.</span>
      </div>

      {loading && <p className="message">Loading replenishment report…</p>}

      {error && (
        <div className="error-panel">
          <p>{error}</p>
          <button onClick={loadReport}>Try again</button>
        </div>
      )}

      {!loading && !error && report && (
        <>
          <section className="metrics">
            <article className="metric-card">
              <span>Mapped products</span>
              <strong>{report.count}</strong>
              <small>Approved product mappings</small>
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
              <span>Slow-moving products</span>
              <strong>{slowMoving}</strong>
              <small>Flagged for longer-history review</small>
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
              <span>Lead time assumption</span>
              <strong>{report.lead_time_days_assumed} days</strong>
            </div>
            <div>
              <span>Safety stock assumption</span>
              <strong>{report.safety_stock_days_assumed} days</strong>
            </div>
          </section>

          <section className="report-section">
            <div className="section-heading">
              <div>
                <h2>Replenishment recommendations</h2>
                <p>
                  Stock is taken from the latest dated inventory snapshot.
                </p>
              </div>
              <span className="product-count">
                {items.length} products
              </span>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Completed sales</th>
                    <th>Avg. daily demand</th>
                    <th>Latest stock</th>
                    <th>Reorder point</th>
                    <th>Suggested units</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.inventory_item_id}>
                      <td>
                        <strong>{item.inventory_description}</strong>
                        <small>
                          Inventory ID: {item.inventory_item_id}
                        </small>
                        <small>
                          Snapshot: {item.latest_snapshot_date || "Unavailable"}
                        </small>
                      </td>
                      <td>{formatNumber(item.completed_units_in_window)}</td>
                      <td>{formatNumber(item.average_daily_demand, 4)}</td>
                      <td>
                        {formatNumber(item.available_stock_latest_snapshot, 0)}
                      </td>
                      <td>
                        {formatNumber(item.provisional_reorder_point_units, 4)}
                      </td>
                      <td>
                        {formatNumber(
                          item.suggested_replenishment_units_provisional
                        )}
                      </td>
                      <td>
                        <span
                          className={`status ${
                            item.recommendation?.startsWith("SLOW-MOVING")
                              ? "status-slow"
                              : item.recommendation?.includes("REVIEW")
                                ? "status-review"
                                : "status-ok"
                          }`}
                        >
                          {item.recommendation}
                        </span>
                        {item.review_note && (
                          <small className="review-note">
                            {item.review_note}
                          </small>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="footnote">
              These recommendations use a simple 14-day average and
              provisional assumptions. Validate the assumptions before
              any operational use.
            </p>
          </section>

          {needsReview > 0 && (
            <p className="review-summary">
              {needsReview} product(s) have a review-related status or
              require additional attention.
            </p>
          )}
        </>
      )}

      <footer>
        Supply Chain Forecasting System · Synthetic demonstration
      </footer>
    </main>
  );
}

export default App;
