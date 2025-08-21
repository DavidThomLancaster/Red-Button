import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createJobApi } from "../api/jobs";
import { useAuth } from "../auth/AuthContext";

const CreateJob: React.FC = () => {
  const { token, logout } = useAuth();
  const nav = useNavigate();
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      if (!token) throw new Error("Not authenticated");
      await createJobApi(token, name, notes || undefined);
      nav("/jobs");
    } catch (e: any) {
      if (e.status === 401) logout();
      else setErr(e?.message || "Failed to create job");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={onSubmit} style={{ maxWidth: 480, margin: "48px auto", display: "grid", gap: 12 }}>
      <h2>Create Job</h2>
      <input placeholder="Job name" value={name} onChange={e=>setName(e.target.value)} required />
      <textarea placeholder="Notes (optional)" value={notes} onChange={e=>setNotes(e.target.value)} rows={4} />
      {err && <div style={{ color: "crimson" }}>{err}</div>}
      <button disabled={loading || !name.trim()}>{loading ? "Creating..." : "Create"}</button>
    </form>
  );
};
export default CreateJob;
