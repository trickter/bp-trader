import { useEffect, useMemo, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type MouseEvent, type WheelEvent } from "react";

import type { BacktestResult, Candle, TradeMarker } from "../lib/types";
import { formatCurrency } from "../lib/utils";

const MARKER_COLORS: Record<string, string> = {
  open: "#38bdf8",
  add: "#14b8a6",
  reduce: "#f59e0b",
  close: "#fb7185",
  stop: "#ef4444",
  take_profit: "#a3e635",
};

function formatAxisLabel(timestamp: string) {
  return timestamp.slice(5, 16).replace("T", " ");
}

function resolveMarkerIndex(candles: Candle[], marker: TradeMarker) {
  if (!candles.length) {
    return null;
  }

  const explicit = marker.candleTimestamp
    ? candles.findIndex((candle) => candle.timestamp === marker.candleTimestamp)
    : -1;
  if (explicit >= 0) {
    return explicit;
  }

  const markerTime = Date.parse(marker.timestamp);
  if (Number.isNaN(markerTime)) {
    return null;
  }

  for (let index = 0; index < candles.length; index += 1) {
    const current = Date.parse(candles[index].timestamp);
    const next = index < candles.length - 1 ? Date.parse(candles[index + 1].timestamp) : Number.POSITIVE_INFINITY;
    if (markerTime >= current && markerTime < next) {
      return index;
    }
  }

  return null;
}

function buildChartWarnings(result: BacktestResult, markerIndexes: Map<string, number | null>) {
  const warnings = [...result.chartWarnings];

  if (result.priceSource !== result.chartPriceSource) {
    warnings.push("Backtest price source and chart price source are inconsistent.");
  }

  if (result.candles.length > 0) {
    const minPrice = Math.min(...result.candles.map((candle) => candle.low));
    const maxPrice = Math.max(...result.candles.map((candle) => candle.high));
    for (const marker of result.tradeMarkers) {
      if (markerIndexes.get(marker.id) == null) {
        warnings.push(`Marker ${marker.id} does not map to any returned candle.`);
      }
      if (marker.price < minPrice || marker.price > maxPrice) {
        warnings.push(`Marker ${marker.id} price falls outside the candle price range.`);
      }
    }
  }

  return Array.from(new Set(warnings));
}

function buildEquityY(equityCurve: BacktestResult["equityCurve"], top: number, bottom: number) {
  const values = equityCurve.map((point) => point.equity);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return (equity: number) => {
    const ratio = (equity - min) / span;
    return bottom - ratio * (bottom - top);
  };
}

