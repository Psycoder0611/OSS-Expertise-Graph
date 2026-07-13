from pathlib import Path
from typing import Any

from neo4j import GraphDatabase

from database.connection import PASSWORD, URI, USERNAME
from ingestion.github_api import (
    get_commit_details,
    get_commits,
    get_repository,
)


def get_file_extension(file_path: str) -> str:
    """
    Return the file extension without the leading dot.

    Examples:
        "src/app.py" -> "py"
        "README" -> ""
    """
    return Path(file_path).suffix.lstrip(".")


def extract_contributor(commit: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize contributor information from one GitHub commit.

    GitHub stores:
    - Git author information inside commit["commit"]["author"]
    - Linked GitHub account information inside commit["author"]

    Some commits are not linked to a GitHub account, so we need a fallback.
    """

    git_author = commit["commit"]["author"]
    github_author = commit.get("author")

    if github_author:
        return {
            "id": str(github_author["id"]),
            "login": github_author["login"],
            "name": git_author.get("name"),
            "avatar_url": github_author.get("avatar_url"),
        }

    author_name = git_author.get("name") or "Unknown contributor"
    author_email = git_author.get("email") or "unknown"

    return {
        "id": f"unlinked:{author_email}",
        "login": author_name,
        "name": author_name,
        "avatar_url": None,
    }


def ingest_repository(
    owner: str,
    repository: str,
    commit_limit: int = 10,
) -> None:
    """
    Load one GitHub repository and its recent commit activity into Neo4j.
    """

    repository_data = get_repository(
        owner=owner,
        repository=repository,
    )

    commits = get_commits(
        owner=owner,
        repository=repository,
        per_page=commit_limit,
    )

    repository_full_name = repository_data["full_name"]

    driver = GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD),
    )

    try:
        driver.execute_query(
            """
            MERGE (r:Repository {full_name: $full_name})
            SET
                r.name = $name,
                r.owner = $owner,
                r.language = $language,
                r.stars = $stars,
                r.url = $url
            """,
            full_name=repository_full_name,
            name=repository_data["name"],
            owner=repository_data["owner"]["login"],
            language=repository_data.get("language"),
            stars=repository_data.get("stargazers_count", 0),
            url=repository_data.get("html_url"),
            database_="neo4j",
        )

        processed_commits = 0
        processed_files = 0

        for commit in commits:
            contributor = extract_contributor(commit)
            commit_date = commit["commit"]["author"]["date"]
            full_sha = commit["sha"]

            details = get_commit_details(
                owner=owner,
                repository=repository,
                sha=full_sha,
            )

            changed_files = details.get("files", [])

            for file_data in changed_files:
                file_path = file_data["filename"]
                file_key = f"{repository_full_name}:{file_path}"

                driver.execute_query(
                    """
                    MATCH (r:Repository {full_name: $repository_full_name})

                    MERGE (p:Person {id: $person_id})
                    SET
                        p.login = $login,
                        p.name = $person_name,
                        p.avatar_url = $avatar_url

                    MERGE (f:File {key: $file_key})
                    SET
                        f.path = $file_path,
                        f.extension = $extension,
                        f.status = $status

                    MERGE (p)-[:CONTRIBUTES_TO]->(r)
                    MERGE (f)-[:BELONGS_TO]->(r)

                    MERGE (p)-[m:MODIFIED]->(f)
                    ON CREATE SET
                        m.count = 1,
                        m.last_date = datetime($commit_date),
                        m.total_changes = $total_changes
                    ON MATCH SET
                        m.count = m.count + 1,
                        m.last_date =
                            CASE
                                WHEN datetime($commit_date) > m.last_date
                                THEN datetime($commit_date)
                                ELSE m.last_date
                            END,
                        m.total_changes =
                            coalesce(m.total_changes, 0) + $total_changes
                    """,
                    repository_full_name=repository_full_name,
                    person_id=contributor["id"],
                    login=contributor["login"],
                    person_name=contributor["name"],
                    avatar_url=contributor["avatar_url"],
                    file_key=file_key,
                    file_path=file_path,
                    extension=get_file_extension(file_path),
                    status=file_data.get("status"),
                    commit_date=commit_date,
                    total_changes=file_data.get("changes", 0),
                    database_="neo4j",
                )

                processed_files += 1

            processed_commits += 1

        print("Repository ingestion completed successfully.")
        print("Repository:", repository_full_name)
        print("Commits processed:", processed_commits)
        print("File changes processed:", processed_files)

    finally:
        driver.close()


if __name__ == "__main__":
    ingest_repository(
        owner="Psycoder0611",
        repository="OSS-Expertise-Graph",
        commit_limit=20,
    )