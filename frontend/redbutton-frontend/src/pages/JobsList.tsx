import React, { useEffect, useState } from "react";
import { listJobsApi, deleteJobApi } from "../api/jobs";
import { useAuth } from "../auth/AuthContext";
import type { Job } from "../types";
import { Link } from "react-router-dom";

const JobsList: React.FC = () => {
  const { token, logout } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set()); // track buttons

  useEffect(() => {
    let mounted = true;
    (async () => {
      if (!token) return;
      try {
        const { jobs } = await listJobsApi(token);
        if (mounted) setJobs(jobs);
      } catch (e: any) {
        if (e.status === 401) logout();
        else setErr(e?.message || "Failed to load jobs");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [token, logout]);

  if (loading) return <p style={{ padding: 16 }}>Loading…</p>;
  if (err) return <p style={{ padding: 16, color: "crimson" }}>{err}</p>;

  async function handleRemoveJob(jobId: string) {
    if (!token) {
      console.error("No auth token available");
      return;
    }

    // Optimistic UI: remove immediately, but keep a snapshot to rollback if needed
    const prev = jobs;
    setJobs(curr => curr.filter(j => j.job_id !== jobId));
    setDeletingIds(s => new Set(s).add(jobId));

    try {
      const res = await deleteJobApi(token, jobId);
      console.log(res.status, res.job_id);

      // Optional: re-fetch to be 100% in sync with server
      // const { jobs: latest } = await listJobsApi(token);
      // setJobs(latest);
    } catch (e: any) {
      // Rollback on failure
      console.error("Delete failed", e);
      if (e.status === 401) logout();
      setJobs(prev); // revert
      alert(e?.message || "Failed to delete job");
    } finally {
      setDeletingIds(s => {
        const next = new Set(s);
        next.delete(jobId);
        return next;
      });
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: "24px auto", padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Jobs</h2>
        <Link to="/jobs/new"><button>Create Job</button></Link>
      </div>
      {jobs.length === 0 ? <p>No jobs yet.</p> : (
        <ul style={{ paddingLeft: 16 }}>
          {jobs.map(j => {
            const isDeleting = deletingIds.has(j.job_id);
            return (
              <li key={j.job_id} style={{ padding: 8, display: "flex", alignItems: "center", gap: 12 }}>
                <Link to={`/jobs/${j.job_id}`} style={{ textDecoration: "none", flex: 1 }}>
                  <strong>{j.name}</strong>
                  {j.status ? ` — ${j.status}` : ""} 
                  {j.created_at ? ` (${new Date(j.created_at).toLocaleString()})` : ""}
                </Link>
                <button
                  disabled={isDeleting}
                  onClick={() => handleRemoveJob(j.job_id)}
                >
                  {isDeleting ? "Removing…" : "Remove Job"}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

export default JobsList;


// import React, { useEffect, useState } from "react";
// import { listJobsApi, deleteJobApi } from "../api/jobs";
// import { useAuth } from "../auth/AuthContext";
// import type { Job } from "../types";
// import { Link } from "react-router-dom";

// const JobsList: React.FC = () => {
//   const { token, logout } = useAuth();
//   const [jobs, setJobs] = useState<Job[]>([]);
//   const [err, setErr] = useState<string | null>(null);
//   const [loading, setLoading] = useState(true);

//   useEffect(() => {
//     let mounted = true;
//     (async () => {
//       if (!token) return;
//       try {
//         const { jobs } = await listJobsApi(token);
//         if (mounted) setJobs(jobs);
//       } catch (e: any) {
//         if (e.status === 401) logout();
//         else setErr(e?.message || "Failed to load jobs");
//       } finally {
//         if (mounted) setLoading(false);
//       }
//     })();
//     return () => { mounted = false; };
//   }, [token, logout]);

//   if (loading) return <p style={{ padding: 16 }}>Loading…</p>;
//   if (err) return <p style={{ padding: 16, color: "crimson" }}>{err}</p>;

//   function handleRemoveJob(jobId: string) {
//     if (!token) {
//       console.error("No auth token available");
//       return;
//     }
//     deleteJobApi(token, jobId)   // token is now a string
//       .then(res => {
//         console.log(res.status, res.job_id);
//         // setJobs(prev => prev.filter(j => j.job_id !== jobId));
//       })
//       .catch(err => console.error("Delete failed", err));
//   }

//   return (
//     <div style={{ maxWidth: 800, margin: "24px auto", padding: 16 }}>
//       <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
//         <h2>Jobs</h2>
//         <Link to="/jobs/new"><button>Create Job</button></Link>
//       </div>
//       {jobs.length === 0 ? <p>No jobs yet.</p> : (
//         <ul style={{ paddingLeft: 16 }}>
//           {jobs.map(j => (
//             <li key={j.job_id} style={{ padding: 8 }}>
//               <Link to={`/jobs/${j.job_id}`} style={{ textDecoration: "none" }}>
//                 <strong>{j.name}</strong>
//                 {j.status ? ` — ${j.status}` : ""} 
//                 {j.created_at ? ` (${new Date(j.created_at).toLocaleString()})` : ""}
//               </Link>
//               <button
//                 style={{ marginLeft: 12 }}
//                 onClick={() => handleRemoveJob(j.job_id)}
//               >
//                 Remove Job
//               </button>
//             </li>
//           ))}
//         </ul>
//       )}
//     </div>
//   );
// };
// export default JobsList;
