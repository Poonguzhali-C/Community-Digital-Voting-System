import { useState } from "react";
import api, { getErrorMessage } from "../api";
import { useUi } from "../context/UiContext";

function defaultDeadline() {
  const d = new Date(Date.now() + 2 * 24 * 3600 * 1000);
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

export default function CreateProposalModal({ onClose, onCreated }) {
  const ui = useUi();
  const [form, setForm] = useState({ title: "", description: "", deadline: defaultDeadline() });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    const errs = {};
    if (form.title.trim().length < 3) errs.title = "Title must be at least 3 characters.";
    if (form.description.trim().length < 3) errs.description = "Description must be at least 3 characters.";
    if (!form.deadline || new Date(form.deadline) <= new Date()) errs.deadline = "Deadline must be in the future.";
    setErrors(errs);
    if (Object.keys(errs).length) return;
    setBusy(true);
    try {
      await api.post("/proposals/", {
        title: form.title.trim(),
        description: form.description.trim(),
        deadline: new Date(form.deadline).toISOString(),
      });
      ui.success("Proposal created");
      onCreated();
      onClose();
    } catch (err) {
      ui.error(getErrorMessage(err));
      setBusy(false);
    }
  };

  return (
    <div className="overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={submit} noValidate>
        <div className="modal-head">
          <h2>New proposal</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">×</button>
        </div>
        <label className="field">
          <span>Title</span>
          <input value={form.title} onChange={set("title")} maxLength={200} placeholder="e.g. Build a community garden" />
          {errors.title && <em className="field-error">{errors.title}</em>}
        </label>
        <label className="field">
          <span>Description</span>
          <textarea rows={4} value={form.description} onChange={set("description")} placeholder="Explain what residents are voting on" />
          {errors.description && <em className="field-error">{errors.description}</em>}
        </label>
        <label className="field">
          <span>Voting deadline</span>
          <input type="datetime-local" value={form.deadline} onChange={set("deadline")} />
          <small className="muted">Defaults to 2 days from now. Voting closes automatically at this time.</small>
          {errors.deadline && <em className="field-error">{errors.deadline}</em>}
        </label>
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" disabled={busy}>{busy ? "Creating…" : "Create proposal"}</button>
        </div>
      </form>
    </div>
  );
}
