import { useEffect } from "react";
import { useAuth } from "./context/AuthContext";
import { useUi } from "./context/UiContext";
import Navbar from "./components/Navbar";
import { Spinner } from "./components/common";
import { LoginPage, RegisterPage } from "./pages/AuthPages";
import Dashboard from "./pages/Dashboard";
import ProposalDetail from "./pages/ProposalDetail";
import AdminDashboard from "./pages/AdminDashboard";
import { navigate, useRoute } from "./router";

export default function App() {
  const { user, loading, isAdmin } = useAuth();
  const ui = useUi();
  const { path, parts } = useRoute();
  const isAuthPage = path === "/login" || path === "/register";
  const forbiddenAdmin = !!user && !isAdmin && parts[0] === "admin";

  // Route guards (the backend enforces the same rules independently)
  useEffect(() => {
    if (loading) return;
    if (!user && !isAuthPage) navigate("/login");
    else if (user && isAuthPage) navigate("/");
    else if (forbiddenAdmin) {
      ui.error("Admin access required (403).");
      navigate("/");
    }
  }, [user, loading, isAuthPage, forbiddenAdmin, ui]);

  // Session expiry notice
  useEffect(() => {
    const onExpired = () => ui.error("Your session expired. Please sign in again.");
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, [ui]);

  if (loading) return <Spinner label="Restoring your session…" />;

  let page;
  if (!user) page = path === "/register" ? <RegisterPage /> : <LoginPage />;
  else if (parts[0] === "admin") page = isAdmin ? <AdminDashboard /> : null;
  else if (parts[0] === "proposal" && parts[1]) page = <ProposalDetail key={parts[1]} id={parts[1]} />;
  else page = <Dashboard />;

  return (
    <>
      <Navbar path={path} />
      <main>{page}</main>
      <footer className="footer">Community Digital Voting System · Secure, transparent community decisions</footer>
    </>
  );
}
