import { FormEvent, useState } from "react";

type AdminTokenGateProps = {
  errorMessage?: string | null;
  onSubmit: (token: string) => void;
};

export function AdminTokenGate({ errorMessage, onSubmit }: AdminTokenGateProps) {
  const [token, setToken] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedToken = token.trim();
    if (!trimmedToken) {
      return;
    }

    onSubmit(trimmedToken);
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="relative mx-auto flex min-h-[calc(100vh-4rem)] max-w-4xl items-center justify-center">
        <div className="grid w-full gap-6 rounded-3xl border border-gray-100 bg-white p-6 shadow-sm lg:grid-cols-[1.2fr_0.8fr] lg:p-10">
          <section className="rounded-2xl border border-gray-100 bg-gray-50 p-6">
            <p className="text-[10px] font-semibold uppercase tracking-[0.38em] text-gray-400">Admin auth boundary</p>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-gray-900">Trader Console</h1>
            <p className="mt-4 max-w-xl text-sm leading-6 text-gray-600">
              Enter the shared admin API token before the console mounts. The token is kept only in
              this browser session and is attached to every backend `/api` request.
            </p>
            <div className="mt-8 grid gap-2 text-sm text-gray-600">
              <div className="rounded-xl border border-gray-100 bg-white px-4 py-3">
                Backend rejects missing tokens with `401`.
              </div>
              <div className="rounded-xl border border-gray-100 bg-white px-4 py-3">
                Backend rejects mismatched tokens with `403`.
              </div>
            </div>
          </section>

          <form
            className="rounded-2xl border border-gray-100 bg-white p-6"
            onSubmit={handleSubmit}
          >
            <label className="block text-[10px] font-semibold uppercase tracking-[0.3em] text-gray-400" htmlFor="admin-token">
              X-Admin-Token
            </label>
            <input
              id="admin-token"
              type="password"
              autoComplete="off"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              className="mt-3 w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 outline-none transition focus:border-gray-900"
              placeholder="Enter admin API token"
            />
            {errorMessage ? (
              <p className="mt-3 rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-700">
                {errorMessage}
              </p>
            ) : null}
            <button
              type="submit"
              className="mt-4 w-full rounded-xl bg-gray-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-gray-700"
            >
              Unlock admin shell
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
