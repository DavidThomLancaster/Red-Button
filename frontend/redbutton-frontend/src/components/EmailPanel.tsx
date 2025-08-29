import React, { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import {
  getEmailBatchesApi,
  getEmailDetailsApi,
  patchEmailApi,
  deleteEmailApi,
  deleteEmailBatchApi,
} from "../api/emails";
import type { JobEmailBatchesDTO, BatchWithHeadersDTO, EmailHeaderDTO, EmailDetailsDTO } from "../types";

export const EmailPanel: React.FC<{ jobId: string; refreshKey?: number }> = ({ jobId, refreshKey = 0 }) => {
  const { token, logout } = useAuth();
  const [data, setData] = useState<JobEmailBatchesDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [selected, setSelected] = useState<{ emailId: string; batchId: string } | null>(null);
  const [details, setDetails] = useState<EmailDetailsDTO | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function load() {
    if (!token) return;
    setLoading(true);
    setErr(null);
    try {
      const res = await getEmailBatchesApi(token, jobId);
      setData(res);
      const latest = res.batches[0]?.batch?.id;
      setOpen(latest ? { [latest]: true } : {});
    } catch (e: any) {
      if (e?.status === 401) {
        setErr("Unauthorized for email batches"); // avoid logout loop while wiring
      } else {
        setErr(e?.message || "Failed to load email batches");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [token, jobId, refreshKey]);

  async function onRowClick(bw: BatchWithHeadersDTO, h: EmailHeaderDTO) {
    if (!token) return;
    setSelected({ emailId: h.id, batchId: bw.batch.id });
    try {
      const det = await getEmailDetailsApi(token, jobId, h.id);
      setDetails(det);
    } catch (e: any) {
      setDetails(null);
      setErr(e?.message || "Failed to load email details");
    }
  }

  async function onSave(updated: Partial<EmailDetailsDTO>) {
    if (!token || !selected || !details) return;
    setSaving(true);
    try {
      const det = await patchEmailApi(token, jobId, selected.emailId, {
        subject: updated.subject ?? details.subject,
        body: updated.body ?? details.body,
        to_email: updated.to_email ?? details.to_email,
        status: updated.status ?? details.status,
      });

      setDetails(det);

      // reflect subject/to_email in list
      setData(prev => {
        if (!prev) return prev;
        const copy = structuredClone(prev) as JobEmailBatchesDTO;
        for (const bw of copy.batches) {
          if (bw.batch.id !== selected.batchId) continue;
          const idx = bw.emails.findIndex(e => e.id === selected.emailId);
          if (idx >= 0) {
            bw.emails[idx].subject = det.subject;
            bw.emails[idx].contact_email = det.to_email;
            bw.emails[idx].status = (det.status as any) ?? bw.emails[idx].status;
            bw.emails[idx].last_updated = new Date().toISOString();
          }
        }
        return copy;
      });
    } catch (e: any) {
      alert(e?.body || e?.message || "Update failed");
    } finally {
      setSaving(false);
    }
  }

  async function onDeleteEmail() {
    if (!token || !selected) return;
    if (!confirm("Delete this email? This cannot be undone.")) return;
    setDeleting(true);
    try {
      await deleteEmailApi(token, jobId, selected.emailId);
      // remove from local list
      setData(prev => {
        if (!prev) return prev;
        const copy = structuredClone(prev) as JobEmailBatchesDTO;
        for (const bw of copy.batches) {
          if (bw.batch.id !== selected.batchId) continue;
          bw.emails = bw.emails.filter(e => e.id !== selected.emailId);
          bw.batch.count_total = (bw.batch.count_total ?? bw.emails.length) - 1;
        }
        return copy;
      });
      setSelected(null);
      setDetails(null);
    } catch (e: any) {
      alert(e?.body || e?.message || "Delete failed");
    } finally {
      setDeleting(false);
    }
  }

  async function onDeleteBatch(batchId: string) {
    if (!token) return;
    if (!confirm("Delete this entire batch and all its emails? This cannot be undone.")) return;
    try {
      await deleteEmailBatchApi(token, jobId, batchId);
      setData(prev => (prev ? { ...prev, batches: prev.batches.filter(bw => bw.batch.id !== batchId) } : prev));
    } catch (e: any) {
      alert(e?.body || e?.message || "Batch delete failed");
    }
  }

  if (loading) return <p>Loading email batches…</p>;
  if (err) return <p style={{ color: "crimson" }}>{err}</p>;
  if (!data || data.batches.length === 0) return <p>No email batches yet.</p>;

  return (
    <div style={{ display: "grid", gap: 12 }}>
      {data.batches.map((bw) => (
        <div key={bw.batch.id} style={{ border: "1px solid #e6e6e6", borderRadius: 8, background: "#fff" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: 12 }}>
            <div>
              <strong>Batch #{bw.batch.id.slice(0, 8)}</strong> &middot; {bw.emails.length} emails &middot; created{" "}
              {new Date(bw.batch.created_at).toLocaleString()} &middot; tmpl {bw.batch.template_version}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={() => setOpen(o => ({ ...o, [bw.batch.id]: !o[bw.batch.id] }))}>
                {open[bw.batch.id] ? "Collapse" : "Expand"}
              </button>
              <button onClick={() => onDeleteBatch(bw.batch.id)} style={{ color: "crimson" }}>Delete batch</button>
            </div>
          </div>

          {open[bw.batch.id] && (
            <div style={{ borderTop: "1px solid #eee", padding: 12 }}>
              <EmailTable emails={bw.emails} onClickRow={(h) => onRowClick(bw, h)} />
            </div>
          )}
        </div>
      ))}

      {/* modal */}
      <EmailDetailsModal
        open={!!selected}
        details={details}
        onClose={() => { setSelected(null); setDetails(null); }}
        onSave={onSave}
        onDelete={onDeleteEmail}
        saving={saving}
        deleting={deleting}
      />
    </div>
  );
};

const EmailTable: React.FC<{ emails: EmailHeaderDTO[]; onClickRow: (e: EmailHeaderDTO) => void }> = ({ emails, onClickRow }) => {
  if (emails.length === 0) return <p style={{ margin: 0, color: "#666" }}>No emails in this batch.</p>;
  return (
    <div style={{ overflowX: "auto" }}>
      <table cellPadding={8} style={{ borderCollapse: "collapse", minWidth: 900 }}>
        <thead>
          <tr>
            <Th>Contact</Th>
            <Th>Email</Th>
            <Th>Subject</Th>
            <Th>Status</Th>
            <Th>Updated</Th>
          </tr>
        </thead>
        <tbody>
          {emails.map((e) => (
            <tr key={e.id} onClick={() => onClickRow(e)} style={{ cursor: "pointer" }}>
              <Td>{e.contact_name || "—"}</Td>
              <Td>{e.contact_email}</Td>
              <Td title={e.subject}>{truncate(e.subject, 80)}</Td>
              <Td>{e.status}</Td>
              <Td>{new Date(e.last_updated).toLocaleString()}</Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ---------- modal ----------
const EmailDetailsModal: React.FC<{
  open: boolean;
  details: EmailDetailsDTO | null;
  onClose: () => void;
  onSave: (patch: Partial<EmailDetailsDTO>) => void;
  onDelete: () => void;
  saving: boolean;
  deleting: boolean;
}> = ({ open, details, onClose, onSave, onDelete, saving, deleting }) => {
  const [form, setForm] = useState<{ to_email: string; subject: string; body: string; status: string }>({
    to_email: "", subject: "", body: "", status: "draft",
  });

  useEffect(() => {
    if (details) {
      setForm({
        to_email: details.to_email ?? "",
        subject: details.subject ?? "",
        body: details.body ?? "",
        status: (details.status as string) ?? "draft",
      });
    }
  }, [details]);

  if (!open) return null;

  return (
    <div style={overlay}>
      <div style={modal}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: 0 }}>Email Details</h3>
          <button onClick={onClose}>✕</button>
        </div>

        {!details ? (
          <p style={{ marginTop: 12 }}>Loading…</p>
        ) : (
          <>
            <div style={{ fontSize: 12, color: "#666", marginTop: 8 }}>
              ID: {details.id} &middot; Batch: {details.batch_id}
            </div>

            <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
              <label>
                To
                <input
                  style={input}
                  value={form.to_email}
                  onChange={(e) => setForm(f => ({ ...f, to_email: e.target.value }))}
                />
              </label>
              <label>
                Subject
                <input
                  style={input}
                  value={form.subject}
                  onChange={(e) => setForm(f => ({ ...f, subject: e.target.value }))}
                />
              </label>
              <label>
                Body
                <textarea
                  style={{ ...input, minHeight: 140 }}
                  value={form.body}
                  onChange={(e) => setForm(f => ({ ...f, body: e.target.value }))}
                />
              </label>
              <label>
                Status
                <select
                  style={input}
                  value={form.status}
                  onChange={(e) => setForm(f => ({ ...f, status: e.target.value }))}
                >
                  <option value="draft">draft</option>
                  <option value="ready">ready</option>
                </select>
              </label>

              <div style={{ fontSize: 12, color: "#666" }}>
                Attempts: {details.attempts} &nbsp;|&nbsp; Sent at: {details.sent_at ? new Date(details.sent_at).toLocaleString() : "—"}
                {details.last_error && <div style={{ color: "crimson" }}>Last error: {details.last_error}</div>}
              </div>
            </div>

            <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
              <button onClick={() => onSave(form)} disabled={saving}>
                {saving ? "Saving…" : "Save"}
              </button>
              <button onClick={onDelete} disabled={deleting} style={{ color: "crimson" }}>
                {deleting ? "Deleting…" : "Delete email"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

// ---------- little UI bits ----------
const baseTh: React.CSSProperties = { borderBottom: "1px solid #ddd", textAlign: "left" };
const baseTd: React.CSSProperties = { borderBottom: "1px solid #f0f0f0" };
const Th: React.FC<React.ThHTMLAttributes<HTMLTableHeaderCellElement>> = ({ style, children, ...rest }) => (
  <th style={{ ...baseTh, ...style }} {...rest}>{children}</th>
);
const Td: React.FC<React.TdHTMLAttributes<HTMLTableDataCellElement>> = ({ style, children, ...rest }) => (
  <td style={{ ...baseTd, ...style }} {...rest}>{children}</td>
);
const input: React.CSSProperties = { width: "100%", padding: 8, border: "1px solid #ddd", borderRadius: 6 };
const overlay: React.CSSProperties = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 9999
};
const modal: React.CSSProperties = { width: 700, maxWidth: "95vw", background: "#fff", borderRadius: 10, padding: 16, boxShadow: "0 10px 30px rgba(0,0,0,.2)" };
function truncate(s: string, n: number) { return s.length > n ? s.slice(0, n - 1) + "…" : s; }


// import React, { useEffect, useState } from "react";
// import { useAuth } from "../auth/AuthContext";
// import { getEmailBatchesApi } from "../api/emails"; // or "../api/emails"
// import type { JobEmailBatchesDTO, BatchWithHeadersDTO, EmailHeaderDTO } from "../types";

// export const EmailPanel: React.FC<{ jobId: string; refreshKey?: number }> = ({ jobId, refreshKey = 0 }) => {
//   const { token, logout } = useAuth();
//   const [data, setData] = useState<JobEmailBatchesDTO | null>(null);
//   const [loading, setLoading] = useState(true);
//   const [err, setErr] = useState<string | null>(null);
//   const [open, setOpen] = useState<Record<string, boolean>>({}); // batchId -> expanded?

//   useEffect(() => {
//     let mounted = true;
//     (async () => {
//       if (!token) return;
//       setLoading(true);
//       setErr(null);
//       try {
//         const res = await getEmailBatchesApi(token, jobId);
//         if (!mounted) return;
//         setData(res);
//         // default: expand the newest batch only
//         const latest = res.batches[0]?.batch?.id;
//         setOpen(latest ? { [latest]: true } : {});
//       } catch (e: any) {
//         if (e?.status === 401) logout();
//         else setErr(e?.message || "Failed to load email batches");
//       } finally {
//         if (mounted) setLoading(false);
//       }
//     })();
//     return () => { mounted = false; };
//   }, [token, logout, jobId, refreshKey]);

//   if (loading) return <p>Loading email batches…</p>;
//   if (err) return <p style={{ color: "crimson" }}>{err}</p>;
//   if (!data || data.batches.length === 0) return <p>No email batches yet.</p>;

//   return (
//     <div className="email-panel" style={{ display: "grid", gap: 12 }}>
//       {data.batches.map((bw) => (
//         <BatchCard
//           key={bw.batch.id}
//           bw={bw}
//           open={!!open[bw.batch.id]}
//           onToggle={() => setOpen((prev) => ({ ...prev, [bw.batch.id]: !prev[bw.batch.id] }))}
//         />
//       ))}
//     </div>
//   );
// };

// const BatchCard: React.FC<{
//   bw: BatchWithHeadersDTO;
//   open: boolean;
//   onToggle: () => void;
// }> = ({ bw, open, onToggle }) => {
//   const b = bw.batch;
//   const created = new Date(b.created_at).toLocaleString();
//   const count = b.count_total ?? bw.emails.length;

//   return (
//     <div style={{ border: "1px solid #e6e6e6", borderRadius: 8, background: "#fff" }}>
//       <button
//         onClick={onToggle}
//         style={{
//           width: "100%", textAlign: "left", padding: 12, border: "none",
//           background: "transparent", cursor: "pointer", display: "flex", justifyContent: "space-between"
//         }}
//       >
//         <span>
//           <strong>Batch #{b.id.slice(0, 8)}</strong> &middot; {count} emails &middot; created {created} &middot; tmpl {b.template_version}
//         </span>
//         <span>{open ? "▾" : "▸"}</span>
//       </button>

//       {open && (
//         <div style={{ borderTop: "1px solid #eee", padding: 12 }}>
//           <EmailTable emails={bw.emails} />
//         </div>
//       )}
//     </div>
//   );
// };

// const EmailTable: React.FC<{ emails: EmailHeaderDTO[] }> = ({ emails }) => {
//   if (emails.length === 0) return <p style={{ margin: 0, color: "#666" }}>No emails in this batch.</p>;

//   return (
//     <div style={{ overflowX: "auto" }}>
//       <table cellPadding={8} style={{ borderCollapse: "collapse", minWidth: 900 }}>
//         <thead>
//           <tr>
//             <Th>Contact</Th>
//             <Th>Email</Th>
//             <Th>Trade</Th>
//             <Th>Subject</Th>
//             <Th>Status</Th>
//             <Th>Last Updated</Th>
//           </tr>
//         </thead>
//         <tbody>
//           {emails.map((e) => (
//             <tr key={e.id}>
//               <Td>{e.contact_name || "—"}</Td>
//               <Td>{e.contact_email}</Td>
//               <Td>{e.trade ?? "—"}</Td>
//               <Td title={e.subject}>{truncate(e.subject, 80)}</Td>
//               <Td>{e.status}</Td>
//               <Td>{new Date(e.last_updated).toLocaleString()}</Td>
//             </tr>
//           ))}
//         </tbody>
//       </table>
//     </div>
//   );
// };

// const baseTh: React.CSSProperties = { borderBottom: "1px solid #ddd", textAlign: "left" };
// const baseTd: React.CSSProperties = { borderBottom: "1px solid #f0f0f0" };
// const Th: React.FC<React.ThHTMLAttributes<HTMLTableHeaderCellElement>> = ({ style, children, ...rest }) => (
//   <th style={{ ...baseTh, ...style }} {...rest}>{children}</th>
// );
// const Td: React.FC<React.TdHTMLAttributes<HTMLTableDataCellElement>> = ({ style, children, ...rest }) => (
//   <td style={{ ...baseTd, ...style }} {...rest}>{children}</td>
// );
// function truncate(s: string, n: number) { return s.length > n ? s.slice(0, n - 1) + "…" : s; }
