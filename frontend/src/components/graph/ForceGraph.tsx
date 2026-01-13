import { useRef, useCallback, useEffect, useState } from 'react'
import ForceGraph2D, { ForceGraphMethods, NodeObject, LinkObject } from 'react-force-graph-2d'
import type { RelationshipGraph, GraphNode } from '../../hooks/useRelationships'

interface ForceGraphProps {
  graph: RelationshipGraph
  selectedNode: string | null
  onNodeClick: (nodeId: string | null) => void
  filterTypes: string[]
  width: number
  height: number
}

interface GraphNodeObject extends NodeObject {
  id: string
  name: string
  location?: string
}

interface GraphLinkObject extends LinkObject {
  source: string | GraphNodeObject
  target: string | GraphNodeObject
  type: string
  score: number
}

function getEdgeColor(score: number): string {
  if (score >= 5) return '#9ece6a' // green - close friends
  if (score >= 2) return '#7aa2f7' // blue - friends
  if (score >= -2) return '#e0af68' // yellow - acquaintances
  return '#f7768e' // red - hostile
}

function getEdgeWidth(score: number): number {
  const absScore = Math.abs(score)
  return Math.max(1, Math.min(5, absScore * 0.5))
}

export function ForceGraph({
  graph,
  selectedNode,
  onNodeClick,
  filterTypes,
  width,
  height,
}: ForceGraphProps) {
  const graphRef = useRef<ForceGraphMethods<GraphNodeObject, GraphLinkObject> | undefined>()
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)

  // Filter links by type
  const filteredGraph = {
    nodes: graph.nodes,
    links: filterTypes.length > 0
      ? graph.links.filter((link) => filterTypes.includes(link.type))
      : graph.links,
  }

  // Find connected nodes
  const connectedNodes = new Set<string>()
  if (selectedNode) {
    connectedNodes.add(selectedNode)
    filteredGraph.links.forEach((link) => {
      const sourceId = typeof link.source === 'string' ? link.source : (link.source as GraphNode).id
      const targetId = typeof link.target === 'string' ? link.target : (link.target as GraphNode).id
      if (sourceId === selectedNode) connectedNodes.add(targetId)
      if (targetId === selectedNode) connectedNodes.add(sourceId)
    })
  }

  const handleNodeClick = useCallback(
    (node: GraphNodeObject) => {
      if (selectedNode === node.id) {
        onNodeClick(null) // Deselect
      } else {
        onNodeClick(node.id)
      }
    },
    [selectedNode, onNodeClick]
  )

  const handleNodeHover = useCallback((node: GraphNodeObject | null) => {
    setHoveredNode(node ? node.id : null)
  }, [])

  // Center graph on mount
  useEffect(() => {
    if (graphRef.current) {
      setTimeout(() => {
        graphRef.current?.zoomToFit(400, 50)
      }, 500)
    }
  }, [])

  const nodeCanvasObject = useCallback(
    (node: GraphNodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const label = node.name.split(' ')[0] // First name only
      const fontSize = 12 / globalScale
      ctx.font = `${fontSize}px JetBrains Mono, monospace`

      const isSelected = selectedNode === node.id
      const isConnected = selectedNode ? connectedNodes.has(node.id) : true
      const isHovered = hoveredNode === node.id

      // Node circle
      const radius = isSelected ? 8 : isHovered ? 7 : 6
      ctx.beginPath()
      ctx.arc(node.x!, node.y!, radius, 0, 2 * Math.PI)

      // Color based on state
      if (isSelected) {
        ctx.fillStyle = '#bb9af7' // magenta
      } else if (!isConnected) {
        ctx.fillStyle = '#414868' // dim
      } else if (isHovered) {
        ctx.fillStyle = '#7dcfff' // cyan
      } else {
        ctx.fillStyle = '#7aa2f7' // blue
      }
      ctx.fill()

      // Border
      ctx.strokeStyle = isSelected ? '#bb9af7' : '#565f89'
      ctx.lineWidth = 1.5 / globalScale
      ctx.stroke()

      // Label
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillStyle = isConnected || !selectedNode ? '#c0caf5' : '#565f89'
      ctx.fillText(label, node.x!, node.y! + radius + 2)
    },
    [selectedNode, connectedNodes, hoveredNode]
  )

  const linkCanvasObject = useCallback(
    (link: GraphLinkObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const source = link.source as GraphNodeObject
      const target = link.target as GraphNodeObject

      if (!source.x || !source.y || !target.x || !target.y) return

      const sourceId = typeof link.source === 'string' ? link.source : source.id
      const targetId = typeof link.target === 'string' ? link.target : target.id

      const isHighlighted =
        !selectedNode ||
        connectedNodes.has(sourceId) && connectedNodes.has(targetId)

      ctx.beginPath()
      ctx.moveTo(source.x, source.y)
      ctx.lineTo(target.x, target.y)

      ctx.strokeStyle = isHighlighted ? getEdgeColor(link.score) : '#414868'
      ctx.lineWidth = (isHighlighted ? getEdgeWidth(link.score) : 1) / globalScale
      ctx.stroke()
    },
    [selectedNode, connectedNodes]
  )

  return (
    <ForceGraph2D
      ref={graphRef}
      graphData={filteredGraph}
      width={width}
      height={height}
      backgroundColor="#1a1b26"
      nodeCanvasObject={nodeCanvasObject}
      linkCanvasObject={linkCanvasObject}
      onNodeClick={handleNodeClick}
      onNodeHover={handleNodeHover}
      nodeRelSize={6}
      linkDirectionalParticles={0}
      d3VelocityDecay={0.3}
      warmupTicks={50}
      cooldownTicks={100}
    />
  )
}
