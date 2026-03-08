import type { BacktestResult } from "../lib/types";

export function CandlestickChart({ result }: { result: BacktestResult }) {
  const width = 820;
  const height = 320;
  const padding = 32;
  const prices = result.candles.flatMap((candle) => [
    candle.low,
    candle.high,
    candle.open,
    candle.close,
  ]);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const usableHeight = height - padding * 2;
  const usableWidth = width - padding * 2;

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
          const x = padding + (usableWidth / result.candles.length) * index + 8;
          const bodyWidth = Math.max(8, usableWidth / result.candles.length - 10);
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
          const index = result.candles.findIndex((candle) => candle.timestamp === marker.timestamp);
          if (index === -1) {
            return null;
          }

          const x = padding + (usableWidth / result.candles.length) * index + 14;
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
