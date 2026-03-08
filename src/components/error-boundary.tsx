import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex min-h-[400px] items-center justify-center p-8">
            <div className="text-center">
              <h2 className="mb-2 text-xl font-bold text-red-600">
                Something went wrong
              </h2>
              <p className="text-gray-600">
                {this.state.error?.message || "An unexpected error occurred"}
              </p>
              <button
                onClick={() => this.setState({ hasError: false, error: undefined })}
                className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
              >
                Try again
              </button>
            </div>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
