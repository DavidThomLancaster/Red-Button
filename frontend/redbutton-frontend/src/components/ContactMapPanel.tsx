import React, { useEffect, useState } from "react";
import { getContactsMapApi, patchContactsMapOpsApi, type ContactsMap, type ContactSummary } from "../api/contactsMap";
import { useAuth } from "../auth/AuthContext";
import { ContactPickerDialog } from "../components/ContactPickerDialog";
import { searchContactsApi } from "../api/contactsSearch"; // (dialog imports it internally; ok to keep)

export const ContactMapPanel: React.FC<{ jobId: string }> = ({ jobId }) => {
  const { token } = useAuth();
  const [map, setMap] = useState<ContactsMap | null>(null);
  const [contactsById, setContactsById] = useState<Record<string, ContactSummary>>({});
  const [ref, setRef] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [target, setTarget] = useState<{ trade: string; blockIdx: number } | null>(null);

  const openPicker = (trade: string, blockIdx: number) => {
    setTarget({ trade, blockIdx });
    setPickerOpen(true);
  };

  const closePicker = () => setPickerOpen(false);

  async function load() {
    if (!token) return;
    try {
      const res = await getContactsMapApi(token, jobId);
      setMap(res.map);
      setContactsById(res.contactsById);
      setRef(res.ref);
    } catch (e: any) {
      console.error("Load map failed", e);
      setErr(e?.message || "Failed to load contact map");
    } finally {
      setLoading(false);
    }
  }

  async function addSelectedContacts(ids: string[]) {
    if (!token || !target) return;
    try {
      const ops = ids.map(contact_id => ({
        op: "add_contact" as const,
        trade: target.trade,
        block: target.blockIdx,
        contact_id,
      }));
      const res = await patchContactsMapOpsApi(token, jobId, ref, ops);
      setMap(res.map);
      setContactsById(res.contactsById);
      setRef(res.ref);
    } catch (e) {
      await load(); // stale ref fallback
    }
  }

  useEffect(() => { load(); }, [token, jobId]);

  if (loading) return <div>Loading contact map…</div>;
  if (err) return <div style={{ color: "crimson" }}>{err}</div>;
  if (!map) return <div>No contact map yet.</div>;

  async function removeContact(trade: string, block: number, contact_id: string) {
    if (!token) return;
    try {
      const res = await patchContactsMapOpsApi(token, jobId, ref, [
        { op: "remove_contact", trade, block, contact_id }
      ]);
      setMap(res.map);
      setContactsById(res.contactsById);
      setRef(res.ref);
    } catch (e: any) {
      // if ref is stale (409), just reload
      await load();
    }
  }

  // FIXME - probably going to delete this later.
  async function addContact(trade: string, block: number) {

    // Get contacts from the request we do
      // probably need to open a new dialog box or something to do this that like pops up a list of contacts to choose from...
    // We choose and then we send with the code below. 


    if (!token) return;
    const contact_id = "FAKEID" //window.prompt("Enter contact ID to add:");
    if (!contact_id) return;
    try {
      const res = await patchContactsMapOpsApi(token, jobId, ref, [
        { op: "add_contact", trade, block, contact_id }
      ]);
      setMap(res.map);
      setContactsById(res.contactsById);
      setRef(res.ref);
    } catch (e: any) {
      // handle stale ref by refetching
      await load();
    }
  }

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12, marginTop: 16 }}>
      {Object.entries(map).map(([trade, blocks]) => (
        <div key={trade} style={{ marginBottom: 16 }}>
          <h4 style={{ margin: "8px 0" }}>{trade}</h4>
          <div style={{ paddingLeft: 12 }}>
            {blocks.map((b, idx) => (
              <div key={idx} style={{ marginBottom: 8 }}>
                <div style={{ fontSize: 14, opacity: 0.8 }}>
                  <em>{b.note}</em> &nbsp; — Pages: {b.pages.join(", ")}
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 6 }}>
                  <button onClick={() => openPicker(trade, idx)}>＋</button>
                  {b.contacts.map(cid => {
                    const c = contactsById[cid];
                    const label = c ? (c.name || c.email || cid) : cid;
                    return (
                      <span key={cid} style={{ border: "1px solid #ccc", borderRadius: 16, padding: "2px 8px", display: "inline-flex", alignItems: "center", gap: 6 }}>
                        {label}
                        <button aria-label={`remove ${label}`} onClick={() => removeContact(trade, idx, cid)}>−</button>
                      </span>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Modal */}
      {target && token && (
        <ContactPickerDialog
          open={pickerOpen}
          onClose={closePicker}
          token={token}
          jobId={jobId}
          initialTrade={target.trade}
          excludeIds={map[target.trade][target.blockIdx].contacts}
          onAdd={addSelectedContacts}
        />
      )}
    </div>
  );
};

//   return (
//     <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12, marginTop: 16 }}>
//       {Object.entries(map).map(([trade, blocks]) => (
//         <div key={trade} style={{ marginBottom: 16 }}>
//           <h4 style={{ margin: "8px 0" }}>{trade}</h4>
//           <div style={{ paddingLeft: 12 }}>
//             {blocks.map((b, idx) => (
//               <div key={idx} style={{ marginBottom: 8 }}>
//                 <div style={{ fontSize: 14, opacity: 0.8 }}>
//                   <em>{b.note}</em> &nbsp; — Pages: {b.pages.join(", ")}
//                 </div>
//                 <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 6 }}>
//                   {/* "+" and "−" live together */}
//                   <button onClick={() => addContact(trade, idx)}>＋</button>
//                   {b.contacts.map(cid => {
//                     const c = contactsById[cid];
//                     const label = c ? (c.name || c.email || cid) : cid;
//                     return (
//                       <span key={cid} style={{ border: "1px solid #ccc", borderRadius: 16, padding: "2px 8px", display: "inline-flex", alignItems: "center", gap: 6 }}>
//                         {label}
//                         <button aria-label={`remove ${label}`} onClick={() => removeContact(trade, idx, cid)}>−</button>
//                       </span>
//                     );
//                   })}
//                 </div>
//               </div>
//             ))}
//           </div>
//         </div>
//       ))}
//     </div>
//   );
// };



// // components/ContactMapPanel.tsx
// import React, { useEffect, useState } from "react";
// import { getContactsMapApi, patchContactsMapOpsApi, type ContactsMap, type ContactSummary } from "../api/contactsMap";
// import { useAuth } from "../auth/AuthContext";

// export const ContactMapPanel: React.FC<{ jobId: string; onNeedAddContact?: (trade: string, blockIdx: number) => void }> = ({ jobId, onNeedAddContact }) => {
//   const { token } = useAuth();
//   const [map, setMap] = useState<ContactsMap | null>(null);
//   const [contactsById, setContactsById] = useState<Record<string, ContactSummary>>({});
//   const [ref, setRef] = useState<string>("");
//   const [loading, setLoading] = useState(true);

//   useEffect(() => {
//     if (!token) return;
//     (async () => {
//       const res = await getContactsMapApi(token, jobId);
//       setMap(res.map);
//       setContactsById(res.contactsById);
//       setRef(res.ref);
//       setLoading(false);
//     })().catch(err => {
//       console.error("Load map failed", err);
//       setLoading(false);
//     });
//   }, [token, jobId]);

//   if (loading) return <div>Loading contact map…</div>;
//   if (!map) return <div>No contact map yet.</div>;

//   async function removeContact(trade: string, block: number, contact_id: string) {
//     if (!token) return;
//     const res = await patchContactsMapOpsApi(token, jobId, ref, [{ op: "remove_contact", trade, block, contact_id }]);
//     setMap(res.map);
//     setContactsById(res.contactsById);
//     setRef(res.ref);
//   }

//   return (
//     <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12, marginTop: 16 }}>
//       {Object.entries(map).map(([trade, blocks]) => (
//         <div key={trade} style={{ marginBottom: 16 }}>
//           <h4 style={{ margin: "8px 0" }}>{trade}</h4>
//           <div style={{ paddingLeft: 12 }}>
//             {blocks.map((b, idx) => (
//               <div key={idx} style={{ marginBottom: 8 }}>
//                 <div style={{ fontSize: 14, opacity: 0.8 }}>
//                   <em>{b.note}</em> &nbsp; — Pages: {b.pages.join(", ")}
//                 </div>
//                 <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 6 }}>
//                   {/* "+" to add contacts */}
//                   <button onClick={() => onNeedAddContact?.(trade, idx)}>＋</button>
//                   {/* contact chips with "-" buttons */}
//                   {b.contacts.map(cid => {
//                     const c = contactsById[cid];
//                     const label = c ? (c.name || c.email || cid) : cid;
//                     return (
//                       <span key={cid} style={{ border: "1px solid #ccc", borderRadius: 16, padding: "2px 8px", display: "inline-flex", alignItems: "center", gap: 6 }}>
//                         {label}
//                         <button aria-label={`remove ${label}`} onClick={() => removeContact(trade, idx, cid)}>−</button>
//                       </span>
//                     );
//                   })}
//                 </div>
//               </div>
//             ))}
//           </div>
//         </div>
//       ))}
//     </div>
//   );
// };
