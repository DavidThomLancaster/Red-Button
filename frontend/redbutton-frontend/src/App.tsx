import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import JobsList from "./pages/JobsList";
import CreateJob from "./pages/CreateJob";
import RequireAuth from "./auth/RequireAuth";
import NavBar from "./components/NavBar";
import SingleJob from "./pages/SingleJob";
import { ContactsPage } from "./pages/ContactsPage";

const App: React.FC = () => {
  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/" element={<Login />} />    
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/jobs"
          element={
            <RequireAuth>
              <JobsList />
            </RequireAuth>
          }
        />
        <Route
          path="/jobs/new"
          element={
            <RequireAuth>
              <CreateJob />
            </RequireAuth>
          }
        />
        <Route path="/contacts" element={<ContactsPage />} />
        <Route path="/jobs/:jobId" element={<RequireAuth><SingleJob /></RequireAuth>} />

      

        <Route path="*" element={<div style={{ padding: 16 }}>Not Found</div>} />
      </Routes>
    </>
  );
};

export default App;
//{<Navigate to="/jobs" replace />} />