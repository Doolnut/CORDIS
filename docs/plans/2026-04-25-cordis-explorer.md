# CORDIS Explorer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local desktop-like web app that lets Queensland Trade & Investment analysts query, visualise, and export CORDIS EU research project data to identify companies worth approaching.

**Architecture:** Python + Streamlit frontend, DuckDB as the query engine reading CSVs directly from a user-configured local folder. All computation is local; internet is only needed to call the Claude API if the user uses the natural-language skill. Visualisations use Plotly (charts and maps) and PyVis (network graph).

**Tech Stack:** Python 3.10+, Streamlit 1.35+, DuckDB 0.10+, Plotly, PyVis, pandas (minimal use)

---

## Data Schema Reference

All CSV files use semicolon (`;`) as delimiter with a header row. DuckDB reads them directly via views -- no import step required.

```
project(id, acronym, status, title, startDate, endDate, totalCost,
        ecMaxContribution, legalBasis, topics, frameworkProgramme,
        objective, keywords)

organization(projectID, organisationID, name, shortName, SME,
             activityType, city, country, geolocation,
             organizationURL, contactForm, role,
             ecContribution, netEcContribution, totalCost, active)
  -- activityType codes:
  --   PRC = private for-profit company
  --   HES = higher education institution
  --   REC = research organisation
  --   PUB = public body
  --   OTH = other
  -- role values: coordinator, participant, associatedPartner, thirdParty
  -- SME: 'true' / 'false'  (string, not boolean)
  -- geolocation: "lat,lon" string e.g. "32.7174209,-117.1627714"

euroSciVoc(projectID, euroSciVocPath, euroSciVocTitle)
  -- euroSciVocPath: "/natural sciences/computer and information sciences/..."

topics(projectID, topic, title)

legalBasis(projectID, legalBasis, title, uniqueProgrammePart)

policyPriorities(projectID, ai, biodiversity, cleanAir, climate, digitalAgenda)
  -- values are '0' or '1' strings

webLink(projectID, physUrl, type, source)
  -- type values include: projectDeliverable, projectWebsite, etc.
```

---

## Folder Structure

```
CORDIS/
├── app.py                        # Streamlit entry point
├── requirements.txt
├── run.bat                       # Windows double-click launcher
├── run.sh                        # Mac/Linux launcher
├── README.md
├── Data/                         # User's local CSV files (not committed)
│   ├── project.csv
│   ├── organization.csv
│   ├── euroSciVoc.csv
│   ├── topics.csv
│   ├── legalBasis.csv
│   ├── policyPriorities.csv
│   └── webLink.csv
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py             # DuckDB connection, CSV views, validation
│   │   └── queries.py            # Parameterised query functions
│   └── ui/
│       ├── __init__.py
│       ├── filters.py            # Sidebar filter widgets
│       ├── tables.py             # Results dataframe display
│       ├── charts.py             # Plotly bar charts
│       ├── map_view.py           # Plotly scatter-geo map
│       ├── network.py            # PyVis co-participation network
│       └── export.py             # CSV download button
├── .claude/
│   └── skills/
│       └── cordis.md             # Claude NL-to-SQL skill
└── docs/
    └── plans/
        └── 2026-04-25-cordis-explorer.md
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`, `src/data/__init__.py`, `src/ui/__init__.py`
- Create: `.gitignore`

**Step 1: Create requirements.txt**

```text
streamlit>=1.35.0
duckdb>=0.10.0
plotly>=5.20.0
pyvis>=0.3.2
pandas>=2.2.0
```

**Step 2: Create .gitignore**

```text
Data/
*.db
*.parquet
__pycache__/
.streamlit/secrets.toml
```

**Step 3: Create empty `__init__.py` files**

```bash
touch src/__init__.py src/data/__init__.py src/ui/__init__.py
```

**Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: All packages install without error.

**Step 5: Verify install**

```bash
python -c "import streamlit, duckdb, plotly, pyvis; print('OK')"
```

Expected: prints `OK`

**Step 6: Commit**

```bash
git add requirements.txt .gitignore src/
git commit -m "chore: project scaffolding"
```

---

## Task 2: DuckDB Data Loader

**Files:**
- Create: `src/data/loader.py`

**Step 1: Write the test**

Create `tests/data/test_loader.py`:

