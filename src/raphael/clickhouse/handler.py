# Import standard packages
import json
from typing import Any, Optional, Union

# Import custom packages
from src.raphael.clickhouse.client import ClickHouseClient
from src.raphael.agentry.parallel.models import PersonDossier


_ARRAY_COLUMNS = {
    "primary_roles",
    "awards_and_nominations",
    "documented_controversies",
    "current_and_upcoming_commitments",
    "union_affiliation",
    "languages_and_accents",
    "physical_skills",
}
_NUMERIC_COLUMNS = {"age"}
_SCALAR_STRING_COLUMNS = {"gender", "nationality", "physical_characteristics", "social_media_following"}
_KNOWN_CRITERIA_COLUMNS = _ARRAY_COLUMNS | _NUMERIC_COLUMNS | _SCALAR_STRING_COLUMNS


def _sql_str(value: Optional[str]) -> str:
    """
    Render a Python string as a ClickHouse SQL string literal (NULL if None).
    """
    if value is None:
        return "NULL"
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _sql_array(values: list[str]) -> str:
    """
    Render a list of strings as a ClickHouse Array(String) literal.
    """
    return "[" + ", ".join(_sql_str(v) for v in values) + "]"


def _sql_int(value: Optional[int]) -> str:
    """
    Render an optional int as a ClickHouse SQL literal.
    """
    return "NULL" if value is None else str(value)


def _name_tokens(name: str) -> set[str]:
    """
    Lowercase token set for a person's name, e.g. "Christopher Nolan" -> {"christopher", "nolan"}.
    """
    return {token.casefold() for token in name.strip().split() if token}


def _is_name_variant(name_a: str, name_b: str) -> bool:
    """
    True if one name's token set is a non-empty subset of the other's, e.g.
    "Christopher Nolan" is a variant of "Christopher Edward Nolan".

    Known limitation, accepted for hackathon MVP scale: two genuinely different
    people who happen to share a short name (e.g. two "John Smith"s) will be
    treated as the same person.
    """
    tokens_a, tokens_b = _name_tokens(name_a), _name_tokens(name_b)
    if not tokens_a or not tokens_b:
        return False
    smaller, larger = sorted((tokens_a, tokens_b), key=len)
    return smaller <= larger


def _resolve_canonical_name(name: str, existing_names: list[str]) -> str:
    """
    Map `name` to whatever name is already stored in `people`, if it's an exact
    match or a token-subset variant of one (or more) stored names -- prefers the
    most specific (most tokens) match, alphabetical tiebreak. Falls back to
    `name` unchanged if nothing matches, so a genuinely new person still works.

    Known limitation, accepted for hackathon MVP scale: this always defers to
    whatever is already stored -- it never renames an existing row even if a
    more-complete variant is researched later. Whichever variant is researched
    first becomes the permanent canonical label for that person.
    """
    if name in existing_names:
        return name
    matches = [existing for existing in existing_names if _is_name_variant(name, existing)]
    if not matches:
        return name
    return sorted(matches, key=lambda existing: (-len(_name_tokens(existing)), existing))[0]


def _resolve_canonical_names(names: list[str], existing_names: list[str]) -> list[str]:
    """
    Apply _resolve_canonical_name to every entry, order-preserving.
    """
    return [_resolve_canonical_name(name, existing_names) for name in names]


def _extract_column(result: Optional[Any], column: str) -> list[str]:
    """
    Pull one column's values out of a raw _run_query result (a JSON payload
    {"columns": [...], "rows": [[...], ...]}, possibly wrapped in a list of MCP
    content blocks). Never raises -- returns [] if unparseable/missing.
    """
    text = result
    if isinstance(text, list):
        text = "".join(
            (block.get("text", "") if isinstance(block, dict) else getattr(block, "text", ""))
            for block in text
        )
    if not isinstance(text, str):
        return []
    try:
        payload = json.loads(text)
        idx = payload["columns"].index(column)
        return [row[idx] for row in payload["rows"] if idx < len(row) and row[idx] is not None]
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return []


def _criteria_clause(column: str, value: Union[str, int, list]) -> str:
    """
    Render one criteria entry as a SQL predicate, branching on whether `column`
    is an Array(String) column (needs hasAny(), not =) or a scalar column.
    """
    values = value if isinstance(value, list) else [value]
    if column in _ARRAY_COLUMNS:
        return f"hasAny({column}, {_sql_array([str(v) for v in values])})"
    if column in _NUMERIC_COLUMNS:
        if len(values) > 1:
            return f"{column} IN ({', '.join(_sql_int(v) for v in values)})"
        return f"{column} = {_sql_int(values[0])}"
    if len(values) > 1:
        return f"{column} IN {_sql_array([str(v) for v in values])}"
    return f"{column} = {_sql_str(str(values[0]))}"


