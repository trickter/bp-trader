import type { BacktestResult } from "../lib/types";

export function CandlestickChart({ result }: { result: BacktestResult }) {
  const width = 820;
  const height = 320;
  const padding = 32;
  const usableHeight = height - padding * 2;
  const usableWidth = width - padding * 2;

  if (result.candles.length === 0) {
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

  const prices = result.candles.flatMap((candle) => [
    candle.low,
    candle.high,
    candle.open,
    candle.close,
  ]);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const candleWidth = usableWidth / result.candles.length;
  const candleIndexByTimestamp = new Map(
    result.candles.map((candle, index) => [candle.timestamp, index]),
  );

  const priceToY = (price: number) => {
    const ratio = (price - minPrice) / (maxPrice - minPrice || 1);
    return height - padding - ratio * usableHeight;
  };

  return (
    <div className="overflow-hidden rounded-[28px] border border-cyan-400/10 bg-[radial-gradient(circle_at_top,rgba(55,189,248,0.08),transparent_34%),linear-gradient(180deg,rgba(4,11,30,0.94),rgba(5,11,24,1))] p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.3em] text-cyan-200/50">Backtest tape</p>
          <h3 className="text-lg font-semibold text-white">{result.strategyName}</h3>
        </div>
        <div className="text-right text-xs text-slate-400">
          <p>Price source: {result.priceSource.toUpperCase()}</p>
          <p>{result.tradeMarkers.length} lifecycle markers</p>
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full">
        {[0, 1, 2, 3].map((line) => {
          const y = padding + (usableHeight / 3) * line;
          return (
            <line
              key={line}
              x1={padding}
              y1={y}
              x2={width - padding}
              y2={y}
              stroke="rgba(255,255,255,0.08)"
              strokeDasharray="4 8"
            />
          );
        })}

        {result.candles.map((candle, index) => {
          const x = padding + candleWidth * index + 8;
          const bodyWidth = Math.max(8, candleWidth - 10);
          const openY = priceToY(candle.open);
          const closeY = priceToY(candle.close);
          const highY = priceToY(candle.high);
          const lowY = priceToY(candle.low);
          const rising = candle.close >= candle.open;

          return (
            <g key={candle.timestamp}>
              <line
                x1={x + bodyWidth / 2}
                y1={highY}
                x2={x + bodyWidth / 2}
                y2={lowY}
                stroke={rising ? "#42d392" : "#fb7185"}
                strokeWidth={2}
              />
              <rect
                x={x}
                y={Math.min(openY, closeY)}
                width={bodyWidth}
                height={Math.max(6, Math.abs(openY - closeY))}
                rx={4}
                fill={rising ? "#42d392" : "#fb7185"}
                opacity={0.9}
              />
            </g>
          );
        })}

        {result.tradeMarkers.map((marker) => {
          const index = candleIndexByTimestamp.get(marker.timestamp);
          if (index === -1) {
            return null;
          }
          if (index === undefined) {
            return null;
          }

          const x = padding + candleWidth * index + 14;
          const y = priceToY(marker.price);
          const fill = marker.type === "open" ? "#38bdf8" : "#f59e0b";

          return (
            <g key={marker.id}>
              <circle cx={x} cy={y} r={7} fill={fill} />
              <text x={x} y={y - 12} fill={fill} fontSize="10" textAnchor="middle">
                {marker.type.toUpperCase()}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
