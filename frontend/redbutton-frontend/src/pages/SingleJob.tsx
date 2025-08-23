import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { getJobAPI, submitPdfAPI, generateEmailsApi } from "../api/jobs";
import type { GetJobResponse } from "../types";

// 👇 import your panel (adjust the path if needed)
import { ContactMapPanel } from "../components/ContactMapPanel";

const SingleJob: React.FC = () => {
  const { jobId = "" } = useParams();
  const { token, logout } = useAuth();

  const [data, setData] = useState<GetJobResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  // keep the most recent POST /submit_pdf response here
  const [lastResponse, setLastResponse] = useState<any | null>(null);

  // 🔁 use this to force ContactMapPanel to refetch (by remounting it)
  const [mapRefreshKey, setMapRefreshKey] = useState(0);

  // Load job details
  useEffect(() => {
    let mounted = true;
    (async () => {
      if (!token) return;
      try {
        const res = await getJobAPI(token, jobId);
        if (mounted) setData(res);
      } catch (e: any) {
        if (e?.status === 401) logout();
        else setErr(e?.message || "Failed to load job");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [token, logout, jobId]);

  async function handleUpload() {
    if (!token || !file) return;
    setUploading(true);
    setErr(null);
    try {
      const res: any = await submitPdfAPI(token, jobId, file);
      setLastResponse(res);

      // Optional: reflect status quickly in the header
      setData(prev =>
        prev
          ? {
              ...prev,
              job: {
                ...prev.job,
                status: res.status ?? prev.job.status,
                pdf_ref: res.pdf_ref ?? prev.job.pdf_ref,
                images_ref: res.images_ref ?? prev.job.images_ref,
              },
            }
          : prev
      );

      // Refresh job details and contact map
      const refreshed = await getJobAPI(token, jobId);
      setData(refreshed);
      setMapRefreshKey(k => k + 1); // 👈 force ContactMapPanel to refetch

      setFile(null);
    } catch (e: any) {
      if (e?.status === 401) logout();
      else setErr(e?.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function generateEmails() {
    if (!token) return;
    try {
      const res: any = await generateEmailsApi(token, jobId);
      // TODO - I'll probably have to do more then just print the res later
      console.log(res)
    } catch (e: any) {
      if (e?.status === 401) logout();
      else setErr(e?.message || "Generate emails failed");
    }
  }

  if (loading) return <p style={{ padding: 16 }}>Loading…</p>;
  if (err) return <p style={{ padding: 16, color: "crimson" }}>{err}</p>;
  if (!data) return <p style={{ padding: 16 }}>Not found.</p>;

  const { job } = data;

  return (
    <div style={{ maxWidth: 1000, margin: "24px auto", padding: 16 }}>
      <Link to="/jobs">&larr; Back</Link>

      {/* Job Header */}
      <h2 style={{ marginTop: 8 }}>{job.name}</h2>
      <p><strong>Status:</strong> {job.status || "—"}</p>
      {job.notes && <p><strong>Notes:</strong> {job.notes}</p>}
      {job.created_at && (
        <p><strong>Created:</strong> {new Date(job.created_at).toLocaleString()}</p>
      )}

      {/* Upload */}
      <section style={{ marginTop: 24 }}>
        <h3>Upload PDF</h3>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            disabled={uploading}
          />
          <button onClick={handleUpload} disabled={!file || uploading}>
            {uploading ? "Uploading…" : "Submit PDF"}
          </button>
          {/* Manual refresh button (handy while iterating) */}
          <button onClick={() => setMapRefreshKey(k => k + 1)} disabled={uploading}>
            Refresh Contact Map
          </button>
          <button onClick={() => generateEmails()} disabled={uploading}>
            Generate Emails
          </button>

        </div>
      </section>

      {/* 👇 Contact Map Section */}
      <section style={{ marginTop: 24 }}>
        <h3>Contact Map</h3>
        <div style={{ border: "1px solid #e6e6e6", borderRadius: 8, padding: 12, background: "#fafafa" }}>
          <ContactMapPanel
            key={`cmp:${jobId}:${mapRefreshKey}`} // remount to refetch
            jobId={jobId}
            onNeedAddContact={(trade, blockIdx) => {
              // TODO: open your Contact Picker modal here
              console.log("Add contact requested for", trade, "block", blockIdx);
            }}
          />
        </div>
      </section>

      {/* (Keep your debugging sections below if you like) */}
      {/* ... */}
    </div>
  );
};

export default SingleJob;



//------------------------------------------------------------------------------------------------------------------------------
// import React, { useEffect, useState } from "react";
// import { useParams, Link } from "react-router-dom";
// import { useAuth } from "../auth/AuthContext";
// import { getJobAPI, submitPdfAPI } from "../api/jobs";
// import type { GetJobResponse } from "../types";

// const SingleJob: React.FC = () => {
//   const { jobId = "" } = useParams();
//   const { token, logout } = useAuth();

//   const [data, setData] = useState<GetJobResponse | null>(null);
//   const [err, setErr] = useState<string | null>(null);
//   const [loading, setLoading] = useState(true);

//   const [file, setFile] = useState<File | null>(null);
//   const [uploading, setUploading] = useState(false);

//   // keep the most recent POST /submit_pdf response here
//   const [lastResponse, setLastResponse] = useState<any | null>(null);

//   // best-effort parsed contacts_map from either lastResponse or GET data (if present)
//   const parsedFromLastResponse = useParsedContactsMap(lastResponse?.contacts_map ?? lastResponse?.contact_map);
//   const parsedFromGet = useParsedContactsMap((data as any)?.contacts_map ?? (data as any)?.contact_map);

//   // Load job details
//   useEffect(() => {
//     let mounted = true;
//     (async () => {
//       if (!token) return;
//       try {
//         const res = await getJobAPI(token, jobId);
//         if (mounted) setData(res);
//       } catch (e: any) {
//         if (e?.status === 401) logout();
//         else setErr(e?.message || "Failed to load job");
//       } finally {
//         if (mounted) setLoading(false);
//       }
//     })();
//     return () => {
//       mounted = false;
//     };
//   }, [token, logout, jobId]);

//   async function handleUpload() {
//     if (!token || !file) return;
//     setUploading(true);
//     setErr(null);
//     try {
//       const res: any = await submitPdfAPI(token, jobId, file);
//       console.log("POST /submit_pdf response:", res);
//       setLastResponse(res);

//       // Optional: reflect obvious fields immediately in the visible job header
//       setData((prev) =>
//         prev
//           ? {
//               ...prev,
//               job: {
//                 ...prev.job,
//                 status: res.status ?? prev.job.status,
//                 pdf_ref: res.pdf_ref ?? prev.job.pdf_ref,
//                 images_ref: res.images_ref ?? prev.job.images_ref,
//                 contact_map_ref:
//                   res.contact_map_ref ?? res.contacts_map_ref ?? (prev.job as any).contact_map_ref,
//               },
//             }
//           : prev
//       );

//       // Then refresh the persisted job state
//       const refreshed = await getJobAPI(token, jobId);
//       setData(refreshed);

//       setFile(null);
//     } catch (e: any) {
//       if (e?.status === 401) logout();
//       else setErr(e?.message || "Upload failed");
//     } finally {
//       setUploading(false);
//     }
//   }

//   if (loading) return <p style={{ padding: 16 }}>Loading…</p>;
//   if (err) return <p style={{ padding: 16, color: "crimson" }}>{err}</p>;
//   if (!data) return <p style={{ padding: 16 }}>Not found.</p>;

//   const { job } = data;

//   return (
//     <div style={{ maxWidth: 1000, margin: "24px auto", padding: 16 }}>
//       <Link to="/jobs">&larr; Back</Link>

//       {/* Job Header */}
//       <h2 style={{ marginTop: 8 }}>{job.name}</h2>
//       <p><strong>Status:</strong> {job.status || "—"}</p>
//       {job.notes && <p><strong>Notes:</strong> {job.notes}</p>}
//       {job.created_at && (
//         <p><strong>Created:</strong> {new Date(job.created_at).toLocaleString()}</p>
//       )}

//       {/* Upload */}
//       <section style={{ marginTop: 24 }}>
//         <h3>Upload PDF</h3>
//         <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
//           <input
//             type="file"
//             accept="application/pdf"
//             onChange={(e) => setFile(e.target.files?.[0] ?? null)}
//             disabled={uploading}
//           />
//           <button onClick={handleUpload} disabled={!file || uploading}>
//             {uploading ? "Uploading…" : "Submit PDF"}
//           </button>
//         </div>
//         {file && !uploading && (
//           <div style={{ fontSize: 12, color: "#666", marginTop: 6 }}>
//             Selected: {file.name}
//           </div>
//         )}
//       </section>

//       {/* Latest POST Response (raw) */}
//       <Section title="Latest POST /submit_pdf Response (raw)">
//         {lastResponse ? (
//           <JsonBlock obj={lastResponse} />
//         ) : (
//           <p style={{ margin: 0, color: "#666" }}>No upload this session.</p>
//         )}
//       </Section>

//       {/* Parsed contacts_map from POST */}
//       <Section title="Parsed contacts_map from POST (if provided)">
//         {parsedFromLastResponse.ok ? (
//           <JsonBlock obj={parsedFromLastResponse.value} />
//         ) : (
//           <p style={{ margin: 0, color: "#666" }}>
//             {parsedFromLastResponse.message ??
//               "No contacts_map present on last response or it was not valid JSON."}
//           </p>
//         )}
//       </Section>

//       {/* Current GET Job (raw) */}
//       <Section title="Current GET /jobs/{id} Result (raw)">
//         <JsonBlock obj={data} />
//       </Section>

//       {/* Parsed contacts_map from GET (if your GET includes it) */}
//       <Section title="Parsed contacts_map from GET (if provided)">
//         {parsedFromGet.ok ? (
//           <JsonBlock obj={parsedFromGet.value} />
//         ) : (
//           <p style={{ margin: 0, color: "#666" }}>
//             {parsedFromGet.message ??
//               "No contacts_map on GET response or it was not valid JSON."}
//           </p>
//         )}
//       </Section>
//     </div>
//   );
// };

// /* ---------- helpers ---------- */

// function Section({ title, children }: { title: string; children: React.ReactNode }) {
//   return (
//     <section style={{ marginTop: 24 }}>
//       <h3 style={{ marginBottom: 8 }}>{title}</h3>
//       <div
//         style={{
//           border: "1px solid #e6e6e6",
//           borderRadius: 8,
//           padding: 12,
//           background: "#fafafa",
//         }}
//       >
//         {children}
//       </div>
//     </section>
//   );
// }

// function JsonBlock({ obj }: { obj: any }) {
//   return (
//     <pre
//       style={{
//         margin: 0,
//         whiteSpace: "pre-wrap",
//         wordBreak: "break-word",
//         fontSize: 13,
//         lineHeight: 1.4,
//       }}
//     >
//       {safeStringify(obj, 2)}
//     </pre>
//   );
// }

// function safeStringify(value: any, space = 2): string {
//   try {
//     return JSON.stringify(value, null, space);
//   } catch {
//     // handle circular refs or weird objects
//     return String(value);
//   }
// }

// // Tries to parse contacts_map that might be a stringified JSON.
// // Accepts objects directly, returns a small status object for UI.
// function useParsedContactsMap(source: any): {
//   ok: boolean;
//   value?: any;
//   message?: string;
// } {
//   const [out, setOut] = useState<{ ok: boolean; value?: any; message?: string }>({
//     ok: false,
//     message: "No contacts_map found.",
//   });

//   useEffect(() => {
//     if (source == null) {
//       setOut({ ok: false, message: "No contacts_map found." });
//       return;
//     }
//     if (typeof source === "string") {
//       try {
//         const parsed = JSON.parse(source);
//         setOut({ ok: true, value: parsed });
//       } catch (e: any) {
//         setOut({ ok: false, message: "contacts_map present but not valid JSON string." });
//       }
//       return;
//     }
//     if (typeof source === "object") {
//       setOut({ ok: true, value: source });
//       return;
//     }
//     setOut({ ok: false, message: "contacts_map present but in an unexpected format." });
//   }, [source]);

//   return out;
// }

// export default SingleJob;

// ------------------------------------------------------------------------------------------------------
// src/pages/SingleJob.tsx
// import React, { useEffect, useState } from "react";
// import { useParams, Link } from "react-router-dom";
// import { useAuth } from "../auth/AuthContext";
// import { getJobAPI, submitPdfAPI } from "../api/jobs";
// import type { GetJobResponse, ContactMapPreview } from "../types";

// const SingleJob: React.FC = () => {
//   const { jobId = "" } = useParams();
//   const { token, logout } = useAuth();
//   const [data, setData] = useState<GetJobResponse | null>(null);
//   const [err, setErr] = useState<string | null>(null);
//   const [loading, setLoading] = useState(true);

//   const [file, setFile] = useState<File | null>(null);
//   const [uploading, setUploading] = useState(false);

//   useEffect(() => {
//     let mounted = true;
//     (async () => {
//       if (!token) return;
//       try {
//         const res = await getJobAPI(token, jobId);
//         if (mounted) setData(res);
//       } catch (e: any) {
//         if (e?.status === 401) logout();
//         else setErr(e?.message || "Failed to load job");
//       } finally {
//         if (mounted) setLoading(false);
//       }
//     })();
//     return () => { mounted = false; };
//   }, [token, logout, jobId]);

//   async function handleUpload() {
//     if (!token || !file) return;
//     setUploading(true);
//     setErr(null);
//     try {
//       const res: any = await submitPdfAPI(token, jobId, file);
//       // 1) Try to extract the FULL map from the POST response (supports several shapes)
//       console.log(res)
//       const fullMap = extractFullMap(res);
//       console.log(fullMap) 
//       if (fullMap) {
//         // 2) Convert to the table's expected shape and set immediately
//         const preview = toPreviewFromFull(fullMap);
//         setData(prev =>
//           prev
//             ? {
//                 job: {
//                   ...prev.job,
//                   status: res.status ?? prev.job.status,
//                   pdf_ref: res.pdf_ref ?? prev.job.pdf_ref,
//                   images_ref: res.images_ref ?? prev.job.images_ref,
//                   contact_map_ref: res.contact_map_ref ?? res.contacts_map_ref ?? prev.job.contact_map_ref,
//                 },
//                 contact_map_preview: preview,
//               }
//             : prev
//         );
//       }
//       // 3) Refresh from GET for consistency with what’s persisted
//       const refreshed = await getJobAPI(token, jobId);
//       setData(refreshed);
//       setFile(null);
//     } catch (e: any) {
//       if (e?.status === 401) logout();
//       else setErr(e?.message || "Upload failed");
//     } finally {
//       setUploading(false);
//     }
//   }

//   if (loading) return <p style={{ padding: 16 }}>Loading…</p>;
//   if (err) return <p style={{ padding: 16, color: "crimson" }}>{err}</p>;
//   if (!data) return <p style={{ padding: 16 }}>Not found.</p>;

//   const { job, contact_map_preview } = data;

//   return (
//     <div style={{ maxWidth: 900, margin: "24px auto", padding: 16 }}>
//       <Link to="/jobs">&larr; Back</Link>
//       <h2 style={{ marginTop: 8 }}>{job.name}</h2>
//       <p><strong>Status:</strong> {job.status || "—"}</p>
//       {job.notes && <p><strong>Notes:</strong> {job.notes}</p>}
//       {job.created_at && (
//         <p><strong>Created:</strong> {new Date(job.created_at).toLocaleString()}</p>
//       )}

//       {/* Upload */}
//       <section style={{ marginTop: 24 }}>
//         <h3>Upload PDF</h3>
//         <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
//           <input
//             type="file"
//             accept="application/pdf"
//             onChange={(e) => setFile(e.target.files?.[0] ?? null)}
//             disabled={uploading}
//           />
//           <button onClick={handleUpload} disabled={!file || uploading}>
//             {uploading ? "Uploading…" : "Submit PDF"}
//           </button>
//         </div>
//         {file && !uploading && (
//           <div style={{ fontSize: 12, color: "#666", marginTop: 6 }}>
//             Selected: {file.name}
//           </div>
//         )}
//       </section>

//       {/* Contact map */}
//       <h3 style={{ marginTop: 24 }}>Contact Map</h3>
//       {contact_map_preview ? (
//         <ContactMapPreviewTable preview={contact_map_preview} />
//       ) : (
//         <p>No contact map yet. Upload a PDF to generate one.</p>
//       )}
//     </div>
//   );
// };

// /** ---- Helpers to accept FULL map and render with existing preview table ---- */

// // Accepts various backend shapes and returns the full map object
// function extractFullMap(res: any): FullContactMap | null {
//   // Common shapes:
//   // 1) { contacts_map: {...} }  or  { contact_map: {...} }
//   // 2) Response IS the map itself (root is the object with "trades")
//   const candidate = res?.contacts_map ?? res?.contact_map ?? res;
//   if (candidate && Array.isArray(candidate.trades)) return candidate as FullContactMap;
//   return null;
// }

// // Convert full map → ContactMapPreview (no truncation; includes all trades)
// function toPreviewFromFull(full: FullContactMap): ContactMapPreview {
//   return {
//     generated_at: full.generated_at || new Date().toISOString(),
//     trades: full.trades.map((t) => ({
//       trade: t.trade,
//       pages: t.pages ?? [],
//       notes: t.notes,
//       suggested_contact_id: t.suggested_contact_id ?? null,
//       confidence: t.confidence,
//     })),
//   };
// }

// // Types local to this file so you don't have to touch your global types
// type FullContactMapTrade = {
//   trade: string;
//   pages?: number[];
//   notes?: string;
//   suggested_contact_id?: string | null;
//   confidence?: number;
//   // allow extra fields without TS complaining
//   [k: string]: any;
// };

// type FullContactMap = {
//   generated_at?: string;
//   trades: FullContactMapTrade[];
// };

// function ContactMapPreviewTable({ preview }: { preview: ContactMapPreview }) {
//   return (
//     <div>
//       <div style={{ fontSize: 12, color: "#666", marginBottom: 8 }}>
//         Generated: {new Date(preview.generated_at).toLocaleString()}
//       </div>
//       <div style={{ overflowX: "auto" }}>
//         <table cellPadding={8} style={{ borderCollapse: "collapse", minWidth: 700 }}>
//           <thead>
//             <tr>
//               <Th>Trade</Th>
//               <Th>Pages</Th>
//               <Th>Notes</Th>
//               <Th>Suggested Contact</Th>
//               <Th>Confidence</Th>
//             </tr>
//           </thead>
//           <tbody>
//             {preview.trades.map((t, i) => (
//               <tr key={i}>
//                 <Td>{t.trade}</Td>
//                 <Td>{t.pages?.join(", ")}</Td>
//                 <Td title={t.notes}>{truncate(t.notes ?? "", 90)}</Td>
//                 <Td>{t.suggested_contact_id ?? "—"}</Td>
//                 <Td>{t.confidence !== undefined ? Math.round(t.confidence * 100) + "%" : "—"}</Td>
//               </tr>
//             ))}
//           </tbody>
//         </table>
//       </div>
//     </div>
//   );
// }

// // Styled cells that pass native props
// const baseTh: React.CSSProperties = { borderBottom: "1px solid #ddd", textAlign: "left" };
// const baseTd: React.CSSProperties = { borderBottom: "1px solid #f0f0f0" };
// type ThProps = React.ThHTMLAttributes<HTMLTableHeaderCellElement>;
// type TdProps = React.TdHTMLAttributes<HTMLTableDataCellElement>;
// const Th: React.FC<ThProps> = ({ style, children, ...rest }) => (
//   <th style={{ ...baseTh, ...style }} {...rest}>{children}</th>
// );
// const Td: React.FC<TdProps> = ({ style, children, ...rest }) => (
//   <td style={{ ...baseTd, ...style }} {...rest}>{children}</td>
// );

// function truncate(s: string, n: number) {
//   return s.length > n ? s.slice(0, n - 1) + "…" : s;
// }

// export default SingleJob;

//----------------------------------------------------------------------------------------------------------

// // src/pages/SingleJob.tsx


// import React, { useEffect, useState } from "react";
// import { useParams, Link } from "react-router-dom";
// import { useAuth } from "../auth/AuthContext";
// import { getJobAPI, submitPdfAPI } from "../api/jobs";
// import type { GetJobResponse, ContactMapPreview } from "../types";

// const SingleJob: React.FC = () => {
//   const { jobId = "" } = useParams();
//   const { token, logout } = useAuth();
//   const [data, setData] = useState<GetJobResponse | null>(null);
//   const [err, setErr] = useState<string | null>(null);
//   const [loading, setLoading] = useState(true);

//   const [file, setFile] = useState<File | null>(null);
//   const [uploading, setUploading] = useState(false);

//   useEffect(() => {
//     let mounted = true;
//     (async () => {
//       if (!token) return;
//       try {
//         const res = await getJobAPI(token, jobId);
//         if (mounted) setData(res);
//       } catch (e: any) {
//         if (e?.status === 401) logout();
//         else setErr(e?.message || "Failed to load job");
//       } finally {
//         if (mounted) setLoading(false);
//       }
//     })();
//     return () => { mounted = false; };
//   }, [token, logout, jobId]);

//   async function handleUpload() {
//     if (!token || !file) return;
//     setUploading(true);
//     setErr(null);
//     try {
//         const res = await submitPdfAPI(token, jobId, file);

//         console.log(res)
//         // If the POST returns a preview, show it immediately:
//         setData(prev =>
//         prev
//             ? {
//                 job: {
//                 ...prev.job,
//                 status: res.status ?? prev.job.status,
//                 pdf_ref: res.pdf_ref ?? prev.job.pdf_ref,
//                 images_ref: res.images_ref ?? prev.job.images_ref,
//                 contact_map_ref: res.contact_map_ref ?? prev.job.contact_map_ref,
//                 },
//                 contact_map_preview:
//                 res.preliminary_contact_map ??
//                 res.contact_map_preview ??
//                 prev.contact_map_preview ??
//                 null,
//             }
//             : prev
//         );

//         // Then refresh from GET to keep everything consistent:
//         const refreshed = await getJobAPI(token, jobId);
//         setData(refreshed);
//         setFile(null);
//     } catch (e: any) {
//         if (e?.status === 401) logout();
//         else setErr(e?.message || "Upload failed");
//     } finally {
//         setUploading(false);
//     }
//     }

//   if (loading) return <p style={{ padding: 16 }}>Loading…</p>;
//   if (err) return <p style={{ padding: 16, color: "crimson" }}>{err}</p>;
//   if (!data) return <p style={{ padding: 16 }}>Not found.</p>;

//   const { job, contact_map_preview } = data;

//   return (
//     <div style={{ maxWidth: 900, margin: "24px auto", padding: 16 }}>
//       <Link to="/jobs">&larr; Back</Link>
//       <h2 style={{ marginTop: 8 }}>{job.name}</h2>
//       <p><strong>Status:</strong> {job.status || "—"}</p>
//       {job.notes && <p><strong>Notes:</strong> {job.notes}</p>}
//       {job.created_at && (
//         <p><strong>Created:</strong> {new Date(job.created_at).toLocaleString()}</p>
//       )}

//       {/* Upload */}
//       <section style={{ marginTop: 24 }}>
//         <h3>Upload PDF</h3>
//         <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
//           <input
//             type="file"
//             accept="application/pdf"
//             onChange={(e) => setFile(e.target.files?.[0] ?? null)}
//             disabled={uploading}
//           />
//           <button
//             onClick={handleUpload}
//             disabled={!file || uploading}
//           >
//             {uploading ? "Uploading…" : "Submit PDF"}
//           </button>
//         </div>
//         {file && !uploading && (
//           <div style={{ fontSize: 12, color: "#666", marginTop: 6 }}>
//             Selected: {file.name}
//           </div>
//         )}
//       </section>

//       {/* Contact map */}
//       <h3 style={{ marginTop: 24 }}>Contact Map (Preview)</h3>
//       {contact_map_preview ? (
//         <ContactMapPreviewTable preview={contact_map_preview} />
//       ) : (
//         <p>No contact map yet. Upload a PDF to generate one.</p>
//       )}
//     </div>
//   );
// };

// function ContactMapPreviewTable({ preview }: { preview: ContactMapPreview }) {
//   return (
//     <div>
//       <div style={{ fontSize: 12, color: "#666", marginBottom: 8 }}>
//         Generated: {new Date(preview.generated_at).toLocaleString()}
//       </div>
//       <div style={{ overflowX: "auto" }}>
//         <table cellPadding={8} style={{ borderCollapse: "collapse", minWidth: 700 }}>
//           <thead>
//             <tr>
//               <Th>Trade</Th>
//               <Th>Pages</Th>
//               <Th>Notes</Th>
//               <Th>Suggested Contact</Th>
//               <Th>Confidence</Th>
//             </tr>
//           </thead>
//           <tbody>
//             {preview.trades.map((t, i) => (
//               <tr key={i}>
//                 <Td>{t.trade}</Td>
//                 <Td>{t.pages?.join(", ")}</Td>
//                 <Td title={t.notes}>{truncate(t.notes ?? "", 90)}</Td>
//                 <Td>{t.suggested_contact_id ?? "—"}</Td>
//                 <Td>{t.confidence !== undefined ? Math.round(t.confidence * 100) + "%" : "—"}</Td>
//               </tr>
//             ))}
//           </tbody>
//         </table>
//       </div>
//     </div>
//   );
// }

// // Styled cells that pass native props
// const baseTh: React.CSSProperties = { borderBottom: "1px solid #ddd", textAlign: "left" };
// const baseTd: React.CSSProperties = { borderBottom: "1px solid #f0f0f0" };
// type ThProps = React.ThHTMLAttributes<HTMLTableHeaderCellElement>;
// type TdProps = React.TdHTMLAttributes<HTMLTableDataCellElement>;
// const Th: React.FC<ThProps> = ({ style, children, ...rest }) => (
//   <th style={{ ...baseTh, ...style }} {...rest}>{children}</th>
// );
// const Td: React.FC<TdProps> = ({ style, children, ...rest }) => (
//   <td style={{ ...baseTd, ...style }} {...rest}>{children}</td>
// );

// function truncate(s: string, n: number) {
//   return s.length > n ? s.slice(0, n - 1) + "…" : s;
// }

// export default SingleJob;

// --------------------------------------------------------------------------------------------------------------------

// // src/pages/SingleJob.tsx
// import React, { useEffect, useState } from "react";
// import { useParams, Link } from "react-router-dom";
// import { useAuth } from "../auth/AuthContext";
// import { getJobAPI } from "../api/jobs";
// import type { GetJobResponse, ContactMapPreview } from "../types";

// const SingleJob: React.FC = () => {
//   const { jobId = "" } = useParams();
//   const { token, logout } = useAuth();
//   const [data, setData] = useState<GetJobResponse | null>(null);
//   const [err, setErr] = useState<string | null>(null);
//   const [loading, setLoading] = useState(true);

//   useEffect(() => {
//     let mounted = true;
//     (async () => {
//       if (!token) return;
//       try {
//         const res = await getJobAPI(token, jobId);
//         if (mounted) setData(res);
//       } catch (e: any) {
//         if (e?.status === 401) logout();
//         else setErr(e?.message || "Failed to load job");
//       } finally {
//         if (mounted) setLoading(false);
//       }
//     })();
//     return () => {
//       mounted = false;
//     };
//   }, [token, logout, jobId]);

//   if (loading) return <p style={{ padding: 16 }}>Loading…</p>;
//   if (err) return <p style={{ padding: 16, color: "crimson" }}>{err}</p>;
//   if (!data) return <p style={{ padding: 16 }}>Not found.</p>;

//   const { job, contact_map_preview } = data;

//   return (
//     <div style={{ maxWidth: 900, margin: "24px auto", padding: 16 }}>
//       <Link to="/jobs">&larr; Back</Link>
//       <h2 style={{ marginTop: 8 }}>{job.name}</h2>
//       <p><strong>Status:</strong> {job.status || "—"}</p>
//       {job.notes && <p><strong>Notes:</strong> {job.notes}</p>}
//       {job.created_at && (
//         <p><strong>Created:</strong> {new Date(job.created_at).toLocaleString()}</p>
//       )}

//       <h3 style={{ marginTop: 24 }}>Contact Map (Preview)</h3>
//       {contact_map_preview ? (
//         <ContactMapPreviewTable preview={contact_map_preview} />
//       ) : (
//         <p>No contact map yet. Upload a PDF to generate one.</p>
//       )}
//     </div>
//   );
// };

// function ContactMapPreviewTable({ preview }: { preview: ContactMapPreview }) {
//   return (
//     <div>
//       <div style={{ fontSize: 12, color: "#666", marginBottom: 8 }}>
//         Generated: {new Date(preview.generated_at).toLocaleString()}
//       </div>
//       <div style={{ overflowX: "auto" }}>
//         <table cellPadding={8} style={{ borderCollapse: "collapse", minWidth: 700 }}>
//           <thead>
//             <tr>
//               <Th>Trade</Th>
//               <Th>Pages</Th>
//               <Th>Notes</Th>
//               <Th>Suggested Contact</Th>
//               <Th>Confidence</Th>
//             </tr>
//           </thead>
//           <tbody>
//             {preview.trades.map((t, i) => (
//               <tr key={i}>
//                 <Td>{t.trade}</Td>
//                 <Td>{t.pages?.join(", ")}</Td>
//                 <Td title={t.notes}>{truncate(t.notes ?? "", 90)}</Td>
//                 <Td>{t.suggested_contact_id ?? "—"}</Td>
//                 <Td>{t.confidence !== undefined ? Math.round(t.confidence * 100) + "%" : "—"}</Td>
//               </tr>
//             ))}
//           </tbody>
//         </table>
//       </div>
//     </div>
//   );
// }

// // --- Styled table cells that accept native HTML props ---
// const baseTh: React.CSSProperties = { borderBottom: "1px solid #ddd", textAlign: "left" };
// const baseTd: React.CSSProperties = { borderBottom: "1px solid #f0f0f0" };

// type ThProps = React.ThHTMLAttributes<HTMLTableHeaderCellElement>;
// type TdProps = React.TdHTMLAttributes<HTMLTableDataCellElement>;

// const Th: React.FC<ThProps> = ({ style, children, ...rest }) => (
//   <th style={{ ...baseTh, ...style }} {...rest}>{children}</th>
// );

// const Td: React.FC<TdProps> = ({ style, children, ...rest }) => (
//   <td style={{ ...baseTd, ...style }} {...rest}>{children}</td>
// );

// function truncate(s: string, n: number) {
//   return s.length > n ? s.slice(0, n - 1) + "…" : s;
// }

// export default SingleJob;