def _build_where_clause(criteria: dict[str, Any]) -> str:
    """
    AND-join per-column predicates over the `people` table. Column names come
    from criteria (not user text directly), but can't be parameterized as SQL
    values, so unknown columns are rejected rather than interpolated.
    """
    unknown = set(criteria) - _KNOWN_CRITERIA_COLUMNS
    if unknown:
        raise ValueError(f"Unknown people column(s) in criteria: {sorted(unknown)}")
    if not criteria:
        return "1"
    return " AND ".join(_criteria_clause(column, value) for column, value in criteria.items())


def _build_roster_query(
    criteria: dict[str, Any],
    current_picks: Optional[list[str]],
    limit: int,
) -> str:
    """
    Build the ranked roster SQL: filter `people` by `criteria`, exclude
    `current_picks` from the candidate pool, and rank remaining candidates by
    how many documented collaborations they have with someone already picked.
    """
    where_clause = _build_where_clause(criteria)

    if current_picks:
        picks_array = _sql_array(current_picks)
        return f"""
            WITH collaboration_edges AS (
                SELECT person, collaborator_name FROM collaborations
                UNION ALL
                SELECT collaborator_name AS reverse_person, person AS reverse_collaborator_name FROM collaborations
            ),
            affinity AS (
                SELECT person, uniqExact(collaborator_name) AS affinity_score
                FROM collaboration_edges
                WHERE collaborator_name IN {picks_array}
                GROUP BY person
            )
            SELECT p.*, coalesce(a.affinity_score, 0) AS affinity_score
            FROM people p
            LEFT JOIN affinity a ON a.person = p.name
            WHERE {where_clause}
              AND p.name NOT IN {picks_array}
            ORDER BY affinity_score DESC, p.name ASC
            LIMIT {int(limit)}
        """

    return f"""
        SELECT p.*, 0 AS affinity_score
        FROM people p
        WHERE {where_clause}
        ORDER BY p.name ASC
        LIMIT {int(limit)}
    """