```python
import pytest
import duckdb
import os
import tempfile
import csv

DATA_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def make_fixture_csvs(path: str):
    """Create minimal valid CSV fixtures matching the real schema."""
    os.makedirs(path, exist_ok=True)

    project_rows = [
        ["id", "acronym", "status", "title", "startDate", "endDate",
         "totalCost", "ecMaxContribution", "legalBasis", "topics",
         "frameworkProgramme", "objective", "keywords"],
        ["101", "TEST1", "SIGNED", "Test Project One", "2023-01-01",
         "2026-01-01", "500000", "400000", "HORIZON.1.2", "AI",
         "HORIZON", "Test objective", "machine learning"],
        ["102", "TEST2", "CLOSED", "Test Project Two", "2022-01-01",
         "2024-01-01", "200000", "180000", "HORIZON.2.4", "BIO",
         "HORIZON", "Bio objective", "biotech"],
    ]
    org_rows = [
        ["projectID", "organisationID", "name", "shortName", "SME",
         "activityType", "city", "country", "geolocation",
         "organizationURL", "contactForm", "role",
         "ecContribution", "netEcContribution", "totalCost", "active"],
        ["101", "9001", "Acme Corp", "ACME", "false", "PRC",
         "Berlin", "DE", "52.52,13.40", "http://acme.com", "", "coordinator",
         "200000", "200000", "250000", "true"],
        ["101", "9002", "Uni Hamburg", "UHH", "false", "HES",
         "Hamburg", "DE", "53.55,9.99", "", "", "participant",
         "200000", "200000", "250000", "true"],
        ["102", "9001", "Acme Corp", "ACME", "false", "PRC",
         "Berlin", "DE", "52.52,13.40", "", "", "coordinator",
         "180000", "180000", "200000", "true"],
    ]

    def write_csv(filename, rows):
        with open(os.path.join(path, filename), "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerows(rows)

    write_csv("project.csv", project_rows)
    write_csv("organization.csv", org_rows)
    # Minimal stubs for other tables
    for name, headers in [
        ("euroSciVoc.csv", ["projectID", "euroSciVocPath", "euroSciVocTitle"]),
        ("topics.csv", ["projectID", "topic", "title"]),
        ("legalBasis.csv", ["projectID", "legalBasis", "title", "uniqueProgrammePart"]),
        ("policyPriorities.csv", ["projectID", "ai", "biodiversity", "cleanAir", "climate", "digitalAgenda"]),
        ("webLink.csv", ["projectID", "physUrl", "type", "source"]),
    ]:
        write_csv(name, [headers])


@pytest.fixture
def data_dir(tmp_path):
    make_fixture_csvs(str(tmp_path))
    return str(tmp_path)


def test_loader_creates_views(data_dir):
    from src.data.loader import create_connection
    conn = create_connection(data_dir)
    tables = conn.execute("SHOW TABLES").fetchall()
    names = {t[0] for t in tables}
    assert "project" in names
    assert "organization" in names


def test_loader_rejects_missing_data_dir():
    from src.data.loader import create_connection, DataDirectoryError
    with pytest.raises(DataDirectoryError):
        create_connection("/nonexistent/path")


def test_loader_rejects_missing_required_file(tmp_path):
    from src.data.loader import create_connection, DataDirectoryError
    # Only create project.csv, not organization.csv
    with open(str(tmp_path / "project.csv"), "w") as f:
        f.write("id;title\n")
    with pytest.raises(DataDirectoryError):
        create_connection(str(tmp_path))


def test_project_count(data_dir):
    from src.data.loader import create_connection
    conn = create_connection(data_dir)
    count = conn.execute("SELECT COUNT(*) FROM project").fetchone()[0]
    assert count == 2


def test_organization_count(data_dir):
    from src.data.loader import create_connection
    conn = create_connection(data_dir)
    count = conn.execute("SELECT COUNT(*) FROM organization").fetchone()[0]
    assert count == 3
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/data/test_loader.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.data.loader'`

**Step 3: Implement loader.py**

```python
import duckdb
import os
from pathlib import Path

REQUIRED_FILES = [
    "project.csv",
    "organization.csv",
    "euroSciVoc.csv",
    "topics.csv",
    "legalBasis.csv",
    "policyPriorities.csv",
    "webLink.csv",
]


class DataDirectoryError(Exception):
    pass


def create_connection(data_dir: str) -> duckdb.DuckDBPyConnection:
    path = Path(data_dir)
    if not path.exists() or not path.is_dir():
        raise DataDirectoryError(f"Data directory not found: {data_dir}")

    missing = [f for f in REQUIRED_FILES if not (path / f).exists()]
    if missing:
        raise DataDirectoryError(f"Missing required files: {', '.join(missing)}")

    conn = duckdb.connect(database=":memory:")
    _create_views(conn, path)
    return conn


def _create_views(conn: duckdb.DuckDBPyConnection, data_path: Path) -> None:
    views = {
        "project": "project.csv",
        "organization": "organization.csv",
        "euro_sci_voc": "euroSciVoc.csv",
        "topics": "topics.csv",
        "legal_basis": "legalBasis.csv",
        "policy_priorities": "policyPriorities.csv",
        "web_link": "webLink.csv",
    }
    for view_name, filename in views.items():
        file_path = str(data_path / filename).replace("\\", "/")
        conn.execute(
            f"CREATE VIEW {view_name} AS "
            f"SELECT * FROM read_csv_auto('{file_path}', delim=';', header=true, ignore_errors=true)"
        )
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/data/test_loader.py -v
```

Expected: All 5 tests PASS.

**Step 5: Commit**

```bash
git add src/data/loader.py tests/
git commit -m "feat: DuckDB CSV loader with view creation and validation"
```

---

## Task 3: Query Functions

**Files:**
- Create: `src/data/queries.py`

**Step 1: Write tests**

Create `tests/data/test_queries.py`:

