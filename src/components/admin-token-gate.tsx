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
    <div className="min-h-screen bg-[#020817] px-4 py-8 text-white">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top_left,rgba(56,189,248,0.18),transparent_24%),radial-gradient(circle_at_bottom,rgba(14,165,233,0.1),transparent_28%)]" />
      <div className="relative mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl items-center justify-center">
        <div className="grid w-full gap-6 rounded-[32px] border border-white/10 bg-[linear-gradient(180deg,rgba(6,17,38,0.92),rgba(5,13,28,0.98))] p-6 shadow-[0_20px_80px_rgba(0,0,0,0.45)] lg:grid-cols-[1.2fr_0.8fr] lg:p-10">
          <section className="rounded-[28px] border border-cyan-400/10 bg-cyan-400/5 p-6">
            <p className="text-[11px] uppercase tracking-[0.38em] text-cyan-200/60">Admin auth boundary</p>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-white">Trader Console</h1>
            <p className="mt-4 max-w-xl text-sm leading-6 text-slate-300">
              Enter the shared admin API token before the console mounts. The token is kept only in
              this browser session and is attached to every backend `/api` request.
            </p>
            <div className="mt-8 grid gap-3 text-sm text-slate-300">
              <div className="rounded-2xl border border-white/8 bg-white/5 px-4 py-3">
                Backend rejects missing tokens with `401`.
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/5 px-4 py-3">
                Backend rejects mismatched tokens with `403`.
              </div>
            </div>
          </section>

          <form
            className="rounded-[28px] border border-white/8 bg-black/20 p-6"
            onSubmit={handleSubmit}
          >
            <label className="block text-[11px] uppercase tracking-[0.3em] text-slate-400" htmlFor="admin-token">
              X-Admin-Token
            </label>
            <input
              id="admin-token"
              type="password"
              autoComplete="off"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              className="mt-3 w-full rounded-2xl border border-white/10 bg-slate-950/80 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/60"
              placeholder="Enter admin API token"
            />
            {errorMessage ? (
              <p className="mt-3 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
                {errorMessage}
              </p>
            ) : null}
            <button
              type="submit"
              className="mt-4 w-full rounded-2xl bg-cyan-300 px-4 py-3 text-sm font-medium text-slate-950 transition hover:bg-cyan-200"
            >
              Unlock admin shell
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
