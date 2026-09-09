import { useMemo, useState } from "react"
import type { CastingSelection } from "../../api/types"
import styles from "./EnsembleGraph.module.css"

interface EnsembleGraphProps {
  selections: CastingSelection[]
  linkedName: string | null
  onLinkChange: (name: string | null) => void
}

interface GraphNode {
  name: string
  character: string
  x: number
  y: number
  angle: number
}

interface GraphEdge {
  a: GraphNode
  b: GraphNode
  projects: string[]
}

const VIEW_W = 560
const VIEW_H = 400
const CENTRE_X = VIEW_W / 2
const CENTRE_Y = VIEW_H / 2
const RADIUS = 128

/** Lowercased token set, e.g. "Tessa Thompson" -> {tessa, thompson}. */
function tokens(name: string): Set<string> {
  return new Set(
    name
      .toLowerCase()
      .replace(/[^a-z\s'-]/g, "")
      .split(/\s+/)
      .filter(Boolean),
  )
}

/**
 * True when one name's tokens are a subset of the other's, so "Samuel Jackson"
 * matches a dossier's "Samuel L. Jackson". Mirrors how the backend reconciles
 * name variants when it stores people.
 */
function isSamePerson(a: string, b: string): boolean {
  const ta = tokens(a)
  const tb = tokens(b)
  if (ta.size === 0 || tb.size === 0) return false
  const [smaller, larger] = ta.size <= tb.size ? [ta, tb] : [tb, ta]
  for (const token of smaller) if (!larger.has(token)) return false
  return true
}

/**
 * Builds the collaboration graph for one cast from the dossiers already in the
 * report -- each candidate's `collaborators[].shared_projects` names the
 * productions two actors are both credited on. An edge means documented shared
 * history, never a predicted affinity.
 */
function buildGraph(selections: CastingSelection[]): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const seen = new Set<string>()
  const unique = selections.filter((selection) => {
    if (seen.has(selection.candidate.name)) return false
    seen.add(selection.candidate.name)
    return true
  })

  const nodes: GraphNode[] = unique.map((selection, index) => {
    // -90deg so the first actor sits at the top rather than at 3 o'clock.
    const angle = (index / unique.length) * Math.PI * 2 - Math.PI / 2
    return {
      name: selection.candidate.name,
      character: selection.character.name,
      angle,
      x: CENTRE_X + Math.cos(angle) * RADIUS,
      y: CENTRE_Y + Math.sin(angle) * RADIUS,
    }
  })

  const edges: GraphEdge[] = []
  for (let i = 0; i < unique.length; i += 1) {
    for (let j = i + 1; j < unique.length; j += 1) {
      const forward = unique[i].candidate.dossier?.collaborators ?? []
      const backward = unique[j].candidate.dossier?.collaborators ?? []

      const projects = new Set<string>()
      for (const collaborator of forward) {
        if (isSamePerson(collaborator.name, unique[j].candidate.name)) {
          collaborator.shared_projects.forEach((project) => projects.add(project))
        }
      }
      for (const collaborator of backward) {
        if (isSamePerson(collaborator.name, unique[i].candidate.name)) {
          collaborator.shared_projects.forEach((project) => projects.add(project))
        }
      }

      if (projects.size > 0) {
        edges.push({ a: nodes[i], b: nodes[j], projects: [...projects] })
      }
    }
  }

  return { nodes, edges }
}

export function EnsembleGraph({ selections, linkedName, onLinkChange }: EnsembleGraphProps) {
  const { nodes, edges } = useMemo(() => buildGraph(selections), [selections])
  const [hoveredEdge, setHoveredEdge] = useState<GraphEdge | null>(null)

  const maxProjects = Math.max(1, ...edges.map((edge) => edge.projects.length))
  const totalCredits = edges.reduce((sum, edge) => sum + edge.projects.length, 0)

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <h3 className={styles.label}>Collaboration graph</h3>
        <span className={styles.summary}>
          {edges.length === 0
            ? "no documented shared credits"
            : `${edges.length} ${edges.length === 1 ? "pair" : "pairs"} · ${totalCredits} shared ${totalCredits === 1 ? "credit" : "credits"}`}
        </span>
      </div>

      <div className={styles.figure}>
        <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} className={styles.svg} role="img" aria-label="Actor collaboration graph">
          {/* Reference ring: makes the radial arrangement read as a deliberate
              structure rather than nodes floating in space. */}
          <circle cx={CENTRE_X} cy={CENTRE_Y} r={RADIUS} fill="none" stroke="var(--color-border-dashed)" strokeWidth="1" />

          {edges.map((edge, index) => {
            const isHovered = hoveredEdge === edge
            const touchesLinked = linkedName === edge.a.name || linkedName === edge.b.name
            const active = isHovered || touchesLinked
            return (
              <line
                key={index}
                x1={edge.a.x}
                y1={edge.a.y}
                x2={edge.b.x}
                y2={edge.b.y}
                stroke={active ? "var(--color-accent)" : "var(--color-accent-dim)"}
                strokeWidth={1 + (edge.projects.length / maxProjects) * 3.5}
                strokeOpacity={active ? 0.95 : linkedName ? 0.18 : 0.45}
                strokeLinecap="round"
                className={styles.edge}
                onMouseEnter={() => setHoveredEdge(edge)}
                onMouseLeave={() => setHoveredEdge(null)}
              />
            )
          })}

          {nodes.map((node) => {
            const isLinked = linkedName === node.name
            // Labels flip side at the vertical midline so they always read
            // outward and never overlap the ring.
            const isRight = Math.cos(node.angle) >= 0
            const labelX = CENTRE_X + Math.cos(node.angle) * (RADIUS + 16)
            const labelY = CENTRE_Y + Math.sin(node.angle) * (RADIUS + 16)
            return (
              <g
                key={node.name}
                className={styles.node}
                onMouseEnter={() => onLinkChange(node.name)}
                onMouseLeave={() => onLinkChange(null)}
              >
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={isLinked ? 7 : 5}
                  fill={isLinked ? "var(--color-accent)" : "var(--color-panel-inset)"}
                  stroke="var(--color-accent)"
                  strokeWidth="1.5"
                />
                <text
                  x={labelX}
                  y={labelY}
                  textAnchor={isRight ? "start" : "end"}
                  dominantBaseline="middle"
                  className={isLinked ? styles.nodeLabelActive : styles.nodeLabel}
                  fill={isLinked ? "var(--color-text)" : "var(--color-text-faint)"}
                >
                  {node.name}
                </text>
              </g>
            )
          })}
        </svg>

        {/* Reserved slot rather than a floating tooltip, so hovering an edge
            never shifts the layout underneath the pointer. */}
        <div className={styles.readout}>
          {hoveredEdge ? (
            <>
              <span className={styles.readoutPair}>
                {hoveredEdge.a.name} &amp; {hoveredEdge.b.name}
              </span>
              <span className={styles.readoutProjects}>{hoveredEdge.projects.join(" · ")}</span>
            </>
          ) : edges.length === 0 ? (
            <span className={styles.readoutHint}>
              None of these actors share a documented credit. Chemistry here rests on the predicted signal, not observed history.
            </span>
          ) : (
            <span className={styles.readoutHint}>Hover a line to see the productions two actors share.</span>
          )}
        </div>
      </div>
    </div>
  )
}
