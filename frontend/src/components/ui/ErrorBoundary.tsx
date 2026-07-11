import { Component, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { TriangleAlert } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}
interface State {
  error: Error | null;
}

/** Catches render errors so a crash shows a message instead of a blank screen. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  render() {
    if (this.state.error) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="mx-auto mt-10 max-w-lg">
          <div className="card flex flex-col items-center gap-3 p-8 text-center">
            <TriangleAlert className="text-risk-high" size={26} />
            <p className="text-sm font-medium text-white/80">
              Something went wrong rendering this view.
            </p>
            <pre className="max-w-full overflow-auto rounded-lg bg-ink-900/70 p-3 text-left text-xs text-risk-high">
              {this.state.error.message}
            </pre>
            <Link to="/" className="text-xs text-brand-400 hover:underline">
              ← Back to dashboard
            </Link>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
