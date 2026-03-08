import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../lib/api";

describe("api module", () => {
  beforeEach(() => {
    vi.mocked(fetch).mockReset();
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response);
  });

  it("exposes the admin data readers", () => {
    expect(typeof api.profileSummary).toBe("function");
    expect(typeof api.profileAssets).toBe("function");
    expect(typeof api.profilePositions).toBe("function");
    expect(typeof api.accountEvents).toBe("function");
    expect(typeof api.marketPulse).toBe("function");
    expect(typeof api.exchangeAccounts).toBe("function");
    expect(typeof api.agentContext).toBe("function");
  });

  it("exposes explicit backtest lifecycle methods", () => {
    expect(typeof api.createTemplateBacktest).toBe("function");
    expect(typeof api.createScriptBacktest).toBe("function");
    expect(typeof api.getBacktest).toBe("function");
  });

  it("posts json for backtest creation", async () => {
    await api.createTemplateBacktest("strat_001", {
      symbol: "BTC_USDC_PERP",
      interval: "1d",
      startTime: 1740787200,
      endTime: 1741305600,
      priceSource: "last",
      feeBps: 2,
      slippageBps: 4,
    });

    expect(fetch).toHaveBeenCalledTimes(1);
    const [, init] = vi.mocked(fetch).mock.calls[0];
    expect(init?.method).toBe("POST");
    expect(init?.body).toContain("\"symbol\":\"BTC_USDC_PERP\"");
  });
});
