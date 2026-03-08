import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
  createStrategy: vi.fn(),
  updateStrategy: vi.fn(),
  createTemplateBacktest: vi.fn(),
  getBacktest: vi.fn(),
  marketPulse: vi.fn(),
  marketSymbols: vi.fn(),
  riskControls: vi.fn(),
  updateRiskControls: vi.fn(),
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

function buildChartResult() {
  return {
    id: "bt-1",
    strategyId: "strategy-1",
    strategyKind: "template" as const,
    strategyName: "Signal Run",
    exchangeId: "backpack",
    marketType: "perp" as const,
    symbol: "BTC_USDC_PERP",
    interval: "1h",
    startTime: 1709251200,
    endTime: 1709337600,
    priceSource: "last" as const,
    chartPriceSource: "last" as const,
    feeBps: 2,
    slippageBps: 3,
    status: "completed" as const,
    createdAt: "2026-03-08T10:00:00Z",
    completedAt: "2026-03-08T10:00:05Z",
    totalReturn: 6.4,
    maxDrawdown: -2.1,
    sharpe: 1.2,
    winRate: 58,
    candles: [
      { timestamp: "2026-03-01T00:00:00Z", open: 100, high: 106, low: 98, close: 104, volume: 12 },
      { timestamp: "2026-03-01T01:00:00Z", open: 104, high: 108, low: 102, close: 107, volume: 10 },
      { timestamp: "2026-03-01T02:00:00Z", open: 107, high: 110, low: 105, close: 106, volume: 13 },
      { timestamp: "2026-03-01T03:00:00Z", open: 106, high: 112, low: 104, close: 111, volume: 11 },
      { timestamp: "2026-03-01T04:00:00Z", open: 111, high: 114, low: 109, close: 110, volume: 14 },
      { timestamp: "2026-03-01T05:00:00Z", open: 110, high: 116, low: 108, close: 115, volume: 16 },
    ],
    tradeMarkers: [
      {
        id: "marker-open",
        timestamp: "2026-03-01T00:00:00Z",
        candleTimestamp: "2026-03-01T00:00:00Z",
        action: "open" as const,
        type: "open" as const,
        side: "long" as const,
        price: 101,
        qty: 1,
        reason: "signal",
        relatedTradeId: "trade-1",
        relatedOrderId: "order-1",
      },
    ],
    equityCurve: [
      { timestamp: "2026-03-01T00:00:00Z", equity: 100 },
      { timestamp: "2026-03-01T01:00:00Z", equity: 101 },
      { timestamp: "2026-03-01T02:00:00Z", equity: 103 },
      { timestamp: "2026-03-01T03:00:00Z", equity: 104 },
      { timestamp: "2026-03-01T04:00:00Z", equity: 106 },
      { timestamp: "2026-03-01T05:00:00Z", equity: 107 },
    ],
    chartWarnings: [],
  };
}

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
          exchangeId: "backpack",
          marketType: "perp",
          symbol: "",
          interval: "",
          startTime: 0,
          endTime: 0,
          priceSource: "mark",
          chartPriceSource: "mark",
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
          chartWarnings: [],
        }}
      />,
    );

    expect(screen.getByText("No candles available")).toBeInTheDocument();
  });

  it("renders chart markers when candle timestamps are present", () => {
    const { container } = render(<CandlestickChart result={buildChartResult()} />);

    expect(container.querySelectorAll("path")).toHaveLength(1);
    expect(screen.getByText("OPEN")).toBeInTheDocument();
  });

  it("does not pan on drag without Space, but Space plus drag shifts the viewport", () => {
    render(<CandlestickChart result={buildChartResult()} />);

    const surface = screen.getByTestId("candlestick-chart-surface");
    Object.defineProperty(surface, "getBoundingClientRect", {
      value: () => ({
        left: 0,
        top: 0,
        width: 960,
        height: 560,
        right: 960,
        bottom: 560,
        x: 0,
        y: 0,
        toJSON: () => ({}),
      }),
    });

    fireEvent.wheel(surface, { deltaY: -100 });
    expect(screen.getByText(/View:/)).toHaveTextContent("2.0x / 3 candles");
    expect(screen.getByText("03-01 00:00")).toBeInTheDocument();
    expect(screen.getByText("03-01 02:00")).toBeInTheDocument();

    fireEvent.mouseDown(surface, { clientX: 420 });
    fireEvent.mouseMove(surface, { clientX: 40 });
    fireEvent.mouseUp(surface);

    expect(screen.getByText("03-01 00:00")).toBeInTheDocument();
    expect(screen.getByText("03-01 02:00")).toBeInTheDocument();

    surface.focus();
    fireEvent.keyDown(surface, { code: "Space" });
    fireEvent.mouseDown(surface, { clientX: 420 });
    fireEvent.mouseMove(surface, { clientX: 40 });
    fireEvent.mouseUp(surface);

    expect(screen.getByText("03-01 02:00")).toBeInTheDocument();
    expect(screen.getByText("03-01 03:00")).toBeInTheDocument();
    expect(screen.getByText("03-01 04:00")).toBeInTheDocument();
    expect(screen.queryByText("03-01 00:00")).not.toBeInTheDocument();
    expect(screen.queryByText("03-01 01:00")).not.toBeInTheDocument();

    fireEvent.keyUp(surface, { code: "Space" });
    fireEvent.mouseDown(surface, { clientX: 420 });
    fireEvent.mouseMove(surface, { clientX: 40 });
    fireEvent.mouseUp(surface);

    expect(screen.getByText("03-01 02:00")).toBeInTheDocument();
    expect(screen.getByText("03-01 03:00")).toBeInTheDocument();
  });

  it("preserves shift-drag box zoom after the pan interaction change", () => {
    render(<CandlestickChart result={buildChartResult()} />);

    const surface = screen.getByTestId("candlestick-chart-surface");
    Object.defineProperty(surface, "getBoundingClientRect", {
      value: () => ({
        left: 0,
        top: 0,
        width: 960,
        height: 560,
        right: 960,
        bottom: 560,
        x: 0,
        y: 0,
        toJSON: () => ({}),
      }),
    });

    fireEvent.mouseDown(surface, { clientX: 260, shiftKey: true });
    fireEvent.mouseMove(surface, { clientX: 500, shiftKey: true });
    fireEvent.mouseUp(surface);

    expect(screen.getByText(/View:/)).not.toHaveTextContent("1.0x / 6 candles");
  });
});

describe("async admin pages", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiMock.exchangeAccounts.mockResolvedValue([]);
    apiMock.marketSymbols.mockResolvedValue(["BTC_USDC_PERP"]);
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
    apiMock.strategies.mockResolvedValue([
      {
        id: "strategy-1",
        name: "Flat Run",
        kind: "template",
        description: "Demo strategy",
        market: "BTC_USDC_PERP",
        accountId: "acct_001",
        runtime: "paper",
        status: "healthy",
        lastBacktest: "",
        sharpe: 0,
        priceSource: "index",
        parameters: {},
      },
    ]);
    apiMock.marketSymbols.mockResolvedValue(["BTC_USDC_PERP"]);
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
      exchangeId: "backpack",
      marketType: "perp",
      symbol: "BTC_USDC_PERP",
      interval: "1h",
      startTime: 1709251200,
      endTime: 1709337600,
      priceSource: "index",
      chartPriceSource: "index",
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
      chartWarnings: [],
    });

    render(<BacktestsPage />);

    fireEvent.click(await screen.findByText("Run backtest"));

    await waitFor(() =>
      expect(screen.getByText("No trade markers returned")).toBeInTheDocument(),
    );
    expect(screen.getByText("No candles available")).toBeInTheDocument();
  });
});
