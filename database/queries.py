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


if __name__ == "__main__":
    create_constraints()