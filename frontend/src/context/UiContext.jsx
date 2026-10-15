import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";

const UiContext = createContext(null);
// eslint-disable-next-line react-refresh/only-export-components
export const useUi = () => useContext(UiContext);

/** Provides toast notifications and a promise-based confirmation dialog. */
export function UiProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const [dialog, setDialog] = useState(null);
  const idRef = useRef(0);
  const resolver = useRef(null);

  const dismiss = useCallback((id) => setToasts((t) => t.filter((x) => x.id !== id)), []);

  const notify = useCallback(
    (message, type = "success") => {
      const id = ++idRef.current;
      setToasts((t) => [...t, { id, message, type }]);
      setTimeout(() => dismiss(id), type === "error" ? 6000 : 3500);
    },
    [dismiss]
  );

  const confirm = useCallback(
    (opts) =>
      new Promise((resolve) => {
        resolver.current = resolve;
        setDialog(opts);
      }),
    []
  );

  const answer = (value) => {
    resolver.current?.(value);
    setDialog(null);
  };

  const value = useMemo(
    () => ({
      success: (m) => notify(m, "success"),
      error: (m) => notify(m, "error"),
      info: (m) => notify(m, "info"),
      confirm,
    }),
    [notify, confirm]
  );

  return (
    <UiContext.Provider value={value}>
      {children}
      <div className="toast-stack" role="status" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.type}`}>
            <span className="toast-icon">{t.type === "error" ? "⚠" : t.type === "info" ? "ℹ" : "✓"}</span>
            <span>{t.message}</span>
            <button className="toast-close" onClick={() => dismiss(t.id)} aria-label="Dismiss">
              ×
            </button>
          </div>
        ))}
      </div>
      {dialog && (
        <div className="overlay" onClick={() => answer(false)}>
          <div
            className="dialog"
            role="alertdialog"
            aria-modal="true"
            onClick={(e) => e.stopPropagation()}
          >
            <h3>{dialog.title}</h3>
            <p>{dialog.message}</p>
            <div className="dialog-actions">
              <button className="btn btn-ghost" onClick={() => answer(false)}>
                Cancel
              </button>
              <button
                className={`btn ${dialog.danger ? "btn-danger" : "btn-primary"}`}
                onClick={() => answer(true)}
                autoFocus
              >
                {dialog.confirmText || "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}
    </UiContext.Provider>
  );
}
