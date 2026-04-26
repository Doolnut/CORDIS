# CORDIS Explorer

A local tool for Queensland Trade & Investment to discover EU research organisations from the CORDIS Horizon Europe database.

## Quick Start

### Requirements

- Python 3.10 or later ([download](https://python.org))

### First-time setup

```bash
pip install -r requirements.txt
```

### Run

- **Windows:** Double-click `run.bat`
- **Mac/Linux:** Run `./run.sh` in a terminal

The app opens at `http://localhost:8501`.

### Data

1. Download the CORDIS Horizon Europe data export from the [EU Open Data Portal](https://data.europa.eu/data/datasets/cordis-eu-research-projects-under-horizon-europe-2021-2027).
2. Extract the ZIP and place all CSV files in a folder on your PC.
3. In the app sidebar, enter the path to that folder and click **Load Data**.

Required files: `project.csv`, `organization.csv`, `euroSciVoc.csv`, `topics.csv`, `legalBasis.csv`, `policyPriorities.csv`, `webLink.csv`

## Features

| Tab | What it shows |
|-----|--------------|
| Organisations | Filterable table of all organisations with EC funding totals and project counts |
| Bar Chart | Top 25 organisations ranked by project count or EU funding |
| Map | World map of organisation locations, sized by project count |
| Network | Co-participation graph showing which organisations work together |
| SQL Query | Raw SQL interface with CSV export |

## Filters

Use the sidebar to narrow results by:

- Keyword search (project objectives, keywords, and scientific vocabulary)
- Organisation type (private company, higher education, research org, public body)
- Country
- SME status
- Project status (active/closed)
- Framework programme
- Policy priority tags (AI, climate, biodiversity, etc.)

## Natural Language Queries

This tool includes a Claude Code skill. In Claude Code, type:

```
/cordis
```

Then describe what you want in plain English and Claude will generate SQL ready to paste into the SQL Query tab.

Example: "Show me German biotech companies with active HORIZON projects"

## Organisation Type Codes

| Code | Meaning |
|------|---------|
| PRC | Private for-profit company |
| HES | Higher education institution |
| REC | Research organisation |
| PUB | Public body |
| OTH | Other |

## Data Source

CORDIS Horizon Europe dataset, updated monthly by the Publications Office of the EU. Covers all Horizon Europe projects 2021-2027.
