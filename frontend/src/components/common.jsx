import { useEffect, useState } from "react";

export function StatusBadge({ status }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{status}</span>;
}

export function Spinner({ label = "Loading…" }) {
  return (
    <div className="center-box" role="status">
      <div className="spinner" />
      <span className="muted">{label}</span>
    </div>
  );
}

export function SkeletonCards({ count = 3 }) {
  return (
    <div className="grid">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="card skeleton">
          <div className="sk-line w40" />
          <div className="sk-line w80" />
          <div className="sk-line w60" />
          <div className="sk-block" />
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ icon = "🗳️", title, text, action }) {
  return (
    <div className="empty">
      <div className="empty-icon">{icon}</div>
      <h3>{title}</h3>
      <p className="muted">{text}</p>
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="empty">
      <div className="empty-icon">⚠️</div>
      <h3>Something went wrong</h3>
      <p className="muted">{message}</p>
      {onRetry && (
        <button className="btn btn-primary" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function formatDateTime(iso) {
  return new Date(iso).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function remaining(deadlineIso) {
  return new Date(deadlineIso).getTime() - Date.now();
}

/** Live countdown to the deadline. Calls onExpire once when it reaches zero. */
export function Countdown({ deadline, status, onExpire }) {
  const [ms, setMs] = useState(() => remaining(deadline));

  useEffect(() => {
    if (status !== "ACTIVE") return;
    let fired = false;
    const tick = () => {
      const left = remaining(deadline);
      setMs(left);
      if (left <= 0 && !fired) {
        fired = true;
        onExpire?.();
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [deadline, status, onExpire]);

  if (status === "CLOSED") return <span className="countdown muted">Closed by admin</span>;
  if (status === "EXPIRED" || ms <= 0)
    return <span className="countdown muted">Ended {formatDateTime(deadline)}</span>;

  const s = Math.floor(ms / 1000);
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const text = d > 0 ? `${d}d ${h}h ${m}m` : h > 0 ? `${h}h ${m}m ${sec}s` : `${m}m ${sec}s`;
  const urgent = ms < 3600 * 1000;
  return (
    <span className={`countdown ${urgent ? "urgent" : ""}`} title={formatDateTime(deadline)}>
      ⏱ {text} left
    </span>
  );
}

const COLORS = { yes: "yes", no: "no", abstain: "abstain" };
const LABELS = { yes: "Yes", no: "No", abstain: "Abstain" };

/** Results bars with counts and percentages (data comes from the API / database). */
export function ResultsBars({ proposal }) {
  const total = proposal.total;
  return (
    <div className="results">
      {Object.keys(COLORS).map((k) => {
        const n = proposal[k];
        const pct = total ? (n * 100) / total : 0;
        return (
          <div key={k} className="result-row">
            <div className="result-head">
              <span className={`dot dot-${k}`} /> {LABELS[k]}
              <span className="result-num">
                {n} · {pct.toFixed(1)}%
              </span>
            </div>
            <div className="bar">
              <div className={`bar-fill bar-${k}`} style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
      <div className="muted small">
        {total} {total === 1 ? "vote" : "votes"} in total
      </div>
    </div>
  );
}
