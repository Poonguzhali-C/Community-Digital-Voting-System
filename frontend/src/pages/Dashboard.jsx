import { useCallback, useEffect, useMemo, useState } from "react";
import api, { getErrorMessage } from "../api";
import { useAuth } from "../context/AuthContext";
import CreateProposalModal from "../components/CreateProposalModal";
import ProposalCard from "../components/ProposalCard";
import { EmptyState, ErrorState, SkeletonCards } from "../components/common";

const FILTERS = ["ALL", "ACTIVE", "CLOSED", "EXPIRED"];
const POLL_MS = 15000; // near real-time: refresh from the API every 15 seconds

export default function Dashboard() {
  const { user } = useAuth();
  const [proposals, setProposals] = useState(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("ALL");
  const [query, setQuery] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/proposals/");
      setProposals(data);
      setError("");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
  }, [load]);

  const counts = useMemo(() => {
    const c = { ALL: 0, ACTIVE: 0, CLOSED: 0, EXPIRED: 0 };
    (proposals || []).forEach((p) => {
      c.ALL++;
      c[p.status]++;
    });
    return c;
  }, [proposals]);

  const myVotes = (proposals || []).filter((p) => p.my_vote).length;
  const awaiting = (proposals || []).filter((p) => p.status === "ACTIVE" && !p.my_vote).length;

  const visible = (proposals || []).filter(
    (p) =>
      (filter === "ALL" || p.status === filter) &&
      (p.title + " " + p.description).toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Hello, {user.username} 👋</h1>
          <p className="muted">Review proposals and make your voice heard.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          + New proposal
        </button>
      </div>

      <div className="stats">
        <div className="stat"><div className="stat-num">{counts.ACTIVE}</div><div className="stat-label">Open for voting</div></div>
        <div className="stat accent"><div className="stat-num">{awaiting}</div><div className="stat-label">Awaiting your vote</div></div>
        <div className="stat"><div className="stat-num">{myVotes}</div><div className="stat-label">Votes you cast</div></div>
        <div className="stat"><div className="stat-num">{counts.ALL}</div><div className="stat-label">Total proposals</div></div>
      </div>

      <div className="toolbar">
        <div className="tabs" role="tablist">
          {FILTERS.map((f) => (
            <button key={f} role="tab" aria-selected={filter === f} className={`tab ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
              {f === "ALL" ? "All" : f[0] + f.slice(1).toLowerCase()} <span className="tab-count">{counts[f]}</span>
            </button>
          ))}
        </div>
        <input className="search" placeholder="Search proposals…" value={query} onChange={(e) => setQuery(e.target.value)} />
      </div>

      {error && !proposals ? (
        <ErrorState message={error} onRetry={load} />
      ) : !proposals ? (
        <SkeletonCards />
      ) : visible.length === 0 ? (
        <EmptyState
          title={proposals.length === 0 ? "No proposals yet" : "No proposals match"}
          text={proposals.length === 0 ? "Be the first to start a community discussion." : "Try another filter or search term."}
          action={proposals.length === 0 && <button className="btn btn-primary" onClick={() => setShowCreate(true)}>Create the first proposal</button>}
        />
      ) : (
        <div className="grid">
          {visible.map((p) => (
            <ProposalCard key={p.id} proposal={p} onChanged={load} onExpire={load} />
          ))}
        </div>
      )}

      {showCreate && <CreateProposalModal onClose={() => setShowCreate(false)} onCreated={load} />}
    </div>
  );
}
