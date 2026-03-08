import '@testing-library/jest-dom'

// Mock fetch globally to avoid network errors in tests
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  })
) as typeof fetch
