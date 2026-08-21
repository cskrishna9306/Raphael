# Roadmap

## Goal

Raphael assembles a film's cast (and eventually its crew) the way a scout builds a fantasy sports team — not just by who's talented or available, but by who works well *together*. Given a director's initial picks (or answers to a few guided questions), Raphael's agents research each candidate — filmography, past collaborators, how those projects performed and were received, and sentiment around those working relationships — and use that history to compute a chemistry score between any two people, and for the team as a whole. A FIFA-style chemistry rating, but for movies. As the director swaps people in and out of the roster, the chemistry score updates live, grounding casting decisions in real collaborative history instead of gut feel alone.

## Roadmap

### MVP
- Actors only, scoped to a single project.
- Offline: research relevant people from a movie, run a deep-research (Parallel) call per person, store results to ClickHouse.
- Online: ask the director guided questions, do an initial roster population via agent, show perceived chemistry (pairwise and team-level) and update it live as the roster changes.

### Beyond MVP
- **More roles**: expand from actors to directors, writers, cinematographers, and the rest of the crew.
- **Richer chemistry**: incorporate genre fit, skills, and critical reception, not just "have they worked together."
- **Real-world constraints**: budget limitations, scheduling conflicts, and availability, so a great team on paper is also one that can actually be assembled.

### Bonus features
- Estimate how much time a cast member needs to give a production (projected hours vs. production timeline/release date).
- Calendar scheduling across cast to surface and avoid conflicts.
