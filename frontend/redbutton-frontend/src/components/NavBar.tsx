import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const NavBar: React.FC = () => {
  const { token, logout } = useAuth();
  return (
    <nav style={{ display: "flex", gap: 12, padding: 12, borderBottom: "1px solid #eee" }}>
      <Link to="/jobs">Jobs</Link>
      <Link to="/jobs/new">Create Job</Link>
      <Link to="/contacts">Contacts</Link>
      <div style={{ marginLeft: "auto" }}>
        {token ? <button onClick={logout}>Logout</button> : <Link to="/login">Login</Link>}
      </div>
    </nav>
  );
};

export default NavBar;
