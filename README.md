# Open-Source Contributor Expertise Graph

Finding the right contributor in a large open-source project can be difficult. This project builds a Neo4j knowledge graph from GitHub repositories to identify file experts, surface knowledge concentration risks, and visualize contributor ownership through an interactive Streamlit dashboard.

A Neo4j-powered developer intelligence platform that analyzes GitHub repositories to identify contributor expertise, knowledge concentration, and repository ownership patterns.

## Live Demo

🔗 https://oss-expertise-graph-jt22fcfcyr9onygxoyzdcs.streamlit.app/

## Features

- Identify file experts based on contribution history
- Detect knowledge concentration (Knowledge Risk)
- Analyze multiple GitHub repositories
- Explore contributor ownership across repositories
- 📊 Interactive Streamlit dashboard
- Graph-powered analytics using Neo4j

## Tech Stack

- Python
- Neo4j Aura
- GitHub REST API
- Streamlit
- Pandas

## Dashboard

(<img width="1278" height="872" alt="image" src="https://github.com/user-attachments/assets/98286d32-d126-4374-80e5-c57b731ab95b" />

## Architecture

GitHub API
        ↓
Data Ingestion
        ↓
Neo4j Knowledge Graph
        ↓
Repository Analytics
        ↓
Streamlit Dashboard

## Future Improvements

- GitHub repository search
- Interactive graph visualization
- AI-based reviewer recommendation
- Cross-repository expertise analysis
- Contributor collaboration network

