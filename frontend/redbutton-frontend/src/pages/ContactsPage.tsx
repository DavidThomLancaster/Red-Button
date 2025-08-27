import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { searchMyContactsApi, type ContactOut } from "../api/contactsSearch";
import { AddContactDialog } from "../components/AddContactDialog";

function useDebounced<T>(value: T, ms = 300) {
  const [v, setV] = useState(value);
  useEffect(() => { const t = setTimeout(() => setV(value), ms); return () => clearTimeout(t); }, [value, ms]);
  return v;
}

export const ContactsPage: React.FC = () => {
  const { token } = useAuth();
  const [trade, setTrade] = useState("");
  const [name, setName] = useState("");
  const [serviceArea, setServiceArea] = useState("");
  const [limit, setLimit] = useState(25);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<ContactOut[]>([]);
  const [count, setCount] = useState(0);

  const [adding, setAdding] = useState(false);

  const dName = useDebounced(name, 250);
  const dTrade = useDebounced(trade, 250);
  const dArea = useDebounced(serviceArea, 250);

  async function load() {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const resp = await searchMyContactsApi(token, {
        trade: dTrade || null,
        name: dName || null,
        service_area: dArea || null,
        limit, page
      });
      setItems(Array.isArray(resp.items) ? resp.items : []);
      setCount(typeof resp.count === "number" ? resp.count : resp.items.length);
    } catch (e: any) {
      setItems([]);
      setCount(0);
      setError(e?.message || "Failed to load contacts");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [token, dTrade, dName, dArea, limit, page]);

  const canPrev = page > 1;
  const canNext = items.length >= limit; // naive pager; switch to total when available

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <h2 style={{ margin: 0 }}>Contacts</h2>
        <button onClick={() => setAdding(true)}>+ New Contact</button>
      </div>

      {/* Filters */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: 12, marginBottom: 12 }}>
        <label style={{ display: "grid", gap: 4 }}>
          <span>Trade</span>
          <input value={trade} onChange={e => { setTrade(e.target.value); setPage(1); }} placeholder="plumbing" />
        </label>
        <label style={{ display: "grid", gap: 4 }}>
          <span>Name contains</span>
          <input value={name} onChange={e => { setName(e.target.value); setPage(1); }} placeholder="Company" />
        </label>
        <label style={{ display: "grid", gap: 4 }}>
          <span>Service area</span>
          <input value={serviceArea} onChange={e => { setServiceArea(e.target.value); setPage(1); }} placeholder="84601" />
        </label>
        <label style={{ display: "grid", gap: 4 }}>
          <span>Limit</span>
          <input type="number" min={1} max={200} value={limit}
                 onChange={e => { setLimit(Math.max(1, Math.min(200, Number(e.target.value) || 25))); setPage(1); }}
                 style={{ width: 90 }} />
        </label>
      </div>

      {/* Results */}
      <div style={{ border: "1px solid #eee", borderRadius: 8, overflow: "hidden" }}>
        <div style={{ maxHeight: 520, overflow: "auto" }}>
          {loading ? (
            <div style={{ padding: 16 }}>Loading…</div>
          ) : error ? (
            <div style={{ padding: 16, color: "crimson" }}>{error}</div>
          ) : items.length === 0 ? (
            <div style={{ padding: 16 }}>No contacts found.</div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", borderBottom: "1px solid #eee" }}>
                  <th style={{ padding: 8 }}>Name</th>
                  <th style={{ padding: 8 }}>Email</th>
                  <th style={{ padding: 8 }}>Phone</th>
                  <th style={{ padding: 8 }}>Service Area</th>
                </tr>
              </thead>
              <tbody>
                {items.map(row => (
                  <tr key={row.id} style={{ borderBottom: "1px solid #f5f5f5" }}>
                    <td style={{ padding: 8 }}>{row.name ?? row.email ?? row.id}</td>
                    <td style={{ padding: 8 }}>{row.email ?? "—"}</td>
                    <td style={{ padding: 8 }}>{row.phone ?? "—"}</td>
                    <td style={{ padding: 8 }}>{row.service_area ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer / pager */}
        <div style={{ padding: 12, display: "flex", justifyContent: "space-between" }}>
          <div>Showing {items.length} result{items.length === 1 ? "" : "s"}.</div>
          <div style={{ display: "flex", gap: 8 }}>
            <button disabled={!canPrev} onClick={() => setPage(p => Math.max(1, p - 1))}>‹ Prev</button>
            <button disabled={!canNext} onClick={() => setPage(p => p + 1)}>Next ›</button>
          </div>
        </div>
      </div>

      {/* Add contact modal */}
      <AddContactDialog
        open={adding}
        onClose={() => setAdding(false)}
        onCreated={load}
      />
    </div>
  );
};