```python
import pytest
from tests.data.test_loader import data_dir  # reuse fixture


def test_get_filter_options_countries(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import get_filter_options
    conn = create_connection(data_dir)
    opts = get_filter_options(conn)
    assert "DE" in opts["countries"]


def test_get_filter_options_activity_types(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import get_filter_options
    conn = create_connection(data_dir)
    opts = get_filter_options(conn)
    assert "PRC" in opts["activity_types"]
    assert "HES" in opts["activity_types"]


def test_query_organizations_no_filters(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import query_organizations
    conn = create_connection(data_dir)
    df = query_organizations(conn, filters={})
    assert len(df) == 2  # 2 unique orgs (Acme appears twice but deduplicated)


def test_query_organizations_filter_by_activity_type(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import query_organizations
    conn = create_connection(data_dir)
    df = query_organizations(conn, filters={"activity_types": ["PRC"]})
    assert all(df["activityType"] == "PRC")
    assert len(df) == 1


def test_query_organizations_filter_by_country(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import query_organizations
    conn = create_connection(data_dir)
    df = query_organizations(conn, filters={"countries": ["DE"]})
    assert len(df) >= 1


def test_query_organizations_search_term(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import query_organizations
    conn = create_connection(data_dir)
    df = query_organizations(conn, filters={"search": "machine"})
    assert len(df) >= 1


def test_top_companies_by_project_count(data_dir):
    from src.data.loader import create_connection
    from src.data.queries import top_companies_by_project_count
    conn = create_connection(data_dir)
    df = top_companies_by_project_count(conn, filters={}, limit=10)
    assert "name" in df.columns
    assert "project_count" in df.columns
    # Acme Corp appears in 2 projects
    acme = df[df["name"] == "Acme Corp"]
    assert acme.iloc[0]["project_count"] == 2
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/data/test_queries.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Implement queries.py**

```python
import duckdb
import pandas as pd
from typing import Any


def get_filter_options(conn: duckdb.DuckDBPyConnection) -> dict[str, list]:
    countries = conn.execute(
        "SELECT DISTINCT country FROM organization WHERE country IS NOT NULL ORDER BY country"
    ).df()["country"].tolist()

    activity_types = conn.execute(
        "SELECT DISTINCT activityType FROM organization WHERE activityType IS NOT NULL ORDER BY activityType"
    ).df()["activityType"].tolist()

    frameworks = conn.execute(
        "SELECT DISTINCT frameworkProgramme FROM project WHERE frameworkProgramme IS NOT NULL ORDER BY frameworkProgramme"
    ).df()["frameworkProgramme"].tolist()

    statuses = conn.execute(
        "SELECT DISTINCT status FROM project WHERE status IS NOT NULL ORDER BY status"
    ).df()["status"].tolist()

    policy_cols = ["ai", "biodiversity", "cleanAir", "climate", "digitalAgenda"]

    return {
        "countries": countries,
        "activity_types": activity_types,
        "frameworks": frameworks,
        "statuses": statuses,
        "policy_priorities": policy_cols,
    }


def query_organizations(
    conn: duckdb.DuckDBPyConnection, filters: dict[str, Any]
) -> pd.DataFrame:
    where_clauses = ["1=1"]
    params = []

    if filters.get("activity_types"):
        placeholders = ", ".join(["?" for _ in filters["activity_types"]])
        where_clauses.append(f"o.activityType IN ({placeholders})")
        params.extend(filters["activity_types"])

    if filters.get("countries"):
        placeholders = ", ".join(["?" for _ in filters["countries"]])
        where_clauses.append(f"o.country IN ({placeholders})")
        params.extend(filters["countries"])

    if filters.get("sme_only"):
        where_clauses.append("o.SME = 'true'")

    if filters.get("project_status"):
        placeholders = ", ".join(["?" for _ in filters["project_status"]])
        where_clauses.append(f"p.status IN ({placeholders})")
        params.extend(filters["project_status"])

    if filters.get("frameworks"):
        placeholders = ", ".join(["?" for _ in filters["frameworks"]])
        where_clauses.append(f"p.frameworkProgramme IN ({placeholders})")
        params.extend(filters["frameworks"])

    if filters.get("search"):
        term = f"%{filters['search']}%"
        where_clauses.append(
            "(p.keywords ILIKE ? OR p.objective ILIKE ? "
            "OR esv.euroSciVocTitle ILIKE ? OR o.name ILIKE ?)"
        )
        params.extend([term, term, term, term])

    if filters.get("policy_priorities"):
        for col in filters["policy_priorities"]:
            where_clauses.append(f"TRY_CAST(pp.{col} AS INTEGER) = 1")

    where_sql = " AND ".join(where_clauses)

    sql = f"""
        SELECT
            o.organisationID,
            o.name,
            o.shortName,
            o.activityType,
            o.SME,
            o.city,
            o.country,
            o.organizationURL,
            o.contactForm,
            o.geolocation,
            COUNT(DISTINCT o.projectID) AS project_count,
            SUM(TRY_CAST(o.ecContribution AS DOUBLE)) AS total_ec_contribution
        FROM organization o
        JOIN project p ON p.id = o.projectID
        LEFT JOIN euro_sci_voc esv ON esv.projectID = o.projectID
        LEFT JOIN policy_priorities pp ON pp.projectID = o.projectID
        WHERE {where_sql}
        GROUP BY
            o.organisationID, o.name, o.shortName, o.activityType,
            o.SME, o.city, o.country, o.organizationURL, o.contactForm, o.geolocation
        ORDER BY project_count DESC
    """
    return conn.execute(sql, params).df()


def top_companies_by_project_count(
    conn: duckdb.DuckDBPyConnection,
    filters: dict[str, Any],
    limit: int = 25,
) -> pd.DataFrame:
    df = query_organizations(conn, filters)
    return df.nlargest(limit, "project_count")[["name", "country", "activityType", "project_count", "total_ec_contribution"]]


def run_raw_sql(
    conn: duckdb.DuckDBPyConnection, sql: str
) -> pd.DataFrame:
    return conn.execute(sql).df()
```

**Step 4: Run tests**

```bash
pytest tests/data/test_queries.py -v
```

Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/data/queries.py tests/data/test_queries.py
git commit -m "feat: parameterised query functions with filter support"
```

---

## Task 4: Streamlit App Skeleton and Data Setup

**Files:**
- Create: `app.py`
- Create: `.streamlit/config.toml`

