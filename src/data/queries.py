import duckdb
import pandas as pd
from typing import Any


def get_filter_options(conn: duckdb.DuckDBPyConnection) -> dict[str, list]:
    countries = conn.execute(
        "SELECT DISTINCT country FROM org_project_base WHERE country IS NOT NULL ORDER BY country"
    ).df()["country"].tolist()

    activity_types = conn.execute(
        "SELECT DISTINCT activitytype FROM org_project_base WHERE activitytype IS NOT NULL ORDER BY activitytype"
    ).df()["activitytype"].tolist()

    frameworks = conn.execute(
        "SELECT DISTINCT framework FROM org_project_base WHERE framework IS NOT NULL ORDER BY framework"
    ).df()["framework"].tolist()

    statuses = conn.execute(
        "SELECT DISTINCT status FROM org_project_base WHERE status IS NOT NULL ORDER BY status"
    ).df()["status"].tolist()

    sci_voc_terms = conn.execute(
        "SELECT DISTINCT euroscivoctitle FROM euro_sci_voc WHERE euroscivoctitle IS NOT NULL ORDER BY euroscivoctitle"
    ).df()["euroscivoctitle"].tolist()

    legal_bases = conn.execute(
        "SELECT DISTINCT TRIM('\"' FROM title) AS title FROM legal_basis WHERE uniqueprogrammepart IS TRUE AND title IS NOT NULL ORDER BY 1"
    ).df()["title"].tolist()

    pillars = conn.execute(
        "SELECT DISTINCT pillar FROM org_project_base WHERE pillar IS NOT NULL ORDER BY pillar"
    ).df()["pillar"].tolist()

    return {
        "countries": countries,
        "activity_types": activity_types,
        "frameworks": frameworks,
        "statuses": statuses,
        "policy_priorities": ["ai", "biodiversity", "cleanair", "climate", "digitalagenda"],
        "sci_voc_terms": sci_voc_terms,
        "legal_bases": legal_bases,
        "pillars": pillars,
    }


def query_organizations(
    conn: duckdb.DuckDBPyConnection, filters: dict[str, Any]
) -> pd.DataFrame:
    where_clauses = ["1=1"]
    params: list[Any] = []

    if filters.get("activity_types"):
        placeholders = ", ".join(["?" for _ in filters["activity_types"]])
        where_clauses.append(f"activitytype IN ({placeholders})")
        params.extend(filters["activity_types"])

    if filters.get("countries"):
        placeholders = ", ".join(["?" for _ in filters["countries"]])
        where_clauses.append(f"country IN ({placeholders})")
        params.extend(filters["countries"])

    if filters.get("sme_only"):
        where_clauses.append("sme = 'true'")

    if filters.get("project_status"):
        placeholders = ", ".join(["?" for _ in filters["project_status"]])
        where_clauses.append(f"status IN ({placeholders})")
        params.extend(filters["project_status"])

    if filters.get("frameworks"):
        placeholders = ", ".join(["?" for _ in filters["frameworks"]])
        where_clauses.append(f"framework IN ({placeholders})")
        params.extend(filters["frameworks"])

    if filters.get("policy_priorities"):
        for col in filters["policy_priorities"]:
            where_clauses.append(f"has_{col} = 1")

    if filters.get("search"):
        term = f"%{filters['search']}%"
        where_clauses.append("""(
            name ILIKE ?
            OR organisationid IN (
                SELECT organisationid FROM org_search_index
                WHERE all_keywords  ILIKE ?
                   OR all_objectives ILIKE ?
                   OR all_sci_voc    ILIKE ?
            )
        )""")
        params.extend([term, term, term, term])

    if filters.get("sci_voc_terms"):
        conditions = " OR ".join(["all_sci_voc ILIKE ?" for _ in filters["sci_voc_terms"]])
        where_clauses.append(
            f"organisationid IN (SELECT organisationid FROM org_search_index WHERE {conditions})"
        )
        params.extend([f"%{t}%" for t in filters["sci_voc_terms"]])

    if filters.get("legal_basis"):
        placeholders = ", ".join(["?" for _ in filters["legal_basis"]])
        where_clauses.append(f"""organisationid IN (
            SELECT DISTINCT ob2.organisationid FROM org_project_base ob2
            JOIN legal_basis lb
              ON lb.projectid = TRY_CAST(REPLACE(ob2.projectid, '"', '') AS BIGINT)
            WHERE lb.title IN ({placeholders})
        )""")
        params.extend(filters["legal_basis"])

    if filters.get("pillar"):
        placeholders = ", ".join(["?" for _ in filters["pillar"]])
        where_clauses.append(f"pillar IN ({placeholders})")
        params.extend(filters["pillar"])

    where_sql = " AND ".join(where_clauses)
    limit = int(filters.get("top_n") or 500)

    sql = f"""
        SELECT
            organisationid,
            ANY_VALUE(name)            AS name,
            ANY_VALUE(activitytype)    AS activityType,
            ANY_VALUE(sme)             AS SME,
            ANY_VALUE(city)            AS city,
            ANY_VALUE(country)         AS country,
            ANY_VALUE(geolocation)     AS geolocation,
            ANY_VALUE(organizationurl) AS organizationURL,
            COUNT(DISTINCT projectid)  AS project_count,
            SUM(eccontribution)        AS total_ec_contribution
        FROM org_project_base
        WHERE {where_sql}
        GROUP BY organisationid
        ORDER BY project_count DESC
        LIMIT {limit}
    """
    return conn.execute(sql, params).df()


