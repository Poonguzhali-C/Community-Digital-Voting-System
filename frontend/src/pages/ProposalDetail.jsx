import { useCallback, useEffect, useState } from "react";
import api, { getErrorMessage } from "../api";
import { useAuth } from "../context/AuthContext";
import { useUi } from "../context/UiContext";
import { Countdown, ErrorState, ResultsBars, Spinner, StatusBadge, formatDateTime } from "../components/common";
import VotePanel from "../components/VotePanel";
import { navigate } from "../router";

export default function ProposalDetail({ id }) {
  const { isAdmin } = useAuth();
  const ui = useUi();
  const [proposal, setProposal] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [p, r] = await Promise.all([
        api.get(`/proposals/${id}`),
        api.get(`/proposals/${id}/results`),
      ]);
      setProposal(p.data);
      setResults(r.data);
      setError("");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, [id]);

  useEffect(() => {
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, [load]);

  const close = async () => {
    const ok = await ui.confirm({
      title: "Close this proposal?",
      message: "No more votes can be cast, changed or revoked. This cannot be undone.",
      confirmText: "Close proposal",
      danger: true,
    });
    if (!ok) return;
    try {
      await api.patch(`/proposals/${id}/close`);
      ui.success("Proposal closed");
    } catch (err) {
      ui.error(getErrorMessage(err));
    }
    load();
  };

  if (error && !proposal)
    return (
      <div className="page">
        <button className="link-btn" onClick={() => navigate("/")}>← Back to dashboard</button>
        <ErrorState message={error} onRetry={load} />
      </div>
    );
  if (!proposal || !results) return <div className="page"><Spinner label="Loading proposal…" /></div>;

  const winner =
    results.total === 0
      ? null
      : [["Yes", results.yes], ["No", results.no], ["Abstain", results.abstain]].sort((a, b) => b[1] - a[1]);
  const tie = winner && winner[0][1] === winner[1][1];

  return (
    <div className="page narrow">
      <button className="link-btn" onClick={() => navigate("/")}>← Back to dashboard</button>
      <article className="card detail">
        <div className="card-top">
          <StatusBadge status={proposal.status} />
          <Countdown deadline={proposal.deadline} status={proposal.status} onExpire={load} />
        </div>
        <h1>{proposal.title}</h1>
        <p className="detail-desc">{proposal.description}</p>
        <div className="meta">
          <div><span className="muted small">Created</span><br />{formatDateTime(proposal.created_at)}</div>
          <div><span className="muted small">Deadline</span><br />{formatDateTime(proposal.deadline)}</div>
        </div>

        <h3>Results</h3>
        <ResultsBars proposal={{ ...proposal, ...results }} />
        {proposal.status !== "ACTIVE" && winner && (
          <div className="alert alert-info">
            Final outcome: {tie ? "tie between top options" : <strong>{winner[0][0]}</strong>} ({winner[0][1]} of {results.total} votes)
          </div>
        )}

        <h3>Your vote</h3>
        <VotePanel key={`${proposal.my_vote}-${proposal.status}`} proposal={proposal} onChanged={load} />

        {isAdmin && proposal.status === "ACTIVE" && (
          <div className="admin-zone">
            <div>
              <strong>Admin</strong>
              <div className="muted small">Force-close this proposal before its deadline.</div>
            </div>
            <button className="btn btn-danger" onClick={close}>Close proposal</button>
          </div>
        )}
      </article>
    </div>
  );
}
