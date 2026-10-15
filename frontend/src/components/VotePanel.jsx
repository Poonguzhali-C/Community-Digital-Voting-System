import { useState } from "react";
import api, { getErrorMessage } from "../api";
import { useUi } from "../context/UiContext";

const CHOICES = [
  { key: "YES", label: "Yes", icon: "👍" },
  { key: "NO", label: "No", icon: "👎" },
  { key: "ABSTAIN", label: "Abstain", icon: "✋" },
];

/** Cast / change / revoke a vote. Rules are enforced by the backend; the UI mirrors them. */
export default function VotePanel({ proposal, onChanged }) {
  const ui = useUi();
  const [choice, setChoice] = useState(proposal.my_vote);
  const [busy, setBusy] = useState(false);
  const active = proposal.status === "ACTIVE";
  const hasVote = !!proposal.my_vote;
  const dirty = choice && choice !== proposal.my_vote;

  const run = async (fn, okMessage) => {
    setBusy(true);
    try {
      await fn();
      ui.success(okMessage);
    } catch (err) {
      ui.error(getErrorMessage(err));
    } finally {
      setBusy(false);
      await onChanged(); // always re-sync with the database (also after errors)
    }
  };

  const submit = () =>
    hasVote
      ? run(() => api.put(`/votes/${proposal.my_vote_id}`, { vote: choice }), "Your vote was updated")
      : run(() => api.post(`/proposals/${proposal.id}/vote`, { vote: choice }), "Your vote was recorded");

  const revoke = async () => {
    const ok = await ui.confirm({
      title: "Revoke your vote?",
      message: `Your "${proposal.my_vote}" vote on "${proposal.title}" will be removed. You can vote again while the proposal is active.`,
      confirmText: "Revoke vote",
      danger: true,
    });
    if (ok) run(() => api.delete(`/votes/${proposal.my_vote_id}`), "Your vote was revoked");
  };

  if (!active) {
    return (
      <div className="vote-note">
        {hasVote ? (
          <>You voted <strong>{proposal.my_vote}</strong>. Voting is locked because this proposal is {proposal.status.toLowerCase()}.</>
        ) : (
          <>Voting is closed — this proposal is {proposal.status.toLowerCase()}.</>
        )}
      </div>
    );
  }

  return (
    <div className="vote-panel">
      <div className="vote-choices" role="radiogroup" aria-label="Your vote">
        {CHOICES.map((c) => (
          <button
            key={c.key}
            type="button"
            role="radio"
            aria-checked={choice === c.key}
            className={`choice choice-${c.key.toLowerCase()} ${choice === c.key ? "selected" : ""} ${
              proposal.my_vote === c.key ? "current" : ""
            }`}
            onClick={() => setChoice(c.key)}
            disabled={busy}
          >
            <span className="choice-icon">{c.icon}</span>
            {c.label}
          </button>
        ))}
      </div>
      <div className="vote-actions">
        <button className="btn btn-primary" onClick={submit} disabled={busy || !dirty}>
          {busy ? "Saving…" : hasVote ? "Update vote" : "Submit vote"}
        </button>
        {hasVote && (
          <button className="btn btn-ghost-danger" onClick={revoke} disabled={busy}>
            Revoke vote
          </button>
        )}
      </div>
      {hasVote && (
        <div className="muted small">
          Your current vote: <strong>{proposal.my_vote}</strong>
        </div>
      )}
    </div>
  );
}
