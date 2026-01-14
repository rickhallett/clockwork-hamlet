import { Badge } from '../common'
import type { Digest } from '../../hooks/useDigest'

interface DailyDigestProps {
  digest: Digest
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

export function DailyDigest({ digest }: DailyDigestProps) {
  return (
    <article className="bg-[#f4f1ea] text-[#1a1a1a] rounded-lg overflow-hidden shadow-lg">
      {/* Masthead */}
      <header className="bg-[#1a1a1a] text-[#f4f1ea] px-6 py-4 text-center">
        <div className="border-b border-[#f4f1ea]/30 pb-2 mb-2">
          <h1 className="text-3xl font-bold tracking-widest uppercase font-serif">
            {digest.title}
          </h1>
        </div>
        <div className="flex items-center justify-center gap-4 text-sm">
          <span>Day {digest.day}</span>
          <span className="text-[#f4f1ea]/50">|</span>
          <span>{formatDate(digest.generated_at)}</span>
          <span className="text-[#f4f1ea]/50">|</span>
          <span>Est. Since Time Immemorial</span>
        </div>
      </header>

      {/* Headline */}
      <div className="px-6 py-6 border-b-2 border-[#1a1a1a]">
        <h2 className="text-2xl md:text-3xl font-bold font-serif leading-tight text-center">
          {digest.headline}
        </h2>
      </div>

      {/* Summary */}
      <div className="px-6 py-4">
        <p className="text-lg leading-relaxed first-letter:text-5xl first-letter:font-bold first-letter:float-left first-letter:mr-2 first-letter:mt-1">
          {digest.summary}
        </p>
      </div>

      {/* Highlights */}
      {digest.highlights && digest.highlights.length > 0 && (
        <div className="px-6 py-4 border-t border-[#1a1a1a]/20">
          <h3 className="text-lg font-bold uppercase tracking-wide mb-4 border-b border-[#1a1a1a]/20 pb-2">
            Today&apos;s Highlights
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {digest.highlights.map((highlight, idx) => (
              <div
                key={idx}
                className="border border-[#1a1a1a]/20 p-4 rounded"
              >
                <h4 className="font-bold mb-2">{highlight.title}</h4>
                <p className="text-sm text-[#1a1a1a]/80 mb-3">
                  {highlight.description}
                </p>
                {highlight.agents_involved && highlight.agents_involved.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {highlight.agents_involved.map((agent) => (
                      <Badge key={agent} variant="blue" className="!bg-[#1a1a1a]/10 !text-[#1a1a1a]">
                        {agent}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-[#1a1a1a]/10 px-6 py-3 text-center text-sm italic">
        &ldquo;All the news that fits in a hamlet&rdquo;
      </footer>
    </article>
  )
}
