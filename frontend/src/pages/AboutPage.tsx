import { Link } from "react-router-dom"
import { Panel } from "../components/common/Panel"
import { Button } from "../components/common/Button"
import styles from "./AboutPage.module.css"

const STEPS = [
  {
    number: "01",
    title: "Read",
    body: "Scenes, dialogue and screen time become a character map with weighted roles.",
  },
  {
    number: "02",
    title: "Match",
    body: "Each role draws candidates from the actor pool on range, register and past work.",
  },
  {
    number: "03",
    title: "Cluster",
    body: "Candidates are assembled into up to five full casts, ranked by ensemble chemistry.",
  },
  {
    number: "04",
    title: "Flag",
    body: "Every actor carries a written reputational-risk note, not just a colour.",
  },
]

const CONTRIBUTORS = [
  { initials: "SC", name: "Sai Chaparala", role: "Backend · breakdown & chemistry model" },
  { initials: "MM", name: "Mehul Maheshwari", role: "Interface · roster & risk surfacing" },
]

export function AboutPage() {
  return (
    <Panel className={styles.panel}>
      <div className={styles.hero}>
        <div className={styles.headline}>An agentic casting director that reads the script before it names a name.</div>
        <div className={styles.subhead}>
          Raphael takes a screenplay, works out who the story actually needs, and returns whole casts — not ranked
          individuals. Every recommendation arrives with the reasoning attached: why this ensemble holds together,
          what each name costs you, and where the press risk sits.
        </div>
      </div>

      <div className={styles.section}>
        <div className={styles.label}>How it works</div>
        <div className={styles.steps}>
          {STEPS.map((step) => (
            <div key={step.number} className={styles.step}>
              <div className={styles.stepNumber}>{step.number}</div>
              <div className={styles.stepTitle}>{step.title}</div>
              <div className={styles.stepBody}>{step.body}</div>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.twoColumn}>
        <div className={styles.column}>
          <div className={styles.label}>The chemistry metric</div>
          <p className={styles.paragraph}>
            A pairwise score across shared credits, tonal register and audience response, rolled up into one
            ensemble number. It is a cast-level metric — swapping one actor re-scores everyone around them, which is
            why Raphael returns clusters instead of a leaderboard.
          </p>
        </div>
        <div className={styles.column}>
          <div className={styles.label}>Reputational risk</div>
          <p className={styles.paragraph}>
            A short written summary per actor covering press exposure and public standing, surfaced on the card
            before you commit. Raphael flags; the casting director decides.
          </p>
        </div>
      </div>

      <div className={styles.section}>
        <div className={styles.label}>Contributors</div>
        <div className={styles.contributors}>
          {CONTRIBUTORS.map((contributor) => (
            <div key={contributor.name} className={styles.contributor}>
              <div className={styles.contributorInitials}>{contributor.initials}</div>
              <div>
                <div className={styles.contributorName}>{contributor.name}</div>
                <div className={styles.contributorRole}>{contributor.role}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.footer}>
        <div>
          <div className={styles.label}>Built at</div>
          <div className={styles.footerCopy}>A hackathon project. Recommendations are decision support, not a shortlist to sign.</div>
        </div>
        {/* Signed-out visitors get bounced to /login and returned here after. */}
        <Link to="/ingest">
          <Button variant="primary">Try it on a script →</Button>
        </Link>
      </div>
    </Panel>
  )
}
