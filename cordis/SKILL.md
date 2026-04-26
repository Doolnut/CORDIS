---
name: cordis
description: Query the CORDIS Horizon Europe 2021-2027 dataset to analyse EU research organisations, projects, and funding. Use this skill whenever the user wants to find, rank, filter, or compare EU research organisations or projects — including questions like "top organisations by funding", "which countries lead in a topic", "find projects involving Australian partners", "how much has X organisation received", or any analysis of Horizon Europe data. Trigger even if the user just mentions CORDIS, EU research funding, or Horizon Europe organisations.
---

## What this skill does

Helps you query the CORDIS Horizon Europe dataset to answer questions about organisations, projects, and funding. There are two ways to run a query:

**Option A — Streamlit app SQL tab (preferred)**
Generate SQL and tell the user to paste it into the SQL Query tab of the running CORDIS Explorer app at `http://localhost:8501`.

**Option B — Standalone script**
Run `query_cordis.py` directly in the terminal for natural language queries without launching the app.

---

## Option A: SQL for the Streamlit app

### Column names — critical

The CSVs are loaded with `normalize_names=true`, which lowercases all column names and prefixes SQL reserved words with `_`. Use these names exactly in queries:

**organization table** (one row per org per project):

| Column | Notes |
|--------|-------|
| `projectid` | Links to project (quoted VARCHAR — see joins below) |
| `organisationid` | Unique org identifier |
| `_name` | Organisation name (`name` is reserved) |
| `shortname` | Abbreviation |
| `activitytype` | PRC, HES, REC, PUB, OTH |
| `sme` | `'true'` or `'false'` (string) |
| `_role` | coordinator, participant, associatedPartner (`role` is reserved) |
| `city`, `country`, `street`, `postcode` | Address |
| `geolocation` | `"lat,lon"` string |
| `organizationurl` | Website |
| `eccontribution` | EU funding to this org on this project (quoted VARCHAR) |
| `active` | Whether currently active |

**project table** (one row per project):

| Column | Notes |
|--------|-------|
| `id` | Project ID (quoted VARCHAR) |
| `acronym`, `title` | |
| `status` | SIGNED, CLOSED, TERMINATED |
| `startdate`, `enddate` | |
| `frameworkprogramme` | e.g. HORIZON |
| `fundingscheme` | |
| `totalcost`, `ecmaxcontribution` | Quoted VARCHAR — use `TRY_CAST(REPLACE(col, '"', '') AS DOUBLE)` |
| `objective` | Full project description |
| `keywords` | Comma-separated |
| `topics` | EU topic codes |

**euro_sci_voc table** (many per project):

| Column | Notes |
|--------|-------|
| `projectid` | BIGINT — different type from organization.projectid |
| `euroscivoctitle` | Scientific vocabulary term |
| `euroscivocpath` | Hierarchical path |

**policy_priorities table** (one row per project):

| Column | Notes |
|--------|-------|
| `projectid` | BIGINT |
| `ai`, `biodiversity`, `cleanair`, `climate`, `digitalagenda` | BIGINT (0 or 1) |

### JOIN rules

`organization.projectid` is a quoted VARCHAR (e.g. `'"101194172"'`).
`project.id` is also a quoted VARCHAR — these match directly.
`euro_sci_voc.projectid` and `policy_priorities.projectid` are BIGINT — must cast:

```sql
-- Correct joins
JOIN project p ON p.id = o.projectid
LEFT JOIN euro_sci_voc esv ON esv.projectid = TRY_CAST(REPLACE(o.projectid, '"', '') AS BIGINT)
LEFT JOIN policy_priorities pp ON pp.projectid = TRY_CAST(REPLACE(o.projectid, '"', '') AS BIGINT)
```

### Standard query template

```sql
SELECT
    TRIM('"' FROM o._name)          AS organisation,
    TRIM('"' FROM o.country)        AS country,
    TRIM('"' FROM o.activitytype)   AS type,
    COUNT(DISTINCT o.projectid)     AS projects,
    SUM(TRY_CAST(REPLACE(o.eccontribution, '"', '') AS DOUBLE)) AS total_funding_eur
FROM organization o
JOIN project p ON p.id = o.projectid
WHERE <your filters here>
GROUP BY o._name, o.country, o.activitytype
ORDER BY projects DESC
LIMIT 25;
```

### SQL examples

**Top private companies by project count:**
```sql
SELECT
    TRIM('"' FROM o._name) AS organisation,
    TRIM('"' FROM o.country) AS country,
    COUNT(DISTINCT o.projectid) AS projects,
    SUM(TRY_CAST(REPLACE(o.eccontribution, '"', '') AS DOUBLE)) AS total_funding_eur
FROM organization o
JOIN project p ON p.id = o.projectid
WHERE o.activitytype = '"PRC"'
GROUP BY o._name, o.country
ORDER BY projects DESC
LIMIT 25;
```