def top_companies_by_project_count(
    conn: duckdb.DuckDBPyConnection,
    filters: dict[str, Any],
    limit: int = 25,
) -> pd.DataFrame:
    df = query_organizations(conn, filters)
    return df.nlargest(limit, "project_count")[
        ["name", "country", "activityType", "project_count", "total_ec_contribution", "organisationid"]
    ]


def get_org_detail(
    conn: duckdb.DuckDBPyConnection, org_id: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    org_df = conn.execute("""
        SELECT
            ANY_VALUE(TRIM('"' FROM o._name))           AS name,
            ANY_VALUE(TRIM('"' FROM o.shortname))       AS short_name,
            ANY_VALUE(TRIM('"' FROM o.activitytype))    AS activity_type,
            ANY_VALUE(TRIM('"' FROM o.sme))             AS sme,
            ANY_VALUE(TRIM('"' FROM o.street))          AS street,
            ANY_VALUE(TRIM('"' FROM o.city))            AS city,
            ANY_VALUE(TRIM('"' FROM o.postcode))        AS postcode,
            ANY_VALUE(TRIM('"' FROM o.country))         AS country,
            ANY_VALUE(TRIM('"' FROM o.organizationurl)) AS url,
            ANY_VALUE(TRIM('"' FROM o.contactform))     AS contact,
            COUNT(DISTINCT o.projectid)                 AS project_count,
            SUM(TRY_CAST(REPLACE(o.eccontribution, '"', '') AS DOUBLE)) AS total_ec_contribution
        FROM organization o
        WHERE o.organisationid = ?
    """, [org_id]).df()

    projects_df = conn.execute("""
        SELECT
            p.id                                                           AS project_id,
            TRIM('"' FROM p.acronym)                                       AS acronym,
            TRIM('"' FROM p.title)                                         AS title,
            TRIM('"' FROM p.status)                                        AS status,
            TRIM('"' FROM p.startdate)                                     AS start_date,
            TRIM('"' FROM p.enddate)                                       AS end_date,
            TRIM('"' FROM p.frameworkprogramme)                            AS framework,
            TRIM('"' FROM o._role)                                         AS role,
            TRY_CAST(REPLACE(o.eccontribution, '"', '') AS DOUBLE)         AS ec_contribution
        FROM organization o
        JOIN project p ON p.id = o.projectid
        WHERE o.organisationid = ?
        ORDER BY TRIM('"' FROM p.startdate) DESC
    """, [org_id]).df()

    return org_df, projects_df


def get_project_detail(
    conn: duckdb.DuckDBPyConnection, project_id: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    project_df = conn.execute("""
        SELECT
            TRIM('"' FROM p.id)                                        AS id,
            TRIM('"' FROM p.acronym)                                   AS acronym,
            TRIM('"' FROM p.title)                                     AS title,
            TRIM('"' FROM p.status)                                    AS status,
            TRIM('"' FROM p.startdate)                                 AS start_date,
            TRIM('"' FROM p.enddate)                                   AS end_date,
            TRIM('"' FROM p.frameworkprogramme)                        AS framework,
            TRIM('"' FROM p.fundingscheme)                             AS funding_scheme,
            TRY_CAST(REPLACE(p.totalcost, '"', '') AS DOUBLE)          AS total_cost,
            TRY_CAST(REPLACE(p.ecmaxcontribution, '"', '') AS DOUBLE)  AS ec_max_contribution,
            TRIM('"' FROM p.objective)                                 AS objective,
            TRIM('"' FROM p.keywords)                                  AS keywords,
            TRIM('"' FROM p.topics)                                    AS topics
        FROM project p
        WHERE p.id = ?
        LIMIT 1
    """, [project_id]).df()

    orgs_df = conn.execute("""
        SELECT
            o.organisationid,
            TRIM('"' FROM o._name)           AS name,
            TRIM('"' FROM o.country)         AS country,
            TRIM('"' FROM o.activitytype)    AS type,
            TRIM('"' FROM o._role)           AS role,
            TRY_CAST(REPLACE(o.eccontribution, '"', '') AS DOUBLE) AS ec_contribution,
            TRIM('"' FROM o.city)            AS city,
            TRIM('"' FROM o.organizationurl) AS url
        FROM organization o
        WHERE o.projectid = ?
        ORDER BY ec_contribution DESC NULLS LAST
    """, [project_id]).df()

    return project_df, orgs_df


def run_raw_sql(conn: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return conn.execute(sql).df()
