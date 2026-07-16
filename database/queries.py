from typing import Any

from database.connection import URI, USERNAME, PASSWORD
from neo4j import GraphDatabase


def create_constraints() -> None:
    """Create uniqueness constraints for the graph node types."""

    driver = GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD),
    )

    constraint_queries = [
        """
        CREATE CONSTRAINT person_id_unique IF NOT EXISTS
        FOR (p:Person)
        REQUIRE p.id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT repository_full_name_unique IF NOT EXISTS
        FOR (r:Repository)
        REQUIRE r.full_name IS UNIQUE
        """,
        """
        CREATE CONSTRAINT file_key_unique IF NOT EXISTS
        FOR (f:File)
        REQUIRE f.key IS UNIQUE
        """,
        """
        CREATE CONSTRAINT commit_key_unique IF NOT EXISTS
        FOR (c:Commit)
        REQUIRE c.key IS UNIQUE
        """,
    ]

    try:
        for query in constraint_queries:
            driver.execute_query(
                query,
                database_="neo4j",
            )

        print("Database constraints created successfully.")

    finally:
        driver.close()

# list repo
def get_repositories() -> list[dict[str, Any]]:
    """Return all repositories currently stored in Neo4j."""

    driver = GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD),
    )

    try:
        records, _, _ = driver.execute_query(
            """
            MATCH (r:Repository)
            RETURN
                r.full_name AS full_name,
                r.name AS name,
                r.owner AS owner,
                r.language AS language,
                r.stars AS stars,
                r.url AS url
            ORDER BY r.full_name
            """,
            database_="neo4j",
        )

        return [record.data() for record in records]

    finally:
        driver.close()

def get_repository_files(
    repository_full_name: str,
) -> list[str]:
    """Return all tracked file paths for one repository."""

    driver = GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD),
    )

    try:
        records, _, _ = driver.execute_query(
            """
            MATCH (f:File)-[:BELONGS_TO]->(
                r:Repository {full_name: $repository_full_name}
            )
            RETURN f.path AS file_path
            ORDER BY file_path
            """,
            repository_full_name=repository_full_name,
            database_="neo4j",
        )

        return [record["file_path"] for record in records]

    finally:
        driver.close()

def search_experts(
    repository_full_name: str,
    file_path: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Rank contributors by their history on a selected file."""

    driver = GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD),
    )

    try:
        records, _, _ = driver.execute_query(
            """
            MATCH (p:Person)-[m:MODIFIED]->(f:File)
                  -[:BELONGS_TO]->(
                      r:Repository {
                          full_name: $repository_full_name
                      }
                  )
            WHERE f.path = $file_path

            RETURN
                p.login AS contributor,
                p.name AS name,
                p.avatar_url AS avatar_url,
                m.count AS commits_on_file,
                m.total_changes AS total_changes,
                m.last_date AS last_active

            ORDER BY
                commits_on_file DESC,
                total_changes DESC,
                last_active DESC

            LIMIT $limit
            """,
            repository_full_name=repository_full_name,
            file_path=file_path,
            limit=limit,
            database_="neo4j",
        )

        return [record.data() for record in records]

    finally:
        driver.close()

def get_bus_factor_risks(
    repository_full_name: str,
) -> list[dict[str, Any]]:
    """
    Return files that have only one historical contributor.

    Such files may represent knowledge-concentration risk.
    """

    driver = GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD),
    )

    try:
        records, _, _ = driver.execute_query(
            """
            MATCH (f:File)-[:BELONGS_TO]->(
                r:Repository {full_name: $repository_full_name}
            )

            MATCH (f)<-[:MODIFIED]-(p:Person)

            WITH
                f,
                count(DISTINCT p) AS contributor_count,
                collect(DISTINCT p.login) AS contributors

            WHERE contributor_count = 1

            RETURN
                f.path AS file_path,
                contributors[0] AS sole_contributor,
                contributor_count

            ORDER BY file_path
            """,
            repository_full_name=repository_full_name,
            database_="neo4j",
        )

        return [record.data() for record in records]

    finally:
        driver.close()


if __name__ == "__main__":
    create_constraints()