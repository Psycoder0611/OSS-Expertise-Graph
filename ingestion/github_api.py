import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = "https://api.github.com"


def create_session() -> requests.Session:
    """Create a reusable authenticated GitHub API session."""

    if not GITHUB_TOKEN:
        raise ValueError(
            "GITHUB_TOKEN is missing. Add it to the .env file."
        )

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )

    return session


def get_repository(
    owner: str,
    repository: str,
) -> dict[str, Any]:
    """Retrieve basic information for one public GitHub repository."""

    session = create_session()

    url = f"{BASE_URL}/repos/{owner}/{repository}"

    response = session.get(
        url,
        timeout=30,
    )
    response.raise_for_status()

    return response.json()

def get_commits(
    owner: str,
    repository: str,
    per_page: int = 10,
) -> list[dict[str, Any]]:
    """
    Retrieve the most recent commits from a GitHub repository.

    Parameters
    ----------
    owner:
        GitHub username or organization that owns the repository.
    repository:
        Name of the GitHub repository.
    per_page:
        Number of recent commits to retrieve.
    """

    session = create_session()

    url = f"{BASE_URL}/repos/{owner}/{repository}/commits"

    response = session.get(
        url,
        params={"per_page": per_page},
        timeout=30,
    )

    response.raise_for_status()

    return response.json()

def get_commit_details(
    owner: str,
    repository: str,
    sha: str,
) -> dict[str, Any]:
    """
    Retrieve complete information for one commit.

    The detailed response includes the files changed
    by that commit.
    """

    session = create_session()

    url = (
        f"{BASE_URL}/repos/"
        f"{owner}/{repository}/commits/{sha}"
    )

    response = session.get(
        url,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()

def test_github_connection() -> None:
    """Test the GitHub API using a small public repository."""

    repository = get_repository(
        owner="octocat",
        repository="Hello-World",
    )

    print("GitHub API connection successful!")
    print("Repository:", repository["full_name"])
    print("Description:", repository["description"])
    print("Stars:", repository["stargazers_count"])
    print("Default branch:", repository["default_branch"])

def test_get_commits() -> None:
    """Retrieve and display recent commits from the test repository."""

    commits = get_commits(
        owner="octocat",
        repository="Hello-World",
        per_page=5,
    )

    print("\nRecent commits")
    print("-" * 60)

    for commit in commits:
        sha = commit["sha"]

        commit_data = commit["commit"]
        message = commit_data["message"]
        author_name = commit_data["author"]["name"]
        commit_date = commit_data["author"]["date"]

        github_author = commit.get("author")

        if github_author:
            github_login = github_author["login"]
        else:
            github_login = "No linked GitHub account"

        print("SHA:", sha[:7])
        print("Author name:", author_name)
        print("GitHub login:", github_login)
        print("Date:", commit_date)
        print("Message:", message)
        print("-" * 60)

def test_get_commit_details() -> None:
    """
    Retrieve the latest commit and display
    the files changed in that commit.
    """

    owner = "octocat"
    repository = "Hello-World"

    commits = get_commits(
        owner=owner,
        repository=repository,
        per_page=1,
    )

    if not commits:
        print("No commits were found.")
        return

    latest_commit = commits[0]
    full_sha = latest_commit["sha"]

    details = get_commit_details(
        owner=owner,
        repository=repository,
        sha=full_sha,
    )

    print("\nLatest commit details")
    print("-" * 60)
    print("Full SHA:", full_sha)
    print("Message:", details["commit"]["message"])

    files = details.get("files", [])

    print("Number of changed files:", len(files))
    print("-" * 60)

    for file_data in files:
        print("File:", file_data["filename"])
        print("Status:", file_data["status"])
        print("Additions:", file_data["additions"])
        print("Deletions:", file_data["deletions"])
        print("Total changes:", file_data["changes"])
        print("-" * 60)

if __name__ == "__main__":
    test_github_connection()
    test_get_commits()
    test_get_commit_details()