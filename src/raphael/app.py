# Import standard packages
import asyncio
from typing import Optional

# Import third-party packages
import streamlit as st

# Import custom modules
from src.raphael.tmdb.client import TMDBClient
from src.raphael.tmdb.models import CastMember
from src.raphael.clickhouse.handler import ClickHouseHandler
from src.raphael.agentry.parallel.models import PersonDossier
from src.raphael.chemistry.engine import ChemistryEngine
from src.raphael.roster.chemistry_view import build_roster_report, team_chemistry

CAST_LIMIT = 10
PROFILE_IMAGE_BASE = "https://image.tmdb.org/t/p/w300"

st.set_page_config(page_title="Raphael", page_icon="🎬", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp {
        background: radial-gradient(circle at 20% 0%, #1a1420 0%, #0b0b10 45%, #08080c 100%);
        color: #ece7f0;
    }

    h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 0.03em; }

    .raphael-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3.2rem;
        letter-spacing: 0.08em;
        background: linear-gradient(90deg, #d4af37, #f4e2a1 40%, #d4af37);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .raphael-subtitle { color: #9d94ab; font-size: 1.05rem; margin-top: -0.3rem; }

    .cast-card {
        background: linear-gradient(155deg, #17131f 0%, #100d16 100%);
        border: 1px solid #2c2438;
        border-radius: 14px;
        padding: 14px;
        text-align: center;
        transition: transform 0.15s ease, border-color 0.15s ease;
        height: 100%;
    }
    .cast-card:hover { transform: translateY(-4px); border-color: #d4af37; }
    .cast-card.missing { opacity: 0.45; }

    .cast-photo {
        width: 100%; aspect-ratio: 2/3; object-fit: cover;
        border-radius: 10px; margin-bottom: 10px;
        border: 1px solid #2c2438;
    }
    .cast-photo-placeholder {
        width: 100%; aspect-ratio: 2/3; border-radius: 10px; margin-bottom: 10px;
        display: flex; align-items: center; justify-content: center;
        background: #1c1826; color: #4d4360; font-size: 2rem;
        font-family: 'Bebas Neue', sans-serif; border: 1px solid #2c2438;
    }
    .cast-name { font-weight: 600; font-size: 0.95rem; color: #f2eefa; }
    .cast-meta { font-size: 0.8rem; color: #9d94ab; margin-top: 2px; }
    .cast-badge {
        display: inline-block; margin-top: 8px; padding: 2px 10px;
        border-radius: 999px; font-size: 0.7rem; letter-spacing: 0.04em;
    }
    .badge-known { background: #2c2438; color: #d4af37; }
    .badge-missing { background: #241a1a; color: #c97a7a; }

    .chem-panel {
        background: linear-gradient(155deg, #17131f 0%, #100d16 100%);
        border: 1px solid #2c2438; border-radius: 14px; padding: 20px 24px;
    }
    .chem-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 0; border-bottom: 1px solid #221d2c;
    }
    .chem-row:last-child { border-bottom: none; }
    .chem-pair { font-weight: 600; color: #f2eefa; }
    .chem-shared { font-size: 0.8rem; color: #9d94ab; }
    .chem-score {
        font-family: 'Bebas Neue', sans-serif; font-size: 1.3rem; color: #d4af37;
        min-width: 70px; text-align: right;
    }
    .team-score {
        font-family: 'Bebas Neue', sans-serif; font-size: 3rem; color: #d4af37;
        letter-spacing: 0.05em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_async(coro):
    """Streamlit callbacks are sync -- this is the one seam that bridges into our async handlers."""
    return asyncio.run(coro)


async def _load_movie(title: str) -> tuple[list[tuple[CastMember, PersonDossier]], list[CastMember]]:
    """
    Pull `title`'s top-billed cast from TMDB, then look each one up in ClickHouse.
    Returns (found, missing) -- found people have a full PersonDossier attached,
    missing ones don't (they haven't been researched via `movie-cast`/`add-person` yet).
    """
    tmdb_client = TMDBClient()
    credits = await tmdb_client.find_movie_credits(title)
    if credits is None:
        return [], []

    top_cast = sorted(credits.cast, key=lambda m: m.order if m.order is not None else 999)[:CAST_LIMIT]

    found: list[tuple[CastMember, PersonDossier]] = []
    missing: list[CastMember] = []
    async with ClickHouseHandler() as handler:
        for member in top_cast:
            dossier = await handler.get_person_dossier(member.name)
            if dossier is not None:
                found.append((member, dossier))
            else:
                missing.append(member)
    return found, missing


def _cast_card_html(name: str, subtitle: str, profile_path: Optional[str], known: bool) -> str:
    if profile_path:
        photo = f'<img class="cast-photo" src="{PROFILE_IMAGE_BASE}{profile_path}" />'
    else:
        initials = "".join(part[0] for part in name.split()[:2]).upper()
        photo = f'<div class="cast-photo-placeholder">{initials}</div>'
    badge = (
        '<span class="cast-badge badge-known">researched</span>'
        if known
        else '<span class="cast-badge badge-missing">not yet researched</span>'
    )
    card_class = "cast-card" if known else "cast-card missing"
    return f"""
        <div class="{card_class}">
            {photo}
            <div class="cast-name">{name}</div>
            <div class="cast-meta">{subtitle}</div>
            {badge}
        </div>
    """


st.markdown('<div class="raphael-title">RAPHAEL</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="raphael-subtitle">Cast chemistry, grounded in real collaboration history.</div>',
    unsafe_allow_html=True,
)
st.write("")

input_col, button_col = st.columns([5, 1])
with input_col:
    title_input = st.text_input(
        "Movie title", placeholder="e.g. Oppenheimer", label_visibility="collapsed"
    )
with button_col:
    load_clicked = st.button("Load cast", use_container_width=True, type="primary")

if load_clicked and title_input.strip():
    with st.spinner(f"Pulling '{title_input}' from TMDB and ClickHouse..."):
        found, missing = run_async(_load_movie(title_input.strip()))
    st.session_state["movie_title"] = title_input.strip()
    st.session_state["found"] = found
    st.session_state["missing"] = missing
    st.session_state["included"] = {member.name for member, _ in found}

if "found" in st.session_state:
    found: list[tuple[CastMember, PersonDossier]] = st.session_state["found"]
    missing: list[CastMember] = st.session_state["missing"]

    if not found and not missing:
        st.warning(f"No TMDB match found for '{st.session_state['movie_title']}'.")
    else:
        st.subheader(st.session_state["movie_title"])
        st.caption(f"{len(found)} researched · {len(missing)} not yet researched (top {CAST_LIMIT} billed)")

        cols = st.columns(5)
        for i, (member, dossier) in enumerate(found):
            with cols[i % 5]:
                subtitle = member.character or (dossier.primary_roles[0] if dossier.primary_roles else "")
                st.markdown(
                    _cast_card_html(member.name, subtitle, member.profile_path, known=True),
                    unsafe_allow_html=True,
                )
                st.checkbox(
                    "Include",
                    value=member.name in st.session_state["included"],
                    key=f"include_{member.name}",
                )
        for j, member in enumerate(missing):
            with cols[(len(found) + j) % 5]:
                st.markdown(
                    _cast_card_html(member.name, member.character or "", member.profile_path, known=False),
                    unsafe_allow_html=True,
                )

        st.session_state["included"] = {
            member.name for member, _ in found if st.session_state.get(f"include_{member.name}", True)
        }
        included_names = st.session_state["included"]
        included_dossiers = [dossier for member, dossier in found if member.name in included_names]

        st.write("")
        st.divider()

        if len(included_dossiers) < 2:
            st.info("Include at least two researched cast members to see their chemistry.")
        else:
            report = build_roster_report(st.session_state["movie_title"], included_dossiers)
            graph = ChemistryEngine().build_graph(report)
            score = team_chemistry(graph, list(included_names))

            possible_pairs = len(included_dossiers) * (len(included_dossiers) - 1) // 2
            documented_pairs = len(graph.edges)

            score_col, meta_col = st.columns([1, 2])
            with score_col:
                st.markdown('<div class="chem-panel">', unsafe_allow_html=True)
                st.markdown("**TEAM CHEMISTRY**")
                st.markdown(f'<div class="team-score">{score:.2f}</div>', unsafe_allow_html=True)
                st.caption(f"{documented_pairs} of {possible_pairs} possible pairs have documented shared history.")
                st.markdown("</div>", unsafe_allow_html=True)

            with meta_col:
                st.markdown('<div class="chem-panel">', unsafe_allow_html=True)
                st.markdown("**PAIRWISE CHEMISTRY**")
                if not graph.edges:
                    st.caption("No documented shared history among the included cast yet.")
                else:
                    for edge in sorted(graph.edges, key=lambda e: e.weight or 0.0, reverse=True):
                        shared = ", ".join(c.title for c in edge.shared_credits[:3])
                        st.markdown(
                            f"""
                            <div class="chem-row">
                                <div>
                                    <div class="chem-pair">{edge.source} ↔ {edge.target}</div>
                                    <div class="chem-shared">{shared}</div>
                                </div>
                                <div class="chem-score">{(edge.weight or 0.0):.2f}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                st.markdown("</div>", unsafe_allow_html=True)
