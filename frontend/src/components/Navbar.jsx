import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useUi } from "../context/UiContext";
import { navigate } from "../router";

export default function Navbar({ path }) {
  const { user, isAdmin, logout } = useAuth();
  const ui = useUi();
  const [open, setOpen] = useState(false);

  const go = (to) => {
    setOpen(false);
    navigate(to);
  };
  const handleLogout = async () => {
    const ok = await ui.confirm({
      title: "Sign out?",
      message: "You will need to sign in again to vote.",
      confirmText: "Sign out",
    });
    if (!ok) return;
    await logout();
    setOpen(false);
    navigate("/login");
    ui.success("You have been signed out");
  };
  const link = (to, label) => (
    <button className={`nav-link ${path === to ? "active" : ""}`} onClick={() => go(to)}>
      {label}
    </button>
  );

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <button className="brand" onClick={() => go(user ? "/" : "/login")}>
          <span className="brand-mark">🗳</span> CommunityVote
        </button>
        {user && (
          <>
            <button className="menu-toggle" onClick={() => setOpen(!open)} aria-label="Menu" aria-expanded={open}>
              {open ? "✕" : "☰"}
            </button>
            <nav className={`nav ${open ? "open" : ""}`}>
              {link("/", "Dashboard")}
              {isAdmin && link("/admin", "Admin")}
              <div className="nav-user">
                <span className="avatar">{user.username[0].toUpperCase()}</span>
                <span className="nav-username">{user.username}</span>
                <span className={`role role-${user.role.toLowerCase()}`}>{user.role}</span>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={handleLogout}>Sign out</button>
            </nav>
          </>
        )}
      </div>
    </header>
  );
}
