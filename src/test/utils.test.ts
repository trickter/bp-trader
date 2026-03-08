import { describe, it, expect } from 'vitest'
import { cn } from '../lib/utils'

describe('utils', () => {
  describe('cn', () => {
    it('merges class names', () => {
      expect(cn('foo', 'bar')).toBe('foo bar')
    })

    it('handles conditional classes', () => {
      const condition = true
      expect(cn('foo', condition && 'bar')).toBe('foo bar')
      expect(cn('foo', false && 'bar')).toBe('foo')
    })

    it('handles empty strings', () => {
      expect(cn('foo', '', 'bar')).toBe('foo bar')
    })

    it('handles undefined and null', () => {
      expect(cn('foo', undefined, null, 'bar')).toBe('foo bar')
    })
  })
})
