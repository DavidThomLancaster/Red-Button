import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { registerApi } from "../api/auth";
import { useAuth } from "../auth/AuthContext";

const Register: React.FC = () => {
  const { login } = useAuth();
  const nav = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const { token } = await registerApi(email, password);
      login(token);              // or redirect to /login if your backend doesn't return token
      nav("/jobs");
    } catch (e: any) {
      setErr(e?.message || "Register failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={onSubmit} style={{ maxWidth: 360, margin: "48px auto", display: "grid", gap: 12 }}>
      <h2>Register</h2>
      <input placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} required />
      <input placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} required />
      {err && <div style={{ color: "crimson" }}>{err}</div>}
      <button disabled={loading}>{loading ? "Creating..." : "Create account"}</button>
      <div>Already have an account? <Link to="/login">Login</Link></div>
    </form>
  );
};
export default Register;