**Step 1: Write the skeleton app**

```python
# app.py
import streamlit as st
import os
from src.data.loader import create_connection, DataDirectoryError

st.set_page_config(
    page_title="CORDIS Explorer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("CORDIS Explorer")
st.caption("Queensland Trade & Investment — EU Research Partnership Finder")

# --- Data folder configuration ---
with st.sidebar:
    st.header("Data Configuration")
    default_data_path = os.path.join(os.path.dirname(__file__), "Data")
    data_path = st.text_input(
        "Path to CORDIS data folder",
        value=st.session_state.get("data_path", default_data_path),
        help="Folder containing project.csv, organization.csv, etc.",
    )
    load_btn = st.button("Load Data", type="primary")

if load_btn or "conn" not in st.session_state:
    if data_path:
        try:
            with st.spinner("Loading CORDIS data..."):
                st.session_state["conn"] = create_connection(data_path)
                st.session_state["data_path"] = data_path
            st.sidebar.success("Data loaded.")
        except DataDirectoryError as e:
            st.sidebar.error(str(e))
            st.stop()

if "conn" not in st.session_state:
    st.info("Configure the data folder path in the sidebar and click **Load Data**.")
    st.stop()

conn = st.session_state["conn"]
st.sidebar.divider()
```

**Step 2: Create `.streamlit/config.toml`**

```toml
[theme]
base = "light"

[server]
headless = true
port = 8501
```

**Step 3: Run the app to verify it loads**

```bash
streamlit run app.py
```

Open browser to `http://localhost:8501`. Expected: app loads with sidebar, no errors.

**Step 4: Commit**

```bash
git add app.py .streamlit/
git commit -m "feat: Streamlit app skeleton with data folder configuration"
```

---

## Task 5: Filter Sidebar

**Files:**
- Create: `src/ui/filters.py`

**Step 1: Write the test**

Create `tests/ui/test_filters.py`:

```python
def test_build_filters_returns_dict():
    # Filters is a pure dict-building function; test the dict structure
    from src.ui.filters import build_filters_dict
    result = build_filters_dict(
        search="quantum",
        activity_types=["PRC"],
        countries=["DE", "FR"],
        sme_only=True,
        project_status=["SIGNED"],
        frameworks=["HORIZON"],
        policy_priorities=["ai"],
    )
    assert result["search"] == "quantum"
    assert result["activity_types"] == ["PRC"]
    assert result["sme_only"] is True
    assert "ai" in result["policy_priorities"]
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/ui/test_filters.py -v
```

**Step 3: Implement filters.py**

```python
# src/ui/filters.py
import streamlit as st
import duckdb
from src.data.queries import get_filter_options

ACTIVITY_TYPE_LABELS = {
    "PRC": "Private company (PRC)",
    "HES": "Higher education (HES)",
    "REC": "Research organisation (REC)",
    "PUB": "Public body (PUB)",
    "OTH": "Other (OTH)",
}


def build_filters_dict(
    search, activity_types, countries, sme_only,
    project_status, frameworks, policy_priorities
) -> dict:
    return {
        "search": search or None,
        "activity_types": activity_types or None,
        "countries": countries or None,
        "sme_only": sme_only,
        "project_status": project_status or None,
        "frameworks": frameworks or None,
        "policy_priorities": policy_priorities or None,
    }


def render_filters(conn: duckdb.DuckDBPyConnection) -> dict:
    opts = get_filter_options(conn)

    st.subheader("Search & Filter")

    search = st.text_input(
        "Research area / keyword",
        placeholder="e.g. quantum computing, clean hydrogen, biotech",
        help="Searches project keywords, objectives, and scientific vocabulary",
    )

    activity_types = st.multiselect(
        "Organisation type",
        options=list(ACTIVITY_TYPE_LABELS.keys()),
        format_func=lambda x: ACTIVITY_TYPE_LABELS.get(x, x),
        default=[],
    )

    countries = st.multiselect(
        "Country",
        options=opts["countries"],
        default=[],
    )

    sme_only = st.checkbox("SME only (small/medium enterprises)")

    project_status = st.multiselect(
        "Project status",
        options=opts["statuses"],
        default=[],
    )

    frameworks = st.multiselect(
        "Framework programme",
        options=opts["frameworks"],
        default=[],
    )

    policy_priorities = st.multiselect(
        "Policy priority tags",
        options=opts["policy_priorities"],
        default=[],
    )

    return build_filters_dict(
        search, activity_types, countries, sme_only,
        project_status, frameworks, policy_priorities,
    )
```

**Step 4: Run test**

```bash
pytest tests/ui/test_filters.py -v
```

Expected: PASS.

**Step 5: Wire filters into app.py**

Add to the end of `app.py`:

```python
from src.ui.filters import render_filters

with st.sidebar:
    filters = render_filters(conn)
```

**Step 6: Run app to verify sidebar renders correctly, commit**

```bash
streamlit run app.py
```

```bash
git add src/ui/filters.py tests/ui/ app.py
git commit -m "feat: filter sidebar with search, org type, country, SME, status"
```

---

## Task 6: Results Table

**Files:**
- Create: `src/ui/tables.py`

**Step 1: Write test**

Create `tests/ui/test_tables.py`:

