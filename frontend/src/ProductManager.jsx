import { useEffect, useState } from "react";

const EMPTY_FORM = {
  sku_code: "",
  product_name: "",
  category: "",
  lead_time_days: 7,
  safety_stock_days: 3,
};

// Turn FastAPI's error reply into one readable sentence.
function readError(data, status) {
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) {
    return data.detail
      .map((d) => `${d.loc?.at(-1) ?? "field"}: ${d.msg}`)
      .join("; ");
  }
  return `Request failed (${status})`;
}

function ProductManager({ apiUrl, reportItems, onChanged }) {
  const [skus, setSkus] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null); // { type, text }

  // One helper for every API call: sends JSON, throws a clear error.
  async function request(path, options = {}) {
    const response = await fetch(`${apiUrl}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(readError(data, response.status));
    return { status: response.status, data };
  }

  async function loadSkus() {
    try {
      const { data } = await request("/skus");
      setSkus(data);
    } catch (err) {
      setMessage({ type: "error", text: `Could not load products: ${err.message}` });
    }
  }

  useEffect(() => {
    loadSkus();
  }, []);

  // Run a change, show the result, then refresh the list AND the report.
  async function runChange(action, successText) {
    setBusy(true);
    setMessage(null);
    try {
      const result = await action();
      setMessage({ type: "ok", text: `${successText} (${result.status})` });
      await loadSkus();
      onChanged();
      return true;
    } catch (err) {
      setMessage({ type: "error", text: err.message });
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function createProduct() {
    const body = {
      ...form,
      category: form.category.trim() || null,
      lead_time_days: Number(form.lead_time_days),
      safety_stock_days: Number(form.safety_stock_days),
    };
    const ok = await runChange(
      () => request("/skus", { method: "POST", body: JSON.stringify(body) }),
      `Created ${body.sku_code}`
    );
    if (ok) setForm(EMPTY_FORM);
  }

  function startEdit(sku) {
    setEditingId(sku.id);
    setEditForm({
      product_name: sku.product_name,
      lead_time_days: sku.lead_time_days,
      safety_stock_days: sku.safety_stock_days,
    });
  }

  async function saveEdit(sku) {
    const body = {
      product_name: editForm.product_name,
      lead_time_days: Number(editForm.lead_time_days),
      safety_stock_days: Number(editForm.safety_stock_days),
    };
    const ok = await runChange(
      () =>
        request(`/skus/${sku.id}`, { method: "PATCH", body: JSON.stringify(body) }),
      `Updated ${sku.sku_code}`
    );
    if (ok) setEditingId(null);
  }

  function toggleActive(sku) {
    runChange(
      () =>
        request(`/skus/${sku.id}`, {
          method: "PATCH",
          body: JSON.stringify({ is_active: !sku.is_active }),
        }),
      sku.is_active ? `Deactivated ${sku.sku_code}` : `Activated ${sku.sku_code}`
    );
  }

  function deleteProduct(sku) {
    if (!window.confirm(`Delete ${sku.product_name} (${sku.sku_code})?`)) return;
    runChange(
      () => request(`/skus/${sku.id}`, { method: "DELETE" }),
      `Deleted ${sku.sku_code}`
    );
  }

  function syncFromReport() {
    runChange(
      () => request("/skus/sync-from-report", { method: "POST" }),
      "Added missing report products"
    );
  }

  // Is this SKU linked to a row in the replenishment report?
  function reportStatus(sku) {
    const row = reportItems.find(
      (item) => String(item.inventory_item_id).trim() === sku.sku_code
    );
    if (!row) return "No sales or stock data yet";
    return `In report · stock ${row.available_stock_latest_snapshot || "—"}`;
  }

  return (
    <section className="report-section product-manager">
      <div className="section-heading">
        <div>
          <h2>Product list</h2>
          <p>
            Changes here update the replenishment table above straight away.
            The SKU code links a product to the report.
          </p>
        </div>
        <button className="secondary-button" onClick={syncFromReport} disabled={busy}>
          Add missing report products
        </button>
      </div>

      {message && (
        <p className={`pm-message pm-${message.type}`} role="status">
          {message.text}
        </p>
      )}

      <div className="pm-form">
        <label>
          SKU code
          <input
            value={form.sku_code}
            onChange={(e) => setForm({ ...form, sku_code: e.target.value })}
            placeholder="DEMO-001"
          />
        </label>
        <label>
          Product name
          <input
            value={form.product_name}
            onChange={(e) => setForm({ ...form, product_name: e.target.value })}
            placeholder="Demo Wi-Fi LED Strip"
          />
        </label>
        <label>
          Category
          <input
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
            placeholder="Smart Home"
          />
        </label>
        <label>
          Lead time (days)
          <input
            type="number"
            min="0"
            value={form.lead_time_days}
            onChange={(e) => setForm({ ...form, lead_time_days: e.target.value })}
          />
        </label>
        <label>
          Safety stock (days)
          <input
            type="number"
            min="0"
            value={form.safety_stock_days}
            onChange={(e) => setForm({ ...form, safety_stock_days: e.target.value })}
          />
        </label>
        <button className="refresh-button" onClick={createProduct} disabled={busy}>
          Add product
        </button>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Product</th>
              <th>Lead time</th>
              <th>Safety stock</th>
              <th>Active</th>
              <th>Linked to report</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {skus.length === 0 && (
              <tr>
                <td colSpan="7">
                  No products yet. Add one above, or add the report products.
                </td>
              </tr>
            )}
            {skus.map((sku) =>
              editingId === sku.id ? (
                <tr key={sku.id}>
                  <td>{sku.id}</td>
                  <td>
                    <input
                      value={editForm.product_name}
                      onChange={(e) =>
                        setEditForm({ ...editForm, product_name: e.target.value })
                      }
                    />
                    <small>SKU: {sku.sku_code}</small>
                  </td>
                  <td>
                    <input
                      type="number"
                      min="0"
                      value={editForm.lead_time_days}
                      onChange={(e) =>
                        setEditForm({ ...editForm, lead_time_days: e.target.value })
                      }
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      min="0"
                      value={editForm.safety_stock_days}
                      onChange={(e) =>
                        setEditForm({ ...editForm, safety_stock_days: e.target.value })
                      }
                    />
                  </td>
                  <td>{sku.is_active ? "Yes" : "No"}</td>
                  <td>{reportStatus(sku)}</td>
                  <td className="pm-actions">
                    <button onClick={() => saveEdit(sku)} disabled={busy}>
                      Save
                    </button>
                    <button onClick={() => setEditingId(null)} disabled={busy}>
                      Cancel
                    </button>
                  </td>
                </tr>
              ) : (
                <tr key={sku.id}>
                  <td>{sku.id}</td>
                  <td>
                    <strong>{sku.product_name}</strong>
                    <small>SKU: {sku.sku_code}</small>
                  </td>
                  <td>{sku.lead_time_days} days</td>
                  <td>{sku.safety_stock_days} days</td>
                  <td>{sku.is_active ? "Yes" : "No"}</td>
                  <td>{reportStatus(sku)}</td>
                  <td className="pm-actions">
                    <button onClick={() => startEdit(sku)} disabled={busy}>
                      Edit
                    </button>
                    <button onClick={() => toggleActive(sku)} disabled={busy}>
                      {sku.is_active ? "Deactivate" : "Activate"}
                    </button>
                    <button
                      className="pm-danger"
                      onClick={() => deleteProduct(sku)}
                      disabled={busy}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default ProductManager;
