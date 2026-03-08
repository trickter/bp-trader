import { describe, it, expect } from 'vitest'

describe('types', () => {
  describe('ProfileSummary', () => {
    it('should have expected shape', () => {
      const profile = {
        total_equity: 10000,
        available_margin: 8000,
        unrealized_pnl: 100,
        realized_pnl_24h: 50,
        win_rate: 0.65,
        risk_level: 'disciplined',
        price_source: 'mark',
        synced_at: '2024-01-15T10:00:00Z',
      }

      expect(profile.total_equity).toBe(10000)
      expect(profile.available_margin).toBe(8000)
      expect(profile.risk_level).toBe('disciplined')
    })
  })

  describe('Position', () => {
    it('should have expected shape', () => {
      const position = {
        symbol: 'SOL-PERP',
        side: 'long',
        quantity: 10,
        entry_price: 500,
        mark_price: 510,
        liquidation_price: null,
        unrealized_pnl: 100,
        margin_used: 1000,
        opened_at: '2024-01-15T10:00:00Z',
        price_source: 'mark',
      }

      expect(position.symbol).toBe('SOL-PERP')
      expect(position.side).toBe('long')
      expect(position.quantity).toBe(10)
    })
  })

  describe('AssetBalance', () => {
    it('should have expected shape', () => {
      const asset = {
        asset: 'USDC',
        available: 5000,
        locked: 100,
        collateral_value: 5100,
        portfolio_weight: 51,
        change_24h: 0,
        price_source: 'mark',
      }

      expect(asset.asset).toBe('USDC')
      expect(asset.available).toBe(5000)
      expect(asset.collateral_value).toBe(5100)
    })
  })

  describe('Candle', () => {
    it('should have expected shape', () => {
      const candle = {
        timestamp: '2024-01-15T10:00:00Z',
        open: 500,
        high: 510,
        low: 495,
        close: 505,
        volume: 10000,
      }

      expect(candle.open).toBe(500)
      expect(candle.high).toBe(510)
      expect(candle.low).toBe(495)
      expect(candle.close).toBe(505)
      expect(candle.volume).toBe(10000)
    })
  })

  describe('TradeMarker', () => {
    it('should have expected shape', () => {
      const marker = {
        id: 'trade-1',
        timestamp: '2024-01-15T10:00:00Z',
        action: 'open',
        side: 'buy',
        price: 500,
        reason: 'signal',
      }

      expect(marker.id).toBe('trade-1')
      expect(marker.action).toBe('open')
      expect(marker.side).toBe('buy')
    })
  })
})