```python
import pandas as pd


def test_format_org_table_renames_columns():
    from src.ui.tables import format_org_table
    df = pd.DataFrame({
        "name": ["Acme"], "activityType": ["PRC"], "city": ["Berlin"],
        "country": ["DE"], "project_count": [5],
        "total_ec_contribution": [500000.0], "organizationURL": ["http://a.com"],
        "contactForm": [""], "SME": ["false"],
    })
    result = format_org_table(df)
    assert "Organisation" in result.columns
    assert "Projects" in result.columns
    assert "EC Contribution (EUR)" in result.columns
```

**Step 2: Run test to verify it fails**

**Step 3: Implement tables.py**

```python
# src/ui/tables.py
import streamlit as st
import pandas as pd
import duckdb
from src.data.queries import query_organizations

COLUMN_RENAME = {
    "name": "Organisation",
    "shortName": "Short Name",
    "activityType": "Type",
    "SME": "SME",
    "city": "City",
    "country": "Country",
    "project_count": "Projects",
    "total_ec_contribution": "EC Contribution (EUR)",
    "organizationURL": "Website",
    "contactForm": "Contact",
}


def format_org_table(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["total_ec_contribution"] = df["total_ec_contribution"].apply(
        lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else ""
    )
    return df.rename(columns=COLUMN_RENAME)


def render_results_table(conn: duckdb.DuckDBPyConnection, filters: dict) -> pd.DataFrame:
    with st.spinner("Querying..."):
        df = query_organizations(conn, filters)

    st.subheader(f"Results: {len(df):,} organisations")

    if df.empty:
        st.info("No organisations match the current filters.")
        return df

    display_cols = [
        "name", "activityType", "SME", "city", "country",
        "project_count", "total_ec_contribution", "organizationURL",
    ]
    available = [c for c in display_cols if c in df.columns]
    formatted = format_org_table(df[available])

    st.dataframe(
        formatted,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Website": st.column_config.LinkColumn("Website"),
            "Contact": st.column_config.LinkColumn("Contact"),
        },
    )
    return df
```

**Step 4: Run test, wire into app.py, verify visually, commit**

Add to `app.py`:

```python
from src.ui.tables import render_results_table

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Organisations", "Bar Chart", "Map", "Network", "SQL Query"]
)

with tab1:
    results_df = render_results_table(conn, filters)
```

```bash
pytest tests/ui/test_tables.py -v
streamlit run app.py
git add src/ui/tables.py tests/ui/test_tables.py app.py
git commit -m "feat: organisations results table with formatted display"
```

---

## Task 7: Bar Chart Visualisation

**Files:**
- Create: `src/ui/charts.py`

**Step 1: Write test**

```python
# tests/ui/test_charts.py
import pandas as pd


def test_build_bar_chart_returns_figure():
    from src.ui.charts import build_top_companies_chart
    df = pd.DataFrame({
        "name": ["A", "B", "C"],
        "project_count": [10, 7, 4],
        "total_ec_contribution": [1000000, 700000, 400000],
        "country": ["DE", "FR", "IT"],
    })
    fig = build_top_companies_chart(df, metric="project_count")
    assert fig is not None
    assert hasattr(fig, "data")
```

**Step 2: Run test to verify it fails**

**Step 3: Implement charts.py**

```python
# src/ui/charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import duckdb
from src.data.queries import top_companies_by_project_count

METRIC_LABELS = {
    "project_count": "Number of Projects",
    "total_ec_contribution": "Total EC Contribution (EUR)",
}


def build_top_companies_chart(df: pd.DataFrame, metric: str):
    df = df.dropna(subset=[metric]).nlargest(25, metric)
    fig = px.bar(
        df,
        x=metric,
        y="name",
        orientation="h",
        color="country",
        title=f"Top 25 Organisations by {METRIC_LABELS[metric]}",
        labels={"name": "Organisation", metric: METRIC_LABELS[metric]},
        height=700,
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


def render_bar_chart(conn: duckdb.DuckDBPyConnection, filters: dict) -> None:
    metric = st.radio(
        "Rank by",
        options=["project_count", "total_ec_contribution"],
        format_func=lambda x: METRIC_LABELS[x],
        horizontal=True,
    )
    with st.spinner("Building chart..."):
        df = top_companies_by_project_count(conn, filters, limit=25)

    if df.empty:
        st.info("No data for current filters.")
        return

    fig = build_top_companies_chart(df, metric)
    st.plotly_chart(fig, use_container_width=True)
```

**Step 4: Wire into app.py tab2, run tests, verify chart renders, commit**

```python
# in app.py
from src.ui.charts import render_bar_chart

with tab2:
    render_bar_chart(conn, filters)
```

```bash
pytest tests/ui/test_charts.py -v
streamlit run app.py
git add src/ui/charts.py tests/ui/test_charts.py app.py
git commit -m "feat: bar chart of top organisations by project count or EC contribution"
```

---

## Task 8: World Map Visualisation

**Files:**
- Create: `src/ui/map_view.py`

The `geolocation` column contains `"lat,lon"` strings. We parse these into separate float columns before plotting.

**Step 1: Write test**

```python
# tests/ui/test_map_view.py
import pandas as pd


def test_parse_geolocation():
    from src.ui.map_view import parse_geolocation
    df = pd.DataFrame({
        "name": ["Acme", "No Geo"],
        "geolocation": ["52.52,13.40", None],
        "project_count": [5, 3],
        "country": ["DE", "FR"],
    })
    result = parse_geolocation(df)
    assert result.iloc[0]["lat"] == pytest.approx(52.52)
    assert result.iloc[0]["lon"] == pytest.approx(13.40)
    assert pd.isna(result.iloc[1]["lat"])


def test_build_map_returns_figure():
    import pytest
    from src.ui.map_view import parse_geolocation, build_map
    df = pd.DataFrame({
        "name": ["Acme"],
        "geolocation": ["52.52,13.40"],
        "project_count": [5],
        "country": ["DE"],
        "activityType": ["PRC"],
    })
    df = parse_geolocation(df)
    fig = build_map(df)
    assert fig is not None
```

