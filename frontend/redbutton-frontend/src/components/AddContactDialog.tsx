import React, { useEffect, useState } from "react";
import { createMyContactApi } from "../api/contactsSearch";
import { useAuth } from "../auth/AuthContext";

type Props = {
  open: boolean;
  onClose: () => void;
  onCreated: () => void; // refresh list after success
};

export const AddContactDialog: React.FC<Props> = ({ open, onClose, onCreated }) => {
  const { token } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [serviceArea, setServiceArea] = useState("");
  const [tradesText, setTradesText] = useState(""); // comma-separated
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setName(""); setEmail(""); setPhone(""); setServiceArea(""); setTradesText("");
      setErr(null);
    }
  }, [open]);

  if (!open) return null;

  const trades = tradesText
    .split(",")
    .map(t => t.trim())
    .filter(Boolean);

  async function submit() {
    if (!token) return;
    if (!name.trim()) { setErr("Name is required"); return; }
    setBusy(true);
    setErr(null);
    try {
      await createMyContactApi(token, {
        name: name.trim(),
        email: email.trim() || null,
        phone: phone.trim() || null,
        service_area: serviceArea.trim() || null,
        trades,
      } as any); // service_area snake case only if your backend expects it; otherwise rename
      onCreated();
      onClose();
    } catch (e: any) {
      setErr(e?.message || "Failed to create contact");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div role="dialog" aria-modal="true"
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)",
               display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 }}
      onClick={onClose}
    >
      <div onClick={e => e.stopPropagation()}
           style={{ background: "#fff", width: 560, maxWidth: "95vw",
                    borderRadius: 12, boxShadow: "0 10px 30px rgba(0,0,0,0.2)" }}>
        <div style={{ padding: 16, borderBottom: "1px solid #eee",
                      display: "flex", justifyContent: "space-between" }}>
          <strong>Add personal contact</strong>
          <button onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div style={{ padding: 16, display: "grid", gap: 12 }}>
          {err && <div style={{ color: "crimson" }}>{err}</div>}

          <label style={{ display: "grid", gap: 4 }}>
            <span>Name *</span>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="Company or Person" />
          </label>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <label style={{ display: "grid", gap: 4 }}>
              <span>Email</span>
              <input value={email} onChange={e => setEmail(e.target.value)} placeholder="name@example.com" />
            </label>
            <label style={{ display: "grid", gap: 4 }}>
              <span>Phone</span>
              <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="555-123-4567" />
            </label>
          </div>

          <label style={{ display: "grid", gap: 4 }}>
            <span>Service area</span>
            <input value={serviceArea} onChange={e => setServiceArea(e.target.value)} placeholder="84601" />
          </label>

          <label style={{ display: "grid", gap: 4 }}>
            <span>Trades (comma separated)</span>
            <input value={tradesText} onChange={e => setTradesText(e.target.value)} placeholder="plumbing, electrical" />
          </label>
        </div>

        <div style={{ padding: 16, borderTop: "1px solid #eee", display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button onClick={onClose} disabled={busy}>Cancel</button>
          <button onClick={submit} disabled={busy}>{busy ? "Saving…" : "Save"}</button>
        </div>
      </div>
    </div>
  );
};