**Organisations from a specific country (e.g. Australia):**
```sql
SELECT
    TRIM('"' FROM o._name) AS organisation,
    TRIM('"' FROM o.activitytype) AS type,
    COUNT(DISTINCT o.projectid) AS projects,
    SUM(TRY_CAST(REPLACE(o.eccontribution, '"', '') AS DOUBLE)) AS total_funding_eur
FROM organization o
JOIN project p ON p.id = o.projectid
WHERE o.country = '"AU"'
GROUP BY o._name, o.activitytype
ORDER BY projects DESC
LIMIT 25;
```

**Keyword search across project objectives and scientific vocabulary:**
```sql
SELECT
    TRIM('"' FROM o._name) AS organisation,
    TRIM('"' FROM o.country) AS country,
    COUNT(DISTINCT o.projectid) AS projects
FROM organization o
JOIN project p ON p.id = o.projectid
LEFT JOIN euro_sci_voc esv ON esv.projectid = TRY_CAST(REPLACE(o.projectid, '"', '') AS BIGINT)
WHERE p.keywords ILIKE '%hydrogen%'
   OR p.objective ILIKE '%hydrogen%'
   OR esv.euroscivoctitle ILIKE '%hydrogen%'
GROUP BY o._name, o.country
ORDER BY projects DESC
LIMIT 25;
```

**Coordinators only:**
```sql
SELECT
    TRIM('"' FROM o._name) AS organisation,
    TRIM('"' FROM o.country) AS country,
    COUNT(DISTINCT o.projectid) AS projects_coordinated
FROM organization o
JOIN project p ON p.id = o.projectid
WHERE o._role = '"coordinator"'
GROUP BY o._name, o.country
ORDER BY projects_coordinated DESC
LIMIT 25;
```

**AI policy priority filter:**
```sql
SELECT
    TRIM('"' FROM o._name) AS organisation,
    TRIM('"' FROM o.country) AS country,
    COUNT(DISTINCT o.projectid) AS projects
FROM organization o
JOIN project p ON p.id = o.projectid
JOIN policy_priorities pp ON pp.projectid = TRY_CAST(REPLACE(o.projectid, '"', '') AS BIGINT)
WHERE pp.ai = 1
  AND o.activitytype = '"PRC"'
GROUP BY o._name, o.country
ORDER BY projects DESC
LIMIT 25;
```

**All projects for a specific organisation:**
```sql
SELECT
    TRIM('"' FROM p.acronym)            AS acronym,
    TRIM('"' FROM p.title)              AS title,
    TRIM('"' FROM p.status)             AS status,
    TRIM('"' FROM p.startdate)          AS start,
    TRIM('"' FROM o._role)              AS role,
    TRY_CAST(REPLACE(o.eccontribution, '"', '') AS DOUBLE) AS ec_contribution
FROM organization o
JOIN project p ON p.id = o.projectid
WHERE o._name ILIKE '%University of Queensland%'
ORDER BY p.startdate DESC;
```

**Country breakdown:**
```sql
SELECT
    TRIM('"' FROM o.country) AS country,
    COUNT(DISTINCT o.organisationid) AS organisations,
    COUNT(DISTINCT o.projectid) AS projects,
    SUM(TRY_CAST(REPLACE(o.eccontribution, '"', '') AS DOUBLE)) AS total_funding_eur
FROM organization o
GROUP BY o.country
ORDER BY projects DESC
LIMIT 30;
```

### Note on filter values

Because of the quoted VARCHAR issue, filter values themselves include the quotes in the raw data. Use `ILIKE` with wildcards for text fields to avoid needing to know the exact quoting:
```sql
WHERE o.country ILIKE '%AU%'     -- safer than = '"AU"'
WHERE o.activitytype ILIKE '%PRC%'
```
Or use TRIM and compare clean values:
```sql
WHERE TRIM('"' FROM o.country) = 'AU'
```

---

## Option B: Standalone script

For quick queries without launching the app, run directly in the terminal:

```bash
python "C:/Users/samue/.claude/skills/cordis/scripts/query_cordis.py" \
  --cache-dir "C:/Users/samue/Queensland Parliament/Cooper Electorate Office - Cooper/EO Staff Folders/Dolan, Sam/CORDIS/data" \
  --query "top 10 by project count"
```

The script downloads and caches the data automatically on first run. Supported query patterns:
- `top N by project count`
- `top N by funding`
- `coordinators top N`
- `SME top N`
- `from AU` / `from DE` (country filter)
- `country breakdown`
- `summary` / `overview`
- `find [org name]`

---

## Output format

Always present results as a markdown table:

| Rank | Organisation | Country | Projects | EU Funding (€M) |
|------|-------------|---------|----------|-----------------|
| 1 | ... | ... | ... | ... |

Add one sentence summarising the key finding. For briefings, include:
- Time period: Horizon Europe 2021–present
- Source: *CORDIS, Horizon Europe 2021-2027*