class ClickHouseHandler:
    """
    Small handler that wraps every ClickHouse operation Raphael needs
    (schema setup, inserting research results, point lookups, basic search)
    behind one interface, backed by the mcp-clickhouse tools loaded by
    ClickHouseClient (run_query, list_databases, list_tables).

    Other code should go through this handler rather than touching
    ClickHouseClient/its MCP tools directly.
    """

    def __init__(self):
        """
        Set up (but don't yet open) the underlying MCP-backed ClickHouse client.
        """
        self._client = ClickHouseClient()
        self._tools: dict[str, Any] = {}

    async def __aenter__(self):
        """
        Open the MCP session and index its tools by name.
        """
        await self._client.__aenter__()
        self._tools = {tool.name: tool for tool in self._client.tools}
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Tear down the MCP session.
        """
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def _run_query(self, query: str) -> Optional[Any]:
        """
        Run a raw SQL statement through the run_query MCP tool.
        """
        try:
            return await self._tools["run_query"].ainvoke({"query": query})
        except Exception as e:
            print(f"[ClickHouse] Error running query: {e}\nQuery was: {query}")
            return None

    async def ensure_schema(self) -> None:
        """
        Create the people/credits/collaborations tables if they don't already exist.
        Cheap and idempotent -- safe to call before every read/write.
        """
        await self._run_query(
            """
            CREATE TABLE IF NOT EXISTS people (
                name String,
                bio_summary String,
                primary_roles Array(String),
                awards_and_nominations Array(String),
                documented_controversies Array(String),
                age Nullable(Int32),
                gender Nullable(String),
                nationality Nullable(String),
                physical_characteristics Nullable(String),
                social_media_following Nullable(String),
                current_and_upcoming_commitments Array(String),
                union_affiliation Array(String),
                languages_and_accents Array(String),
                physical_skills Array(String),
                researched_at DateTime DEFAULT now()
            ) ENGINE = MergeTree ORDER BY name
            """
        )
        await self._run_query(
            """
            CREATE TABLE IF NOT EXISTS credits (
                person String,
                title String,
                year Nullable(Int32),
                role String,
                character_or_contribution Nullable(String),
                box_office Nullable(String),
                critical_reception Nullable(String),
                key_collaborators Array(String)
            ) ENGINE = MergeTree ORDER BY (person, year)
            """
        )
        await self._run_query(
            """
            CREATE TABLE IF NOT EXISTS collaborations (
                person String,
                collaborator_name String,
                collaborator_role String,
                shared_projects Array(String),
                public_statements Array(String)
            ) ENGINE = MergeTree ORDER BY (person, collaborator_name)
            """
        )

    async def _fetch_existing_names(self) -> list[str]:
        """
        Fetch every currently-stored people.name, for name-variant canonicalization.
        """
        result = await self._run_query("SELECT name FROM people")
        return _extract_column(result, "name")

    async def insert_person(self, dossier: PersonDossier) -> bool:
        """
        Flatten a PersonDossier (from ParallelClient.research_person) into the
        people/credits/collaborations tables and insert it. Returns True on success.

        The person's own name, and each collaborator's name, are canonicalized
        against already-stored people.name values first (see _resolve_canonical_name)
        so that name variants (e.g. "Christopher Nolan" vs "Christopher Edward Nolan")
        don't create duplicate identities.
        """
        await self.ensure_schema()

        existing_names = await self._fetch_existing_names()
        canonical_name = _resolve_canonical_name(dossier.name, existing_names)

        person_values = (
            f"({_sql_str(canonical_name)}, {_sql_str(dossier.bio_summary)}, "
            f"{_sql_array(dossier.primary_roles)}, "
            f"{_sql_array(dossier.recognition.awards_and_nominations)}, "
            f"{_sql_array(dossier.recognition.documented_controversies)}, "
            f"{_sql_int(dossier.attributes.age)}, {_sql_str(dossier.attributes.gender)}, "
            f"{_sql_str(dossier.attributes.nationality)}, {_sql_str(dossier.attributes.physical_characteristics)}, "
            f"{_sql_str(dossier.attributes.social_media_following)}, "
            f"{_sql_array(dossier.availability.current_and_upcoming_commitments)}, "
            f"{_sql_array(dossier.availability.union_affiliation)}, "
            f"{_sql_array(dossier.skills.languages_and_accents)}, "
            f"{_sql_array(dossier.skills.physical_skills)})"
        )
        result = await self._run_query(
            "INSERT INTO people "
            "(name, bio_summary, primary_roles, awards_and_nominations, documented_controversies, "
            "age, gender, nationality, physical_characteristics, social_media_following, "
            "current_and_upcoming_commitments, union_affiliation, languages_and_accents, physical_skills) "
            f"VALUES {person_values}"
        )
        if result is None:
            return False

        if dossier.filmography:
            credit_rows = ", ".join(
                f"({_sql_str(canonical_name)}, {_sql_str(item.title)}, {_sql_int(item.year)}, "
                f"{_sql_str(item.role)}, {_sql_str(item.character_or_contribution)}, "
                f"{_sql_str(item.box_office)}, {_sql_str(item.critical_reception)}, "
                f"{_sql_array(item.key_collaborators)})"
                for item in dossier.filmography
            )
            result = await self._run_query(
                "INSERT INTO credits "
                "(person, title, year, role, character_or_contribution, box_office, critical_reception, key_collaborators) "
                f"VALUES {credit_rows}"
            )
            if result is None:
                return False

        if dossier.collaborators:
            known_names = existing_names + [canonical_name]
            collaboration_rows = ", ".join(
                f"({_sql_str(canonical_name)}, "
                f"{_sql_str(_resolve_canonical_name(collab.name, known_names))}, "
                f"{_sql_str(collab.role)}, {_sql_array(collab.shared_projects)}, "
                f"{_sql_array(collab.public_statements_about_collaboration)})"
                for collab in dossier.collaborators
            )
            result = await self._run_query(
                "INSERT INTO collaborations "
                "(person, collaborator_name, collaborator_role, shared_projects, public_statements) "
                f"VALUES {collaboration_rows}"
            )
            if result is None:
                return False

        return True

    async def get_person(self, name: str) -> Optional[Any]:
        """
        Point lookup: has this person already been researched?
        """
        await self.ensure_schema()
        return await self._run_query(f"SELECT * FROM people WHERE name = {_sql_str(name)} LIMIT 1")

    async def search_people(self, **criteria: Union[str, int, list]) -> Optional[Any]:
        """
        Basic filtered search over the people table, e.g. search_people(nationality="British")
        or search_people(primary_roles=["Actor"]). Just a filter -- no collaboration-affinity
        ranking; use search_roster for that.
        """
        await self.ensure_schema()
        if not criteria:
            return await self._run_query("SELECT * FROM people")
        return await self._run_query(f"SELECT * FROM people WHERE {_build_where_clause(criteria)}")

    async def search_roster(
        self,
        criteria: Optional[dict[str, Union[str, int, list]]] = None,
        current_picks: Optional[list[str]] = None,
        limit: int = 20,
    ) -> Optional[Any]:
        """
        Rank the researched-people corpus against structured search criteria
        (people-table columns only -- no genre/budget, that's Beyond MVP and
        blocked on the still-unbuilt criteria-translation ticket), favoring
        candidates who've already worked with `current_picks`. Excludes
        `current_picks` themselves from the results.

        `current_picks` are canonicalized against stored people.name values
        first (see _resolve_canonical_name), so e.g. "Christopher Nolan" still
        matches a stored "Christopher Edward Nolan" row.
        """
        await self.ensure_schema()
        if current_picks:
            existing_names = await self._fetch_existing_names()
            current_picks = _resolve_canonical_names(current_picks, existing_names)
        query = _build_roster_query(criteria or {}, current_picks, limit)
        return await self._run_query(query)
