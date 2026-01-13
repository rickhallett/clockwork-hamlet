import { useState } from 'react'
import { DailyDigest, WeeklyDigest } from '../components/digest'
import { useDigest } from '../hooks/useDigest'

export function Digest() {
  const [digestType, setDigestType] = useState<'daily' | 'weekly'>('daily')
  const { digest, isLoading, error } = useDigest(digestType)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-fg-primary mb-2">Village Digest</h1>
          <p className="text-fg-secondary">
            Catch up on the latest happenings in Clockwork Hamlet.
          </p>
        </div>

        {/* Toggle */}
        <div className="flex rounded-lg overflow-hidden border border-bg-highlight">
          <button
            onClick={() => setDigestType('daily')}
            className={`px-4 py-2 text-sm transition-colors ${
              digestType === 'daily'
                ? 'bg-accent-blue text-white'
                : 'bg-bg-secondary text-fg-secondary hover:text-fg-primary'
            }`}
          >
            Daily
          </button>
          <button
            onClick={() => setDigestType('weekly')}
            className={`px-4 py-2 text-sm transition-colors ${
              digestType === 'weekly'
                ? 'bg-accent-magenta text-white'
                : 'bg-bg-secondary text-fg-secondary hover:text-fg-primary'
            }`}
          >
            Weekly
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-accent-yellow/10 border border-accent-yellow/30 rounded-lg px-4 py-3 text-accent-yellow text-sm">
          Using sample digest (API unavailable)
        </div>
      )}

      {isLoading ? (
        <div className="bg-[#f4f1ea] rounded-lg p-8 animate-pulse">
          <div className="h-8 bg-[#1a1a1a]/10 rounded w-3/4 mx-auto mb-4" />
          <div className="h-4 bg-[#1a1a1a]/10 rounded w-1/2 mx-auto mb-8" />
          <div className="space-y-3">
            <div className="h-4 bg-[#1a1a1a]/10 rounded" />
            <div className="h-4 bg-[#1a1a1a]/10 rounded" />
            <div className="h-4 bg-[#1a1a1a]/10 rounded w-3/4" />
          </div>
        </div>
      ) : digest ? (
        digestType === 'daily' ? (
          <DailyDigest digest={digest} />
        ) : (
          <WeeklyDigest digest={digest} />
        )
      ) : (
        <div className="bg-bg-secondary border border-bg-highlight rounded-lg p-8 text-center">
          <p className="text-fg-dim">No {digestType} digest available yet.</p>
          <p className="text-fg-dim text-sm mt-2">
            Digests are generated as the simulation runs.
          </p>
        </div>
      )}
    </div>
  )
}