export function CandlestickChart({ result }: { result: BacktestResult }) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [selectedMarkerId, setSelectedMarkerId] = useState<string | null>(null);
  const [showEquityOverlay, setShowEquityOverlay] = useState(true);
  const [showBenchmarkOverlay, setShowBenchmarkOverlay] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState(0);
  const [isPanning, setIsPanning] = useState(false);
  const [spacePanActive, setSpacePanActive] = useState(false);
  const [chartIsActive, setChartIsActive] = useState(false);
  const [selectionRange, setSelectionRange] = useState<{
    startX: number;
    currentX: number;
    startIndex: number;
    currentIndex: number;
  } | null>(null);
  const dragStartXRef = useRef<number | null>(null);
  const chartContainerRef = useRef<HTMLDivElement | null>(null);

  const width = 960;
  const height = 560;
  const leftPadding = 78;
  const rightPadding = 28;
  const topPadding = 28;
  const bottomPadding = 64;
  const usableHeight = height - topPadding - bottomPadding;
  const usableWidth = width - leftPadding - rightPadding;

  const markerIndexes = useMemo(() => {
    const mapping = new Map<string, number | null>();
    for (const marker of result.tradeMarkers) {
      mapping.set(marker.id, resolveMarkerIndex(result.candles, marker));
    }
    return mapping;
  }, [result.candles, result.tradeMarkers]);

  const chartWarnings = useMemo(
    () => buildChartWarnings(result, markerIndexes),
    [markerIndexes, result],
  );
  const visibleCandles = useMemo(() => {
    if (result.candles.length === 0) {
      return [];
    }
    const visibleCount = Math.max(3, Math.ceil(result.candles.length / zoomLevel));
    const maxStart = Math.max(0, result.candles.length - visibleCount);
    const start = Math.min(panOffset, maxStart);
    return result.candles.slice(start, start + visibleCount);
  }, [panOffset, result.candles, zoomLevel]);
  const visibleStartIndex = useMemo(() => {
    if (result.candles.length === 0) {
      return 0;
    }
    const visibleCount = Math.max(3, Math.ceil(result.candles.length / zoomLevel));
    const maxStart = Math.max(0, result.candles.length - visibleCount);
    return Math.min(panOffset, maxStart);
  }, [panOffset, result.candles.length, zoomLevel]);
  const visibleEndIndex = visibleStartIndex + visibleCandles.length - 1;
  const visibleCount = visibleCandles.length;
  const maxPanStart = Math.max(0, result.candles.length - visibleCount);
  const benchmarkCurve = useMemo(() => {
    if (result.candles.length === 0) {
      return [];
    }
    const baseline = result.candles[0].close || 1;
    return result.candles.map((candle) => ({
      timestamp: candle.timestamp,
      equity: Number((((candle.close / baseline) - 1) * 100 + 100).toFixed(2)),
    }));
  }, [result.candles]);
  const markerLanes = useMemo(() => {
    const counts = new Map<number, number>();
    const lanes = new Map<string, number>();
    for (const marker of result.tradeMarkers) {
      const index = markerIndexes.get(marker.id);
      if (index == null || index < visibleStartIndex || index > visibleEndIndex) {
        continue;
      }
      const localIndex = index - visibleStartIndex;
      const lane = counts.get(localIndex) ?? 0;
      lanes.set(marker.id, lane);
      counts.set(localIndex, lane + 1);
    }
    return lanes;
  }, [markerIndexes, result.tradeMarkers, visibleEndIndex, visibleStartIndex]);
  const selectedMarker =
    result.tradeMarkers.find((marker) => marker.id === selectedMarkerId) ?? result.tradeMarkers[0] ?? null;
  const lifecycleGroupByMarkerId = useMemo(() => {
    const groups = new Map<string, string>();
    let currentGroup = 0;
    const ordered = [...result.tradeMarkers].sort((left, right) => {
      const leftIndex = markerIndexes.get(left.id) ?? Number.MAX_SAFE_INTEGER;
      const rightIndex = markerIndexes.get(right.id) ?? Number.MAX_SAFE_INTEGER;
      if (leftIndex !== rightIndex) {
        return leftIndex - rightIndex;
      }
      return Date.parse(left.timestamp) - Date.parse(right.timestamp);
    });

    for (const marker of ordered) {
      if (marker.action === "open") {
        currentGroup += 1;
      }
      const groupId = `lifecycle-${Math.max(currentGroup, 1)}`;
      groups.set(marker.id, groupId);
      if (marker.action === "close" || marker.action === "stop" || marker.action === "take_profit") {
        currentGroup += 1;
      }
    }

    return groups;
  }, [markerIndexes, result.tradeMarkers]);
  const selectedLifecycleId = selectedMarker ? lifecycleGroupByMarkerId.get(selectedMarker.id) ?? null : null;
  const selectedLifecycleMarkers = selectedLifecycleId
    ? result.tradeMarkers.filter((marker) => lifecycleGroupByMarkerId.get(marker.id) === selectedLifecycleId)
    : [];

  if (visibleCandles.length === 0) {
    return (
      <div className="overflow-hidden rounded-[28px] border border-cyan-400/10 bg-[radial-gradient(circle_at_top,rgba(55,189,248,0.08),transparent_34%),linear-gradient(180deg,rgba(4,11,30,0.94),rgba(5,11,24,1))] p-4">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.3em] text-cyan-200/50">Backtest tape</p>
            <h3 className="text-lg font-semibold text-white">{result.strategyName || "Backtest result"}</h3>
          </div>
          <div className="text-right text-xs text-slate-400">
            <p>Price source: {result.priceSource.toUpperCase()}</p>
            <p>0 lifecycle markers</p>
          </div>
        </div>

        <div className="flex h-72 items-center justify-center rounded-[24px] border border-dashed border-white/10 bg-black/10 text-center">
          <div>
            <p className="text-base font-semibold text-white">No candles available</p>
            <p className="mt-2 text-sm text-slate-400">
              The selected backtest returned zero bars, so trade markers cannot be projected.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const prices = visibleCandles.flatMap((candle) => [candle.low, candle.high, candle.open, candle.close]);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceSpan = maxPrice - minPrice || 1;
  const pricePadding = priceSpan * 0.12;
  const chartMin = minPrice - pricePadding;
  const chartMax = maxPrice + pricePadding;
  const candleSlotWidth = usableWidth / visibleCandles.length;
  const yAxisLevels = Array.from({ length: 5 }, (_, index) => chartMax - ((chartMax - chartMin) / 4) * index);
  const hoveredCandle = hoveredIndex == null ? null : visibleCandles[hoveredIndex];
  const visibleTradeMarkers = result.tradeMarkers.filter((marker) => {
    const index = markerIndexes.get(marker.id);
    return index != null && index >= visibleStartIndex && index <= visibleEndIndex;
  });
  const visibleMarkerCounts = useMemo(() => {
    const counts = new Map<number, number>();
    for (const marker of visibleTradeMarkers) {
      const absoluteIndex = markerIndexes.get(marker.id);
      if (absoluteIndex == null) {
        continue;
      }
      const localIndex = absoluteIndex - visibleStartIndex;
      counts.set(localIndex, (counts.get(localIndex) ?? 0) + 1);
    }
    return counts;
  }, [markerIndexes, visibleStartIndex, visibleTradeMarkers]);
  const visibleEquityCurve = result.equityCurve.slice(visibleStartIndex, visibleEndIndex + 1);
  const visibleBenchmarkCurve = benchmarkCurve.slice(visibleStartIndex, visibleEndIndex + 1);
  const overlayCurve = useMemo(() => {
    const merged = [...visibleEquityCurve, ...visibleBenchmarkCurve];
    return merged.length >= 2 ? merged : [];
  }, [visibleBenchmarkCurve, visibleEquityCurve]);
  const equityToY =
    overlayCurve.length >= 2
      ? buildEquityY(overlayCurve, topPadding + 12, topPadding + usableHeight * 0.28)
      : null;
  const hoveredCandleX =
    hoveredIndex == null ? null : leftPadding + candleSlotWidth * hoveredIndex + candleSlotWidth * 0.5;

  const priceToY = (price: number) => {
    const ratio = (price - chartMin) / (chartMax - chartMin || 1);
    return height - bottomPadding - ratio * usableHeight;
  };

  function resetPanState() {
    dragStartXRef.current = null;
    setIsPanning(false);
  }

  function resetSelectionState() {
    setSelectionRange(null);
  }

  function resetInteractionState() {
    resetPanState();
    resetSelectionState();
  }

  useEffect(() => {
    function handleWindowKeyDown(event: globalThis.KeyboardEvent) {
      if (event.code !== "Space" || !chartIsActive) {
        return;
      }
      event.preventDefault();
      setSpacePanActive(true);
    }

    function handleWindowKeyUp(event: globalThis.KeyboardEvent) {
      if (event.code !== "Space") {
        return;
      }
      if (chartIsActive) {
        event.preventDefault();
      }
      setSpacePanActive(false);
      resetPanState();
    }

    function handleWindowBlur() {
      setSpacePanActive(false);
      setChartIsActive(false);
      resetInteractionState();
      setHoveredIndex(null);
    }

    function handleVisibilityChange() {
      if (document.visibilityState === "hidden") {
        handleWindowBlur();
      }
    }

    window.addEventListener("keydown", handleWindowKeyDown);
    window.addEventListener("keyup", handleWindowKeyUp);
    window.addEventListener("blur", handleWindowBlur);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      window.removeEventListener("keydown", handleWindowKeyDown);
      window.removeEventListener("keyup", handleWindowKeyUp);
      window.removeEventListener("blur", handleWindowBlur);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [chartIsActive]);

  function zoomIn() {
    const maxZoom = Math.max(1, result.candles.length / 3);
    setZoomLevel((value) => Math.min(maxZoom, Math.max(1, value * 2)));
    setHoveredIndex(null);
  }

  function zoomOut() {
    setZoomLevel((value) => Math.max(1, value / 2));
    setPanOffset(0);
    setHoveredIndex(null);
  }

  function handleWheel(event: WheelEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    if (event.deltaY < 0) {
      zoomIn();
      return;
    }
    zoomOut();
  }

  useEffect(() => {
    const node = chartContainerRef.current;
    if (!node) {
      return;
    }

    function handleNativeWheel(event: globalThis.WheelEvent) {
      event.preventDefault();
    }

    node.addEventListener("wheel", handleNativeWheel, { passive: false });
    return () => {
      node.removeEventListener("wheel", handleNativeWheel);
    };
  }, [result.candles.length, visibleCount]);

  function handleMouseDown(event: MouseEvent<HTMLDivElement>) {
    event.preventDefault();
    setChartIsActive(true);
    event.currentTarget.focus();
    if (event.shiftKey) {
      const rect = event.currentTarget.getBoundingClientRect();
      const relativeX = event.clientX - rect.left;
      const clampedX = Math.max(leftPadding, Math.min(leftPadding + usableWidth, (relativeX / rect.width) * width));
      const index = Math.max(
        0,
        Math.min(visibleCandles.length - 1, Math.floor((clampedX - leftPadding) / Math.max(candleSlotWidth, 1))),
      );
      setSelectionRange({
        startX: clampedX,
        currentX: clampedX,
        startIndex: index,
        currentIndex: index,
      });
      setHoveredIndex(null);
      resetPanState();
      return;
    }
    if (!spacePanActive) {
      resetPanState();
      return;
    }
    dragStartXRef.current = event.clientX;
    setIsPanning(true);
  }

  function handleMouseMove(event: MouseEvent<HTMLDivElement>) {
    if (selectionRange) {
      const rect = event.currentTarget.getBoundingClientRect();
      const relativeX = event.clientX - rect.left;
      const clampedX = Math.max(leftPadding, Math.min(leftPadding + usableWidth, (relativeX / rect.width) * width));
      const index = Math.max(
        0,
        Math.min(visibleCandles.length - 1, Math.floor((clampedX - leftPadding) / Math.max(candleSlotWidth, 1))),
      );
      setSelectionRange((current) =>
        current
          ? {
              ...current,
              currentX: clampedX,
              currentIndex: index,
            }
          : current,
      );
      return;
    }
    if (!spacePanActive || !isPanning || dragStartXRef.current == null) {
      return;
    }
    event.preventDefault();
    const deltaX = event.clientX - dragStartXRef.current;
    const stepWidth = Math.max(10, usableWidth / Math.max(visibleCount * 1.8, 1));
    const candleShift = Math.trunc(deltaX / stepWidth);
    if (candleShift === 0) {
      return;
    }
    setPanOffset((value) => Math.max(0, Math.min(maxPanStart, value - candleShift)));
    dragStartXRef.current = event.clientX;
    setHoveredIndex(null);
  }

  function handleMouseUp() {
    if (selectionRange) {
      const localStart = Math.min(selectionRange.startIndex, selectionRange.currentIndex);
      const localEnd = Math.max(selectionRange.startIndex, selectionRange.currentIndex);
      const absoluteStart = visibleStartIndex + localStart;
      const absoluteEnd = visibleStartIndex + localEnd;
      const selectedCount = Math.max(absoluteEnd - absoluteStart + 1, 1);
      const nextZoom = Math.max(1, Math.min(result.candles.length / 3, result.candles.length / selectedCount));
      setZoomLevel(nextZoom);
      setPanOffset(absoluteStart);
      resetSelectionState();
    }
    resetPanState();
  }

  function resetView() {
    setZoomLevel(1);
    setPanOffset(0);
    resetInteractionState();
    setHoveredIndex(null);
  }

  function handleKeyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    if (event.code === "Space") {
      event.preventDefault();
      setChartIsActive(true);
      setSpacePanActive(true);
    }
  }

  function handleKeyUp(event: ReactKeyboardEvent<HTMLDivElement>) {
    if (event.code === "Space") {
      event.preventDefault();
      setSpacePanActive(false);
      resetPanState();
    }
  }

  return (
    <div className="overflow-hidden rounded-[28px] border border-cyan-400/10 bg-[radial-gradient(circle_at_top,rgba(55,189,248,0.08),transparent_34%),linear-gradient(180deg,rgba(4,11,30,0.94),rgba(5,11,24,1))] p-4">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.3em] text-cyan-200/50">Backtest tape</p>
          <h3 className="text-lg font-semibold text-white">{result.strategyName}</h3>
          <p className="mt-1 text-sm text-slate-400">
            {result.exchangeId || "unknown"} · {result.marketType || "unknown"} · {result.symbol} · {result.interval}
          </p>
        </div>
        <div className="grid gap-2 text-right text-xs text-slate-400">
          <p>Backtest source: {result.priceSource.toUpperCase()}</p>
          <p>Chart source: {result.chartPriceSource.toUpperCase()}</p>
          <p>{visibleTradeMarkers.length} visible trade markers</p>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => setShowEquityOverlay((value) => !value)}
          className={`rounded-full border px-3 py-1.5 text-xs transition ${
            showEquityOverlay
              ? "border-amber-300/40 bg-amber-300/15 text-amber-100"
              : "border-white/10 bg-white/5 text-slate-300"
          }`}
        >
          Equity overlay
        </button>
        <button
          type="button"
          onClick={() => setShowBenchmarkOverlay((value) => !value)}
          className={`rounded-full border px-3 py-1.5 text-xs transition ${
            showBenchmarkOverlay
              ? "border-fuchsia-300/40 bg-fuchsia-300/15 text-fuchsia-100"
              : "border-white/10 bg-white/5 text-slate-300"
          }`}
        >
          Buy & hold benchmark
        </button>
        <button
          type="button"
          onClick={resetView}
          className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1.5 text-xs text-cyan-100 transition hover:bg-cyan-300/15"
        >
          Reset view
        </button>
      </div>

      {chartWarnings.length > 0 ? (
        <div className="mb-4 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
          {chartWarnings.join(" ")}
        </div>
      ) : null}

      <div className="grid gap-4">
        <div
          ref={chartContainerRef}
          data-testid="candlestick-chart-surface"
          tabIndex={0}
          className={`rounded-[24px] border border-white/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0.01))] p-3 outline-none ${
            isPanning ? "cursor-grabbing" : spacePanActive ? "cursor-grab" : selectionRange ? "cursor-col-resize" : "cursor-crosshair"
          }`}
          style={{
            userSelect: chartIsActive || isPanning || selectionRange ? "none" : "auto",
            overscrollBehavior: "contain",
          }}
          onWheel={handleWheel}
          onKeyDown={handleKeyDown}
          onKeyUp={handleKeyUp}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onDoubleClick={resetView}
          onDragStart={(event) => event.preventDefault()}
          onFocus={() => setChartIsActive(true)}
          onBlur={() => {
            setChartIsActive(false);
            setSpacePanActive(false);
            resetInteractionState();
          }}
          onMouseEnter={() => setChartIsActive(true)}
          onMouseLeave={() => {
            setChartIsActive(false);
            setSpacePanActive(false);
            handleMouseUp();
            setHoveredIndex(null);
          }}
        >
          <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full">
            <rect
              x={leftPadding}
              y={topPadding}
              width={usableWidth}
              height={usableHeight}
              rx={18}
              fill="rgba(5, 12, 31, 0.65)"
              stroke="rgba(255,255,255,0.06)"
            />

            {yAxisLevels.map((level) => {
              const y = priceToY(level);
              return (
                <g key={level}>
                  <line
                    x1={leftPadding}
                    y1={y}
                    x2={width - rightPadding}
                    y2={y}
                    stroke="rgba(255,255,255,0.08)"
                    strokeDasharray="5 7"
                  />
                  <text x={leftPadding - 12} y={y + 4} fill="rgba(226,232,240,0.82)" fontSize="12" textAnchor="end">
                    {formatCurrency(level)}
                  </text>
                </g>
              );
            })}

            {visibleCandles.map((candle, index) => {
              const x = leftPadding + candleSlotWidth * index + candleSlotWidth * 0.18;
              const bodyWidth = Math.max(12, candleSlotWidth * 0.62);
              const openY = priceToY(candle.open);
              const closeY = priceToY(candle.close);
              const highY = priceToY(candle.high);
              const lowY = priceToY(candle.low);
              const rising = candle.close >= candle.open;
              const fill = rising ? "#22c55e" : "#f43f5e";

              return (
                <g key={candle.timestamp} onMouseEnter={() => setHoveredIndex(index)} onMouseLeave={() => setHoveredIndex(null)}>
                  <rect
                    x={x - candleSlotWidth * 0.15}
                    y={topPadding}
                    width={bodyWidth + candleSlotWidth * 0.3}
                    height={usableHeight}
                    fill={hoveredIndex === index ? "rgba(56,189,248,0.08)" : "transparent"}
                  />
                  <line
                    x1={x + bodyWidth / 2}
                    y1={highY}
                    x2={x + bodyWidth / 2}
                    y2={lowY}
                    stroke={fill}
                    strokeWidth={2.4}
                    strokeLinecap="round"
                  />
                  <rect
                    x={x}
                    y={Math.min(openY, closeY)}
                    width={bodyWidth}
                    height={Math.max(8, Math.abs(openY - closeY))}
                    rx={5}
                    fill={fill}
                  />
                  {index % Math.max(1, Math.ceil(visibleCandles.length / 6)) === 0 ? (
                    <text
                      x={x + bodyWidth / 2}
                      y={height - bottomPadding + 20}
                      fill="rgba(148,163,184,0.82)"
                      fontSize="11"
                      textAnchor="middle"
                    >
                      {formatAxisLabel(candle.timestamp)}
                    </text>
                  ) : null}
                  {(visibleMarkerCounts.get(index) ?? 0) > 1 ? (
                    <g transform={`translate(${x + bodyWidth / 2}, ${topPadding + 14})`}>
                      <circle r="11" fill="rgba(15,23,42,0.92)" stroke="rgba(56,189,248,0.35)" />
                      <text y="4" fill="rgba(226,232,240,0.96)" fontSize="10" textAnchor="middle" fontWeight="700">
                        {visibleMarkerCounts.get(index)}
                      </text>
                    </g>
                  ) : null}
                </g>
              );
            })}

            {equityToY && showBenchmarkOverlay && visibleBenchmarkCurve.length >= 2 ? (
              <polyline
                fill="none"
                stroke="rgba(217,70,239,0.85)"
                strokeWidth="2"
                strokeDasharray="6 5"
                points={visibleBenchmarkCurve
                  .map((point, index) => {
                    const x = leftPadding + candleSlotWidth * index + candleSlotWidth * 0.5;
                    const y = equityToY(point.equity);
                    return `${x},${y}`;
                  })
                  .join(" ")}
              />
            ) : null}

            {equityToY && showEquityOverlay && visibleEquityCurve.length >= 2 ? (
              <polyline
                fill="none"
                stroke="rgba(250,204,21,0.95)"
                strokeWidth="2.5"
                points={visibleEquityCurve
                  .map((point, index) => {
                    const x = leftPadding + candleSlotWidth * index + candleSlotWidth * 0.5;
                    const y = equityToY(point.equity);
                    return `${x},${y}`;
                  })
                  .join(" ")}
              />
            ) : null}

            {visibleTradeMarkers.map((marker) => {
              const index = markerIndexes.get(marker.id);
              if (index == null) {
                return null;
              }

              const localIndex = index - visibleStartIndex;
              const x = leftPadding + candleSlotWidth * localIndex + candleSlotWidth * 0.5;
              const y = priceToY(marker.price);
              const color = MARKER_COLORS[marker.action] ?? "#e2e8f0";
              const direction = marker.action === "close" || marker.action === "reduce" || marker.action === "stop" ? 1 : -1;
              const lane = markerLanes.get(marker.id) ?? 0;
              const laneOffset = lane * 16;
              const inSelectedLifecycle =
                selectedLifecycleId != null && lifecycleGroupByMarkerId.get(marker.id) === selectedLifecycleId;
              const path =
                direction < 0 ? "M 0 0 L 8 -12 L -8 -12 Z" : "M 0 0 L 8 12 L -8 12 Z";

              return (
                <g key={marker.id} onClick={() => setSelectedMarkerId(marker.id)} className="cursor-pointer">
                  <line
                    x1={x}
                    y1={y}
                    x2={x}
                    y2={y + direction * (28 + laneOffset)}
                    stroke={color}
                    strokeWidth={selectedMarker?.id === marker.id ? 3.5 : inSelectedLifecycle ? 3 : 2}
                    strokeDasharray="4 4"
                    opacity={selectedLifecycleId && !inSelectedLifecycle ? 0.45 : 1}
                  />
                  <g transform={`translate(${x}, ${y + direction * (28 + laneOffset)})`}>
                    <path d={path} fill={color} opacity={selectedLifecycleId && !inSelectedLifecycle ? 0.45 : 1} />
                  </g>
                  <text
                    x={x}
                    y={y + direction * (44 + laneOffset)}
                    fill={color}
                    fontSize="10"
                    fontWeight="700"
                    textAnchor="middle"
                    opacity={selectedLifecycleId && !inSelectedLifecycle ? 0.45 : 1}
                  >
                    {marker.action.toUpperCase()}
                  </text>
                </g>
              );
            })}

            {selectedLifecycleMarkers.length >= 2
              ? (() => {
                  const points = selectedLifecycleMarkers
                    .map((marker) => {
                      const absoluteIndex = markerIndexes.get(marker.id);
                      if (absoluteIndex == null || absoluteIndex < visibleStartIndex || absoluteIndex > visibleEndIndex) {
                        return null;
                      }
                      const localIndex = absoluteIndex - visibleStartIndex;
                      const x = leftPadding + candleSlotWidth * localIndex + candleSlotWidth * 0.5;
                      const y = priceToY(marker.price);
                      return `${x},${y}`;
                    })
                    .filter((point): point is string => point !== null);
                  if (points.length < 2) {
                    return null;
                  }
                  return (
                    <polyline
                      fill="none"
                      stroke="rgba(56,189,248,0.55)"
                      strokeWidth="2"
                      strokeDasharray="3 4"
                      points={points.join(" ")}
                    />
                  );
                })()
              : null}

            {selectionRange ? (
              <rect
                x={Math.min(selectionRange.startX, selectionRange.currentX)}
                y={topPadding}
                width={Math.abs(selectionRange.currentX - selectionRange.startX)}
                height={usableHeight}
                fill="rgba(56,189,248,0.12)"
                stroke="rgba(56,189,248,0.55)"
                strokeDasharray="6 4"
                rx="10"
              />
            ) : null}

            {hoveredCandle && hoveredCandleX != null ? (
              <>
                <line
                  x1={hoveredCandleX}
                  y1={topPadding}
                  x2={hoveredCandleX}
                  y2={height - bottomPadding}
                  stroke="rgba(56,189,248,0.6)"
                  strokeDasharray="4 4"
                />
                <g transform={`translate(${Math.min(hoveredCandleX + 12, width - 210)}, ${topPadding + 8})`}>
                  <rect
                    width="190"
                    height="122"
                    rx="14"
                    fill="rgba(2,8,23,0.94)"
                    stroke="rgba(56,189,248,0.25)"
                  />
                  <text x="12" y="22" fill="rgba(226,232,240,0.96)" fontSize="11" fontWeight="700">
                    {hoveredCandle.timestamp}
                  </text>
                  <text x="12" y="44" fill="rgba(148,163,184,0.92)" fontSize="11">
                    O {formatCurrency(hoveredCandle.open)}
                  </text>
                  <text x="12" y="62" fill="rgba(148,163,184,0.92)" fontSize="11">
                    H {formatCurrency(hoveredCandle.high)}
                  </text>
                  <text x="12" y="80" fill="rgba(148,163,184,0.92)" fontSize="11">
                    L {formatCurrency(hoveredCandle.low)}
                  </text>
                  <text x="12" y="98" fill="rgba(148,163,184,0.92)" fontSize="11">
                    C {formatCurrency(hoveredCandle.close)}
                  </text>
                  <text x="12" y="116" fill="rgba(148,163,184,0.92)" fontSize="11">
                    V {hoveredCandle.volume.toLocaleString()}
                  </text>
                </g>
              </>
            ) : null}
          </svg>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-xs text-slate-300">
          Strategy end equity: <span className="text-white">{result.equityCurve.at(-1)?.equity?.toFixed(2) ?? "n/a"}</span>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-xs text-slate-300">
          Benchmark end equity: <span className="text-white">{benchmarkCurve.at(-1)?.equity?.toFixed(2) ?? "n/a"}</span>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-xs text-slate-300">
          Relative alpha:{" "}
          <span className="text-white">
            {result.equityCurve.length > 0 && benchmarkCurve.length > 0
              ? `${(result.equityCurve.at(-1)!.equity - benchmarkCurve.at(-1)!.equity).toFixed(2)}`
              : "n/a"}
          </span>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-xs text-slate-300">
          View: <span className="text-white">{zoomLevel.toFixed(1)}x / {visibleCandles.length} candles</span>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-xs text-slate-300 md:col-span-2 xl:col-span-4">
          Interaction: <span className="text-white">Wheel to zoom. Hold Space and drag horizontally to pan. Shift + drag to box zoom. Double-click to reset.</span>
        </div>
      </div>
    </div>
  );
}
