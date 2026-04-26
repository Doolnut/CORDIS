# CORDIS Explorer — Claude Code Context

A Streamlit app for Queensland Trade & Investment analysts to explore the CORDIS Horizon Europe dataset and identify EU research organisations for partnership outreach.

## Stack

- **Frontend:** Streamlit 1.37+
- **Query engine:** DuckDB (in-memory, reads CSVs as views)
- **Charts:** Plotly Express (bar chart, scatter_geo map)
- **Network graph:** PyVis (vis.js under the hood)
- **Data:** CORDIS Horizon Europe CSVs (~200MB, semicolon-delimited)

## Project structure

```
app.py                    # Streamlit entry point
src/
  data/
    loader.py             # DuckDB connection, CSV views, validation
    queries.py            # All SQL query functions
  ui/
    filters.py            # Sidebar filter widgets + build_filters_dict
    tables.py             # Organisations results table (clickable rows)
    charts.py             # Bar chart (clickable bars)
    map_view.py           # World map (clickable points)
    network.py            # Co-participation network graph
    export.py             # df_to_csv_bytes helper
    detail.py             # Org detail + project detail drill-down panels
Data/                     # User's local CORDIS CSVs (not committed)
```

## Critical data quirks — read before touching queries

### 1. Column name normalisation

`read_csv_auto(..., normalize_names=true)` is used in the loader. This:
- Lowercases all column names (`activityType` → `activitytype`)
- Prefixes SQL reserved words with `_` — the three affected columns are:
  - `name` → `_name`
  - `role` → `_role`
  - `order` → `_order`

All queries reference `o._name`, `o._role` etc. The SELECT aliases them back to friendly names (`AS name`, `AS role`) so downstream Python code can use `df["name"]` normally.

### 2. Quoted string values

The CORDIS CSVs have field values wrapped in literal double-quote characters (e.g. `"101194172"` is stored as the string `'"101194172"'`). DuckDB does not strip these during parsing when `normalize_names=true` is active.

Consequences:
- **Numeric JOINs:** `euro_sci_voc.projectid` and `policy_priorities.projectid` are BIGINT; `organization.projectid` is VARCHAR with quotes. Join with `TRY_CAST(REPLACE(o.projectid, '"', '') AS BIGINT)`.
- **Display fields:** Use `TRIM('"' FROM field)` to strip outer quotes before showing to users (in `get_org_detail` and `get_project_detail`).
- **project.id vs organization.projectid:** Both are quoted VARCHAR — they compare correctly as-is. No stripping needed for this JOIN.
- **Geolocation:** Values look like `'"52.52,13.40"'` — strip quotes before splitting on `,` in `parse_geolocation`.
- **Filter dropdowns:** `get_filter_options` reads raw values including any quotes. This is intentional — the same raw values are used in WHERE clauses, so they match correctly.

### 3. Type reference

| Table | Column | Type | Notes |
|-------|--------|------|-------|
| organization | projectid | VARCHAR | Quoted numeric string |
| organization | organisationid | VARCHAR | Quoted numeric string |
| organization | _name | VARCHAR | Reserved word — underscore prefix |
| organization | _role | VARCHAR | Reserved word — underscore prefix |
| project | id | VARCHAR | Quoted numeric string |
| euro_sci_voc | projectid | BIGINT | Plain integer — needs CAST to join with org |
| policy_priorities | projectid | BIGINT | Plain integer — needs CAST to join with org |
| policy_priorities | ai, biodiversity, etc. | BIGINT | 0 or 1 flags |

## Session state keys

| Key | Type | Purpose |
|-----|------|---------|
| `conn` | DuckDBPyConnection | Shared database connection |
| `data_path` | str | Last loaded data folder path |
| `selected_org_id` | str or None | Raw `organisationid` value of selected org |
| `selected_project_id` | str or None | Raw `id` value of selected project |

## Click-to-inspect flow

Clicking an org in Tab 1 (table), Tab 2 (bar chart), or Tab 3 (map) sets `selected_org_id` in session state. A detail panel renders below all tabs showing org info and a project list. Clicking a project row sets `selected_project_id`, replacing the org panel with a project detail view (which includes a partner org table). Clicking a partner org navigates to that org.

The Network tab (Tab 4) does not support click-to-select — PyVis runs in an iframe with no Streamlit bridge.

## Filters dict shape

```python
{
    "search": str | None,
    "activity_types": list[str] | None,   # e.g. ["PRC", "HES"]
    "countries": list[str] | None,         # ISO 2-letter codes
    "sme_only": bool,
    "project_status": list[str] | None,    # e.g. ["SIGNED"]
    "frameworks": list[str] | None,        # e.g. ["HORIZON"]
    "policy_priorities": list[str] | None, # lowercase column names: "ai", "cleanair", etc.
    "top_n": int,                          # applied as LIMIT, default 500
}
```

All filters are applied in `query_organizations`. The `top_n` LIMIT is always applied (defaults to 500 if missing).

## Running the app

```bash
pip install -r requirements.txt
streamlit run app.py
# or double-click run.bat on Windows
```

App binds to `localhost` only. Telemetry is disabled. Both settings are in `.streamlit/config.toml`.
