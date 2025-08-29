import React, { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { getEmailBatchesApi } from "../api/emails"; // or "../api/emails"
import type { JobEmailBatchesDTO, BatchWithHeadersDTO, EmailHeaderDTO } from "../types";

export const EmailPanel: React.FC<{ jobId: string; refreshKey?: number }> = ({ jobId, refreshKey = 0 }) => {
  const { token, logout } = useAuth();
  const [data, setData] = useState<JobEmailBatchesDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<Record<string, boolean>>({}); // batchId -> expanded?

  useEffect(() => {
    let mounted = true;
    (async () => {
      if (!token) return;
      setLoading(true);
      setErr(null);
      try {
        const res = await getEmailBatchesApi(token, jobId);
        if (!mounted) return;
        setData(res);
        // default: expand the newest batch only
        const latest = res.batches[0]?.batch?.id;
        setOpen(latest ? { [latest]: true } : {});
      } catch (e: any) {
        if (e?.status === 401) logout();
        else setErr(e?.message || "Failed to load email batches");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [token, logout, jobId, refreshKey]);

  if (loading) return <p>Loading email batches…</p>;
  if (err) return <p style={{ color: "crimson" }}>{err}</p>;
  if (!data || data.batches.length === 0) return <p>No email batches yet.</p>;

  return (
    <div className="email-panel" style={{ display: "grid", gap: 12 }}>
      {data.batches.map((bw) => (
        <BatchCard
          key={bw.batch.id}
          bw={bw}
          open={!!open[bw.batch.id]}
          onToggle={() => setOpen((prev) => ({ ...prev, [bw.batch.id]: !prev[bw.batch.id] }))}
        />
      ))}
    </div>
  );
};

const BatchCard: React.FC<{
  bw: BatchWithHeadersDTO;
  open: boolean;
  onToggle: () => void;
}> = ({ bw, open, onToggle }) => {
  const b = bw.batch;
  const created = new Date(b.created_at).toLocaleString();
  const count = b.count_total ?? bw.emails.length;

  return (
    <div style={{ border: "1px solid #e6e6e6", borderRadius: 8, background: "#fff" }}>
      <button
        onClick={onToggle}
        style={{
          width: "100%", textAlign: "left", padding: 12, border: "none",
          background: "transparent", cursor: "pointer", display: "flex", justifyContent: "space-between"
        }}
      >
        <span>
          <strong>Batch #{b.id.slice(0, 8)}</strong> &middot; {count} emails &middot; created {created} &middot; tmpl {b.template_version}
        </span>
        <span>{open ? "▾" : "▸"}</span>
      </button>

      {open && (
        <div style={{ borderTop: "1px solid #eee", padding: 12 }}>
          <EmailTable emails={bw.emails} />
        </div>
      )}
    </div>
  );
};

const EmailTable: React.FC<{ emails: EmailHeaderDTO[] }> = ({ emails }) => {
  if (emails.length === 0) return <p style={{ margin: 0, color: "#666" }}>No emails in this batch.</p>;

  return (
    <div style={{ overflowX: "auto" }}>
      <table cellPadding={8} style={{ borderCollapse: "collapse", minWidth: 900 }}>
        <thead>
          <tr>
            <Th>Contact</Th>
            <Th>Email</Th>
            <Th>Trade</Th>
            <Th>Subject</Th>
            <Th>Status</Th>
            <Th>Last Updated</Th>
          </tr>
        </thead>
        <tbody>
          {emails.map((e) => (
            <tr key={e.id}>
              <Td>{e.contact_name || "—"}</Td>
              <Td>{e.contact_email}</Td>
              <Td>{e.trade ?? "—"}</Td>
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

const baseTh: React.CSSProperties = { borderBottom: "1px solid #ddd", textAlign: "left" };
const baseTd: React.CSSProperties = { borderBottom: "1px solid #f0f0f0" };
const Th: React.FC<React.ThHTMLAttributes<HTMLTableHeaderCellElement>> = ({ style, children, ...rest }) => (
  <th style={{ ...baseTh, ...style }} {...rest}>{children}</th>
);
const Td: React.FC<React.TdHTMLAttributes<HTMLTableDataCellElement>> = ({ style, children, ...rest }) => (
  <td style={{ ...baseTd, ...style }} {...rest}>{children}</td>
);
function truncate(s: string, n: number) { return s.length > n ? s.slice(0, n - 1) + "…" : s; }
