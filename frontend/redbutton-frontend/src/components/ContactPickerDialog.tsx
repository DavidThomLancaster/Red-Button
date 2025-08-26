import React, { useEffect, useMemo, useState } from "react";
import { searchContactsApi, type ContactOut, type ContactSearchReq, type ContactSearchResp } from "../api/contactsSearch";

function useDebounced<T>(value: T, ms = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

type Props = {
  open: boolean;
  onClose: () => void;
  token: string;
  jobId: string;
  initialTrade?: string | null;
  initialServiceArea?: string | null;
  excludeIds?: string[];             // disable ones already in the block
  onAdd: (ids: string[]) => Promise<void> | void;  // called with selected IDs
};

export const ContactPickerDialog: React.FC<Props> = ({
  open, onClose, token, jobId, initialTrade, initialServiceArea, excludeIds = [], onAdd
}) => {
  const [trade, setTrade] = useState<string | "">((initialTrade ?? "") as string);
  const [name, setName] = useState("");
  const [serviceArea, setServiceArea] = useState<string | "">((initialServiceArea ?? "") as string);
  const [limit, setLimit] = useState(10);
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ContactOut[]>([]);
  const [count, setCount] = useState(0);

  const [selected, setSelected] = useState<Set<string>>(new Set());

  const debouncedName = useDebounced(name, 300);

  const exclude = useMemo(() => new Set(excludeIds), [excludeIds]);

  useEffect(() => {
    if (!open) return;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const body: ContactSearchReq = {
          trade: trade || null,
          name: debouncedName || null,
          service_area: serviceArea || null,
          limit, page
        };
        const resp: ContactSearchResp = await searchContactsApi(token, jobId, body);
        setResults(resp.items);
        setCount(resp.count);
      } catch (e: any) {
        setError(e?.message || "Failed to search contacts");
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, token, jobId, trade, debouncedName, serviceArea, limit, page]);

  useEffect(() => {
    if (open) {
      // reset selection when dialog opens
      setSelected(new Set());
      setPage(1);
    }
  }, [open]);

  if (!open) return null;

  const toggle = (id: string) => {
    setSelected(prev => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id); else n.add(id);
      return n;
    });
  };

  const alreadyAdded = (id: string) => exclude.has(id);

  const canPrev = page > 1;
  const canNext = count >= limit; // naive: if page returned 'limit' items, allow next

  const handleConfirm = async () => {
    const ids = [...selected].filter(id => !alreadyAdded(id));
    if (ids.length === 0) { onClose(); return; }
    await Promise.resolve(onAdd(ids));
    onClose();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)",
        display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50
      }}
      onClick={onClose}
    >
      <div
        style={{ background: "#fff", width: 720, maxWidth: "95vw", borderRadius: 12, boxShadow: "0 10px 30px rgba(0,0,0,0.2)" }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ padding: 16, borderBottom: "1px solid #eee", display: "flex", justifyContent: "space-between" }}>
          <strong>Select contacts to add</strong>
          <button onClick={onClose} aria-label="Close">✕</button>
        </div>

        {/* Filters */}
        <div style={{ padding: 16, display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: 12, alignItems: "end" }}>
          <label style={{ display: "grid", gap: 4 }}>
            <span>Trade</span>
            <input value={trade} onChange={e => setTrade(e.target.value)} placeholder="plumbing" />
          </label>
          <label style={{ display: "grid", gap: 4 }}>
            <span>Name contains</span>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="Company" />
          </label>
          <label style={{ display: "grid", gap: 4 }}>
            <span>Service area</span>
            <input value={serviceArea} onChange={e => setServiceArea(e.target.value)} placeholder="84601" />
          </label>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <label>Limit <input type="number" min={1} max={200} value={limit} onChange={e => setLimit(+e.target.value || 10)} style={{ width: 70 }} /></label>
          </div>
        </div>

        {/* Results */}
        <div style={{ padding: 16, minHeight: 220 }}>
          {loading ? (
            <div>Searching…</div>
          ) : error ? (
            <div style={{ color: "crimson" }}>{error}</div>
          ) : results.length === 0 ? (
            <div>No contacts found.</div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", borderBottom: "1px solid #eee" }}>
                  <th style={{ padding: 8 }} />
                  <th style={{ padding: 8 }}>Name</th>
                  <th style={{ padding: 8 }}>Email</th>
                  <th style={{ padding: 8 }}>Phone</th>
                  <th style={{ padding: 8 }}>Service Area</th>
                  <th style={{ padding: 8 }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {results.map(r => {
                  const disabled = alreadyAdded(r.id);
                  const checked = selected.has(r.id);
                  return (
                    <tr key={r.id} style={{ borderBottom: "1px solid #f5f5f5" }}>
                      <td style={{ padding: 8 }}>
                        <input
                          type="checkbox"
                          checked={checked}
                          disabled={disabled}
                          onChange={() => toggle(r.id)}
                        />
                      </td>
                      <td style={{ padding: 8 }}>{r.name ?? r.email ?? r.id}</td>
                      <td style={{ padding: 8 }}>{r.email ?? "—"}</td>
                      <td style={{ padding: 8 }}>{r.phone ?? "—"}</td>
                      <td style={{ padding: 8 }}>{r.service_area ?? "—"}</td>
                      <td style={{ padding: 8, opacity: 0.7 }}>{disabled ? "Already in block" : ""}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: 16, display: "flex", justifyContent: "space-between", borderTop: "1px solid #eee" }}>
          <div style={{ display: "flex", gap: 8 }}>
            <button disabled={!canPrev} onClick={() => setPage(p => Math.max(1, p - 1))}>‹ Prev</button>
            <button disabled={!canNext} onClick={() => setPage(p => p + 1)}>Next ›</button>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={onClose}>Cancel</button>
            <button onClick={handleConfirm}>Add selected ({[...selected].filter(id => !exclude.has(id)).length})</button>
          </div>
        </div>
      </div>
    </div>
  );
};
