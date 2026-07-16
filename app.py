from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from database.queries import (
    get_bus_factor_risks,
    get_repositories,
    get_repository_files,
    search_experts,
)


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="OSS Expertise Graph",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# CUSTOM STYLING
# ---------------------------------------------------------

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1450px;
        }

        .hero-container {
            padding: 2.2rem 2.4rem;
            border-radius: 22px;
            background:
                radial-gradient(
                    circle at top right,
                    rgba(255, 75, 75, 0.22),
                    transparent 35%
                ),
                linear-gradient(
                    135deg,
                    rgba(30, 31, 40, 0.98),
                    rgba(17, 18, 24, 0.98)
                );
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 1.8rem;
        }

        .hero-eyebrow {
            color: #ff6b6b;
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.12rem;
            text-transform: uppercase;
            margin-bottom: 0.6rem;
        }

        .hero-title {
            font-size: 2.8rem;
            font-weight: 800;
            line-height: 1.08;
            margin-bottom: 0.8rem;
        }

        .hero-subtitle {
            color: #c7c9d3;
            font-size: 1.05rem;
            line-height: 1.65;
            max-width: 900px;
        }

        .metric-card {
            padding: 1.2rem 1.3rem;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(255, 255, 255, 0.075);
            min-height: 118px;
        }

        .metric-label {
            color: #a9acb8;
            font-size: 0.82rem;
            margin-bottom: 0.45rem;
        }

        .metric-value {
            color: white;
            font-size: 1.55rem;
            font-weight: 700;
            overflow-wrap: anywhere;
        }

        .section-kicker {
            color: #ff6b6b;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.1rem;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }

        .section-description {
            color: #aeb1bc;
            margin-bottom: 1.2rem;
        }

        .expert-card {
            padding: 1.35rem;
            border-radius: 18px;
            background: linear-gradient(
                145deg,
                rgba(255, 255, 255, 0.055),
                rgba(255, 255, 255, 0.022)
            );
            border: 1px solid rgba(255, 255, 255, 0.09);
            margin-bottom: 1rem;
        }

        .rank-badge {
            display: inline-block;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            background: rgba(255, 75, 75, 0.16);
            color: #ff7474;
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .risk-high {
            color: #ff6b6b;
            font-weight: 700;
        }

        .risk-medium {
            color: #ffc857;
            font-weight: 700;
        }

        .risk-low {
            color: #5bd6a2;
            font-weight: 700;
        }

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(255, 255, 255, 0.075);
            padding: 1rem;
            border-radius: 14px;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
        }

        .stButton > button {
            border-radius: 12px;
            font-weight: 700;
            min-height: 3rem;
        }

        .stLinkButton > a {
            border-radius: 12px;
            font-weight: 700;
            min-height: 3rem;
        }

        div[data-baseweb="select"] > div {
            border-radius: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

@st.cache_data(ttl=300)
def load_repositories() -> list[dict[str, Any]]:
    """Load repositories from Neo4j."""
    return get_repositories()


@st.cache_data(ttl=300)
def load_files(repository_full_name: str) -> list[str]:
    """Load tracked files for one repository."""
    return get_repository_files(repository_full_name)


def format_last_active(value: Any) -> str:
    """Convert a Neo4j datetime into a readable date."""

    if value is None:
        return "Unknown"

    try:
        if hasattr(value, "to_native"):
            value = value.to_native()

        if isinstance(value, datetime):
            return value.strftime("%b %d, %Y")

        return str(value)

    except Exception:
        return str(value)


def calculate_expertise_score(expert: dict[str, Any]) -> int:
    """
    Produce a simple explainable expertise score.

    Commit history is weighted more heavily than total line changes.
    """

    commits = expert.get("commits_on_file") or 0
    total_changes = expert.get("total_changes") or 0

    score = (commits * 70) + min(total_changes, 300)

    return int(score)


def rank_medal(rank: int) -> str:
    """Return a medal for the first three contributors."""

    medals = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
    }

    return medals.get(rank, "🏅")


def repository_risk_level(risk_percentage: float) -> tuple[str, str]:
    """Return a readable repository risk level."""

    if risk_percentage >= 75:
        return "High risk", "risk-high"

    if risk_percentage >= 35:
        return "Moderate risk", "risk-medium"

    return "Low risk", "risk-low"


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:
    st.title("🔗 OSS Graph")

    st.caption(
        "Developer knowledge intelligence powered by GitHub activity "
        "and Neo4j."
    )

    st.divider()

    st.markdown("### How it works")

    st.markdown(
        """
        **1. GitHub ingestion**  
        Repository commits and changed files are collected.

        **2. Knowledge graph**  
        Contributors, repositories, and files become connected nodes.

        **3. Expertise analysis**  
        Contributors are ranked using file-level activity.

        **4. Risk detection**  
        Files owned by only one contributor are flagged.
        """
    )

    st.divider()

    st.info(
    "Expertise scores are transparent and rule-based, using commit "
    "frequency, total code changes, and recent activity. Results reflect "
    "the commit history currently ingested into the graph."
)


# ---------------------------------------------------------
# HERO SECTION
# ---------------------------------------------------------

st.markdown(
    """
<div class="hero-container">
    <div class="hero-eyebrow">Neo4j Developer Intelligence</div>
    <div class="hero-title">Open-Source Contributor Expertise Graph</div>
    <div class="hero-subtitle">
        Discover who understands each file, identify the best
        contributor to contact, and detect knowledge-concentration
        risks using real GitHub activity.
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

repositories = load_repositories()

if not repositories:
    st.warning(
        "No repositories were found in Neo4j. "
        "Run the GitHub ingestion script first."
    )
    st.stop()


repository_names = [
    repository["full_name"]
    for repository in repositories
]

selected_repository = st.selectbox(
    "Repository",
    repository_names,
    help="Choose an ingested GitHub repository to analyze.",
)

selected_repository_data = next(
    repository
    for repository in repositories
    if repository["full_name"] == selected_repository
)

files = load_files(selected_repository)

risks = get_bus_factor_risks(selected_repository)

risk_percentage = (
    round((len(risks) / len(files)) * 100, 1)
    if files
    else 0
)

risk_level, risk_class = repository_risk_level(risk_percentage)


# ---------------------------------------------------------
# REPOSITORY OVERVIEW
# ---------------------------------------------------------

st.markdown(
    """
    <div class="section-kicker">Repository overview</div>
    """,
    unsafe_allow_html=True,
)

overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)

overview_values = [
    (
        "📦 Repository",
        selected_repository_data.get("name") or "Unknown",
    ),
    (
        "👤 Owner",
        selected_repository_data.get("owner") or "Unknown",
    ),
    (
        "💻 Primary language",
        selected_repository_data.get("language") or "Unknown",
    ),
    (
        "📄 Files tracked",
        str(len(files)),
    ),
]

for column, (label, value) in zip(
    [
        overview_col1,
        overview_col2,
        overview_col3,
        overview_col4,
    ],
    overview_values,
):
    with column:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


summary_col1, summary_col2, summary_col3 = st.columns([1, 1, 2])

with summary_col1:
    st.metric(
        "⭐ GitHub stars",
        selected_repository_data.get("stars") or 0,
    )

with summary_col2:
    st.metric(
        "⚠️ Knowledge-risk files",
        len(risks),
    )

with summary_col3:
    repository_url = selected_repository_data.get("url")

    if repository_url:
        st.link_button(
            "Open repository on GitHub ↗",
            repository_url,
            use_container_width=True,
        )


st.markdown(
    f"""
    <strong>Knowledge Risk:</strong>
    <span class="{risk_class}">
        {risk_level} · {risk_percentage}%
    </span>
    """,
    unsafe_allow_html=True,
)

st.progress(min(risk_percentage / 100, 1.0))

st.divider()


# ---------------------------------------------------------
# ANALYSIS TABS
# ---------------------------------------------------------

expert_tab, risk_tab, methodology_tab = st.tabs(
    [
        "🎯 File Experts",
        "⚠️ Knowledge Risk",
        "🧠 Methodology",
    ]
)


# ---------------------------------------------------------
# FILE EXPERTS TAB
# ---------------------------------------------------------

with expert_tab:
    st.markdown(
        """
        <div class="section-kicker">Expert recommendation</div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Find the right contributor for a file")

    st.markdown(
        """
        <div class="section-description">
            Contributors are ranked using their historical commit
            frequency, total code changes, and recent activity on the
            selected file.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not files:
        st.info("No tracked files were found for this repository.")

    else:
        selected_file = st.selectbox(
            "File path",
            files,
            help="Select the file for which you need an expert.",
        )

        find_experts_clicked = st.button(
            "Analyze contributor expertise",
            type="primary",
            use_container_width=True,
        )

        if find_experts_clicked:
            experts = search_experts(
                repository_full_name=selected_repository,
                file_path=selected_file,
            )

            if not experts:
                st.info(
                    "No contributor history was found for this file."
                )

            else:
                st.success(
                    f"Found {len(experts)} contributor"
                    f"{'s' if len(experts) != 1 else ''} "
                    f"with experience on `{selected_file}`."
                )

                st.subheader(f"Recommended experts for `{selected_file}`")

                for rank, expert in enumerate(experts, start=1):
                    contributor = (
                        expert.get("contributor")
                        or expert.get("name")
                        or "Unknown contributor"
                    )

                    display_name = (
                        expert.get("name")
                        or contributor
                    )

                    avatar_url = expert.get("avatar_url")
                    commits = expert.get("commits_on_file") or 0
                    total_changes = expert.get("total_changes") or 0

                    last_active = format_last_active(
                        expert.get("last_active")
                    )

                    expertise_score = calculate_expertise_score(expert)

                    with st.container(border=True):
                        avatar_col, details_col = st.columns(
                            [1, 6],
                            vertical_alignment="center",
                        )

                        with avatar_col:
                            if avatar_url:
                                st.image(
                                    avatar_url,
                                    width=92,
                                )
                            else:
                                st.markdown("## 👤")

                        with details_col:
                            st.markdown(
                                f"""
                                <span class="rank-badge">
                                    {rank_medal(rank)} Rank #{rank}
                                </span>

                                ### {display_name}

                                GitHub account: **@{contributor}**
                                """,
                                unsafe_allow_html=True,
                            )

                            stat1, stat2, stat3, stat4 = st.columns(4)

                            with stat1:
                                st.metric(
                                    "Expertise score",
                                    expertise_score,
                                )

                            with stat2:
                                st.metric(
                                    "Commits on file",
                                    commits,
                                )

                            with stat3:
                                st.metric(
                                    "Total changes",
                                    total_changes,
                                )

                            with stat4:
                                st.metric(
                                    "Last active",
                                    last_active,
                                )

                            if rank == 1:
                                st.caption(
                                    "Top recommendation based on the "
                                    "strongest historical file activity."
                                )


# ---------------------------------------------------------
# KNOWLEDGE RISK TAB
# ---------------------------------------------------------

with risk_tab:
    st.markdown(
        """
        <div class="section-kicker">Repository resilience</div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Knowledge Risk Analysis")

    st.markdown(
        """
        <div class="section-description">
            Project knowledge is considered concentrated when only one historical
            contributor has modified a file. These files may become difficult
            to maintain if that contributor is unavailable.
        </div>
        """,
        unsafe_allow_html=True,
    )

    risk_col1, risk_col2, risk_col3 = st.columns(3)

    with risk_col1:
        st.metric(
            "Total files",
            len(files),
        )

    with risk_col2:
        st.metric(
            "Knowledge-risk files",
            len(risks),
        )

    with risk_col3:
        st.metric(
            "Risk coverage",
            f"{risk_percentage}%",
        )

    st.progress(min(risk_percentage / 100, 1.0))

    if not risks:
        st.success(
            "No files with concentrated contributor knowledge were detected."
        )

    else:
        risks_dataframe = pd.DataFrame(risks)

        risks_dataframe["Risk level"] = "High"
        risks_dataframe["Recommendation"] = (
            "Add a second reviewer or maintainer"
        )

        risks_dataframe = risks_dataframe.rename(
            columns={
                "file_path": "File",
                "sole_contributor": "Sole contributor",
                "contributor_count": "Contributor count",
            }
        )

        display_columns = [
            "File",
            "Sole contributor",
            "Risk level",
            "Recommendation",
        ]

        st.dataframe(
            risks_dataframe[display_columns],
            use_container_width=True,
            hide_index=True,
            column_config={
                "File": st.column_config.TextColumn(
                    width="large"
                ),
                "Risk level": st.column_config.TextColumn(
                    width="small"
                ),
                "Recommendation": st.column_config.TextColumn(
                    width="large"
                ),
            },
        )


# ---------------------------------------------------------
# METHODOLOGY TAB
# ---------------------------------------------------------

with methodology_tab:
    st.subheader("How expertise is calculated")

    st.write(
        "The current recommendation system uses a transparent, "
        "rule-based score rather than an unexplained machine-learning "
        "model."
    )

    methodology_col1, methodology_col2 = st.columns(2)

    with methodology_col1:
        st.markdown(
            """
            #### Expertise signals

            - Number of commits touching the file
            - Total additions and deletions
            - Most recent activity date
            - Historical connection between contributor and file
            """
        )

    with methodology_col2:
        st.markdown(
            """
            #### Graph model

            ```text
            Person ──MODIFIED──> File
              │                   │
              └─CONTRIBUTES_TO─> Repository
                                  ▲
                      File ─BELONGS_TO─┘
            ```
            """
        )

    st.info(
        "Future versions can also incorporate pull-request reviews, "
        "issue discussions, code ownership, and recency decay."
    )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "Built with Python · Streamlit · GitHub REST API · Neo4j Aura | "
    "Analyzing contributor expertise and knowledge risk across repositories."
)