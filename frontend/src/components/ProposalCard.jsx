import { Countdown, ResultsBars, StatusBadge, formatDateTime } from "./common";
import VotePanel from "./VotePanel";
import { navigate } from "../router";

export default function ProposalCard({ proposal, onChanged, onExpire }) {
  return (
    <article className={`card proposal status-${proposal.status.toLowerCase()}`}>
      <div className="card-top">
        <StatusBadge status={proposal.status} />
        <Countdown deadline={proposal.deadline} status={proposal.status} onExpire={onExpire} />
      </div>
      <h3 className="card-title">{proposal.title}</h3>
      <p className="card-desc">{proposal.description}</p>
      <div className="muted small">Created {formatDateTime(proposal.created_at)}</div>
      <ResultsBars proposal={proposal} />
      <VotePanel key={`${proposal.id}-${proposal.my_vote}-${proposal.status}`} proposal={proposal} onChanged={onChanged} />
      <button className="link-btn" onClick={() => navigate(`/proposal/${proposal.id}`)}>
        View details →
      </button>
    </article>
  );
}
