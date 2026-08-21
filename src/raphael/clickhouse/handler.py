# Import standard packages
from typing import Any, Optional

# Import custom packages
from src.raphael.clickhouse.client import ClickHouseClient
from src.raphael.agentry.parallel.models import PersonDossier


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

    async def insert_person(self, dossier: PersonDossier) -> bool:
        """
        Flatten a PersonDossier (from ParallelClient.research_person) into the
        people/credits/collaborations tables and insert it. Returns True on success.
        """
        await self.ensure_schema()

        person_values = (
            f"({_sql_str(dossier.name)}, {_sql_str(dossier.bio_summary)}, "
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
                f"({_sql_str(dossier.name)}, {_sql_str(item.title)}, {_sql_int(item.year)}, "
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
            collaboration_rows = ", ".join(
                f"({_sql_str(dossier.name)}, {_sql_str(collab.name)}, {_sql_str(collab.role)}, "
                f"{_sql_array(collab.shared_projects)}, {_sql_array(collab.public_statements_about_collaboration)})"
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

    async def search_people(self, **criteria: str) -> Optional[Any]:
        """
        Basic filtered search over the people table, e.g. search_people(nationality="British").
        Deliberately modest -- full roster ranking (genre/budget/collaboration-weighted) is
        separate, still-unbuilt work.
        """
        await self.ensure_schema()
        if not criteria:
            return await self._run_query("SELECT * FROM people")

        where_clause = " AND ".join(f"{column} = {_sql_str(value)}" for column, value in criteria.items())
        return await self._run_query(f"SELECT * FROM people WHERE {where_clause}")
