import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

/** Catches render errors so a crash shows a readable panel, not a blank/red overlay. */
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  render() {
    if (this.state.error) {
      return (
        <div style={{
          minHeight: "100vh", display: "grid", placeItems: "center",
          background: "#05070c", color: "#e7edf7", fontFamily: "system-ui, sans-serif", padding: 24,
        }}>
          <div style={{ maxWidth: 560 }}>
            <h1 style={{ fontSize: 18, marginBottom: 8 }}>Algo ha fallado al renderizar</h1>
            <pre style={{
              whiteSpace: "pre-wrap", fontSize: 12, color: "#fb5e7e",
              background: "rgba(255,255,255,0.04)", padding: 12, borderRadius: 8,
            }}>{String(this.state.error?.message ?? this.state.error)}</pre>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
