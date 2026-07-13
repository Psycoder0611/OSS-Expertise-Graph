import os

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

# Read variables from the .env file.
load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")


def test_connection() -> None:
    """Connect to Neo4j Aura and verify that the database is reachable."""

    if not URI or not USERNAME or not PASSWORD:
        raise ValueError(
            "Missing Neo4j credentials. Check NEO4J_URI, "
            "NEO4J_USERNAME, and NEO4J_PASSWORD in the .env file."
        )

    driver = GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD),
    )

    try:
        driver.verify_connectivity()

        records, _, _ = driver.execute_query(
            """
            RETURN
                'Connected to Neo4j successfully!' AS message,
                2 + 3 AS test_value
            """,
            database_="neo4j",
        )

        print(records[0]["message"])
        print("Test calculation:", records[0]["test_value"])

    except AuthError:
        print("Authentication failed. Check the Neo4j username and password.")

    except ServiceUnavailable:
        print("Neo4j is unavailable. Check the URI and internet connection.")

    finally:
        driver.close()


if __name__ == "__main__":
    test_connection()