**Step 2: Run test to verify it fails**

**Step 3: Implement map_view.py**

```python
# src/ui/map_view.py
import streamlit as st
import pandas as pd
import plotly.express as px
import duckdb
from src.data.queries import query_organizations


def parse_geolocation(df: pd.DataFrame) -> pd.DataFrame:
    def split_geo(val):
        if pd.isna(val) or not str(val).strip():
            return pd.NA, pd.NA
        parts = str(val).split(",")
        if len(parts) != 2:
            return pd.NA, pd.NA
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            return pd.NA, pd.NA

    df = df.copy()
    coords = df["geolocation"].apply(split_geo)
    df["lat"] = coords.apply(lambda x: x[0])
    df["lon"] = coords.apply(lambda x: x[1])
    return df


def build_map(df: pd.DataFrame):
    df = df.dropna(subset=["lat", "lon"])
    fig = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        color="country",
        size="project_count",
        hover_name="name",
        hover_data={"country": True, "project_count": True, "lat": False, "lon": False},
        title="Organisation Locations",
        projection="natural earth",
    )
    fig.update_layout(height=600)
    return fig


def render_map(conn: duckdb.DuckDBPyConnection, filters: dict) -> None:
    with st.spinner("Building map..."):
        df = query_organizations(conn, filters)

    if df.empty:
        st.info("No data for current filters.")
        return

    df = parse_geolocation(df)
    valid = df.dropna(subset=["lat", "lon"])
    st.caption(f"Showing {len(valid):,} of {len(df):,} organisations with geolocation data.")
    fig = build_map(df)
    st.plotly_chart(fig, use_container_width=True)
```

**Step 4: Wire into app.py tab3, run tests, verify map renders, commit**

```python
from src.ui.map_view import render_map

with tab3:
    render_map(conn, filters)
```

```bash
pytest tests/ui/test_map_view.py -v
streamlit run app.py
git add src/ui/map_view.py tests/ui/test_map_view.py app.py
git commit -m "feat: world map of organisation locations sized by project count"
```

---

## Task 9: Network Graph

**Files:**
- Create: `src/ui/network.py`

This graph shows companies as nodes sized by their project count. Edges connect two companies that appear in the same project. To keep it readable, limit to the top 50 companies by project count before computing edges.

**Step 1: Write test**

```python
# tests/ui/test_network.py
import pandas as pd


def test_build_edges_finds_shared_projects(data_dir):
    from src.data.loader import create_connection
    from src.ui.network import build_co_participation_edges
    conn = create_connection(data_dir)
    # Acme (9001) and Uni Hamburg (9002) both appear in project 101
    edges = build_co_participation_edges(conn, top_n=50)
    assert len(edges) >= 1
    names = set(edges["org_a"].tolist() + edges["org_b"].tolist())
    assert "Acme Corp" in names
```

**Step 2: Run test to verify it fails**

**Step 3: Implement network.py**

```python
# src/ui/network.py
import streamlit as st
import pandas as pd
import duckdb
from pyvis.network import Network
import streamlit.components.v1 as components


def build_co_participation_edges(
    conn: duckdb.DuckDBPyConnection, top_n: int = 50, filters: dict | None = None
) -> pd.DataFrame:
    # Get top N organisations by project count
    top_orgs = conn.execute(f"""
        SELECT name, COUNT(DISTINCT projectID) AS project_count
        FROM organization
        GROUP BY name
        ORDER BY project_count DESC
        LIMIT {top_n}
    """).df()

    if top_orgs.empty:
        return pd.DataFrame(columns=["org_a", "org_b", "shared_projects"])

    # Find pairs that share projects
    edges = conn.execute(f"""
        WITH top AS (
            SELECT name FROM organization
            GROUP BY name
            ORDER BY COUNT(DISTINCT projectID) DESC
            LIMIT {top_n}
        )
        SELECT
            a.name AS org_a,
            b.name AS org_b,
            COUNT(DISTINCT a.projectID) AS shared_projects
        FROM organization a
        JOIN organization b ON a.projectID = b.projectID AND a.name < b.name
        WHERE a.name IN (SELECT name FROM top)
          AND b.name IN (SELECT name FROM top)
        GROUP BY a.name, b.name
        HAVING shared_projects >= 2
        ORDER BY shared_projects DESC
    """).df()

    return edges


def build_network_html(
    conn: duckdb.DuckDBPyConnection, top_n: int = 50
) -> str:
    node_data = conn.execute(f"""
        SELECT name, COUNT(DISTINCT projectID) AS project_count, country
        FROM organization
        GROUP BY name, country
        ORDER BY project_count DESC
        LIMIT {top_n}
    """).df()

    edges = build_co_participation_edges(conn, top_n=top_n)

    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
    net.barnes_hut()

    for _, row in node_data.iterrows():
        net.add_node(
            row["name"],
            label=row["name"],
            title=f"{row['name']} ({row['country']}): {row['project_count']} projects",
            size=max(5, min(50, row["project_count"] * 2)),
        )

    for _, row in edges.iterrows():
        net.add_edge(row["org_a"], row["org_b"], value=row["shared_projects"])

    net.set_options("""
    {
      "physics": {"enabled": true, "solver": "barnesHut"},
      "interaction": {"hover": true, "tooltipDelay": 100}
    }
    """)
    return net.generate_html()


def render_network(conn: duckdb.DuckDBPyConnection, filters: dict) -> None:
    top_n = st.slider("Number of top organisations to include", 10, 100, 50, step=10)

    with st.spinner("Building network graph..."):
        html = build_network_html(conn, top_n=top_n)

    st.caption(
        f"Nodes: top {top_n} organisations by project count. "
        "Edges: two organisations co-appear in the same project (min 2 shared projects)."
    )
    components.html(html, height=620, scrolling=False)
```

