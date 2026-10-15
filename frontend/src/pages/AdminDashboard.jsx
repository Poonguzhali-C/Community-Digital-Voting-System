import { useCallback, useEffect, useState } from "react";
import api, { getErrorMessage } from "../api";
import { useUi } from "../context/UiContext";
import { ErrorState, Spinner, StatusBadge, formatDateTime } from "../components/common";
import { navigate } from "../router";

export default function AdminDashboard() {
  const ui = useUi();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    try {
      const [stats, users, proposals] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/admin/users"),
        api.get("/proposals/"),
      ]);
      setData({ stats: stats.data, users: users.data, proposals: proposals.data });
      setError("");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const close = async (p) => {
    const ok = await ui.confirm({
      title: "Close proposal?",
      message: `"${p.title}" will stop accepting votes immediately. This cannot be undone.`,
      confirmText: "Close proposal",
      danger: true,
    });
    if (!ok) return;
    setBusyId(p.id);
    try {
      await api.patch(`/proposals/${p.id}/close`);
      ui.success("Proposal closed");
    } catch (err) {
      ui.error(getErrorMessage(err));
    }
    setBusyId(null);
    load();
  };

  if (error && !data) return <div className="page"><ErrorState message={error} onRetry={load} /></div>;
  if (!data) return <div className="page"><Spinner label="Loading admin data…" /></div>;
  const { stats, users, proposals } = data;

  const cards = [
    ["Users", stats.users, `${stats.admins} admin${stats.admins === 1 ? "" : "s"}`],
    ["Proposals", stats.proposals, `${stats.active} active`],
    ["Closed / Expired", `${stats.closed} / ${stats.expired}`, "finished proposals"],
    ["Votes cast", stats.votes, "all proposals"],
  ];

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Admin dashboard</h1>
          <p className="muted">Monitor activity and manage proposals.</p>
        </div>
        <button className="btn btn-ghost" onClick={load}>↻ Refresh</button>
      </div>

      <div className="stats">
        {cards.map(([label, num, sub]) => (
          <div key={label} className="stat">
            <div className="stat-num">{num}</div>
            <div className="stat-label">{label}</div>
            <div className="muted small">{sub}</div>
          </div>
        ))}
      </div>

      <section className="card">
        <h2>Proposals</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Title</th><th>Status</th><th>Deadline</th><th>Yes</th><th>No</th><th>Abstain</th><th>Total</th><th /></tr>
            </thead>
            <tbody>
              {proposals.length === 0 && <tr><td colSpan="8" className="muted center">No proposals yet</td></tr>}
              {proposals.map((p) => (
                <tr key={p.id}>
                  <td><button className="link-btn" onClick={() => navigate(`/proposal/${p.id}`)}>{p.title}</button></td>
                  <td><StatusBadge status={p.status} /></td>
                  <td>{formatDateTime(p.deadline)}</td>
                  <td>{p.yes}</td><td>{p.no}</td><td>{p.abstain}</td><td><strong>{p.total}</strong></td>
                  <td>
                    {p.status === "ACTIVE" && (
                      <button className="btn btn-danger btn-sm" disabled={busyId === p.id} onClick={() => close(p)}>
                        {busyId === p.id ? "Closing…" : "Close"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <h2>Users</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>Username</th><th>Role</th><th>Votes cast</th></tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.id}</td><td>{u.username}</td>
                  <td><span className={`role role-${u.role.toLowerCase()}`}>{u.role}</span></td>
                  <td>{u.votes_cast}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
