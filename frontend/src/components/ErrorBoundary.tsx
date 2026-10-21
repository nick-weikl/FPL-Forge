import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";
export default class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Application rendering failed", error, info.componentStack);
  }
  render() {
    if (this.state.failed)
      return (
        <main className="app-main">
          <section className="forge-state forge-state--error" role="alert">
            <h1>Something went wrong</h1>
            <p>Reload to try again. Your saved browser data will be kept.</p>
            <button className="forge-button" onClick={() => window.location.reload()}>
              Reload app
            </button>
          </section>
        </main>
      );
    return this.props.children;
  }
}
