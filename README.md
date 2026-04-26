# CORDIS Explorer

A local tool for Queensland Trade & Investment to discover and assess EU research organisations from the CORDIS Horizon Europe database.

## Quick Start

### Requirements

- Python 3.10 or later ([download](https://python.org))
- Streamlit 1.37 or later (installed via requirements)

### First-time setup

```bash
pip install -r requirements.txt
```

### Run

- **Windows:** Double-click `run.bat`
- **Mac/Linux:** Run `./run.sh` in a terminal

The app opens at `http://localhost:8501` (local access only).

### Data

1. Download the CORDIS Horizon Europe data export from the [EU Open Data Portal](https://data.europa.eu/data/datasets/cordis-eu-research-projects-under-horizon-europe-2021-2027).
2. Extract the ZIP and place all CSV files in a folder on your PC.
3. In the app sidebar, enter the path to that folder and click **Load Data**.

Required files: `project.csv`, `organization.csv`, `euroSciVoc.csv`, `topics.csv`, `legalBasis.csv`, `policyPriorities.csv`, `webLink.csv`

---

## Features

### Views

| Tab | What it shows |
|-----|--------------|
| Organisations | Filterable table of all organisations with EC funding totals and project counts |
| Bar Chart | Top 25 organisations ranked by project count or total EU funding |
| Map | World map of organisation locations, sized by project count |
| Network | Co-participation graph — organisations linked by shared projects |
| SQL Query | Raw SQL interface against the full dataset, with CSV export |

### Click to inspect

Click any organisation in the **Organisations table**, **Bar Chart**, or **Map** to open a detail panel below the tabs showing:

- Organisation name, country, funding total, and project count
- Address, website, and contact info
- Full list of projects the organisation has participated in

Click any project row to open the **project detail view**:

- Project title, acronym, status, framework, budget, and period
- Full objective text
- All partner organisations with their funding amounts

Click any partner organisation to navigate to their detail view. Use **Back to org** to return, or **Clear** to dismiss the panel.

### Filters

Use the sidebar to narrow results across all tabs:

| Filter | Description |
|--------|-------------|
| Keyword search | Searches project objectives, keywords, and scientific vocabulary |
| Organisation type | Private company, higher education, research org, public body |
| Country | ISO country code filter (multi-select) |
| SME only | Limit to small and medium enterprises |
| Project status | Active (SIGNED), closed, terminated |
| Framework programme | e.g. HORIZON, FP7 |
| Policy priority tags | AI, climate, biodiversity, clean air, digital agenda |
| Max results | Limit all views to top N organisations by project count (default 500) |

### Export

- **Organisations tab:** Export current filtered results as CSV
- **SQL Query tab:** Export query results as CSV

---

## Natural Language Queries

This tool includes a Claude Code skill. In Claude Code, type:

```
/cordis
```

Then describe what you want in plain English. Claude will generate SQL ready to paste into the **SQL Query** tab.

Examples:
- "Show me German biotech companies with active HORIZON projects"
- "Which Australian universities are coordinating climate projects?"
- "Top 10 SMEs by EC funding in the digital agenda"

---

## Organisation Type Codes

| Code | Meaning |
|------|---------|
| PRC | Private for-profit company |
| HES | Higher education institution |
| REC | Research organisation |
| PUB | Public body |
| OTH | Other |

---

## Data Source

CORDIS Horizon Europe dataset, updated monthly by the Publications Office of the EU. Covers all Horizon Europe projects 2021–2027. [Download here.](https://data.europa.eu/data/datasets/cordis-eu-research-projects-under-horizon-europe-2021-2027)