**Step 4: Wire into app.py tab4, run tests, verify graph renders, commit**

```python
from src.ui.network import render_network

with tab4:
    render_network(conn, filters)
```

```bash
pytest tests/ui/test_network.py -v
streamlit run app.py
git add src/ui/network.py tests/ui/test_network.py app.py
git commit -m "feat: co-participation network graph of top organisations"
```

---

## Task 10: SQL Query Box and CSV Export

**Files:**
- Create: `src/ui/export.py`
- Modify: `app.py`

**Step 1: Write test**

```python
# tests/ui/test_export.py
import pandas as pd


def test_df_to_csv_bytes():
    from src.ui.export import df_to_csv_bytes
    df = pd.DataFrame({"name": ["Acme"], "country": ["DE"]})
    result = df_to_csv_bytes(df)
    assert isinstance(result, bytes)
    assert b"Acme" in result
```

**Step 2: Run test to verify it fails**

**Step 3: Implement export.py**

```python
# src/ui/export.py
import pandas as pd


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
```

**Step 4: Add SQL tab and export buttons to app.py**

```python
from src.data.queries import run_raw_sql
from src.ui.export import df_to_csv_bytes
import pandas as pd

# In the SQL tab (tab5):
with tab5:
    st.subheader("Raw SQL Query")
    st.caption("Tables: project, organization, euro_sci_voc, topics, legal_basis, policy_priorities, web_link")
    sql_input = st.text_area(
        "SQL",
        value="SELECT name, country, COUNT(DISTINCT projectID) AS projects\nFROM organization\nWHERE activityType = 'PRC'\nGROUP BY name, country\nORDER BY projects DESC\nLIMIT 25",
        height=200,
    )
    if st.button("Run Query"):
        try:
            result_df = run_raw_sql(conn, sql_input)
            st.dataframe(result_df, use_container_width=True, hide_index=True)
            st.download_button(
                "Export query results as CSV",
                data=df_to_csv_bytes(result_df),
                file_name="cordis_query_results.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"Query error: {e}")

# Export button on Organisations tab — add after render_results_table in tab1:
with tab1:
    results_df = render_results_table(conn, filters)
    if not results_df.empty:
        st.download_button(
            "Export results as CSV",
            data=df_to_csv_bytes(results_df),
            file_name="cordis_organisations.csv",
            mime="text/csv",
        )
```

**Step 5: Run tests, verify export works in browser, commit**

```bash
pytest tests/ui/test_export.py -v
streamlit run app.py
git add src/ui/export.py tests/ui/test_export.py app.py
git commit -m "feat: SQL query box and CSV export for organisation results"
```

---

## Task 11: Claude NL-to-SQL Skill

**Files:**
- Create: `.claude/skills/cordis.md`

**Step 1: Write the skill file**

```markdown
---
name: cordis
description: Convert natural language questions into DuckDB SQL queries against the CORDIS EU research database
type: skill
---

# CORDIS Query Skill

You convert natural language questions from Queensland Trade & Investment analysts into
DuckDB SQL queries against the local CORDIS database.

## Database Schema

### project
One row per EU research project.

| Column | Type | Notes |
|--------|------|-------|
| id | VARCHAR | Primary key, matches organization.projectID |
| acronym | VARCHAR | Short project name |
| status | VARCHAR | SIGNED, CLOSED, TERMINATED |
| title | VARCHAR | Full project title |
| startDate | DATE | e.g. 2023-01-01 |
| endDate | DATE | |
| totalCost | DOUBLE | Total project cost in EUR |
| ecMaxContribution | DOUBLE | EU funding amount in EUR |
| frameworkProgramme | VARCHAR | e.g. HORIZON, FP7 |
| objective | VARCHAR | Full project description |
| keywords | VARCHAR | Comma-separated keywords |

### organization
One row per organisation per project (many per project).

| Column | Type | Notes |
|--------|------|-------|
| projectID | VARCHAR | Foreign key to project.id |
| organisationID | VARCHAR | Org identifier |
| name | VARCHAR | Full organisation name |
| shortName | VARCHAR | Abbreviation |
| SME | VARCHAR | 'true' or 'false' |
| activityType | VARCHAR | PRC=private company, HES=higher education, REC=research org, PUB=public body, OTH=other |
| city | VARCHAR | |
| country | VARCHAR | ISO 2-letter code, e.g. 'DE', 'AU', 'US' |
| geolocation | VARCHAR | "lat,lon" string |
| organizationURL | VARCHAR | Website |
| contactForm | VARCHAR | EU contact form URL |
| role | VARCHAR | coordinator, participant, associatedPartner, thirdParty |
| ecContribution | DOUBLE | EU funding received by this org on this project |
| SME | VARCHAR | 'true' or 'false' |
| active | VARCHAR | 'true' or 'false' |

### euro_sci_voc
Scientific vocabulary classification. Many rows per project.

| Column | Notes |
|--------|-------|
| projectID | |
| euroSciVocPath | Hierarchical path e.g. "/natural sciences/computer and information sciences/artificial intelligence/machine learning" |
| euroSciVocTitle | Leaf term e.g. "machine learning" |

### topics
EU funding call topics. Many rows per project.

| Column | Notes |
|--------|-------|
| projectID | |
| topic | Topic code e.g. "HORIZON-MSCA-2022-SE-01-01" |
| title | Human-readable title |

### policy_priorities
One row per project. Values are '0' or '1' strings.

Columns: projectID, ai, biodiversity, cleanAir, climate, digitalAgenda

### web_link
Project deliverables and websites.

| Column | Notes |
|--------|-------|
| projectID | |
| physUrl | URL |
| type | projectDeliverable, projectWebsite, etc. |

## How to Answer

1. Understand the question in terms of the schema above.
2. Write a DuckDB SQL query. DuckDB supports standard SQL plus:
   - `ILIKE` for case-insensitive LIKE
   - `TRY_CAST(x AS DOUBLE)` for safe numeric casting
   - `read_csv_auto()` is not needed — tables are pre-loaded
3. Return the SQL in a code block, ready to paste into the SQL Query tab.
4. Briefly explain what the query returns and any caveats.

## Example Translations

**"Show me all German private companies working on hydrogen projects"**
```sql
SELECT DISTINCT
    o.name, o.city, o.country, o.organizationURL,
    COUNT(DISTINCT o.projectID) AS project_count
