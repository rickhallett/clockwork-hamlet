import { useState, useCallback, useRef, useEffect } from 'react'
import { Card, Badge } from '../components/common'
import { ForceGraph, GraphControls } from '../components/graph'
import { useRelationships } from '../hooks'

function getScoreColor(score: number): 'green' | 'blue' | 'yellow' | 'red' {
  if (score >= 5) return 'green'
  if (score >= 2) return 'blue'
  if (score >= -2) return 'yellow'
  return 'red'
}

function getScoreLabel(score: number): string {
  if (score >= 7) return 'Close Friends'
  if (score >= 4) return 'Friends'
  if (score >= 0) return 'Acquaintances'
  if (score >= -4) return 'Wary'
  return 'Hostile'
}

export function Relationships() {
  const { graph, isLoading, error } = useRelationships()
  const [activeTypes, setActiveTypes] = useState<string[]>([])
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 })

  // Update dimensions based on container size
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        setDimensions({
          width: rect.width,
          height: Math.max(400, Math.min(600, rect.width * 0.5)),
        })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  const handleToggleType = useCallback((type: string) => {
    setActiveTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }, [])

  const handleClearSelection = useCallback(() => {
    setSelectedNode(null)
  }, [])

  // Filter relationships for the list view
  const filteredRelationships = graph?.links.filter((link) =>
    activeTypes.length === 0 || activeTypes.includes(link.type)
  ) || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-fg-primary mb-2">Relationships</h1>
        <p className="text-fg-secondary">
          The social network of Clockwork Hamlet. See how villagers feel about each other.
        </p>
      </div>

      <GraphControls
        activeTypes={activeTypes}
        onToggleType={handleToggleType}
        selectedNode={selectedNode}
        onClearSelection={handleClearSelection}
      />

      {/* Graph visualization */}
      <Card className="overflow-hidden">
        <div ref={containerRef} className="w-full">
          {isLoading ? (
            <div className="h-[400px] flex items-center justify-center">
              <div className="animate-pulse text-fg-dim">Loading relationships...</div>
            </div>
          ) : graph ? (
            <ForceGraph
              graph={graph}
              selectedNode={selectedNode}
              onNodeClick={setSelectedNode}
              filterTypes={activeTypes}
              width={dimensions.width}
              height={dimensions.height}
            />
          ) : (
            <div className="h-[400px] flex items-center justify-center">
              <p className="text-fg-dim">{error || 'No relationship data available'}</p>
            </div>
          )}
        </div>
      </Card>

      {/* Legend */}
      <div className="flex items-center gap-6 text-sm">
        <span className="text-fg-dim">Edge colors:</span>
        <div className="flex items-center gap-2">
          <div className="w-3 h-0.5 bg-accent-green" />
          <span className="text-fg-secondary">Close (+5)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-0.5 bg-accent-blue" />
          <span className="text-fg-secondary">Friends (+2)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-0.5 bg-accent-yellow" />
          <span className="text-fg-secondary">Neutral</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-0.5 bg-accent-red" />
          <span className="text-fg-secondary">Hostile</span>
        </div>
      </div>

      {/* Relationship list */}
      <div>
        <h2 className="text-lg font-semibold text-fg-primary mb-4">All Relationships</h2>
        <div className="space-y-3">
          {filteredRelationships.length > 0 ? (
            filteredRelationships.map((rel, idx) => {
              const sourceId = typeof rel.source === 'string' ? rel.source : rel.source
              const targetId = typeof rel.target === 'string' ? rel.target : rel.target
              const sourceName = graph?.nodes.find((n) => n.id === sourceId)?.name || sourceId
              const targetName = graph?.nodes.find((n) => n.id === targetId)?.name || targetId

              return (
                <Card key={idx} className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <span className="text-accent-magenta font-medium">{sourceName}</span>
                      <span className="text-fg-dim">\u2192</span>
                      <span className="text-accent-cyan font-medium">{targetName}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={getScoreColor(rel.score)}>
                      {getScoreLabel(rel.score)}
                    </Badge>
                    <span className="text-fg-dim text-sm w-8 text-right">
                      {rel.score > 0 ? '+' : ''}{rel.score}
                    </span>
                  </div>
                </Card>
              )
            })
          ) : (
            <p className="text-fg-dim text-center py-4">No relationships to display</p>
          )}
        </div>
      </div>
    </div>
  )
}
