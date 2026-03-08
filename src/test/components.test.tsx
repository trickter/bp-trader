import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CandlestickChart } from "../components/candlestick-chart";
import { DataTable, type Column } from "../components/data-table";
import { BacktestsPage } from "../pages/backtests-page";
import { MarketPulsePage } from "../pages/market-pulse-page";
import { ProfilePage } from "../pages/profile-page";
import { StrategiesPage } from "../pages/strategies-page";

const apiMock = vi.hoisted(() => ({
  profileSummary: vi.fn(),
  profileAssets: vi.fn(),
  profilePositions: vi.fn(),
  accountEvents: vi.fn(),
  strategies: vi.fn(),
  createTemplateBacktest: vi.fn(),
  getBacktest: vi.fn(),
  marketPulse: vi.fn(),
  exchangeAccounts: vi.fn(),
  agentContext: vi.fn(),
}));

vi.mock("../lib/api", () => ({
  api: apiMock,
}));

type TableRow = {
  id: string;
  symbol: string;
};

const columns: Column<TableRow>[] = [
  { key: "symbol", label: "Symbol", render: (item) => item.symbol },
];

describe("DataTable", () => {
  it("renders table rows using caller-supplied row keys", () => {
    render(
      <DataTable
        rows={[
          { id: "sol", symbol: "SOL-PERP" },
          { id: "btc", symbol: "BTC-PERP" },
        ]}
        getRowKey={(row) => row.id}
        columns={columns}
      />,
    );

    expect(screen.getByText("SOL-PERP")).toBeInTheDocument();
    expect(screen.getByText("BTC-PERP")).toBeInTheDocument();
  });

  it("renders configured empty text when no rows exist", () => {
    render(<DataTable rows={[]} getRowKey={() => ""} columns={columns} emptyText="No rows yet" />);

    expect(screen.getByText("No rows yet")).toBeInTheDocument();
  });
});

describe("CandlestickChart", () => {
  it("renders a controlled empty state when no candles are available", () => {
    render(
      <CandlestickChart
        result={{
          id: "bt-empty",
          strategyId: "",
          strategyKind: "template",
          strategyName: "Empty Run",
          symbol: "",
          interval: "",
          startTime: 0,
          endTime: 0,
          priceSource: "mark",
          feeBps: 0,
          slippageBps: 0,
          status: "completed",
          createdAt: "",
          completedAt: "",
          totalReturn: 0,
          maxDrawdown: 0,
          sharpe: 0,
          winRate: 0,
          candles: [],
          tradeMarkers: [],
          equityCurve: [],
        }}
      />,
    );

    expect(screen.getByText("No candles available")).toBeInTheDocument();
  });

  it("renders chart markers when candle timestamps are present", () => {
    const { container } = render(
      <CandlestickChart
        result={{
          id: "bt-1",
          strategyId: "strategy-1",
          strategyKind: "template",
          strategyName: "Signal Run",
          symbol: "BTC_USDC_PERP",
          interval: "1h",
          startTime: 1709251200,
          endTime: 1709337600,
          priceSource: "last",
          feeBps: 2,
          slippageBps: 3,
          status: "completed",
          createdAt: "2026-03-08T10:00:00Z",
          completedAt: "2026-03-08T10:00:05Z",
          totalReturn: 6.4,
          maxDrawdown: -2.1,
          sharpe: 1.2,
          winRate: 58,
          candles: [
            {
              timestamp: "2026-03-01T00:00:00Z",
              open: 100,
              high: 106,
              low: 98,
              close: 104,
              volume: 12,
            },
          ],
          tradeMarkers: [
            {
              id: "marker-open",
              timestamp: "2026-03-01T00:00:00Z",
              type: "open",
              side: "long",
              price: 101,
              reason: "signal",
            },
          ],
          equityCurve: [],
        }}
      />,
    );

    expect(container.querySelectorAll("circle")).toHaveLength(1);
    expect(screen.getByText("OPEN")).toBeInTheDocument();
  });
});

describe("async admin pages", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiMock.exchangeAccounts.mockResolvedValue([]);
    apiMock.agentContext.mockResolvedValue({
      mode: "admin",
      accountMode: "mock",
      availableCapabilities: [],
      capabilities: [],
      domainVocabulary: [],
      resources: {},
    });
  });

  it("shows a visible error state instead of a false empty table on profile failures", async () => {
    apiMock.profileSummary.mockRejectedValue(new Error("Profile summary unavailable"));
    apiMock.profileAssets.mockResolvedValue([]);
    apiMock.profilePositions.mockResolvedValue([]);
    apiMock.accountEvents.mockResolvedValue([]);

    render(<ProfilePage />);

    expect(await screen.findAllByText("Profile summary unavailable")).toHaveLength(2);
  });

  it("shows loading and then empty states for strategies", async () => {
    let resolveStrategies: (value: unknown) => void = () => undefined;
    apiMock.strategies.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveStrategies = resolve;
        }),
    );

    render(<StrategiesPage />);

    expect(document.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);

    resolveStrategies([]);

    await waitFor(() =>
      expect(screen.getByText("No strategies configured")).toBeInTheDocument(),
    );
  });

  it("shows a real error state for market pulse fetch failures", async () => {
    apiMock.marketPulse.mockRejectedValue(new Error("Upstream market pulse timeout"));

    render(<MarketPulsePage />);

    await waitFor(() =>
      expect(screen.getByText("Market pulse failed to load")).toBeInTheDocument(),
    );
    expect(screen.getByText("Upstream market pulse timeout")).toBeInTheDocument();
  });

  it("shows marker table empty state when a backtest returns zero trades", async () => {
    apiMock.createTemplateBacktest.mockResolvedValue({
      id: "bt-2",
      strategyId: "strategy-1",
      strategyKind: "template",
      status: "completed",
      createdAt: "2026-03-08T10:00:00Z",
      resultPath: "/api/backtests/bt-2",
      pollAfterMs: 0,
      demoMode: true,
    });
    apiMock.getBacktest.mockResolvedValue({
      id: "bt-2",
      strategyId: "strategy-1",
      strategyKind: "template",
      strategyName: "Flat Run",
      symbol: "BTC_USDC_PERP",
      interval: "1h",
      startTime: 1709251200,
      endTime: 1709337600,
      priceSource: "index",
      feeBps: 2,
      slippageBps: 3,
      status: "completed",
      createdAt: "2026-03-08T10:00:00Z",
      completedAt: "2026-03-08T10:00:05Z",
      totalReturn: 0,
      maxDrawdown: 0,
      sharpe: 0,
      winRate: 0,
      candles: [],
      tradeMarkers: [],
      equityCurve: [],
    });

    render(<BacktestsPage />);

    await waitFor(() =>
      expect(screen.getByText("No trade markers returned")).toBeInTheDocument(),
    );
    expect(screen.getByText("No candles available")).toBeInTheDocument();
  });
});