FROM organization o
JOIN project p ON p.id = o.projectID
WHERE o.activityType = 'PRC'
  AND o.country = 'DE'
  AND (p.keywords ILIKE '%hydrogen%' OR p.objective ILIKE '%hydrogen%')
GROUP BY o.name, o.city, o.country, o.organizationURL
ORDER BY project_count DESC;
```

**"Which SME companies have the most active HORIZON projects?"**
```sql
SELECT
    o.name, o.country,
    COUNT(DISTINCT o.projectID) AS project_count,
    SUM(TRY_CAST(o.ecContribution AS DOUBLE)) AS total_funding
FROM organization o
JOIN project p ON p.id = o.projectID
WHERE o.SME = 'true'
  AND p.status = 'SIGNED'
  AND p.frameworkProgramme = 'HORIZON'
GROUP BY o.name, o.country
ORDER BY project_count DESC
LIMIT 25;
```

**"Show me companies working on AI from outside the EU"**
```sql
SELECT DISTINCT
    o.name, o.country, o.city, o.organizationURL,
    COUNT(DISTINCT o.projectID) AS project_count
FROM organization o
JOIN policy_priorities pp ON pp.projectID = o.projectID
WHERE o.activityType = 'PRC'
  AND TRY_CAST(pp.ai AS INTEGER) = 1
  AND o.country NOT IN (
    'AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR',
    'DE','GR','HU','IE','IT','LV','LT','LU','MT','NL',
    'PL','PT','RO','SK','SI','ES','SE'
  )
GROUP BY o.name, o.country, o.city, o.organizationURL
ORDER BY project_count DESC;
```
```

**Step 2: Verify the skill file is valid and commit**

```bash
cat .claude/skills/cordis.md
git add .claude/skills/cordis.md
git commit -m "feat: Claude NL-to-SQL skill for CORDIS queries"
```

---

## Task 12: Launchers and README

**Files:**
- Create: `run.bat`
- Create: `run.sh`
- Create: `README.md`

**Step 1: Create run.bat**

```bat
@echo off
echo Starting CORDIS Explorer...
python -m streamlit run app.py
pause
```

**Step 2: Create run.sh**

```bash
#!/bin/bash
python3 -m streamlit run app.py
```

```bash
chmod +x run.sh
```

**Step 3: Create README.md**

````markdown
# CORDIS Explorer

A local tool for Queensland Trade & Investment to discover EU research organisations
from the CORDIS database.

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

1. Download the CORDIS data export from the EU Open Data Portal.
2. Place all CSV files in a folder on your PC.
3. In the app sidebar, enter the path to that folder and click **Load Data**.

Required files: `project.csv`, `organization.csv`, `euroSciVoc.csv`,
`topics.csv`, `legalBasis.csv`, `policyPriorities.csv`, `webLink.csv`

## Natural Language Queries

This tool includes a Claude Code skill. In Claude Code, type:

```
/cordis
```

Then describe what you want in plain English. Claude will generate SQL you can
paste into the **SQL Query** tab.

Example: "Show me German biotech companies with active HORIZON projects"

## Organisation Type Codes

| Code | Meaning |
|------|---------|
| PRC | Private for-profit company |
| HES | Higher education institution |
| REC | Research organisation |
| PUB | Public body |
| OTH | Other |
````

**Step 4: Commit**

```bash
git add run.bat run.sh README.md
git commit -m "docs: launchers and README with setup instructions"
```

---

## Final Checklist

Before marking complete:

- [ ] `pytest` passes with no failures
- [ ] App loads real CORDIS data from the `Data/` folder
- [ ] Filters produce correct results (test with "hydrogen" keyword + PRC type)
- [ ] Bar chart shows top 25 companies ranked correctly
- [ ] Map renders pins on correct locations for a known company (e.g. a German firm)
- [ ] Network graph loads without crashing on the full dataset
- [ ] SQL tab executes a query and exports CSV correctly
- [ ] `/cordis` skill generates valid SQL when tested in Claude
- [ ] `run.bat` launches the app from a fresh terminal with no extra steps
