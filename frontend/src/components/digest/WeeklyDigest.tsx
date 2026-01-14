import { Badge } from '../common'
import type { Digest } from '../../hooks/useDigest'

interface WeeklyDigestProps {
  digest: Digest
}

export function WeeklyDigest({ digest }: WeeklyDigestProps) {
  return (
    <article className="bg-[#f4f1ea] text-[#1a1a1a] rounded-lg overflow-hidden shadow-lg">
      {/* Masthead - Magazine style */}
      <header className="bg-gradient-to-r from-[#2d1f1f] to-[#1a1a1a] text-[#f4f1ea] px-6 py-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm uppercase tracking-widest">Week {Math.ceil(digest.day / 7)}</span>
          <span className="text-sm">The Official Weekly Chronicle</span>
        </div>
        <h1 className="text-4xl font-bold tracking-wide uppercase font-serif text-center py-4 border-y border-[#f4f1ea]/30">
          {digest.title}
        </h1>
      </header>

      {/* Cover Story */}
      <div className="px-8 py-8 border-b-4 border-double border-[#1a1a1a]">
        <span className="text-xs uppercase tracking-widest text-[#1a1a1a]/60 mb-2 block">
          Cover Story
        </span>
        <h2 className="text-3xl md:text-4xl font-bold font-serif leading-tight mb-4">
          {digest.headline}
        </h2>
        <p className="text-lg leading-relaxed text-[#1a1a1a]/90">
          {digest.summary}
        </p>
      </div>

      {/* Feature Stories */}
      {digest.highlights && digest.highlights.length > 0 && (
        <div className="px-8 py-6">
          <h3 className="text-xl font-bold uppercase tracking-wide mb-6 flex items-center gap-3">
            <span className="flex-1 h-px bg-[#1a1a1a]/30" />
            <span>This Week&apos;s Features</span>
            <span className="flex-1 h-px bg-[#1a1a1a]/30" />
          </h3>

          <div className="space-y-6">
            {digest.highlights.map((highlight, idx) => (
              <div
                key={idx}
                className="flex gap-4 pb-6 border-b border-[#1a1a1a]/10 last:border-0"
              >
                <div className="text-4xl font-bold text-[#1a1a1a]/20 shrink-0">
                  {String(idx + 1).padStart(2, '0')}
                </div>
                <div>
                  <h4 className="text-xl font-bold mb-2">{highlight.title}</h4>
                  <p className="text-[#1a1a1a]/80 mb-3">
                    {highlight.description}
                  </p>
                  {highlight.agents_involved && highlight.agents_involved.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      <span className="text-sm text-[#1a1a1a]/60 mr-2">Featuring:</span>
                      {highlight.agents_involved.map((agent) => (
                        <Badge key={agent} variant="magenta" className="!bg-[#1a1a1a]/10 !text-[#1a1a1a]">
                          {agent}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-[#1a1a1a] text-[#f4f1ea] px-6 py-4 text-center">
        <p className="text-sm italic mb-2">
          &ldquo;Your weekly window into hamlet life&rdquo;
        </p>
        <p className="text-xs text-[#f4f1ea]/60">
          Published every seventh day since the founding of Clockwork Hamlet
        </p>
      </footer>
    </article>
  )
}
