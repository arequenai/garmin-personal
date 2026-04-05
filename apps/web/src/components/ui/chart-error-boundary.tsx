"use client";

import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

const defaultFallback = (
  <div className="flex items-center justify-center rounded-xl border border-whoop-border bg-whoop-card p-6">
    <p className="text-xs text-whoop-text-muted">Chart failed to render</p>
  </div>
);

export class ChartErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    console.error("[ChartErrorBoundary]", error);
  }

  render() {
    if (this.state.hasError) return this.props.fallback ?? defaultFallback;
    return this.props.children;
  }
}
