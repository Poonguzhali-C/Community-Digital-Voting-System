import { useState } from "react";
import { getErrorMessage } from "../api";
import { useAuth } from "../context/AuthContext";
import { useUi } from "../context/UiContext";
import { navigate } from "../router";

function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="auth-wrap">
      <div className="auth-hero">
        <div className="auth-hero-inner">
          <div className="brand-mark big">🗳</div>
          <h1>Your community. Your voice.</h1>
          <p>Vote on public proposals, track live results and make decisions together — transparently and securely.</p>
          <ul className="hero-points">
            <li>✓ One vote per person, enforced by the server</li>
            <li>✓ Change or revoke your vote while a proposal is active</li>
            <li>✓ Live results with automatic deadlines</li>
          </ul>
        </div>
      </div>
      <div className="auth-panel">
        <div className="auth-card">
          <h2>{title}</h2>
          <p className="muted">{subtitle}</p>
          {children}
          <div className="auth-footer">{footer}</div>
        </div>
      </div>
    </div>
  );
}

function PasswordField({ value, onChange, label = "Password", autoComplete }) {
  const [show, setShow] = useState(false);
  return (
    <label className="field">
      <span>{label}</span>
      <div className="input-group">
        <input
          type={show ? "text" : "password"}
          value={value}
          onChange={onChange}
          autoComplete={autoComplete}
        />
        <button type="button" className="input-addon" onClick={() => setShow(!show)}>
          {show ? "Hide" : "Show"}
        </button>
      </div>
    </label>
  );
}

export function LoginPage() {
  const { login } = useAuth();
  const ui = useUi();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.username.trim() || !form.password) {
      setError("Please enter your username and password.");
      return;
    }
    setBusy(true);
    try {
      const user = await login(form.username.trim(), form.password);
      ui.success(`Welcome back, ${user.username}!`);
      navigate("/");
    } catch (err) {
      setError(getErrorMessage(err));
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="Sign in"
      subtitle="Welcome back — sign in to cast your vote."
      footer={
        <>
          New here? <button className="link-btn" onClick={() => navigate("/register")}>Create an account</button>
        </>
      }
    >
      <form onSubmit={submit} noValidate>
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        <label className="field">
          <span>Username</span>
          <input
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            autoComplete="username"
            autoFocus
          />
        </label>
        <PasswordField
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          autoComplete="current-password"
        />
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </AuthShell>
  );
}

export function RegisterPage() {
  const { register } = useAuth();
  const ui = useUi();
  const [form, setForm] = useState({ username: "", password: "", confirm: "" });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    const errs = {};
    if (!/^[A-Za-z0-9_.-]{3,50}$/.test(form.username))
      errs.username = "3–50 characters: letters, numbers, dot, dash or underscore.";
    if (form.password.length < 8) errs.password = "Password must be at least 8 characters.";
    if (form.password !== form.confirm) errs.confirm = "Passwords do not match.";
    setErrors(errs);
    if (Object.keys(errs).length) return;
    setBusy(true);
    try {
      const user = await register(form.username, form.password);
      ui.success(`Account created. Welcome, ${user.username}!`);
      navigate("/");
    } catch (err) {
      setError(getErrorMessage(err));
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="Create your account"
      subtitle="Join your community and start voting."
      footer={
        <>
          Already registered? <button className="link-btn" onClick={() => navigate("/login")}>Sign in</button>
        </>
      }
    >
      <form onSubmit={submit} noValidate>
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        <label className="field">
          <span>Username</span>
          <input
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            autoComplete="username"
            autoFocus
          />
          {errors.username && <em className="field-error">{errors.username}</em>}
        </label>
        <PasswordField
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          autoComplete="new-password"
        />
        {errors.password && <em className="field-error under">{errors.password}</em>}
        <PasswordField
          label="Confirm password"
          value={form.confirm}
          onChange={(e) => setForm({ ...form, confirm: e.target.value })}
          autoComplete="new-password"
        />
        {errors.confirm && <em className="field-error under">{errors.confirm}</em>}
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>
    </AuthShell>
  );
}
