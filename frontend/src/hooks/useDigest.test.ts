import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useDigest } from './useDigest'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('useDigest', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('daily digest', () => {
    it('transforms API response correctly', async () => {
      const mockApiResponse = {
        day: 5,
        total_events_today: 12,
        headlines: [
          { summary: 'Big Event at Town Square', significance: 5, type: 'action' },
          { summary: 'Mystery at the Bakery', significance: 3, type: 'dialogue' },
        ],
        other_events: [
          { summary: 'Small talk at tavern', type: 'social' },
        ],
        generated_at: 1700000000,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponse),
      })

      const { result } = renderHook(() => useDigest('daily'))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Should have transformed data
      expect(result.current.digest).toBeDefined()
      expect(result.current.digest?.title).toBe('THE DAILY HAMLET')
      expect(result.current.digest?.type).toBe('daily')
      expect(result.current.digest?.day).toBe(5)
      expect(result.current.digest?.headline).toBe('Big Event at Town Square')
      expect(result.current.digest?.highlights).toHaveLength(3) // 2 headlines + 1 other event
    })

    it('handles empty highlights gracefully', async () => {
      const mockApiResponse = {
        day: 1,
        total_events_today: 0,
        headlines: [],
        other_events: [],
        generated_at: 1700000000,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponse),
      })

      const { result } = renderHook(() => useDigest('daily'))

      await waitFor(() => !result.current.isLoading)

      // Should not throw on .length access
      expect(result.current.digest?.highlights).toBeDefined()
      expect(result.current.digest?.highlights?.length).toBe(0)
      expect(result.current.digest?.headline).toBe('A Quiet Day in the Village')
    })

    it('uses placeholder on API error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() => useDigest('daily'))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Should use placeholder
      expect(result.current.digest).toBeDefined()
      expect(result.current.digest?.title).toBe('THE DAILY HAMLET')
      expect(result.current.error).toBe('Network error')
    })

    it('handles 404 by setting digest to null', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      })

      const { result } = renderHook(() => useDigest('daily'))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.digest).toBeNull()
      expect(result.current.error).toBeNull()
    })
  })

  describe('weekly digest', () => {
    it('transforms API response correctly', async () => {
      const mockApiResponse = {
        week_ending_day: 7,
        total_significant_events: 25,
        top_stories: [
          'The Great Mystery of the Missing Cheese',
          'Unexpected Romance Blossoms',
          'Village Festival Preparations Begin',
        ],
        events_by_type: {
          action: 10,
          dialogue: 8,
          social: 7,
        },
        generated_at: 1700000000,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponse),
      })

      const { result } = renderHook(() => useDigest('weekly'))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.digest).toBeDefined()
      expect(result.current.digest?.title).toBe('THE WEEKLY HAMLET CHRONICLE')
      expect(result.current.digest?.type).toBe('weekly')
      expect(result.current.digest?.day).toBe(7)
      expect(result.current.digest?.headline).toBe('The Great Mystery of the Missing Cheese')
      expect(result.current.digest?.highlights).toHaveLength(3)
    })

    it('handles empty top_stories gracefully', async () => {
      const mockApiResponse = {
        week_ending_day: 7,
        total_significant_events: 0,
        top_stories: [],
        events_by_type: {},
        generated_at: 1700000000,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockApiResponse),
      })

      const { result } = renderHook(() => useDigest('weekly'))

      await waitFor(() => !result.current.isLoading)

      expect(result.current.digest?.highlights).toBeDefined()
      expect(result.current.digest?.highlights?.length).toBe(0)
      expect(result.current.digest?.headline).toBe('A Week of Village Life')
    })

    it('uses placeholder on API error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Server error'))

      const { result } = renderHook(() => useDigest('weekly'))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.digest).toBeDefined()
      expect(result.current.digest?.title).toBe('THE WEEKLY HAMLET CHRONICLE')
      expect(result.current.error).toBe('Server error')
    })
  })

  describe('refetch', () => {
    it('allows manual refetch of digest', async () => {
      const mockApiResponse = {
        day: 1,
        total_events_today: 5,
        headlines: [{ summary: 'Initial headline', significance: 3, type: 'action' }],
        other_events: [],
        generated_at: 1700000000,
      }

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockApiResponse),
      })

      const { result } = renderHook(() => useDigest('daily'))

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Initial fetch
      expect(mockFetch).toHaveBeenCalledTimes(1)

      // Trigger refetch
      result.current.refetch()

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('loading state', () => {
    it('sets isLoading true while fetching', async () => {
      let resolvePromise: (value: unknown) => void
      const pendingPromise = new Promise((resolve) => {
        resolvePromise = resolve
      })

      mockFetch.mockReturnValueOnce(pendingPromise)

      const { result } = renderHook(() => useDigest('daily'))

      // Should be loading initially
      expect(result.current.isLoading).toBe(true)

      // Resolve the promise
      resolvePromise!({
        ok: true,
        json: () => Promise.resolve({ day: 1, headlines: [], other_events: [], generated_at: 0 }),
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })
  })
})
